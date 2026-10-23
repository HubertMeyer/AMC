using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;

namespace AccessibleMediaController.Core.YouTube;

public enum YouTubePlaylistSyncActionKind
{
    Add,
    Restore,
    Update
}

public sealed record YouTubePlaylistSyncAction(
    YouTubePlaylistSyncActionKind Kind,
    YouTubeAccountPlaylist Playlist,
    string? ExistingSubscriptionId,
    string Label);

public sealed record YouTubePlaylistSyncPlan(
    IReadOnlyList<YouTubePlaylistSyncAction> Actions,
    int Additions,
    int Restores,
    int Updates,
    int Suppressed,
    int Duplicates,
    int Invalid,
    int Truncated);

public sealed record YouTubePlaylistSyncApplyResult(
    int Added,
    int Restored,
    int Updated,
    int AddedVideos,
    int UpdatedVideos,
    int Suppressed,
    int Duplicates,
    int Invalid,
    int Truncated)
{
    public int Changed => Added + Restored + Updated;
}

/// <summary>
/// Tworzy niedestrukcyjny plan synchronizacji playlist. Brak playlisty na
/// koncie nigdy nie usuwa lokalnej kolekcji, a wcześniej usunięta kolekcja
/// wraca tylko po jawnym zaznaczeniu przywracania.
/// </summary>
public static class YouTubePlaylistSyncPlanner
{
    public static YouTubePlaylistSyncPlan Create(
        IEnumerable<YouTubeAccountPlaylist> remotePlaylists,
        PodcastSettings localPodcasts,
        bool restoreSuppressed = false)
    {
        ArgumentNullException.ThrowIfNull(remotePlaylists);
        ArgumentNullException.ThrowIfNull(localPodcasts);
        var actions = new List<YouTubePlaylistSyncAction>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var additions = 0;
        var restores = 0;
        var updates = 0;
        var suppressed = 0;
        var duplicates = 0;
        var invalid = 0;
        var truncated = 0;

        foreach (var playlist in remotePlaylists)
        {
            if (!IsSafeIdentifier(playlist.PlaylistId, 160))
            {
                invalid++;
                continue;
            }
            if (!seen.Add(playlist.PlaylistId))
            {
                duplicates++;
                continue;
            }
            if (playlist.Videos.Any(video => !IsSafeIdentifier(video.VideoId, 64)))
            {
                invalid++;
                continue;
            }

            var existing = localPodcasts.Subscriptions.FirstOrDefault(subscription =>
                MatchesPlaylist(subscription, playlist.PlaylistId));
            if (existing is not null && existing.SourceKind != PodcastSourceKind.YouTubePlaylist)
                throw new InvalidDataException(
                    "Biblioteka zawiera sprzeczny rekord playlisty YouTube. Nie zapisano synchronizacji.");
            if (existing is { IsInLibrary: false } && !restoreSuppressed)
            {
                suppressed++;
                continue;
            }

            var kind = existing switch
            {
                null => YouTubePlaylistSyncActionKind.Add,
                { IsInLibrary: false } => YouTubePlaylistSyncActionKind.Restore,
                _ => YouTubePlaylistSyncActionKind.Update
            };
            if (kind == YouTubePlaylistSyncActionKind.Add) additions++;
            else if (kind == YouTubePlaylistSyncActionKind.Restore) restores++;
            else updates++;
            if (playlist.VideosTruncated) truncated++;
            actions.Add(new YouTubePlaylistSyncAction(
                kind,
                playlist,
                existing?.Id,
                BuildLabel(playlist)));
        }

        return new YouTubePlaylistSyncPlan(
            actions,
            additions,
            restores,
            updates,
            suppressed,
            duplicates,
            invalid,
            truncated);
    }

    internal static bool MatchesPlaylist(
        PodcastSubscriptionSettings subscription,
        string playlistId)
    {
        if (string.Equals(subscription.Id, "youtube-playlist:" + playlistId, StringComparison.Ordinal))
            return true;
        return IsPlaylistUri(subscription.FeedUrl, playlistId)
            || IsPlaylistUri(subscription.HomepageUrl, playlistId);
    }

    private static bool IsPlaylistUri(string? value, string playlistId)
    {
        if (!Uri.TryCreate(value, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || !(uri.Host.Equals("youtube.com", StringComparison.OrdinalIgnoreCase)
                || uri.Host.EndsWith(".youtube.com", StringComparison.OrdinalIgnoreCase)))
            return false;
        var query = uri.Query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries);
        foreach (var field in query)
        {
            var pair = field.Split('=', 2);
            if (pair.Length == 2
                && string.Equals(Uri.UnescapeDataString(pair[0]), "list", StringComparison.OrdinalIgnoreCase)
                && string.Equals(Uri.UnescapeDataString(pair[1]), playlistId, StringComparison.Ordinal))
                return true;
        }
        return false;
    }

