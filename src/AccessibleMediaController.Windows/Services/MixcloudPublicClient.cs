using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

internal enum MixcloudAddressKind
{
    Channel,
    Show
}

internal sealed record MixcloudShowDocument(
    string PageUrl,
    string Title,
    string Channel,
    string Description,
    TimeSpan Duration);

/// <summary>
/// Reads Mixcloud's documented public catalogue. Public GET requests need no
/// account or API secret. Mixcloud does not expose audio stream URLs here, so
/// persisted shows point only at their stable public pages.
/// </summary>
internal sealed class MixcloudPublicClient : IDisposable
{
    private const string UserResultPrefix = "podcast-directory:mixcloud:";
    private const string ShowResultPrefix = "internet-media-search:mixcloud:";
    private const int MaximumSearchItemsPerKind = 30;
    private const int MaximumChannelItems = 100;
    private static readonly TimeSpan CacheLifetime = TimeSpan.FromMinutes(5);
    private static readonly HashSet<string> ReservedFirstSegments = new(
        [
            "about", "categories", "contact", "developers", "discover", "jobs",
            "live", "login", "popular", "privacy", "select", "signup", "terms",
            "upload"
        ],
        StringComparer.OrdinalIgnoreCase);

    private readonly HttpClient _client;
    private readonly object _cacheGate = new();
    private readonly Dictionary<string, (DateTime StoredUtc, IReadOnlyList<MediaItem> Items)> _cache =
        new(StringComparer.OrdinalIgnoreCase);

    public MixcloudPublicClient()
        : this(new HttpClientHandler(), TimeSpan.FromSeconds(15))
    {
    }

    internal MixcloudPublicClient(HttpMessageHandler handler, TimeSpan? timeout = null)
    {
        _client = new HttpClient(handler)
        {
            Timeout = timeout ?? TimeSpan.FromSeconds(15)
        };
        _client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMultimediaController/0.1");
    }

    internal async Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        var normalized = CleanText(query, 300);
        if (normalized.Length == 0) return [];
        lock (_cacheGate)
        {
            if (_cache.TryGetValue(normalized, out var cached)
                && DateTime.UtcNow - cached.StoredUtc <= CacheLifetime)
            {
                return cached.Items;
            }
        }

        var escaped = Uri.EscapeDataString(normalized);
        var usersTask = GetAsync<MixcloudSearchResponse<MixcloudUser>>(
            $"https://api.mixcloud.com/search/?q={escaped}&type=user&limit={MaximumSearchItemsPerKind}",
            cancellationToken);
        var showsTask = GetAsync<MixcloudSearchResponse<MixcloudShow>>(
            $"https://api.mixcloud.com/search/?q={escaped}&type=cloudcast&limit={MaximumSearchItemsPerKind}",
            cancellationToken);
        await Task.WhenAll(usersTask, showsTask).ConfigureAwait(false);

        var known = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var users = (usersTask.Result?.Data ?? [])
            .Select(ToUserItem)
            .Where(item => item is not null && known.Add(item.Source!))
            .Cast<MediaItem>();
        var shows = (showsTask.Result?.Data ?? [])
            .Select(ToShowItem)
            .Where(item => item is not null && known.Add(item.Source!))
            .Cast<MediaItem>();
        var items = users.Concat(shows).ToArray();
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

