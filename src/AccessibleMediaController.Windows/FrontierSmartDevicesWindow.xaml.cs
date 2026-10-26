using System.IO;
using System.Net.Http;
using System.Net.Sockets;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Devices.FrontierSmart;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class FrontierSmartDevicesWindow : Window
{
    private readonly FrontierSmartSettings settings;
    private readonly FrontierSmartClient client;
    private readonly IFrontierSmartDiscoveryService discovery;
    private readonly Dictionary<string, FrontierSmartSnapshot> snapshots =
        new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, string> errors =
        new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> discoveredAddresses =
        new(StringComparer.OrdinalIgnoreCase);
    private readonly CancellationTokenSource cancellation = new();
    private readonly CancellationToken cancellationToken;
    private bool busy;

    public FrontierSmartDevicesWindow(
        FrontierSmartSettings settings,
        FrontierSmartClient client,
        IFrontierSmartDiscoveryService discovery,
        IReadOnlyDictionary<string, FrontierSmartSnapshot>? knownSnapshots = null,
        IEnumerable<string>? knownDiscoveredAddresses = null,
        bool creatingSession = false)
    {
        InitializeComponent();
        this.settings = settings;
        this.client = client;
        this.discovery = discovery;
        cancellationToken = cancellation.Token;
        if (knownSnapshots is not null)
        {
            foreach (var (id, snapshot) in knownSnapshots) snapshots[id] = snapshot;
        }
        if (knownDiscoveredAddresses is not null)
        {
            foreach (var address in knownDiscoveredAddresses)
            {
                if (FrontierSmartAddressPolicy.TryNormalize(address, out var normalized))
                    discoveredAddresses.Add(normalized);
            }
        }
        CreateSessionButton.Visibility = creatingSession ? Visibility.Visible : Visibility.Collapsed;
        ReloadRows(settings.SelectedDeviceId);
    }

    public bool Changed { get; private set; }
    public bool SessionCreated { get; private set; }
    public IReadOnlyDictionary<string, FrontierSmartSnapshot> Snapshots => snapshots;
    public IReadOnlyCollection<string> DiscoveredAddresses => discoveredAddresses;
    private FrontierSmartDeviceRow? SelectedRow => DevicesList.SelectedItem as FrontierSmartDeviceRow;

    private async void Window_Loaded(object sender, RoutedEventArgs e)
    {
        FocusInitialControl();
        if (settings.Devices.Count > 0 || discoveredAddresses.Count > 0) return;
        await DiscoverDevicesAsync(automatic: true);
    }

    private async void Discover_Click(object sender, RoutedEventArgs e)
    {
        await DiscoverDevicesAsync(automatic: false);
    }

    private async Task DiscoverDevicesAsync(bool automatic)
    {
        if (busy) return;
        if (ReferenceEquals(Keyboard.FocusedElement, DiscoverButton)) FocusControl(DevicesList);
        var restoreListFocus = DevicesList.IsKeyboardFocusWithin || automatic;
        var foundAddresses = Array.Empty<string>();
        var newCandidateCount = 0;
        var completed = false;
        await RunAsync(async () =>
        {
            OperationStatusText.ShowProgress("Wykrywanie urządzeń Frontier Smart w sieci lokalnej…");
            foundAddresses = (await discovery.DiscoverAddressesAsync(cancellationToken: cancellationToken))
                .ToArray();
            foreach (var address in foundAddresses)
            {
                if (!settings.Devices.Any(device =>
                        string.Equals(device.Address, address, StringComparison.OrdinalIgnoreCase)))
                {
                    if (discoveredAddresses.Add(address)) newCandidateCount++;
                }
            }
            var preferred = foundAddresses.FirstOrDefault() is { } first
                ? FrontierSmartDeviceRow.DiscoveredRowId(first)
                : settings.SelectedDeviceId;
            ReloadRows(preferred);
            completed = true;
        });
        if (!completed || cancellation.IsCancellationRequested) return;
        OperationStatusText.Announce(newCandidateCount switch
        {
            0 when foundAddresses.Length > 0 => "Nie wykryto nowych urządzeń Frontier Smart. Urządzenia znalezione w sieci są już na liście.",
            0 => "Nie wykryto urządzenia Frontier Smart. Możesz ponowić wykrywanie albo rozwinąć dodawanie ręczne po adresie IP.",
            1 => "Wykryto jedno urządzenie Frontier Smart. Wybierz je, wpisz PIN i użyj Połącz i dodaj.",
            _ => $"Wykryto nowe urządzenia Frontier Smart: {newCandidateCount}. Wybierz urządzenie, wpisz PIN i użyj Połącz i dodaj."
        });
        var focusStillBelongsToList = DevicesList.IsKeyboardFocusWithin
            || Keyboard.FocusedElement is ListBoxItem;
        if (restoreListFocus && focusStillBelongsToList && DevicesList.SelectedItem is not null)
            _ = Dispatcher.BeginInvoke(FocusSelectedDevice, DispatcherPriority.ContextIdle);
        else if (automatic && focusStillBelongsToList && DevicesList.SelectedItem is null)
            _ = Dispatcher.BeginInvoke(() => FocusControl(DiscoverButton), DispatcherPriority.ContextIdle);
    }

    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (!FrontierSmartAddressPolicy.TryNormalize(AddressBox.Text, out var address))
        {
            OperationStatusText.Announce("Podaj lokalny adres IP, na przykład 192.168.1.25.");
            FocusControl(AddressBox);
            return;
        }
        if (!TryGetEnteredPin(out var pin)) return;
        await VerifyAndAddAsync(address, pin, manualAddress: true);
    }

    private async void Connect_Click(object sender, RoutedEventArgs e)
    {
        await ConnectSelectedAsync();
    }

    private async Task ConnectSelectedAsync()
    {
        if (SelectedRow is not { IsDiscoveredCandidate: true } row)
        {
            OperationStatusText.Announce("Wybierz wykryte urządzenie, które chcesz połączyć z AMC.");
            FocusSelectedDevice();
            return;
        }
        if (!TryGetEnteredPin(out var pin)) return;
        await VerifyAndAddAsync(row.Device.Address, pin, manualAddress: false);
    }

    private async Task VerifyAndAddAsync(string address, string pin, bool manualAddress)
    {
        string? addedId = null;
        string? addedName = null;
        var partialSnapshot = false;
        await RunAsync(async () =>
        {
            OperationStatusText.ShowProgress("Sprawdzanie połączenia z urządzeniem Frontier Smart…");
            try
            {
                var identity = await client.ReadIdentityAsync(address, pin, cancellationToken);
                FrontierSmartSnapshot? snapshot = null;
                try
                {
                    snapshot = await client.ReadSnapshotAsync(address, pin, cancellationToken);
                }
                catch (Exception exception) when (IsConnectionFailure(exception))
                {
                    partialSnapshot = true;
                    DiagnosticLog.Warning(
                        "frontier-add-state",
                        $"Potwierdzono urządzenie przy {address}, ale pełny stan nie jest jeszcze dostępny: {exception.GetType().Name}.");
                }
                addedId = Upsert(address, pin, identity, snapshot);
                addedName = identity.DisplayName;
                if (manualAddress) AddressBox.Clear();
                PinBox.Clear();
                ReloadRows(addedId);
            }
            catch (FrontierSmartProtocolException exception) when (exception.Message.Contains("PIN", StringComparison.OrdinalIgnoreCase))
            {
                PinBox.Clear();
                OperationStatusText.Announce("Urządzenie odrzuciło PIN. Sprawdź go i spróbuj ponownie.");
                FocusControl(PinBox);
            }
            catch (Exception exception) when (IsConnectionFailure(exception))
            {
                OperationStatusText.Announce("Pod tym adresem nie udało się potwierdzić urządzenia Frontier Smart. Sprawdź adres, PIN i połączenie z tą samą siecią.");
                DiagnosticLog.Warning("frontier-add", $"Nie udało się zweryfikować {address}: {exception.GetType().Name}.");
                FocusControl(manualAddress ? AddressBox : PinBox);
            }
        });
        if (addedId is null || cancellation.IsCancellationRequested) return;
        OperationStatusText.Announce(partialSnapshot
            ? $"Dodano urządzenie {addedName}. Pełny stan nie jest jeszcze dostępny; AMC spróbuje go odczytać przy wejściu do sesji."
            : $"Dodano i sprawdzono urządzenie {addedName}.");
        _ = Dispatcher.BeginInvoke(FocusSelectedDevice, DispatcherPriority.ContextIdle);
    }

    private async void Refresh_Click(object sender, RoutedEventArgs e)
    {
        if (SelectedRow is not { IsDiscoveredCandidate: false } row) return;
        if (!TryGetPin(row.Device, out var pin)) return;
        await RunAsync(async () =>
        {
            OperationStatusText.ShowProgress($"Odświeżanie urządzenia {row.Device.DisplayName}…");
            try
            {
                var snapshot = await client.ReadSnapshotAsync(row.Device.Address, pin, cancellationToken);
                var id = Upsert(row.Device.Address, pin, snapshot);
                PinBox.Clear();
                errors.Remove(id);
                ReloadRows(id);
                OperationStatusText.Announce($"Odświeżono urządzenie {snapshot.DisplayName}.");
            }
            catch (FrontierSmartProtocolException exception) when (exception.Message.Contains("PIN", StringComparison.OrdinalIgnoreCase))
            {
                FrontierSmartPinStore.Delete(row.Device.Id);
                errors[row.Device.Id] = "PIN wymaga ponownego podania";
                ReloadRows(row.Device.Id);
                OperationStatusText.Announce("Urządzenie odrzuciło zapisany PIN. Wpisz aktualny PIN i odśwież ponownie.");
                FocusControl(PinBox);
            }
            catch (Exception exception) when (IsConnectionFailure(exception))
            {
                errors[row.Device.Id] = "urządzenie obecnie niedostępne";
                ReloadRows(row.Device.Id);
                OperationStatusText.Announce($"Brak odpowiedzi urządzenia {row.Device.DisplayName}. Zapamiętany wpis pozostał bez zmian.");
            }
        });
    }

    private void Remove_Click(object sender, RoutedEventArgs e)
    {
        if (SelectedRow is not { IsDiscoveredCandidate: false } row) return;
        var answer = AccessibleDialog.Show(
            this,
            $"Usunąć urządzenie „{row.Device.DisplayName}” z AMC?\n\nNie zmieni to ustawień samego urządzenia.",
            "Usuń urządzenie Frontier Smart",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question,
            MessageBoxResult.No);
        if (answer != MessageBoxResult.Yes) return;
        settings.Devices.RemoveAll(device => string.Equals(device.Id, row.Device.Id, StringComparison.OrdinalIgnoreCase));
        FrontierSmartPinStore.Delete(row.Device.Id);
        snapshots.Remove(row.Device.Id);
        errors.Remove(row.Device.Id);
        if (string.Equals(settings.SelectedDeviceId, row.Device.Id, StringComparison.OrdinalIgnoreCase))
            settings.SelectedDeviceId = settings.Devices.FirstOrDefault()?.Id;
        Changed = true;
        ReloadRows(settings.SelectedDeviceId);
        OperationStatusText.Announce($"Usunięto urządzenie {row.Device.DisplayName} z AMC.");
    }

    private void Activate_Click(object sender, RoutedEventArgs e) => ActivateSelectedDevice();

    private void ActivateSelectedDevice()
    {
        if (SelectedRow is not { IsDiscoveredCandidate: false } row)
        {
            OperationStatusText.Announce("Najpierw połącz wykryte urządzenie albo wybierz urządzenie już zapisane w AMC.");
            return;
        }
        settings.SelectedDeviceId = row.Device.Id;
        Changed = true;
        ReloadRows(row.Device.Id);
        OperationStatusText.Announce($"Aktywne urządzenie: {row.Device.DisplayName}.");
        Dispatcher.BeginInvoke(FocusSelectedDevice, DispatcherPriority.ContextIdle);
    }

    private void CreateSession_Click(object sender, RoutedEventArgs e)
    {
        if (settings.Devices.Count == 0)
        {
            if (SelectedRow is { IsDiscoveredCandidate: true })
            {
                OperationStatusText.Announce("Wpisz PIN wybranego urządzenia i użyj Połącz i dodaj.");
                FocusControl(PinBox);
            }
            else
            {
                OperationStatusText.Announce("Najpierw wykryj lub dodaj i sprawdź urządzenie Frontier Smart.");
                FocusControl(DiscoverButton);
            }
            return;
        }
        settings.SessionEnabled = true;
        settings.SelectedDeviceId ??= settings.Devices[0].Id;
        Changed = true;
        SessionCreated = true;
        DialogResult = true;
    }

    private string Upsert(string address, string pin, FrontierSmartSnapshot snapshot) =>
        Upsert(
            address,
            pin,
            new FrontierSmartIdentity(snapshot.DisplayName, snapshot.RadioId, snapshot.FirmwareVersion),
            snapshot);

    private string Upsert(
        string address,
        string pin,
        FrontierSmartIdentity identity,
        FrontierSmartSnapshot? snapshot)
    {
        var id = string.IsNullOrWhiteSpace(identity.RadioId)
            ? $"frontier:{address}"
            : identity.RadioId.Trim();
        var existing = settings.Devices.FirstOrDefault(device =>
            string.Equals(device.Id, id, StringComparison.OrdinalIgnoreCase)
            || string.Equals(device.Address, address, StringComparison.OrdinalIgnoreCase));
        if (existing is null)
        {
            existing = new FrontierSmartDeviceSettings();
            settings.Devices.Add(existing);
        }
        var previousId = existing.Id;
        existing.Id = id;
        existing.Address = address;
        existing.DisplayName = string.IsNullOrWhiteSpace(identity.DisplayName)
            ? $"Frontier Smart {address}"
            : identity.DisplayName.Trim();
        existing.Firmware = identity.FirmwareVersion?.Trim() ?? string.Empty;
        existing.LastSeenUtcTicks = DateTime.UtcNow.Ticks;
        if (!string.IsNullOrWhiteSpace(previousId)
            && !string.Equals(previousId, id, StringComparison.OrdinalIgnoreCase))
        {
            FrontierSmartPinStore.Delete(previousId);
            snapshots.Remove(previousId);
            errors.Remove(previousId);
        }
        FrontierSmartPinStore.Write(id, pin);
        if (snapshot is not null) snapshots[id] = snapshot;
        errors.Remove(id);
        discoveredAddresses.Remove(address);
        settings.SelectedDeviceId ??= id;
        Changed = true;
        return id;
    }

    private void ReloadRows(string? preferredId)
    {
        preferredId ??= SelectedRow?.RowId;
        var savedRows = settings.Devices
            .OrderBy(device => device.DisplayName, StringComparer.CurrentCultureIgnoreCase)
            .Select(device => new FrontierSmartDeviceRow(
                device,
                snapshots.GetValueOrDefault(device.Id),
                errors.GetValueOrDefault(device.Id),
                string.Equals(device.Id, settings.SelectedDeviceId, StringComparison.OrdinalIgnoreCase)))
            .ToArray();
        var savedAddresses = settings.Devices
            .Select(device => device.Address)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        var discoveredRows = discoveredAddresses
            .Where(address => !savedAddresses.Contains(address))
            .OrderBy(address => address, StringComparer.OrdinalIgnoreCase)
            .Select(address => FrontierSmartDeviceRow.CreateDiscovered(address))
            .ToArray();
        var rows = savedRows.Concat(discoveredRows).ToArray();
        DevicesList.ItemsSource = rows;
        DevicesList.SelectedItem = rows.FirstOrDefault(row =>
            string.Equals(row.RowId, preferredId, StringComparison.OrdinalIgnoreCase));
        if (DevicesList.SelectedItem is null && rows.Length > 0) DevicesList.SelectedIndex = 0;
        UpdateSelection();
    }

    private async Task RunAsync(Func<Task> action)
    {
        if (busy) return;
        SetBusy(true);
        try
        {
            await action();
        }
        catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
        {
        }
        catch (Exception exception)
        {
            OperationStatusText.Announce("Operacja Frontier Smart nie powiodła się. Sprawdź sieć lokalną i spróbuj ponownie.");
            DiagnosticLog.Warning("frontier-manager", $"Operacja nie powiodła się: {exception.GetType().Name}.");
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void SetBusy(bool value)
    {
        busy = value;
        DiscoverButton.IsEnabled = !value;
        ConnectButton.IsEnabled = !value && SelectedRow is { IsDiscoveredCandidate: true };
        AddButton.IsEnabled = !value;
        AddressBox.IsEnabled = !value;
        PinBox.IsEnabled = !value;
        ActivateButton.IsEnabled = !value && SelectedRow is { IsDiscoveredCandidate: false };
        RefreshButton.IsEnabled = !value && SelectedRow is { IsDiscoveredCandidate: false };
        RemoveButton.IsEnabled = !value && SelectedRow is { IsDiscoveredCandidate: false };
        CreateSessionButton.IsEnabled = !value && settings.Devices.Count > 0;
    }

    private void DevicesList_SelectionChanged(object sender, SelectionChangedEventArgs e) => UpdateSelection();

    private void UpdateSelection()
    {
        var confirmed = SelectedRow is { IsDiscoveredCandidate: false };
        ConnectButton.IsEnabled = !busy && SelectedRow is { IsDiscoveredCandidate: true };
        RefreshButton.IsEnabled = !busy && confirmed;
        RemoveButton.IsEnabled = !busy && confirmed;
        ActivateButton.IsEnabled = !busy && confirmed;
        CreateSessionButton.IsEnabled = !busy && settings.Devices.Count > 0;
        DeviceDetailsText.Text = SelectedRow?.Details
            ?? "Brak urządzeń na liście. AMC szuka ich automatycznie; możesz też ponowić wykrywanie albo rozwinąć dodawanie ręczne po adresie IP.";
    }

    private bool TryGetEnteredPin(out string pin)
    {
        pin = PinBox.Password;
        if (!string.IsNullOrWhiteSpace(pin) && pin.Length <= 16 && pin.All(char.IsAsciiDigit)) return true;
        OperationStatusText.Announce("PIN urządzenia musi zawierać od 1 do 16 cyfr.");
        FocusControl(PinBox);
        return false;
    }

    private bool TryGetPin(FrontierSmartDeviceSettings device, out string pin)
    {
        if (!string.IsNullOrWhiteSpace(PinBox.Password)) return TryGetEnteredPin(out pin);
        if (FrontierSmartPinStore.TryRead(device.Id, out pin)) return true;
        OperationStatusText.Announce($"Wpisz PIN urządzenia {device.DisplayName}.");
        FocusControl(PinBox);
        return false;
    }

    private void FocusInitialControl()
    {
        if (DevicesList.SelectedItem is not null)
        {
            FocusSelectedDevice();
            return;
        }
        FocusControl(DevicesList);
    }

    private void FocusSelectedDevice()
    {
        if (DevicesList.SelectedItem is null) return;
        DevicesList.ScrollIntoView(DevicesList.SelectedItem);
        DevicesList.UpdateLayout();
        if (DevicesList.ItemContainerGenerator.ContainerFromItem(DevicesList.SelectedItem) is ListBoxItem item)
        {
            FocusControl(item);
            return;
        }
        FocusControl(DevicesList);
    }

    private static void FocusControl(IInputElement element)
    {
        element.Focus();
        Keyboard.Focus(element);
    }

    private async void Window_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.F5 && Keyboard.Modifiers == ModifierKeys.None)
        {
            if (SelectedRow is { IsDiscoveredCandidate: false }) Refresh_Click(this, new RoutedEventArgs());
            else Discover_Click(this, new RoutedEventArgs());
            e.Handled = true;
            return;
        }
        if (e.Key == Key.Enter && Keyboard.Modifiers == ModifierKeys.None && DevicesList.IsKeyboardFocusWithin)
        {
            e.Handled = true;
            if (SelectedRow is { IsDiscoveredCandidate: true }) await ConnectSelectedAsync();
            else ActivateSelectedDevice();
            return;
        }
        if (e.Key != Key.Escape) return;
        Close();
        e.Handled = true;
    }

    private void Window_Closed(object? sender, EventArgs e)
    {
        cancellation.Cancel();
        cancellation.Dispose();
    }

    private static bool IsConnectionFailure(Exception exception) => exception is
        HttpRequestException or TaskCanceledException or IOException or SocketException
        or FormatException or ArgumentException;
}

