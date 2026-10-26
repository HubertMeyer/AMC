using System.Net;
using System.Text;
using AccessibleMediaController.Core.AppleMusic;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

internal static class AppleMusicPrototypeTests
{
    public static void Run()
    {
        SearchMapsAccessibleItems();
        LibraryPaginationUsesCatalogIdentity();
        LibraryPlaylistUsesUserToken();
        ArtistNavigationUsesOfficialViews();
        LibraryAndFavoriteWritesUseBothTokens();
        PlaylistWritesUseLibraryIdentity();
        CapabilityContractDoesNotPromiseDeletes();
        Console.WriteLine("Apple Music prototype: OK");
    }

    private static void LibraryPaginationUsesCatalogIdentity()
    {
        var calls = new List<string>();
        var handler = new Handler(request =>
        {
            calls.Add(request.RequestUri!.PathAndQuery);
            Check(request.Headers.TryGetValues("Music-User-Token", out var values)
                  && values.Single() == "user-token",
                "Strona biblioteki nie dostała Music User Token.");
            if (request.RequestUri.AbsolutePath == "/v1/me/library/songs"
                && !request.RequestUri.Query.Contains("offset", StringComparison.Ordinal))
            {
                return Json(HttpStatusCode.OK, """
                    {"data":[{"id":"library-song-1","type":"library-songs","attributes":{"name":"Z biblioteki","artistName":"Wykonawca","playParams":{"catalogId":"catalog-song-1"}}}],"next":"/v1/me/library/songs?offset=100"}
                    """);
            }
            if (request.RequestUri.AbsolutePath == "/v1/me/library/songs")
            {
                return Json(HttpStatusCode.OK, """
                    {"data":[{"id":"library-song-2","type":"library-songs","attributes":{"name":"Tylko w bibliotece","artistName":"Wykonawca"}}]}
                    """);
            }
            return Json(HttpStatusCode.OK, """{"data":[]}""");
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var items = client.GetLibraryAsync("developer-token", "user-token")
            .GetAwaiter().GetResult();
        Check(calls.Count == 6, "Biblioteka nie przeszła po wszystkich typach i następnej stronie.");
        Check(items.Count == 2 && items.All(item => item.IsInLibrary),
            "Biblioteka nie zachowała obu utworów i członkostwa.");
        Check(items.Any(item => item.ExternalId == "songs:catalog-song-1"),
            "Katalogowy odpowiednik utworu bibliotecznego nie został użyty do odtwarzania.");
        Check(items.Any(item => item.ExternalId == "library-songs:library-song-2"),
            "Element bez katalogowego odpowiednika nie zachował bezpiecznej tożsamości bibliotecznej.");
    }

    private static void LibraryPlaylistUsesUserToken()
    {
        var handler = new Handler(request =>
        {
            Check(request.RequestUri!.AbsolutePath == "/v1/me/library/playlists/p.123/tracks",
                "Prywatna playlista nie używa bibliotecznego endpointu utworów.");
            Check(request.Headers.TryGetValues("Music-User-Token", out var values)
                  && values.Single() == "user-token",
                "Otwieranie prywatnej playlisty nie wysłało Music User Token.");
            return Json(HttpStatusCode.OK, """
                {"data":[{"id":"library-song-1","type":"library-songs","attributes":{"name":"Utwór","artistName":"Wykonawca","playParams":{"catalogId":"song-1"}}}]}
                """);
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var playlist = new MediaItem
        {
            Id = "appleMusic:library-playlists:p.123",
            ExternalId = "library-playlists:p.123",
            Title = "Prywatna playlista",
            Kind = MediaItemKind.Playlist
        };
        var items = client.GetContainerItemsAsync(
                "developer-token",
                "pl",
                playlist,
                cancellationToken: default,
                musicUserToken: "user-token")
            .GetAwaiter().GetResult();
        Check(items.Single().ExternalId == "songs:song-1",
            "Utwór z prywatnej playlisty nie został znormalizowany do MusicKit.");
    }

    private static void SearchMapsAccessibleItems()
    {
        var handler = new Handler(request =>
        {
            Check(request.Method == HttpMethod.Get, "Wyszukiwanie musi używać GET.");
            Check(request.RequestUri!.AbsolutePath == "/v1/catalog/pl/search", "Nieprawidłowa ścieżka wyszukiwania.");
            Check(request.RequestUri.Query.Contains("types=songs,albums,artists,playlists,music-videos", StringComparison.Ordinal),
                "Wyszukiwanie nie obejmuje wszystkich uzgodnionych rodzajów.");
            Check(request.Headers.Authorization?.Scheme == "Bearer"
                && request.Headers.Authorization.Parameter == "developer-token", "Brak developer tokenu.");
            Check(!request.Headers.Contains("Music-User-Token"), "Katalog nie powinien wymagać tokenu użytkownika.");
            return Json(HttpStatusCode.OK, """
                {"results":{"songs":{"data":[{"id":"song-1","type":"songs","attributes":{"name":"Piosenka","artistName":"Wykonawca","albumName":"Album","durationInMillis":185000,"url":"https://music.apple.com/pl/song/song-1","isFavorite":true},"relationships":{"albums":{"data":[{"id":"album-1","type":"albums"}]},"artists":{"data":[{"id":"artist-1","type":"artists"}]}}}]},"albums":{"data":[{"id":"album-1","type":"albums","attributes":{"name":"Album","artistName":"Wykonawca","url":"https://music.apple.com/pl/album/album-1"}}]}}}
                """);
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var items = client.SearchCatalogAsync("developer-token", "PL", "Piosenka").GetAwaiter().GetResult();
        Check(items.Count == 2, "Wyszukiwanie nie zmapowało utworu i albumu.");
        var track = items.Single(item => item.Kind == MediaItemKind.Track);
        Check(track.RelatedAlbumExternalId == "albums:album-1", "Brak relacji utworu do albumu.");
        Check(track.RelatedArtistExternalId == "artists:artist-1", "Brak relacji utworu do wykonawcy.");
        Check(track.Duration == TimeSpan.FromSeconds(185), "Nieprawidłowy czas utworu.");
        Check(track.AccessibleLabel == "Piosenka, Wykonawca, utwór", "NVDA nie dostał celowej etykiety.");
        Check(!track.AccessibleLabel.Contains("song-1", StringComparison.Ordinal), "Identyfikator wyciekł do etykiety NVDA.");
    }

    private static void ArtistNavigationUsesOfficialViews()
    {
        var paths = new List<string>();
        var handler = new Handler(request =>
        {
            paths.Add(request.RequestUri!.PathAndQuery);
            return Json(HttpStatusCode.OK, """{"data":[]}""");
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var artist = new MediaItem
        {
            Id = "appleMusic:artists:artist-1", ExternalId = "artists:artist-1",
            Title = "Wykonawca", Kind = MediaItemKind.Artist
        };
        foreach (var section in AppleMusicCapabilities.SupportedArtistSections)
            client.GetContainerItemsAsync("developer-token", "pl", artist, section).GetAwaiter().GetResult();
        Check(paths.Any(path => path.Contains("/view/full-albums", StringComparison.Ordinal)), "Brak widoku albumów wykonawcy.");
        Check(paths.Any(path => path.Contains("/view/top-songs", StringComparison.Ordinal)), "Brak widoku utworów wykonawcy.");
        Check(paths.Any(path => path.Contains("/view/similar-artists", StringComparison.Ordinal)), "Brak podobnych wykonawców.");
    }

    private static void LibraryAndFavoriteWritesUseBothTokens()
    {
        var paths = new List<string>();
        var handler = new Handler(request =>
        {
            paths.Add(request.RequestUri!.PathAndQuery);
            Check(request.Method == HttpMethod.Post, "Modyfikacja Apple Music musi używać POST.");
            Check(request.Headers.Authorization?.Parameter == "developer-token", "Brak developer tokenu przy zapisie.");
            Check(request.Headers.TryGetValues("Music-User-Token", out var values)
                && values.Single() == "user-token", "Brak Music User Token przy zapisie.");
            return new HttpResponseMessage(HttpStatusCode.Accepted) { Content = new ByteArrayContent([]) };
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var item = new MediaItem
        {
            Id = "appleMusic:songs:1", ExternalId = "songs:1", Title = "Utwór", Kind = MediaItemKind.Track
        };
        client.AddToLibraryAsync("developer-token", "user-token", [item]).GetAwaiter().GetResult();
        client.AddToFavoritesAsync("developer-token", "user-token", [item]).GetAwaiter().GetResult();
        Check(paths.Any(path => path.StartsWith("/v1/me/library?", StringComparison.Ordinal)), "Brak zapisu do biblioteki.");
        Check(paths.Any(path => path.StartsWith("/v1/me/favorites?", StringComparison.Ordinal)), "Brak zapisu do ulubionych.");
        Check(paths.All(path => path.Contains("ids", StringComparison.Ordinal) && path.Contains("songs", StringComparison.Ordinal)),
            "Zapisy nie przekazały typu i identyfikatora utworu.");
    }

    private static void PlaylistWritesUseLibraryIdentity()
    {
        var step = 0;
        var handler = new Handler(request =>
        {
            step++;
            Check(request.Headers.Contains("Music-User-Token"), "Playlista wymaga Music User Token.");
            if (step == 1)
            {
                Check(request.RequestUri!.AbsolutePath == "/v1/me/library/playlists", "Nieprawidłowa ścieżka tworzenia playlisty.");
                return Json(HttpStatusCode.Created, """
                    {"data":[{"id":"p.123","type":"library-playlists","attributes":{"name":"Moja playlista","canEdit":true}}]}
                    """);
            }
            Check(request.RequestUri!.AbsolutePath == "/v1/me/library/playlists/p.123/tracks", "Nieprawidłowa ścieżka dodawania utworów.");
            return new HttpResponseMessage(HttpStatusCode.NoContent) { Content = new ByteArrayContent([]) };
        });
        using var client = new AppleMusicApiClient(new HttpClient(handler));
        var playlist = client.CreatePlaylistAsync("developer-token", "user-token", "Moja playlista")
            .GetAwaiter().GetResult();
        Check(playlist.ExternalId == "library-playlists:p.123" && playlist.IsInLibrary,
            "Playlista nie zachowała tożsamości bibliotecznej.");
        var track = new MediaItem
        {
            Id = "appleMusic:songs:1", ExternalId = "songs:1", Title = "Utwór", Kind = MediaItemKind.Track
        };
        client.AddTracksToPlaylistAsync("developer-token", "user-token", playlist, [track])
            .GetAwaiter().GetResult();
        Check(step == 2, "Nie wykonano obu operacji playlisty.");
    }

    private static void CapabilityContractDoesNotPromiseDeletes()
    {
        Check(AppleMusicCapabilities.CanAddToLibrary(MediaItemKind.Album), "Album powinien dać się dodać do biblioteki.");
        Check(!AppleMusicCapabilities.CanRemoveFromLibrary(MediaItemKind.Album),
            "Nie wolno reklamować nieistniejącego DELETE biblioteki.");
        Check(AppleMusicCapabilities.CanAddToFavorites(MediaItemKind.Artist),
            "Wykonawca powinien dać się dodać do ulubionych.");
        Check(!AppleMusicCapabilities.CanRemoveFromFavorites(MediaItemKind.Artist),
            "Nie wolno mylić ratings z usuwaniem Favorites.");
        Check(AppleMusicCapabilities.CanAppendPlaylistTracks, "Dodawanie do playlisty powinno być dostępne.");
        Check(!AppleMusicCapabilities.CanRemovePlaylistTracks && !AppleMusicCapabilities.CanReorderPlaylistTracks,
            "Nie wolno reklamować usuwania ani zmiany kolejności playlisty.");
    }

    private static HttpResponseMessage Json(HttpStatusCode status, string json) => new(status)
    {
        Content = new StringContent(json, Encoding.UTF8, "application/json")
    };

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed class Handler(Func<HttpRequestMessage, HttpResponseMessage> response) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken) => Task.FromResult(response(request));
    }
}
