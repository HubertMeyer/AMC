using System.Diagnostics;
using System.Text.Json;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Łączy publiczne wyniki Apple Podcasts, SoundCloud, Spreakera i YouTube tą samą drogą,
/// której używa główne AMC. Protokół dostaje tylko celowe etykiety oraz
/// publiczne adresy HTTP(S); wyjątki, klasy i rekordy klientów nie opuszczają
/// hosta.
/// </summary>
internal sealed class LitePodcastDirectorySearchCoordinator : IDisposable
{
    public const string Operation = "podcast.searchDirectories";
    private const int MaximumQueryLength = 300;

    private readonly ApplePodcastDirectoryClient _apple;
    private readonly SpreakerPodcastDirectoryClient _spreaker;
    private readonly YouTubeSearchClient _youTube;

    public LitePodcastDirectorySearchCoordinator()
    {
        _apple = new ApplePodcastDirectoryClient();
        _spreaker = new SpreakerPodcastDirectoryClient();
        _youTube = new YouTubeSearchClient();
    }

    public object Search(JsonElement args)
    {
        var query = NormalizeQuery(LiteArgs.RequireText(args, "query"));
        if (query.Length == 0)
            throw new LiteRequestException("Wpisz tekst do wyszukania.");

        var searches = new[]
        {
            SearchSourceAsync(
                "Apple Podcasts",
                token => _apple.SearchAsync(query, token)),
            SearchSourceAsync(
                "Spreaker",
                token => _spreaker.SearchAsync(query, token)),
            SearchSourceAsync(
                "YouTube",
                token => _youTube.SearchAsync(query, token))
        };
        var results = Task.WhenAll(searches).GetAwaiter().GetResult();
        if (results.All(result => result.Error is not null))
        {
            throw new LiteRequestException(
                "Publiczne katalogi podcastów, SoundCloud i YouTube są chwilowo niedostępne.");
        }

        var knownAddresses = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var items = results
            .SelectMany(result => result.Items.Select(item => (result.Name, Item: item)))
            .Where(candidate => TryPublicAddress(candidate.Item.Source, out _))
            .OrderBy(candidate => ResultRank(candidate.Item))
            .Where(candidate => knownAddresses.Add(NormalizeAddress(candidate.Item.Source!)))
            .Select(candidate => ToPayload(candidate.Name, candidate.Item))
            .ToArray();
        var warnings = results
            .Where(result => result.Error is not null)
            .Select(result => $"Katalog {result.Name} jest chwilowo niedostępny")
            .ToArray();

        foreach (var result in results)
        {
            Console.Error.WriteLine(
                $"[lite-host] katalog {result.Name}: {result.Items.Count} wyników, "
                + $"{result.Duration.TotalSeconds:0.0} s"
                + (result.Error is null ? string.Empty : ", chwilowo niedostępny"));
        }
        return new { items, warnings };
    }

    private static async Task<SearchSourceResult> SearchSourceAsync(
        string name,
        Func<CancellationToken, Task<IReadOnlyList<MediaItem>>> search)
    {
        var stopwatch = Stopwatch.StartNew();
        try
        {
            var items = await search(CancellationToken.None).ConfigureAwait(false);
            return new SearchSourceResult(name, items, null, stopwatch.Elapsed);
        }
        catch (Exception exception) when (exception is HttpRequestException
            or InvalidDataException
            or ArgumentException
            or NotSupportedException
            or TimeoutException
            or OperationCanceledException)
        {
            return new SearchSourceResult(name, [], exception, stopwatch.Elapsed);
        }
    }

    private static object ToPayload(string sourceName, MediaItem item)
    {
        var remoteKind = SoundCloudPodcastClient.IsSoundCloudSearchResult(item)
            ? "soundcloudPodcast"
            : YouTubeSearchClient.IsChannelSearchResult(item)
                ? "youtubeChannel"
                : YouTubeSearchClient.IsSearchResult(item)
                    ? "youtubeVideo"
                    : "rss";
        var detail = remoteKind switch
        {
            "youtubeChannel" => "kanał YouTube",
            "youtubeVideo" when YouTubeSearchClient.IsLiveSearchResult(item) =>
                "YouTube, transmisja na żywo",
            "youtubeVideo" => "YouTube",
            "soundcloudPodcast" => "podcast SoundCloud",
            _ => sourceName
        };
        return new
        {
            id = item.Id,
            title = item.Title,
            artist = item.Artist,
            kind = item.Kind == MediaItemKind.Podcast ? "podcast" : "episode",
            remoteKind,
            address = item.Source,
            pageAddress = PublicAddressOrNull(item.PublicUri),
            detail,
            durationTicks = Math.Max(0, item.Duration.Ticks)
        };
    }

    private static int ResultRank(MediaItem item) =>
        YouTubeSearchClient.IsChannelSearchResult(item)
            ? 0
            : YouTubeSearchClient.IsSearchResult(item)
                ? 2
                : 1;

    private static string NormalizeQuery(string query)
    {
        var normalized = string.Join(' ', query.Split(
            (char[]?)null,
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        return normalized.Length <= MaximumQueryLength
            ? normalized
            : normalized[..MaximumQueryLength].Trim();
    }

    private static string? PublicAddressOrNull(string? value) =>
        TryPublicAddress(value, out var address) ? address!.AbsoluteUri : null;

    private static bool TryPublicAddress(string? value, out Uri? address)
    {
        address = null;
        if (!Uri.TryCreate(value?.Trim(), UriKind.Absolute, out var candidate)
            || candidate.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(candidate.UserInfo))
        {
            return false;
        }
        address = candidate;
        return true;
    }

    private static string NormalizeAddress(string address)
    {
        if (!TryPublicAddress(address, out var uri)) return address.Trim();
        return uri!.GetComponents(
                UriComponents.SchemeAndServer | UriComponents.PathAndQuery,
                UriFormat.SafeUnescaped)
            .TrimEnd('/');
    }

    public void Dispose()
    {
        _apple.Dispose();
        _spreaker.Dispose();
    }

    private sealed record SearchSourceResult(
        string Name,
        IReadOnlyList<MediaItem> Items,
        Exception? Error,
        TimeSpan Duration);
}
