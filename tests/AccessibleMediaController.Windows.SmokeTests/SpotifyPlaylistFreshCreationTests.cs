using System.Net;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Core.Spotify;
using AccessibleMediaController.Windows.Services;

internal static class SpotifyPlaylistFreshCreationTests
{
    public static void Run()
    {
        using var handler = new DelayedPlaylistListStub();
        using var http = new HttpClient(handler);
        var settings = new SpotifySettings
        {
            ClientId = "test",
            GrantedScope = SpotifyScopes.Requested
        };
        using var service = new SpotifyIntegrationService(
            settings,
            http,
            _ => Task.FromResult(new SpotifyTokenSet(
                "token-testowy",
                "odswiezenie-testowe",
                DateTimeOffset.UtcNow.AddHours(1),
                SpotifyScopes.Requested,
                "Bearer")));

        var created = service.CreatePlaylistAsync(
                "Nowa publiczna",
                true,
                CancellationToken.None)
            .GetAwaiter().GetResult();
        var targets = service.GetEditablePlaylistsAsync(CancellationToken.None)
            .GetAwaiter().GetResult();
        Check(targets.Any(target => target.Id == created.Id),
            "potwierdzona nowa playlista zniknęła, gdy /me/playlists było jeszcze niespójne");

        var item = new MediaItem
        {
            Title = "Utwór testowy",
            Kind = MediaItemKind.Track,
            ExternalId = "track-1"
        };
        var result = service.AddItemsToPlaylistsAsync(
                [created.Id],
                [item],
                CancellationToken.None)
            .GetAwaiter().GetResult();
        Check(result.AddedCount == 1 && handler.AddRequests == 1,
            "świeżo utworzona playlista nie przyjęła elementu przed pojawieniem się w katalogu");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException($"Playlisty Spotify: {message}.");
    }

    private sealed class DelayedPlaylistListStub : HttpMessageHandler
    {
        public int AddRequests { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            var uri = request.RequestUri?.AbsoluteUri ?? string.Empty;
            if (request.Method == HttpMethod.Get && uri.EndsWith("/v1/me", StringComparison.Ordinal))
                return Json("""{"id":"user-1","display_name":"Użytkownik","product":"premium","country":"PL"}""");
            if (request.Method == HttpMethod.Get && uri.Contains("/me/playlists", StringComparison.Ordinal))
                return Json("""{"items":[],"next":null}""");
            if (request.Method == HttpMethod.Post && uri.EndsWith("/me/playlists", StringComparison.Ordinal))
            {
                var body = await request.Content!.ReadAsStringAsync(cancellationToken);
                using var document = JsonDocument.Parse(body);
                var name = document.RootElement.GetProperty("name").GetString();
                return Json(JsonSerializer.Serialize(new
                {
                    id = "created-1",
                    name,
                    @public = true,
                    collaborative = false,
                    snapshot_id = "created",
                    owner = new { id = "user-1", display_name = "Użytkownik" }
                }), HttpStatusCode.Created);
            }
            if (request.Method == HttpMethod.Get && uri.Contains("/playlists/created-1/items", StringComparison.Ordinal))
                return Json("""{"items":[],"next":null}""");
            if (request.Method == HttpMethod.Post && uri.Contains("/playlists/created-1/items", StringComparison.Ordinal))
            {
                AddRequests++;
                return Json("""{"snapshot_id":"after-add"}""", HttpStatusCode.Created);
            }
            return new HttpResponseMessage(HttpStatusCode.NotFound);
        }

        private static HttpResponseMessage Json(
            string body,
            HttpStatusCode status = HttpStatusCode.OK) => new(status)
        {
            Content = new StringContent(body, Encoding.UTF8, "application/json")
        };
    }
}
