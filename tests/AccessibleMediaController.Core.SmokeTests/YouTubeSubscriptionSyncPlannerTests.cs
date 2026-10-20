using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeSubscriptionSyncPlannerTests
{
    internal static void Run()
    {
        PlansOnlyNewChannels();
        DoesNotRestoreLocallyRemovedChannel();
        ExplicitRestoreIsSeparateAction();
        RemoteAbsenceNeverRemovesLocalData();
        DeduplicatesAndRejectsUnsafeIdentity();
        Console.WriteLine("OK: jednokierunkowy plan synchronizacji YouTube do AMC (5 scenariuszy)");
    }

    private static void PlansOnlyNewChannels()
    {
        var local = new PodcastSettings
        {
            Subscriptions =
            [
                Channel("youtube-channel:UC-OBECNY", "https://www.youtube.com/channel/UC-OBECNY/videos", true)
            ]
        };
        var plan = YouTubeSubscriptionSyncPlanner.Create(
            [Remote("UC-OBECNY", "Obecny"), Remote("UC-NOWY", "  Nowy   kanał  ")], local);

        Assert(plan.Actions.Count == 1 && plan.Actions[0].Kind == YouTubeSubscriptionSyncActionKind.Add,
            "Istniejący kanał zostałby dodany ponownie albo nowy pominięty.");
        Assert(plan.Actions[0].ChannelUri.AbsoluteUri
               == "https://www.youtube.com/channel/UC-NOWY/videos",
            "Nowy kanał nie ma kanonicznego adresu.");
        Assert(plan.Actions[0].Title == "Nowy kanał" && plan.AlreadyPresent == 1,
            "Nazwa albo licznik istniejących kanałów są nieprawidłowe.");
    }

    private static void DoesNotRestoreLocallyRemovedChannel()
    {
        var removed = Channel(
            "lokalny-rekord", "https://www.youtube.com/channel/UC-USUNIETY/videos", false);
        var local = new PodcastSettings { Subscriptions = [removed] };
        var plan = YouTubeSubscriptionSyncPlanner.Create([Remote("UC-USUNIETY", "Usunięty")], local);

        Assert(plan.Actions.Count == 0 && plan.Suppressed == 1 && !removed.IsInLibrary,
            "Zwykła synchronizacja przywróciłaby świadomie usunięty kanał.");
    }

    private static void ExplicitRestoreIsSeparateAction()
    {
        var removed = Channel(
            "lokalny-rekord", "https://www.youtube.com/channel/UC-USUNIETY/videos", false);
        var local = new PodcastSettings { Subscriptions = [removed] };
        var plan = YouTubeSubscriptionSyncPlanner.Create(
            [Remote("UC-USUNIETY", "Usunięty")], local, restoreSuppressed: true);

        Assert(plan.Actions.Count == 1
               && plan.Actions[0].Kind == YouTubeSubscriptionSyncActionKind.Restore
               && plan.Actions[0].ExistingSubscriptionId == removed.Id,
            "Jawne przywrócenie nie wskazuje istniejącego rekordu.");
        Assert(!removed.IsInLibrary, "Samo planowanie zmieniło Bibliotekę przed potwierdzeniem.");
    }

    private static void RemoteAbsenceNeverRemovesLocalData()
    {
        var localOnly = Channel(
            "youtube-channel:UC-LOKALNY", "https://www.youtube.com/channel/UC-LOKALNY/videos", true);
        var local = new PodcastSettings { Subscriptions = [localOnly] };
        var plan = YouTubeSubscriptionSyncPlanner.Create([], local);

        Assert(plan.Actions.Count == 0 && localOnly.IsInLibrary,
            "Brak po stronie YouTube usunąłby lokalny kanał.");
    }

    private static void DeduplicatesAndRejectsUnsafeIdentity()
    {
        var local = new PodcastSettings();
        var plan = YouTubeSubscriptionSyncPlanner.Create(
            [
                Remote("UC-RAZ", "Pierwsza nazwa"),
                Remote("UC-RAZ", "Druga nazwa"),
                Remote("../niebezpieczny", "Zły")
            ],
            local);

        Assert(plan.Actions.Count == 1 && plan.Actions[0].Title == "Pierwsza nazwa"
               && plan.Duplicates == 1 && plan.Invalid == 1,
            "Duplikat lub niebezpieczna tożsamość trafiłyby do planu.");
        Assert(local.Subscriptions.Count == 0, "Planowanie zmieniło ustawienia Podcastów.");
    }

    private static PodcastSubscriptionSettings Channel(string id, string url, bool inLibrary) => new()
    {
        Id = id,
        Title = id,
        FeedUrl = url,
        SourceKind = PodcastSourceKind.YouTubeChannel,
        IsInLibrary = inLibrary
    };

    private static YouTubeSubscription Remote(string channelId, string title) =>
        new("sub-" + channelId, channelId, title, null);

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
