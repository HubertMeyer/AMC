using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.LocalMedia;

public sealed record LocalFolderLibraryChange(
    string Message,
    string? SelectedSourceId,
    IReadOnlyList<LocalFolderSourceStatus> Sources);

/// <summary>
/// One narrow owner of Foldery Biblioteki mutations for non-WPF frontends.
/// It touches only library.db; state.json, podcasts.db and user files are not
/// rewritten or removed.
/// </summary>
public sealed class LocalFolderLibraryManager(string databasePath)
{
    private readonly object _gate = new();
    private readonly LocalLibraryDatabase _database = new(Path.GetFullPath(databasePath));

    public IReadOnlyList<LocalFolderSourceStatus> List()
    {
        lock (_gate)
        {
            var state = Load();
            return Statuses(state);
        }
    }

    public LocalFolderLibraryChange Add(string requestedPath)
    {
        if (string.IsNullOrWhiteSpace(requestedPath))
            throw new InvalidOperationException("Wybierz folder do dodania.");
        string path;
        try { path = Path.TrimEndingDirectorySeparator(Path.GetFullPath(requestedPath)); }
        catch (Exception exception) when (
            exception is ArgumentException or NotSupportedException or PathTooLongException)
        {
            throw new InvalidOperationException("Ścieżka folderu jest nieprawidłowa.", exception);
        }
        if (!Directory.Exists(path))
            throw new InvalidOperationException("Nie można otworzyć wybranego folderu.");

        lock (_gate)
        {
            var state = Load();
            var conflict = LocalFolderSourcePolicy.FindConflict(
                state.LocalMedia.FolderSources, path);
            if (conflict is { Kind: LocalFolderSourceConflictKind.SameSource })
            {
                var refreshed = RefreshCore(state, [conflict.ExistingSource]);
                return Change(
                    state,
                    $"Folder „{conflict.ExistingSource.DisplayName}” był już w Bibliotece. {refreshed}",
                    conflict.ExistingSource.Id);
            }
            if (conflict is not null)
            {
                throw new InvalidOperationException(
                    conflict.Kind == LocalFolderSourceConflictKind.CoveredByExistingSource
                        ? $"Nie dodano folderu. Należy już do Folderu Biblioteki „{conflict.ExistingSource.DisplayName}”."
                        : $"Nie dodano folderu. Obejmowałby już dodany Folder Biblioteki „{conflict.ExistingSource.DisplayName}”.");
            }

            var displayName = Path.GetFileName(path);
            var source = new LocalFolderSourceSettings
            {
                Id = Guid.NewGuid().ToString("N"),
                Path = path,
                DisplayName = string.IsNullOrWhiteSpace(displayName) ? path : displayName
            };
            state.LocalMedia.FolderSources.Add(source);
            var summary = RefreshCore(state, [source]);
            return Change(
                state,
                $"Dodano Folder Biblioteki „{source.DisplayName}”. {summary}",
                source.Id);
        }
    }

    public LocalFolderLibraryChange Refresh(IReadOnlyCollection<string>? sourceIds = null)
    {
        lock (_gate)
        {
            var state = Load();
            var requested = (sourceIds ?? [])
                .Where(id => !string.IsNullOrWhiteSpace(id))
                .ToHashSet(StringComparer.Ordinal);
            var sources = state.LocalMedia.FolderSources
                .Where(source => requested.Count == 0 || requested.Contains(source.Id))
                .ToArray();
            if (sources.Length == 0)
                throw new InvalidOperationException(
                    requested.Count == 0
                        ? "Brak Folderów Biblioteki do odświeżenia."
                        : "Wybranego folderu nie ma już w Bibliotece.");
            var summary = RefreshCore(state, sources);
            return new LocalFolderLibraryChange(
                summary,
                sources.Length == 1 ? sources[0].Id : null,
                Statuses(state));
        }
    }

    public LocalFolderLibraryChange Detach(string sourceId)
    {
        lock (_gate)
        {
            var state = Load();
            var source = state.LocalMedia.FolderSources.FirstOrDefault(item =>
                string.Equals(item.Id, sourceId, StringComparison.Ordinal))
                ?? throw new InvalidOperationException(
                    "Wybranego folderu nie ma już w Bibliotece.");
            LocalFolderSourcePolicy.DetachSource(state.LocalMedia.FolderSources, source.Id);
            _database.Save(state);
            return new LocalFolderLibraryChange(
                $"Odłączono folder „{source.DisplayName}”. Pliki na dysku i zapisane dane AMC pozostały bez zmian.",
                null,
                Statuses(state));
        }
    }

