using System.Windows;
using System.Windows.Automation;
using System.Windows.Input;
using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows;

internal static class PlaybackShuffleUiTests
{
    public static void Run()
    {
        AssertShortcutRouting();

        Exception? failure = null;
        var thread = new Thread(() =>
        {
            var directory = Path.Combine(Path.GetTempPath(), $"amc-shuffle-ui-{Guid.NewGuid():N}");
            Directory.CreateDirectory(directory);
            MainWindow? window = null;
            try
            {
                var store = new ConfigurationStore(Path.Combine(directory, "state.json"));
                window = new MainWindow(store.LoadOrCreate(), store)
                {
                    SuppressDesktopIntegrationForTests = true
                };
                var local = new DemoMediaSession(
                    "local",
                    "Pliki lokalne",
                    [new MediaItem { Id = "local-1", Title = "Utwór" }],
                    shuffleRandom: new Random(1));

                window.UpdatePlayerShufflePresentation(local);
                Assert(window.PlayerShuffleButton.Visibility == Visibility.Visible
                       && window.PlaybackShuffleMenuItem.Visibility == Visibility.Visible
                       && window.PlayerShuffleMenuItem.Visibility == Visibility.Visible,
                    "Polecenie losowania nie jest widoczne na wszystkich powierzchniach sesji lokalnej.");
                Assert((string)window.PlayerShuffleButton.Content == "Włącz odtwarzanie losowe"
                       && (string)window.PlaybackShuffleMenuItem.Header == "Włącz odtwarzanie losowe"
                       && (string)window.PlayerShuffleMenuItem.Header == "Włącz odtwarzanie losowe",
                    "Przycisk i menu nie podają tego samego działania przed włączeniem losowania.");
                Assert(AutomationProperties.GetName(window.PlayerShuffleButton) == "Włącz odtwarzanie losowe"
                       && AutomationProperties.GetName(window.PlaybackShuffleMenuItem) == "Włącz odtwarzanie losowe"
                       && AutomationProperties.GetName(window.PlayerShuffleMenuItem) == "Włącz odtwarzanie losowe",
                    "NVDA nie otrzymuje jednej użytkowej etykiety działania losowania.");
                Assert(AutomationProperties.GetAcceleratorKey(window.PlayerShuffleButton) == "R"
                       && AutomationProperties.GetAcceleratorKey(window.PlaybackShuffleMenuItem) == "R"
                       && AutomationProperties.GetAcceleratorKey(window.PlayerShuffleMenuItem) == "R",
                    "Skrót R nie jest przekazany do UI Automation na wszystkich powierzchniach.");

                local.SetShuffleEnabled(true);
                window.UpdatePlayerShufflePresentation(local);
                Assert((string)window.PlayerShuffleButton.Content == "Wyłącz odtwarzanie losowe"
                       && window.PlaybackShuffleMenuItem.IsChecked
                       && window.PlayerShuffleMenuItem.IsChecked,
                    "Po włączeniu stan i działanie odwrotne nie są jednoznaczne.");

                var radio = new DemoMediaSession(
                    "radio",
                    "Radio internetowe",
                    [new MediaItem { Id = "radio-1", Title = "Stacja" }]);
                window.UpdatePlayerShufflePresentation(radio);
                Assert(window.PlayerShuffleButton.Visibility == Visibility.Collapsed
                       && window.PlaybackShuffleMenuItem.Visibility == Visibility.Collapsed
                       && window.PlayerShuffleMenuItem.Visibility == Visibility.Collapsed,
                    "Losowanie jest reklamowane w Radiu, gdzie R służy do nagrywania.");
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
            throw new InvalidOperationException("Test interfejsu losowania nie powiódł się.", failure);

        Console.WriteLine("OK: R i trzy dostępne powierzchnie losowania mają zgodne etykiety i stan");
    }

    private static void AssertShortcutRouting()
    {
        foreach (var sessionId in new[] { "local", "podcasts", "spotify" })
        {
            Assert(MainWindowShortcutRouter.ResolvePlayerShuffle(
                    Key.R, ModifierKeys.None, playerActive: true, sessionId)
                   == CommandIds.ToggleShuffle,
                $"R nie przełącza losowania w sesji {sessionId}.");
        }
        foreach (var sessionId in new[] { "radio", "wiim", "appleMusic", "tidal" })
        {
            Assert(MainWindowShortcutRouter.ResolvePlayerShuffle(
                    Key.R, ModifierKeys.None, playerActive: true, sessionId) is null,
                $"R został błędnie przejęty przez losowanie w sesji {sessionId}.");
        }
        Assert(MainWindowShortcutRouter.ResolvePlayerShuffle(
                Key.R, ModifierKeys.None, playerActive: false, "local") is null
               && MainWindowShortcutRouter.ResolvePlayerShuffle(
                   Key.R, ModifierKeys.Control, playerActive: true, "local") is null,
            "Losowanie przejmuje R poza odtwarzaczem albo z modyfikatorem.");
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
