using System.Net;
using System.Net.Http.Headers;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeBroadcastClientTests
{
    internal static void Run()
    {
        ReadsLiveAndUpcomingWithDetails();
        ReportsQuotaWithoutEchoingServerBody();
        RejectsUnsafeChannelIdentityBeforeNetwork();
        Console.WriteLine("OK: transmisje YouTube na żywo i zaplanowane (3 scenariusze)");
    }

    private static void ReadsLiveAndUpcomingWithDetails()
    {
        var handler = new QueueHandler(
            Json("""{"items":[{"id":{"videoId":"LIVE_1"},"snippet":{"title":"Msza teraz","channelTitle":"Parafia"}}]}"""),
            Json("""{"items":[{"id":{"videoId":"NEXT_2"},"snippet":{"title":"Msza wieczorna","channelTitle":"Parafia"}}]}"""),
            Json("""{"items":[{"id":"LIVE_1","snippet":{"title":"Msza teraz","channelTitle":"Parafia"},"liveStreamingDetails":{"actualStartTime":"2026-10-23T16:00:00Z"}},{"id":"NEXT_2","snippet":{"title":"Msza wieczorna","channelTitle":"Parafia"},"liveStreamingDetails":{"scheduledStartTime":"2026-10-23T18:00:00Z"}}]}"""));
        using var client = new YouTubeBroadcastClient(new HttpClient(handler));
        var rows = client.ReadChannelAsync("syntetyczny-token", "UC_test-123", CancellationToken.None)
            .GetAwaiter().GetResult();

        Assert(rows.Count == 2
               && rows[0].State == YouTubeBroadcastState.Live
               && rows[0].PageUri.AbsoluteUri == "https://www.youtube.com/watch?v=LIVE_1"
               && rows[0].ActualStartUtc == DateTimeOffset.Parse("2026-10-23T16:00:00Z")
               && rows[1].State == YouTubeBroadcastState.Upcoming
               && rows[1].ScheduledStartUtc == DateTimeOffset.Parse("2026-10-23T18:00:00Z"),
            "Klient nie zachował stanu, czasu albo publicznego adresu transmisji.");
        Assert(handler.Requests.Count == 3
               && handler.Requests[0].Query["eventType"] == "live"
               && handler.Requests[1].Query["eventType"] == "upcoming"
               && handler.Requests.Take(2).All(request => request.Query["channelId"] == "UC_test-123")
               && handler.Requests[2].Query["part"] == "snippet,liveStreamingDetails"
               && handler.Requests.All(request => request.Authorization?.Scheme == "Bearer"
                                                && request.Authorization.Parameter == "syntetyczny-token"),
            "Żądania nie używają oficjalnego filtra kanału, stanów i nagłówka Bearer.");
    }

    private static void ReportsQuotaWithoutEchoingServerBody()
    {
        const string marker = "PRYWATNA-TRESC-SERWERA";
        var handler = new QueueHandler(new HttpResponseMessage(HttpStatusCode.Forbidden)
        {
            Content = new StringContent("{\"error\":{\"errors\":[{\"reason\":\"quotaExceeded\",\"message\":\""
                                        + marker + "\"}]}}")
        });
        using var client = new YouTubeBroadcastClient(new HttpClient(handler));
        try
        {
            _ = client.ReadChannelAsync("token", "UC_test", CancellationToken.None)
                .GetAwaiter().GetResult();
            throw new InvalidOperationException("Przekroczenie limitu zostało przyjęte jako sukces.");
        }
        catch (InvalidOperationException exception)
        {
            Assert(exception.Message.Contains("limit wyszukiwania", StringComparison.Ordinal)
                   && !exception.ToString().Contains(marker, StringComparison.Ordinal),
                "Limit nie dostał użytkowego komunikatu albo ujawnił odpowiedź serwera.");
        }
    }

    private static void RejectsUnsafeChannelIdentityBeforeNetwork()
    {
        var handler = new QueueHandler();
        using var client = new YouTubeBroadcastClient(new HttpClient(handler));
        try
        {
            _ = client.ReadChannelAsync("token", "../sekret", CancellationToken.None)
                .GetAwaiter().GetResult();
            throw new InvalidOperationException("Niebezpieczny identyfikator kanału został przyjęty.");
        }
        catch (InvalidDataException exception)
        {
            Assert(exception.Message.Contains("stabilnego identyfikatora", StringComparison.Ordinal)
                   && handler.Requests.Count == 0,
                "Odmowa nie ma użytkowego opisu albo nastąpiła dopiero po sieci.");
        }
    }

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
        AuthenticationHeaderValue? Authorization,
        Dictionary<string, string> Query);

    private sealed class QueueHandler(params HttpResponseMessage[] responses) : HttpMessageHandler
    {
        private readonly Queue<HttpResponseMessage> _responses = new(responses);
        internal List<CapturedRequest> Requests { get; } = [];

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            Requests.Add(new CapturedRequest(
                request.Headers.Authorization,
                ParseQuery(request.RequestUri!.Query)));
            if (_responses.Count == 0)
                throw new InvalidOperationException("Atrapa nie ma kolejnej odpowiedzi.");
            return Task.FromResult(_responses.Dequeue());
        }
    }
}
