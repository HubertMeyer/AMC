using System.Net.Http;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Devices.FrontierSmart;
using AccessibleMediaController.Core.Input;
using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows;

namespace AccessibleMediaController.FrontierSmart.Windows.SmokeTests;

internal static class Program
{
    [STAThread]
    public static int Main()
    {
        var tests = new (string Name, Action Run)[]
        {
            ("wspólny katalog komend", TestCommandSurfaces),
            ("dynamiczna sesja i slot", TestDynamicSession),
            ("etykiety wierszy", TestUserFacingLabels),
            ("fokus Menedżera sesji po ponownym otwarciu", TestSessionManagerFocus),
            ("automatyczne wykrywanie i fokus kreatora", TestDeviceWindowFocus),
            ("fokus listy trybów i presetów", TestChoiceWindowFocus)
        };
        var application = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        var failures = 0;
        foreach (var (name, run) in tests)
        {
            try
            {
                run();
                Console.WriteLine($"OK: {name}");
            }
            catch (Exception exception)
            {
                failures++;
                Console.Error.WriteLine($"BŁĄD: {name}: {exception.GetType().Name}: {exception.Message}");
            }
        }
        application.Shutdown();
        Console.WriteLine($"Frontier Smart Windows: {tests.Length - failures}/{tests.Length} testów zaliczonych.");
        return failures == 0 ? 0 : 1;
    }

    private static void TestCommandSurfaces()
    {
        Equal("Menedżer sesji", CommandCatalog.GetDisplayName(CommandIds.SessionList));
        Equal("Urządzenia Frontier Smart", CommandCatalog.GetDisplayName(CommandIds.ManageFrontierSmartDevices));
        var entries = CommandPaletteSearch.CreateEntries(
            KeyboardProfile.CreateDefault(),
            new AppSettings(),
            includeCommandPalette: true);
        Equal("Ctrl+F5 (Frontier Smart)", Entry(CommandIds.ManageFrontierSmartDevices).LocalShortcut);
        Equal("F5 (Frontier Smart)", Entry(CommandIds.RefreshFrontierSmartDevices).LocalShortcut);
        Equal("Ctrl+Alt+P (Frontier Smart)", Entry(CommandIds.ViewFrontierSmartPresets).LocalShortcut);
        True(entries.Any(entry => entry.CommandId == CommandIds.ViewFrontierSmartModes));
        return;

        CommandPaletteEntry Entry(string id) => entries.Single(entry => entry.CommandId == id);
    }

    private static void TestDynamicSession()
    {
        var settings = new AppSettings();
        var manager = new SessionManager(settings);
        var item = new MediaItem { Id = "radio-test", Title = "Radio testowe", Kind = MediaItemKind.Device };
        var (session, slot) = manager.AddOrUpdateTransientSession(
            "frontierSmart",
            "Frontier Smart",
            [item],
            output: null,
            preferredSlot: 9);
        Equal("Frontier Smart", session.DisplayName);
        Equal(9, slot);
        Equal("frontierSmart", settings.SessionSlots[9]);
        Equal("Frontier Smart", SessionSlotOrder.GetDisplayName("frontierSmart"));
    }

    private static void TestUserFacingLabels()
    {
        var device = new FrontierSmartDeviceSettings
        {
            Id = "opaque-id",
            Address = "192.168.1.25",
            DisplayName = "Radio w kuchni"
        };
        var row = new FrontierSmartDeviceRow(device, null, null, true);
        Equal("Radio w kuchni, aktywne, zapisane, stan jeszcze nieodświeżony", row.ToString());
        False(row.ToString().Contains(nameof(FrontierSmartDeviceSettings), StringComparison.Ordinal));
        var choice = new FrontierSmartChoiceRow(0, "Radio internetowe", "Radio internetowe");
        Equal("Radio internetowe", choice.ToString());
        var sessionRow = new SessionSelectionWindow.SessionRow(9, "frontierSmart", "Frontier Smart");
        Equal("9, Frontier Smart", sessionRow.ToString());
    }

    private static void TestSessionManagerFocus()
    {
        for (var pass = 0; pass < 2; pass++)
        {
            var manager = new SessionManager(new AppSettings());
            manager.AddOrUpdateTransientSession("frontierSmart", "Frontier Smart", [], null, 9);
            var window = new SessionSelectionWindow(
                manager,
                _ => Task.FromResult(new SessionCreationResult(false)))
            {
                Left = -10000,
                Top = -10000,
                ShowInTaskbar = false
            };
            window.Show();
            Pump();
            Equal("Menedżer sesji", window.Title);
            var create = Require<Button>(window, "CreateSessionButton");
            Equal("Utwórz nową sesję Frontier Smart", AutomationProperties.GetName(create));
            var list = Require<ListBox>(window, "SessionList");
            True(list.SelectedItem is SessionSelectionWindow.SessionRow);
            True(list.IsKeyboardFocusWithin || Keyboard.FocusedElement is ListBoxItem);
            window.Close();
            Pump();
        }
    }

