using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class FacebookPageTests
{
    private static readonly Uri Page = new("https://www.facebook.com/buremisie/");

    public static void Run()
    {
        Assert.True(FacebookPublicPageClient.TryNormalizePageAddress(
                new Uri("http://www.facebook.com/buremisie"), out var normalized)
            && normalized == Page,
            "adres strony normalizuje się bez danych logowania");
        Assert.True(!FacebookPublicPageClient.TryNormalizePageAddress(
                new Uri("https://www.facebook.com/buremisie/videos/123456789/"), out _)
            && !FacebookPublicPageClient.TryNormalizePageAddress(
                new Uri("https://www.facebook.com.evil.example/buremisie/"), out _),
            "film i obca domena nie są stronami do śledzenia");

        const string response = """
            {"data":{"node":{"timeline_list_feed_units":{"edges":[{"node":{"creation_time":1792915190,"actors":[{"name":"Wspólnota Burego Misia"}],"comet_sections":{"content":{"story":{"message":{"text":"Dłuższy film ze wspólnoty"},"attachments":[{"media":{"__typename":"Video","id":"4170870626378494"}}]}}}}},{"node":{"creation_time":1792915180,"actors":[{"name":"Wspólnota Burego Misia"}],"comet_sections":{"content":{"story":{"attachments":[{"media":{"__typename":"Photo","id":"987654321"}}]}}}}}]}}}}
            """;
        var feed = FacebookPublicPageClient.ParseResponse(response, Page, "100064737484510");
        Assert.True(feed.Episodes.Count == 1
            && feed.Episodes[0].Title == "Dłuższy film ze wspólnoty"
            && feed.Episodes[0].MediaUri.AbsoluteUri
                == "https://www.facebook.com/buremisie/videos/4170870626378494/"
            && feed.Episodes[0].MediaType is null,
            "do Biblioteki trafia stabilny adres filmu, nie zdjęcie ani adres strumienia");
        Assert.True(feed.Title == "Wspólnota Burego Misia",
            "nazwa źródła jest użytkowym tekstem strony");

        var errorRaised = false;
        try
        {
            FacebookPublicPageClient.ParseResponse("{\"errors\":[{\"message\":\"blocked\"}]}", Page, "1");
        }
        catch (InvalidDataException)
        {
            errorRaised = true;
        }
        Assert.True(errorRaised, "zmiana odpowiedzi Facebooka jest błędem, a nie pustym kanałem");

        var root = Path.Combine(Path.GetTempPath(), "amc-facebook-page-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            using var store = LitePodcastProgressStore.Open(Path.Combine(root, "podcasts.db"), () => false);
            var added = store.AddSource(feed, null, PodcastSourceKind.FacebookPage);
            var targets = store.GetRefreshTargets(added.SubscriptionId);
            Assert.True(targets.Count == 1 && targets[0].SourceKind == PodcastSourceKind.FacebookPage,
                "strona jest zapisana jako osobne źródło możliwe do odświeżenia ręcznie");
            var secondPage = new Uri("https://www.facebook.com/inna.strona/");
            store.AddSource(feed with
            {
                Id = "facebook-page:999999999",
                FeedUri = secondPage,
                HomepageUri = secondPage,
                Title = "Inna strona",
                Episodes = []
            }, null, PodcastSourceKind.FacebookPage);
            Assert.True(store.GetRefreshTargets(null).Count == 2,
                "kilka stron ma osobne subskrypcje i można je sprawdzić jednym poleceniem");
            Assert.True(store.GetDueRefreshTargets().Count == 0,
                "żadna strona Facebooka nie jest sprawdzana automatycznie");
            var downloads = store.GetDownloadTargets([feed.Episodes[0].Id]);
            Assert.True(downloads.Count == 1 && downloads[0].MediaUrl == feed.Episodes[0].MediaUri.AbsoluteUri,
                "film ze strony trafia do istniejącego pobierania odcinków");
            Assert.True(PodcastDownloadNaming.SuggestedFileName(
                    downloads[0].Title, downloads[0].MediaUrl, downloads[0].MediaType)
                .EndsWith(".mp3", StringComparison.OrdinalIgnoreCase),
                "pobieranie dźwięku filmu proponuje plik MP3");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    public static void RunLive()
    {
        using var client = new FacebookPublicPageClient();
        var feed = client.FetchAsync(Page, CancellationToken.None).GetAwaiter().GetResult();
        Assert.True(feed.Title.Contains("Burego Misia", StringComparison.Ordinal)
            && feed.Episodes.Any(episode => episode.MediaUri.Host == "www.facebook.com"),
            "rzeczywista publiczna strona zwraca co najmniej jeden film");
        Console.WriteLine($"Strona: {feed.Title}; filmy: {feed.Episodes.Count}; pierwszy: {feed.Episodes[0].MediaUri}");
    }
}
