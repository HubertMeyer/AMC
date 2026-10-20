using System.Net;
using System.Net.Http.Headers;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeSubscriptionClientTests
{
    internal static void Run()
    {
        ReadsAllPagesAndDeduplicatesByChannelId();
        RejectsRepeatedPageToken();
        ReportsQuotaWithoutEchoingServerBody();
        ReportsAccountWithoutYouTubeChannel();
        SkipsRowsWithoutStableChannelIdentity();
        Console.WriteLine("OK: oficjalny odczyt subskrypcji YouTube (5 scenariuszy)");
    }

    private static void ReadsAllPagesAndDeduplicatesByChannelId()
    {
        var handler = new PagesHandler(
            Json("{\"nextPageToken\":\"DRUGA\",\"items\":["
                + Item("sub-1", "UC-1", "Kanał pierwszy", "https://img.example/1.jpg") + ","
                + Item("sub-2", "UC-2", "Kanał drugi", "http://niebezpieczny.example/2.jpg") + "]}"),
            Json("{\"items\":[" + Item("sub-1b", "UC-1", "Duplikat", null) + ","
                + Item("sub-3", "UC-3", "Kanał trzeci", null) + "]}"));
        using var client = new YouTubeSubscriptionClient(new HttpClient(handler));
        var rows = client.ReadAllAsync("syntetyczny-token", CancellationToken.None)
            .GetAwaiter().GetResult();

        Assert(rows.Select(row => row.ChannelId).SequenceEqual(new[] { "UC-1", "UC-2", "UC-3" }),
            "Stronicowanie nie zachowało stabilnych kanałów albo dopuściło duplikat.");
        Assert(rows[0].ThumbnailUri?.Scheme == "https" && rows[1].ThumbnailUri is null,
            "Klient przyjął niebezpieczny adres miniatury albo zgubił HTTPS.");
        Assert(handler.Requests.Count == 2
               && handler.Requests[0].Query["part"] == "snippet"
               && handler.Requests[0].Query["mine"] == "true"
               && handler.Requests[0].Query["maxResults"] == "50"
               && handler.Requests[1].Query["pageToken"] == "DRUGA",
            "Żądania nie używają oficjalnego kontraktu stronicowania subscriptions.list.");
        Assert(handler.Requests.All(request => request.Authorization?.Scheme == "Bearer"
                                               && request.Authorization.Parameter == "syntetyczny-token"),
            "Token nie został przekazany wyłącznie w nagłówku Bearer.");
    }

    private static void RejectsRepeatedPageToken()
    {
        const string page = "{\"nextPageToken\":\"TO-SAMO\",\"items\":[]}";
        var handler = new PagesHandler(Json(page), Json(page), Json(page));
        using var client = new YouTubeSubscriptionClient(new HttpClient(handler));
        var rejected = false;
        try { _ = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult(); }
        catch (InvalidDataException exception)
        {
            rejected = exception.Message.Contains("powtarzającą", StringComparison.Ordinal);
        }
        Assert(rejected && handler.Requests.Count == 2,
            "Powtórzony token strony wywołałby nieskończone pobieranie.");
    }

    private static void ReportsQuotaWithoutEchoingServerBody()
    {
        const string marker = "PRYWATNA-TRESC-SERWERA";
        var handler = new PagesHandler(new HttpResponseMessage(HttpStatusCode.Forbidden)
        {
            Content = new StringContent("{\"error\":{\"errors\":[{\"reason\":\"quotaExceeded\",\"message\":\""
                + marker + "\"}]}}")
        });
        using var client = new YouTubeSubscriptionClient(new HttpClient(handler));
        try
        {
            _ = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult();
            throw new InvalidOperationException("Przekroczenie limitu zostało przyjęte jako sukces.");
        }
        catch (InvalidOperationException exception)
        {
            Assert(exception.Message.Contains("dzienny limit", StringComparison.Ordinal)
                   && !exception.ToString().Contains(marker, StringComparison.Ordinal),
                "Limit nie dostał użytkowego komunikatu albo ujawnił odpowiedź serwera.");
        }
    }

    private static void ReportsAccountWithoutYouTubeChannel()
    {
        var handler = new PagesHandler(new HttpResponseMessage(HttpStatusCode.Forbidden)
        {
            Content = new StringContent(
                "{\"error\":{\"errors\":[{\"reason\":\"youtubeSignupRequired\"}]}}")
        });
        using var client = new YouTubeSubscriptionClient(new HttpClient(handler));
        try
        {
            _ = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult();
            throw new InvalidOperationException("Brak kanału został przyjęty jako sukces.");
        }
        catch (InvalidOperationException exception)
        {
            Assert(exception.Message == "To konto Google nie ma jeszcze kanału YouTube.",
                "Brak kanału nie ma jednoznacznego komunikatu.");
        }
    }

    private static void SkipsRowsWithoutStableChannelIdentity()
    {
        var handler = new PagesHandler(Json(
            "{\"items\":[{\"id\":\"sub-brak\",\"snippet\":{\"title\":\"Bez identyfikatora\"}},"
            + Item("sub-ok", "UC-OK", "", null) + "]}"));
        using var client = new YouTubeSubscriptionClient(new HttpClient(handler));
        var rows = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult();
        Assert(rows.Count == 1 && rows[0].ChannelId == "UC-OK" && rows[0].Title == "Kanał YouTube",
            "Wiersz bez tożsamości trafiłby do synchronizacji albo pusta nazwa wyciekła do NVDA.");
    }

    private static string Item(string subscriptionId, string channelId, string title, string? thumbnail) =>
        "{\"id\":\"" + subscriptionId + "\",\"snippet\":{\"title\":\"" + title
        + "\",\"resourceId\":{\"channelId\":\"" + channelId + "\"}"
        + (thumbnail is null
            ? string.Empty
            : ",\"thumbnails\":{\"medium\":{\"url\":\"" + thumbnail + "\"}}")
        + "}}";

    private static HttpResponseMessage Json(string body) => new(HttpStatusCode.OK)
    {
        Content = new StringContent(body)
    };

    private static Dictionary<string, string> ParseQuery(string query) =>
        query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries)
            .Select(part => part.Split('=', 2))
            .ToDictionary(
                pair => Uri.UnescapeDataString(pair[0]),
                pair => pair.Length == 2 ? Uri.UnescapeDataString(pair[1]) : string.Empty,
                StringComparer.Ordinal);

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed record CapturedRequest(
        Uri Uri,
        AuthenticationHeaderValue? Authorization,
        Dictionary<string, string> Query);

    private sealed class PagesHandler(params HttpResponseMessage[] responses) : HttpMessageHandler
    {
        private readonly Queue<HttpResponseMessage> _responses = new(responses);
        internal List<CapturedRequest> Requests { get; } = [];

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            Requests.Add(new CapturedRequest(
                request.RequestUri!, request.Headers.Authorization,
                ParseQuery(request.RequestUri!.Query)));
            if (_responses.Count == 0)
                throw new InvalidOperationException("Atrapa nie ma kolejnej odpowiedzi.");
            return Task.FromResult(_responses.Dequeue());
        }
    }
}
