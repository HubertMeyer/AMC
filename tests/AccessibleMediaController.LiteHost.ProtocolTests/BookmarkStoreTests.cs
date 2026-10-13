using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.LiteHost.Protocol;
using Microsoft.Data.Sqlite;
using System.Text.Json;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

/// <summary>Waski zapis B: jedna tabela, duplikat i bramka starego WPF.</summary>
internal static class BookmarkStoreTests
{
    public static void Run()
    {
        var root = Path.Combine(
            Path.GetTempPath(), "amc-bookmark-store-" + Guid.NewGuid().ToString("N")[..8]);
        Directory.CreateDirectory(root);
        try
        {
            var database = Path.Combine(root, "library.db");
            CreateDatabase(database);
            var store = new LiteBookmarkStore(database, () => false);

            store.Add("plik-1", "Nagranie", TimeSpan.FromSeconds(12.4), DateTime.UtcNow);
            store.Add("plik-1", "Nagranie", TimeSpan.FromSeconds(12.8), DateTime.UtcNow);
            var named = JsonSerializer.SerializeToElement(store.Add(
                "plik-1",
                "Nagranie",
                TimeSpan.FromSeconds(12.6),
                DateTime.UtcNow,
                "  Ważny   fragment  "));
            Assert.True(!named.GetProperty("added").GetBoolean()
                && named.GetProperty("nameChanged").GetBoolean()
                && named.GetProperty("name").GetString() == "Ważny fragment",
                "nazwana zakladka nadaje nazwe istniejacej szybkiej zakladce");
            store.MutateBookmarks(settings =>
            {
                settings.Entries.Add(new BookmarkEntry
                {
                    Id = "chapter-1",
                    SessionId = "podcasts",
                    SessionName = "Podcasty i YouTube",
                    ItemId = "episode-1",
                    ItemTitle = "Odcinek",
                    Name = "Rozdział pierwszy",
                    PositionTicks = TimeSpan.FromMinutes(1).Ticks,
                    CreatedUtcTicks = DateTime.UtcNow.Ticks,
                    Purpose = BookmarkPurpose.Chapter,
                    ChapterOrigin = ChapterOrigin.Provider,
                    ChapterSourceId = "podcast-feed"
                });
                settings.Entries.Add(new BookmarkEntry
                {
                    Id = "bookmark-and-chapter",
                    SessionId = "local",
                    SessionName = "Pliki lokalne",
                    ItemId = "plik-1",
                    ItemTitle = "Nagranie",
                    Name = "Zakładka i rozdział",
                    PositionTicks = TimeSpan.FromMinutes(2).Ticks,
                    CreatedUtcTicks = DateTime.UtcNow.Ticks,
                    Purpose = BookmarkPurpose.Bookmark | BookmarkPurpose.Chapter,
                    ChapterOrigin = ChapterOrigin.User
                });
                return true;
            });

            var first = store.FindRelative(
                "local", "plik-1", TimeSpan.Zero, direction: 1);
            Assert.True(first is not null
                && first.PositionTicks == TimeSpan.FromSeconds(12).Ticks,
                "nastepna zakladka korzysta z tych samych regul co pelny AMC");
            var second = store.FindAdjacent(
                "local", "plik-1", first!.Id, direction: 1);
            Assert.True(second is not null
                && second.Id == "bookmark-and-chapter",
                "kontynuacja od kotwicy znajduje kolejna zakladke");
            var beforeFirst = store.FindAdjacent(
                "local", "plik-1", first.Id, direction: -1);
            Assert.True(beforeFirst is null,
                "przed pierwsza zakladka nie ma sztucznego wyniku");

            string quickBookmarkId;
            using (var connection = new SqliteConnection($"Data Source={database};Pooling=False"))
            {
                connection.Open();
                using var quick = connection.CreateCommand();
                quick.CommandText = """
                    SELECT id FROM bookmarks
                    WHERE item_id = 'plik-1' AND purpose = 1
                    ORDER BY ordinal LIMIT 1;
                    """;
                quickBookmarkId = Convert.ToString(quick.ExecuteScalar())!;
                using var quickName = connection.CreateCommand();
                quickName.CommandText = "SELECT name FROM bookmarks WHERE id = $id;";
                quickName.Parameters.AddWithValue("$id", quickBookmarkId);
                Assert.Equal(
                    "Ważny fragment",
                    Convert.ToString(quickName.ExecuteScalar()),
                    "znormalizowana nazwa zostaje zapisana w bazie");
            }
            var removal = JsonSerializer.SerializeToElement(store.Remove(
                [quickBookmarkId, "bookmark-and-chapter", "missing"]));
            Assert.True(removal.GetProperty("requestedCount").GetInt32() == 3
                && removal.GetProperty("removedCount").GetInt32() == 2,
                "usuwanie raportuje tylko rzeczywiscie zmienione zakladki");

            using (var connection = new SqliteConnection($"Data Source={database};Pooling=False"))
            {
                connection.Open();
                using var count = connection.CreateCommand();
                count.CommandText = "SELECT COUNT(*) FROM bookmarks;";
                Assert.True(Convert.ToInt64(count.ExecuteScalar()) == 2L,
                    "zwykla zakladka znika, a oba rozdzialy zostaja");
                using var combined = connection.CreateCommand();
                combined.CommandText =
                    "SELECT purpose FROM bookmarks WHERE id = 'bookmark-and-chapter';";
                Assert.True(Convert.ToInt32(combined.ExecuteScalar())
                    == (int)BookmarkPurpose.Chapter,
                    "usuniecie zakladki zachowuje ten sam wpis jako rozdzial");
                using var sentinel = connection.CreateCommand();
                sentinel.CommandText = "SELECT value FROM untouched WHERE id = 1;";
                Assert.Equal("zostaje", Convert.ToString(sentinel.ExecuteScalar()),
                    "waski zapis nie moze dotknac innych tabel");
            }

            var blocked = new LiteBookmarkStore(database, () => true);
            Assert.True(blocked.FindRelative(
                    "local", "plik-1", TimeSpan.Zero, direction: 1) is null,
                "odczyt zakladek pozostaje dozwolony przy dzialajacym starym AMC");
            var refused = false;
            try
            {
                blocked.Add("plik-1", "Nagranie", TimeSpan.FromSeconds(30), DateTime.UtcNow);
            }
            catch (LiteRequestException)
            {
                refused = true;
            }
            Assert.True(refused, "dzialajace stare AMC musi zablokowac zapis");
            refused = false;
            try
            {
                blocked.Remove(["bookmark-and-chapter"]);
            }
            catch (LiteRequestException)
            {
                refused = true;
            }
            Assert.True(refused, "dzialajace stare AMC musi blokowac tez usuwanie");

            TestRadioRecordingImport(root);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void TestRadioRecordingImport(string root)
    {
        var database = Path.Combine(root, "recording-library.db");
        CreateDatabase(database);
        var recording = Path.Combine(root, "Poranna audycja.mp3");
        File.WriteAllBytes(recording, [1, 2, 3, 4]);
        using (var connection = new SqliteConnection($"Data Source={database};Pooling=False"))
        {
            connection.Open();
            using var exclude = connection.CreateCommand();
            exclude.CommandText =
                "INSERT INTO excluded_paths(ordinal, path) VALUES(0, $path);";
            exclude.Parameters.AddWithValue("$path", recording);
            exclude.ExecuteNonQuery();
        }

        var store = new LiteBookmarkStore(database, () => false);
        LiteRecordingBookmark[] markers =
        [
            new(recording, TimeSpan.FromSeconds(5.2), DateTime.UtcNow, ""),
            new(recording, TimeSpan.FromSeconds(12.7), DateTime.UtcNow, "  Gość   audycji  ")
        ];
        var first = store.ImportRadioRecordingBookmarks(markers, DateTime.UtcNow);
        Assert.True(first.ImportedFileCount == 1 && first.BookmarkChangeCount == 2,
            "zakonczenie nagrania importuje plik i obie zakladki");
        var second = store.ImportRadioRecordingBookmarks(markers, DateTime.UtcNow);
        Assert.True(second.ImportedFileCount == 1 && second.BookmarkChangeCount == 0,
            "ponowna finalizacja nie dubluje pliku ani zakladek");

        using (var connection = new SqliteConnection($"Data Source={database};Pooling=False"))
        {
            connection.Open();
            Assert.True(Scalar(connection, "SELECT COUNT(*) FROM local_items;") == 1,
                "nagranie ma jeden wpis Biblioteki");
            Assert.True(Scalar(connection,
                    "SELECT is_in_library + is_available + is_radio_recording FROM local_items LIMIT 1;") == 3,
                "nagranie jest dostepnym plikiem Biblioteki oznaczonym jako nagranie radia");
            Assert.Equal("Poranna audycja", Text(connection,
                    "SELECT title FROM local_items LIMIT 1;"),
                "tytul nowego nagrania jest tekstem uzytkowym z nazwy pliku");
            Assert.True(Scalar(connection, "SELECT COUNT(*) FROM excluded_paths;") == 0,
                "import usuwa dawne wykluczenie tej sciezki");
            Assert.True(Scalar(connection, "SELECT COUNT(*) FROM bookmarks;") == 2,
                "obie zakladki trafiaja do wspolnej tabeli AMC");
            Assert.Equal("Gość audycji", Text(connection,
                    "SELECT name FROM bookmarks WHERE name <> '' LIMIT 1;"),
                "nazwa zakladki zostaje znormalizowana bez technicznych wartosci");
            Assert.Equal("zostaje", Text(connection,
                    "SELECT value FROM untouched WHERE id = 1;"),
                "import nagrania nie narusza obcych tabel");
        }

        var blocked = new LiteBookmarkStore(database, () => true);
        var refused = false;
        try
        {
            blocked.ImportRadioRecordingBookmarks(markers, DateTime.UtcNow);
        }
        catch (LiteRequestException)
        {
            refused = true;
        }
        Assert.True(refused,
            "stare AMC blokuje takze finalny import zakladek nagrania");
    }

    private static long Scalar(SqliteConnection connection, string sql)
    {
        using var command = connection.CreateCommand();
        command.CommandText = sql;
        return Convert.ToInt64(command.ExecuteScalar());
    }

    private static string Text(SqliteConnection connection, string sql)
    {
        using var command = connection.CreateCommand();
        command.CommandText = sql;
        return Convert.ToString(command.ExecuteScalar()) ?? string.Empty;
    }

    private static void CreateDatabase(string path)
    {
        using var connection = new SqliteConnection($"Data Source={path};Pooling=False");
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText = """
            CREATE TABLE bookmarks (
                id TEXT PRIMARY KEY,
                ordinal INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                session_name TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_title TEXT NOT NULL,
                name TEXT NOT NULL,
                position_ticks INTEGER NOT NULL,
                created_utc_ticks INTEGER NOT NULL,
                purpose INTEGER NOT NULL DEFAULT 1,
                chapter_origin INTEGER NOT NULL DEFAULT 0,
                chapter_source_id TEXT NULL
            );
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE local_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                has_custom_title INTEGER NOT NULL,
                path TEXT NOT NULL,
                duration_ticks INTEGER NOT NULL,
                bitrate_kbps INTEGER NULL,
                bitrate_estimated INTEGER NOT NULL,
                sample_rate_hz INTEGER NULL,
                is_favorite INTEGER NOT NULL,
                is_in_library INTEGER NOT NULL,
                is_available INTEGER NOT NULL,
                is_in_queue INTEGER NOT NULL,
                is_play_next INTEGER NOT NULL,
                resume_mode INTEGER NOT NULL,
                playback_rate_override REAL NULL,
                output_device_id TEXT NULL,
                resume_position_ticks INTEGER NOT NULL,
                file_length INTEGER NULL,
                last_write_utc_ticks INTEGER NULL,
                loudness_normalization_override INTEGER NULL,
                smooth_track_transitions_override INTEGER NULL,
                inter_track_silence_ms_override INTEGER NULL,
                tempo_algorithm_override INTEGER NULL,
                clip_start_ticks INTEGER NULL,
                clip_end_ticks INTEGER NULL,
                is_radio_recording INTEGER NOT NULL DEFAULT 0,
                radio_recording_completed_utc_ticks INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE excluded_paths (
                ordinal INTEGER PRIMARY KEY,
                path TEXT NOT NULL
            );
            CREATE TABLE untouched (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO untouched(id, value) VALUES (1, 'zostaje');
            """;
        command.ExecuteNonQuery();
    }
}
