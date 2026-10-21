using AccessibleMediaController.Core.Configuration;
using Microsoft.Data.Sqlite;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Atomowa aktualizacja jednej sesji historii odtwarzania w <c>library.db</c>.
///
/// Kolejność jest taka sama jak w <see cref="PlaybackHistory.Record"/>:
/// najnowsza pozycja ma ordinal zero, ponowne odtworzenie przesuwa wpis na
/// początek, a ogon jest ograniczony do 500 pozycji. Klasa nie zna GUI ani
/// obiektów odtwarzacza, dzięki czemu zapis można sprawdzić bez uruchamiania
/// urządzenia audio.
/// </summary>
internal static class LitePlaybackHistoryMutation
{
    public static bool Record(
        SqliteConnection connection,
        SqliteTransaction transaction,
        string sessionId,
        string itemId)
    {
        var session = sessionId.Trim().ToLowerInvariant();
        var item = itemId.Trim();
        if (session.Length == 0 || item.Length == 0) return false;

        var entries = new List<string>();
        using (var read = connection.CreateCommand())
        {
            read.Transaction = transaction;
            read.CommandText =
                "SELECT item_id FROM playback_history "
                + "WHERE session_id = $session COLLATE NOCASE ORDER BY ordinal;";
            read.Parameters.AddWithValue("$session", session);
            using var reader = read.ExecuteReader();
            while (reader.Read())
            {
                var value = reader.GetString(0);
                if (!string.IsNullOrWhiteSpace(value)
                    && !entries.Contains(value, StringComparer.Ordinal))
                {
                    entries.Add(value);
                }
            }
        }

        var existing = entries.FindIndex(value =>
            string.Equals(value, item, StringComparison.Ordinal));
        if (existing == 0) return false;
        if (existing > 0) entries.RemoveAt(existing);
        entries.Insert(0, item);
        if (entries.Count > PlaybackHistory.MaxEntriesPerSession)
        {
            entries.RemoveRange(
                PlaybackHistory.MaxEntriesPerSession,
                entries.Count - PlaybackHistory.MaxEntriesPerSession);
        }

        using (var delete = connection.CreateCommand())
        {
            delete.Transaction = transaction;
            delete.CommandText =
                "DELETE FROM playback_history "
                + "WHERE session_id = $session COLLATE NOCASE;";
            delete.Parameters.AddWithValue("$session", session);
            delete.ExecuteNonQuery();
        }

        for (var ordinal = 0; ordinal < entries.Count; ordinal++)
        {
            using var insert = connection.CreateCommand();
            insert.Transaction = transaction;
            insert.CommandText =
                "INSERT INTO playback_history(session_id, ordinal, item_id) "
                + "VALUES($session, $ordinal, $item);";
            insert.Parameters.AddWithValue("$session", session);
            insert.Parameters.AddWithValue("$ordinal", ordinal);
            insert.Parameters.AddWithValue("$item", entries[ordinal]);
            insert.ExecuteNonQuery();
        }
        return true;
    }
}
