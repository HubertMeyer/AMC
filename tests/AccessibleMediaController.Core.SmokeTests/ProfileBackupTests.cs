using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Configuration;

internal static class ProfileBackupTests
{
    public static void Run()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            "amc-profile-backup-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            ExportsAndImportsIndependentSections(root);
            PreservesLegacyFullBackup(root);
            RejectsInvalidScopeWithoutChangingProfile(root);
            Console.WriteLine("PASS ProfileBackupTests");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void ExportsAndImportsIndependentSections(string root)
    {
        var sourceStore = CreateStore(Path.Combine(root, "source"));
        sourceStore.Save(CreateSource());
        var radioPath = Path.Combine(root, "radio.amcradio.json");
        var schedulesPath = Path.Combine(root, "schedules.amcschedules.json");
        var settingsPath = Path.Combine(root, "settings.amcsettings.json");

        var radioSummary = sourceStore.ExportCurrentBackup(
            radioPath,
            [ProfileBackupSectionCatalog.Radio]);
        sourceStore.ExportCurrentBackup(
            schedulesPath,
            [ProfileBackupSectionCatalog.RadioSchedules]);
        sourceStore.ExportCurrentBackup(
            settingsPath,
            [ProfileBackupSectionCatalog.Configuration]);

        Equal(ProfileBackupSectionCatalog.Radio, radioSummary.Sections.Single(), "Manifest Radia");
        Equal(1, radioSummary.RadioStations, "Liczba stacji w kopii Radia");
        Equal(0, radioSummary.RecordingSchedules, "Kopia Radia nie zawiera harmonogramow");
        Equal("profileBackup", JsonNode.Parse(File.ReadAllText(radioPath))?["kind"]?.GetValue<string>(),
            "Rodzaj kopii czesciowej");
        False(Directory.EnumerateFiles(root, ".*.tmp", SearchOption.TopDirectoryOnly).Any(),
            "Eksport nie zostawia plikow tymczasowych");

        var targetStore = CreateStore(Path.Combine(root, "target"));
        targetStore.Save(CreateTarget());
        targetStore.ImportAndSaveBackup(radioPath, [ProfileBackupSectionCatalog.Radio]);
        var afterRadio = targetStore.LoadOrCreate();
        Equal("Radio z kopii", afterRadio.Radio.Stations.Single().Name,
            "Import Radia zastapil stacje");
        Equal("plan-docelowy", afterRadio.Radio.RecordingSchedules.Single().Id,
            "Import Radia zachowal harmonogram");
        Equal(true, afterRadio.Settings.PausePlaybackWhenLeavingPlayer,
            "Import Radia zachowal ustawienia");
        Equal("plik-docelowy", afterRadio.LocalMedia.Items.Single().Id,
            "Import Radia zachowal Biblioteke");

        targetStore.ImportAndSaveBackup(
            schedulesPath,
            [ProfileBackupSectionCatalog.RadioSchedules]);
        var afterSchedules = targetStore.LoadOrCreate();
        Equal("Radio z kopii", afterSchedules.Radio.Stations.Single().Name,
            "Import harmonogramow zachowal stacje");
        Equal("plan-z-kopii", afterSchedules.Radio.RecordingSchedules.Single().Id,
            "Import harmonogramow zastapil tylko plany");

        targetStore.ImportAndSaveBackup(
            settingsPath,
            [ProfileBackupSectionCatalog.Configuration]);
        var afterSettings = targetStore.LoadOrCreate();
        Equal(false, afterSettings.Settings.PausePlaybackWhenLeavingPlayer,
            "Import ustawien zastapil ustawienia");
        Equal("Radio z kopii", afterSettings.Radio.Stations.Single().Name,
            "Import ustawien zachowal Radio");
        Equal("plan-z-kopii", afterSettings.Radio.RecordingSchedules.Single().Id,
            "Import ustawien zachowal harmonogramy");
    }

    private static void PreservesLegacyFullBackup(string root)
    {
        var sourceStore = CreateStore(Path.Combine(root, "legacy-source"));
        sourceStore.Save(CreateSource());
        var path = Path.Combine(root, "all.amcbackup.json");
        sourceStore.ExportCurrentBackup(path, ProfileBackupSectionCatalog.All);
        Equal("fullBackup", JsonNode.Parse(File.ReadAllText(path))?["kind"]?.GetValue<string>(),
            "Pelna kopia zachowuje historyczny rodzaj pliku");

        var targetStore = CreateStore(Path.Combine(root, "legacy-target"));
        targetStore.Save(CreateTarget());
        var result = targetStore.ImportAndSaveBackup(path);
        Equal(7, result.Summary.Sections.Count, "Pelna kopia opisuje wszystkie dzialy");
        var restored = targetStore.LoadOrCreate();
        Equal("Playlista z kopii", restored.Playlists.Entries.Single().Name,
            "Pelna kopia odtwarza playlisty AMC");
        Equal("plik-z-kopii", restored.LocalMedia.Items.Single().Id,
            "Pelna kopia odtwarza Biblioteke");
    }

