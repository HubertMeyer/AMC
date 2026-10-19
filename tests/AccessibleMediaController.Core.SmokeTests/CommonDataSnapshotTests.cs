using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Configuration;

internal static class CommonDataSnapshotTests
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "amc-common-snapshot-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            FiltersPrivateAndTransientData(root);
            AppliesOnlyCommonData(root);
            RoundTripsThroughConfigurationStores(root);
            FirstImportWithExistingPublicDataRequiresDecision(root);
            DetectsPublicConflict(root);
            RejectsCorruptSynchronizationMetadata(root);
            PreservesPreviousVerifiedSnapshot(root);
            RejectsTampering(root);
            Console.WriteLine("PASS CommonDataSnapshotTests");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void FiltersPrivateAndTransientData(string root)
    {
        var state = CreateSource();
        var path = Path.Combine(root, "filtered.amc-common-data.json");
        var summary = CommonDataSnapshotStore.Export(
            path,
            state,
            new DateTime(2026, 10, 19, 2, 30, 0, DateTimeKind.Utc));
        var snapshot = CommonDataSnapshotStore.Read(path);
        var json = File.ReadAllText(path);

        Equal(1, summary.LocalFiles, "Liczba lokalnych plikow");
        Equal(1, summary.RadioStations, "Liczba stacji");
        Equal(1, summary.PodcastSources, "Liczba zrodel podcastow");
        Equal(1, snapshot.Data.SearchHistory.Entries.Count, "Tylko wspolna historia wyszukiwania");
        False(snapshot.Data.SearchHistory.Entries.ContainsKey("spotify"), "Brak historii Spotify");
        False(snapshot.Data.PlaybackHistory.ItemIdsBySession.ContainsKey("tidal"), "Brak historii TIDAL");
        Equal(2, snapshot.Data.Bookmarks.Entries.Count, "Zakladka i rozdzial uzytkownika");
        False(snapshot.Data.Bookmarks.Entries.Any(entry => entry.ChapterOrigin == ChapterOrigin.Provider),
            "Brak rozdzialow dostawcy");
        Equal(string.Empty, snapshot.Data.LocalMedia.LibraryView, "Brak widoku chwilowego");
        Equal(null, snapshot.Data.LocalMedia.CurrentItemId, "Brak biezacego elementu");
        Equal(null, snapshot.Data.Radio.CurrentItemId, "Brak biezacej stacji");
        Equal(string.Empty, snapshot.Data.Radio.RecordingsFolder, "Brak ustawienia folderu profilu");
        Equal(null, snapshot.Data.Podcasts.DownloadsFolder, "Brak ustawienia folderu pobierania");
        False(json.Contains("tajny-klient-spotify", StringComparison.Ordinal), "Brak danych Spotify");
        False(json.Contains("tajny-klient-tidal", StringComparison.Ordinal), "Brak danych TIDAL");
        False(json.Contains("SessionNavigation", StringComparison.OrdinalIgnoreCase), "Brak nawigacji i fokusu");
        False(json.Contains("KeyboardProfiles", StringComparison.OrdinalIgnoreCase), "Brak profili klawiatury v1");
    }

    private static void AppliesOnlyCommonData(string root)
    {
        var snapshotPath = Path.Combine(root, "apply.amc-common-data.json");
        CommonDataSnapshotStore.Export(snapshotPath, CreateSource());

        var target = ConfigurationStore.CreateDefaultState();
        target.Settings.LastSessionId = "wiim";
        target.Settings.SessionSlots = new Dictionary<int, string> { [1] = "wiim" };
        target.Spotify.ClientId = "publiczne-spotify-zostaje";
        target.Tidal.ClientId = "publiczny-tidal-zostaje";
        target.Sonos.SelectedHouseholdId = "dom-publiczny";
        target.WiiM.SelectedDeviceId = "wiim-publiczny";
        target.LocalMedia.LibraryView = "Ostatnie";
        target.LocalMedia.CurrentItemId = "target-current";
        target.LocalMedia.Volume = 17;
        target.Radio.CurrentItemId = "radio-current";
        target.Radio.RecordingsFolder = "D:\\Publiczne nagrania";
        target.Radio.TimeshiftMinutes = 44;
        target.Podcasts.DownloadsFolder = "D:\\Publiczne podcasty";
        target.Podcasts.Volume = 23;
        target.SearchHistory.Entries["spotify"] = ["zostaje prywatne"];
        target.Playlists.Entries.Add(new PlaylistEntry
        {
            Id = "spotify-playlist",
            SessionId = "spotify",
            Name = "Nie ruszaj"
        });

        var plan = CommonDataSnapshotStore.PlanImport(
            snapshotPath,
            target,
            Path.Combine(root, "missing-sync.json"));
        Equal(CommonDataImportDisposition.Ready, plan.Disposition, "Pierwszy import jest gotowy");
        var merged = CommonDataSnapshotStore.Apply(plan, target);

        Equal("wiim", merged.Settings.LastSessionId, "Zachowana ostatnia sesja profilu");
        Equal("wiim", merged.Settings.SessionSlots[1], "Zachowana kolejnosc sesji profilu");
        Equal("publiczne-spotify-zostaje", merged.Spotify.ClientId, "Spotify nie jest migrowane");
        Equal("publiczny-tidal-zostaje", merged.Tidal.ClientId, "TIDAL nie jest migrowany");
        Equal("dom-publiczny", merged.Sonos.SelectedHouseholdId, "Sonos nie jest migrowany");
        Equal("wiim-publiczny", merged.WiiM.SelectedDeviceId, "WiiM nie jest migrowany");
        Equal("Ostatnie", merged.LocalMedia.LibraryView, "Zachowany widok publiczny");
        Equal("target-current", merged.LocalMedia.CurrentItemId, "Zachowany fokus publiczny");
        Equal(17, merged.LocalMedia.Volume, "Zachowana glosnosc publiczna");
        Equal("radio-current", merged.Radio.CurrentItemId, "Zachowana biezaca stacja publiczna");
        Equal("D:\\Publiczne nagrania", merged.Radio.RecordingsFolder, "Zachowany folder nagran");
        Equal(44, merged.Radio.TimeshiftMinutes, "Zachowany Time Shift profilu");
        Equal("D:\\Publiczne podcasty", merged.Podcasts.DownloadsFolder, "Zachowany folder podcastow");
        Equal(23, merged.Podcasts.Volume, "Zachowana glosnosc podcastow");
        True(merged.SearchHistory.Entries.ContainsKey("spotify"), "Zachowane prywatne dane celu");
        True(merged.Playlists.Entries.Any(entry => entry.Id == "spotify-playlist"),
            "Zachowana playlista uslugi prywatnej");
        Equal("Plik ze zrodla", merged.LocalMedia.Items.Single().Title, "Przeniesiony plik lokalny");
        Equal("Radio ze zrodla", merged.Radio.Stations.Single().Name, "Przeniesiona stacja");
        Equal("Podcast ze zrodla", merged.Podcasts.Subscriptions.Single().Title, "Przeniesiony podcast");
    }

    private static void DetectsPublicConflict(string root)
    {
        var snapshotPath = Path.Combine(root, "conflict.amc-common-data.json");
        var metadataPath = Path.Combine(root, "conflict.sync.json");
        CommonDataSnapshotStore.Export(snapshotPath, CreateSource());

        var target = ConfigurationStore.CreateDefaultState();
        var firstPlan = CommonDataSnapshotStore.PlanImport(snapshotPath, target, metadataPath);
        var imported = CommonDataSnapshotStore.Apply(firstPlan, target);
        CommonDataSnapshotStore.MarkImported(metadataPath, firstPlan, imported);

        var unchangedPlan = CommonDataSnapshotStore.PlanImport(snapshotPath, imported, metadataPath);
        Equal(CommonDataImportDisposition.NoChanges, unchangedPlan.Disposition, "Ten sam stan nie wymaga importu");

        imported.Radio.Stations.Add(new RadioStationSettings
        {
            Id = "public-change",
            Name = "Zmiana tylko w AMC",
            StreamUrl = "https://example.invalid/public"
        });
        var conflict = CommonDataSnapshotStore.PlanImport(snapshotPath, imported, metadataPath);
        Equal(CommonDataImportDisposition.Conflict, conflict.Disposition, "Wykryta zmiana publiczna");
        Throws<CommonDataConflictException>(() => CommonDataSnapshotStore.Apply(conflict, imported));
        var accepted = CommonDataSnapshotStore.Apply(
            conflict,
            imported,
            CommonDataConflictResolution.UseTestData);
        False(accepted.Radio.Stations.Any(station => station.Id == "public-change"),
            "Swiadoma decyzja przyjmuje dane Test");
    }

    private static void RoundTripsThroughConfigurationStores(string root)
    {
        var caseRoot = Path.Combine(root, "configuration-stores");
        var sourceRoot = Path.Combine(caseRoot, "test");
        var targetRoot = Path.Combine(caseRoot, "public");
        Directory.CreateDirectory(sourceRoot);
        Directory.CreateDirectory(targetRoot);
        var snapshotPath = Path.Combine(caseRoot, "common-data.json");

        var sourceStore = new ConfigurationStore(
            Path.Combine(sourceRoot, "state.json"),
            Path.Combine(sourceRoot, "library.db"),
            Path.Combine(sourceRoot, "podcasts.db"));
        sourceStore.Save(CreateSource());
        var uiSearchHistory = new SearchHistorySettings();
        uiSearchHistory.Entries["global"] = ["historia z interfejsu wxPython"];
        sourceStore.ExportCommonDataSnapshot(snapshotPath, uiSearchHistory);

        var targetStore = new ConfigurationStore(
            Path.Combine(targetRoot, "state.json"),
            Path.Combine(targetRoot, "library.db"),
            Path.Combine(targetRoot, "podcasts.db"));
        var target = ConfigurationStore.CreateDefaultState();
        target.Settings.LastSessionId = "radio";
        target.Spotify.ClientId = "publiczne konto pozostaje";
        targetStore.Save(target);

        var imported = targetStore.ImportCommonDataSnapshot(snapshotPath);
        Equal(CommonDataImportDisposition.Ready, imported.Disposition, "Pierwszy import magazynow");
        True(File.Exists(Path.Combine(targetRoot, "common-data-sync.json")),
            "Znacznik synchronizacji powstal dopiero po zapisie");

        var reopened = targetStore.LoadOrCreate();
        Equal("radio", reopened.Settings.LastSessionId, "Profil publiczny zachowal ostatnia sesje");
        Equal("publiczne konto pozostaje", reopened.Spotify.ClientId,
            "Profil publiczny zachowal prywatne konto");
        Equal("Plik ze zrodla", reopened.LocalMedia.Items.Single().Title,
            "Plik zostal ponownie odczytany z docelowej bazy SQLite");
        Equal("Podcast ze zrodla", reopened.Podcasts.Subscriptions.Single().Title,
            "Podcast zostal ponownie odczytany z docelowej bazy SQLite");
        Equal("historia z interfejsu wxPython", reopened.SearchHistory.Entries["global"].Single(),
            "Migawka zawiera autorytatywna historie wyszukiwania interfejsu");
        Equal(CommonDataImportDisposition.NoChanges,
            targetStore.PlanCommonDataImport(snapshotPath).Disposition,
            "Ponowne otwarcie magazynow rozpoznaje aktualny stan");
    }

    private static void FirstImportWithExistingPublicDataRequiresDecision(string root)
    {
        var snapshotPath = Path.Combine(root, "first-conflict.amc-common-data.json");
        CommonDataSnapshotStore.Export(snapshotPath, CreateSource());
        var target = ConfigurationStore.CreateDefaultState();
        target.Radio.Stations.Add(new RadioStationSettings
        {
            Id = "public-existing",
            Name = "Istniejace radio publiczne",
            StreamUrl = "https://example.invalid/existing"
        });

        var plan = CommonDataSnapshotStore.PlanImport(
            snapshotPath,
            target,
            Path.Combine(root, "first-conflict.sync.json"));
        Equal(CommonDataImportDisposition.Conflict, plan.Disposition,
            "Pierwszy import nie nadpisuje istniejacych danych publicznych bez pytania");
    }

    private static void RejectsCorruptSynchronizationMetadata(string root)
    {
        var snapshotPath = Path.Combine(root, "metadata.amc-common-data.json");
        var metadataPath = Path.Combine(root, "metadata.sync.json");
        CommonDataSnapshotStore.Export(snapshotPath, CreateSource());
        var target = ConfigurationStore.CreateDefaultState();
        var plan = CommonDataSnapshotStore.PlanImport(snapshotPath, target, metadataPath);
        var imported = CommonDataSnapshotStore.Apply(plan, target);
        CommonDataSnapshotStore.MarkImported(metadataPath, plan, imported);
        File.WriteAllText(metadataPath, "{\"formatVersion\":1,\"sourceProfileId\":\"test\"}");

        Throws<InvalidDataException>(() =>
            CommonDataSnapshotStore.PlanImport(snapshotPath, imported, metadataPath));
    }

    private static void PreservesPreviousVerifiedSnapshot(string root)
    {
        var path = Path.Combine(root, "atomic.amc-common-data.json");
        var first = CreateSource();
        CommonDataSnapshotStore.Export(path, first, new DateTime(2026, 10, 19, 1, 0, 0, DateTimeKind.Utc));
        var firstText = File.ReadAllText(path);
        first.Radio.Stations[0].Name = "Nowsze radio";
        CommonDataSnapshotStore.Export(path, first, new DateTime(2026, 10, 19, 2, 0, 0, DateTimeKind.Utc));

        True(File.Exists(path + ".previous"), "Zachowana poprzednia dobra migawka");
        Equal(firstText, File.ReadAllText(path + ".previous"), "Poprzednia migawka jest identyczna");
        Equal("Nowsze radio", CommonDataSnapshotStore.Read(path).Data.Radio.Stations.Single().Name,
            "Nowa migawka jest kompletna");
    }

    private static void RejectsTampering(string root)
    {
        var path = Path.Combine(root, "tampered.amc-common-data.json");
        CommonDataSnapshotStore.Export(path, CreateSource());
        var node = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
        node["data"]!["radio"]!["stations"]![0]!["name"] = "Podmieniona stacja";
        File.WriteAllText(path, node.ToJsonString());
        Throws<InvalidDataException>(() => CommonDataSnapshotStore.Read(path));
    }

    private static PersistedState CreateSource()
    {
        var state = ConfigurationStore.CreateDefaultState();
        state.Settings.LastSessionId = "spotify";
        state.Spotify.ClientId = "tajny-klient-spotify";
        state.Tidal.ClientId = "tajny-klient-tidal";
        state.SearchHistory.Entries["global"] = ["wspolne pytanie"];
        state.SearchHistory.Entries["spotify"] = ["prywatne pytanie"];
        state.PlaybackHistory.ItemIdsBySession["local"] = ["file-1"];
        state.PlaybackHistory.ItemIdsBySession["tidal"] = ["tidal-1"];
        state.Bookmarks.Entries =
        [
            Bookmark("bookmark", BookmarkPurpose.Bookmark, ChapterOrigin.User),
            Bookmark("user-chapter", BookmarkPurpose.Chapter, ChapterOrigin.User),
            Bookmark("provider-chapter", BookmarkPurpose.Chapter, ChapterOrigin.Provider),
            new BookmarkEntry { Id = "spotify-bookmark", SessionId = "spotify", Purpose = BookmarkPurpose.Bookmark }
        ];
        state.LocalMedia = new LocalMediaSettings
        {
            Items = [new LocalMediaItemSettings { Id = "file-1", Title = "Plik ze zrodla", Path = "D:\\Muzyka\\plik.mp3", ResumePositionTicks = 12 }],
            FolderSources = [new LocalFolderSourceSettings { Id = "folder-1", Path = "D:\\Muzyka", DisplayName = "Muzyka" }],
            LibraryView = "Foldery",
            CurrentFolderPath = "D:\\Muzyka",
            CurrentItemId = "file-1",
            Volume = 88,
            PlaybackRate = 1.5
        };
        state.Radio.Stations = [new RadioStationSettings
        {
            Id = "radio-1",
            Name = "Radio ze zrodla",
            StreamUrl = "https://example.invalid/radio",
            IsInLibrary = true
        }];
        state.Radio.CurrentItemId = "radio-1";
        state.Radio.RecordingsFolder = "D:\\Nagrania testowe";
        state.Radio.TimeshiftMinutes = 99;
        state.Radio.RecordingSchedules = [new RadioRecordingScheduleSettings
        {
            Id = "schedule-1",
            Name = "Wieczorne nagranie",
            StationId = "radio-1",
            StationName = "Radio ze zrodla",
            StreamUrl = "https://example.invalid/radio",
            NextStartUtcTicks = DateTime.UtcNow.AddDays(1).Ticks
        }];
        state.Radio.RecordingHistory = [new RadioRecordingHistorySettings
        {
            Id = "recording-1",
            StationId = "radio-1",
            StationName = "Radio ze zrodla",
            Path = "D:\\Nagrania\\gotowe.mp3",
            SavedFileCount = 1
        }];
        state.Podcasts = new PodcastSettings
        {
            Subscriptions = [new PodcastSubscriptionSettings { Id = "podcast-1", Title = "Podcast ze zrodla", FeedUrl = "https://example.invalid/feed" }],
            Episodes = [new PodcastEpisodeSettings { Id = "episode-1", SubscriptionId = "podcast-1", Title = "Odcinek", MediaUrl = "https://example.invalid/audio", ResumePositionTicks = 25 }],
            DownloadsFolder = "D:\\Podcasty testowe",
            CurrentItemId = "episode-1",
            Volume = 91,
            PlaybackRate = 1.4
        };
        state.Playlists.Entries =
        [
            new PlaylistEntry { Id = "local-list", SessionId = "local", Name = "Lokalna", ItemIds = ["file-1"] },
            new PlaylistEntry { Id = "spotify-list", SessionId = "spotify", Name = "Spotify" }
        ];
        return state;
    }

    private static BookmarkEntry Bookmark(
        string id,
        BookmarkPurpose purpose,
        ChapterOrigin origin) => new()
    {
        Id = id,
        SessionId = "local",
        ItemId = "file-1",
        ItemTitle = "Plik ze zrodla",
        Purpose = purpose,
        ChapterOrigin = origin
    };

    private static void True(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }

    private static void False(bool value, string message) => True(!value, message);

    private static void Equal<T>(T expected, T actual, string message)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException($"{message}: oczekiwano {expected}, otrzymano {actual}.");
    }

    private static void Throws<TException>(Action action) where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException)
        {
            return;
        }
        throw new InvalidOperationException($"Oczekiwano wyjatku {typeof(TException).Name}.");
    }
}
