using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Waska brama hosta do jednokierunkowej migawki AMC Test -> AMC. Python nie
/// zapisuje state.json ani SQLite; caly zapis nadal nalezy do Core.
/// </summary>
internal sealed class LiteCommonDataSnapshotCoordinator
{
    public const string ExportOperation = "profile.commonDataExport";
    public const string StatusOperation = "profile.commonDataStatus";
    public const string ImportOperation = "profile.commonDataImport";
    public const string BackupExportOperation = "profile.backupExport";
    public const string BackupInspectOperation = "profile.backupInspect";
    public const string BackupImportOperation = "profile.backupImport";

    private readonly string _releaseProfile;
    private readonly string _snapshotPath;
    private readonly ConfigurationStore _store;

    public LiteCommonDataSnapshotCoordinator(
        string releaseProfile,
        string snapshotPath,
        string statePath,
        string libraryDatabasePath,
        string podcastDatabasePath)
    {
        _releaseProfile = releaseProfile.Trim().ToLowerInvariant();
        if (_releaseProfile is not (CommonDataSnapshotStore.SourceProfileId
            or CommonDataSnapshotStore.TargetProfileId))
        {
            throw new ArgumentException("Nieznany profil wydania.", nameof(releaseProfile));
        }
        _snapshotPath = Path.GetFullPath(snapshotPath);
        _store = new ConfigurationStore(
            Path.GetFullPath(statePath),
            Path.GetFullPath(libraryDatabasePath),
            Path.GetFullPath(podcastDatabasePath));
    }

    public object Export(JsonElement args)
    {
        RequireProfile(CommonDataSnapshotStore.SourceProfileId);
        var summary = _store.ExportCommonDataSnapshot(
            _snapshotPath,
            ReadSearchHistory(args));
        return Payload("exported", summary);
    }

    public object Status()
    {
        if (!File.Exists(_snapshotPath))
        {
            return new
            {
                state = "missing",
                available = false,
                message = "Nie ma jeszcze danych z AMC Test."
            };
        }

        try
        {
            if (_releaseProfile == CommonDataSnapshotStore.TargetProfileId)
            {
                var plan = _store.PlanCommonDataImport(_snapshotPath);
                return Payload(DispositionName(plan.Disposition), plan.Summary);
            }

            var snapshot = CommonDataSnapshotStore.Read(_snapshotPath);
            return Payload("available", CommonDataSnapshotStore.Summarize(snapshot));
        }
        catch (InvalidDataException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (IOException)
        {
            throw new LiteRequestException("Nie można zapisać wskazanej kopii danych AMC.");
        }
    }