    private static void RejectsInvalidScopeWithoutChangingProfile(string root)
    {
        var sourceStore = CreateStore(Path.Combine(root, "invalid-source"));
        sourceStore.Save(CreateSource());
        var path = Path.Combine(root, "radio-only.amcradio.json");
        sourceStore.ExportCurrentBackup(path, [ProfileBackupSectionCatalog.Radio]);

        var targetStore = CreateStore(Path.Combine(root, "invalid-target"));
        targetStore.Save(CreateTarget());
        Throws<InvalidDataException>(() => targetStore.ImportAndSaveBackup(
            path,
            [ProfileBackupSectionCatalog.Library]));
        var unchanged = targetStore.LoadOrCreate();
        Equal("Radio docelowe", unchanged.Radio.Stations.Single().Name,
            "Odrzucony import nie zmienia profilu");
        Equal("plik-docelowy", unchanged.LocalMedia.Items.Single().Id,
            "Odrzucony import nie zmienia Biblioteki");
    }

    private static ConfigurationStore CreateStore(string directory)
    {
        Directory.CreateDirectory(directory);
        return new ConfigurationStore(Path.Combine(directory, "state.json"));
    }

    private static PersistedState CreateSource()
    {
        var state = ConfigurationStore.CreateDefaultState();
        state.Settings.PausePlaybackWhenLeavingPlayer = false;
        state.LocalMedia.Items.Add(new LocalMediaItemSettings
        {
            Id = "plik-z-kopii",
            Title = "Audycja z kopii",
            Path = @"C:\Media\audycja.mp3",
            IsInLibrary = true
        });
        state.Playlists.Entries.Add(new PlaylistEntry
        {
            Id = "playlista-z-kopii",
            SessionId = "local",
            Name = "Playlista z kopii",
            CreatedUtcTicks = DateTime.UtcNow.Ticks,
            ItemIds = ["plik-z-kopii"]
        });
        state.Radio.Stations =
        [
            new RadioStationSettings
            {
                Id = "radio-z-kopii",
                Name = "Radio z kopii",
                StreamUrl = "https://example.invalid/source"
            }
        ];
        state.Radio.RecordingSchedules =
        [
            CreateSchedule("plan-z-kopii", "radio-z-kopii", "Radio z kopii")
        ];
        return state;
    }

    private static PersistedState CreateTarget()
    {
        var state = ConfigurationStore.CreateDefaultState();
        state.Settings.PausePlaybackWhenLeavingPlayer = true;
        state.LocalMedia.Items.Add(new LocalMediaItemSettings
        {
            Id = "plik-docelowy",
            Title = "Audycja docelowa",
            Path = @"C:\Media\docelowa.mp3",
            IsInLibrary = true
        });
        state.Radio.Stations =
        [
            new RadioStationSettings
            {
                Id = "radio-docelowe",
                Name = "Radio docelowe",
                StreamUrl = "https://example.invalid/target"
            }
        ];
        state.Radio.RecordingSchedules =
        [
            CreateSchedule("plan-docelowy", "radio-docelowe", "Radio docelowe")
        ];
        return state;
    }

    private static RadioRecordingScheduleSettings CreateSchedule(
        string id,
        string stationId,
        string stationName) => new()
    {
        Id = id,
        Name = "Poranek",
        StationId = stationId,
        StationName = stationName,
        StreamUrl = "https://example.invalid/live",
        NextStartUtcTicks = new DateTime(2026, 10, 22, 6, 0, 0, DateTimeKind.Utc).Ticks,
        TimeZoneId = "UTC",
        DurationMinutes = 60,
        Recurrence = RadioScheduleRecurrence.Daily,
        Enabled = true
    };

    private static void Equal<T>(T expected, T actual, string message)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new Exception($"{message}. Oczekiwano: {expected}; otrzymano: {actual}.");
    }

    private static void False(bool value, string message)
    {
        if (value) throw new Exception(message);
    }

    private static void Throws<T>(Action action) where T : Exception
    {
        try
        {
            action();
        }
        catch (T)
        {
            return;
        }
        throw new Exception($"Oczekiwano wyjatku {typeof(T).Name}.");
    }
}