    private string RefreshCore(
        PersistedState state,
        IReadOnlyCollection<LocalFolderSourceSettings> sources)
    {
        var successful = new List<(LocalFolderSourceSettings Source, IReadOnlyList<string> Files)>();
        var failed = 0;
        foreach (var source in sources)
        {
            try
            {
                if (!Directory.Exists(source.Path))
                {
                    failed++;
                    continue;
                }
                successful.Add((source, LocalAudioFileDiscovery.FindFiles(source.Path)));
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException or ArgumentException)
            {
                failed++;
            }
        }

        var catalog = state.LocalMedia.Items.Select(ToMediaItem).ToList();
        var sync = LocalLibrarySynchronizer.Synchronize(
            catalog,
            successful.Select(item => item.Source.Path),
            successful.SelectMany(item => item.Files),
            state.LocalMedia.ExcludedPaths);
        MergeCatalog(state, catalog);
        _database.Save(state);

        var parts = new List<string>();
        if (sync.AddedItems.Count > 0) parts.Add($"dodano: {sync.AddedItems.Count}");
        if (sync.RestoredItems.Count > 0) parts.Add($"ponownie dostępne: {sync.RestoredItems.Count}");
        if (sync.BecameUnavailableItems.Count > 0)
            parts.Add($"niedostępne: {sync.BecameUnavailableItems.Count}");
        if (failed > 0) parts.Add($"niedostępne foldery: {failed}");
        return parts.Count == 0
            ? "Biblioteka lokalna jest aktualna."
            : $"Odświeżono Bibliotekę: {string.Join(", ", parts)}.";
    }

    private LocalFolderLibraryChange Change(
        PersistedState state,
        string message,
        string? selectedSourceId)
        => new(message, selectedSourceId, Statuses(state));

    private PersistedState Load()
    {
        var state = new PersistedState();
        _database.LoadInto(state);
        return state;
    }

    private static IReadOnlyList<LocalFolderSourceStatus> Statuses(PersistedState state) =>
        LocalFolderSourcePolicy.BuildStatuses(
            state.LocalMedia.FolderSources,
            state.LocalMedia.Items,
            state.LocalMedia.ExcludedPaths);

    private static MediaItem ToMediaItem(LocalMediaItemSettings item) => new()
    {
        Id = item.Id,
        Title = item.Title,
        HasCustomTitle = item.HasCustomTitle,
        Kind = MediaItemKind.Track,
        Duration = TimeSpan.FromTicks(Math.Max(0, item.DurationTicks)),
        BitrateKbps = item.BitrateKbps,
        IsBitrateEstimated = item.IsBitrateEstimated,
        SampleRateHz = item.SampleRateHz,
        Source = item.Path,
        IsFavorite = item.IsFavorite,
        IsInLibrary = item.IsInLibrary,
        IsAvailable = item.IsAvailable,
        IsInQueue = item.IsInQueue,
        IsPlayNext = item.IsPlayNext
    };

    private static void MergeCatalog(PersistedState state, IReadOnlyList<MediaItem> catalog)
    {
        var existing = state.LocalMedia.Items.ToDictionary(item => item.Id, StringComparer.Ordinal);
        var added = new List<string>();
        var merged = new List<LocalMediaItemSettings>(catalog.Count);
        foreach (var item in catalog)
        {
            if (existing.TryGetValue(item.Id, out var saved))
            {
                saved.Title = item.Title;
                saved.HasCustomTitle = item.HasCustomTitle;
                saved.Path = item.Source ?? saved.Path;
                saved.IsFavorite = item.IsFavorite;
                saved.IsInLibrary = item.IsInLibrary;
                saved.IsAvailable = item.IsAvailable;
                saved.IsInQueue = item.IsInQueue;
                saved.IsPlayNext = item.IsPlayNext;
                merged.Add(saved);
                continue;
            }

            var path = item.Source ?? string.Empty;
            long? length = null;
            long? modified = null;
            try
            {
                var file = new FileInfo(path);
                if (file.Exists)
                {
                    length = file.Length;
                    modified = file.LastWriteTimeUtc.Ticks;
                }
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException or ArgumentException)
            {
                // The scan already proved the path useful. Fingerprints are
                // optional and may be filled by normal playback later.
            }
            merged.Add(new LocalMediaItemSettings
            {
                Id = item.Id,
                Title = item.Title,
                HasCustomTitle = item.HasCustomTitle,
                Path = path,
                DurationTicks = item.Duration.Ticks,
                BitrateKbps = item.BitrateKbps,
                IsBitrateEstimated = item.IsBitrateEstimated,
                SampleRateHz = item.SampleRateHz,
                IsFavorite = item.IsFavorite,
                IsInLibrary = item.IsInLibrary,
                IsAvailable = item.IsAvailable,
                IsInQueue = item.IsInQueue,
                IsPlayNext = item.IsPlayNext,
                FileLength = length,
                LastWriteUtcTicks = modified
            });
            added.Add(item.Id);
        }
        state.LocalMedia.Items = merged;
        state.LocalMedia.CustomOrderItemIds = LocalLibraryManualOrder.Normalize(
            state.LocalMedia.CustomOrderItemIds,
            catalog,
            initializeAlphabetically: true);
        if (!state.CollectionOrders.LibraryAddedItemIdsBySession.TryGetValue(
                "local", out var addedOrder))
        {
            addedOrder = [];
            state.CollectionOrders.LibraryAddedItemIdsBySession["local"] = addedOrder;
        }
        foreach (var itemId in added)
        {
            if (!addedOrder.Contains(itemId, StringComparer.Ordinal)) addedOrder.Add(itemId);
        }
    }
}
