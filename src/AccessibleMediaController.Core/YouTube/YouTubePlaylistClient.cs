using System.Globalization;
using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

namespace AccessibleMediaController.Core.YouTube;

public sealed record YouTubePlaylistVideo(
    string VideoId,
    string Title,
    string ChannelTitle,
    DateTimeOffset? Published);

public sealed record YouTubeAccountPlaylist(
    string PlaylistId,
    string Title,
    string ChannelTitle,
    string PrivacyStatus,
    int TotalItemCount,
    IReadOnlyList<YouTubePlaylistVideo> Videos,
    bool VideosTruncated);

/// <summary>
/// Odczytuje własne playlisty zalogowanego konta przez oficjalne YouTube Data
/// API v3. Klient wykonuje wyłącznie GET i świadomie ogranicza każdą playlistę
/// do pierwszych stu pozycji, zgodnie z limitem kolekcji YouTube w AMC.
/// </summary>
public sealed class YouTubePlaylistClient : IDisposable
{
    private static readonly Uri ApiRoot = new("https://www.googleapis.com/youtube/v3/");
    private const int MaximumPlaylistPages = 200;
    private const int MaximumVideos = 100;
    private const int MaximumVideoPages = MaximumVideos / 50;
    private readonly HttpClient _http;
    private readonly bool _ownsHttpClient;

