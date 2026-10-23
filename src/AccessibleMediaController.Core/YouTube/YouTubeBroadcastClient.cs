using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

namespace AccessibleMediaController.Core.YouTube;

public enum YouTubeBroadcastState
{
    Live,
    Upcoming
}

public sealed record YouTubeBroadcast(
    string VideoId,
    string Title,
    string ChannelTitle,
    Uri PageUri,
    YouTubeBroadcastState State,
    DateTimeOffset? ScheduledStartUtc,
    DateTimeOffset? ActualStartUtc);

/// <summary>
/// Odczytuje trwające i zaplanowane transmisje jednego publicznego kanału
/// przez oficjalne YouTube Data API. Token pozostaje wyłącznie w hoście.
/// Jedno odświeżenie zużywa dwa wywołania search.list; wynik jest celowo
/// ograniczony do pierwszej strony każdego stanu.
/// </summary>
public sealed class YouTubeBroadcastClient : IDisposable
{
    private static readonly Uri SearchEndpoint =
        new("https://www.googleapis.com/youtube/v3/search");
    private static readonly Uri VideosEndpoint =
        new("https://www.googleapis.com/youtube/v3/videos");
    private const int MaximumResultsPerState = 25;
    private readonly HttpClient _http;
    private readonly bool _ownsHttpClient;

