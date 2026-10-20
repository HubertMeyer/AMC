using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Core.YouTube;

public sealed record YouTubeSubscriptionSyncApplyResult(
    int Added,
    int Restored,
    int AlreadyPresent,
    int Suppressed,
    int Duplicates,
    int Invalid)
{
    public int Changed => Added + Restored;
}

/// <summary>
/// Stosuje zatwierdzoną synchronizację konta bez pobierania całych kanałów.
/// Nowe źródła są zapisywane jako puste rekordy oczekujące na istniejący,
/// porcjowany mechanizm odświeżania Podcastów i YouTube.
/// </summary>
public static class YouTubeSubscriptionSyncApplier
{
    private const string AccountChannelIdPrefix = "youtube-account-channel:";

    public static YouTubeSubscriptionSyncApplyResult Apply(
        IEnumerable<YouTubeSubscription> remoteSubscriptions,
        PodcastSettings localPodcasts,
        bool restoreSuppressed = false)
    {
        ArgumentNullException.ThrowIfNull(remoteSubscriptions);
        ArgumentNullException.ThrowIfNull(localPodcasts);
        var plan = YouTubeSubscriptionSyncPlanner.Create(
            remoteSubscriptions,
            localPodcasts,
            restoreSuppressed);

        // Sprawdź cały plan przed pierwszą zmianą. Uszkodzony lub ręcznie
        // zmieniony profil nie może pozostawić połowy zaimportowanych kanałów.
        foreach (var action in plan.Actions)
        {
            if (action.Kind == YouTubeSubscriptionSyncActionKind.Add)
            {
                var newId = AccountChannelIdPrefix + action.ChannelId;
                if (localPodcasts.Subscriptions.Any(candidate =>
                        string.Equals(candidate.Id, newId, StringComparison.Ordinal)))
                {
                    throw new InvalidDataException(
                        "Biblioteka zawiera sprzeczny rekord kanału YouTube. Nie zapisano synchronizacji.");
                }
                continue;
            }

            if (string.IsNullOrWhiteSpace(action.ExistingSubscriptionId)
                || localPodcasts.Subscriptions.All(candidate =>
                    !string.Equals(
                        candidate.Id,
                        action.ExistingSubscriptionId,
                        StringComparison.Ordinal)))
            {
                throw new InvalidDataException(
                    "Biblioteka zmieniła się przed przywróceniem kanału YouTube. Nie zapisano synchronizacji.");
            }
        }

        var added = 0;
        var restored = 0;
        foreach (var action in plan.Actions)
        {
            if (action.Kind == YouTubeSubscriptionSyncActionKind.Restore)
            {
                var existing = localPodcasts.Subscriptions.First(candidate =>
                    string.Equals(
                        candidate.Id,
                        action.ExistingSubscriptionId,
                        StringComparison.Ordinal));
                existing.IsInLibrary = true;
                if (!existing.HasCustomTitle && !string.IsNullOrWhiteSpace(action.Title))
                    existing.Title = action.Title;
                restored++;
                continue;
            }

            localPodcasts.Subscriptions.Add(new PodcastSubscriptionSettings
            {
                Id = AccountChannelIdPrefix + action.ChannelId,
                Title = action.Title,
                Author = action.Title,
                Description = "Kanał dodany z subskrypcji konta YouTube; materiały pojawią się po odświeżeniu.",
                FeedUrl = action.ChannelUri.AbsoluteUri,
                SourceKind = PodcastSourceKind.YouTubeChannel,
                HomepageUrl = $"https://www.youtube.com/channel/{Uri.EscapeDataString(action.ChannelId)}",
                LastRefreshUtcTicks = 0,
                RefreshIntervalMinutes = localPodcasts.YouTubeRefreshIntervalMinutes,
                IsInLibrary = true
            });
            added++;
        }

        return new YouTubeSubscriptionSyncApplyResult(
            added,
            restored,
            plan.AlreadyPresent,
            plan.Suppressed,
            plan.Duplicates,
            plan.Invalid);
    }
}
