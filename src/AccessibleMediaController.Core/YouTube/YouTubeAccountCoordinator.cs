namespace AccessibleMediaController.Core.YouTube;

public interface IYouTubeCredentialStore
{
    bool TryRead(out YouTubeTokenSet? tokens);
    void Write(YouTubeTokenSet tokens);
    void Delete();
}

public sealed record YouTubeAccountStatus(
    bool Connected,
    string Message,
    DateTimeOffset? ExpiresAtUtc);

public sealed record YouTubeAccountOperationResult(bool Succeeded, string Message);

/// <summary>
/// Jeden właściciel cyklu konta YouTube w hoście C#. Interfejs użytkownika
/// przekazuje tylko jawne polecenie i otrzymuje użytkowy stan; tokeny, kod i
/// PKCE nie wychodzą poza tę warstwę.
/// </summary>
public sealed class YouTubeAccountCoordinator : IDisposable
{
    internal static TimeSpan DefaultLoginTimeout { get; } = TimeSpan.FromMinutes(15);
    internal static TimeSpan MaximumLoginTimeout { get; } = TimeSpan.FromMinutes(30);

    private readonly string _clientId;
    private readonly string? _clientSecret;
    private readonly Uri? _tokenBrokerEndpoint;
    private readonly IYouTubeCredentialStore _store;
    private readonly YouTubeOAuthTokenClient _tokenClient;
    private readonly Func<Uri, CancellationToken, Task<bool>> _openAuthorizationPage;
    private readonly Func<DateTimeOffset> _now;
    private readonly TimeSpan _loginTimeout;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private bool _disposed;

    public YouTubeAccountCoordinator(
        string clientId,
        string clientSecret,
        IYouTubeCredentialStore store,
        YouTubeOAuthTokenClient tokenClient,
        Func<Uri, CancellationToken, Task<bool>> openAuthorizationPage,
        Func<DateTimeOffset>? now = null,
        TimeSpan? loginTimeout = null)
        : this(
            clientId,
            clientSecret,
            null,
            store,
            tokenClient,
            openAuthorizationPage,
            now,
            loginTimeout)
    {
    }

    public YouTubeAccountCoordinator(
        string clientId,
        Uri tokenBrokerEndpoint,
        IYouTubeCredentialStore store,
        YouTubeOAuthTokenClient tokenClient,
        Func<Uri, CancellationToken, Task<bool>> openAuthorizationPage,
        Func<DateTimeOffset>? now = null,
        TimeSpan? loginTimeout = null)
        : this(
            clientId,
            null,
            tokenBrokerEndpoint,
            store,
            tokenClient,
            openAuthorizationPage,
            now,
            loginTimeout)
    {
    }

    private YouTubeAccountCoordinator(
        string clientId,
        string? clientSecret,
        Uri? tokenBrokerEndpoint,
        IYouTubeCredentialStore store,
        YouTubeOAuthTokenClient tokenClient,
        Func<Uri, CancellationToken, Task<bool>> openAuthorizationPage,
        Func<DateTimeOffset>? now,
        TimeSpan? loginTimeout)
    {
        // Walidacja korzysta z tego samego kontraktu co rzeczywiste żądanie,
        // bez uruchamiania sieci i bez przechowywania osobnego wariantu reguł.
        if ((clientSecret is null) == (tokenBrokerEndpoint is null))
            throw new ArgumentException("Wybierz dokładnie jeden sposób wymiany tokenów YouTube.");
        if (clientSecret is not null)
        {
            _ = YouTubeOAuthProtocol.CreateRefreshFields(
                clientId, clientSecret, "validation-only");
        }
        else
        {
            _ = YouTubeOAuthProtocol.CreateBrokerRefreshFields(clientId, "validation-only");
            _ = YouTubeOAuthProtocol.ValidateTokenBrokerEndpoint(tokenBrokerEndpoint!);
        }
        _clientId = clientId.Trim();
        _clientSecret = clientSecret?.Trim();
        _tokenBrokerEndpoint = tokenBrokerEndpoint;
        _store = store ?? throw new ArgumentNullException(nameof(store));
        _tokenClient = tokenClient ?? throw new ArgumentNullException(nameof(tokenClient));
        _openAuthorizationPage = openAuthorizationPage
            ?? throw new ArgumentNullException(nameof(openAuthorizationPage));
        _now = now ?? (() => DateTimeOffset.UtcNow);
        _loginTimeout = loginTimeout ?? DefaultLoginTimeout;
        if (_loginTimeout <= TimeSpan.Zero || _loginTimeout > MaximumLoginTimeout)
            throw new ArgumentOutOfRangeException(nameof(loginTimeout));
    }