    public object Import(JsonElement args)
    {
        RequireProfile(CommonDataSnapshotStore.TargetProfileId);
        var acceptTestData = LiteArgs.ReadBool(args, "acceptTestData", false);
        try
        {
            var result = _store.ImportCommonDataSnapshot(
                _snapshotPath,
                acceptTestData
                    ? CommonDataConflictResolution.UseTestData
                    : CommonDataConflictResolution.Stop);
            return Payload(
                result.Disposition == CommonDataImportDisposition.NoChanges
                    ? "current"
                    : "imported",
                result.Summary,
                result.State.SearchHistory.Entries);
        }
        catch (CommonDataConflictException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (InvalidDataException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (IOException exception)
        {
            throw new LiteRequestException("Nie udalo sie bezpiecznie zapisac danych publicznego AMC: " + exception.Message);
        }
    }

    public object ExportBackup(JsonElement args)
    {
        var path = ReadBackupPath(args, mustExist: false);
        try
        {
            var summary = _store.ExportCurrentBackup(path, ReadSections(args, required: true)!);
            return BackupPayload("exported", summary);
        }
        catch (InvalidDataException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (IOException)
        {
            throw new LiteRequestException("Nie można zapisać wskazanej kopii danych AMC.");
        }
    }

    public object InspectBackup(JsonElement args)
    {
        var path = ReadBackupPath(args, mustExist: true);
        try
        {
            return BackupPayload("ready", _store.InspectBackup(path));
        }
        catch (InvalidDataException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (IOException)
        {
            throw new LiteRequestException("Nie można odczytać wskazanej kopii danych AMC.");
        }
    }

    public object ImportBackup(JsonElement args)
    {
        var path = ReadBackupPath(args, mustExist: true);
        try
        {
            var result = _store.ImportAndSaveBackup(
                path,
                ReadSections(args, required: false));
            return BackupPayload("imported", result.Summary);
        }
        catch (InvalidDataException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (IOException exception)
        {
            throw new LiteRequestException("Nie udało się bezpiecznie zapisać kopii danych: " + exception.Message);
        }
    }

    private void RequireProfile(string expected)
    {
        if (!string.Equals(_releaseProfile, expected, StringComparison.Ordinal))
        {
            var message = expected == CommonDataSnapshotStore.SourceProfileId
                ? "Migawke danych moze tworzyc tylko AMC Test."
                : "Dane z AMC Test moze odswiezyc tylko publiczne AMC.";
            throw new LiteRequestException(message);
        }
    }

    private static string DispositionName(CommonDataImportDisposition disposition) =>
        disposition switch
        {
            CommonDataImportDisposition.Ready => "ready",
            CommonDataImportDisposition.NoChanges => "current",
            CommonDataImportDisposition.Conflict => "conflict",
            _ => "unknown"
        };

    private static string ReadBackupPath(JsonElement args, bool mustExist)
    {
        var path = Path.GetFullPath(LiteArgs.RequireText(args, "path"));
        if (!path.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
            throw new LiteRequestException("Kopia danych AMC musi być plikiem JSON.");
        if (mustExist && !File.Exists(path))
            throw new LiteRequestException("Nie znaleziono wskazanej kopii danych AMC.");
        return path;
    }

    private static IReadOnlyList<string>? ReadSections(JsonElement args, bool required)
    {
        if (args.ValueKind != JsonValueKind.Object
            || !args.TryGetProperty("sections", out var value))
        {
            if (required) throw new LiteRequestException("Nie wybrano zakresu kopii danych.");
            return null;
        }
        if (value.ValueKind != JsonValueKind.Array)
            throw new LiteRequestException("Zakres kopii danych ma nieprawidłowy format.");
        var result = new List<string>();
        foreach (var item in value.EnumerateArray())
        {
            if (item.ValueKind != JsonValueKind.String)
                throw new LiteRequestException("Zakres kopii danych ma nieprawidłowy format.");
            result.Add(item.GetString() ?? string.Empty);
            if (result.Count > ProfileBackupSectionCatalog.All.Count)
                throw new LiteRequestException("Zakres kopii danych jest zbyt duży.");
        }
        return result;
    }

    private static object BackupPayload(string stateName, ProfileBackupSummary summary) => new
    {
        state = stateName,
        sections = summary.Sections,
        localFiles = summary.LocalFiles,
        radioStations = summary.RadioStations,
        podcastSources = summary.PodcastSources,
        podcastEpisodes = summary.PodcastEpisodes,
        bookmarks = summary.Bookmarks,
        playlists = summary.Playlists,
        recordingSchedules = summary.RecordingSchedules,
        recordingHistoryEntries = summary.RecordingHistoryEntries
    };

    private static object Payload(
        string state,
        CommonDataSnapshotSummary summary,
        Dictionary<string, List<string>>? searchHistory = null) => new
    {
        state,
        available = true,
        createdUtcTicks = summary.CreatedUtc.Ticks,
        localFiles = summary.LocalFiles,
        radioStations = summary.RadioStations,
        podcastSources = summary.PodcastSources,
        podcastEpisodes = summary.PodcastEpisodes,
        bookmarks = summary.Bookmarks,
        playlists = summary.Playlists,
        recordingSchedules = summary.RecordingSchedules,
        recordingHistoryEntries = summary.RecordingHistoryEntries,
        searchHistory
    };

    private static SearchHistorySettings? ReadSearchHistory(JsonElement args)
    {
        if (args.ValueKind != JsonValueKind.Object
            || !args.TryGetProperty("searchHistory", out var value))
        {
            return null;
        }
        if (value.ValueKind != JsonValueKind.Object)
            throw new LiteRequestException("Historia wyszukiwania ma nieprawidlowy format.");

        var settings = new SearchHistorySettings();
        var scopeCount = 0;
        foreach (var property in value.EnumerateObject())
        {
            if (++scopeCount > 32 || property.Name.Length is 0 or > 80)
                throw new LiteRequestException("Historia wyszukiwania jest zbyt duza.");
            if (property.Value.ValueKind != JsonValueKind.Array)
                throw new LiteRequestException("Historia wyszukiwania ma nieprawidlowy format.");
            var entries = new List<string>();
            foreach (var item in property.Value.EnumerateArray())
            {
                if (item.ValueKind != JsonValueKind.String)
                    throw new LiteRequestException("Historia wyszukiwania ma nieprawidlowy format.");
                var text = item.GetString()?.Trim() ?? string.Empty;
                if (text.Length == 0) continue;
                if (text.Length > 500)
                    throw new LiteRequestException("Wpis historii wyszukiwania jest zbyt dlugi.");
                if (!entries.Contains(text, StringComparer.OrdinalIgnoreCase)) entries.Add(text);
                if (entries.Count >= SearchQueryHistory.MaxEntriesPerScope) break;
            }
            settings.Entries[property.Name] = entries;
        }
        return settings;
    }
}
