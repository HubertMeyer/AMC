using System.Text.Json;
using AccessibleMediaController.Core.Configuration;

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
}