    internal async Task<PodcastFeedDocument> FetchChannelAsync(
        Uri address,
        CancellationToken cancellationToken = default)
    {
        if (!TryNormalizeAddress(address, out var kind, out var normalized)
            || kind != MixcloudAddressKind.Channel)
        {
            throw new InvalidDataException(
                "Adres Mixcloud nie prowadzi do publicznego profilu.");
        }
        var username = normalized.Segments[1].Trim('/');
        var profileTask = GetAsync<MixcloudUser>(
            $"https://api.mixcloud.com/{Uri.EscapeDataString(username)}/",
            cancellationToken);
        var showsTask = GetAsync<MixcloudSearchResponse<MixcloudShow>>(
            $"https://api.mixcloud.com/{Uri.EscapeDataString(username)}/cloudcasts/?limit={MaximumChannelItems}",
            cancellationToken);
        await Task.WhenAll(profileTask, showsTask).ConfigureAwait(false);
        var profile = profileTask.Result
            ?? throw new InvalidDataException("Mixcloud nie zwrócił danych profilu.");
        var title = CleanText(profile.Name, 500);
        if (title.Length == 0) title = CleanText(profile.Username, 300);
        if (title.Length == 0) title = "Profil Mixcloud";
        var episodes = (showsTask.Result?.Data ?? [])
            .Select(ToFeedEpisode)
            .Where(episode => episode is not null)
            .Cast<PodcastFeedEpisode>()
            .ToArray();
        return new PodcastFeedDocument(
            $"mixcloud:user:{username.ToLowerInvariant()}",
            title,
            title,
            CleanText(profile.Biography, 4000),
            normalized,
            normalized,
            episodes,
            EpisodesTruncated: !string.IsNullOrWhiteSpace(showsTask.Result?.Paging?.Next));
    }

    internal async Task<MixcloudShowDocument> FetchShowAsync(
        Uri address,
        CancellationToken cancellationToken = default)
    {
        if (!TryNormalizeAddress(address, out var kind, out var normalized)
            || kind != MixcloudAddressKind.Show)
        {
            throw new InvalidDataException(
                "Adres Mixcloud nie prowadzi do publicznej audycji.");
        }
        var apiAddress = "https://api.mixcloud.com"
            + normalized.AbsolutePath.TrimEnd('/') + "/";
        var show = await GetAsync<MixcloudShow>(apiAddress, cancellationToken)
            .ConfigureAwait(false)
            ?? throw new InvalidDataException("Mixcloud nie zwrócił danych audycji.");
        var page = PublicMixcloudAddress(show.Url) ?? normalized;
        var title = CleanText(show.Name, 500);
        if (title.Length == 0) title = "Audycja Mixcloud";
        var channel = CleanText(show.User?.Name, 300);
        if (channel.Length == 0) channel = CleanText(show.User?.Username, 300);
        return new MixcloudShowDocument(
            page.AbsoluteUri,
            title,
            channel,
            CleanText(show.Description, 4000),
            SafeDuration(show.AudioLength));
    }

    internal static bool IsChannelSearchResult(MediaItem? item) =>
        item?.Id.StartsWith(UserResultPrefix, StringComparison.Ordinal) == true;

    internal static bool IsShowSearchResult(MediaItem? item) =>
        item?.Id.StartsWith(ShowResultPrefix, StringComparison.Ordinal) == true;

