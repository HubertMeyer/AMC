using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.AppleMusic;

public sealed class AppleMusicApiException(
    string message,
    HttpStatusCode statusCode,
    TimeSpan? retryAfter = null) : InvalidOperationException(message)
{
    public HttpStatusCode StatusCode { get; } = statusCode;
    public TimeSpan? RetryAfter { get; } = retryAfter;
    public bool IsAuthorizationFailure => StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden;
}

/// <summary>
/// Pierwsza, niezalezna od UI warstwa Apple Music dla AMC. Przyjmuje gotowy
/// developer token i Music User Token; nie generuje JWT i nie zapisuje klucza
/// prywatnego Apple. Logowanie i odtwarzanie nalezy do MusicKit on the Web.
/// </summary>
public sealed class AppleMusicApiClient(HttpClient? httpClient = null) : IDisposable
{
    private static readonly Uri ApiBaseAddress = new("https://api.music.apple.com/v1/");
    private readonly HttpClient http = httpClient ?? new HttpClient
    {
        BaseAddress = ApiBaseAddress,
        Timeout = TimeSpan.FromSeconds(30)
    };
    private readonly bool ownsHttpClient = httpClient is null;

    public async Task<IReadOnlyList<MediaItem>> SearchCatalogAsync(
        string developerToken,
        string storefront,
        string query,
        CancellationToken cancellationToken = default)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        storefront = NormalizeStorefront(storefront);
        if (string.IsNullOrWhiteSpace(query)) return [];
        var address = $"catalog/{storefront}/search?term={Escape(query.Trim())}"
            + "&types=songs,albums,artists,playlists,music-videos&limit=25";
        using var document = await GetAsync(address, developerToken, null, cancellationToken).ConfigureAwait(false);
        return MapResources(document.RootElement);
    }

    public async Task<IReadOnlyList<MediaItem>> GetLibraryAsync(
        string developerToken,
        string musicUserToken,
        CancellationToken cancellationToken = default)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        EnsureToken(musicUserToken, "Konto Apple Music nie jest zalogowane.");
        var items = new List<MediaItem>();
        foreach (var resource in new[] { "songs", "albums", "artists", "playlists", "music-videos" })
        {
            items.AddRange(await GetPagedResourcesAsync(
                    $"me/library/{resource}?limit=100",
                    developerToken,
                    musicUserToken,
                    libraryItems: true,
                    cancellationToken)
                .ConfigureAwait(false));
        }
        return items.DistinctBy(item => item.Id, StringComparer.Ordinal).ToArray();
    }

    public async Task<IReadOnlyList<MediaItem>> GetContainerItemsAsync(
        string developerToken,
        string storefront,
        MediaItem container,
        ArtistBrowseSection? artistSection = null,
        CancellationToken cancellationToken = default,
        string? musicUserToken = null)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        storefront = NormalizeStorefront(storefront);
        if (!TryParseExternalId(container.ExternalId, out var type, out var id))
            throw new InvalidOperationException("Element nie ma identyfikatora katalogu Apple Music.");

        var address = type switch
        {
            "albums" => $"catalog/{storefront}/albums/{Escape(id)}/tracks?limit=300",
            "playlists" => $"catalog/{storefront}/playlists/{Escape(id)}/tracks?limit=300",
            "artists" when artistSection == ArtistBrowseSection.Tracks =>
                $"catalog/{storefront}/artists/{Escape(id)}/view/top-songs?limit=100&with=attributes",
            "artists" when artistSection == ArtistBrowseSection.SimilarArtists =>
                $"catalog/{storefront}/artists/{Escape(id)}/view/similar-artists?limit=100&with=attributes",
            "artists" when artistSection is null or ArtistBrowseSection.Albums =>
                $"catalog/{storefront}/artists/{Escape(id)}/view/full-albums?limit=100&with=attributes",
            "library-albums" => $"me/library/albums/{Escape(id)}/tracks?limit=300",
            "library-playlists" => $"me/library/playlists/{Escape(id)}/tracks?limit=300",
            "library-artists" when artistSection is null or ArtistBrowseSection.Albums =>
                $"me/library/artists/{Escape(id)}/albums?limit=100",
            _ => throw new InvalidOperationException("Tego elementu Apple Music nie można otworzyć jako kontenera.")
        };
        var libraryContainer = type.StartsWith("library-", StringComparison.Ordinal);
        if (libraryContainer)
            EnsureToken(musicUserToken ?? string.Empty, "Konto Apple Music nie jest zalogowane.");
        var items = (await GetPagedResourcesAsync(
                address,
                developerToken,
                libraryContainer ? musicUserToken : null,
                libraryItems: libraryContainer,
                cancellationToken)
            .ConfigureAwait(false)).ToArray();
        foreach (var item in items)
        {
            if (type is "albums" or "library-albums")
            {
                item.RelatedAlbumExternalId ??= container.ExternalId;
                item.RelatedAlbumTitle ??= container.Title;
            }
            if (type is "artists" or "library-artists")
            {
                item.RelatedArtistExternalId ??= container.ExternalId;
                item.RelatedArtistName ??= container.Title;
            }
        }
        return items;
    }

    public Task AddToLibraryAsync(
        string developerToken,
        string musicUserToken,
        IReadOnlyList<MediaItem> items,
        CancellationToken cancellationToken = default) =>
        SendIdMutationAsync("me/library", developerToken, musicUserToken, items,
            AppleMusicCapabilities.CanAddToLibrary, cancellationToken);

    public Task AddToFavoritesAsync(
        string developerToken,
        string musicUserToken,
        IReadOnlyList<MediaItem> items,
        CancellationToken cancellationToken = default) =>
        SendIdMutationAsync("me/favorites", developerToken, musicUserToken, items,
            AppleMusicCapabilities.CanAddToFavorites, cancellationToken);

    public async Task<MediaItem> CreatePlaylistAsync(
        string developerToken,
        string musicUserToken,
        string name,
        string? description = null,
        CancellationToken cancellationToken = default)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        EnsureToken(musicUserToken, "Konto Apple Music nie jest zalogowane.");
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Nazwa playlisty nie może być pusta.", nameof(name));
        using var request = CreateRequest(HttpMethod.Post, "me/library/playlists", developerToken, musicUserToken);
        request.Content = JsonContent.Create(new
        {
            attributes = new
            {
                name = name.Trim(),
                description = description?.Trim() ?? string.Empty,
                isPublic = false
            }
        });
        using var response = await SendAsync(request, cancellationToken).ConfigureAwait(false);
        await EnsureSuccessAsync(response, cancellationToken).ConfigureAwait(false);
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken).ConfigureAwait(false);
        return MapResources(document.RootElement, libraryItems: true).FirstOrDefault()
            ?? throw new InvalidOperationException("Apple Music utworzył playlistę, ale nie zwrócił jej danych.");
    }

    public async Task AddTracksToPlaylistAsync(
        string developerToken,
        string musicUserToken,
        MediaItem playlist,
        IReadOnlyList<MediaItem> tracks,
        CancellationToken cancellationToken = default)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        EnsureToken(musicUserToken, "Konto Apple Music nie jest zalogowane.");
        if (!TryParseExternalId(playlist.ExternalId, out var playlistType, out var playlistId)
            || playlistType != "library-playlists")
            throw new InvalidOperationException("Wybrany element nie jest edytowalną playlistą Apple Music.");
        var data = tracks.Select(ParsePlaylistTrack).ToArray();
        if (data.Length == 0)
            throw new InvalidOperationException("Brak utworów do dodania do playlisty Apple Music.");
        using var request = CreateRequest(
            HttpMethod.Post,
            $"me/library/playlists/{Escape(playlistId)}/tracks",
            developerToken,
            musicUserToken);
        request.Content = JsonContent.Create(new { data });
        using var response = await SendAsync(request, cancellationToken).ConfigureAwait(false);
        await EnsureSuccessAsync(response, cancellationToken).ConfigureAwait(false);
    }

    private async Task SendIdMutationAsync(
        string address,
        string developerToken,
        string musicUserToken,
        IReadOnlyList<MediaItem> items,
        Func<MediaItemKind, bool> capability,
        CancellationToken cancellationToken)
    {
        EnsureToken(developerToken, "Brak tokenu deweloperskiego Apple Music.");
        EnsureToken(musicUserToken, "Konto Apple Music nie jest zalogowane.");
        if (items.Count == 0) throw new InvalidOperationException("Brak elementów do zmiany w Apple Music.");
        if (items.Any(item => !capability(item.Kind)))
            throw new InvalidOperationException("Co najmniej jeden rodzaj elementu nie obsługuje tej operacji w Apple Music.");
        var resources = items.Select(ParseCatalogResource).ToArray();
        var query = string.Join("&", resources
            .GroupBy(resource => resource.Type, StringComparer.Ordinal)
            .Select(group => $"ids[{group.Key}]={string.Join(',', group.Select(resource => Escape(resource.Id)))}"));
        using var request = CreateRequest(HttpMethod.Post, $"{address}?{query}", developerToken, musicUserToken);
        request.Content = new ByteArrayContent([]);
        using var response = await SendAsync(request, cancellationToken).ConfigureAwait(false);
        await EnsureSuccessAsync(response, cancellationToken).ConfigureAwait(false);
    }

    private async Task<JsonDocument> GetAsync(
        string address,
        string developerToken,
        string? musicUserToken,
        CancellationToken cancellationToken)
    {
        using var request = CreateRequest(HttpMethod.Get, address, developerToken, musicUserToken);
        using var response = await SendAsync(request, cancellationToken).ConfigureAwait(false);
        await EnsureSuccessAsync(response, cancellationToken).ConfigureAwait(false);
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        return await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    private async Task<IReadOnlyList<MediaItem>> GetPagedResourcesAsync(
        string firstAddress,
        string developerToken,
        string? musicUserToken,
        bool libraryItems,
        CancellationToken cancellationToken)
    {
        var result = new List<MediaItem>();
        string? address = firstAddress;
        var visited = new HashSet<string>(StringComparer.Ordinal);
        while (!string.IsNullOrWhiteSpace(address) && visited.Add(address))
        {
            cancellationToken.ThrowIfCancellationRequested();
            using var document = await GetAsync(
                    address,
                    developerToken,
                    musicUserToken,
                    cancellationToken)
                .ConfigureAwait(false);
            result.AddRange(MapResources(document.RootElement, libraryItems));
            address = document.RootElement.TryGetProperty("next", out var next)
                && next.ValueKind == JsonValueKind.String
                ? next.GetString()
                : null;
        }
        return result;
    }

    private HttpRequestMessage CreateRequest(
        HttpMethod method,
        string address,
        string developerToken,
        string? musicUserToken)
    {
        var request = new HttpRequestMessage(method, ResolveAddress(address));
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", developerToken.Trim());
        if (!string.IsNullOrWhiteSpace(musicUserToken))
            request.Headers.TryAddWithoutValidation("Music-User-Token", musicUserToken.Trim());
        return request;
    }

    private Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
        http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

    private static async Task EnsureSuccessAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode) return;
        var detail = string.Empty;
        try
        {
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken).ConfigureAwait(false);
            if (document.RootElement.TryGetProperty("errors", out var errors)
                && errors.ValueKind == JsonValueKind.Array && errors.GetArrayLength() > 0)
                detail = FirstString(errors[0], "detail", "title", "code") ?? string.Empty;
        }
        catch (JsonException)
        {
        }
        var message = response.StatusCode switch
        {
            HttpStatusCode.Unauthorized => "Token deweloperski Apple Music jest nieprawidłowy albo wygasł.",
            HttpStatusCode.Forbidden => "Apple Music nie udzielił dostępu do danych tego konta. Zaloguj konto ponownie.",
            HttpStatusCode.NotFound => "Element nie jest dostępny w tym katalogu Apple Music.",
            HttpStatusCode.TooManyRequests => "Apple Music ograniczył liczbę zapytań. Spróbuj ponownie później.",
            _ => $"Apple Music zwrócił błąd HTTP {(int)response.StatusCode}."
        };
        if (detail.Length > 0) message += $" {detail}";
        throw new AppleMusicApiException(message, response.StatusCode, response.Headers.RetryAfter?.Delta);
    }

    internal static IReadOnlyList<MediaItem> MapResources(JsonElement root, bool libraryItems = false)
    {
        var mapped = new List<MediaItem>();
        foreach (var resource in EnumerateResources(root))
        {
            if (!TryIdentity(resource, out var type, out var id)
                || !resource.TryGetProperty("attributes", out var attributes)) continue;
            var kind = KindForType(type);
            var title = FirstString(attributes, "name", "title");
            if (kind is null || string.IsNullOrWhiteSpace(title)) continue;
            var artist = FirstString(attributes, "artistName") ?? string.Empty;
            var (playableType, playableId) = ResolvePreferredIdentity(
                type,
                id,
                kind.Value,
                attributes);
            var externalId = $"{playableType}:{playableId}";
            var duration = attributes.TryGetProperty("durationInMillis", out var durationValue)
                && durationValue.TryGetInt64(out var milliseconds)
                    ? TimeSpan.FromMilliseconds(Math.Max(0, milliseconds))
                    : TimeSpan.Zero;
            mapped.Add(new MediaItem
            {
                Id = $"appleMusic:{externalId}",
                ExternalId = externalId,
                Title = title,
                Artist = artist,
                Kind = kind.Value,
                Duration = duration,
                Source = $"applemusic:{externalId}",
                PublicUri = FirstString(attributes, "url"),
                RelatedAlbumExternalId = kind == MediaItemKind.Album
                    ? externalId : FirstRelationshipId(resource, "albums"),
                RelatedAlbumTitle = kind == MediaItemKind.Album
                    ? title : FirstString(attributes, "albumName"),
                RelatedArtistExternalId = kind == MediaItemKind.Artist
                    ? externalId : FirstRelationshipId(resource, "artists"),
                RelatedArtistName = kind == MediaItemKind.Artist ? title : artist,
                IsFavorite = TryBoolean(attributes, "isFavorite"),
                IsInLibrary = libraryItems || type.StartsWith("library-", StringComparison.Ordinal)
            });
        }
        return mapped.DistinctBy(item => item.Id, StringComparer.Ordinal).ToArray();
    }

    private static IEnumerable<JsonElement> EnumerateResources(JsonElement root)
    {
        if (root.TryGetProperty("results", out var results) && results.ValueKind == JsonValueKind.Object)
        {
            foreach (var group in results.EnumerateObject())
                foreach (var resource in DataResources(group.Value)) yield return resource;
            yield break;
        }
        foreach (var resource in DataResources(root)) yield return resource;
    }

    private static IEnumerable<JsonElement> DataResources(JsonElement holder)
    {
        if (!holder.TryGetProperty("data", out var data)) yield break;
        if (data.ValueKind == JsonValueKind.Array)
            foreach (var resource in data.EnumerateArray()) yield return resource;
        else if (data.ValueKind == JsonValueKind.Object) yield return data;
    }

    private static MediaItemKind? KindForType(string type) => type switch
    {
        "songs" or "library-songs" => MediaItemKind.Track,
        "albums" or "library-albums" => MediaItemKind.Album,
        "artists" or "library-artists" => MediaItemKind.Artist,
        "playlists" or "library-playlists" => MediaItemKind.Playlist,
        "music-videos" or "library-music-videos" => MediaItemKind.Video,
        _ => null
    };

    private static (string Type, string Id) ResolvePreferredIdentity(
        string type,
        string id,
        MediaItemKind kind,
        JsonElement attributes)
    {
        if (!type.StartsWith("library-", StringComparison.Ordinal)
            || !attributes.TryGetProperty("playParams", out var playParams)
            || playParams.ValueKind != JsonValueKind.Object
            || FirstString(playParams, "catalogId") is not { Length: > 0 } catalogId)
        {
            return (type, id);
        }
        var catalogType = kind switch
        {
            MediaItemKind.Track => "songs",
            MediaItemKind.Album => "albums",
            MediaItemKind.Artist => "artists",
            MediaItemKind.Playlist => "playlists",
            MediaItemKind.Video => "music-videos",
            _ => type
        };
        return (catalogType, catalogId);
    }

    private static (string Type, string Id) ParseCatalogResource(MediaItem item)
    {
        if (!TryParseExternalId(item.ExternalId, out var type, out var id)
            || type is not ("songs" or "albums" or "artists" or "playlists" or "music-videos"))
            throw new InvalidOperationException("Operacja wymaga elementu z katalogowym identyfikatorem Apple Music.");
        return (type, id);
    }

    private static object ParsePlaylistTrack(MediaItem item)
    {
        if (!TryParseExternalId(item.ExternalId, out var type, out var id)
            || type is not ("songs" or "music-videos" or "library-songs" or "library-music-videos"))
            throw new InvalidOperationException("Do playlisty Apple Music można dodać utwór albo teledysk.");
        return new { id, type };
    }

    internal static bool TryParseExternalId(string? externalId, out string type, out string id)
    {
        type = string.Empty;
        id = string.Empty;
        if (string.IsNullOrWhiteSpace(externalId)) return false;
        var separator = externalId.IndexOf(':');
        if (separator <= 0 || separator == externalId.Length - 1) return false;
        type = externalId[..separator];
        id = externalId[(separator + 1)..];
        return KindForType(type) is not null && id.Length > 0;
    }

    private static bool TryIdentity(JsonElement resource, out string type, out string id)
    {
        type = resource.TryGetProperty("type", out var typeValue) ? typeValue.GetString() ?? string.Empty : string.Empty;
        id = resource.TryGetProperty("id", out var idValue) ? idValue.GetString() ?? string.Empty : string.Empty;
        return type.Length > 0 && id.Length > 0;
    }

    private static string? FirstRelationshipId(JsonElement resource, string name)
    {
        if (!resource.TryGetProperty("relationships", out var relationships)
            || !relationships.TryGetProperty(name, out var relationship)
            || !relationship.TryGetProperty("data", out var data)) return null;
        var value = data.ValueKind switch
        {
            JsonValueKind.Array when data.GetArrayLength() > 0 => data[0],
            JsonValueKind.Object => data,
            _ => default
        };
        return value.ValueKind == JsonValueKind.Object && TryIdentity(value, out var type, out var id)
            ? $"{type}:{id}" : null;
    }

    private static string? FirstString(JsonElement element, params string[] names)
    {
        foreach (var name in names)
            if (element.TryGetProperty(name, out var value)
                && value.ValueKind == JsonValueKind.String
                && !string.IsNullOrWhiteSpace(value.GetString())) return value.GetString()!.Trim();
        return null;
    }

    private static bool TryBoolean(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value)
        && value.ValueKind is JsonValueKind.True or JsonValueKind.False
        && value.GetBoolean();

    private Uri ResolveAddress(string address) =>
        Uri.TryCreate(address, UriKind.Absolute, out var absolute)
            ? absolute : new Uri(http.BaseAddress ?? ApiBaseAddress, address);

    private static string NormalizeStorefront(string value)
    {
        var normalized = value.Trim().ToLowerInvariant();
        return normalized.Length == 2 && normalized.All(character => character is >= 'a' and <= 'z')
            ? normalized
            : throw new ArgumentException("Storefront Apple Music musi mieć dwie litery, na przykład pl.", nameof(value));
    }

    private static void EnsureToken(string value, string message)
    {
        if (string.IsNullOrWhiteSpace(value)) throw new InvalidOperationException(message);
    }

    private static string Escape(string value) => Uri.EscapeDataString(value);

    public void Dispose()
    {
        if (ownsHttpClient) http.Dispose();
    }
}