    public YouTubeBroadcastClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
        _ownsHttpClient = httpClient is null;
    }

    public async Task<IReadOnlyList<YouTubeBroadcast>> ReadChannelAsync(
        string accessToken,
        string channelId,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(accessToken) || accessToken.Length > 8192)
            throw new InvalidOperationException("Najpierw zaloguj się do YouTube.");
        channelId = channelId?.Trim() ?? string.Empty;
        if (!IsSafeChannelId(channelId))
            throw new InvalidDataException(
                "Ten kanał YouTube nie ma stabilnego identyfikatora potrzebnego do odczytu transmisji.");

        var candidates = new Dictionary<string, SearchCandidate>(StringComparer.Ordinal);
        foreach (var state in new[] { YouTubeBroadcastState.Live, YouTubeBroadcastState.Upcoming })
        {
            var rows = await SearchAsync(accessToken, channelId, state, cancellationToken)
                .ConfigureAwait(false);
            foreach (var row in rows)
                candidates.TryAdd(row.VideoId, row);
        }
        if (candidates.Count == 0) return [];

        var details = new Dictionary<string, VideoDetails>(StringComparer.Ordinal);
        foreach (var ids in candidates.Keys.Chunk(50))
        {
            foreach (var item in await ReadDetailsAsync(accessToken, ids, cancellationToken)
                         .ConfigureAwait(false))
                details[item.VideoId] = item;
        }

        return candidates.Values
            .Select(candidate => CreateBroadcast(candidate, details.GetValueOrDefault(candidate.VideoId)))
            .OrderBy(item => item.State == YouTubeBroadcastState.Live ? 0 : 1)
            .ThenBy(item => item.ScheduledStartUtc ?? DateTimeOffset.MaxValue)
            .ThenBy(item => item.Title, StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    private async Task<IReadOnlyList<SearchCandidate>> SearchAsync(
        string accessToken,
        string channelId,
        YouTubeBroadcastState state,
        CancellationToken cancellationToken)
    {
        var eventType = state == YouTubeBroadcastState.Live ? "live" : "upcoming";
        var query = BuildQuery(new Dictionary<string, string>
        {
            ["part"] = "snippet",
            ["type"] = "video",
            ["channelId"] = channelId,
            ["eventType"] = eventType,
            ["maxResults"] = MaximumResultsPerState.ToString(System.Globalization.CultureInfo.InvariantCulture)
        });
        using var request = new HttpRequestMessage(
            HttpMethod.Get,
            new UriBuilder(SearchEndpoint) { Query = query }.Uri);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        using var response = await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(DescribeFailure(response.StatusCode, body));
        return ParseSearch(body, state);
    }

    private async Task<IReadOnlyList<VideoDetails>> ReadDetailsAsync(
        string accessToken,
        IEnumerable<string> videoIds,
        CancellationToken cancellationToken)
    {
        var ids = string.Join(',', videoIds);
        var query = BuildQuery(new Dictionary<string, string>
        {
            ["part"] = "snippet,liveStreamingDetails",
            ["id"] = ids
        });
        using var request = new HttpRequestMessage(
            HttpMethod.Get,
            new UriBuilder(VideosEndpoint) { Query = query }.Uri);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        using var response = await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(DescribeFailure(response.StatusCode, body));
        return ParseDetails(body);
    }

    private static IReadOnlyList<SearchCandidate> ParseSearch(
        string body,
        YouTubeBroadcastState state)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            if (!document.RootElement.TryGetProperty("items", out var items)
                || items.ValueKind != JsonValueKind.Array)
                return [];
            var result = new List<SearchCandidate>();
            foreach (var item in items.EnumerateArray())
            {
                if (!item.TryGetProperty("id", out var id)
                    || !id.TryGetProperty("videoId", out var videoElement))
                    continue;
                var videoId = videoElement.GetString()?.Trim() ?? string.Empty;
                if (!IsSafeVideoId(videoId)) continue;
                var snippet = item.TryGetProperty("snippet", out var value)
                    ? value
                    : default;
                result.Add(new SearchCandidate(
                    videoId,
                    ReadText(snippet, "title", "Transmisja YouTube", 500),
                    ReadText(snippet, "channelTitle", "Kanał YouTube", 300),
                    state));
            }
            return result;
        }
        catch (JsonException)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelną listę transmisji.");
        }
    }

    private static IReadOnlyList<VideoDetails> ParseDetails(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            if (!document.RootElement.TryGetProperty("items", out var items)
                || items.ValueKind != JsonValueKind.Array)
                return [];
            var result = new List<VideoDetails>();
            foreach (var item in items.EnumerateArray())
            {
                var videoId = item.TryGetProperty("id", out var id)
                    ? id.GetString()?.Trim() ?? string.Empty
                    : string.Empty;
                if (!IsSafeVideoId(videoId)) continue;
                var snippet = item.TryGetProperty("snippet", out var snippetValue)
                    ? snippetValue
                    : default;
                var live = item.TryGetProperty("liveStreamingDetails", out var liveValue)
                    ? liveValue
                    : default;
                result.Add(new VideoDetails(
                    videoId,
                    ReadText(snippet, "title", string.Empty, 500),
                    ReadText(snippet, "channelTitle", string.Empty, 300),
                    ReadTime(live, "scheduledStartTime"),
                    ReadTime(live, "actualStartTime")));
            }
            return result;
        }
        catch (JsonException)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelne szczegóły transmisji.");
        }
    }

    private static YouTubeBroadcast CreateBroadcast(
        SearchCandidate candidate,
        VideoDetails? details) =>
        new(
            candidate.VideoId,
            string.IsNullOrWhiteSpace(details?.Title) ? candidate.Title : details.Title,
            string.IsNullOrWhiteSpace(details?.ChannelTitle)
                ? candidate.ChannelTitle
                : details.ChannelTitle,
            new Uri($"https://www.youtube.com/watch?v={Uri.EscapeDataString(candidate.VideoId)}"),
            candidate.State,
            details?.ScheduledStartUtc,
            details?.ActualStartUtc);

    private static string BuildQuery(IReadOnlyDictionary<string, string> fields) =>
        string.Join('&', fields.Select(pair =>
            $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}"));

    private static string ReadText(
        JsonElement element,
        string property,
        string fallback,
        int maximum)
    {
        if (element.ValueKind != JsonValueKind.Object
            || !element.TryGetProperty(property, out var value)
            || value.ValueKind != JsonValueKind.String)
            return fallback;
        var text = string.Join(' ', (value.GetString() ?? string.Empty)
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        if (text.Length == 0) return fallback;
        return text.Length <= maximum ? text : text[..maximum].Trim();
    }

    private static DateTimeOffset? ReadTime(JsonElement element, string property)
    {
        if (element.ValueKind != JsonValueKind.Object
            || !element.TryGetProperty(property, out var value)
            || value.ValueKind != JsonValueKind.String
            || !DateTimeOffset.TryParse(
                value.GetString(),
                System.Globalization.CultureInfo.InvariantCulture,
                System.Globalization.DateTimeStyles.AssumeUniversal
                    | System.Globalization.DateTimeStyles.AdjustToUniversal,
                out var parsed))
            return null;
        return parsed;
    }

    private static bool IsSafeChannelId(string value) =>
        value.Length is >= 2 and <= 256
        && value.All(character => char.IsAsciiLetterOrDigit(character)
                                  || character is '-' or '_');

    private static bool IsSafeVideoId(string value) =>
        value.Length is >= 2 and <= 64
        && value.All(character => char.IsAsciiLetterOrDigit(character)
                                  || character is '-' or '_');

    private static string DescribeFailure(HttpStatusCode statusCode, string body)
    {
        var reason = ReadErrorReason(body);
        if (statusCode == HttpStatusCode.Unauthorized
            || string.Equals(reason, "authError", StringComparison.OrdinalIgnoreCase)
            || string.Equals(reason, "invalidCredentials", StringComparison.OrdinalIgnoreCase))
            return "Logowanie YouTube straciło ważność. Zaloguj się ponownie.";
        if (string.Equals(reason, "quotaExceeded", StringComparison.OrdinalIgnoreCase)
            || string.Equals(reason, "dailyLimitExceeded", StringComparison.OrdinalIgnoreCase))
            return "Wyczerpano dzienny limit wyszukiwania transmisji YouTube. Spróbuj później.";
        if (statusCode == HttpStatusCode.TooManyRequests)
            return "YouTube chwilowo ograniczył liczbę żądań. Spróbuj później.";
        if (statusCode == HttpStatusCode.Forbidden)
            return "YouTube odmówił dostępu do transmisji tego kanału.";
        return "Nie udało się pobrać transmisji YouTube.";
    }

    private static string? ReadErrorReason(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            if (!document.RootElement.TryGetProperty("error", out var error)
                || !error.TryGetProperty("errors", out var errors)
                || errors.ValueKind != JsonValueKind.Array)
                return null;
            foreach (var item in errors.EnumerateArray())
                if (item.TryGetProperty("reason", out var reason))
                    return reason.GetString()?.Trim();
            return null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public void Dispose()
    {
        if (_ownsHttpClient) _http.Dispose();
    }

    private sealed record SearchCandidate(
        string VideoId,
        string Title,
        string ChannelTitle,
        YouTubeBroadcastState State);

    private sealed record VideoDetails(
        string VideoId,
        string Title,
        string ChannelTitle,
        DateTimeOffset? ScheduledStartUtc,
        DateTimeOffset? ActualStartUtc);
}
