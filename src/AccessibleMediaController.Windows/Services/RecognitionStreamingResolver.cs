using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

internal interface IRecognitionStreamingResolver
{
    bool IsAvailable(RecognizedTrackStreamingService service);
    bool HasCachedMatch(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service);
    Task<RecognitionResolutionResult> ResolveAsync(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        CancellationToken cancellationToken);
}

internal sealed record RecognitionResolutionResult(
    RecognizedTrackStreamingService Service,
    MediaItem Track,
    MediaItem? Album,
    MediaItem? Artist,
    bool CacheChanged);

/// <summary>
/// Rozwiązuje wynik Shazama dopiero na jawne żądanie użytkownika. Trafione
/// identyfikatory i publiczne adresy zapisuje w rekordzie historii, więc
/// ponowne kopiowanie albo otwarcie nie odpytuje sieci drugi raz.
/// </summary>
internal sealed class RecognitionStreamingResolver(
    Func<RecognizedTrackStreamingService, bool> availability,
    Func<RecognizedTrackStreamingService, string, CancellationToken,
        Task<IReadOnlyList<MediaItem>>> search) : IRecognitionStreamingResolver
{
    public bool IsAvailable(RecognizedTrackStreamingService service) => availability(service);

    public bool HasCachedMatch(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service) => Match(entry, service) is not null;

    public async Task<RecognitionResolutionResult> ResolveAsync(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        CancellationToken cancellationToken)
    {
        if (TryFromCache(entry, service, out var cached)) return cached;
        if (!IsAvailable(service))
        {
            throw new InvalidOperationException(
                $"Usługa {RecognizedTrackStreamingServiceRules.GetLabel(service)} nie jest zalogowana. "
                + "Zaloguj usługę przez Ctrl+F5 albo wybierz inną pozycję pod strzałką w prawo.");
        }

        var query = string.Join(' ', new[] { entry.Artist, entry.Title }
            .Where(value => !string.IsNullOrWhiteSpace(value)));
        var results = await search(service, query, cancellationToken).ConfigureAwait(false);
        var track = RecognizedTrackMatchSelector.SelectBest(entry, results)
            ?? throw new InvalidOperationException(
                $"Nie znaleziono wystarczająco pewnego dopasowania w "
                + RecognizedTrackStreamingServiceRules.GetLabel(service) + ".");
        var resolved = CreateResult(entry, service, track, cacheChanged: true);
        Save(entry, service, resolved);
        return resolved;
    }

    private static bool TryFromCache(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        out RecognitionResolutionResult result)
    {
        var match = Match(entry, service);
        if (match is null
            || string.IsNullOrWhiteSpace(match.TrackExternalId)
            || !TryPublicUri(match.TrackPublicUri, out _))
        {
            result = null!;
            return false;
        }

        var track = CreateTrack(entry, service, match);
        var album = CreateAlbum(entry, service, match);
        var artist = CreateArtist(entry, service, match);
        result = new RecognitionResolutionResult(service, track, album, artist, CacheChanged: false);
        return true;
    }

    private static RecognitionResolutionResult CreateResult(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        MediaItem matchedTrack,
        bool cacheChanged)
    {
        var trackUri = matchedTrack.PublicUri ?? BuildPublicUri(
            service, MediaItemKind.Track, matchedTrack.ExternalId!);
        if (!TryPublicUri(trackUri, out _))
            throw new InvalidOperationException("Usługa nie zwróciła publicznego łącza do utworu.");

        var match = new RadioRecognizedTrackMatchSettings
        {
            TrackExternalId = matchedTrack.ExternalId!,
            TrackPublicUri = trackUri,
            AlbumExternalId = EmptyToNull(matchedTrack.RelatedAlbumExternalId),
            AlbumTitle = EmptyToNull(matchedTrack.RelatedAlbumTitle) ?? EmptyToNull(entry.Album),
            AlbumPublicUri = string.IsNullOrWhiteSpace(matchedTrack.RelatedAlbumExternalId)
                ? null
                : BuildPublicUri(service, MediaItemKind.Album, matchedTrack.RelatedAlbumExternalId),
            ArtistExternalId = EmptyToNull(matchedTrack.RelatedArtistExternalId),
            ArtistName = EmptyToNull(matchedTrack.RelatedArtistName)
                ?? EmptyToNull(matchedTrack.Artist)
                ?? EmptyToNull(entry.Artist),
            ArtistPublicUri = string.IsNullOrWhiteSpace(matchedTrack.RelatedArtistExternalId)
                ? null
                : BuildPublicUri(service, MediaItemKind.Artist, matchedTrack.RelatedArtistExternalId),
            ResolvedUtcTicks = DateTime.UtcNow.Ticks
        };
        var track = CreateTrack(entry, service, match);
        return new RecognitionResolutionResult(
            service,
            track,
            CreateAlbum(entry, service, match),
            CreateArtist(entry, service, match),
            cacheChanged);
    }

    private static MediaItem CreateTrack(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        RadioRecognizedTrackMatchSettings match) => new()
    {
        Id = StableId(service, MediaItemKind.Track, match.TrackExternalId),
        Kind = MediaItemKind.Track,
        Title = entry.Title,
        Artist = string.IsNullOrWhiteSpace(entry.Artist) ? match.ArtistName ?? string.Empty : entry.Artist,
        ExternalId = match.TrackExternalId,
        Source = Source(service, MediaItemKind.Track, match.TrackExternalId),
        PublicUri = match.TrackPublicUri,
        RelatedAlbumExternalId = match.AlbumExternalId,
        RelatedAlbumTitle = match.AlbumTitle,
        RelatedArtistExternalId = match.ArtistExternalId,
        RelatedArtistName = match.ArtistName,
        IsAvailable = true
    };

    private static MediaItem? CreateAlbum(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        RadioRecognizedTrackMatchSettings match)
    {
        if (string.IsNullOrWhiteSpace(match.AlbumExternalId)) return null;
        return new MediaItem
        {
            Id = StableId(service, MediaItemKind.Album, match.AlbumExternalId),
            Kind = MediaItemKind.Album,
            Title = match.AlbumTitle ?? entry.Album,
            Artist = match.ArtistName ?? entry.Artist,
            ExternalId = match.AlbumExternalId,
            Source = Source(service, MediaItemKind.Album, match.AlbumExternalId),
            PublicUri = match.AlbumPublicUri
                ?? BuildPublicUri(service, MediaItemKind.Album, match.AlbumExternalId),
            RelatedArtistExternalId = match.ArtistExternalId,
            RelatedArtistName = match.ArtistName,
            IsAvailable = true
        };
    }

    private static MediaItem? CreateArtist(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        RadioRecognizedTrackMatchSettings match)
    {
        if (string.IsNullOrWhiteSpace(match.ArtistExternalId)) return null;
        return new MediaItem
        {
            Id = StableId(service, MediaItemKind.Artist, match.ArtistExternalId),
            Kind = MediaItemKind.Artist,
            Title = match.ArtistName ?? entry.Artist,
            ExternalId = match.ArtistExternalId,
            Source = Source(service, MediaItemKind.Artist, match.ArtistExternalId),
            PublicUri = match.ArtistPublicUri
                ?? BuildPublicUri(service, MediaItemKind.Artist, match.ArtistExternalId),
            IsAvailable = true
        };
    }

    private static void Save(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service,
        RecognitionResolutionResult result)
    {
        var match = new RadioRecognizedTrackMatchSettings
        {
            TrackExternalId = result.Track.ExternalId!,
            TrackPublicUri = result.Track.PublicUri!,
            AlbumExternalId = result.Album?.ExternalId,
            AlbumTitle = result.Album?.Title,
            AlbumPublicUri = result.Album?.PublicUri,
            ArtistExternalId = result.Artist?.ExternalId,
            ArtistName = result.Artist?.Title,
            ArtistPublicUri = result.Artist?.PublicUri,
            ResolvedUtcTicks = DateTime.UtcNow.Ticks
        };
        if (service == RecognizedTrackStreamingService.Spotify) entry.SpotifyMatch = match;
        else entry.TidalMatch = match;
    }

    private static RadioRecognizedTrackMatchSettings? Match(
        RadioRecognizedTrackSettings entry,
        RecognizedTrackStreamingService service) => service switch
    {
        RecognizedTrackStreamingService.Spotify => entry.SpotifyMatch,
        RecognizedTrackStreamingService.Tidal => entry.TidalMatch,
        _ => null
    };

    private static string StableId(
        RecognizedTrackStreamingService service,
        MediaItemKind kind,
        string externalId) => $"recognized:{service}:{kind}:{externalId}";

    private static string Source(
        RecognizedTrackStreamingService service,
        MediaItemKind kind,
        string externalId) => service switch
    {
        RecognizedTrackStreamingService.Spotify =>
            $"spotify:{KindSegment(kind)}:{externalId}",
        RecognizedTrackStreamingService.Tidal => $"tidal:{externalId}",
        _ => externalId
    };

    private static string BuildPublicUri(
        RecognizedTrackStreamingService service,
        MediaItemKind kind,
        string externalId)
    {
        var id = service == RecognizedTrackStreamingService.Tidal
            ? externalId[(externalId.IndexOf(':') + 1)..]
            : externalId;
        return service switch
        {
            RecognizedTrackStreamingService.Spotify =>
                $"https://open.spotify.com/{KindSegment(kind)}/{Uri.EscapeDataString(id)}",
            RecognizedTrackStreamingService.Tidal =>
                $"https://tidal.com/browse/{KindSegment(kind)}/{Uri.EscapeDataString(id)}",
            _ => string.Empty
        };
    }

    private static string KindSegment(MediaItemKind kind) => kind switch
    {
        MediaItemKind.Track => "track",
        MediaItemKind.Album => "album",
        MediaItemKind.Artist => "artist",
        _ => "track"
    };

    private static bool TryPublicUri(string? value, out Uri? uri) =>
        Uri.TryCreate(value, UriKind.Absolute, out uri)
        && uri.Scheme is "http" or "https";

    private static string? EmptyToNull(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}
