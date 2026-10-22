using System.Diagnostics;
using System.Globalization;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;
using Microsoft.Data.Sqlite;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteRecordingBookmark(
    string Path,
    TimeSpan Position,
    DateTime CreatedUtc,
    string Name);

internal sealed record LiteRecordingBookmarkImportResult(
    int ImportedFileCount,
    int BookmarkChangeCount);

/// <summary>
/// Waski zapis szybkiej zakladki do tej samej tabeli, ktora czyta pelne AMC.
///
/// Nie zapisujemy calego <c>PersistedState</c>: host Lite nie ma kompletnego
/// stanu i taki zapis skasowalby cudze dane. Jedna transakcja dotyka tylko
/// jednego wiersza tabeli <c>bookmarks</c>.
/// </summary>
internal sealed class LiteBookmarkStore
{
    private const long TicksPerSecond = TimeSpan.TicksPerSecond;
    private readonly object _gate = new();
    private readonly string _databasePath;
    private readonly Func<bool> _fullAmcIsRunning;

    public LiteBookmarkStore(string databasePath, Func<bool>? fullAmcIsRunning = null)
    {
        _databasePath = Path.GetFullPath(databasePath);
        _fullAmcIsRunning = fullAmcIsRunning ?? FullAmcIsRunning;
    }

    public object Add(
        string itemId,
        string itemTitle,
        TimeSpan position,
        DateTime utcNow,
        string? name = null) =>
        Add("local", "Pliki lokalne", itemId, itemTitle, position, utcNow, name);

