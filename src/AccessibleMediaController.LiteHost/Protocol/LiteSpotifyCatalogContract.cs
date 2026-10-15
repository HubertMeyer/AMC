using System.Text.Json;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.LiteHost.Protocol;

/// <summary>
/// Read-only Spotify contract for the wx frontend. Credentials and playback
/// handles never cross JSON-lines. IDs are model fields; every item also has
/// an explicit, user-facing accessible label which never contains an ID or URI.
/// </summary>
public static class LiteSpotifyCatalogContract
{
    public const string SessionId = "spotify";
    public const string CapabilitiesOperation = "spotify.capabilities";
    public const string AccountStatusOperation = "spotify.accountStatus";
    public const string CollectionRootOperation = "spotify.collectionRoot";
    public const string CollectionViewOperation = "spotify.collectionView";
    public const string ContainerItemsOperation = "spotify.containerItems";
    public const string SearchOperation = "spotify.search";

    private const int MaximumQueryLength = 200;
    private const int MaximumLabelPartLength = 300;
    private const int MaximumExternalIdLength = 128;

    private static readonly IReadOnlyDictionary<string, MediaItemKind> ContainerKinds =
        new Dictionary<string, MediaItemKind>(StringComparer.OrdinalIgnoreCase)
        {
            ["album"] = MediaItemKind.Album,
            ["artist"] = MediaItemKind.Artist,
            ["playlist"] = MediaItemKind.Playlist,
            ["podcast"] = MediaItemKind.Podcast
        };

