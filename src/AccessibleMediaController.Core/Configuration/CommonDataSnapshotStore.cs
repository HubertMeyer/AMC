using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AccessibleMediaController.Core.Configuration;

/// <summary>
/// Wersjonowana, jednokierunkowa migawka danych wspolnych AMC Test -> AMC.
/// To NIE jest kopia state.json ani baz SQLite: format zawiera wylacznie jawnie
/// dopuszczone sekcje modelu i ma wlasna wersje zgodnosci.
/// </summary>
public static class CommonDataSnapshotStore
{
    public const int CurrentFormatVersion = 1;
    public const string SnapshotKind = "amcCommonData";
    public const string SourceProfileId = "test";
    public const string TargetProfileId = "public";

    private const long MaximumSnapshotBytes = 256L * 1024L * 1024L;
    private static readonly HashSet<string> CommonSessionIds = new(
        ["local", "files", "radio", "podcasts"],
        StringComparer.OrdinalIgnoreCase);
    private static readonly HashSet<string> CommonSearchScopes = new(
        ["global", "local", "files", "radio", "podcasts"],
        StringComparer.OrdinalIgnoreCase);

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter() }
    };

    private static readonly JsonSerializerOptions CanonicalJsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false,
        Converters = { new JsonStringEnumConverter() }
    };

    public static CommonDataSnapshotSummary Export(
        string path,
        PersistedState state,
        DateTime? createdUtc = null)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        ArgumentNullException.ThrowIfNull(state);

        var payload = CreatePayload(state);
        var envelope = new CommonDataSnapshotEnvelope
        {
            FormatVersion = CurrentFormatVersion,
            Kind = SnapshotKind,
            SourceProfileId = SourceProfileId,
            CreatedUtcTicks = (createdUtc ?? DateTime.UtcNow).ToUniversalTime().Ticks,
            ContentSha256 = Fingerprint(payload),
            Data = payload
        };
        WriteEnvelopeAtomically(path, envelope);
        return Summarize(envelope);
    }

    public static CommonDataSnapshotEnvelope Read(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var info = new FileInfo(path);
        if (!info.Exists) throw new FileNotFoundException("Nie znaleziono migawki danych AMC Test.", path);
        if (info.Length <= 0 || info.Length > MaximumSnapshotBytes)
            throw new InvalidDataException("Migawka danych ma nieprawidlowy rozmiar.");

        CommonDataSnapshotEnvelope? envelope;
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            envelope = JsonSerializer.Deserialize<CommonDataSnapshotEnvelope>(stream, JsonOptions);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException("Migawka danych AMC Test jest uszkodzona.", exception);
        }

        Validate(envelope);
        return envelope!;
    }

    public static CommonDataImportPlan PlanImport(
        string snapshotPath,
        PersistedState publicState,
        string synchronizationMetadataPath)
    {
        ArgumentNullException.ThrowIfNull(publicState);
        var snapshot = Read(snapshotPath);
        var currentTargetHash = Fingerprint(CreatePayload(publicState));
        var metadata = ReadMetadata(synchronizationMetadataPath);

        var alreadyCurrent = string.Equals(
            currentTargetHash,
            snapshot.ContentSha256,
            StringComparison.OrdinalIgnoreCase);
        var publicChanged = metadata is null
            ? !IsEmptyCommonData(publicState)
            : !string.Equals(
                currentTargetHash,
                metadata.AppliedTargetContentSha256,
                StringComparison.OrdinalIgnoreCase);

        var disposition = alreadyCurrent
            ? CommonDataImportDisposition.NoChanges
            : publicChanged
                ? CommonDataImportDisposition.Conflict
                : CommonDataImportDisposition.Ready;
        return new CommonDataImportPlan(
            disposition,
            snapshot,
            currentTargetHash,
            Summarize(snapshot));
    }

    /// <summary>
    /// Scala dane z migawki z profilem publicznym. Ustawienia profilu,
    /// nawigacja, stan odtwarzacza, Spotify, TIDAL, Sonos, WiiM, zdalne
    /// kolejki i profile klawiatury pozostaja z kopii docelowej.
    /// </summary>
    public static PersistedState Apply(
        CommonDataImportPlan plan,
        PersistedState publicState,
        CommonDataConflictResolution resolution = CommonDataConflictResolution.Stop)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(publicState);
        if (plan.Disposition == CommonDataImportDisposition.Conflict
            && resolution != CommonDataConflictResolution.UseTestData)
        {
            throw new CommonDataConflictException(
                "Publiczne AMC ma wlasne zmiany. Wybierz zachowanie danych publicznych albo swiadomie przyjmij dane z AMC Test.");
        }

        var result = StateSnapshotCopier.Copy(publicState);
        var source = plan.Snapshot.Data;

        result.SearchHistory.Entries = MergeScopedDictionary(
            result.SearchHistory.Entries,
            source.SearchHistory.Entries,
            CommonSearchScopes);
        result.PlaybackHistory.ItemIdsBySession = MergeScopedDictionary(
            result.PlaybackHistory.ItemIdsBySession,
            source.PlaybackHistory.ItemIdsBySession,
            CommonSessionIds);

        result.Bookmarks.Entries.RemoveAll(IsCommonBookmark);
        result.Bookmarks.Entries.AddRange(
            StateSnapshotCopier.Copy(source.Bookmarks).Entries);

        MergeCollectionOrders(result.CollectionOrders, source.CollectionOrders);

        result.Playlists.Entries.RemoveAll(entry => IsCommonSession(entry.SessionId));
        result.Playlists.Entries.AddRange(
            StateSnapshotCopier.Copy(source.Playlists).Entries);

        result.SessionPresets.EntriesBySession = MergeScopedDictionary(
            result.SessionPresets.EntriesBySession,
            source.SessionPresets.EntriesBySession,
            CommonSessionIds);

        result.PlaybackVolumes.Entries.RemoveAll(entry => IsCommonSession(entry.SessionId));
        result.PlaybackVolumes.Entries.AddRange(
            StateSnapshotCopier.Copy(source.PlaybackVolumes).Entries);

        ReplaceLocalData(result.LocalMedia, source.LocalMedia);
        ReplaceRadioData(result.Radio, source.Radio);
        ReplacePodcastData(result.Podcasts, source.Podcasts);
        return result;
    }

    public static void MarkImported(
        string synchronizationMetadataPath,
        CommonDataImportPlan plan,
        PersistedState savedPublicState,
        DateTime? appliedUtc = null)
    {
        var metadata = new CommonDataSynchronizationMetadata
        {
            FormatVersion = CurrentFormatVersion,
            SourceProfileId = SourceProfileId,
            SourceContentSha256 = plan.Snapshot.ContentSha256,
            AppliedTargetContentSha256 = Fingerprint(CreatePayload(savedPublicState)),
            AppliedUtcTicks = (appliedUtc ?? DateTime.UtcNow).ToUniversalTime().Ticks
        };
        WriteJsonAtomically(synchronizationMetadataPath, metadata, preservePrevious: true);
    }

    public static CommonDataSnapshotSummary Summarize(CommonDataSnapshotEnvelope envelope)
    {
        var data = envelope.Data;
        return new CommonDataSnapshotSummary(
            new DateTime(envelope.CreatedUtcTicks, DateTimeKind.Utc),
            data.LocalMedia.Items.Count,
            data.Radio.Stations.Count,
            data.Podcasts.Subscriptions.Count,
            data.Podcasts.Episodes.Count,
            data.Bookmarks.Entries.Count,
            data.Playlists.Entries.Count,
            data.Radio.RecordingSchedules.Count,
            data.Radio.RecordingHistory.Count);
    }

    internal static CommonDataSnapshotPayload CreatePayload(PersistedState state)
    {
        var search = StateSnapshotCopier.Copy(state.SearchHistory);
        search.Entries = FilterDictionary(search.Entries, CommonSearchScopes);

        var playbackHistory = StateSnapshotCopier.Copy(state.PlaybackHistory);
        playbackHistory.ItemIdsBySession = FilterDictionary(
            playbackHistory.ItemIdsBySession,
            CommonSessionIds);

        var bookmarks = StateSnapshotCopier.Copy(state.Bookmarks);
        bookmarks.Entries = bookmarks.Entries.Where(IsCommonBookmark).ToList();

        var orders = StateSnapshotCopier.Copy(state.CollectionOrders);
        FilterCollectionOrders(orders);

        var playlists = StateSnapshotCopier.Copy(state.Playlists);
        playlists.Entries = playlists.Entries
            .Where(entry => IsCommonSession(entry.SessionId))
            .ToList();

        var presets = StateSnapshotCopier.Copy(state.SessionPresets);
        presets.EntriesBySession = FilterDictionary(
            presets.EntriesBySession,
            CommonSessionIds);

        var volumes = StateSnapshotCopier.Copy(state.PlaybackVolumes);
        volumes.Entries = volumes.Entries
            .Where(entry => IsCommonSession(entry.SessionId))
            .ToList();

        var local = StateSnapshotCopier.Copy(state.LocalMedia);
        local.LibraryView = string.Empty;
        local.CurrentFolderPath = null;
        local.CurrentItemId = null;
        local.Volume = 35;
        local.PlaybackRate = 1d;

        var radio = StateSnapshotCopier.Copy(state.Radio);
        radio.CurrentItemId = null;
        ResetRadioProfilePreferences(radio);

        var podcasts = StateSnapshotCopier.Copy(state.Podcasts);
        podcasts.DownloadsFolder = null;
        podcasts.CurrentItemId = null;
        podcasts.Volume = 35;
        podcasts.PlaybackRate = 1d;
        podcasts.RssRefreshIntervalMinutes = 60;
        podcasts.YouTubeRefreshIntervalMinutes = 60;
        podcasts.AutomaticRefreshBatchSize = 4;

        return new CommonDataSnapshotPayload
        {
            SearchHistory = search,
            PlaybackHistory = playbackHistory,
            Bookmarks = bookmarks,
            CollectionOrders = orders,
            Playlists = playlists,
            SessionPresets = presets,
            PlaybackVolumes = volumes,
            LocalMedia = local,
            Radio = radio,
            Podcasts = podcasts
        };
    }

    private static void Validate(CommonDataSnapshotEnvelope? envelope)
    {
        if (envelope is null
            || envelope.FormatVersion != CurrentFormatVersion
            || !string.Equals(envelope.Kind, SnapshotKind, StringComparison.Ordinal)
            || !string.Equals(envelope.SourceProfileId, SourceProfileId, StringComparison.Ordinal)
            || envelope.CreatedUtcTicks <= 0
            || envelope.Data is null
            || envelope.Data.SearchHistory is null
            || envelope.Data.SearchHistory.Entries is null
            || envelope.Data.PlaybackHistory is null
            || envelope.Data.PlaybackHistory.ItemIdsBySession is null
            || envelope.Data.Bookmarks is null
            || envelope.Data.Bookmarks.Entries is null
            || envelope.Data.CollectionOrders is null
            || envelope.Data.CollectionOrders.FavoriteAddedItemIdsBySession is null
            || envelope.Data.CollectionOrders.FavoriteItemIdsBySession is null
            || envelope.Data.CollectionOrders.LibraryAddedItemIdsBySession is null
            || envelope.Data.CollectionOrders.LibraryItemIdsBySession is null
            || envelope.Data.CollectionOrders.QueueItemIdsBySession is null
            || envelope.Data.CollectionOrders.QueueRegularItemIdsBySession is null
            || envelope.Data.CollectionOrders.QueuePlayNextItemIdsBySession is null
            || envelope.Data.Playlists is null
            || envelope.Data.Playlists.Entries is null
            || envelope.Data.SessionPresets is null
            || envelope.Data.SessionPresets.EntriesBySession is null
            || envelope.Data.PlaybackVolumes is null
            || envelope.Data.PlaybackVolumes.Entries is null
            || envelope.Data.LocalMedia is null
            || envelope.Data.LocalMedia.Items is null
            || envelope.Data.LocalMedia.FolderSources is null
            || envelope.Data.LocalMedia.FolderPlaybackOptions is null
            || envelope.Data.LocalMedia.ExcludedPaths is null
            || envelope.Data.LocalMedia.CustomOrderItemIds is null
            || envelope.Data.Radio is null
            || envelope.Data.Radio.Stations is null
            || envelope.Data.Radio.Presets is null
            || envelope.Data.Radio.RecordingSchedules is null
            || envelope.Data.Radio.RecognizedTracks is null
            || envelope.Data.Radio.RecordingHistory is null
            || envelope.Data.Podcasts is null
            || envelope.Data.Podcasts.Subscriptions is null
            || envelope.Data.Podcasts.Episodes is null)
        {
            throw new InvalidDataException("To nie jest obslugiwana migawka danych AMC Test.");
        }

        var actualHash = Fingerprint(envelope.Data);
        if (!string.Equals(actualHash, envelope.ContentSha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Migawka danych AMC Test nie przeszla kontroli integralnosci.");

        // Format ma byc zamkniety: nawet recznie przygotowany dokument nie moze
        // przemycic sekcji uslug prywatnych przez slowniki sesji.
        if (envelope.Data.SearchHistory.Entries.Keys.Any(key => !CommonSearchScopes.Contains(key))
            || HasForeignSession(envelope.Data.PlaybackHistory.ItemIdsBySession.Keys)
            || envelope.Data.Bookmarks.Entries.Any(entry => !IsCommonBookmark(entry))
            || HasForeignSession(envelope.Data.CollectionOrders.FavoriteAddedItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.FavoriteItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.LibraryAddedItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.LibraryItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.QueueItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.QueueRegularItemIdsBySession.Keys)
            || HasForeignSession(envelope.Data.CollectionOrders.QueuePlayNextItemIdsBySession.Keys)
            || envelope.Data.Playlists.Entries.Any(entry => !IsCommonSession(entry.SessionId))
            || HasForeignSession(envelope.Data.SessionPresets.EntriesBySession.Keys)
            || envelope.Data.PlaybackVolumes.Entries.Any(entry => !IsCommonSession(entry.SessionId)))
        {
            throw new InvalidDataException("Migawka zawiera dane sesji niedostepnej w publicznym AMC.");
        }
    }

    private static bool HasForeignSession(IEnumerable<string> keys) =>
        keys.Any(key => !IsCommonSession(key));

    private static bool IsCommonBookmark(BookmarkEntry entry) =>
        IsCommonSession(entry.SessionId)
        && ((entry.Purpose & BookmarkPurpose.Bookmark) != 0
            || ((entry.Purpose & BookmarkPurpose.Chapter) != 0
                && entry.ChapterOrigin == ChapterOrigin.User));

    private static bool IsCommonSession(string? sessionId) =>
        !string.IsNullOrWhiteSpace(sessionId) && CommonSessionIds.Contains(sessionId);

    private static Dictionary<string, List<T>> FilterDictionary<T>(
        Dictionary<string, List<T>> source,
        HashSet<string> allowedKeys)
    {
        var result = new Dictionary<string, List<T>>(StringComparer.OrdinalIgnoreCase);
        foreach (var pair in source.OrderBy(pair => pair.Key, StringComparer.OrdinalIgnoreCase))
        {
            if (allowedKeys.Contains(pair.Key)) result[pair.Key] = pair.Value;
        }
        return result;
    }

    private static Dictionary<string, List<T>> MergeScopedDictionary<T>(
        Dictionary<string, List<T>> target,
        Dictionary<string, List<T>> incoming,
        HashSet<string> replacedKeys)
    {
        var result = new Dictionary<string, List<T>>(target, target.Comparer);
        foreach (var key in result.Keys.Where(replacedKeys.Contains).ToArray()) result.Remove(key);
        foreach (var pair in incoming) result[pair.Key] = [.. pair.Value];
        return result;
    }

    private static void FilterCollectionOrders(CollectionOrderSettings orders)
    {
        orders.FavoriteAddedItemIdsBySession = FilterDictionary(
            orders.FavoriteAddedItemIdsBySession, CommonSessionIds);
        orders.FavoriteItemIdsBySession = FilterDictionary(
            orders.FavoriteItemIdsBySession, CommonSessionIds);
        orders.LibraryAddedItemIdsBySession = FilterDictionary(
            orders.LibraryAddedItemIdsBySession, CommonSessionIds);
        orders.LibraryItemIdsBySession = FilterDictionary(
            orders.LibraryItemIdsBySession, CommonSessionIds);
        orders.QueueItemIdsBySession = FilterDictionary(
            orders.QueueItemIdsBySession, CommonSessionIds);
        orders.QueueRegularItemIdsBySession = FilterDictionary(
            orders.QueueRegularItemIdsBySession, CommonSessionIds);
        orders.QueuePlayNextItemIdsBySession = FilterDictionary(
            orders.QueuePlayNextItemIdsBySession, CommonSessionIds);
    }

    private static void MergeCollectionOrders(
        CollectionOrderSettings target,
        CollectionOrderSettings incoming)
    {
        target.FavoriteAddedItemIdsBySession = MergeScopedDictionary(
            target.FavoriteAddedItemIdsBySession,
            incoming.FavoriteAddedItemIdsBySession,
            CommonSessionIds);
        target.FavoriteItemIdsBySession = MergeScopedDictionary(
            target.FavoriteItemIdsBySession,
            incoming.FavoriteItemIdsBySession,
            CommonSessionIds);
        target.LibraryAddedItemIdsBySession = MergeScopedDictionary(
            target.LibraryAddedItemIdsBySession,
            incoming.LibraryAddedItemIdsBySession,
            CommonSessionIds);
        target.LibraryItemIdsBySession = MergeScopedDictionary(
            target.LibraryItemIdsBySession,
            incoming.LibraryItemIdsBySession,
            CommonSessionIds);
        target.QueueItemIdsBySession = MergeScopedDictionary(
            target.QueueItemIdsBySession,
            incoming.QueueItemIdsBySession,
            CommonSessionIds);
        target.QueueRegularItemIdsBySession = MergeScopedDictionary(
            target.QueueRegularItemIdsBySession,
            incoming.QueueRegularItemIdsBySession,
            CommonSessionIds);
        target.QueuePlayNextItemIdsBySession = MergeScopedDictionary(
            target.QueuePlayNextItemIdsBySession,
            incoming.QueuePlayNextItemIdsBySession,
            CommonSessionIds);
    }

    private static void ReplaceLocalData(LocalMediaSettings target, LocalMediaSettings source)
    {
        var copy = StateSnapshotCopier.Copy(source);
        target.Items = copy.Items;
        target.FolderSources = copy.FolderSources;
        target.FolderPlaybackOptions = copy.FolderPlaybackOptions;
        target.ExcludedPaths = copy.ExcludedPaths;
        target.CustomOrderItemIds = copy.CustomOrderItemIds;
    }

    private static void ReplaceRadioData(RadioSettings target, RadioSettings source)
    {
        var copy = StateSnapshotCopier.Copy(source);
        target.Stations = copy.Stations;
        target.Presets = copy.Presets;
        target.RecordingSchedules = copy.RecordingSchedules;
        target.RecognizedTracks = copy.RecognizedTracks;
        target.RecordingHistory = copy.RecordingHistory;
    }

    private static void ReplacePodcastData(PodcastSettings target, PodcastSettings source)
    {
        var copy = StateSnapshotCopier.Copy(source);
        target.Subscriptions = copy.Subscriptions;
        target.Episodes = copy.Episodes;
    }

    private static void ResetRadioProfilePreferences(RadioSettings radio)
    {
        radio.Volume = 35;
        radio.TimeshiftMinutes = 10;
        radio.RecordingsFolder = string.Empty;
        radio.UsePodcastDownloadsFolderForRecordings = false;
        radio.PreferStationFolderInNewSchedules = true;
        radio.RecordingFormat = RadioRecordingFormat.Mp3;
        radio.RecordingBitrateKbps = 192;
        radio.WakeScheduledRecordings = false;
        radio.AutomaticTrackRecognitionEnabled = false;
        radio.AutomaticTrackRecognitionScope = RadioRecognitionScope.CurrentStation;
    }

    private static string Fingerprint(CommonDataSnapshotPayload payload)
    {
        var bytes = JsonSerializer.SerializeToUtf8Bytes(payload, CanonicalJsonOptions);
        return Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    }

    private static void WriteEnvelopeAtomically(
        string path,
        CommonDataSnapshotEnvelope envelope)
    {
        var temporaryPath = path + ".tmp";
        WriteJsonFile(temporaryPath, envelope);
        // Przed podmiana weryfikujemy DOKLADNIE plik tymczasowy. Uszkodzony
        // eksport nie moze wyprzec ostatniej dobrej migawki.
        _ = Read(temporaryPath);
        ReplaceAtomically(temporaryPath, path, preservePrevious: true);
    }

    private static void WriteJsonAtomically<T>(string path, T value, bool preservePrevious)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var temporaryPath = path + ".tmp";
        WriteJsonFile(temporaryPath, value);
        ReplaceAtomically(temporaryPath, path, preservePrevious);
    }

    private static void WriteJsonFile<T>(string path, T value)
    {
        var directory = Path.GetDirectoryName(Path.GetFullPath(path));
        if (!string.IsNullOrWhiteSpace(directory)) Directory.CreateDirectory(directory);
        using var stream = new FileStream(
            path,
            FileMode.Create,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 64 * 1024,
            FileOptions.WriteThrough);
        JsonSerializer.Serialize(stream, value, JsonOptions);
        stream.Flush(flushToDisk: true);
    }

    private static void ReplaceAtomically(string temporaryPath, string path, bool preservePrevious)
    {
        if (File.Exists(path))
        {
            File.Replace(
                temporaryPath,
                path,
                preservePrevious ? path + ".previous" : null,
                ignoreMetadataErrors: true);
        }
        else
        {
            File.Move(temporaryPath, path);
        }
    }

    private static CommonDataSynchronizationMetadata? ReadMetadata(string path)
    {
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path)) return null;
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            var metadata = JsonSerializer.Deserialize<CommonDataSynchronizationMetadata>(stream, JsonOptions);
            if (metadata is { FormatVersion: CurrentFormatVersion }
                && string.Equals(metadata.SourceProfileId, SourceProfileId, StringComparison.Ordinal)
                && IsSha256(metadata.SourceContentSha256)
                && IsSha256(metadata.AppliedTargetContentSha256))
            {
                return metadata;
            }
            throw new InvalidDataException(
                "Nie mozna potwierdzic poprzedniego odswiezenia danych publicznego AMC.");
        }
        catch (JsonException exception)
        {
            // Uszkodzony znacznik NIE moze zostac potraktowany jak pierwszy
            // import, bo daloby to prawo do cichego nadpisania zmian publicznych.
            throw new InvalidDataException(
                "Nie mozna potwierdzic poprzedniego odswiezenia danych publicznego AMC.",
                exception);
        }
    }

    private static bool IsSha256(string? value) =>
        value is { Length: 64 } && value.All(Uri.IsHexDigit);

    private static bool IsEmptyCommonData(PersistedState state)
    {
        var empty = CreatePayload(ConfigurationStore.CreateDefaultState());
        return string.Equals(
            Fingerprint(CreatePayload(state)),
            Fingerprint(empty),
            StringComparison.OrdinalIgnoreCase);
    }
}