    public object Add(
        string sessionId,
        string sessionName,
        string itemId,
        string itemTitle,
        TimeSpan position,
        DateTime utcNow,
        string? name = null)
    {
        if (string.IsNullOrWhiteSpace(sessionId))
            throw new LiteRequestException("Bieżąca sesja nie ma identyfikatora.");
        if (string.IsNullOrWhiteSpace(itemId))
            throw new LiteRequestException("Bieżący materiał nie ma identyfikatora Biblioteki.");
        EnsureMayWriteBookmarks();

        var roundedTicks = TimeSpan.FromSeconds(
            Math.Round(Math.Max(0d, position.TotalSeconds))).Ticks;
        var createdTicks = utcNow.ToUniversalTime().Ticks;
        var normalizedName = NormalizeName(name);
        lock (_gate)
        {
            using var connection = new SqliteConnection(new SqliteConnectionStringBuilder
            {
                DataSource = _databasePath,
                Mode = SqliteOpenMode.ReadWrite,
                Cache = SqliteCacheMode.Shared,
                // Jedno nacisniecie B = jedna krotka transakcja. Pula nie
                // moze trzymac uchwytu do bazy po operacji ani utrudniac
                // pozniejszego uruchomienia glownego AMC.
                Pooling = false
            }.ToString());
            connection.Open();
            using var transaction = connection.BeginTransaction();

            using var existing = connection.CreateCommand();
            existing.Transaction = transaction;
            existing.CommandText = """
                SELECT id, position_ticks, name
                FROM bookmarks
                WHERE session_id = $session_id COLLATE NOCASE
                  AND item_id = $item_id
                  AND (purpose & 1) != 0
                  AND ABS(position_ticks - $position_ticks) <= $tolerance
                ORDER BY ABS(position_ticks - $position_ticks), ordinal
                LIMIT 1;
                """;
            existing.Parameters.AddWithValue("$item_id", itemId);
            existing.Parameters.AddWithValue("$session_id", sessionId.Trim());
            existing.Parameters.AddWithValue("$position_ticks", roundedTicks);
            existing.Parameters.AddWithValue("$tolerance", TicksPerSecond);
            string? existingId = null;
            long existingTicks = 0;
            var existingName = string.Empty;
            using (var reader = existing.ExecuteReader())
            {
                if (reader.Read())
                {
                    existingId = reader.GetString(0);
                    existingTicks = reader.GetInt64(1);
                    existingName = reader.GetString(2);
                }
            }
            if (existingId is not null)
            {
                var nameChanged = normalizedName.Length > 0
                    && !string.Equals(
                        existingName,
                        normalizedName,
                        StringComparison.CurrentCulture);
                if (nameChanged)
                {
                    using var rename = connection.CreateCommand();
                    rename.Transaction = transaction;
                    rename.CommandText = "UPDATE bookmarks SET name = $name WHERE id = $id;";
                    rename.Parameters.AddWithValue("$name", normalizedName);
                    rename.Parameters.AddWithValue("$id", existingId);
                    rename.ExecuteNonQuery();
                    existingName = normalizedName;
                }
                transaction.Commit();
                return new
                {
                    added = false,
                    nameChanged,
                    bookmarkId = existingId,
                    positionSeconds = TimeSpan.FromTicks(existingTicks).TotalSeconds,
                    name = existingName
                };
            }

            long ordinal;
            using (var order = connection.CreateCommand())
            {
                order.Transaction = transaction;
                order.CommandText = "SELECT COALESCE(MAX(ordinal), -1) + 1 FROM bookmarks;";
                ordinal = Convert.ToInt64(order.ExecuteScalar());
            }

            var bookmarkId = Guid.NewGuid().ToString("N");
            using var insert = connection.CreateCommand();
            insert.Transaction = transaction;
            insert.CommandText = """
                INSERT INTO bookmarks(
                    id, ordinal, session_id, session_name, item_id, item_title,
                    name, position_ticks, created_utc_ticks, purpose,
                    chapter_origin, chapter_source_id)
                VALUES(
                    $id, $ordinal, $session_id, $session_name, $item_id, $item_title,
                    $name, $position_ticks, $created_ticks, 1, 0, NULL);
                """;
            insert.Parameters.AddWithValue("$id", bookmarkId);
            insert.Parameters.AddWithValue("$ordinal", ordinal);
            insert.Parameters.AddWithValue("$session_id", sessionId.Trim());
            insert.Parameters.AddWithValue(
                "$session_name",
                string.IsNullOrWhiteSpace(sessionName) ? sessionId.Trim() : sessionName.Trim());
            insert.Parameters.AddWithValue("$item_id", itemId);
            insert.Parameters.AddWithValue("$item_title", itemTitle);
            insert.Parameters.AddWithValue("$name", normalizedName);
            insert.Parameters.AddWithValue("$position_ticks", roundedTicks);
            insert.Parameters.AddWithValue("$created_ticks", createdTicks);
            insert.ExecuteNonQuery();
            transaction.Commit();
            return new
            {
                added = true,
                nameChanged = false,
                bookmarkId,
                positionSeconds = TimeSpan.FromTicks(roundedTicks).TotalSeconds,
                name = normalizedName
            };
        }
    }

    /// <summary>
    /// Sprawdza warunki zapisu jeszcze PRZED dodaniem znacznika do trwajacego
    /// nagrania. Dzieki temu uzytkownik nie dostaje pozornego potwierdzenia,
    /// ktore dopiero po zakonczeniu pliku okazaloby sie nietrwale.
    /// </summary>
    public void EnsureMayWriteBookmarks()
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");

