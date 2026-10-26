using System.Security.Cryptography;
using System.Text;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.Configuration;

public sealed class PlaybackHistory(PlaybackHistorySettings settings)
{
    public const int MaxEntriesPerSession = 500;

    public IReadOnlyList<string> GetItemIds(string sessionId)
    {
        if (string.IsNullOrWhiteSpace(sessionId)
            || !settings.ItemIdsBySession.TryGetValue(sessionId, out var entries))
        {
            return [];
        }
        return entries;
    }

    public IReadOnlyList<MediaItem> GetItems(string sessionId, IEnumerable<MediaItem> currentItems)
    {
        var currentById = currentItems
            .GroupBy(item => item.Id, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First(), StringComparer.Ordinal);
        var snapshotsById = GetSnapshotsById(sessionId);
        var result = new List<MediaItem>();
        foreach (var itemId in GetItemIds(sessionId))
        {
            if (currentById.TryGetValue(itemId, out var current)) result.Add(current);
            else if (snapshotsById.TryGetValue(itemId, out var snapshot)) result.Add(snapshot.ToMediaItem());
        }
        return result;
    }

    public bool Contains(string sessionId, string itemId) =>
        GetItemIds(sessionId).Contains(itemId, StringComparer.Ordinal);

    public bool CanReplay(string sessionId, string itemId, IEnumerable<MediaItem> currentItems)
    {
        if (currentItems.Any(item => string.Equals(item.Id, itemId, StringComparison.Ordinal))) return true;
        return GetSnapshotsById(sessionId).TryGetValue(itemId, out var snapshot)
            && snapshot.ReplaySupported;
    }

    public bool Record(string sessionId, string itemId)
    {
        if (string.IsNullOrWhiteSpace(sessionId) || string.IsNullOrWhiteSpace(itemId)) return false;
        var entries = GetOrCreateIds(sessionId);
        var existingIndex = entries.FindIndex(id => string.Equals(id, itemId, StringComparison.Ordinal));
        if (existingIndex == 0) return false;
        if (existingIndex > 0) entries.RemoveAt(existingIndex);
        entries.Insert(0, itemId);
        Trim(entries, sessionId);
        return true;
    }

    public bool Record(
        string sessionId,
        MediaItem item,
        bool replaySupported = true,
        DateTime? observedUtc = null)
    {
        ArgumentNullException.ThrowIfNull(item);
        if (string.IsNullOrWhiteSpace(sessionId) || string.IsNullOrWhiteSpace(item.Id)) return false;

        var entries = GetOrCreateIds(sessionId);
        var snapshots = GetOrCreateSnapshots(sessionId);
        var existingIndex = entries.FindIndex(id => string.Equals(id, item.Id, StringComparison.Ordinal));
        var existingSnapshot = snapshots.FirstOrDefault(candidate =>
            string.Equals(candidate.Id, item.Id, StringComparison.Ordinal));
        var snapshot = PlaybackHistoryItemSettings.FromMediaItem(
            item,
            replaySupported,
            observedUtc ?? DateTime.UtcNow);
        var snapshotChanged = existingSnapshot is null || !SameSnapshot(existingSnapshot, snapshot);
        if (existingIndex == 0 && !snapshotChanged) return false;

        if (existingSnapshot is not null) snapshots.Remove(existingSnapshot);
        snapshots.Insert(0, snapshot);
        if (existingIndex > 0) entries.RemoveAt(existingIndex);
        if (existingIndex != 0) entries.Insert(0, item.Id);
        Trim(entries, sessionId);
        return existingIndex != 0 || snapshotChanged;
    }

    public void Remove(string sessionId, IEnumerable<string> itemIds)
    {
        var ids = itemIds.ToHashSet(StringComparer.Ordinal);
        if (settings.ItemIdsBySession.TryGetValue(sessionId, out var entries))
        {
            entries.RemoveAll(ids.Contains);
            if (entries.Count == 0) settings.ItemIdsBySession.Remove(sessionId);
        }
        if (settings.ItemsBySession.TryGetValue(sessionId, out var snapshots))
        {
            snapshots.RemoveAll(item => ids.Contains(item.Id));
            if (snapshots.Count == 0) settings.ItemsBySession.Remove(sessionId);
        }
    }