    public YouTubeAccountStatus GetStatus()
    {
        ThrowIfDisposed();
        if (!_store.TryRead(out var tokens) || tokens is null)
            return new YouTubeAccountStatus(false, "YouTube: niezalogowano", null);
        return new YouTubeAccountStatus(true, "YouTube: zalogowano", tokens.ExpiresAtUtc);
    }

    public async Task<YouTubeAccountOperationResult> LoginAsync(CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            using var receiver = YouTubeOAuthLoopbackReceiver.Start();
            var request = YouTubeOAuthProtocol.CreateAuthorizationRequest(_clientId, receiver.RedirectUri);
            if (!await _openAuthorizationPage(request.AuthorizationUri, cancellationToken).ConfigureAwait(false))
            {
                return new YouTubeAccountOperationResult(
                    false, "Nie udało się otworzyć oficjalnej strony logowania YouTube.");
            }

            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(_loginTimeout);
            YouTubeAuthorizationCallback callback;
            try
            {
                callback = await receiver.ReceiveAsync(request.State, timeout.Token).ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
            {
                return new YouTubeAccountOperationResult(
                    false, "Upłynął czas oczekiwania na logowanie YouTube.");
            }
            if (!callback.Succeeded || string.IsNullOrWhiteSpace(callback.Code))
                return new YouTubeAccountOperationResult(false, callback.Message);

            var tokens = _tokenBrokerEndpoint is null
                ? await _tokenClient.ExchangeCodeAsync(
                    _clientId,
                    _clientSecret!,
                    receiver.RedirectUri,
                    callback.Code,
                    request.CodeVerifier,
                    _now(),
                    cancellationToken).ConfigureAwait(false)
                : await _tokenClient.ExchangeCodeThroughBrokerAsync(
                    _tokenBrokerEndpoint,
                    _clientId,
                    receiver.RedirectUri,
                    callback.Code,
                    request.CodeVerifier,
                    _now(),
                    cancellationToken).ConfigureAwait(false);
            _store.Write(tokens);
            return new YouTubeAccountOperationResult(true, "Zalogowano do YouTube.");
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<string> GetAccessTokenAsync(CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (!_store.TryRead(out var tokens) || tokens is null)
                throw new InvalidOperationException("Najpierw zaloguj się do YouTube.");
            if (tokens.ExpiresAtUtc > _now().AddMinutes(2)) return tokens.AccessToken;

            var refreshed = _tokenBrokerEndpoint is null
                ? await _tokenClient.RefreshAsync(
                    tokens, _clientSecret!, _now(), cancellationToken).ConfigureAwait(false)
                : await _tokenClient.RefreshThroughBrokerAsync(
                    _tokenBrokerEndpoint, tokens, _now(), cancellationToken).ConfigureAwait(false);
            _store.Write(refreshed);
            return refreshed.AccessToken;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<YouTubeAccountOperationResult> LogoutAsync(CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            _store.Delete();
            return new YouTubeAccountOperationResult(true, "Wylogowano z YouTube.");
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<YouTubeAccountOperationResult> RevokeAndLogoutAsync(
        Func<CancellationToken, Task> deleteAuthorizedData,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        ArgumentNullException.ThrowIfNull(deleteAuthorizedData);
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_store.TryRead(out var tokens) && tokens is not null)
                await _tokenClient.RevokeAsync(tokens.RefreshToken, cancellationToken)
                    .ConfigureAwait(false);

            // Poświadczenie pozostaje do czasu zakończenia lokalnego usuwania.
            // Jeśli zapis na dysku zawiedzie, użytkownik może powtórzyć operację;
            // ponowne cofnięcie już unieważnionego tokenu jest bezpieczne.
            await deleteAuthorizedData(cancellationToken).ConfigureAwait(false);
            _store.Delete();
            return new YouTubeAccountOperationResult(
                true,
                "Cofnięto dostęp YouTube w Google i usunięto dane konta z AMC.");
        }
        finally
        {
            _gate.Release();
        }
    }

    private void ThrowIfDisposed()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _gate.Dispose();
    }
}
