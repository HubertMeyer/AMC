using AccessibleMediaController.Core.AppleMusic;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

internal sealed class AppleMusicIntegrationService : IDisposable
{
    private readonly AppleMusicApiClient apiClient;

    public AppleMusicIntegrationService(AppleMusicApiClient? apiClient = null) =>
        this.apiClient = apiClient ?? new AppleMusicApiClient();

    public bool IsConfigured => TryGetCredentials(out _);
    public bool HasStoredLogin =>
        TryGetCredentials(out var credentials)
        && !string.IsNullOrWhiteSpace(credentials!.MusicUserToken);

    public bool TryGetCredentials(out AppleMusicCredentials? credentials) =>
        AppleMusicCredentialStore.TryRead(out credentials);

    public AppleMusicCredentials RequireCredentials(bool requireUserToken)
    {
        if (!TryGetCredentials(out var credentials) || credentials is null)
            throw new InvalidOperationException(
                "Apple Music nie jest skonfigurowane. Otwórz Konto Apple Music przez Ctrl+F5.");
        if (requireUserToken && string.IsNullOrWhiteSpace(credentials.MusicUserToken))
            throw new InvalidOperationException(
                "Konto Apple Music nie jest zalogowane. Otwórz Konto Apple Music przez Ctrl+F5.");
        return credentials;
    }

    public void SaveDeveloperToken(string developerToken, string storefront)
    {
        TryGetCredentials(out var existing);
        AppleMusicCredentialStore.Write(new AppleMusicCredentials(
            developerToken,
            existing?.MusicUserToken,
            storefront));
    }

    public void SaveMusicUserToken(string musicUserToken)
    {
        var credentials = RequireCredentials(requireUserToken: false);
        if (string.IsNullOrWhiteSpace(musicUserToken))
            throw new InvalidOperationException("Logowanie Apple Music nie zwróciło tokenu użytkownika.");
        AppleMusicCredentialStore.Write(credentials with { MusicUserToken = musicUserToken.Trim() });
    }

    public void SignOut()
    {
        var credentials = RequireCredentials(requireUserToken: false);
        AppleMusicCredentialStore.Write(credentials with { MusicUserToken = null });
    }

    public void RemoveConfiguration() => AppleMusicCredentialStore.Delete();

    public async Task ValidateDeveloperTokenAsync(
        string developerToken,
        string storefront,
        CancellationToken cancellationToken = default) =>
        _ = await apiClient.SearchCatalogAsync(
            developerToken,
            storefront,
            "test",
            cancellationToken).ConfigureAwait(false);

    public Task<IReadOnlyList<MediaItem>> SynchronizeLibraryAsync(
        CancellationToken cancellationToken = default)
    {
        var credentials = RequireCredentials(requireUserToken: true);
        return apiClient.GetLibraryAsync(
            credentials.DeveloperToken,
            credentials.MusicUserToken!,
            cancellationToken);
    }

    public Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        var credentials = RequireCredentials(requireUserToken: false);
        return apiClient.SearchCatalogAsync(
            credentials.DeveloperToken,
            credentials.Storefront,
            query,
            cancellationToken);
    }

    public Task<IReadOnlyList<MediaItem>> GetContainerItemsAsync(
        MediaItem container,
        ArtistBrowseSection? artistSection = null,
        CancellationToken cancellationToken = default)
    {
        var credentials = RequireCredentials(requireUserToken: false);
        return apiClient.GetContainerItemsAsync(
            credentials.DeveloperToken,
            credentials.Storefront,
            container,
            artistSection,
            cancellationToken,
            credentials.MusicUserToken);
    }

    public Task AddToLibraryAsync(
        IReadOnlyList<MediaItem> items,
        CancellationToken cancellationToken = default)
    {
        var credentials = RequireCredentials(requireUserToken: true);
        return apiClient.AddToLibraryAsync(
            credentials.DeveloperToken,
            credentials.MusicUserToken!,
            items,
            cancellationToken);
    }

    public Task AddToFavoritesAsync(
        IReadOnlyList<MediaItem> items,
        CancellationToken cancellationToken = default)
    {
        var credentials = RequireCredentials(requireUserToken: true);
        return apiClient.AddToFavoritesAsync(
            credentials.DeveloperToken,
            credentials.MusicUserToken!,
            items,
            cancellationToken);
    }

    public void Dispose() => apiClient.Dispose();
}