        // Zainstalowany starszy WPF nie zna jeszcze blokady hosta Lite i moze
        // zapisac cala tabele ze swojej pamieci. Wtedy nasz poprawny INSERT
        // zostalby pozniej utracony. Odmawiamy, dopoki ten proces dziala.
        if (_fullAmcIsRunning())
        {
            throw new LiteRequestException(
                "Zamknij najpierw główne AMC. Równoczesny zapis zakładki z dwóch wersji mógłby utracić dane.");
        }
    }

    /// <summary>
    /// Po finalizacji nagrania importuje jedynie jego pliki i zakladki. Nie
    /// odtwarza ani nie zapisuje calego PersistedState, wiec nie moze nadpisac
    /// kolejki, Ulubionych, historii ani ustawien otwartych w wxPython.
    /// </summary>
    public LiteRecordingBookmarkImportResult ImportRadioRecordingBookmarks(
        IReadOnlyCollection<LiteRecordingBookmark> markers,
        DateTime completedUtc)
    {
        ArgumentNullException.ThrowIfNull(markers);
        var groups = markers
            .Where(marker => !string.IsNullOrWhiteSpace(marker.Path))
            .GroupBy(marker => Path.GetFullPath(marker.Path), StringComparer.OrdinalIgnoreCase)
            .ToArray();
        if (groups.Length == 0) return new(0, 0);
        EnsureMayWriteBookmarks();

        lock (_gate)
        {
            using var connection = OpenConnection();
            using var transaction = connection.BeginTransaction();
            var nextOrdinal = ReadNextBookmarkOrdinal(connection, transaction);
            var importedFiles = 0;
            var bookmarkChanges = 0;

            foreach (var group in groups)
            {
                var path = group.Key;
                if (!File.Exists(path)) continue;
                var info = new FileInfo(path);
                var title = Path.GetFileNameWithoutExtension(path);
                var item = FindLocalItemByPath(connection, transaction, path);
                var itemId = item?.Id ?? $"local-{Guid.NewGuid():N}";
                if (item is null)
                {
                    using var insertItem = connection.CreateCommand();
                    insertItem.Transaction = transaction;
                    insertItem.CommandText = """
                        INSERT INTO local_items(
                            id, title, has_custom_title, path, duration_ticks,
                            bitrate_kbps, bitrate_estimated, sample_rate_hz,
                            is_favorite, is_in_library, is_available, is_in_queue,
                            is_play_next, resume_mode, playback_rate_override,
                            output_device_id, resume_position_ticks, file_length,
                            last_write_utc_ticks, loudness_normalization_override,
                            smooth_track_transitions_override,
                            inter_track_silence_ms_override, tempo_algorithm_override,
                            clip_start_ticks, clip_end_ticks, is_radio_recording,
                            radio_recording_completed_utc_ticks)
                        VALUES(
                            $id, $title, 0, $path, 0,
                            NULL, 0, NULL,
                            0, 1, 1, 0,
                            0, 0, NULL,
                            NULL, 0, $length,
                            $last_write, NULL,
                            NULL,
                            NULL, NULL,
                            NULL, NULL, 1,
                            $completed);
                        """;
                    insertItem.Parameters.AddWithValue("$id", itemId);
                    insertItem.Parameters.AddWithValue("$title", title);
                    insertItem.Parameters.AddWithValue("$path", path);
                    insertItem.Parameters.AddWithValue("$length", info.Length);
                    insertItem.Parameters.AddWithValue("$last_write", info.LastWriteTimeUtc.Ticks);
                    insertItem.Parameters.AddWithValue(
                        "$completed", completedUtc.ToUniversalTime().Ticks);
                    insertItem.ExecuteNonQuery();
                }
                else
                {
                    title = item.Title;
                    using var updateItem = connection.CreateCommand();
                    updateItem.Transaction = transaction;
                    updateItem.CommandText = """
                        UPDATE local_items
                        SET is_in_library = 1,
                            is_available = 1,
                            is_radio_recording = 1,
                            radio_recording_completed_utc_ticks = $completed,
                            file_length = $length,
                            last_write_utc_ticks = $last_write
                        WHERE id = $id;
                        """;
                    updateItem.Parameters.AddWithValue("$completed", completedUtc.ToUniversalTime().Ticks);
                    updateItem.Parameters.AddWithValue("$length", info.Length);
                    updateItem.Parameters.AddWithValue("$last_write", info.LastWriteTimeUtc.Ticks);
                    updateItem.Parameters.AddWithValue("$id", itemId);
                    updateItem.ExecuteNonQuery();
                }

                using (var include = connection.CreateCommand())
                {
                    include.Transaction = transaction;
                    include.CommandText =
                        "DELETE FROM excluded_paths WHERE path = $path COLLATE NOCASE;";
                    include.Parameters.AddWithValue("$path", path);
                    include.ExecuteNonQuery();
                }

                foreach (var marker in group)
                {
                    if (AddBookmark(
                            connection,
                            transaction,
                            itemId,
                            title,
                            marker,
                            ref nextOrdinal))
                    {
                        bookmarkChanges++;
                    }
                }
                importedFiles++;
            }

            if (importedFiles > 0)
            {
                using var metadata = connection.CreateCommand();
                metadata.Transaction = transaction;
                metadata.CommandText = """
                    INSERT INTO metadata(key, value) VALUES('last_saved_utc', $value)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                    """;
                metadata.Parameters.AddWithValue(
                    "$value", DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture));
                metadata.ExecuteNonQuery();
            }
            transaction.Commit();
            return new(importedFiles, bookmarkChanges);
        }
    }

    private static bool AddBookmark(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string itemId,
        string itemTitle,
        LiteRecordingBookmark marker,
        ref long nextOrdinal)
    {
        var positionTicks = TimeSpan.FromSeconds(
            Math.Round(Math.Max(0d, marker.Position.TotalSeconds))).Ticks;
        var name = NormalizeName(marker.Name);
        using var existing = connection.CreateCommand();
        existing.Transaction = transaction;
        existing.CommandText = """
            SELECT id, name
            FROM bookmarks
            WHERE session_id = 'local' COLLATE NOCASE
              AND item_id = $item_id
              AND (purpose & 1) != 0
              AND ABS(position_ticks - $position_ticks) <= $tolerance
            ORDER BY ABS(position_ticks - $position_ticks), ordinal
            LIMIT 1;
            """;
        existing.Parameters.AddWithValue("$item_id", itemId);
        existing.Parameters.AddWithValue("$position_ticks", positionTicks);
        existing.Parameters.AddWithValue("$tolerance", TicksPerSecond);
        string? existingId = null;
        var existingName = string.Empty;
        using (var reader = existing.ExecuteReader())
        {
            if (reader.Read())
            {
                existingId = reader.GetString(0);
                existingName = reader.GetString(1);
            }
        }
        if (existingId is not null)
        {
            if (name.Length == 0
                || string.Equals(name, existingName, StringComparison.CurrentCulture))
            {
                return false;
            }
            using var rename = connection.CreateCommand();
            rename.Transaction = transaction;
            rename.CommandText = "UPDATE bookmarks SET name = $name WHERE id = $id;";
            rename.Parameters.AddWithValue("$name", name);
            rename.Parameters.AddWithValue("$id", existingId);
            rename.ExecuteNonQuery();
            return true;
        }

        using var insert = connection.CreateCommand();
        insert.Transaction = transaction;
        insert.CommandText = """
            INSERT INTO bookmarks(
                id, ordinal, session_id, session_name, item_id, item_title,
                name, position_ticks, created_utc_ticks, purpose,
                chapter_origin, chapter_source_id)
            VALUES(
                $id, $ordinal, 'local', 'Pliki lokalne', $item_id, $item_title,
                $name, $position_ticks, $created_ticks, 1, 0, NULL);
            """;
        insert.Parameters.AddWithValue("$id", Guid.NewGuid().ToString("N"));
        insert.Parameters.AddWithValue("$ordinal", nextOrdinal++);
        insert.Parameters.AddWithValue("$item_id", itemId);
        insert.Parameters.AddWithValue("$item_title", itemTitle);
        insert.Parameters.AddWithValue("$name", name);
        insert.Parameters.AddWithValue("$position_ticks", positionTicks);
        insert.Parameters.AddWithValue(
            "$created_ticks", marker.CreatedUtc.ToUniversalTime().Ticks);
        insert.ExecuteNonQuery();
        return true;
    }

    private static long ReadNextBookmarkOrdinal(
        SqliteConnection connection,
        SqliteTransaction transaction)
    {
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT COALESCE(MAX(ordinal), -1) + 1 FROM bookmarks;";
        return Convert.ToInt64(command.ExecuteScalar(), CultureInfo.InvariantCulture);
    }

    private static LocalItemIdentity? FindLocalItemByPath(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string path)
    {
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = """
            SELECT id, title
            FROM local_items
            WHERE path = $path COLLATE NOCASE
            ORDER BY is_in_library DESC
            LIMIT 1;
            """;
        command.Parameters.AddWithValue("$path", path);
        using var reader = command.ExecuteReader();
        return reader.Read()
            ? new LocalItemIdentity(reader.GetString(0), reader.GetString(1))
            : null;
    }

    private sealed record LocalItemIdentity(string Id, string Title);

    private static string NormalizeName(string? name)
    {
        if (string.IsNullOrWhiteSpace(name)) return string.Empty;
        var normalized = string.Join(
            ' ',
            name.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries));
        return normalized.Length <= 200
            ? normalized
            : normalized[..200].TrimEnd();
    }

    /// <summary>
    /// Usuwa wyłącznie bit zakładki dla wskazanych wpisów. Wpis będący także
    /// rozdziałem zostaje w bazie jako rozdział, zgodnie z
    /// <see cref="BookmarkIndex.Remove"/>. Zwykła zakładka znika w całości.
    /// </summary>
    public object Remove(IReadOnlyCollection<string> bookmarkIds)
    {
        ArgumentNullException.ThrowIfNull(bookmarkIds);
        var ids = bookmarkIds
            .Where(id => !string.IsNullOrWhiteSpace(id))
            .Select(id => id.Trim())
            .Distinct(StringComparer.Ordinal)
            .Take(1_000)
            .ToArray();
        if (ids.Length == 0)
            throw new LiteRequestException("Brak zakładek do usunięcia.");
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        if (_fullAmcIsRunning())
        {
            throw new LiteRequestException(
                "Zamknij najpierw główne AMC. Równoczesne usuwanie zakładek z dwóch wersji mogłoby utracić dane.");
        }

        lock (_gate)
        {
            using var connection = OpenConnection();
            using var transaction = connection.BeginTransaction();
            var removed = 0;
            foreach (var id in ids)
            {
                int? purpose = null;
                using (var read = connection.CreateCommand())
                {
                    read.Transaction = transaction;
                    read.CommandText = """
                        SELECT purpose FROM bookmarks
                        WHERE id = $id AND (purpose & 1) != 0;
                        """;
                    read.Parameters.AddWithValue("$id", id);
                    var value = read.ExecuteScalar();
                    if (value is not null && value is not DBNull)
                        purpose = Convert.ToInt32(value, CultureInfo.InvariantCulture);
                }
                if (purpose is null) continue;

                using var change = connection.CreateCommand();
                change.Transaction = transaction;
                change.Parameters.AddWithValue("$id", id);
                if ((purpose.Value & (int)BookmarkPurpose.Chapter) != 0)
                {
                    change.CommandText =
                        "UPDATE bookmarks SET purpose = purpose & ~1 WHERE id = $id;";
                }
                else
                {
                    change.CommandText = "DELETE FROM bookmarks WHERE id = $id;";
                }
                removed += change.ExecuteNonQuery();
            }
            transaction.Commit();
            return new { requestedCount = ids.Length, removedCount = removed };
        }
    }

    /// <summary>
    /// Odczytuje zakladke wzgledem rzeczywistej pozycji odtwarzania. To jest
    /// operacja tylko do odczytu, wiec pozostaje bezpieczna takze wtedy, gdy
    /// starszy interfejs AMC jest uruchomiony. Reguly wyboru (w tym
    /// dwusekundowa tolerancja) pozostaja wspolne z pelnym AMC.
    /// </summary>
    public BookmarkEntry? FindRelative(
        string sessionId,
        string itemId,
        TimeSpan currentPosition,
        int direction)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            var index = new BookmarkIndex(ReadBookmarks(connection, transaction));
            return index.FindRelative(sessionId, itemId, currentPosition, direction);
        }
    }

    /// <summary>
    /// Kontynuuje nawigacje od konkretnej zakladki. Pelny AMC uzywa tej
    /// sciezki przez piec sekund, aby dwie bardzo bliskie zakladki nadal byly
    /// osiagalne kolejnymi nacisnieciami Shift+Page Up lub Shift+Page Down.
    /// </summary>
    public BookmarkEntry? FindAdjacent(
        string sessionId,
        string itemId,
        string anchorBookmarkId,
        int direction)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            var index = new BookmarkIndex(ReadBookmarks(connection, transaction));
            return index.FindAdjacent(sessionId, itemId, anchorBookmarkId, direction);
        }
    }

    public BookmarkEntry? FindNamedRelative(
        string sessionId,
        string itemId,
        TimeSpan currentPosition,
        int direction)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            var index = new BookmarkIndex(ReadBookmarks(connection, transaction));
            return index.FindNamedRelative(sessionId, itemId, currentPosition, direction);
        }
    }

    public BookmarkEntry? FindNamedAdjacent(
        string sessionId,
        string itemId,
        string anchorBookmarkId,
        int direction)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            var index = new BookmarkIndex(ReadBookmarks(connection, transaction));
            return index.FindNamedAdjacent(sessionId, itemId, anchorBookmarkId, direction);
        }
    }

    public IReadOnlyList<ChapterSegment> GetChapters(
        string sessionId,
        string itemId,
        TimeSpan itemDuration)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            return new ChapterIndex(ReadBookmarks(connection, transaction))
                .GetForItem(sessionId, itemId, itemDuration);
        }
    }

    public ChapterAddResult AddUserChapter(
        string sessionId,
        string sessionName,
        MediaItem item,
        TimeSpan position,
        DateTime utcNow,
        string name) =>
        MutateBookmarks(settings => new ChapterIndex(settings).AddUserChapter(
            sessionId,
            sessionName,
            item,
            position,
            utcNow,
            name));

    public int ReplaceProviderChapters(
        string sessionId,
        string sessionName,
        MediaItem item,
        string sourceFamily,
        IEnumerable<ProviderChapterPoint> chapters,
        DateTime utcNow) =>
        MutateBookmarks(settings => new ChapterIndex(settings).ReplaceProviderChapters(
            sessionId,
            sessionName,
            item,
            sourceFamily,
            chapters,
            utcNow));

    public ChapterSegment? FindChapter(
        string sessionId,
        string itemId,
        TimeSpan itemDuration,
        TimeSpan currentPosition,
        int direction)
    {
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        lock (_gate)
        {
            using var connection = OpenReadOnlyConnection();
            using var transaction = connection.BeginTransaction();
            return new ChapterIndex(ReadBookmarks(connection, transaction)).FindRelative(
                sessionId,
                itemId,
                itemDuration,
                currentPosition,
                direction);
        }
    }

    /// <summary>
    /// Wczytuje i zapisuje wyłącznie tabelę zakładek w jednej sekcji
    /// krytycznej. Odświeżanie kanału może dzięki temu użyć wspólnego
    /// ChapterIndex bez nadpisywania Biblioteki, historii ani kolejki.
    /// </summary>
    public T MutateBookmarks<T>(Func<BookmarkSettings, T> mutation)
    {
        ArgumentNullException.ThrowIfNull(mutation);
        if (!File.Exists(_databasePath))
            throw new LiteRequestException("Nie znajduję bazy Biblioteki AMC.");
        if (_fullAmcIsRunning())
        {
            throw new LiteRequestException(
                "Zamknij najpierw główne AMC. Równoczesna zmiana rozdziałów z dwóch wersji mogłaby utracić dane.");
        }

        lock (_gate)
        {
            using var connection = OpenConnection();
            using var transaction = connection.BeginTransaction();
            var settings = ReadBookmarks(connection, transaction);
            var result = mutation(settings);

            using (var clear = connection.CreateCommand())
            {
                clear.Transaction = transaction;
                clear.CommandText = "DELETE FROM bookmarks;";
                clear.ExecuteNonQuery();
            }
            for (var index = 0; index < settings.Entries.Count; index++)
            {
                var entry = settings.Entries[index];
                using var insert = connection.CreateCommand();
                insert.Transaction = transaction;
                insert.CommandText = """
                    INSERT INTO bookmarks(
                        id, ordinal, session_id, session_name, item_id, item_title,
                        name, position_ticks, created_utc_ticks, purpose,
                        chapter_origin, chapter_source_id)
                    VALUES(
                        $id, $ordinal, $session, $session_name, $item, $item_title,
                        $name, $position, $created, $purpose, $origin, $source);
                    """;
                insert.Parameters.AddWithValue("$id", entry.Id);
                insert.Parameters.AddWithValue("$ordinal", index);
                insert.Parameters.AddWithValue("$session", entry.SessionId);
                insert.Parameters.AddWithValue("$session_name", entry.SessionName);
                insert.Parameters.AddWithValue("$item", entry.ItemId);
                insert.Parameters.AddWithValue("$item_title", entry.ItemTitle);
                insert.Parameters.AddWithValue("$name", entry.Name);
                insert.Parameters.AddWithValue("$position", entry.PositionTicks);
                insert.Parameters.AddWithValue("$created", entry.CreatedUtcTicks);
                insert.Parameters.AddWithValue("$purpose", (int)entry.Purpose);
                insert.Parameters.AddWithValue("$origin", (int)entry.ChapterOrigin);
                insert.Parameters.AddWithValue(
                    "$source", (object?)entry.ChapterSourceId ?? DBNull.Value);
                insert.ExecuteNonQuery();
            }
            using (var metadata = connection.CreateCommand())
            {
                metadata.Transaction = transaction;
                metadata.CommandText = """
                    INSERT INTO metadata(key, value) VALUES('last_saved_utc', $value)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                    """;
                metadata.Parameters.AddWithValue(
                    "$value", DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture));
                metadata.ExecuteNonQuery();
            }
            transaction.Commit();
            return result;
        }
    }

    private SqliteConnection OpenConnection()
    {
        var connection = new SqliteConnection(new SqliteConnectionStringBuilder
        {
            DataSource = _databasePath,
            Mode = SqliteOpenMode.ReadWrite,
            Cache = SqliteCacheMode.Shared,
            Pooling = false
        }.ToString());
        RegisterPolishCollation(connection);
        connection.Open();
        using var setup = connection.CreateCommand();
        setup.CommandText = "PRAGMA busy_timeout=5000;";
        setup.ExecuteNonQuery();
        return connection;
    }

    private SqliteConnection OpenReadOnlyConnection()
    {
        var connection = new SqliteConnection(new SqliteConnectionStringBuilder
        {
            DataSource = _databasePath,
            Mode = SqliteOpenMode.ReadOnly,
            Cache = SqliteCacheMode.Shared,
            Pooling = false
        }.ToString());
        RegisterPolishCollation(connection);
        connection.Open();
        using var setup = connection.CreateCommand();
        setup.CommandText = "PRAGMA busy_timeout=5000;";
        setup.ExecuteNonQuery();
        return connection;
    }

    private static void RegisterPolishCollation(SqliteConnection connection)
    {
        connection.CreateCollation(
            "AMC_PL",
            (left, right) => CultureInfo.GetCultureInfo("pl-PL").CompareInfo.Compare(
                left,
                right,
                CompareOptions.IgnoreCase | CompareOptions.IgnoreNonSpace));
    }

    private static BookmarkSettings ReadBookmarks(
        SqliteConnection connection,
        SqliteTransaction transaction)
    {
        var settings = new BookmarkSettings();
        using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = """
            SELECT id, session_id, session_name, item_id, item_title, name,
                   position_ticks, created_utc_ticks, purpose, chapter_origin,
                   chapter_source_id
            FROM bookmarks ORDER BY ordinal;
            """;
        using var reader = command.ExecuteReader();
        while (reader.Read())
        {
            settings.Entries.Add(new BookmarkEntry
            {
                Id = reader.GetString(0),
                SessionId = reader.GetString(1),
                SessionName = reader.GetString(2),
                ItemId = reader.GetString(3),
                ItemTitle = reader.GetString(4),
                Name = reader.GetString(5),
                PositionTicks = reader.GetInt64(6),
                CreatedUtcTicks = reader.GetInt64(7),
                Purpose = (BookmarkPurpose)reader.GetInt32(8),
                ChapterOrigin = (ChapterOrigin)reader.GetInt32(9),
                ChapterSourceId = reader.IsDBNull(10) ? null : reader.GetString(10)
            });
        }
        return settings;
    }

    private static bool FullAmcIsRunning()
    {
        foreach (var process in Process.GetProcessesByName("AccessibleMediaController"))
        {
            using (process)
            {
                if (process.Id != Environment.ProcessId && !process.HasExited) return true;
            }
        }
        return false;
    }
}
