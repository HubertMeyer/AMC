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
        KeepsFailedAutomaticRefreshFairAndPersistent();
        Console.WriteLine("OK: atomowy zapis subskrypcji YouTube (5 scenariuszy)");
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
        WithDatabase(settings, (database, store) =>
        {
            var ordinary = store.ApplyYouTubeSubscriptions(
                [Remote("UC-USUNIETY", "Nazwa z YouTube")]);
            Assert(ordinary.Changed == 0 && ordinary.Suppressed == 1,
                "Zwykła synchronizacja przywróciła świadomie usunięty kanał.");
            Assert(store.GetRefreshTargets().Count == 0,
                "Usunięty kanał wrócił do aktywnych źródeł.");

            var reopened = new PodcastLibraryMutationStore(database.Path);
            var afterRestart = reopened.ApplyYouTubeSubscriptions(
                [Remote("UC-USUNIETY", "Nazwa z YouTube")]);
            Assert(afterRestart.Changed == 0 && afterRestart.Suppressed == 1
                   && reopened.GetRefreshTargets().Count == 0,
                "Ponowne uruchomienie albo synchronizacja przywróciły usunięty kanał.");

            var restored = reopened.ApplyYouTubeSubscriptions(
                [Remote("UC-USUNIETY", "Nazwa z YouTube")],
                restoreSuppressed: true);
            Assert(restored.Restored == 1 && restored.Added == 0,
                "Jawne przywrócenie nie użyło istniejącego rekordu.");
            var target = reopened.GetRefreshTargets().Single();
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

    private static void KeepsFailedAutomaticRefreshFairAndPersistent()
    {
        var start = new DateTime(2026, 10, 23, 18, 0, 0, DateTimeKind.Utc);
        var settings = new PodcastSettings
        {
            AutomaticRefreshBatchSize = 5,
            YouTubeRefreshIntervalMinutes = 60,
            Subscriptions = Enumerable.Range(1, 6)
                .Select(number => new PodcastSubscriptionSettings
                {
                    Id = $"kanał-{number}",
                    Title = $"Kanał {number}",
                    FeedUrl = $"https://www.youtube.com/channel/UC-KANAL-{number}/videos",
                    SourceKind = PodcastSourceKind.YouTubeChannel,
                    IsInLibrary = true,
                    RefreshIntervalMinutes = 60
                })
                .ToList()
        };
        WithDatabase(settings, (database, store) =>
        {
            var firstBatch = store.GetDueRefreshTargets(start);
            Assert(firstBatch.Count == 5,
                "Pierwszy przebieg nie zachował ustawionego rozmiaru porcji.");
            foreach (var target in firstBatch)
                store.MarkRefreshAttempt(target.SubscriptionId, start);

            var reopened = new PodcastLibraryMutationStore(database.Path);
            var secondBatch = reopened.GetDueRefreshTargets(start.AddMinutes(1));
            Assert(secondBatch.Count == 1 && secondBatch[0].SubscriptionId == "kanał-6",
                "Nieudana porcja zablokowała następny kanał albo nie przetrwała ponownego otwarcia bazy.");
            reopened.MarkRefreshAttempt(secondBatch[0].SubscriptionId, start.AddMinutes(1));

            Assert(reopened.GetDueRefreshTargets(start.AddMinutes(2)).Count == 0,
                "Automat ponowił nieudane źródła bez zachowania odstępu.");
            Assert(reopened.GetRefreshTargets().Count == 6,
                "Odstęp automatu zablokował ręczne odświeżanie F5.");

            var retry = reopened.GetDueRefreshTargets(start.AddMinutes(61));
            Assert(retry.Count == 5
                   && retry.All(target => target.SubscriptionId != "kanał-6"),
                "Po upływie odstępu automat nie wrócił do najstarszej nieudanej porcji.");
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
