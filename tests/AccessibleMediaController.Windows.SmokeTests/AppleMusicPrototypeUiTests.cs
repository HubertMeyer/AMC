using System.Reflection;
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

internal static class AppleMusicPrototypeUiTests
{
    private const BindingFlags InstancePrivate =
        BindingFlags.Instance | BindingFlags.NonPublic;

    public static void Run()
    {
        AssertCredentialBoundary();
        AssertPlaybackBoundary();
        AssertCommandContract();
        AssertPackagedBridge();
        AssertWindowContract();
        Console.WriteLine(
            "OK: Apple Music ma bezpieczny token, spójne Ctrl+F5, ukryty silnik i dostępne etykiety");
    }

    private static void AssertCredentialBoundary()
    {
        Check(AppleMusicCredentialStore.IsDeveloperToken("naglowek.dane.podpis"),
            "Poprawny kształt JWT został odrzucony.");
        const string privateKeyMarker = "-----BEGIN" + " PRIVATE KEY-----";
        Check(!AppleMusicCredentialStore.IsDeveloperToken(privateKeyMarker),
            "Magazyn zaakceptował prywatny klucz zamiast gotowego JWT.");
        Check(AppleMusicCredentialStore.IsStorefront("pl")
              && !AppleMusicCredentialStore.IsStorefront("pol"),
            "Walidacja katalogu kraju nie wymusza dwóch liter.");
    }

    private static void AssertPlaybackBoundary()
    {
        var song = new MediaItem
        {
            Id = "apple-song", Title = "Utwór", Kind = MediaItemKind.Track,
            ExternalId = "songs:123"
        };
        Check(AppleMusicMediaOutput.TryPlaybackResource(song, out var songType, out var songId)
              && songType == "songs" && songId == "123",
            "Silnik nie rozpoznaje utworu Apple Music.");
        var video = new MediaItem
        {
            Id = "apple-video", Title = "Teledysk", Kind = MediaItemKind.Video,
            ExternalId = "music-videos:456"
        };
        Check(AppleMusicMediaOutput.TryPlaybackResource(video, out _, out _),
            "Silnik nie rozpoznaje teledysku Apple Music.");
        var album = new MediaItem
        {
            Id = "apple-album", Title = "Album", Kind = MediaItemKind.Album,
            ExternalId = "albums:789"
        };
        Check(!AppleMusicMediaOutput.TryPlaybackResource(album, out _, out _),
            "Silnik próbuje odtwarzać kontener zamiast otworzyć jego zawartość.");

        var tokenFailure = AppleMusicMediaOutput.FriendlyFailure(
            "authorize failed for token sekret.abc.xyz");
        Check(tokenFailure.Contains("Ctrl+F5", StringComparison.Ordinal)
              && !tokenFailure.Contains("sekret", StringComparison.Ordinal),
            "Komunikat błędu ujawnia token albo nie prowadzi do konta.");
        var urlFailure = AppleMusicMediaOutput.FriendlyFailure(
            "failed at https://music.example/private");
        Check(!urlFailure.Contains("https://", StringComparison.Ordinal),
            "Komunikat błędu ujawnia techniczny adres usługi.");
    }

    private static void AssertCommandContract()
    {
        Check(CommandCatalog.GetDisplayName(CommandIds.ManageAppleMusicConnection)
              == "Konto Apple Music",
            "Katalog poleceń nie zawiera użytkowej nazwy konta Apple Music.");
        var entries = CommandPaletteSearch.CreateEntries(
            KeyboardProfile.CreateDefault(),
            new AppSettings());
        var account = entries.Single(entry =>
            entry.CommandId == CommandIds.ManageAppleMusicConnection);
        Check(account.LocalShortcut == "Ctrl+F5 (Apple Music)"
              && account.Label.Contains("Konto Apple Music", StringComparison.Ordinal),
            "Paleta nie podaje nazwy i kontekstowego skrótu Apple Music.");
        Check(MainWindow.SessionHasRemoteSearch("appleMusic", allServices: false)
              && MainWindow.RemoteSearchLabel("appleMusic", allServices: false)
                  == "katalogu Apple Music",
            "Ctrl+F nie opisuje katalogu Apple Music.");
    }

    private static void AssertPackagedBridge()
    {
        var folder = Path.Combine(AppContext.BaseDirectory, "apple-music-player");
        var index = Path.Combine(folder, "index.html");
        var bridge = Path.Combine(folder, "bridge.js");
        Check(File.Exists(index) && File.Exists(bridge),
            "Kompilacja nie zawiera składników MusicKit.");
        var html = File.ReadAllText(index);
        var script = File.ReadAllText(bridge);
        Check(html.Contains("https://js-cdn.music.apple.com/musickit/v3/musickit.js",
                  StringComparison.Ordinal)
              && script.Contains("music.authorize()", StringComparison.Ordinal)
              && script.Contains("music.setQueue", StringComparison.Ordinal),
            "Mostek nie używa oficjalnego MusicKit do logowania i kolejki.");
    }

    private static void AssertWindowContract()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            var directory = Path.Combine(
                Path.GetTempPath(),
                $"amc-apple-music-ui-{Guid.NewGuid():N}");
            Directory.CreateDirectory(directory);
            MainWindow? window = null;
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
                sessions.SelectSession("appleMusic");
                typeof(MainWindow)
                    .GetMethod("UpdateFileMenuForCurrentSession", InstancePrivate)!
                    .Invoke(window, null);

                Check(window.ManageAppleMusicConnectionMenuItem.Visibility == Visibility.Visible,
                    "Menu konta jest ukryte w sesji Apple Music.");
                Check(AutomationProperties.GetName(window.ManageAppleMusicConnectionMenuItem)
                      == "Konto Apple Music…"
                      && AutomationProperties.GetAcceleratorKey(
                          window.ManageAppleMusicConnectionMenuItem) == "Ctrl+F5",
                    "Menu nie przekazuje NVDA nazwy i skrótu konta Apple Music.");
                Check(!window.AppleMusicPlayerWebView.Focusable
                      && !window.AppleMusicPlayerWebView.IsHitTestVisible
                      && AutomationProperties.GetName(window.AppleMusicPlayerWebView) == string.Empty,
                    "Ukryty silnik MusicKit trafia do fokusu albo drzewa NVDA.");

                var helpArgs = new object[] { Key.F5, ModifierKeys.Control, string.Empty };
                var resolved = (bool)typeof(MainWindow)
                    .GetMethod("TryResolveKeyboardHelpCommand", InstancePrivate)!
                    .Invoke(window, helpArgs)!;
                Check(resolved
                      && (string)helpArgs[2] == CommandIds.ManageAppleMusicConnection,
                    "Pomoc klawiatury nie mapuje Ctrl+F5 na konto Apple Music.");
                var visible = (bool)typeof(MainWindow)
                    .GetMethod("CommandVisibleInPalette", InstancePrivate)!
                    .Invoke(window, [CommandIds.ManageAppleMusicConnection])!;
                Check(visible, "Paleta ukrywa konto w sesji Apple Music.");
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                window?.Close();
                try { Directory.Delete(directory, recursive: true); }
                catch { }
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure is not null)
            throw new InvalidOperationException(
                "Test interfejsu prototypu Apple Music nie powiódł się.",
                failure);
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
