using AccessibleMediaController.LiteHost;
using Microsoft.Data.Sqlite;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class PlaybackHistoryMutationTests
{
    public static void Run()
    {
        MovesReplayedItemToFrontAndKeepsSessionsSeparate();
        CapsOneSessionAtFiveHundredItems();
        Console.WriteLine("PlaybackHistoryMutationTests: OK");
    }

    private static void MovesReplayedItemToFrontAndKeepsSessionsSeparate()
    {
        using var connection = OpenDatabase();
        Record(connection, "radio", "stacja-1");
        Record(connection, "radio", "stacja-2");
        Record(connection, "podcasts", "odcinek-1");
        Record(connection, "RADIO", "stacja-1");

        Assert.True(Read(connection, "radio").SequenceEqual(["stacja-1", "stacja-2"]),
            "ponowne odtworzenie przesuwa stację na początek bez duplikatu");
        Assert.True(Read(connection, "podcasts").SequenceEqual(["odcinek-1"]),
            "historia podcastów pozostaje oddzielona od historii radia");

        using var transaction = connection.BeginTransaction();
        var changed = LitePlaybackHistoryMutation.Record(
            connection, transaction, "radio", "stacja-1");
        transaction.Commit();
        Assert.True(!changed, "pozycja już na początku nie wymaga ponownego zapisu");
    }

    private static void CapsOneSessionAtFiveHundredItems()
    {
        using var connection = OpenDatabase();
        for (var index = 0; index < 505; index++)
            Record(connection, "local", $"plik-{index}");

        var entries = Read(connection, "local");
        Assert.True(entries.Count == 500, "historia sesji ma najwyżej 500 pozycji");
        Assert.Equal("plik-504", entries[0], "najnowszy plik jest pierwszy");
        Assert.Equal("plik-5", entries[^1], "obcinany jest najstarszy ogon");
    }

    private static SqliteConnection OpenDatabase()
    {
        var connection = new SqliteConnection("Data Source=:memory:");
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText =
            """
            CREATE TABLE playback_history (
                session_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY(session_id, ordinal)
            );
            """;
        command.ExecuteNonQuery();
        return connection;
    }

    private static void Record(
        SqliteConnection connection, string sessionId, string itemId)
    {
        using var transaction = connection.BeginTransaction();
        LitePlaybackHistoryMutation.Record(
            connection, transaction, sessionId, itemId);
        transaction.Commit();
    }

    private static List<string> Read(
        SqliteConnection connection, string sessionId)
    {
        using var command = connection.CreateCommand();
        command.CommandText =
            "SELECT item_id FROM playback_history "
            + "WHERE session_id = $session COLLATE NOCASE ORDER BY ordinal;";
        command.Parameters.AddWithValue("$session", sessionId);
        using var reader = command.ExecuteReader();
        var result = new List<string>();
        while (reader.Read()) result.Add(reader.GetString(0));
        return result;
    }
}
