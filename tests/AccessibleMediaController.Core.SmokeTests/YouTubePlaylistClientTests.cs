using System.Net;
using System.Net.Http.Headers;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubePlaylistClientTests
{
    internal static void Run()
    {
        ReadsOwnedPlaylistsAndFirstHundredVideos();
        RejectsRepeatedPlaylistPageToken();
        ReportsQuotaWithoutEchoingServerBody();
        Console.WriteLine("OK: oficjalny odczyt playlist YouTube (3 scenariusze)");
    }

    private static void ReadsOwnedPlaylistsAndFirstHundredVideos()
    {
        var firstVideos = string.Join(',', Enumerable.Range(1, 50).Select(Video));
        var secondVideos = string.Join(',', Enumerable.Range(51, 50).Select(Video));
        var handler = new PagesHandler(
            Json("{\"items\":[{\"id\":\"PL-PIERWSZA\",\"snippet\":{" +
                "\"title\":\" Moja  playlista \",\"channelTitle\":\"Kanał\"}," +
                "\"status\":{\"privacyStatus\":\"private\"}," +
                "\"contentDetails\":{\"itemCount\":101}}]}"),
            Json("{\"nextPageToken\":\"DRUGA\",\"items\":[" + firstVideos + "]}"),
            Json("{\"nextPageToken\":\"TRZECIA\",\"items\":[" + secondVideos + "]}"));
        using var client = new YouTubePlaylistClient(new HttpClient(handler));
        var rows = client.ReadAllAsync("syntetyczny-token", CancellationToken.None)
            .GetAwaiter().GetResult();

        var playlist = rows.Single();
        Assert(playlist.Title == "Moja playlista"
               && playlist.PrivacyStatus == "private"
               && playlist.TotalItemCount == 101
               && playlist.Videos.Count == 100
               && playlist.VideosTruncated,
            "Klient nie zachował metadanych albo limitu pierwszych 100 materiałów.");
        Assert(handler.Requests.Count == 3
               && handler.Requests[0].Path.EndsWith("/playlists", StringComparison.Ordinal)
               && handler.Requests[0].Query["mine"] == "true"
               && handler.Requests[0].Query["part"] == "snippet,status,contentDetails"
               && handler.Requests[1].Query["playlistId"] == "PL-PIERWSZA"
               && handler.Requests[2].Query["pageToken"] == "DRUGA",
            "Żądania nie używają oficjalnego kontraktu playlists.list i playlistItems.list.");
        Assert(handler.Requests.All(request => request.Authorization?.Scheme == "Bearer"
                                               && request.Authorization.Parameter == "syntetyczny-token"),
            "Token nie został przekazany wyłącznie w nagłówku Bearer.");
    }

    private static void RejectsRepeatedPlaylistPageToken()
    {
        const string page = "{\"nextPageToken\":\"TO-SAMO\",\"items\":[]}";
        var handler = new PagesHandler(Json(page), Json(page));
        using var client = new YouTubePlaylistClient(new HttpClient(handler));
        try
        {
            _ = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult();
            throw new InvalidOperationException("Powtórzony token został zaakceptowany.");
        }
        catch (InvalidDataException exception)
        {
            Assert(exception.Message.Contains("powtarzającą", StringComparison.Ordinal)
                   && handler.Requests.Count == 2,
                "Powtórzony token strony nie zatrzymał pobierania playlist.");
        }
    }

    private static void ReportsQuotaWithoutEchoingServerBody()
    {
        const string marker = "PRYWATNA-TRESC-SERWERA";
        var handler = new PagesHandler(new HttpResponseMessage(HttpStatusCode.Forbidden)
        {
            Content = new StringContent(
                "{\"error\":{\"errors\":[{\"reason\":\"quotaExceeded\",\"message\":\"" +
                marker + "\"}]}}")
        });
        using var client = new YouTubePlaylistClient(new HttpClient(handler));
        try
        {
            _ = client.ReadAllAsync("token", CancellationToken.None).GetAwaiter().GetResult();
            throw new InvalidOperationException("Przekroczenie limitu zostało przyjęte jako sukces.");
        }
        catch (InvalidOperationException exception)
        {
            Assert(exception.Message.Contains("dzienny limit", StringComparison.Ordinal)
                   && !exception.ToString().Contains(marker, StringComparison.Ordinal),
                "Limit nie dostał bezpiecznego komunikatu albo ujawnił odpowiedź serwera.");
        }
    }

    private static string Video(int ordinal)
    {
        var id = $"Video{ordinal:000000}";
        return "{\"snippet\":{\"title\":\"Materiał " + ordinal +
               "\",\"videoOwnerChannelTitle\":\"Kanał\",\"publishedAt\":\"2026-10-23T12:00:00Z\"}," +
               "\"contentDetails\":{\"videoId\":\"" + id + "\"}}";
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
        string Path,
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
                request.RequestUri!.AbsolutePath,
                request.Headers.Authorization,
                ParseQuery(request.RequestUri.Query)));
            if (_responses.Count == 0)
                throw new InvalidOperationException("Atrapa nie ma kolejnej odpowiedzi.");
            return Task.FromResult(_responses.Dequeue());
        }
    }
}
