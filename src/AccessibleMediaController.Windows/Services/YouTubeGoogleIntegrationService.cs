namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Jeden właściciel konfiguracji, logowania i odczytu biblioteki YouTube.
/// Dane trwałe znajdują się wyłącznie w Menedżerze poświadczeń Windows.
/// </summary>
internal sealed class YouTubeGoogleIntegrationService : IDisposable
{
    private readonly YouTubeGoogleOAuthClient oauth;
    private readonly YouTubeDataApiClient api;
    private readonly SemaphoreSlim tokenGate = new(1, 1);

    internal YouTubeGoogleIntegrationService(
        YouTubeGoogleOAuthClient? oauthClient = null,
        YouTubeDataApiClient? apiClient = null)
    {
        oauth = oauthClient ?? new YouTubeGoogleOAuthClient();
        api = apiClient ?? new YouTubeDataApiClient();
    }

    public bool IsConfigured => TryGetCredentials(out _);

    public bool HasStoredLogin => TryGetCredentials(out var credentials)
        && credentials?.HasLogin == true;

    public string AccountDisplayName => TryGetCredentials(out var credentials)
        ? credentials?.AccountDisplayName ?? string.Empty
        : string.Empty;

    public bool TryGetCredentials(out YouTubeGoogleCredentialSet? credentials) =>
        YouTubeGoogleCredentialStore.TryRead(out credentials);

    public void SaveClientId(string clientId)
    {
        var normalized = (clientId ?? string.Empty).Trim();
        if (!YouTubeGoogleCredentialStore.IsValidClientId(normalized))
        {
            throw new InvalidOperationException(
                "Wpisz identyfikator klienta Google typu Aplikacja na komputer. Powinien kończyć się na .apps.googleusercontent.com.");
        }

        if (TryGetCredentials(out var current)
            && current is not null
            && string.Equals(current.ClientId, normalized, StringComparison.Ordinal))
        {
            YouTubeGoogleCredentialStore.Write(current);
            return;
        }

        YouTubeGoogleCredentialStore.Write(new YouTubeGoogleCredentialSet(
            normalized,
            null,
            null,
            DateTimeOffset.MinValue,
            YouTubeGoogleOAuthClient.RequestedScope,
            string.Empty));
    }

    public async Task<string> AuthorizeAsync(CancellationToken cancellationToken)
    {
        var configured = RequireCredentials(requireLogin: false);
        var authenticated = await oauth.AuthorizeAsync(configured.ClientId, cancellationToken)
            .ConfigureAwait(false);
        var displayName = await api.GetAccountDisplayNameAsync(
            authenticated.AccessToken!,
            cancellationToken).ConfigureAwait(false);
        authenticated = authenticated with { AccountDisplayName = displayName };
        YouTubeGoogleCredentialStore.Write(authenticated);
        return displayName;
    }

    public async Task<YouTubeAccountLibrary> ReadLibraryAsync(CancellationToken cancellationToken)
    {
        var authenticated = await RequireValidLoginAsync(cancellationToken).ConfigureAwait(false);
        var displayNameTask = api.GetAccountDisplayNameAsync(authenticated.AccessToken!, cancellationToken);
        var subscriptionsTask = api.GetSubscriptionsAsync(authenticated.AccessToken!, cancellationToken);
        var playlistsTask = api.GetPlaylistsAsync(authenticated.AccessToken!, cancellationToken);
        await Task.WhenAll(displayNameTask, subscriptionsTask, playlistsTask).ConfigureAwait(false);
        var displayName = await displayNameTask.ConfigureAwait(false);
        if (!string.Equals(displayName, authenticated.AccountDisplayName, StringComparison.Ordinal))
            YouTubeGoogleCredentialStore.Write(authenticated with { AccountDisplayName = displayName });
        return new YouTubeAccountLibrary(
            displayName,
            await subscriptionsTask.ConfigureAwait(false),
            await playlistsTask.ConfigureAwait(false));
    }

    public void SignOut()
    {
        var current = RequireCredentials(requireLogin: false);
        YouTubeGoogleCredentialStore.Write(current with
        {
            AccessToken = null,
            RefreshToken = null,
            ExpiresAtUtc = DateTimeOffset.MinValue,
            Scope = YouTubeGoogleOAuthClient.RequestedScope,
            AccountDisplayName = string.Empty
        });
    }

    public void RemoveConfiguration() => YouTubeGoogleCredentialStore.Delete();

    private async Task<YouTubeGoogleCredentialSet> RequireValidLoginAsync(
        CancellationToken cancellationToken)
    {
        var current = RequireCredentials(requireLogin: true);
        if (current.ExpiresAtUtc > DateTimeOffset.UtcNow.AddMinutes(2)) return current;

        await tokenGate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            current = RequireCredentials(requireLogin: true);
            if (current.ExpiresAtUtc > DateTimeOffset.UtcNow.AddMinutes(2)) return current;
            var refreshed = await oauth.RefreshAsync(current, cancellationToken).ConfigureAwait(false);
            YouTubeGoogleCredentialStore.Write(refreshed);
            return refreshed;
        }
        finally
        {
            tokenGate.Release();
        }
    }

    private static YouTubeGoogleCredentialSet RequireCredentials(bool requireLogin)
    {
        if (!YouTubeGoogleCredentialStore.TryRead(out var credentials) || credentials is null)
            throw new InvalidOperationException("Najpierw zapisz identyfikator klienta Google dla aplikacji desktopowej.");
        if (requireLogin && !credentials.HasLogin)
            throw new InvalidOperationException("Najpierw zaloguj konto Google w oknie konta YouTube.");
        return credentials;
    }

    public void Dispose()
    {
        oauth.Dispose();
        api.Dispose();
        tokenGate.Dispose();
    }
}