    private static string BuildLabel(YouTubeAccountPlaylist playlist)
    {
        var title = Normalize(playlist.Title, "Playlista YouTube", 500);
        var privacy = playlist.PrivacyStatus switch
        {
            "private" => "prywatna",
            "unlisted" => "niepubliczna",
            _ => "publiczna"
        };
        var count = playlist.VideosTruncated
            ? $"pierwsze {playlist.Videos.Count} z {Math.Max(playlist.TotalItemCount, playlist.Videos.Count)} materiałów"
            : $"{playlist.Videos.Count} materiałów";
        return $"{title}; {privacy}; {count}";
    }

    private static bool IsSafeIdentifier(string? value, int maximumLength) =>
        value is { Length: >= 2 }
        && value.Length <= maximumLength
        && value.All(character => char.IsAsciiLetterOrDigit(character) || character is '_' or '-');

    private static string Normalize(string? value, string fallback, int maximumLength)
    {
        var normalized = string.Join(' ', (value ?? string.Empty).Split(
            (char[]?)null,
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        if (normalized.Length == 0) return fallback;
        return normalized.Length <= maximumLength ? normalized : normalized[..maximumLength].Trim();
    }
}

public static class YouTubePlaylistSyncApplier
{
    public static YouTubePlaylistSyncApplyResult Apply(
        IEnumerable<YouTubeAccountPlaylist> remotePlaylists,
        PodcastSettings localPodcasts,
        bool restoreSuppressed = false,
        DateTime? refreshUtc = null)
    {
        ArgumentNullException.ThrowIfNull(remotePlaylists);
        ArgumentNullException.ThrowIfNull(localPodcasts);
        var plan = YouTubePlaylistSyncPlanner.Create(
            remotePlaylists,
            localPodcasts,
            restoreSuppressed);

        foreach (var action in plan.Actions)
        {
            var expectedId = "youtube-playlist:" + action.Playlist.PlaylistId;
            if (action.Kind == YouTubePlaylistSyncActionKind.Add)
            {
                if (localPodcasts.Subscriptions.Any(candidate =>
                        string.Equals(candidate.Id, expectedId, StringComparison.Ordinal)))
                    throw new InvalidDataException(
                        "Biblioteka zawiera sprzeczny rekord playlisty YouTube. Nie zapisano synchronizacji.");
                continue;
            }
            if (string.IsNullOrWhiteSpace(action.ExistingSubscriptionId)
                || localPodcasts.Subscriptions.All(candidate =>
                    !string.Equals(candidate.Id, action.ExistingSubscriptionId, StringComparison.Ordinal)))
                throw new InvalidDataException(
                    "Biblioteka zmieniła się przed zapisem playlisty YouTube. Nie zapisano synchronizacji.");
        }

        var added = 0;
        var restored = 0;
        var updated = 0;
        var addedVideos = 0;
        var updatedVideos = 0;
        var timestamp = (refreshUtc ?? DateTime.UtcNow).ToUniversalTime();
        foreach (var action in plan.Actions)
        {
            var update = PodcastLibraryUpdater.Apply(
                localPodcasts,
                ToFeed(action.Playlist),
                action.ExistingSubscriptionId is null
                    ? null
                    : localPodcasts.Subscriptions.First(candidate =>
                        string.Equals(candidate.Id, action.ExistingSubscriptionId, StringComparison.Ordinal))
                        is { HasCustomTitle: true } existing
                            ? existing.Title
                            : null,
                timestamp,
                sourceKind: PodcastSourceKind.YouTubePlaylist,
                addToLibrary: true);
            addedVideos += update.AddedEpisodes;
            updatedVideos += update.UpdatedEpisodes;
            if (action.Kind == YouTubePlaylistSyncActionKind.Add) added++;
            else if (action.Kind == YouTubePlaylistSyncActionKind.Restore) restored++;
            else updated++;
        }

        return new YouTubePlaylistSyncApplyResult(
            added,
            restored,
            updated,
            addedVideos,
            updatedVideos,
            plan.Suppressed,
            plan.Duplicates,
            plan.Invalid,
            plan.Truncated);
    }

    private static PodcastFeedDocument ToFeed(YouTubeAccountPlaylist playlist)
    {
        var playlistUri = new Uri(
            "https://www.youtube.com/playlist?list=" + Uri.EscapeDataString(playlist.PlaylistId));
        var id = "youtube-playlist:" + playlist.PlaylistId;
        var description = string.IsNullOrWhiteSpace(playlist.Description)
            ? playlist.PrivacyStatus == "private"
                ? "Prywatna playlista zalogowanego konta YouTube. Dostępność odtwarzania poszczególnych materiałów zależy od YouTube."
                : "Playlista pobrana z zalogowanego konta YouTube."
            : playlist.Description;
        return new PodcastFeedDocument(
            id,
            playlist.Title,
            playlist.ChannelTitle,
            description,
            playlistUri,
            playlistUri,
            playlist.Videos.Select(video =>
            {
                var page = new Uri(
                    "https://www.youtube.com/watch?v=" + Uri.EscapeDataString(video.VideoId));
                return new PodcastFeedEpisode(
                    id + ":" + video.VideoId,
                    video.VideoId,
                    video.Title,
                    video.ChannelTitle,
                    video.Description,
                    video.Published,
                    TimeSpan.Zero,
                    page,
                    page,
                    "video/youtube",
                    null);
            }).ToArray(),
            playlist.VideosTruncated);
    }
}