    private static readonly IReadOnlyDictionary<string, string> ArtistSections =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["albums"] = "albums",
            ["tracks"] = "tracks"
        };

    public static LiteSpotifyCapabilitiesResult CreateCapabilities() => new(
        SessionId,
        ReadOnly: true,
        OneSession: true,
        AccountStatus: true,
        CollectionRoot: true,
        CollectionRead: true,
        ContainerBrowse: true,
        CatalogSearch: true,
        CollectionWrite: false,
        Login: false,
        Playback: true,
        "Katalog i odtwarzanie Spotify mają osobne stany połączenia. "
            + "Katalog pozostaje tylko do odczytu, a dźwięk odtwarza natywna sesja Librespot. "
            + "Ta warstwa nie loguje i nie zapisuje biblioteki.");

    public static LiteSpotifyAccountStatusResult CreateAccountStatus(
        LiteSpotifyAccountProbe probe)
    {
        ArgumentNullException.ThrowIfNull(probe);
        var catalog = !probe.CatalogConfigured
            ? new LiteSpotifyConnectionStatus(
                "notConfigured", false, false,
                "Katalog Spotify nie jest skonfigurowany.",
                null, "nieznany")
            : probe.CatalogConnected switch
            {
                true => new LiteSpotifyConnectionStatus(
                    "connected", true, true,
                    string.IsNullOrWhiteSpace(probe.AccountDisplayName)
                        ? "Katalog Spotify jest połączony."
                        : $"Katalog Spotify jest połączony: {CleanText(probe.AccountDisplayName)}.",
                    NullIfEmpty(CleanText(probe.AccountDisplayName)),
                    PlanLabel(probe.AccountProduct)),
                false => new LiteSpotifyConnectionStatus(
                    "disconnected", true, false,
                    "Katalog Spotify nie jest połączony.",
                    null, "nieznany"),
                null => new LiteSpotifyConnectionStatus(
                    "unavailable", true, false,
                    "Nie można teraz sprawdzić połączenia katalogu Spotify.",
                    null, "nieznany")
            };

        var playback = probe.PlaybackConnected switch
        {
            true => new LiteSpotifyConnectionStatus(
                "connected", true, true,
                "Konto odtwarzania Spotify jest zapisane i gotowe dla natywnej sesji.",
                null, "nieznany"),
            false => new LiteSpotifyConnectionStatus(
                "disconnected", true, false,
                "Konto odtwarzania Spotify nie jest połączone.",
                null, "nieznany"),
            null => new LiteSpotifyConnectionStatus(
                "unavailable", true, false,
                "Nie można teraz sprawdzić połączenia odtwarzania Spotify.",
                null, "nieznany")
        };

        return new LiteSpotifyAccountStatusResult(SessionId, catalog, playback);
    }

    public static LiteSpotifyCollectionRootResult CreateCollectionRoot() => new(
        "Biblioteka Spotify",
        [
            new("liked", "Polubione utwory"),
            new("albums", "Albumy"),
            new("artists", "Wykonawcy"),
            new("playlists", "Playlisty"),
            new("podcasts", "Podcasty"),
            new("episodes", "Zapisane odcinki")
        ]);

    public static string ReadCollectionView(JsonElement args)
    {
        var view = LiteArgs.RequireText(args, "view").Trim().ToLowerInvariant();
        return view is "liked" or "albums" or "artists" or "playlists"
            or "podcasts" or "episodes"
            ? view
            : throw new LiteRequestException("Nieznany widok kolekcji Spotify.");
    }

    public static string ReadSearchQuery(JsonElement args)
    {
        var query = LiteArgs.RequireText(args, "query").Trim();
        if (query.Length == 0)
            throw new LiteRequestException("Wpisz tekst do wyszukania w Spotify.");
        if (query.Length > MaximumQueryLength)
            throw new LiteRequestException("Tekst wyszukiwania Spotify jest zbyt długi.");
        return query;
    }

    public static LiteSpotifyContainerRequest ReadContainerRequest(JsonElement args)
    {
        var title = CleanText(LiteArgs.RequireText(args, "title"));
        var kindText = LiteArgs.RequireText(args, "kind").Trim();
        var externalId = LiteArgs.RequireText(args, "externalId").Trim();
        if (!ContainerKinds.TryGetValue(kindText, out var kind))
            throw new LiteRequestException("Ten rodzaj elementu Spotify nie jest kontenerem.");
        if (!TryNormalizeExternalId(externalId, kind, out var normalizedId))
            throw new LiteRequestException("Element Spotify ma nieprawidłową tożsamość katalogową.");

        string? artistSection = null;
        if (LiteArgs.ReadText(args, "artistSection") is { } requestedSection)
        {
            if (kind != MediaItemKind.Artist
                || !ArtistSections.TryGetValue(requestedSection.Trim(), out artistSection))
            {
                throw new LiteRequestException(
                    "Wybrana kategoria nie należy do wykonawcy Spotify.");
            }
        }

        return new LiteSpotifyContainerRequest(
            kind,
            normalizedId,
            title,
            CleanText(LiteArgs.ReadText(args, "artist") ?? string.Empty),
            artistSection);
    }

    public static LiteSpotifyItemsResult CreateSearchResult(IReadOnlyList<MediaItem> items) =>
        CreateItemsResult("Wyniki wyszukiwania Spotify", items);

    public static LiteSpotifyItemsResult CreateCollectionViewResult(
        string view,
        IReadOnlyList<MediaItem> items,
        string warning = "")
    {
        ArgumentNullException.ThrowIfNull(items);
        var filtered = view switch
        {
            "liked" => items.Where(item => item.Kind == MediaItemKind.Track && item.IsFavorite),
            "albums" => items.Where(item => item.Kind == MediaItemKind.Album && item.IsInLibrary),
            "artists" => items.Where(item => item.Kind == MediaItemKind.Artist && item.IsInLibrary),
            "playlists" => items.Where(item => item.Kind == MediaItemKind.Playlist && item.IsInLibrary),
            "podcasts" => items.Where(item => item.Kind == MediaItemKind.Podcast && item.IsInLibrary),
            "episodes" => items.Where(item => item.Kind == MediaItemKind.Episode && item.IsFavorite),
            _ => throw new LiteRequestException("Nieznany widok kolekcji Spotify.")
        };
        var heading = view switch
        {
            "liked" => "Polubione utwory Spotify",
            "albums" => "Albumy Spotify",
            "artists" => "Wykonawcy Spotify",
            "playlists" => "Playlisty Spotify",
            "podcasts" => "Podcasty Spotify",
            "episodes" => "Zapisane odcinki Spotify",
            _ => "Biblioteka Spotify"
        };
        return CreateItemsResult(heading, filtered.ToArray(), warning);
    }

    public static LiteSpotifyItemsResult CreateContainerResult(
        LiteSpotifyContainerRequest request,
        IReadOnlyList<MediaItem> items,
        bool available,
        bool hasMore = false)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentNullException.ThrowIfNull(items);
        var heading = request.Kind switch
        {
            MediaItemKind.Album => $"Album, {request.Title}",
            MediaItemKind.Playlist => $"Playlista, {request.Title}",
            MediaItemKind.Podcast => $"Podcast, {request.Title}",
            MediaItemKind.Artist when request.ArtistSection == "tracks" =>
                $"Utwory wykonawcy, {request.Title}",
            MediaItemKind.Artist => $"Albumy wykonawcy, {request.Title}",
            _ => "Spotify"
        };
        var warning = available
            ? string.Empty
            : "Spotify nie udostępnił zawartości tego elementu.";
        return CreateItemsResult(
            heading,
            items,
            warning,
            available,
            hasMore,
            preserveOccurrences: true);
    }

    public static string FailureMessage(LiteSpotifyFailureReason reason, string operation) => reason switch
    {
        LiteSpotifyFailureReason.NotConfigured =>
            "Katalog Spotify nie jest skonfigurowany. Otwórz ustawienia konta Spotify.",
        LiteSpotifyFailureReason.NotConnected =>
            "Katalog Spotify nie jest połączony. Otwórz ustawienia konta Spotify.",
        LiteSpotifyFailureReason.AccessDenied =>
            "Spotify odmówił dostępu do katalogu. Sprawdź połączenie konta Spotify.",
        LiteSpotifyFailureReason.NotFound =>
            "Spotify nie znalazł wybranych danych.",
        LiteSpotifyFailureReason.RateLimited =>
            "Spotify chwilowo ograniczył liczbę zapytań. Spróbuj ponownie później.",
        LiteSpotifyFailureReason.Network =>
            "Brak połączenia ze Spotify.",
        LiteSpotifyFailureReason.Timeout =>
            "Spotify nie odpowiedział w wyznaczonym czasie.",
        LiteSpotifyFailureReason.Cancelled =>
            "Operację Spotify anulowano.",
        _ => operation switch
        {
            SearchOperation => "Nie udało się wyszukać w Spotify.",
            ContainerItemsOperation => "Nie udało się otworzyć zawartości Spotify.",
            CollectionViewOperation => "Nie udało się odświeżyć kolekcji Spotify.",
            _ => "Nie udało się odczytać danych Spotify."
        }
    };

    private static LiteSpotifyItemsResult CreateItemsResult(
        string heading,
        IReadOnlyList<MediaItem> items,
        string warning = "",
        bool available = true,
        bool hasMore = false,
        bool preserveOccurrences = false)
    {
        var supported = items.Where(IsSupportedItem).ToArray();
        var visible = preserveOccurrences
            ? supported.Select((item, index) =>
                    LiteSpotifyCatalogItem.FromMediaItem(item, index))
                .ToArray()
            : supported.Select(item => LiteSpotifyCatalogItem.FromMediaItem(item))
                .GroupBy(item => $"{item.Kind}:{item.ExternalId}", StringComparer.Ordinal)
                .Select(group => group.First())
                .ToArray();
        return new LiteSpotifyItemsResult(
            CleanText(heading), visible, CleanText(warning), available, hasMore);
    }

    private static bool IsSupportedItem(MediaItem item) =>
        !string.IsNullOrWhiteSpace(item.Title)
        && TryNormalizeExternalId(item.ExternalId, item.Kind, out _)
        && item.Kind is MediaItemKind.Track or MediaItemKind.Album
            or MediaItemKind.Artist or MediaItemKind.Playlist
            or MediaItemKind.Podcast or MediaItemKind.Episode;

    internal static bool TryNormalizeExternalId(
        string? value,
        MediaItemKind kind,
        out string normalized)
    {
        normalized = string.Empty;
        if (string.IsNullOrWhiteSpace(value)) return false;
        var candidate = value.Trim();
        var expectedType = ServiceType(kind);
        if (expectedType is null) return false;
        if (candidate.StartsWith("spotify:", StringComparison.OrdinalIgnoreCase))
        {
            var parts = candidate.Split(':', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length != 3
                || !string.Equals(parts[1], expectedType, StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }
            candidate = parts[2];
        }
        if (candidate.Length is 0 or > MaximumExternalIdLength
            || !candidate.All(char.IsLetterOrDigit))
        {
            return false;
        }
        normalized = candidate;
        return true;
    }

    internal static string? ServiceType(MediaItemKind kind) => kind switch
    {
        MediaItemKind.Track => "track",
        MediaItemKind.Album => "album",
        MediaItemKind.Artist => "artist",
        MediaItemKind.Playlist => "playlist",
        MediaItemKind.Podcast => "show",
        MediaItemKind.Episode => "episode",
        _ => null
    };

    internal static string CleanText(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return string.Empty;
        var clean = new string(value
            .Where(character => !char.IsControl(character))
            .ToArray()).Trim();
        if (clean.Length > MaximumLabelPartLength)
            clean = clean[..MaximumLabelPartLength].TrimEnd() + "…";
        return clean;
    }

    private static string? NullIfEmpty(string value) => value.Length == 0 ? null : value;

    private static string PlanLabel(string? product) => product?.Trim().ToLowerInvariant() switch
    {
        "premium" => "Premium",
        "free" or "open" => "bezpłatne",
        _ => "nieznany"
    };

    internal static string? PublicUri(MediaItem item)
    {
        if (!Uri.TryCreate(item.PublicUri, UriKind.Absolute, out var uri)
            || uri.Scheme != Uri.UriSchemeHttps
            || !string.Equals(uri.Host, "open.spotify.com", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }
        return uri.AbsoluteUri;
    }
}

public enum LiteSpotifyFailureReason
{
    Unknown,
    NotConfigured,
    NotConnected,
    AccessDenied,
    NotFound,
    RateLimited,
    Network,
    Timeout,
    Cancelled
}

public sealed record LiteSpotifyCapabilitiesResult(
    [property: JsonPropertyName("sessionId")] string SessionId,
    [property: JsonPropertyName("readOnly")] bool ReadOnly,
    [property: JsonPropertyName("oneSession")] bool OneSession,
    [property: JsonPropertyName("accountStatus")] bool AccountStatus,
    [property: JsonPropertyName("collectionRoot")] bool CollectionRoot,
    [property: JsonPropertyName("collectionRead")] bool CollectionRead,
    [property: JsonPropertyName("containerBrowse")] bool ContainerBrowse,
    [property: JsonPropertyName("catalogSearch")] bool CatalogSearch,
    [property: JsonPropertyName("collectionWrite")] bool CollectionWrite,
    [property: JsonPropertyName("login")] bool Login,
    [property: JsonPropertyName("playback")] bool Playback,
    [property: JsonPropertyName("message")] string Message);

public sealed record LiteSpotifyAccountProbe(
    bool CatalogConfigured,
    bool? CatalogConnected,
    string AccountDisplayName,
    string AccountProduct,
    bool? PlaybackConnected);

public sealed record LiteSpotifyAccountStatusResult(
    [property: JsonPropertyName("sessionId")] string SessionId,
    [property: JsonPropertyName("catalog")] LiteSpotifyConnectionStatus Catalog,
    [property: JsonPropertyName("playback")] LiteSpotifyConnectionStatus Playback);

public sealed record LiteSpotifyConnectionStatus(
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("configured")] bool Configured,
    [property: JsonPropertyName("connected")] bool Connected,
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("accountDisplayName")] string? AccountDisplayName,
    [property: JsonPropertyName("accountPlan")] string AccountPlan);

