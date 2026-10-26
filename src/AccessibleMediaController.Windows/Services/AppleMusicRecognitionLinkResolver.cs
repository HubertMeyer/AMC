using System.Globalization;
using System.Net.Http;
using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

internal interface IAppleMusicRecognitionLinkResolver
{
    bool HasCachedMatch(RadioRecognizedTrackSettings entry);
    Task<AppleMusicRecognitionLinkResult> ResolveAsync(
        RadioRecognizedTrackSettings entry,
        CancellationToken cancellationToken);
}

internal sealed record AppleMusicRecognitionLinkResult(
    string TrackLink,
    string? AlbumLink,
    string? ArtistLink,
    bool CacheChanged);

/// <summary>
/// Wyszukuje publiczne, niesekretne łącza Apple Music bez logowania do konta.
/// Zapytanie jest wykonywane dopiero po wybraniu działania Apple Music, a
/// pewne dopasowanie zapisujemy w historii, aby nie powtarzać zapytań.
/// </summary>
internal sealed class AppleMusicRecognitionLinkResolver : IAppleMusicRecognitionLinkResolver
{
    private static readonly HttpClient SharedHttpClient = CreateHttpClient();
    private readonly HttpClient _httpClient;
    private readonly string _countryCode;

    public AppleMusicRecognitionLinkResolver(
        HttpClient? httpClient = null,
        string? countryCode = null)
    {
        _httpClient = httpClient ?? SharedHttpClient;
        _countryCode = NormalizeCountryCode(countryCode);
    }

    public bool HasCachedMatch(RadioRecognizedTrackSettings entry) =>
        TryFromCache(entry, out _);

