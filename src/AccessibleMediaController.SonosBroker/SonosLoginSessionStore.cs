using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;

namespace AccessibleMediaController.SonosBroker;

internal sealed class SonosLoginSessionStore
{
    private const int PkceLength = 43;
    private readonly ConcurrentDictionary<string, LoginSession> sessions = new(StringComparer.Ordinal);
    private readonly ConcurrentDictionary<string, string> states = new(StringComparer.Ordinal);
    private readonly object capacityGate = new();
    private readonly int maximumSessions;

    internal SonosLoginSessionStore(int maximumSessions)
    {
        if (maximumSessions < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(maximumSessions));
        }

        this.maximumSessions = maximumSessions;
    }

    internal static bool IsPkceValue(string? value) =>
        value is not null
        && value.Length == PkceLength
        && value.All(character => character is >= 'A' and <= 'Z'
            or >= 'a' and <= 'z'
            or >= '0' and <= '9'
            or '-'
            or '_');

    internal SessionCreateResult Create(
        string codeChallenge,
        DateTimeOffset nowUtc,
        TimeSpan lifetime)
    {
        ArgumentException.ThrowIfNullOrEmpty(codeChallenge);
        if (!IsPkceValue(codeChallenge) || lifetime <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(codeChallenge));
        }

        RemoveExpired(nowUtc);
        lock (capacityGate)
        {
            if (sessions.Count >= maximumSessions)
            {
                return new SessionCreateResult(
                    SessionCreateStatus.CapacityReached, null, null, nowUtc);
            }

            for (var attempt = 0; attempt < 8; attempt++)
            {
                var sessionId = RandomValue();
                var state = RandomValue();
                var expires = nowUtc.Add(lifetime);
                var session = new LoginSession(sessionId, state, codeChallenge, expires);
                if (!sessions.TryAdd(sessionId, session))
                {
                    continue;
                }

                if (states.TryAdd(state, sessionId))
                {
                    return new SessionCreateResult(
                        SessionCreateStatus.Success, sessionId, state, expires);
                }

                sessions.TryRemove(sessionId, out _);
            }

            return new SessionCreateResult(
                SessionCreateStatus.CapacityReached, null, null, nowUtc);
        }
    }

    internal CallbackBeginStatus BeginCallback(string? state, DateTimeOffset nowUtc)
    {
        if (!IsPkceValue(state)
            || !states.TryGetValue(state!, out var sessionId)
            || !sessions.TryGetValue(sessionId, out var session))
        {
            return CallbackBeginStatus.Unknown;
        }

        lock (session.Gate)
        {
            if (nowUtc >= session.ExpiresAtUtc)
            {
                Remove(session);
                return CallbackBeginStatus.Unknown;
            }

            if (session.CallbackStarted)
            {
                return CallbackBeginStatus.AlreadyStarted;
            }

            session.CallbackStarted = true;
            return CallbackBeginStatus.Started;
        }
    }

    internal CallbackStoreStatus StoreCallback(
        string? state,
        SessionReadStatus status,
        TokenResponse? tokens,
        DateTimeOffset nowUtc)
    {
        if (!IsPkceValue(state)
            || !states.TryGetValue(state!, out var sessionId)
            || !sessions.TryGetValue(sessionId, out var session))
        {
            return CallbackStoreStatus.Unknown;
        }

        lock (session.Gate)
        {
            if (nowUtc >= session.ExpiresAtUtc)
            {
                Remove(session);
                return CallbackStoreStatus.Unknown;
            }

            if (!session.CallbackStarted || session.Status != SessionReadStatus.Pending)
            {
                return CallbackStoreStatus.AlreadyCompleted;
            }

            if (status == SessionReadStatus.Success && tokens is null)
            {
                throw new ArgumentException(
                    "Udany wynik logowania wymaga tokenów.", nameof(tokens));
            }

            if (status is not (SessionReadStatus.Success
                or SessionReadStatus.Denied
                or SessionReadStatus.InvalidCallback
                or SessionReadStatus.TokenExchangeFailed))
            {
                throw new ArgumentOutOfRangeException(nameof(status));
            }

            session.Status = status;
            session.Tokens = tokens;
            return CallbackStoreStatus.Stored;
        }
    }

    internal SessionReadResult ReadOnce(
        string? sessionId,
        string? verifier,
        DateTimeOffset nowUtc)
    {
        if (!IsPkceValue(sessionId)
            || !IsPkceValue(verifier)
            || !sessions.TryGetValue(sessionId!, out var session))
        {
            return new SessionReadResult(SessionReadStatus.Unknown);
        }

        var actual = SHA256.HashData(Encoding.ASCII.GetBytes(verifier!));
        var expected = DecodeBase64Url(session.CodeChallenge);
        if (expected is null || !CryptographicOperations.FixedTimeEquals(actual, expected))
        {
            return new SessionReadResult(SessionReadStatus.ProofMismatch);
        }

        lock (session.Gate)
        {
            if (nowUtc >= session.ExpiresAtUtc)
            {
                Remove(session);
                return new SessionReadResult(SessionReadStatus.Unknown);
            }

            if (session.Status == SessionReadStatus.Pending)
            {
                return new SessionReadResult(SessionReadStatus.Pending);
            }

            var result = new SessionReadResult(session.Status, session.Tokens);
            Remove(session);
            return result;
        }
    }

    internal int RemoveExpired(DateTimeOffset nowUtc)
    {
        var removed = 0;
        foreach (var session in sessions.Values)
        {
            if (nowUtc < session.ExpiresAtUtc)
            {
                continue;
            }

            lock (session.Gate)
            {
                if (nowUtc >= session.ExpiresAtUtc && Remove(session))
                {
                    removed++;
                }
            }
        }

        return removed;
    }

    private bool Remove(LoginSession session)
    {
        lock (capacityGate)
        {
            states.TryRemove(session.State, out _);
            return sessions.TryRemove(session.SessionId, out _);
        }
    }

    private static string RandomValue() => Base64Url(RandomNumberGenerator.GetBytes(32));

    private static string Base64Url(byte[] value) =>
        Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');

    private static byte[]? DecodeBase64Url(string value)
    {
        try
        {
            var padded = value.Replace('-', '+').Replace('_', '/') + "=";
            return Convert.FromBase64String(padded);
        }
        catch (FormatException)
        {
            return null;
        }
    }

    private sealed class LoginSession
    {
        internal LoginSession(
            string sessionId,
            string state,
            string codeChallenge,
            DateTimeOffset expiresAtUtc)
        {
            SessionId = sessionId;
            State = state;
            CodeChallenge = codeChallenge;
            ExpiresAtUtc = expiresAtUtc;
        }

        internal object Gate { get; } = new();
        internal string SessionId { get; }
        internal string State { get; }
        internal string CodeChallenge { get; }
        internal DateTimeOffset ExpiresAtUtc { get; }
        internal bool CallbackStarted { get; set; }
        internal SessionReadStatus Status { get; set; } = SessionReadStatus.Pending;
        internal TokenResponse? Tokens { get; set; }
    }
}