    private static void TestDeviceWindowFocus()
    {
        using var client = new FrontierSmartClient(new NoNetworkHandler());
        var discovery = new FakeDiscoveryService("192.168.1.44");
        var settings = new FrontierSmartSettings();
        IReadOnlyCollection<string> rememberedCandidates;
        var first = new FrontierSmartDevicesWindow(
            settings,
            client,
            discovery,
            creatingSession: true)
        {
            Left = -10000,
            Top = -10000,
            ShowInTaskbar = false
        };
        first.Show();
        Pump();
        Equal(1, discovery.CallCount);
        var pin = Require<PasswordBox>(first, "PinBox");
        Equal("PIN urządzenia Frontier Smart", AutomationProperties.GetName(pin));
        False(ReferenceEquals(Keyboard.FocusedElement, pin));
        False(ReferenceEquals(Keyboard.FocusedElement, Require<Button>(first, "CloseButton")));
        var list = Require<ListBox>(first, "DevicesList");
        True(list.SelectedItem is FrontierSmartDeviceRow { IsDiscoveredCandidate: true });
        var candidate = (FrontierSmartDeviceRow)list.SelectedItem;
        True(candidate.ToString().Contains("wymaga podania PIN-u", StringComparison.Ordinal));
        True(list.IsKeyboardFocusWithin || Keyboard.FocusedElement is ListBoxItem);
        True(Require<Button>(first, "ConnectButton").IsEnabled);
        var create = Require<Button>(first, "CreateSessionButton");
        True(create.Visibility == Visibility.Visible);
        False(create.IsEnabled);
        False(Require<Expander>(first, "ManualAddressExpander").IsExpanded);
        rememberedCandidates = first.DiscoveredAddresses.ToArray();
        first.Close();
        Pump();

        var reopened = new FrontierSmartDevicesWindow(
            settings,
            client,
            discovery,
            knownDiscoveredAddresses: rememberedCandidates,
            creatingSession: true)
        {
            Left = -10000,
            Top = -10000,
            ShowInTaskbar = false
        };
        reopened.Show();
        Pump();
        Equal(1, discovery.CallCount);
        list = Require<ListBox>(reopened, "DevicesList");
        True(list.SelectedItem is FrontierSmartDeviceRow { IsDiscoveredCandidate: true });
        True(list.IsKeyboardFocusWithin || Keyboard.FocusedElement is ListBoxItem);
        reopened.Close();
        Pump();

        settings.Devices.Add(new FrontierSmartDeviceSettings
        {
            Id = "saved-radio",
            Address = "192.168.1.45",
            DisplayName = "Radio w kuchni"
        });
        settings.SelectedDeviceId = "saved-radio";
        var populated = new FrontierSmartDevicesWindow(settings, client, discovery)
        {
            Left = -10000,
            Top = -10000,
            ShowInTaskbar = false
        };
        populated.Show();
        Pump();
        Equal(1, discovery.CallCount);
        list = Require<ListBox>(populated, "DevicesList");
        True(list.SelectedItem is FrontierSmartDeviceRow { IsDiscoveredCandidate: false });
        True(list.IsKeyboardFocusWithin || Keyboard.FocusedElement is ListBoxItem);
        populated.Close();
        Pump();
    }

    private static void TestChoiceWindowFocus()
    {
        var window = new FrontierSmartChoiceWindow(
            "Tryby",
            "Wybierz tryb",
            [new FrontierSmartChoiceRow(0, "Radio internetowe", "Radio internetowe")])
        {
            Left = -10000,
            Top = -10000,
            ShowInTaskbar = false
        };
        window.Show();
        Pump();
        var list = Require<ListBox>(window, "ChoiceList");
        True(list.SelectedItem is FrontierSmartChoiceRow);
        True(list.IsKeyboardFocusWithin || Keyboard.FocusedElement is ListBoxItem);
        window.Close();
        Pump();
    }

    private static T Require<T>(FrameworkElement root, string name) where T : class =>
        root.FindName(name) as T
        ?? throw new InvalidOperationException($"Brak kontrolki {name}.");

    private static void Pump() =>
        Dispatcher.CurrentDispatcher.Invoke(() => { }, DispatcherPriority.ApplicationIdle);

    private static void True(bool value)
    {
        if (!value) throw new InvalidOperationException("Oczekiwano wartości prawda.");
    }

    private static void False(bool value) => True(!value);

    private static void Equal<T>(T expected, T actual)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException($"Oczekiwano „{expected}”, otrzymano „{actual}”.");
    }

    private sealed class NoNetworkHandler : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken) =>
            throw new InvalidOperationException("Test interfejsu nie może wykonywać połączeń sieciowych.");
    }

    private sealed class FakeDiscoveryService(params string[] addresses) : IFrontierSmartDiscoveryService
    {
        public int CallCount { get; private set; }

        public Task<IReadOnlyList<string>> DiscoverAddressesAsync(
            TimeSpan? duration = null,
            CancellationToken cancellationToken = default)
        {
            cancellationToken.ThrowIfCancellationRequested();
            CallCount++;
            return Task.FromResult<IReadOnlyList<string>>(addresses);
        }
    }
}
