using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Windows;
using AccessibleMediaController.Windows.Services;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

internal static class PlayerAccessibilityTests
{
    public static void Run()
    {
        Assert(
            MainWindow.FormatPlaybackRateDescription(1d).EndsWith(
                "normalna prędkość",
                StringComparison.Ordinal),
            "Prędkość 1,00 razy nie jest opisana jako normalna.");
        Assert(
            MainWindow.FormatPlaybackRateDescription(0.75d).EndsWith(
                "wolniej niż normalnie",
                StringComparison.Ordinal),
            "Prędkość poniżej 1,00 razy nie jest opisana jako wolniejsza.");
        Assert(
            MainWindow.FormatPlaybackRateDescription(1.25d).EndsWith(
                "szybciej niż normalnie",
                StringComparison.Ordinal),
            "Prędkość powyżej 1,00 razy nie jest opisana jako szybsza.");
        Assert(MainWindow.FormatPlayerVolumeText(100) == "Głośność: 100%",
            "Głośność 100 nie ma jednostki procentowej.");

        var bootstrap = HeadlessPlaybackWebViewPolicy.AccessibilityBootstrapScript;
        foreach (var required in new[]
                 {
                     "aria-hidden",
                     "tabindex",
                     "HTMLMediaElement",
                     "MutationObserver",
                     "focusin",
                     "iframe"
                 })
        {
            Assert(bootstrap.Contains(required, StringComparison.Ordinal),
                $"Polityka ukrytego silnika odtwarzania nie zawiera zabezpieczenia: {required}.");
        }

        Exception? failure = null;
        var thread = new Thread(() =>
        {
            var temporaryDirectory = Path.Combine(
                Path.GetTempPath(),
                "amc-player-accessibility-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporaryDirectory);
            MainWindow? window = null;
            try
            {
                var store = new ConfigurationStore(Path.Combine(temporaryDirectory, "state.json"));
                window = new MainWindow(store.LoadOrCreate(), store)
                {
                    SuppressDesktopIntegrationForTests = true
                };

                Assert(
                    KeyboardNavigation.GetTabNavigation(window.PlayerPanel)
                    == KeyboardNavigationMode.Cycle,
                    "Tab może opuścić kontrolki widocznego odtwarzacza i wejść do ukrytego silnika.");
                AssertHeadless(window.TidalPlayerWebView, "TIDAL");
                AssertHeadless(window.SpotifyPlayerWebView, "Spotify");
                Assert(!Descendants(window.PlayerPanel).OfType<ComboBox>().Any(),
                    "Widok odtwarzacza wystawia nieopisane pole kombi.");

                window.UpdatePlayerVolumePresentation(100);
                Assert(window.PlayerVolumeText.Text == "Głośność: 100%",
                    "Widoczny stan głośności nie wyjaśnia wartości 100.");
                Assert(AutomationProperties.GetName(window.PlayerVolumeText)
                       == "Głośność: 100 procent",
                    "NVDA nie otrzymuje jednostki dla bieżącej głośności.");
                Assert(AutomationProperties.GetName(window.PlayerVolumeDownButton).Contains(
                           "obecna głośność 100 procent",
                           StringComparison.Ordinal)
                       && AutomationProperties.GetName(window.PlayerVolumeUpButton).Contains(
                           "obecna głośność 100 procent",
                           StringComparison.Ordinal),
                    "Przyciski głośności nie podają aktualnej wartości i działania.");
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                window?.Close();
                try
                {
                    Directory.Delete(temporaryDirectory, recursive: true);
                }
                catch
                {
                    // Katalog testowy nie wpływa na wynik kontroli dostępności.
                }
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        if (failure is not null)
            throw new InvalidOperationException("Test dostępności odtwarzacza nie powiódł się.", failure);

        RunRealTidalEngineProbe();

        Console.WriteLine(
            "OK: ukryte silniki nie wchodzą do Tab/NVDA, a głośność i prędkość mają jednoznaczne etykiety");
    }

    private static void RunRealTidalEngineProbe()
    {
        TidalWebViewSmokeTests.RunOnSta(async () =>
        {
            var profile = Directory.CreateTempSubdirectory("amc-player-accessibility-webview-").FullName;
            var view = new WebView2 { Focusable = false, IsHitTestVisible = false };
            var window = new Window
            {
                Content = view,
                Width = 1,
                Height = 1,
                Left = -20000,
                Top = -20000,
                ShowActivated = false,
                ShowInTaskbar = false,
                WindowStyle = WindowStyle.None,
                Title = "AMC — test ukrytego silnika TIDAL"
            };
            try
            {
                window.Show();
                var environment = await CoreWebView2Environment.CreateAsync(
                    userDataFolder: profile,
                    options: TidalWebViewPolicy.CreateOptions());
                await view.EnsureCoreWebView2Async(environment);
                await HeadlessPlaybackWebViewPolicy.ApplyAsync(view.CoreWebView2);

                var assets = Path.Combine(AppContext.BaseDirectory, "tidal-player");
                Assert(File.Exists(Path.Combine(assets, "index.html"))
                       && File.Exists(Path.Combine(assets, "tidal-player.js")),
                    "W wyniku testowym brakuje lokalnych plików silnika TIDAL.");
                view.CoreWebView2.SetVirtualHostNameToFolderMapping(
                    "dev.tidal.com",
                    assets,
                    CoreWebView2HostResourceAccessKind.DenyCors);
                var navigation = new TaskCompletionSource<bool>(
                    TaskCreationOptions.RunContinuationsAsynchronously);
                view.CoreWebView2.NavigationCompleted += (_, e) =>
                    navigation.TrySetResult(e.IsSuccess);
                view.CoreWebView2.Navigate("https://dev.tidal.com:5173/index.html");
                Assert(await navigation.Task.WaitAsync(TimeSpan.FromSeconds(15)),
                    "Lokalny dokument silnika TIDAL nie został wczytany.");

                var videoCount = 0;
                for (var attempt = 0; attempt < 100 && videoCount < 2; attempt++)
                {
                    var countJson = await view.ExecuteScriptAsync(
                        "document.querySelectorAll('video').length");
                    _ = int.TryParse(countJson, out videoCount);
                    if (videoCount < 2) await Task.Delay(100);
                }
                Assert(videoCount >= 2,
                    "Rzeczywisty silnik TIDAL nie utworzył dwóch elementów odtwarzania bez przerw.");

                await view.ExecuteScriptAsync("""
                    (() => {
                      const probe = document.createElement('select');
                      probe.id = 'amc-accessibility-probe';
                      probe.innerHTML = '<option>100</option><option>200</option>';
                      document.body.appendChild(probe);
                      probe.focus();
                    })();
                    """);
                await Task.Delay(100);
                var resultJson = await view.ExecuteScriptAsync("""
                    (() => {
                      const videos = [...document.querySelectorAll('video')];
                      const probe = document.getElementById('amc-accessibility-probe');
                      return {
                        rootHidden: document.documentElement.getAttribute('aria-hidden'),
                        videoIds: videos.map(video => video.id),
                        videosHidden: videos.every(video => video.getAttribute('aria-hidden') === 'true'),
                        videosOutOfTab: videos.every(video => video.tabIndex === -1),
                        controlsHidden: videos.every(video => video.controls === false),
                        probeHidden: probe.getAttribute('aria-hidden'),
                        probeTabIndex: probe.tabIndex,
                        probeFocused: document.activeElement === probe
                      };
                    })();
                    """);
                using var result = JsonDocument.Parse(resultJson);
                var root = result.RootElement;
                var videoIds = root.GetProperty("videoIds")
                    .EnumerateArray()
                    .Select(value => value.GetString())
                    .ToArray();
                Assert(root.GetProperty("rootHidden").GetString() == "true",
                    "Dokument ukrytego silnika nadal jest widoczny dla UI Automation.");
                Assert(videoIds.Contains("video-one", StringComparer.Ordinal)
                       && videoIds.Contains("video-two", StringComparer.Ordinal),
                    "Test nie objął obu wewnętrznych elementów video-one i video-two biblioteki TIDAL.");
                Assert(root.GetProperty("videosHidden").GetBoolean()
                       && root.GetProperty("videosOutOfTab").GetBoolean()
                       && root.GetProperty("controlsHidden").GetBoolean(),
                    "Wewnętrzne elementy multimedialne TIDAL są nadal fokusowalne lub widoczne dla NVDA.");
                Assert(root.GetProperty("probeHidden").GetString() == "true"
                       && root.GetProperty("probeTabIndex").GetInt32() == -1
                       && !root.GetProperty("probeFocused").GetBoolean(),
                    "Element dodany później przez bibliotekę może wejść do Tab albo przejąć fokus: "
                    + $"aria-hidden={root.GetProperty("probeHidden")}, "
                    + $"tabIndex={root.GetProperty("probeTabIndex")}, "
                    + $"focused={root.GetProperty("probeFocused")}.");
            }
            finally
            {
                view.Dispose();
                window.Close();
                try
                {
                    Directory.Delete(profile, recursive: true);
                }
                catch
                {
                    // Prywatny profil WebView2 bywa zwalniany chwilę po teście.
                }
            }
        });
    }

    private static void AssertHeadless(FrameworkElement webView, string name)
    {
        Assert(!webView.Focusable, $"Ukryty silnik {name} jest fokusowalny.");
        Assert(!KeyboardNavigation.GetIsTabStop(webView),
            $"Ukryty silnik {name} wchodzi do kolejności Tab.");
        Assert(string.IsNullOrEmpty(AutomationProperties.GetName(webView)),
            $"Ukryty silnik {name} ma nazwę odczytywaną przez NVDA.");
    }

    private static IEnumerable<DependencyObject> Descendants(DependencyObject parent)
    {
        foreach (var child in LogicalTreeHelper.GetChildren(parent).OfType<DependencyObject>())
        {
            yield return child;
            foreach (var descendant in Descendants(child)) yield return descendant;
        }
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
