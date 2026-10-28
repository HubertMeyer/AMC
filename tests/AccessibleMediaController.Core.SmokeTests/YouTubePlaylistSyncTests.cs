using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubePlaylistSyncTests
{
    internal static void Run()
    {
        PreviewDoesNotMutateAndApplyStoresVideos();
        UpdatesExistingPlaylistWithoutLosingLocalTitle();
        KeepsSuppressedUntilExplicitRestore();
        RemoteAbsenceNeverRemovesLocalPlaylist();
        Console.WriteLine("OK: atomowa synchronizacja playlist YouTube (4 scenariusze)");
    }

    private static void PreviewDoesNotMutateAndApplyStoresVideos()
    {
        WithDatabase(new PodcastSettings(), (database, store) =>
        {
            var remote = Playlist("PL-NOWA", "Nowa playlista", Video("Film0000001", "Film pierwszy"));
            var preview = store.PreviewYouTubePlaylists([remote]);
            Assert(preview.Additions == 1 && preview.Actions.Count == 1
                   && store.GetRefreshTargets().Count == 0,
                "Podgląd playlist zmienił Bibliotekę przed potwierdzeniem.");

            var applied = store.ApplyYouTubePlaylists([remote]);
            Assert(applied.Added == 1 && applied.AddedVideos == 1,
                "Jawny zapis nie dodał playlisty i materiału.");
            var settings = new PodcastSettings();
            database.LoadInto(settings);
            Assert(settings.Subscriptions.Single().SourceKind == PodcastSourceKind.YouTubePlaylist
                   && settings.Subscriptions.Single().IsInLibrary
                   && settings.Subscriptions.Single().IsYouTubeAccountData
                   && settings.Subscriptions.Single().YouTubeAccountDataRefreshedUtcTicks > 0
                   && settings.Subscriptions.Single().Description == "Opis playlisty z YouTube."
                   && settings.Episodes.Single().SourceIdentifier == "Film0000001"
                   && settings.Episodes.Single().Description == "Pełny opis materiału."
                   && settings.Episodes.Single().MediaType == "video/youtube",
                "Playlista nie została zapisana jako dostępne źródło YouTube.");
        });
    }

    private static void UpdatesExistingPlaylistWithoutLosingLocalTitle()
    {
        var initial = new PodcastSettings();
        var first = Playlist("PL-STALA", "Nazwa z YouTube", Video("Film0000001", "Pierwszy"));
        YouTubePlaylistSyncApplier.Apply([first], initial);
        var subscription = initial.Subscriptions.Single();
        subscription.Title = "Moja nazwa lokalna";
        subscription.HasCustomTitle = true;

        WithDatabase(initial, (database, store) =>
        {
            var second = Playlist(
                "PL-STALA",
                "Zmieniona nazwa z YouTube",
                Video("Film0000001", "Pierwszy poprawiony"),
                Video("Film0000002", "Drugi"));
            var preview = store.PreviewYouTubePlaylists([second]);
            Assert(preview.Updates == 1 && preview.Additions == 0,
                "Istniejąca playlista nie została zaplanowana jako aktualizacja.");
            var applied = store.ApplyYouTubePlaylists([second]);
            var settings = new PodcastSettings();
            database.LoadInto(settings);
            Assert(applied.Updated == 1 && applied.AddedVideos == 1
                   && settings.Subscriptions.Single().Title == "Moja nazwa lokalna"
                   && settings.Episodes.Count == 2,
                "Aktualizacja zgubiła lokalną nazwę albo nie dopisała materiału.");
        });
    }

    private static void KeepsSuppressedUntilExplicitRestore()
    {
        var settings = new PodcastSettings();
        YouTubePlaylistSyncApplier.Apply([Playlist("PL-USUNIETA", "Usunięta")], settings);
        settings.Subscriptions.Single().IsInLibrary = false;
        WithDatabase(settings, (database, store) =>
        {
            var remote = Playlist("PL-USUNIETA", "Usunięta");
            var ordinary = store.ApplyYouTubePlaylists([remote]);
            Assert(ordinary.Suppressed == 1 && ordinary.Changed == 0,
                "Zwykła synchronizacja przywróciła świadomie usuniętą playlistę.");
            var restored = store.ApplyYouTubePlaylists([remote], restoreSuppressed: true);
            var loaded = new PodcastSettings();
            database.LoadInto(loaded);
            Assert(restored.Restored == 1 && loaded.Subscriptions.Single().IsInLibrary,
                "Jawne przywrócenie playlisty nie zadziałało.");
        });
    }

    private static void RemoteAbsenceNeverRemovesLocalPlaylist()
    {
        var settings = new PodcastSettings();
        YouTubePlaylistSyncApplier.Apply([Playlist("PL-LOKALNA", "Lokalna")], settings);
        WithDatabase(settings, (database, store) =>
        {
            var applied = store.ApplyYouTubePlaylists([]);
            var loaded = new PodcastSettings();
            database.LoadInto(loaded);
            Assert(applied.Changed == 0 && loaded.Subscriptions.Single().IsInLibrary,
                "Brak po stronie YouTube usunął lokalną playlistę.");
        });
    }

    private static YouTubeAccountPlaylist Playlist(
        string id,
        string title,
        params YouTubePlaylistVideo[] videos) =>
        new(id, title, "Kanał", "Opis playlisty z YouTube.", "public", videos.Length, videos, false);

    private static YouTubePlaylistVideo Video(string id, string title) =>
        new(id, title, "Kanał", "Pełny opis materiału.", DateTimeOffset.Parse("2026-10-23T12:00:00Z"));

    private static void WithDatabase(
        PodcastSettings initial,
        Action<PodcastLibraryDatabase, PodcastLibraryMutationStore> action)
    {
        var directory = Path.Combine(
            Path.GetTempPath(),
            "amc-youtube-playlist-sync-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            var path = Path.Combine(directory, "podcasts.db");
            var database = new PodcastLibraryDatabase(path);
            database.Initialize(initial);
            action(database, new PodcastLibraryMutationStore(path));
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
