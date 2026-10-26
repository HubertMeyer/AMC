using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;

namespace AccessibleMediaController.Windows.Services;

internal sealed record YouTubeAccountSubscription(string ChannelId, string Title);

internal sealed record YouTubeAccountVideo(
    string VideoId,
    string Title,
    string ChannelTitle,
    DateTimeOffset? Published);

internal sealed record YouTubeAccountPlaylist(
    string PlaylistId,
    string Title,
    string ChannelTitle,
    string PrivacyStatus,
    IReadOnlyList<YouTubeAccountVideo> Videos);

internal sealed record YouTubeAccountLibrary(
    string AccountDisplayName,
    IReadOnlyList<YouTubeAccountSubscription> Subscriptions,
    IReadOnlyList<YouTubeAccountPlaylist> Playlists);

/// <summary>
/// Odczytowy klient YouTube Data API. Korzysta wyłącznie z zakresu
/// youtube.readonly; nie modyfikuje konta Google i nie przekazuje tokenu do
/// yt-dlp ani do odtwarzacza.
/// </summary>
internal sealed class YouTubeDataApiClient(HttpClient? httpClient = null) : IDisposable
{
    private static readonly Uri ApiRoot = new("https://www.googleapis.com/youtube/v3/");
    private const int MaximumPages = 20;
    private const int MaximumPlaylistVideos = 100;
    private readonly HttpClient http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
    private readonly bool ownsHttpClient = httpClient is null;

    public async Task<string> GetAccountDisplayNameAsync(
        string accessToken,
        CancellationToken cancellationToken)
    {
        using var document = await GetAsync(
            BuildUri("channels", ("part", "snippet"), ("mine", "true"), ("maxResults", "1")),
            accessToken,
            cancellationToken).ConfigureAwait(false);
        var item = Items(document.RootElement).FirstOrDefault();
        var title = item.ValueKind == JsonValueKind.Object
            ? ReadNestedString(item, "snippet", "title")
            : string.Empty;
        return title.Length > 0 ? title : "konto Google";
    }

    public async Task<IReadOnlyList<YouTubeAccountSubscription>> GetSubscriptionsAsync(
        string accessToken,
        CancellationToken cancellationToken)
    {
        var result = new List<YouTubeAccountSubscription>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;
        for (var page = 0; page < MaximumPages; page++)
        {
            var parameters = new List<(string Name, string Value)>
            {
                ("part", "snippet"),
                ("mine", "true"),
                ("maxResults", "50")
            };
            if (!string.IsNullOrWhiteSpace(pageToken)) parameters.Add(("pageToken", pageToken));
            using var document = await GetAsync(
                BuildUri("subscriptions", parameters.ToArray()),
                accessToken,
                cancellationToken).ConfigureAwait(false);
            foreach (var item in Items(document.RootElement))
            {
                var channelId = ReadNestedString(item, "snippet", "resourceId", "channelId");
                if (!IsSafeIdentifier(channelId, 160) || !known.Add(channelId)) continue;
                var title = CleanText(ReadNestedString(item, "snippet", "title"), 500);
                result.Add(new YouTubeAccountSubscription(
                    channelId,
                    title.Length > 0 ? title : "Kanał YouTube"));
            }
            pageToken = ReadString(document.RootElement, "nextPageToken");
            if (pageToken.Length == 0) break;
        }
        return result;
    }

    public async Task<IReadOnlyList<YouTubeAccountPlaylist>> GetPlaylistsAsync(
        string accessToken,
        CancellationToken cancellationToken)
    {
        var metadata = new List<(string Id, string Title, string ChannelTitle, string Privacy)>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;
        for (var page = 0; page < MaximumPages; page++)
        {
            var parameters = new List<(string Name, string Value)>
            {
                ("part", "snippet,status"),
                ("mine", "true"),
                ("maxResults", "50")
            };
            if (!string.IsNullOrWhiteSpace(pageToken)) parameters.Add(("pageToken", pageToken));
            using var document = await GetAsync(
                BuildUri("playlists", parameters.ToArray()),
                accessToken,
                cancellationToken).ConfigureAwait(false);
            foreach (var item in Items(document.RootElement))
            {
                var id = ReadString(item, "id");
                if (!IsSafeIdentifier(id, 160) || !known.Add(id)) continue;
                var title = CleanText(ReadNestedString(item, "snippet", "title"), 500);
                var channel = CleanText(ReadNestedString(item, "snippet", "channelTitle"), 300);
                var privacy = CleanText(ReadNestedString(item, "status", "privacyStatus"), 40);
                metadata.Add((id, title.Length > 0 ? title : "Playlista YouTube", channel, privacy));
            }
            pageToken = ReadString(document.RootElement, "nextPageToken");
            if (pageToken.Length == 0) break;
        }

        var result = new List<YouTubeAccountPlaylist>(metadata.Count);
        foreach (var playlist in metadata)
        {
            var videos = await GetPlaylistVideosAsync(
                playlist.Id,
                accessToken,
                cancellationToken).ConfigureAwait(false);
            result.Add(new YouTubeAccountPlaylist(
                playlist.Id,
                playlist.Title,
                playlist.ChannelTitle,
                playlist.Privacy,
                videos));
        }
        return result;
    }

