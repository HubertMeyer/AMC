using System.Net;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Windows adapter around the already tested Spotify API implementation.
/// This class exposes no login, disconnect or collection mutation method.
/// </summary>
internal sealed class LiteSpotifyWindowsCatalogBackend : ILiteSpotifyReadOnlyBackend
{
    private const string CatalogCredentialTarget = "AccessibleMediaController/Spotify";
    private const string PlaybackCredentialTarget =
        "AccessibleMediaController/SpotifyLibrespot";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() }
    };

    private readonly SpotifySettings _settings;
    private readonly SpotifyIntegrationService _integration;
    private readonly SpotifyApiClient _api = new();

    public LiteSpotifyWindowsCatalogBackend(string statePath)
    {
        _settings = ReadSettings(statePath);
        CachedCollection = _settings.CachedCollectionItems
            .Select(item => item.ToMediaItem())
            .ToArray();
        _integration = new SpotifyIntegrationService(_settings);
    }

    public IReadOnlyList<MediaItem> CachedCollection { get; }

    public LiteSpotifyAccountProbe ReadAccountStatus() => new(
        CatalogConfigured: _integration.IsConfigured,
        CatalogConnected: ProbeCredential(CatalogCredentialTarget),
        AccountDisplayName: _settings.AccountDisplayName,
        AccountProduct: _settings.AccountProduct,
        PlaybackConnected: ProbeCredential(PlaybackCredentialTarget));

    public async Task<LiteSpotifyCollectionRefresh> RefreshCollectionAsync(
        CancellationToken cancellationToken)
    {
        EnsureCatalogReady();
        try
        {
            var result = await _integration.SynchronizeAsync(cancellationToken)
                .ConfigureAwait(false);
            return new LiteSpotifyCollectionRefresh(
                result.Items,
                result.Warnings.Count > 0 || !result.IsComplete);
        }
        catch (Exception exception)
        {
            throw Translate(exception, cancellationToken);
        }
    }

    public async Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken)
    {
        EnsureCatalogReady();
        try
        {
            return await _integration.SearchAsync(query, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (Exception exception)
        {
            throw Translate(exception, cancellationToken);
        }
    }

    public async Task<string?> GetDescriptionAsync(
        LiteSpotifyDescriptionRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        EnsureCatalogReady();
        try
        {
            var credentials = await _integration
                .GetPlaybackCredentialsAsync(cancellationToken)
                .ConfigureAwait(false);
            return await _api.GetPodcastDescriptionAsync(
                    credentials.AccessToken,
                    request.ExternalId,
                    request.Kind,
                    cancellationToken)
                .ConfigureAwait(false);
        }
        catch (Exception exception)
        {
            throw Translate(exception, cancellationToken);
        }
    }

    public async Task<LiteSpotifyContainerBackendResult> GetContainerItemsAsync(
        LiteSpotifyContainerRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        EnsureCatalogReady();
        try
        {
            if (request.Kind == MediaItemKind.Playlist)
            {
                var playlistItems = await _integration.GetPlaylistTracksAsync(
                        request.ExternalId,
                        cancellationToken)
                    .ConfigureAwait(false);
                return playlistItems is null
                    ? new([], Available: false)
                    : new(playlistItems, Available: true);
            }

            // The token remains inside this C# process. The method name comes
            // from the old SDK integration, but the same OAuth token is also
            // the credential used by the read-only Web API catalogue.
            var credentials = await _integration.GetPlaybackCredentialsAsync(cancellationToken)
                .ConfigureAwait(false);
            return request.Kind switch
            {
                MediaItemKind.Album => FromOptionalItems(
                    await _api.GetAlbumTracksAsync(
                            credentials.AccessToken,
                            request.ExternalId,
                            cancellationToken)
                        .ConfigureAwait(false)),
                MediaItemKind.Podcast => FromOptionalItems(
                    await _api.GetShowEpisodesAsync(
                            credentials.AccessToken,
                            request.ExternalId,
                            cancellationToken)
                        .ConfigureAwait(false)),
                MediaItemKind.Artist when request.ArtistSection == "tracks" =>
                    FromArtistTracks(
                        await _api.GetArtistTracksAsync(
                                credentials.AccessToken,
                                _integration.CountryCode,
                                request.ExternalId,
                                request.Title,
                                cancellationToken)
                            .ConfigureAwait(false)),
                MediaItemKind.Artist => FromOptionalItems(
                    await _api.GetArtistAlbumsAsync(
                            credentials.AccessToken,
                            request.ExternalId,
                            cancellationToken)
                        .ConfigureAwait(false)),
                _ => new([], Available: false)
            };
        }
        catch (Exception exception)
        {
            throw Translate(exception, cancellationToken);
        }
    }

    private void EnsureCatalogReady()
    {
        if (!_integration.IsConfigured)
            throw new LiteSpotifyBackendException(LiteSpotifyFailureReason.NotConfigured);
        var stored = ProbeCredential(CatalogCredentialTarget);
        if (stored == false)
            throw new LiteSpotifyBackendException(LiteSpotifyFailureReason.NotConnected);
        if (stored is null)
            throw new LiteSpotifyBackendException(LiteSpotifyFailureReason.Unknown);
    }

    private static LiteSpotifyContainerBackendResult FromOptionalItems(
        IReadOnlyList<MediaItem>? items) => items is null
        ? new([], Available: false)
        : new(items, Available: true);

    private static LiteSpotifyContainerBackendResult FromArtistTracks(
        SpotifyArtistTracksBatch batch) => batch.Failure is null
        ? new(batch.Items, Available: true, HasMore: batch.HasMore)
        : new([], Available: false);

    private static SpotifySettings ReadSettings(string statePath)
    {
        try
        {
            using var stream = new FileStream(
                statePath,
                FileMode.Open,
                FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            using var document = JsonDocument.Parse(stream);
            if (document.RootElement.ValueKind != JsonValueKind.Object
                || !document.RootElement.TryGetProperty("spotify", out var spotify)
                || spotify.ValueKind != JsonValueKind.Object)
            {
                return new SpotifySettings();
            }
            return JsonSerializer.Deserialize<SpotifySettings>(
                    spotify.GetRawText(), JsonOptions)
                ?? new SpotifySettings();
        }
        catch (IOException)
        {
            return new SpotifySettings();
        }
        catch (UnauthorizedAccessException)
        {
            return new SpotifySettings();
        }
        catch (JsonException)
        {
            // A damaged profile cannot be trusted as configured. Do not leak
            // parser details through the protocol and do not rewrite the file.
            return new SpotifySettings();
        }
    }

    private static LiteSpotifyBackendException Translate(
        Exception exception,
        CancellationToken cancellationToken)
    {
        if (exception is LiteSpotifyBackendException translated) return translated;
        var reason = exception switch
        {
            SpotifyApiException api when api.StatusCode == HttpStatusCode.TooManyRequests =>
                LiteSpotifyFailureReason.RateLimited,
            SpotifyApiException api when api.StatusCode is HttpStatusCode.Unauthorized
                or HttpStatusCode.Forbidden => LiteSpotifyFailureReason.AccessDenied,
            SpotifyApiException api when api.StatusCode == HttpStatusCode.NotFound =>
                LiteSpotifyFailureReason.NotFound,
            HttpRequestException => LiteSpotifyFailureReason.Network,
            TaskCanceledException when !cancellationToken.IsCancellationRequested =>
                LiteSpotifyFailureReason.Timeout,
            OperationCanceledException => LiteSpotifyFailureReason.Cancelled,
            InvalidOperationException invalid when invalid.Message.Contains(
                "logowania Spotify", StringComparison.OrdinalIgnoreCase) =>
                LiteSpotifyFailureReason.NotConnected,
            _ => LiteSpotifyFailureReason.Unknown
        };
        return new LiteSpotifyBackendException(reason, exception);
    }

    /// <summary>
    /// Existence-only credential probe. Unlike the legacy stores it does not
    /// deserialize, repair or delete anything, so account-status is genuinely
    /// read-only and cannot alter a damaged credential as a side effect.
    /// </summary>
    private static bool? ProbeCredential(string target)
    {
        if (!CredRead(target, CredentialTypeGeneric, 0, out var pointer))
        {
            var error = Marshal.GetLastWin32Error();
            return error == ErrorNotFound ? false : null;
        }
        CredFree(pointer);
        return true;
    }

    public void Dispose()
    {
        _api.Dispose();
        _integration.Dispose();
    }

    private const uint CredentialTypeGeneric = 1;
    private const int ErrorNotFound = 1168;

    [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredRead(
        string target,
        uint type,
        uint reservedFlag,
        out IntPtr credentialPointer);

    [DllImport("advapi32.dll")]
    private static extern void CredFree(IntPtr buffer);
}
