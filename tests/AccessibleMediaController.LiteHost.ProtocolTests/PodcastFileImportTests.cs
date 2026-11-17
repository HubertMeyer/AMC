using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using Microsoft.Data.Sqlite;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class PodcastFileImportTests
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "amc-podcast-file-import-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "subscriptions.csv");
            File.WriteAllText(input, """
                Channel Id,Channel Url,Channel Title
                UCfirst_123,https://www.youtube.com/channel/UCfirst_123,Pierwszy kanał
                UCsecond_456,https://www.youtube.com/channel/UCsecond_456,Drugi kanał
                """);
            var database = Path.Combine(root, "podcasts.db");
            using var store = LitePodcastProgressStore.Open(database, () => false);
            using var coordinator = new LitePodcastOpmlCoordinator(store, bookmarks: null);

            var inspect = JsonDocument.Parse(JsonSerializer.Serialize(coordinator.Inspect(Args(new { path = input }))));
            var entries = inspect.RootElement.GetProperty("entries");
            Assert.True(entries.GetArrayLength() == 2,
                "podgląd CSV musi zwracać oba kanały bez zapisu do bazy");
            Assert.True(entries[0].GetProperty("sourceKind").GetString() == "youtubeChannel"
                && entries[0].GetProperty("feedUrl").GetString() == "https://www.youtube.com/channel/UCfirst_123/videos",
                "podgląd kanału musi przekazać kanoniczny adres oraz rodzaj źródła");
            Assert.True(store.GetRefreshTargets(null).Count == 0,
                "sam podgląd importu nie może modyfikować biblioteki");

            var imported = JsonDocument.Parse(JsonSerializer.Serialize(coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[] { "https://www.youtube.com/channel/UCsecond_456/videos" }
            }))));
            Assert.True(imported.RootElement.GetProperty("selected").GetInt32() == 1
                && imported.RootElement.GetProperty("imported").GetInt32() == 1
                && imported.RootElement.GetProperty("failed").GetInt32() == 0,
                "import ma zapisać wyłącznie zaznaczony kanał bez pobierania sieciowego");

            var targets = store.GetRefreshTargets(null);
            Assert.True(targets.Count == 1
                && targets[0].SourceKind == PodcastSourceKind.YouTubeChannel
                && targets[0].Title == "Drugi kanał",
                "wybrany kanał musi wejść jako kanał YouTube z zachowaną nazwą");

            File.WriteAllText(input, """
                Channel Id,Channel Url,Channel Title
                UCsecond_456,https://www.youtube.com/channel/UCsecond_456,Zmieniona nazwa
                """);
            coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[] { "https://www.youtube.com/channel/UCsecond_456/videos" }
            }));
            targets = store.GetRefreshTargets(null);
            Assert.True(targets.Count == 1 && targets[0].Title == "Drugi kanał",
                "powtórzony import nie może nadpisać istniejącej nazwy źródła");

            coordinator.Dispose();
            store.Dispose();
            ImportKeepsCaseDistinctYouTubeIdentifiers(root);
            ImportPlaceholderKeepsExistingYouTubeMetadata(root);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static JsonElement Args(object value)
    {
        using var document = JsonDocument.Parse(JsonSerializer.Serialize(value));
        return document.RootElement.Clone();
    }

    private static void ImportKeepsCaseDistinctYouTubeIdentifiers(string root)
    {
        const string upperId = "UCcase_Abc123";
        const string lowerId = "UCcase_aBc123";
        var input = Path.Combine(root, "case-sensitive-subscriptions.csv");
        var database = Path.Combine(root, "case-sensitive-podcasts.db");
        File.WriteAllText(input, $$"""
            Channel Id,Channel Url,Channel Title
            {{upperId}},https://www.youtube.com/channel/{{upperId}},Kanał wielkie A
            {{lowerId}},https://www.youtube.com/channel/{{lowerId}},Kanał małe a
            """);

        using (var store = LitePodcastProgressStore.Open(database, () => false))
        using (var coordinator = new LitePodcastOpmlCoordinator(store, bookmarks: null))
        {
            var preview = JsonDocument.Parse(JsonSerializer.Serialize(coordinator.Inspect(Args(new { path = input }))));
            Assert.True(preview.RootElement.GetProperty("count").GetInt32() == 2,
                "podgląd musi zachować dwa różniące się wielkością liter identyfikatory YouTube");

            var selectedUrl = $"https://www.youtube.com/channel/{upperId}/videos";
            var selected = JsonDocument.Parse(JsonSerializer.Serialize(coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[] { selectedUrl }
            }))));
            Assert.True(selected.RootElement.GetProperty("selected").GetInt32() == 1
                && selected.RootElement.GetProperty("imported").GetInt32() == 1,
                "wybór jednego kanału nie może zaimportować kanału o identyfikatorze różniącym się tylko wielkością liter");
        }

        using (var reopened = LitePodcastProgressStore.Open(database, () => false))
        {
            var targets = reopened.GetRefreshTargets(null);
            Assert.True(targets.Count == 1
                && targets[0].SubscriptionId == "youtube-channel:" + upperId
                && targets[0].FeedUrl == $"https://www.youtube.com/channel/{upperId}/videos",
                "po restarcie pozostaje trwała, rozróżniająca wielkość liter tożsamość wybranego kanału");
            Assert.True(ReadSubscription(database, "youtube-channel:" + upperId).IsInLibrary,
                "wybrany kanał pozostaje członkiem Biblioteki");
        }

        File.WriteAllText(input, $$"""
            Channel Id,Channel Url,Channel Title
            {{upperId}},https://www.youtube.com/channel/{{upperId}},Nie nadpisuj pierwszego
            {{lowerId}},https://www.youtube.com/channel/{{lowerId}},Kanał małe a
            """);
        using (var store = LitePodcastProgressStore.Open(database, () => false))
        using (var coordinator = new LitePodcastOpmlCoordinator(store, bookmarks: null))
        {
            coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[] { $"https://www.youtube.com/channel/{upperId}/videos" }
            }));
            var both = JsonDocument.Parse(JsonSerializer.Serialize(coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[]
                {
                    $"https://www.youtube.com/channel/{upperId}/videos",
                    $"https://www.youtube.com/channel/{lowerId}/videos"
                }
            }))));
            Assert.True(both.RootElement.GetProperty("selected").GetInt32() == 2
                && both.RootElement.GetProperty("imported").GetInt32() == 2,
                "ponowny import obu kanałów musi zachować dwa odrębne źródła");
        }

        using var finalStore = LitePodcastProgressStore.Open(database, () => false);
        var finalTargets = finalStore.GetRefreshTargets(null);
        Assert.True(finalTargets.Count == 2
            && finalTargets.Any(target => target.SubscriptionId == "youtube-channel:" + upperId
                && target.Title == "Kanał wielkie A")
            && finalTargets.Any(target => target.SubscriptionId == "youtube-channel:" + lowerId
                && target.Title == "Kanał małe a"),
            "ponowny import nie może nadpisać drugiego źródła o identyfikatorze różniącym się tylko wielkością liter");
    }

    private static void ImportPlaceholderKeepsExistingYouTubeMetadata(string root)
    {
        const string channelId = "UCmetadata_Abc";
        const string subscriptionId = "youtube-channel:" + channelId;
        const string episodeId = "youtube-episode-metadata";
        var database = Path.Combine(root, "existing-youtube-metadata.db");
        var input = Path.Combine(root, "existing-youtube-metadata.csv");
        File.WriteAllText(input, $$"""
            Channel Id,Channel Url,Channel Title
            {{channelId}},https://www.youtube.com/channel/{{channelId}},Nazwa z pliku CSV
            """);
        var originalRefresh = new DateTime(2026, 11, 17, 10, 0, 0, DateTimeKind.Utc);
        var originalFeed = new PodcastFeedDocument(
            subscriptionId,
            "Prawdziwa nazwa kanału",
            "Prawdziwy autor",
            "Prawdziwy opis",
            new Uri($"https://www.youtube.com/channel/{channelId}/videos"),
            new Uri($"https://www.youtube.com/channel/{channelId}"),
            [new PodcastFeedEpisode(
                episodeId,
                "trwały-identyfikator-odcinka",
                "Prawdziwy materiał",
                "Autor materiału",
                "Opis materiału",
                new DateTimeOffset(originalRefresh),
                TimeSpan.FromMinutes(7),
                new Uri("https://media.example.test/youtube-metadata.m4a"),
                null,
                "audio/mp4",
                123)]);

        using (var store = LitePodcastProgressStore.Open(database, () => false))
            store.AddSource(originalFeed, null, PodcastSourceKind.YouTubeChannel);
        var originalSavedSubscription = ReadSubscription(database, subscriptionId);
        SetEpisodeFlags(database, episodeId);

        using (var store = LitePodcastProgressStore.Open(database, () => false))
        using (var coordinator = new LitePodcastOpmlCoordinator(store, bookmarks: null))
        {
            coordinator.Import(Args(new
            {
                path = input,
                feedUrls = new[] { $"https://www.youtube.com/channel/{channelId}/videos" }
            }));
        }

        var saved = ReadSubscription(database, subscriptionId);
        var episode = ReadEpisode(database, episodeId);
        Assert.True(!saved.HasCustomTitle
            && saved.IsInLibrary
            && saved.Title == "Prawdziwa nazwa kanału"
            && saved.Author == "Prawdziwy autor"
            && saved.Description == "Prawdziwy opis"
            && saved.HomepageUrl == $"https://www.youtube.com/channel/{channelId}"
            && saved.LastRefreshUtcTicks == originalSavedSubscription.LastRefreshUtcTicks,
            "zastępczy import YouTube nie może nadpisać rzeczywistych metadanych źródła bez własnej nazwy");
        Assert.True(episode.Title == "Prawdziwy materiał"
            && episode.IsPlayed
            && episode.IsFavorite
            && !episode.IsNew
            && episode.ResumePositionTicks == TimeSpan.FromMinutes(3).Ticks,
            "zastępczy import YouTube nie może zmienić danych ani flag istniejącego odcinka");

        var refreshedFeed = originalFeed with
        {
            Title = "Nazwa z prawdziwego odświeżenia",
            Author = "Autor po odświeżeniu",
            Description = "Opis po odświeżeniu"
        };
        using (var store = LitePodcastProgressStore.Open(database, () => false))
            store.ApplyRefresh(subscriptionId, refreshedFeed);
        var refreshed = ReadSubscription(database, subscriptionId);
        Assert.True(refreshed.Title == "Nazwa z prawdziwego odświeżenia"
            && refreshed.Author == "Autor po odświeżeniu"
            && refreshed.Description == "Opis po odświeżeniu"
            && refreshed.LastRefreshUtcTicks > originalSavedSubscription.LastRefreshUtcTicks,
            "zwykłe odświeżenie źródła nadal musi aktualizować rzeczywiste metadane");
    }

    private static PodcastSubscriptionSettings ReadSubscription(string database, string id) =>
        ReadPayload<PodcastSubscriptionSettings>(database, "podcast_subscriptions", id);

    private static PodcastEpisodeSettings ReadEpisode(string database, string id) =>
        ReadPayload<PodcastEpisodeSettings>(database, "podcast_episodes", id);

    private static T ReadPayload<T>(string database, string table, string id)
    {
        using var connection = new SqliteConnection($"Data Source={database};Pooling=False");
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText = $"SELECT payload_json FROM {table} WHERE id = $id;";
        command.Parameters.AddWithValue("$id", id);
        return JsonSerializer.Deserialize<T>(Convert.ToString(command.ExecuteScalar())!)!;
    }

    private static void SetEpisodeFlags(string database, string episodeId)
    {
        var episode = ReadEpisode(database, episodeId);
        episode.IsNew = false;
        episode.IsPlayed = true;
        episode.IsFavorite = true;
        episode.ResumePositionTicks = TimeSpan.FromMinutes(3).Ticks;
        using var connection = new SqliteConnection($"Data Source={database};Pooling=False");
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText = """
            UPDATE podcast_episodes
            SET is_new = 0, is_played = 1, is_favorite = 1, payload_json = $payload
            WHERE id = $id;
            """;
        command.Parameters.AddWithValue("$id", episodeId);
        command.Parameters.AddWithValue("$payload", JsonSerializer.Serialize(episode));
        command.ExecuteNonQuery();
    }
}