    public void Normalize()
    {
        settings.ItemIdsBySession = new Dictionary<string, List<string>>(
            settings.ItemIdsBySession ?? new Dictionary<string, List<string>>(),
            StringComparer.OrdinalIgnoreCase);
        settings.ItemsBySession = new Dictionary<string, List<PlaybackHistoryItemSettings>>(
            settings.ItemsBySession ?? new Dictionary<string, List<PlaybackHistoryItemSettings>>(),
            StringComparer.OrdinalIgnoreCase);

        foreach (var sessionId in settings.ItemIdsBySession.Keys.ToArray())
        {
            var normalized = (settings.ItemIdsBySession[sessionId] ?? [])
                .Where(id => !string.IsNullOrWhiteSpace(id))
                .Distinct(StringComparer.Ordinal)
                .Take(MaxEntriesPerSession)
                .ToList();
            if (normalized.Count == 0) settings.ItemIdsBySession.Remove(sessionId);
            else settings.ItemIdsBySession[sessionId] = normalized;
        }

        foreach (var sessionId in settings.ItemsBySession.Keys.ToArray())
        {
            HashSet<string> knownIds = settings.ItemIdsBySession.TryGetValue(sessionId, out var ids)
                ? ids.ToHashSet(StringComparer.Ordinal)
                : [];
            var normalized = (settings.ItemsBySession[sessionId] ?? [])
                .Where(item => item is not null
                    && !string.IsNullOrWhiteSpace(item.Id)
                    && !string.IsNullOrWhiteSpace(item.Title)
                    && knownIds.Contains(item.Id))
                .DistinctBy(item => item.Id, StringComparer.Ordinal)
                .Take(MaxEntriesPerSession)
                .ToList();
            if (normalized.Count == 0) settings.ItemsBySession.Remove(sessionId);
            else settings.ItemsBySession[sessionId] = normalized;
        }
    }

    public static string CreateObservedItemId(string sessionId, params string?[] identityParts)
    {
        var identity = string.Join('\u001f', identityParts.Select(part => part?.Trim() ?? string.Empty));
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(identity)))
            .ToLowerInvariant();
        return $"{sessionId}:observed:{hash[..32]}";
    }

    private List<string> GetOrCreateIds(string sessionId)
    {
        if (!settings.ItemIdsBySession.TryGetValue(sessionId, out var entries))
        {
            entries = [];
            settings.ItemIdsBySession[sessionId] = entries;
        }
        return entries;
    }

    private List<PlaybackHistoryItemSettings> GetOrCreateSnapshots(string sessionId)
    {
        if (!settings.ItemsBySession.TryGetValue(sessionId, out var snapshots))
        {
            snapshots = [];
            settings.ItemsBySession[sessionId] = snapshots;
        }
        return snapshots;
    }

    private Dictionary<string, PlaybackHistoryItemSettings> GetSnapshotsById(string sessionId) =>
        settings.ItemsBySession.TryGetValue(sessionId, out var snapshots)
            ? snapshots
                .Where(item => item is not null && !string.IsNullOrWhiteSpace(item.Id))
                .GroupBy(item => item.Id, StringComparer.Ordinal)
                .ToDictionary(group => group.Key, group => group.First(), StringComparer.Ordinal)
            : new Dictionary<string, PlaybackHistoryItemSettings>(StringComparer.Ordinal);

    private void Trim(List<string> entries, string sessionId)
    {
        if (entries.Count > MaxEntriesPerSession)
            entries.RemoveRange(MaxEntriesPerSession, entries.Count - MaxEntriesPerSession);
        if (!settings.ItemsBySession.TryGetValue(sessionId, out var snapshots)) return;
        var retained = entries.ToHashSet(StringComparer.Ordinal);
        snapshots.RemoveAll(item => !retained.Contains(item.Id));
        if (snapshots.Count == 0) settings.ItemsBySession.Remove(sessionId);
    }

    private static bool SameSnapshot(PlaybackHistoryItemSettings first, PlaybackHistoryItemSettings second) =>
        first.Id == second.Id
        && first.Title == second.Title
        && first.Artist == second.Artist
        && first.Kind == second.Kind
        && first.DurationTicks == second.DurationTicks
        && first.BitrateKbps == second.BitrateKbps
        && first.IsBitrateEstimated == second.IsBitrateEstimated
        && first.SampleRateHz == second.SampleRateHz
        && first.Source == second.Source
        && first.PublicUri == second.PublicUri
        && first.HomepageUri == second.HomepageUri
        && first.Country == second.Country
        && first.Language == second.Language
        && first.Tags == second.Tags
        && first.Codec == second.Codec
        && first.ExternalId == second.ExternalId
        && first.RelatedAlbumExternalId == second.RelatedAlbumExternalId
        && first.RelatedAlbumTitle == second.RelatedAlbumTitle
        && first.RelatedArtistExternalId == second.RelatedArtistExternalId
        && first.RelatedArtistName == second.RelatedArtistName
        && first.IsAvailable == second.IsAvailable
        && first.ReplaySupported == second.ReplaySupported;
}
