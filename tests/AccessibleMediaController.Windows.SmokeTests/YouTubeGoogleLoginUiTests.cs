using System.Net;
using System.Net.Http;
using System.Reflection;
using System.Text;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Input;
using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Input;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows;
using AccessibleMediaController.Windows.Services;

internal static class YouTubeGoogleLoginUiTests
{
    private const BindingFlags InstancePrivate = BindingFlags.Instance | BindingFlags.NonPublic;
    private const string ClientId = "123456789012-abcdefghijklmnop.apps.googleusercontent.com";

    public static void Run()
    {
        AssertCredentialAndOAuthBoundary();
        AssertApiPagination();
        AssertCommandContract();
        AssertWindowContract();
        Console.WriteLine("OK: YouTube ma bezpieczne OAuth, stronicowanie API, Ctrl+F5 i etykiety NVDA");
    }

    private static void AssertCredentialAndOAuthBoundary()
    {
        Check(YouTubeGoogleCredentialStore.IsValidClientId(ClientId),
            "Poprawny publiczny Client ID Google został odrzucony.");
        Check(!YouTubeGoogleCredentialStore.IsValidClientId("sekret-klienta"),
            "Walidacja przyjęła sekret zamiast Client ID aplikacji desktopowej.");
        var uri = YouTubeGoogleOAuthClient.BuildAuthorizationUri(
            ClientId,
            new Uri("http://127.0.0.1:54321/"),
            "wyzwanie-pkce",
            "stan-testowy");
        var text = uri.AbsoluteUri;
        Check(text.StartsWith("https://accounts.google.com/o/oauth2/v2/auth", StringComparison.Ordinal)
              && text.Contains("code_challenge_method=S256", StringComparison.Ordinal)
              && text.Contains("access_type=offline", StringComparison.Ordinal)
              && text.Contains("prompt=consent", StringComparison.Ordinal)
              && text.Contains(Uri.EscapeDataString(YouTubeGoogleOAuthClient.RequestedScope), StringComparison.Ordinal)
              && !text.Contains("client_secret", StringComparison.OrdinalIgnoreCase),
            "Adres logowania nie ma PKCE/offline/read-only albo żąda sekretu klienta.");
    }

    private static void AssertApiPagination()
    {
        var requests = new List<HttpRequestMessage>();
        var handler = new StubHandler(request =>
        {
            requests.Add(CloneRequest(request));
            var path = request.RequestUri!.AbsolutePath;
            var query = request.RequestUri.Query;
            if (path.EndsWith("/channels", StringComparison.Ordinal))
                return Json("{\"items\":[{\"snippet\":{\"title\":\"Moje konto\"}}]}");
            if (path.EndsWith("/subscriptions", StringComparison.Ordinal))
            {
                return query.Contains("pageToken=druga", StringComparison.Ordinal)
                    ? Json("{\"items\":[{\"snippet\":{\"title\":\"Kanał drugi\",\"resourceId\":{\"channelId\":\"UCdrugi_123\"}}}]}" )
                    : Json("{\"nextPageToken\":\"druga\",\"items\":[{\"snippet\":{\"title\":\"Kanał pierwszy\",\"resourceId\":{\"channelId\":\"UCpierwszy_123\"}}}]}" );
            }
            if (path.EndsWith("/playlists", StringComparison.Ordinal))
                return Json("{\"items\":[{\"id\":\"PLtest_123\",\"snippet\":{\"title\":\"Moja lista\",\"channelTitle\":\"Moje konto\"},\"status\":{\"privacyStatus\":\"private\"}}]}" );
            if (path.EndsWith("/playlistItems", StringComparison.Ordinal))
            {
                return query.Contains("pageToken=film2", StringComparison.Ordinal)
                    ? Json("{\"items\":[{\"snippet\":{\"title\":\"Film drugi\",\"videoOwnerChannelTitle\":\"Autor 2\",\"publishedAt\":\"2026-10-02T10:00:00Z\"},\"contentDetails\":{\"videoId\":\"video_002\"}}]}" )
                    : Json("{\"nextPageToken\":\"film2\",\"items\":[{\"snippet\":{\"title\":\"Film pierwszy\",\"videoOwnerChannelTitle\":\"Autor 1\",\"publishedAt\":\"2026-10-01T10:00:00Z\"},\"contentDetails\":{\"videoId\":\"video_001\"}}]}" );
            }
            return new HttpResponseMessage(HttpStatusCode.NotFound);
        });

        using var http = new HttpClient(handler);
        using var api = new YouTubeDataApiClient(http);
        var account = api.GetAccountDisplayNameAsync("token-testowy", CancellationToken.None)
            .GetAwaiter().GetResult();
        var subscriptions = api.GetSubscriptionsAsync("token-testowy", CancellationToken.None)
            .GetAwaiter().GetResult();
        var playlists = api.GetPlaylistsAsync("token-testowy", CancellationToken.None)
            .GetAwaiter().GetResult();

        Check(account == "Moje konto" && subscriptions.Count == 2,
            "Klient nie odczytał konta albo wszystkich stron subskrypcji.");
        Check(playlists.Count == 1
              && playlists[0].PrivacyStatus == "private"
              && playlists[0].Videos.Count == 2,
            "Klient nie odczytał prywatnej playlisty albo wszystkich stron materiałów.");
        Check(requests.All(request =>
                request.Headers.Authorization?.Scheme == "Bearer"
                && request.Headers.Authorization.Parameter == "token-testowy"
                && !request.RequestUri!.Query.Contains("access_token", StringComparison.OrdinalIgnoreCase)
                && !request.RequestUri.Query.Contains("token-testowy", StringComparison.Ordinal)),
            "Token nie jest przekazywany wyłącznie w nagłówku Bearer.");
    }

