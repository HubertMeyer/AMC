using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

namespace AccessibleMediaController.Core.YouTube;

public sealed record YouTubeSubscription(
    string SubscriptionId,
    string ChannelId,
    string Title,
    Uri? ThumbnailUri);

/// <summary>
/// Odczyt subskrypcji zalogowanego użytkownika z oficjalnego YouTube Data
/// API v3. Klient wykonuje wyłącznie GET, obsługuje wszystkie strony i nie zna
/// Biblioteki AMC; polityka importu pozostaje osobną warstwą.
/// </summary>
public sealed class YouTubeSubscriptionClient : IDisposable
{
    private static readonly Uri Endpoint =
        new("https://www.googleapis.com/youtube/v3/subscriptions");
    private const int MaxPages = 200;
    private readonly HttpClient _http;
    private readonly bool _ownsHttpClient;

    public YouTubeSubscriptionClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
        _ownsHttpClient = httpClient is null;
    }

    public async Task<IReadOnlyList<YouTubeSubscription>> ReadAllAsync(
        string accessToken,
        CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(accessToken) || accessToken.Length > 8192)
            throw new InvalidOperationException("Najpierw zaloguj się do YouTube.");

        var result = new List<YouTubeSubscription>();
        var channelIds = new HashSet<string>(StringComparer.Ordinal);
        var pageTokens = new HashSet<string>(StringComparer.Ordinal);
        string? pageToken = null;

        for (var page = 0; page < MaxPages; page++)
        {
            if (pageToken is not null && !pageTokens.Add(pageToken))
                throw new InvalidDataException("YouTube zwrócił powtarzającą się stronę subskrypcji.");
            using var request = new HttpRequestMessage(HttpMethod.Get, BuildUri(pageToken));
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
            using var response = await _http.SendAsync(request, cancellationToken).ConfigureAwait(false);
            var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
                throw new InvalidOperationException(DescribeFailure(response.StatusCode, body));

            var parsed = ParsePage(body);
            foreach (var item in parsed.Items)
            {
                if (channelIds.Add(item.ChannelId)) result.Add(item);
            }
            pageToken = parsed.NextPageToken;
            if (string.IsNullOrWhiteSpace(pageToken)) return result;
        }

        throw new InvalidDataException(
            "Lista subskrypcji YouTube jest zbyt duża, aby bezpiecznie pobrać ją w jednym przebiegu.");
    }

    private static Uri BuildUri(string? pageToken)
    {
        var fields = new Dictionary<string, string>
        {
            ["part"] = "snippet",
            ["mine"] = "true",
            ["maxResults"] = "50"
        };
        if (!string.IsNullOrWhiteSpace(pageToken)) fields["pageToken"] = pageToken;
        var query = string.Join('&', fields.Select(pair =>
            $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}"));
        return new UriBuilder(Endpoint) { Query = query }.Uri;
    }

    private static SubscriptionPage ParsePage(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            var root = document.RootElement;
            var nextPageToken = root.TryGetProperty("nextPageToken", out var next)
                ? next.GetString()?.Trim()
                : null;
            if (nextPageToken?.Length > 512)
                throw new InvalidDataException("YouTube zwrócił nieprawidłowy znacznik strony subskrypcji.");
            var items = new List<YouTubeSubscription>();
            if (!root.TryGetProperty("items", out var array)
                || array.ValueKind != JsonValueKind.Array)
                return new SubscriptionPage(items, nextPageToken);

            foreach (var element in array.EnumerateArray())
            {
                if (!element.TryGetProperty("snippet", out var snippet)
                    || !snippet.TryGetProperty("resourceId", out var resource)
                    || !resource.TryGetProperty("channelId", out var channelElement))
                    continue;
                var channelId = channelElement.GetString()?.Trim();
                if (string.IsNullOrWhiteSpace(channelId) || channelId.Length > 256) continue;
                var subscriptionId = element.TryGetProperty("id", out var idElement)
                    ? idElement.GetString()?.Trim() ?? string.Empty
                    : string.Empty;
                if (subscriptionId.Length > 512) subscriptionId = string.Empty;
                var title = snippet.TryGetProperty("title", out var titleElement)
                    ? TrimBounded(titleElement.GetString(), 1000)
                    : null;
                items.Add(new YouTubeSubscription(
                    subscriptionId,
                    channelId,
                    string.IsNullOrWhiteSpace(title) ? "Kanał YouTube" : title,
                    ReadThumbnail(snippet)));
            }
            return new SubscriptionPage(items, nextPageToken);
        }
        catch (JsonException)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelną listę subskrypcji.");
        }
    }

    private static Uri? ReadThumbnail(JsonElement snippet)
    {
        if (!snippet.TryGetProperty("thumbnails", out var thumbnails)) return null;
        foreach (var name in new[] { "medium", "default", "high" })
        {
            if (!thumbnails.TryGetProperty(name, out var thumbnail)
                || !thumbnail.TryGetProperty("url", out var urlElement))
                continue;
            var value = TrimBounded(urlElement.GetString(), 2048);
            if (Uri.TryCreate(value, UriKind.Absolute, out var uri)
                && uri.Scheme == Uri.UriSchemeHttps)
                return uri;
        }
        return null;
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
            return "YouTube odmówił dostępu do subskrypcji tego konta.";
        return "Nie udało się pobrać subskrypcji YouTube.";
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
            {
                if (item.TryGetProperty("reason", out var reason)) return reason.GetString()?.Trim();
            }
            return null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static string? TrimBounded(string? value, int limit)
    {
        var normalized = value?.Trim();
        if (string.IsNullOrEmpty(normalized)) return null;
        return normalized.Length <= limit ? normalized : normalized[..limit];
    }

    public void Dispose()
    {
        if (_ownsHttpClient) _http.Dispose();
    }

    private sealed record SubscriptionPage(
        IReadOnlyList<YouTubeSubscription> Items,
        string? NextPageToken);
}