public sealed record LiteSpotifyCollectionRootResult(
    [property: JsonPropertyName("heading")] string Heading,
    [property: JsonPropertyName("views")] IReadOnlyList<LiteSpotifyCollectionRootItem> Views);

public sealed record LiteSpotifyCollectionRootItem(
    [property: JsonPropertyName("view")] string View,
    [property: JsonPropertyName("label")] string Label);

public sealed record LiteSpotifyContainerRequest(
    MediaItemKind Kind,
    string ExternalId,
    string Title,
    string Artist,
    string? ArtistSection);

public sealed record LiteSpotifyItemsResult(
    [property: JsonPropertyName("heading")] string Heading,
    [property: JsonPropertyName("items")] IReadOnlyList<LiteSpotifyCatalogItem> Items,
    [property: JsonPropertyName("warning")] string Warning,
    [property: JsonPropertyName("available")] bool Available,
    [property: JsonPropertyName("hasMore")] bool HasMore);

public sealed record LiteSpotifyCatalogItem(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("externalId")] string ExternalId,
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("artist")] string Artist,
    [property: JsonPropertyName("kind")] string Kind,
    [property: JsonPropertyName("accessibleLabel")] string AccessibleLabel,
    [property: JsonPropertyName("durationTicks")] long DurationTicks,
    [property: JsonPropertyName("publicUri")] string? PublicUri,
    [property: JsonPropertyName("relatedAlbumExternalId")] string? RelatedAlbumExternalId,
    [property: JsonPropertyName("relatedAlbumTitle")] string? RelatedAlbumTitle,
    [property: JsonPropertyName("relatedArtistExternalId")] string? RelatedArtistExternalId,
    [property: JsonPropertyName("relatedArtistName")] string? RelatedArtistName,
    [property: JsonPropertyName("collectionAddedUtcTicks")] long? CollectionAddedUtcTicks,
    [property: JsonPropertyName("isFavorite")] bool IsFavorite,
    [property: JsonPropertyName("isInLibrary")] bool IsInLibrary,
    [property: JsonPropertyName("isAvailable")] bool IsAvailable)
{
    public static LiteSpotifyCatalogItem FromMediaItem(
        MediaItem item,
        int? occurrenceIndex = null)
    {
        if (!LiteSpotifyCatalogContract.TryNormalizeExternalId(
                item.ExternalId, item.Kind, out var externalId))
        {
            throw new ArgumentException("Nieprawidłowy element Spotify.", nameof(item));
        }
        var serviceType = LiteSpotifyCatalogContract.ServiceType(item.Kind)!;
        var title = LiteSpotifyCatalogContract.CleanText(item.Title);
        var artist = LiteSpotifyCatalogContract.CleanText(item.Artist);
        var kindLabel = item.Kind switch
        {
            MediaItemKind.Track => "utwór",
            MediaItemKind.Album => "album",
            MediaItemKind.Artist => "wykonawca",
            MediaItemKind.Playlist => "playlista",
            MediaItemKind.Podcast => "podcast",
            MediaItemKind.Episode => "odcinek",
            _ => "element"
        };
        var label = artist.Length == 0
            ? $"{title}, {kindLabel}"
            : $"{title}, {artist}, {kindLabel}";
        if (!item.IsAvailable) label += ", niedostępny";
        var id = $"spotify:{serviceType}:{externalId}";
        if (occurrenceIndex is { } index) id += $":occurrence:{index}";
        return new LiteSpotifyCatalogItem(
            id,
            externalId,
            title,
            artist,
            item.Kind.ToString().ToLowerInvariant(),
            label,
            Math.Max(0, item.Duration.Ticks),
            LiteSpotifyCatalogContract.PublicUri(item),
            NormalizeRelated(item.RelatedAlbumExternalId),
            NullIfEmpty(LiteSpotifyCatalogContract.CleanText(item.RelatedAlbumTitle)),
            NormalizeRelated(item.RelatedArtistExternalId),
            NullIfEmpty(LiteSpotifyCatalogContract.CleanText(item.RelatedArtistName)),
            item.CollectionAddedUtcTicks,
            item.IsFavorite,
            item.IsInLibrary,
            item.IsAvailable);
    }

    private static string? NormalizeRelated(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return null;
        var candidate = value.Trim();
        if (candidate.StartsWith("spotify:", StringComparison.OrdinalIgnoreCase))
        {
            var parts = candidate.Split(':', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length != 3) return null;
            candidate = parts[2];
        }
        return candidate.Length is > 0 and <= 128 && candidate.All(char.IsLetterOrDigit)
            ? candidate
            : null;
    }

    private static string? NullIfEmpty(string value) => value.Length == 0 ? null : value;
}