    private async Task<IReadOnlyList<YouTubeAccountVideo>> GetPlaylistVideosAsync(
        string playlistId,
        string accessToken,
        CancellationToken cancellationToken)
    {
        var result = new List<YouTubeAccountVideo>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;
        for (var page = 0; page < MaximumPages && result.Count < MaximumPlaylistVideos; page++)
        {
            var parameters = new List<(string Name, string Value)>
            {
                ("part", "snippet,contentDetails"),
                ("playlistId", playlistId),
                ("maxResults", "50")
            };
            if (!string.IsNullOrWhiteSpace(pageToken)) parameters.Add(("pageToken", pageToken));
            using var document = await GetAsync(
                BuildUri("playlistItems", parameters.ToArray()),
                accessToken,
                cancellationToken).ConfigureAwait(false);
            foreach (var item in Items(document.RootElement))
            {
                if (result.Count >= MaximumPlaylistVideos) break;
                var videoId = ReadNestedString(item, "contentDetails", "videoId");
                if (!IsSafeIdentifier(videoId, 64) || !known.Add(videoId)) continue;
                var title = CleanText(ReadNestedString(item, "snippet", "title"), 500);
                if (title.Equals("Deleted video", StringComparison.OrdinalIgnoreCase)
                    || title.Equals("Private video", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                var channel = CleanText(
                    ReadNestedString(item, "snippet", "videoOwnerChannelTitle"),
                    300);
                var publishedText = ReadNestedString(item, "snippet", "publishedAt");
                var published = DateTimeOffset.TryParse(publishedText, out var parsed)
                    ? parsed
                    : (DateTimeOffset?)null;
                result.Add(new YouTubeAccountVideo(
                    videoId,
                    title.Length > 0 ? title : "Materiał YouTube",
                    channel,
                    published));
            }
            pageToken = ReadString(document.RootElement, "nextPageToken");
            if (pageToken.Length == 0) break;
        }
        return result;
    }

    internal static Uri BuildUri(string resource, params (string Name, string Value)[] parameters)
    {
        if (resource.Length == 0 || resource.Any(character => !char.IsAsciiLetter(character)))
            throw new ArgumentException("Nieprawidłowa nazwa zasobu YouTube.", nameof(resource));
        var query = string.Join('&', parameters
            .Where(parameter => parameter.Value.Length > 0)
            .Select(parameter =>
                $"{Uri.EscapeDataString(parameter.Name)}={Uri.EscapeDataString(parameter.Value)}"));
        return new UriBuilder(new Uri(ApiRoot, resource)) { Query = query }.Uri;
    }

    private async Task<JsonDocument> GetAsync(
        Uri address,
        string accessToken,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, address);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        using var response = await http.SendAsync(request, cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            var status = response.StatusCode;
            var reason = await ReadApiErrorAsync(response, cancellationToken).ConfigureAwait(false);
            throw new InvalidOperationException(DescribeApiError(status, reason));
        }
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        return await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    private static IEnumerable<JsonElement> Items(JsonElement root)
    {
        if (!root.TryGetProperty("items", out var items) || items.ValueKind != JsonValueKind.Array)
            yield break;
        foreach (var item in items.EnumerateArray()) yield return item;
    }

    private static async Task<string> ReadApiErrorAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            using var document = JsonDocument.Parse(content);
            return ReadNestedString(document.RootElement, "error", "message");
        }
        catch
        {
            return string.Empty;
        }
    }

    private static string DescribeApiError(HttpStatusCode status, string reason)
    {
        if (status is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
        {
            if (reason.Contains("quota", StringComparison.OrdinalIgnoreCase))
                return "YouTube Data API wyczerpało dzienny limit projektu Google. Spróbuj później.";
            return "Google odrzucił dostęp do biblioteki YouTube. Zaloguj konto ponownie i sprawdź, czy YouTube Data API v3 jest włączone.";
        }
        return $"YouTube Data API zwróciło błąd HTTP {(int)status}. Spróbuj ponownie później.";
    }

    private static string ReadNestedString(JsonElement element, params string[] path)
    {
        foreach (var name in path)
        {
            if (element.ValueKind != JsonValueKind.Object
                || !element.TryGetProperty(name, out element))
            {
                return string.Empty;
            }
        }
        return element.ValueKind == JsonValueKind.String
            ? element.GetString()?.Trim() ?? string.Empty
            : string.Empty;
    }

    private static string ReadString(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()?.Trim() ?? string.Empty
            : string.Empty;

    private static bool IsSafeIdentifier(string value, int maximumLength) =>
        value.Length is >= 2
        && value.Length <= maximumLength
        && value.All(character => char.IsAsciiLetterOrDigit(character) || character is '_' or '-');

    private static string CleanText(string value, int maximumLength)
    {
        var normalized = string.Join(' ', value.Split(
            (char[]?)null,
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        return normalized.Length <= maximumLength ? normalized : normalized[..maximumLength].Trim();
    }

    public void Dispose()
    {
        if (ownsHttpClient) http.Dispose();
    }
}