public sealed class CommonDataSnapshotEnvelope
{
    public int FormatVersion { get; set; }
    public string Kind { get; set; } = string.Empty;
    public string SourceProfileId { get; set; } = string.Empty;
    public long CreatedUtcTicks { get; set; }
    public string ContentSha256 { get; set; } = string.Empty;
    public CommonDataSnapshotPayload Data { get; set; } = new();
}

public sealed class CommonDataSnapshotPayload
{
    public SearchHistorySettings SearchHistory { get; set; } = new();
    public PlaybackHistorySettings PlaybackHistory { get; set; } = new();
    public BookmarkSettings Bookmarks { get; set; } = new();
    public CollectionOrderSettings CollectionOrders { get; set; } = new();
    public PlaylistSettings Playlists { get; set; } = new();
    public SessionPresetSettings SessionPresets { get; set; } = new();
    public PlaybackVolumeMemorySettings PlaybackVolumes { get; set; } = new();
    public LocalMediaSettings LocalMedia { get; set; } = new();
    public RadioSettings Radio { get; set; } = new();
    public PodcastSettings Podcasts { get; set; } = new();
}

public enum CommonDataImportDisposition
{
    Ready,
    NoChanges,
    Conflict
}

public enum CommonDataConflictResolution
{
    Stop,
    UseTestData
}

public sealed record CommonDataImportPlan(
    CommonDataImportDisposition Disposition,
    CommonDataSnapshotEnvelope Snapshot,
    string CurrentTargetContentSha256,
    CommonDataSnapshotSummary Summary);

public sealed record CommonDataSnapshotSummary(
    DateTime CreatedUtc,
    int LocalFiles,
    int RadioStations,
    int PodcastSources,
    int PodcastEpisodes,
    int Bookmarks,
    int Playlists,
    int RecordingSchedules,
    int RecordingHistoryEntries);

public sealed record CommonDataImportResult(
    CommonDataImportDisposition Disposition,
    CommonDataSnapshotSummary Summary,
    PersistedState State);

public sealed class CommonDataSynchronizationMetadata
{
    public int FormatVersion { get; set; }
    public string SourceProfileId { get; set; } = string.Empty;
    public string SourceContentSha256 { get; set; } = string.Empty;
    public string AppliedTargetContentSha256 { get; set; } = string.Empty;
    public long AppliedUtcTicks { get; set; }
}

public sealed class CommonDataConflictException(string message) : InvalidOperationException(message);
