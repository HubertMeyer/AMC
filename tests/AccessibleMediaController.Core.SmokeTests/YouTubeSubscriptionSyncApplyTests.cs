using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeSubscriptionSyncApplyTests
{
    internal static void Run()
    {
        AddsShellsForBoundedRefreshAndIsIdempotent();
        KeepsSuppressedUntilExplicitRestore();
        RemoteAbsenceDoesNotRemoveLocalSource();
        ConflictDoesNotPartiallyMutateDatabase();
        Console.WriteLine("OK: atomowy zapis subskrypcji YouTube (4 scenariusze)");
    }

    private static void AddsShellsForBoundedRefreshAndIsIdempotent()
    {
        WithDatabase(new PodcastSettings(), (database, store) =>
        {
            var preview = store.PreviewYouTubeSubscriptions(
                [Remote("UC-JEDEN", "Kanał jeden"), Remote("UC-DWA", "Kanał dwa")]);
            Assert(preview.Actions.Count == 2 && store.GetRefreshTargets().Count == 0,
                "Sam podgląd zmienił Bibliotekę przed potwierdzeniem.");
            var first = store.ApplyYouTubeSubscriptions(
                [Remote("UC-JEDEN", "Kanał jeden"), Remote("UC-DWA", "Kanał dwa")]);
            Assert(first.Added == 2 && first.Changed == 2,
                "Pierwsza synchronizacja nie dodała dwóch źródeł.");

            var due = store.GetDueRefreshTargets(DateTime.UtcNow);
            Assert(due.Count == 2
                   && due.All(item => item.SourceKind == PodcastSourceKind.YouTubeChannel),
                "Nowe źródła nie oczekują na istniejące porcjowane odświeżenie.");
            Assert(due.All(item => item.FeedUrl.EndsWith("/videos", StringComparison.Ordinal)),
                "Zapisano niestabilny adres kanału YouTube.");

            var second = store.ApplyYouTubeSubscriptions(
                [Remote("UC-JEDEN", "Kanał jeden"), Remote("UC-DWA", "Kanał dwa")]);
            Assert(second.Added == 0 && second.AlreadyPresent == 2,
                "Ponowienie synchronizacji utworzyłoby duplikaty.");
            Assert(store.GetRefreshTargets().Count == 2,
                "Ponowienie zmieniło liczbę źródeł.");
        });
    }

    private static void KeepsSuppressedUntilExplicitRestore()
    {
        var settings = new PodcastSettings
        {
            Subscriptions =
            [
                new PodcastSubscriptionSettings
                {
                    Id = "stary-kanal",
                    Title = "Stara nazwa",
                    FeedUrl = "https://www.youtube.com/channel/UC-USUNIETY/videos",
                    SourceKind = PodcastSourceKind.YouTubeChannel,
                    IsInLibrary = false
                }
            ]
        };
        WithDatabase(settings, (_, store) =>
        {
            var ordinary = store.ApplyYouTubeSubscriptions(
                [Remote("UC-USUNIETY", "Nazwa z YouTube")]);
            Assert(ordinary.Changed == 0 && ordinary.Suppressed == 1,
                "Zwykła synchronizacja przywróciła świadomie usunięty kanał.");
            Assert(store.GetRefreshTargets().Count == 0,
                "Usunięty kanał wrócił do aktywnych źródeł.");

            var restored = store.ApplyYouTubeSubscriptions(
                [Remote("UC-USUNIETY", "Nazwa z YouTube")],
                restoreSuppressed: true);
            Assert(restored.Restored == 1 && restored.Added == 0,
                "Jawne przywrócenie nie użyło istniejącego rekordu.");
            var target = store.GetRefreshTargets().Single();
            Assert(target.SubscriptionId == "stary-kanal" && target.Title == "Nazwa z YouTube",
                "Przywrócenie zgubiło tożsamość albo aktualną nazwę kanału.");
        });
    }

    private static void RemoteAbsenceDoesNotRemoveLocalSource()
    {
        var settings = new PodcastSettings
        {
            Subscriptions =
            [
                new PodcastSubscriptionSettings
                {
                    Id = "lokalny-kanal",
                    Title = "Lokalny kanał",
                    FeedUrl = "https://www.youtube.com/channel/UC-LOKALNY/videos",
                    SourceKind = PodcastSourceKind.YouTubeChannel,
                    IsInLibrary = true
                }
            ]
        };
        WithDatabase(settings, (_, store) =>
        {
            var result = store.ApplyYouTubeSubscriptions([]);
            Assert(result.Changed == 0 && store.GetRefreshTargets().Count == 1,
                "Brak subskrypcji w odpowiedzi Google usunął lokalne źródło.");
        });
    }

    private static void ConflictDoesNotPartiallyMutateDatabase()
    {
        var settings = new PodcastSettings
        {
            Subscriptions =
            [
                new PodcastSubscriptionSettings
                {
                    Id = "youtube-account-channel:UC-KOLIZJA",
                    Title = "Inny typ",
                    FeedUrl = "https://example.test/feed.xml",
                    SourceKind = PodcastSourceKind.Rss,
                    IsInLibrary = true
                }
            ]
        };
        WithDatabase(settings, (_, store) =>
        {
            try
            {
                store.ApplyYouTubeSubscriptions(
                    [Remote("UC-NOWY", "Nowy"), Remote("UC-KOLIZJA", "Kolizja")]);
                throw new InvalidOperationException("Sprzeczny profil został zaakceptowany.");
            }
            catch (InvalidDataException)
            {
            }
            var targets = store.GetRefreshTargets();
            Assert(targets.Count == 1 && targets[0].SourceKind == PodcastSourceKind.Rss,
                "Błąd w połowie planu pozostawił częściowy zapis.");
        });
    }

    private static void WithDatabase(
        PodcastSettings initial,
        Action<PodcastLibraryDatabase, PodcastLibraryMutationStore> action)
    {
        var directory = Path.Combine(
            Path.GetTempPath(),
            "amc-youtube-sync-" + Guid.NewGuid().ToString("N"));
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

    private static YouTubeSubscription Remote(string id, string title) =>
        new("subscription-" + id, id, title, null);

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