    public YouTubePlaylistClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
        _ownsHttpClient = httpClient is null;
    }

    public async Task<IReadOnlyList<YouTubeAccountPlaylist>> ReadAllAsync(
        string accessToken,
        CancellationToken cancellationToken)
    {
        ValidateToken(accessToken);
        var metadata = new List<PlaylistMetadata>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        var pageTokens = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;

        for (var page = 0; page < MaximumPlaylistPages; page++)
        {
            if (pageToken is not null && !pageTokens.Add(pageToken))
                throw new InvalidDataException("YouTube zwrócił powtarzającą się stronę playlist.");
            var response = await GetAsync(
                BuildUri("playlists",
                    ("part", "snippet,status,contentDetails"),
                    ("mine", "true"),
                    ("maxResults", "50"),
                    ("pageToken", pageToken ?? string.Empty)),
                accessToken,
                cancellationToken).ConfigureAwait(false);
            var parsed = ParsePlaylistPage(response);
            foreach (var item in parsed.Items)
                if (known.Add(item.PlaylistId)) metadata.Add(item);
            pageToken = parsed.NextPageToken;
            if (string.IsNullOrWhiteSpace(pageToken)) break;
            if (page == MaximumPlaylistPages - 1)
                throw new InvalidDataException(
                    "Lista playlist YouTube jest zbyt duża, aby bezpiecznie pobrać ją w jednym przebiegu.");
        }

        var result = new List<YouTubeAccountPlaylist>(metadata.Count);
        foreach (var playlist in metadata)
        {
            var videos = await ReadVideosAsync(
                playlist.PlaylistId,
                playlist.TotalItemCount,
                accessToken,
                cancellationToken).ConfigureAwait(false);
            result.Add(new YouTubeAccountPlaylist(
                playlist.PlaylistId,
                playlist.Title,
                playlist.ChannelTitle,
                playlist.PrivacyStatus,
                playlist.TotalItemCount,
                videos.Items,
                videos.Truncated));
        }
        return result;
    }

    private async Task<VideoPageResult> ReadVideosAsync(
        string playlistId,
        int totalItemCount,
        string accessToken,
        CancellationToken cancellationToken)
    {
        var result = new List<YouTubePlaylistVideo>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        var pageTokens = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;
        var moreAvailable = false;

        for (var page = 0; page < MaximumVideoPages; page++)
        {
            if (pageToken is not null && !pageTokens.Add(pageToken))
                throw new InvalidDataException(
                    "YouTube zwrócił powtarzającą się stronę materiałów playlisty.");
            var response = await GetAsync(
                BuildUri("playlistItems",
                    ("part", "snippet,contentDetails"),
                    ("playlistId", playlistId),
                    ("maxResults", "50"),
                    ("pageToken", pageToken ?? string.Empty)),
                accessToken,
                cancellationToken).ConfigureAwait(false);
            var parsed = ParseVideoPage(response);
            foreach (var item in parsed.Items)
            {
                if (result.Count >= MaximumVideos) break;
                if (known.Add(item.VideoId)) result.Add(item);
            }
            pageToken = parsed.NextPageToken;
            moreAvailable = !string.IsNullOrWhiteSpace(pageToken);
            if (!moreAvailable) break;
        }

        return new VideoPageResult(
            result,
            moreAvailable || totalItemCount > result.Count);
    }

    private async Task<string> GetAsync(
        Uri uri,
        string accessToken,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, uri);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        using var response = await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(DescribeFailure(response.StatusCode, body));
        return body;
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

    private static PlaylistPage ParsePlaylistPage(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            var next = ReadPageToken(document.RootElement, "playlist");
            var result = new List<PlaylistMetadata>();
            foreach (var item in Items(document.RootElement))
            {
                var id = ReadString(item, "id");
                if (!IsSafeIdentifier(id, 160)) continue;
                var title = CleanText(ReadNestedString(item, "snippet", "title"), 500);
                var channel = CleanText(ReadNestedString(item, "snippet", "channelTitle"), 300);
                var privacy = CleanText(ReadNestedString(item, "status", "privacyStatus"), 40);
                var itemCount = ReadNonNegativeInt(item, "contentDetails", "itemCount");
                result.Add(new PlaylistMetadata(
                    id,
                    title.Length > 0 ? title : "Playlista YouTube",
                    channel.Length > 0 ? channel : "YouTube",
                    NormalizePrivacy(privacy),
                    itemCount));
            }
            return new PlaylistPage(result, next);
        }
        catch (JsonException)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelną listę playlist.");
        }
    }

    private static VideoPage ParseVideoPage(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            var next = ReadPageToken(document.RootElement, "materiałów playlisty");
            var result = new List<YouTubePlaylistVideo>();
            foreach (var item in Items(document.RootElement))
            {
                var id = ReadNestedString(item, "contentDetails", "videoId");
                if (!IsSafeIdentifier(id, 64)) continue;
                var title = CleanText(ReadNestedString(item, "snippet", "title"), 500);
                if (title.Equals("Deleted video", StringComparison.OrdinalIgnoreCase)
                    || title.Equals("Private video", StringComparison.OrdinalIgnoreCase))
                    continue;
                var channel = CleanText(
                    ReadNestedString(item, "snippet", "videoOwnerChannelTitle"),
                    300);
                var published = DateTimeOffset.TryParse(
                    ReadNestedString(item, "snippet", "publishedAt"),
                    CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal,
                    out var parsed)
                    ? parsed
                    : (DateTimeOffset?)null;
                result.Add(new YouTubePlaylistVideo(
                    id,
                    title.Length > 0 ? title : "Materiał YouTube",
                    channel.Length > 0 ? channel : "YouTube",
                    published));
            }
            return new VideoPage(result, next);
        }
        catch (JsonException)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelną zawartość playlisty.");
        }
    }

    private static IEnumerable<JsonElement> Items(JsonElement root)
    {
        if (!root.TryGetProperty("items", out var items) || items.ValueKind != JsonValueKind.Array)
            yield break;
        foreach (var item in items.EnumerateArray()) yield return item;
    }

    private static string? ReadPageToken(JsonElement root, string kind)
    {
        var value = ReadString(root, "nextPageToken");
        if (value.Length > 512)
            throw new InvalidDataException($"YouTube zwrócił nieprawidłowy znacznik strony {kind}.");
        return value.Length == 0 ? null : value;
    }

    private static string ReadNestedString(JsonElement element, params string[] path)
    {
        foreach (var name in path)
        {
            if (element.ValueKind != JsonValueKind.Object
                || !element.TryGetProperty(name, out element)) return string.Empty;
        }
        return element.ValueKind == JsonValueKind.String
            ? element.GetString()?.Trim() ?? string.Empty
            : string.Empty;
    }

    private static string ReadString(JsonElement element, string name) =>
        element.ValueKind == JsonValueKind.Object
        && element.TryGetProperty(name, out var value)
        && value.ValueKind == JsonValueKind.String
            ? value.GetString()?.Trim() ?? string.Empty
            : string.Empty;

    private static int ReadNonNegativeInt(JsonElement element, params string[] path)
    {
        foreach (var name in path)
        {
            if (element.ValueKind != JsonValueKind.Object
                || !element.TryGetProperty(name, out element)) return 0;
        }
        return element.ValueKind == JsonValueKind.Number
               && element.TryGetInt32(out var value)
               && value >= 0
            ? value
            : 0;
    }

    private static string NormalizePrivacy(string value) => value.ToLowerInvariant() switch
    {
        "private" => "private",
        "unlisted" => "unlisted",
        _ => "public"
    };

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

    private static void ValidateToken(string accessToken)
    {
        if (string.IsNullOrWhiteSpace(accessToken) || accessToken.Length > 8192)
            throw new InvalidOperationException("Najpierw zaloguj się do YouTube.");
    }

    private static string DescribeFailure(HttpStatusCode statusCode, string body)
    {
        var reason = ReadErrorReason(body);
        if (statusCode == HttpStatusCode.Unauthorized
            || string.Equals(reason, "authError", StringComparison.OrdinalIgnoreCase)
            || string.Equals(reason, "invalidCredentials", StringComparison.OrdinalIgnoreCase))
            return "Logowanie YouTube straciło ważność. Zaloguj się ponownie.";
        if (string.Equals(reason, "youtubeSignupRequired", StringComparison.OrdinalIgnoreCase))
            return "To konto Google nie ma jeszcze kanału YouTube.";
        if (string.Equals(reason, "quotaExceeded", StringComparison.OrdinalIgnoreCase)
            || string.Equals(reason, "dailyLimitExceeded", StringComparison.OrdinalIgnoreCase))
            return "Wyczerpano dzienny limit YouTube. Spróbuj później.";
        if (statusCode == HttpStatusCode.TooManyRequests)
            return "YouTube chwilowo ograniczył liczbę żądań. Spróbuj później.";
        if (statusCode == HttpStatusCode.Forbidden)
            return "YouTube odmówił dostępu do playlist tego konta.";
        return "Nie udało się pobrać playlist YouTube.";
    }

    private static string? ReadErrorReason(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            if (!document.RootElement.TryGetProperty("error", out var error)
                || !error.TryGetProperty("errors", out var errors)
                || errors.ValueKind != JsonValueKind.Array) return null;
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

    private sealed record PlaylistMetadata(
        string PlaylistId,
        string Title,
        string ChannelTitle,
        string PrivacyStatus,
        int TotalItemCount);
    private sealed record PlaylistPage(IReadOnlyList<PlaylistMetadata> Items, string? NextPageToken);
    private sealed record VideoPage(IReadOnlyList<YouTubePlaylistVideo> Items, string? NextPageToken);
    private sealed record VideoPageResult(IReadOnlyList<YouTubePlaylistVideo> Items, bool Truncated);
}
