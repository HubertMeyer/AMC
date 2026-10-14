using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Searches Apple's public podcast directory. Results are only directory
/// metadata and public RSS/Atom addresses; no Apple account is required and
/// AMC does not send the user's library to Apple.
/// </summary>
internal sealed class ApplePodcastDirectoryClient : IDisposable
{
    private static readonly Regex PodcastIdSegment = new(
        "^id(?<id>[1-9][0-9]*)$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);
    private readonly HttpClient _client;
    private readonly bool _ownsClient;
    private readonly object _cacheGate = new();
    private readonly Dictionary<string, (DateTime StoredUtc, IReadOnlyList<MediaItem> Items)> _cache =
        new(StringComparer.OrdinalIgnoreCase);
    private static readonly TimeSpan CacheLifetime = TimeSpan.FromMinutes(5);

    public ApplePodcastDirectoryClient()
    {
        _client = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
        _ownsClient = true;
        _client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMultimediaController/0.1");
    }

    internal ApplePodcastDirectoryClient(HttpMessageHandler handler, TimeSpan? timeout = null)
    {
        _client = new HttpClient(handler)
        {
            Timeout = timeout ?? TimeSpan.FromSeconds(15)
        };
        _ownsClient = true;
        _client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMultimediaController/0.1");
    }

    public async Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        var normalized = string.Join(' ', query
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        if (normalized.Length == 0) return [];
        lock (_cacheGate)
        {
            if (_cache.TryGetValue(normalized, out var cached)
                && DateTime.UtcNow - cached.StoredUtc <= CacheLifetime)
            {
                return cached.Items;
            }
        }

        var address = new Uri(
            "https://itunes.apple.com/search" +
            $"?term={Uri.EscapeDataString(normalized)}&country=PL&media=podcast&entity=podcast&limit=50&explicit=Yes");
        var response = await _client.GetFromJsonAsync<AppleSearchResponse>(address, cancellationToken)
            .ConfigureAwait(false);
        var items = (response?.Results ?? [])
            .Where(result => TryPublicHttpUri(result.FeedUrl, out _))
            .GroupBy(result => result.FeedUrl!.Trim(), StringComparer.OrdinalIgnoreCase)
            .Select(group => group.First())
            .Take(50)
            .Select(ToMediaItem)
            .ToArray();
        lock (_cacheGate)
        {
            foreach (var staleKey in _cache
                         .Where(entry => DateTime.UtcNow - entry.Value.StoredUtc > CacheLifetime)
                         .Select(entry => entry.Key)
                         .ToArray())
            {
                _cache.Remove(staleKey);
            }
            _cache[normalized] = (DateTime.UtcNow, items);
        }
        return items;
    }

    /// <summary>
    /// Resolves a public Apple Podcasts page to the public RSS/Atom address
    /// exposed by Apple's documented Lookup operation. This does not sign in
    /// to an Apple account and cannot expose subscriber-only Apple audio.
    /// </summary>
    public async Task<MediaItem> LookupAsync(
        Uri applePodcastPage,
        CancellationToken cancellationToken = default)
    {
        if (!TryGetPodcastId(applePodcastPage, out var podcastId))
        {
            throw new ArgumentException(
                "Adres nie jest publiczną stroną podcastu w Apple Podcasts.",
                nameof(applePodcastPage));
        }

        var address = new Uri(
            "https://itunes.apple.com/lookup" +
            $"?id={podcastId}&country=PL&media=podcast&entity=podcast");
        var response = await _client.GetFromJsonAsync<AppleSearchResponse>(address, cancellationToken)
            .ConfigureAwait(false);
        var result = (response?.Results ?? [])
            .FirstOrDefault(candidate => candidate.CollectionId == podcastId
                && TryPublicHttpUri(candidate.FeedUrl, out _));
        if (result is null)
        {
            throw new InvalidDataException(
                "Ten podcast Apple nie udostępnia publicznego kanału RSS lub Atom. " +
                "Treści dostępnych wyłącznie w subskrypcji Apple nie można otworzyć w AMC.");
        }
        return ToMediaItem(result);
    }

    internal static bool TryGetPodcastId(Uri? address, out long podcastId)
    {
        podcastId = 0;
        if (address is null
            || !address.IsAbsoluteUri
            || address.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(address.UserInfo)
            || !string.Equals(address.IdnHost, "podcasts.apple.com", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        foreach (var segment in address.AbsolutePath.Split('/', StringSplitOptions.RemoveEmptyEntries).Reverse())
        {
            var match = PodcastIdSegment.Match(Uri.UnescapeDataString(segment));
            if (match.Success
                && long.TryParse(
                    match.Groups["id"].Value,
                    System.Globalization.NumberStyles.None,
                    System.Globalization.CultureInfo.InvariantCulture,
                    out podcastId))
            {
                return true;
            }
        }
        podcastId = 0;
        return false;
    }

    private static MediaItem ToMediaItem(ApplePodcastResult result)
    {
        var feedUrl = result.FeedUrl!.Trim();
        var externalId = result.CollectionId > 0
            ? result.CollectionId.ToString(System.Globalization.CultureInfo.InvariantCulture)
            : Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(feedUrl))).ToLowerInvariant();
        return new MediaItem
        {
            Id = $"podcast-directory:apple:{externalId}",
            Title = string.IsNullOrWhiteSpace(result.CollectionName)
                ? "Podcast bez nazwy"
                : result.CollectionName.Trim(),
            Artist = result.ArtistName?.Trim() ?? string.Empty,
            Kind = MediaItemKind.Podcast,
            Source = feedUrl,
            PublicUri = TryPublicHttpUri(result.CollectionViewUrl, out var pageUri)
                ? pageUri!.AbsoluteUri
                : null,
            Tags = result.PrimaryGenreName?.Trim(),
            ExternalId = $"apple:{externalId}",
            IsAvailable = true,
            IsInLibrary = false
        };
    }

    private static bool TryPublicHttpUri(string? value, out Uri? uri)
    {
        uri = null;
        if (!Uri.TryCreate(value?.Trim(), UriKind.Absolute, out var parsed)
            || parsed.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(parsed.UserInfo))
        {
            return false;
        }
        uri = parsed;
        return true;
    }

    public void Dispose()
    {
        if (_ownsClient) _client.Dispose();
    }

    private sealed class AppleSearchResponse
    {
        [JsonPropertyName("results")]
        public ApplePodcastResult[]? Results { get; set; }
    }

    private sealed class ApplePodcastResult
    {
        [JsonPropertyName("collectionId")]
        public long CollectionId { get; set; }

        [JsonPropertyName("collectionName")]
        public string? CollectionName { get; set; }

        [JsonPropertyName("artistName")]
        public string? ArtistName { get; set; }

        [JsonPropertyName("feedUrl")]
        public string? FeedUrl { get; set; }

        [JsonPropertyName("collectionViewUrl")]
        public string? CollectionViewUrl { get; set; }

        [JsonPropertyName("primaryGenreName")]
        public string? PrimaryGenreName { get; set; }
    }
}