    public async Task<AppleMusicRecognitionLinkResult> ResolveAsync(
        RadioRecognizedTrackSettings entry,
        CancellationToken cancellationToken)
    {
        if (TryFromCache(entry, out var cached)) return cached;

        var query = string.Join(' ', new[] { entry.Artist, entry.Title }
            .Where(value => !string.IsNullOrWhiteSpace(value)));
        if (string.IsNullOrWhiteSpace(query))
            throw new InvalidOperationException("Brak tytułu do wyszukania w Apple Music.");

        var requestUri = "https://itunes.apple.com/search"
            + $"?term={Uri.EscapeDataString(query)}"
            + $"&country={Uri.EscapeDataString(_countryCode)}"
            + "&media=music&entity=song&limit=20";
        using var response = await _httpClient.GetAsync(requestUri, cancellationToken)
            .ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidOperationException(
                $"Apple Music nie zwróciło wyników wyszukiwania (HTTP {(int)response.StatusCode}).");
        }

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken)
            .ConfigureAwait(false);
        using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
        var candidates = ParseCandidates(document.RootElement);
        var track = RecognizedTrackMatchSelector.SelectBest(entry, candidates)
            ?? throw new InvalidOperationException(
                "Nie znaleziono wystarczająco pewnego dopasowania w Apple Music.");
        if (!TryApplePublicUri(track.PublicUri, out var trackLink))
            throw new InvalidOperationException("Apple Music nie zwróciło łącza do utworu.");

        var match = new RadioRecognizedTrackMatchSettings
        {
            TrackExternalId = track.ExternalId!,
            TrackPublicUri = trackLink,
            AlbumExternalId = EmptyToNull(track.RelatedAlbumExternalId),
            AlbumTitle = EmptyToNull(track.RelatedAlbumTitle) ?? EmptyToNull(entry.Album),
            AlbumPublicUri = ValidApplePublicUri(track.HomepageUri),
            ArtistExternalId = EmptyToNull(track.RelatedArtistExternalId),
            ArtistName = EmptyToNull(track.RelatedArtistName)
                ?? EmptyToNull(track.Artist)
                ?? EmptyToNull(entry.Artist),
            ArtistPublicUri = ValidApplePublicUri(track.Source),
            ResolvedUtcTicks = DateTime.UtcNow.Ticks
        };
        entry.AppleMusicMatch = match;
        return Result(match, cacheChanged: true);
    }

    private static IReadOnlyList<MediaItem> ParseCandidates(JsonElement root)
    {
        if (!root.TryGetProperty("results", out var results)
            || results.ValueKind != JsonValueKind.Array)
        {
            return [];
        }

        var candidates = new List<MediaItem>();
        foreach (var result in results.EnumerateArray())
        {
            var trackId = ScalarString(result, "trackId");
            var title = String(result, "trackName");
            var artist = String(result, "artistName");
            var trackLink = ValidApplePublicUri(String(result, "trackViewUrl"));
            if (string.IsNullOrWhiteSpace(trackId)
                || string.IsNullOrWhiteSpace(title)
                || trackLink is null)
            {
                continue;
            }

            candidates.Add(new MediaItem
            {
                Id = $"apple-public:track:{trackId}",
                Kind = MediaItemKind.Track,
                Title = title,
                Artist = artist ?? string.Empty,
                ExternalId = trackId,
                PublicUri = trackLink,
                RelatedAlbumExternalId = ScalarString(result, "collectionId"),
                RelatedAlbumTitle = String(result, "collectionName"),
                RelatedArtistExternalId = ScalarString(result, "artistId"),
                RelatedArtistName = artist,
                // Te pola przenoszą wyłącznie publiczne łącza na czas wyboru.
                // Nie są prezentowane użytkownikowi ani używane do odtwarzania.
                HomepageUri = ValidApplePublicUri(String(result, "collectionViewUrl")),
                Source = ValidApplePublicUri(String(result, "artistViewUrl")),
                IsAvailable = true
            });
        }
        return candidates;
    }

    private static bool TryFromCache(
        RadioRecognizedTrackSettings entry,
        out AppleMusicRecognitionLinkResult result)
    {
        var match = entry.AppleMusicMatch;
        if (match is null
            || string.IsNullOrWhiteSpace(match.TrackExternalId)
            || !TryApplePublicUri(match.TrackPublicUri, out _))
        {
            result = null!;
            return false;
        }
        result = Result(match, cacheChanged: false);
        return true;
    }

    private static AppleMusicRecognitionLinkResult Result(
        RadioRecognizedTrackMatchSettings match,
        bool cacheChanged) => new(
            ValidApplePublicUri(match.TrackPublicUri)!,
            ValidApplePublicUri(match.AlbumPublicUri),
            ValidApplePublicUri(match.ArtistPublicUri),
            cacheChanged);

    private static string? String(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? EmptyToNull(value.GetString())
            : null;

    private static string? ScalarString(JsonElement element, string name)
    {
        if (!element.TryGetProperty(name, out var value)) return null;
        return value.ValueKind switch
        {
            JsonValueKind.String => EmptyToNull(value.GetString()),
            JsonValueKind.Number => value.GetRawText(),
            _ => null
        };
    }

    private static string? ValidApplePublicUri(string? value) =>
        TryApplePublicUri(value, out var uri) ? uri : null;

    private static bool TryApplePublicUri(string? value, out string uri)
    {
        if (Uri.TryCreate(value?.Trim(), UriKind.Absolute, out var parsed)
            && parsed.Scheme is "http" or "https"
            && (string.Equals(parsed.Host, "apple.com", StringComparison.OrdinalIgnoreCase)
                || parsed.Host.EndsWith(".apple.com", StringComparison.OrdinalIgnoreCase)))
        {
            uri = parsed.AbsoluteUri;
            return true;
        }
        uri = string.Empty;
        return false;
    }

    private static string NormalizeCountryCode(string? value)
    {
        var normalized = value?.Trim().ToUpperInvariant();
        if (normalized is { Length: 2 }
            && normalized.All(character => character is >= 'A' and <= 'Z'))
        {
            return normalized;
        }
        try
        {
            normalized = RegionInfo.CurrentRegion.TwoLetterISORegionName.ToUpperInvariant();
            if (normalized.Length == 2) return normalized;
        }
        catch (ArgumentException)
        {
            // Neutralna kultura nie ma regionu; polski sklep jest bezpiecznym
            // ustawieniem domyślnym dla bieżącej wersji AMC.
        }
        return "PL";
    }

    private static HttpClient CreateHttpClient()
    {
        var client = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
        client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMultimediaController/1.0");
        return client;
    }

    private static string? EmptyToNull(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}