    private static void AssertCommandContract()
    {
        Check(CommandCatalog.GetDisplayName(CommandIds.ManageYouTubeConnection)
              == "Konto YouTube i import z Google",
            "Katalog poleceń nie zawiera użytkowej nazwy konta YouTube.");
        var entries = CommandPaletteSearch.CreateEntries(
            KeyboardProfile.CreateDefault(),
            new AppSettings());
        var account = entries.Single(entry => entry.CommandId == CommandIds.ManageYouTubeConnection);
        var refresh = entries.Single(entry => entry.CommandId == CommandIds.RefreshPodcastLibrary);
        Check(account.LocalShortcut == "Ctrl+F5 (Podcasty i YouTube)"
              && refresh.LocalShortcut == "Ctrl+Windows+F5 (globalnie) lub menu Plik",
            "Paleta nie rozdziela konta YouTube od odświeżania wszystkich źródeł.");
    }

    private static void AssertWindowContract()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            var directory = Path.Combine(Path.GetTempPath(), $"amc-youtube-google-ui-{Guid.NewGuid():N}");
            Directory.CreateDirectory(directory);
            MainWindow? window = null;
            YouTubeGoogleAccountWindow? accountWindow = null;
            try
            {
                var store = new ConfigurationStore(Path.Combine(directory, "state.json"));
                window = new MainWindow(store.LoadOrCreate(), store)
                {
                    SuppressDesktopIntegrationForTests = true
                };
                var sessions = (SessionManager)typeof(MainWindow)
                    .GetField("_sessions", InstancePrivate)!
                    .GetValue(window)!;
                sessions.SelectSession("podcasts");
                typeof(MainWindow)
                    .GetMethod("UpdateFileMenuForCurrentSession", InstancePrivate)!
                    .Invoke(window, null);

                Check(window.ManageYouTubeConnectionMenuItem.Visibility == Visibility.Visible,
                    "Menu konta YouTube jest ukryte w sesji Podcasty i YouTube.");
                Check(AutomationProperties.GetName(window.ManageYouTubeConnectionMenuItem)
                      == "Konto YouTube i import z Google…"
                      && AutomationProperties.GetAcceleratorKey(window.ManageYouTubeConnectionMenuItem)
                          == "Ctrl+F5",
                    "Menu konta YouTube nie przekazuje NVDA pełnej nazwy i skrótu.");
                Check(AutomationProperties.GetAcceleratorKey(window.RefreshAllPodcastsMenuItem)
                      == "Ctrl+Windows+F5",
                    "Menu odświeżania nadal koliduje z Ctrl+F5 konta YouTube.");

                var helpArgs = new object[] { Key.F5, ModifierKeys.Control, string.Empty };
                var resolved = (bool)typeof(MainWindow)
                    .GetMethod("TryResolveKeyboardHelpCommand", InstancePrivate)!
                    .Invoke(window, helpArgs)!;
                Check(resolved && (string)helpArgs[2] == CommandIds.ManageYouTubeConnection,
                    "Pomoc klawiatury nie mapuje Ctrl+F5 na konto YouTube.");
                var visible = (bool)typeof(MainWindow)
                    .GetMethod("CommandVisibleInPalette", InstancePrivate)!
                    .Invoke(window, [CommandIds.ManageYouTubeConnection])!;
                Check(visible, "Paleta ukrywa konto YouTube w jego sesji.");

                using var integration = new YouTubeGoogleIntegrationService();
                accountWindow = new YouTubeGoogleAccountWindow(
                    integration,
                    (_, _) => Task.FromResult(new YouTubeGoogleImportSummary(0, 0, 0, 0)));
                Check(AutomationProperties.GetName(accountWindow.ClientIdBox)
                          .Contains("Aplikacja na komputer", StringComparison.Ordinal)
                      && AutomationProperties.GetName(accountWindow.ImportButton)
                          == "Importuj subskrybowane kanały i własne playlisty YouTube"
                      && !AutomationProperties.GetName(accountWindow.ClientIdBox)
                          .Contains("TextBox", StringComparison.Ordinal),
                    "Okno konta ujawnia nazwę techniczną albo ma niepełne etykiety NVDA.");
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                accountWindow?.Close();
                window?.Close();
                try { Directory.Delete(directory, recursive: true); }
                catch { }
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure is not null)
            throw new InvalidOperationException("Test logowania Google/YouTube nie powiódł się.", failure);
    }

    private static HttpResponseMessage Json(string content) => new(HttpStatusCode.OK)
    {
        Content = new StringContent(content, Encoding.UTF8, "application/json")
    };

    private static HttpRequestMessage CloneRequest(HttpRequestMessage request)
    {
        var clone = new HttpRequestMessage(request.Method, request.RequestUri);
        clone.Headers.Authorization = request.Headers.Authorization;
        return clone;
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed class StubHandler(Func<HttpRequestMessage, HttpResponseMessage> responder)
        : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken) => Task.FromResult(responder(request));
    }
}