    internal static bool TryNormalizeAddress(
        Uri? address,
        out MixcloudAddressKind kind,
        out Uri normalized)
    {
        kind = default;
        normalized = null!;
        if (address is null
            || address.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(address.UserInfo)
            || address.Host is not ("mixcloud.com" or "www.mixcloud.com"))
        {
            return false;
        }
        var segments = address.AbsolutePath
            .Split('/', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (segments.Length is not (1 or 2)
            || ReservedFirstSegments.Contains(segments[0])
            || segments.Any(segment => segment.Length == 0 || segment.Length > 200))
        {
            return false;
        }
        kind = segments.Length == 1 ? MixcloudAddressKind.Channel : MixcloudAddressKind.Show;
        normalized = new Uri(
            "https://www.mixcloud.com/"
            + string.Join('/', segments.Select(Uri.EscapeDataString))
            + "/");
        return true;
    }

    private async Task<T?> GetAsync<T>(string address, CancellationToken cancellationToken)
    {
        try
        {
            return await _client.GetFromJsonAsync<T>(address, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (System.Text.Json.JsonException exception)
        {
            throw new InvalidDataException("Mixcloud zwrócił nieprawidłowe dane.", exception);
        }
    }

    private static MediaItem? ToUserItem(MixcloudUser user)
    {
        var page = PublicMixcloudAddress(user.Url);
        if (page is null
            || !TryNormalizeAddress(page, out var kind, out var normalized)
            || kind != MixcloudAddressKind.Channel)
        {
            return null;
        }
        var username = normalized.Segments[1].Trim('/');
        var title = CleanText(user.Name, 500);
        if (title.Length == 0) title = CleanText(user.Username, 300);
        if (title.Length == 0) title = "Profil Mixcloud";
        return new MediaItem
        {
            Id = UserResultPrefix + StableId(username),
            Title = title,
            Kind = MediaItemKind.Podcast,
            Source = normalized.AbsoluteUri,
            PublicUri = normalized.AbsoluteUri,
            ExternalId = $"mixcloud:user:{username.ToLowerInvariant()}",
            Tags = "Mixcloud",
            IsAvailable = true,
            IsInLibrary = false
        };
    }

    private static MediaItem? ToShowItem(MixcloudShow show)
    {
        var page = PublicMixcloudAddress(show.Url);
        if (page is null
            || !TryNormalizeAddress(page, out var kind, out var normalized)
            || kind != MixcloudAddressKind.Show)
        {
            return null;
        }
        var title = CleanText(show.Name, 500);
        if (title.Length == 0) title = "Audycja Mixcloud";
        return new MediaItem
        {
            Id = ShowResultPrefix + StableId(normalized.AbsoluteUri),
            Title = title,
            Artist = CleanText(show.User?.Name, 300),
            Kind = MediaItemKind.Episode,
            Duration = SafeDuration(show.AudioLength),
            Source = normalized.AbsoluteUri,
            PublicUri = normalized.AbsoluteUri,
            ExternalId = "internet-media:public",
            Tags = "Mixcloud",
            IsAvailable = true,
            IsInLibrary = false
        };
    }

    private static PodcastFeedEpisode? ToFeedEpisode(MixcloudShow show)
    {
        var page = PublicMixcloudAddress(show.Url);
        if (page is null
            || !TryNormalizeAddress(page, out var kind, out var normalized)
            || kind != MixcloudAddressKind.Show)
        {
            return null;
        }
        var title = CleanText(show.Name, 500);
        if (title.Length == 0) title = "Audycja Mixcloud";
        DateTimeOffset? published = null;
        if (DateTimeOffset.TryParse(
                show.CreatedTime,
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
                out var parsed))
        {
            published = parsed;
        }
        return new PodcastFeedEpisode(
            "mixcloud:show:" + StableId(normalized.AbsoluteUri),
            normalized.AbsoluteUri,
            title,
            CleanText(show.User?.Name, 300),
            CleanText(show.Description, 4000),
            published,
            SafeDuration(show.AudioLength),
            normalized,
            normalized,
            "audio/mixcloud",
            null);
    }

    private static Uri? PublicMixcloudAddress(string? value)
    {
        if (!Uri.TryCreate(value?.Trim(), UriKind.Absolute, out var parsed)
            || !TryNormalizeAddress(parsed, out _, out var normalized))
        {
            return null;
        }
        return normalized;
    }

    private static TimeSpan SafeDuration(long seconds) =>
        seconds is > 0 and < 365 * 24 * 60 * 60
            ? TimeSpan.FromSeconds(seconds)
            : TimeSpan.Zero;

    private static string StableId(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)))
            .ToLowerInvariant();

    private static string CleanText(string? value, int maximumLength)
    {
        var normalized = string.Join(' ', (value ?? string.Empty).Replace('\0', ' ')
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        return normalized.Length <= maximumLength
            ? normalized
            : normalized[..maximumLength].Trim();
    }

    public void Dispose() => _client.Dispose();

    private sealed class MixcloudSearchResponse<T>
    {
        [JsonPropertyName("data")]
        public T[]? Data { get; set; }

        [JsonPropertyName("paging")]
        public MixcloudPaging? Paging { get; set; }
    }

    private sealed class MixcloudPaging
    {
        [JsonPropertyName("next")]
        public string? Next { get; set; }
    }

    private sealed class MixcloudUser
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("username")]
        public string? Username { get; set; }

        [JsonPropertyName("url")]
        public string? Url { get; set; }

        [JsonPropertyName("biog")]
        public string? Biography { get; set; }
    }

    private sealed class MixcloudShow
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("url")]
        public string? Url { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("audio_length")]
        public long AudioLength { get; set; }

        [JsonPropertyName("created_time")]
        public string? CreatedTime { get; set; }

        [JsonPropertyName("user")]
        public MixcloudUser? User { get; set; }
    }
}
