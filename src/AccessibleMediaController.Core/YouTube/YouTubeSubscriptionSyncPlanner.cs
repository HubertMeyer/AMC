using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Core.YouTube;

public enum YouTubeSubscriptionSyncActionKind
{
    Add,
    Restore
}

public sealed record YouTubeSubscriptionSyncAction(
    YouTubeSubscriptionSyncActionKind Kind,
    string ChannelId,
    string Title,
    Uri ChannelUri,
    string? ExistingSubscriptionId);

public sealed record YouTubeSubscriptionSyncPlan(
    IReadOnlyList<YouTubeSubscriptionSyncAction> Actions,
    int AlreadyPresent,
    int Suppressed,
    int Duplicates,
    int Invalid);

/// <summary>
/// Czysta, niedestrukcyjna decyzja synchronizacji YouTube → AMC. Nie zapisuje
/// bazy i nie pobiera kanałów. Dzięki temu warstwa wykonawcza może najpierw
/// pokazać użytkownikowi podsumowanie i zastosować plan w kontrolowanych
/// porcjach.
/// </summary>
public static class YouTubeSubscriptionSyncPlanner
{
    public static YouTubeSubscriptionSyncPlan Create(
        IEnumerable<YouTubeSubscription> remoteSubscriptions,
        PodcastSettings localPodcasts,
        bool restoreSuppressed = false)
    {
        ArgumentNullException.ThrowIfNull(remoteSubscriptions);
        ArgumentNullException.ThrowIfNull(localPodcasts);
        var actions = new List<YouTubeSubscriptionSyncAction>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var alreadyPresent = 0;
        var suppressed = 0;
        var duplicates = 0;
        var invalid = 0;

        foreach (var remote in remoteSubscriptions)
        {
            if (!IsSafeChannelId(remote.ChannelId))
            {
                invalid++;
                continue;
            }
            if (!seen.Add(remote.ChannelId))
            {
                duplicates++;
                continue;
            }
            var existing = localPodcasts.Subscriptions.FirstOrDefault(subscription =>
                subscription.SourceKind == PodcastSourceKind.YouTubeChannel
                && MatchesChannel(subscription, remote.ChannelId));
            if (existing is { IsInLibrary: true })
            {
                alreadyPresent++;
                continue;
            }
            if (existing is not null && !restoreSuppressed)
            {
                suppressed++;
                continue;
            }

            var title = NormalizeTitle(remote.Title);
            actions.Add(new YouTubeSubscriptionSyncAction(
                existing is null
                    ? YouTubeSubscriptionSyncActionKind.Add
                    : YouTubeSubscriptionSyncActionKind.Restore,
                remote.ChannelId,
                title,
                new Uri($"https://www.youtube.com/channel/{Uri.EscapeDataString(remote.ChannelId)}/videos"),
                existing?.Id));
        }

        return new YouTubeSubscriptionSyncPlan(
            actions, alreadyPresent, suppressed, duplicates, invalid);
    }

    private static bool MatchesChannel(PodcastSubscriptionSettings subscription, string channelId)
    {
        if (string.Equals(
                subscription.Id,
                "youtube-channel:" + channelId,
                StringComparison.Ordinal))
            return true;
        return IsChannelUri(subscription.FeedUrl, channelId)
            || IsChannelUri(subscription.HomepageUrl, channelId);
    }

    private static bool IsChannelUri(string? value, string channelId)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || !(uri.Host.Equals("youtube.com", StringComparison.OrdinalIgnoreCase)
                || uri.Host.EndsWith(".youtube.com", StringComparison.OrdinalIgnoreCase)))
            return false;
        var segments = uri.AbsolutePath
            .Split('/', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        return segments.Length >= 2
            && string.Equals(segments[0], "channel", StringComparison.OrdinalIgnoreCase)
            && string.Equals(segments[1], channelId, StringComparison.Ordinal);
    }

    private static bool IsSafeChannelId(string? channelId) =>
        channelId is { Length: >= 3 and <= 256 }
        && channelId.All(character => char.IsAsciiLetterOrDigit(character)
            || character is '-' or '_');

    private static string NormalizeTitle(string? value)
    {
        var normalized = string.Join(' ', (value ?? string.Empty)
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        if (normalized.Length == 0) return "Kanał YouTube";
        return normalized.Length <= 500 ? normalized : normalized[..500];
    }
}