public sealed record FrontierSmartDeviceRow(
    FrontierSmartDeviceSettings Device,
    FrontierSmartSnapshot? Snapshot,
    string? Error,
    bool IsActive,
    bool IsDiscoveredCandidate = false)
{
    public string RowId => Device.Id;
    public string NavigationText => IsDiscoveredCandidate
        ? $"Wykryte urządzenie Frontier Smart {Device.Address}"
        : Device.DisplayName;

    public static string DiscoveredRowId(string address) => $"frontier-discovered:{address}";

    public static FrontierSmartDeviceRow CreateDiscovered(string address) => new(
        new FrontierSmartDeviceSettings
        {
            Id = DiscoveredRowId(address),
            Address = address,
            DisplayName = "Wykryte urządzenie Frontier Smart"
        },
        null,
        null,
        false,
        true);

    public string Label
    {
        get
        {
            if (IsDiscoveredCandidate)
                return $"Wykryte urządzenie Frontier Smart, adres {Device.Address}, wymaga podania PIN-u";
            var active = IsActive ? ", aktywne" : string.Empty;
            if (!string.IsNullOrWhiteSpace(Error)) return $"{Device.DisplayName}{active}, {Error}";
            if (Snapshot is null) return $"{Device.DisplayName}{active}, zapisane, stan jeszcze nieodświeżony";
            return $"{Device.DisplayName}{active}, dostępne, {Snapshot.PlaybackSummary}";
        }
    }

    public string Details
    {
        get
        {
            if (IsDiscoveredCandidate)
            {
                return $"Wykryto urządzenie Frontier Smart pod adresem {Device.Address}. "
                    + "Wpisz PIN wybranego urządzenia i użyj Połącz i dodaj. Samo zaznaczenie niczego nie zapisuje.";
            }
            var parts = new List<string>
            {
                $"Nazwa: {Device.DisplayName}.",
                $"Adres IP: {Device.Address}."
            };
            if (!string.IsNullOrWhiteSpace(Device.Firmware)) parts.Add($"Oprogramowanie urządzenia: {Device.Firmware}.");
            if (Snapshot is not null)
            {
                parts.Add($"Stan: {Snapshot.PlaybackSummary}.");
                if (Snapshot.VolumePercent is { } volume) parts.Add($"Głośność: {volume} procent.");
                if (!string.IsNullOrWhiteSpace(Snapshot.Artist)) parts.Add($"Wykonawca: {Snapshot.Artist}.");
                if (!string.IsNullOrWhiteSpace(Snapshot.Album)) parts.Add($"Album: {Snapshot.Album}.");
            }
            else if (!string.IsNullOrWhiteSpace(Error)) parts.Add($"Stan: {Error}.");
            return string.Join(' ', parts);
        }
    }

    public override string ToString() => Label;
}
