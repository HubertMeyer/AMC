using System.Collections.Concurrent;
using System.Text.Json;

namespace AccessibleMediaController.LiteHost.Protocol;

/// <summary>
/// Wynik jednej komendy dodatku NVDA, przygotowany przez frontend wxPython.
/// Tekst jest wyłącznie zamierzonym komunikatem dla użytkownika; identyfikator
/// korelacji nigdy nie trafia do odpowiedzi dodatku.
/// </summary>
public sealed record LiteNvdaReplyResult(bool Ok, string Message);

/// <summary>
/// Wąski przekaźnik pomiędzy zabezpieczonym potokiem NVDA w hoście C# a
/// właścicielem interfejsu w Pythonie. Nie wykonuje dowolnych poleceń:
/// wejście potoku zostało wcześniej sprawdzone przez <c>NvdaCommands</c>, a
/// z frontendu przyjmuje wyłącznie odpowiedź dla istniejącego żądania.
/// </summary>
public sealed class LiteNvdaRelay : IDisposable
{
    public const string ReplyOperation = "nvda.reply";
    public const string EventName = "nvda.command";

    private readonly ConcurrentDictionary<string, TaskCompletionSource<LiteNvdaReplyResult>> _pending = new();
    private long _nextId;
    private bool _disposed;

    public async Task<LiteNvdaReplyResult> RequestAsync(
        string command,
        LiteEventSink events,
        CancellationToken cancellation)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        var requestId = Interlocked.Increment(ref _nextId).ToString(System.Globalization.CultureInfo.InvariantCulture);
        var completion = new TaskCompletionSource<LiteNvdaReplyResult>(
            TaskCreationOptions.RunContinuationsAsynchronously);
        if (!_pending.TryAdd(requestId, completion))
            throw new InvalidOperationException("Nie można rozpocząć polecenia dodatku NVDA.");

        try
        {
            events.Publish(EventName, new { requestId, command });
            return await completion.Task.WaitAsync(cancellation).ConfigureAwait(false);
        }
        finally
        {
            _pending.TryRemove(requestId, out _);
        }
    }

    public object Reply(LiteRequest request, LiteEventSink _events)
    {
        if (request.Args.ValueKind != JsonValueKind.Object
            || !request.Args.TryGetProperty("requestId", out var idValue)
            || idValue.ValueKind != JsonValueKind.String
            || idValue.GetString() is not { Length: > 0 } requestId
            || !request.Args.TryGetProperty("ok", out var okValue)
            || okValue.ValueKind is not (JsonValueKind.True or JsonValueKind.False)
            || !request.Args.TryGetProperty("message", out var messageValue)
            || messageValue.ValueKind != JsonValueKind.String)
        {
            throw new InvalidOperationException("Niepoprawna odpowiedź interfejsu dla dodatku NVDA.");
        }

        var message = messageValue.GetString() ?? string.Empty;
        if (message.Length > 2000)
            throw new InvalidOperationException("Odpowiedź interfejsu dla dodatku NVDA jest zbyt długa.");

        var accepted = _pending.TryGetValue(requestId, out var completion)
            && completion.TrySetResult(new LiteNvdaReplyResult(okValue.GetBoolean(), message));
        return new { accepted };
    }

    public IReadOnlyDictionary<string, Func<LiteRequest, LiteEventSink, object?>> Handlers() =>
        new Dictionary<string, Func<LiteRequest, LiteEventSink, object?>>(StringComparer.Ordinal)
        {
            [ReplyOperation] = Reply
        };

    public void Dispose()
    {
        _disposed = true;
        foreach (var completion in _pending.Values)
            completion.TrySetCanceled();
        _pending.Clear();
    }
}
