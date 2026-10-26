using System.Reflection;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Threading;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows;

internal static class ActiveRecordingArrowTests
{
    private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;

    internal static void Run()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            var root = Path.Combine(Path.GetTempPath(), "amc-active-recording-arrows-" + Guid.NewGuid().ToString("N"));
            MainWindow? window = null;
            HwndSource? inputSource = null;
            try
            {
                SynchronizationContext.SetSynchronizationContext(new DispatcherSynchronizationContext());
                var store = new ConfigurationStore(Path.Combine(root, "state.json"));
                var state = store.LoadOrCreate();
                state.Settings.Updates.CheckAutomatically = false;
                state.Settings.Updates.InstallOnExit = false;
                state.Settings.LastSessionId = "radio";
                state.Tidal.ClientId = state.Spotify.ClientId = string.Empty;
                state.Tidal.CachedCollectionItems.Clear();
                state.Spotify.CachedCollectionItems.Clear();
                state.Podcasts.Subscriptions.Clear();
                state.Podcasts.Episodes.Clear();
                state.LocalMedia.Items.Clear();
                state.LocalMedia.FolderSources.Clear();
                state.WiiM.Devices.Clear();
                state.Radio.Stations.Clear();
                state.Radio.RecordingSchedules.Clear();
                state.Radio.WakeScheduledRecordings = false;
                state.Radio.RecordingsFolder = Path.Combine(root, "Nagrania");
                store.Save(state);

                window = new MainWindow(store.LoadOrCreate(), store)
                {
                    SuppressDesktopIntegrationForTests = true,
                    ShowInTaskbar = false
                };
                window.Show();
                Pump();

                var station = new MediaItem
                {
                    Id = "station-test",
                    Title = "Stacja próby",
                    Kind = MediaItemKind.Station,
                    Source = "https://example.invalid/live",
                    Codec = "AAC",
                    BitrateKbps = 128
                };
                var rowType = typeof(MainWindow).GetNestedType("MediaItemRow", BindingFlags.NonPublic)!;
                var constructor = rowType.GetConstructors(
                    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).Single();
                var row = constructor.Invoke(
                [
                    station,
                    "Nagrywane, audycja.mp3",
                    "Stacja próby",
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    "192 kb/s, plik audycja.mp3, folder domyślny"
                ]);
                var rows = Array.CreateInstance(rowType, 1);
                rows.SetValue(row, 0);
                window.MediaList.ItemsSource = rows;
                window.MediaList.SelectedIndex = 0;
                var sessions = (SessionManager)typeof(MainWindow).GetField("_sessions", Private)!.GetValue(window)!;
                sessions.SelectSession("radio");
                typeof(MainWindow).GetField("_currentView", Private)!.SetValue(window, "Nagrywane");
                typeof(MainWindow).GetField("_captureAnnouncements", Private)!.SetValue(window, true);
                window.MediaList.Focus();
                Keyboard.Focus(window.MediaList);

                inputSource = new HwndSource(new HwndSourceParameters("AMC active recording arrow test")
                {
                    Width = 1,
                    Height = 1,
                    WindowStyle = unchecked((int)0x80000000)
                });
                Send(window, inputSource, Key.Right);
                var spoken = (string?)typeof(MainWindow).GetField("_capturedAnnouncement", Private)!.GetValue(window)
                    ?? string.Empty;
                Check(spoken == "192 kb/s, plik audycja.mp3, folder domyślny",
                    "Prawa strzałka podała inny komunikat: " + spoken);

                Send(window, inputSource, Key.Left);
                spoken = (string?)typeof(MainWindow).GetField("_capturedAnnouncement", Private)!.GetValue(window)
                    ?? string.Empty;
                Check(spoken.Contains("AAC", StringComparison.OrdinalIgnoreCase)
                      && spoken.Contains("128", StringComparison.Ordinal),
                    "Lewa strzałka przestała podawać parametry strumienia: " + spoken);
                Check(!spoken.Contains("192", StringComparison.Ordinal)
                      && !spoken.Contains("folder domyślny", StringComparison.OrdinalIgnoreCase),
                    "Lewa strzałka pomieszała strumień z ustawieniami zapisu: " + spoken);
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                inputSource?.Dispose();
                window?.Close();
                Dispatcher.CurrentDispatcher.InvokeShutdown();
                try { Directory.Delete(root, true); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }) { IsBackground = true };
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        if (!thread.Join(TimeSpan.FromSeconds(30))) failure = new Exception("Timeout testu strzałek nagrywania");
        if (failure is not null) throw failure;
        Console.WriteLine("OK: lewa strzałka czyta strumień, prawa ustawienia zapisu aktywnego nagrania");
    }

    private static void Send(MainWindow window, PresentationSource inputSource, Key key)
    {
        var args = new KeyEventArgs(Keyboard.PrimaryDevice, inputSource, Environment.TickCount, key)
        {
            RoutedEvent = Keyboard.PreviewKeyDownEvent,
            Source = window.MediaList
        };
        typeof(MainWindow).GetMethod("MediaList_PreviewKeyDown", Private)!
            .Invoke(window, [window.MediaList, args]);
        Check(args.Handled, $"Klawisz {key} nie został obsłużony na liście Nagrywane.");
        Pump();
    }

    private static void Pump() =>
        Dispatcher.CurrentDispatcher.Invoke(() => { }, DispatcherPriority.ContextIdle);

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
