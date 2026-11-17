using System.Net;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Spotify;
using AccessibleMediaController.Windows.Services;

/// <summary>
/// Measures the real Spotify catalogue reader through a synthetic HTTP transport.
/// It never contacts Spotify and never reads a stored credential.
/// </summary>
internal static class SpotifyPlaylistAccessMessageTests
{
    internal static void Run()
    {
        using var handler = new ForbiddenPlaylistHandler();
        using var http = new HttpClient(handler);
        using var service = new SpotifyIntegrationService(
            new SpotifySettings { ClientId = "test" },
            http,
            _ => Task.FromResult(new SpotifyTokenSet(
                "test-access-token",
                "test-refresh-token",
                DateTimeOffset.UtcNow.AddHours(1),
                SpotifyScopes.Requested,
                "Bearer")));

        var items = service.GetPlaylistTracksAsync(
                "playlist-other-user",
                CancellationToken.None)
            .GetAwaiter().GetResult();

        Check(items is null && handler.PlaylistRequestCount == 1,
            "HTTP 403 playlisty nie został bezpiecznie rozpoznany jako brak udostępnionej zawartości.");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException($"Playlisty Spotify: {message}");
    }

    private sealed class ForbiddenPlaylistHandler : HttpMessageHandler
    {
        internal int PlaylistRequestCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            var path = request.RequestUri?.AbsolutePath ?? string.Empty;
            if (request.Method == HttpMethod.Get
                && path == "/v1/playlists/playlist-other-user/items")
            {
                PlaylistRequestCount++;
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.Forbidden));
            }
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
        }
    }
}