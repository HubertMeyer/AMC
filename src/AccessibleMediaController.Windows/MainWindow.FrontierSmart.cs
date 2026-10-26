using System.IO;
using System.Net.Http;
using System.Net.Sockets;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Threading;
using AccessibleMediaController.Core.Commands;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Devices.FrontierSmart;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class MainWindow
{
    private const string FrontierSmartSessionId = "frontierSmart";
    private readonly List<MediaItem> _frontierSmartItems = [];
    private readonly Dictionary<string, FrontierSmartSnapshot> _frontierSmartSnapshots =
        new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _frontierSmartDiscoveredAddresses =
        new(StringComparer.OrdinalIgnoreCase);
    private readonly FrontierSmartClient _frontierSmartClient = new();
    private readonly FrontierSmartDiscoveryService _frontierSmartDiscovery = new();
    private readonly CancellationTokenSource _frontierSmartCancellation = new();
    private readonly SemaphoreSlim _frontierSmartOperationGate = new(1, 1);
    private bool _frontierSmartRefreshInProgress;

    private bool IsFrontierSmartSession(string? sessionId = null) =>
        string.Equals(sessionId ?? _sessions.Current.Id, FrontierSmartSessionId, StringComparison.Ordinal);

    private void LoadPersistedFrontierSmart()
    {
        _frontierSmartItems.Clear();
        foreach (var device in _state.FrontierSmart.Devices)
        {
            _frontierSmartItems.Add(BuildFrontierSmartMediaItem(
                device,
                _frontierSmartSnapshots.GetValueOrDefault(device.Id)));
        }
    }

    private static MediaItem BuildFrontierSmartMediaItem(
        FrontierSmartDeviceSettings device,
        FrontierSmartSnapshot? snapshot)
    {
        var current = snapshot is null
            ? "zapisane urządzenie, stan jeszcze nieodświeżony"
            : snapshot.PlaybackSummary;
        return new MediaItem
        {
            Id = device.Id,
            Title = device.DisplayName,
            Artist = current,
            Kind = MediaItemKind.Device,
            Duration = snapshot?.Duration ?? TimeSpan.Zero,
            IsAvailable = true
        };
    }

    private DemoMediaSession? RegisterFrontierSmartSession(string? preferredDeviceId = null)
    {
        if (!_state.FrontierSmart.SessionEnabled) return null;
        LoadPersistedFrontierSmart();
        var (session, _) = _sessions.AddOrUpdateTransientSession(
            FrontierSmartSessionId,
            "Frontier Smart",
            _frontierSmartItems,
            output: null,
            preferredSlot: 9);
        session.ReplaceItems(_frontierSmartItems);
        preferredDeviceId ??= _state.FrontierSmart.SelectedDeviceId;
        var item = session.Items.FirstOrDefault(candidate =>
            string.Equals(candidate.Id, preferredDeviceId, StringComparison.OrdinalIgnoreCase));
        if (item is not null) session.SelectItem(item);
        return session;
    }

    private Task<SessionCreationResult> CreateFrontierSmartSessionAsync(Window owner)
    {
        var dialog = new FrontierSmartDevicesWindow(
            _state.FrontierSmart,
            _frontierSmartClient,
            _frontierSmartDiscovery,
            _frontierSmartSnapshots,
            _frontierSmartDiscoveredAddresses,
            creatingSession: true)
        {
            Owner = owner
        };
        var accepted = dialog.ShowDialog() == true && dialog.SessionCreated;
        ReplaceFrontierSmartSnapshots(dialog.Snapshots);
        ReplaceFrontierSmartDiscoveredAddresses(dialog.DiscoveredAddresses);
        if (!accepted)
            return Task.FromResult(new SessionCreationResult(false, Announcement: "Nie utworzono sesji Frontier Smart"));

        _state.FrontierSmart.SessionEnabled = true;
        var session = RegisterFrontierSmartSession(_state.FrontierSmart.SelectedDeviceId);
        QueueStateSave(announceFailure: true);
        var slot = _sessions.FindSlot(FrontierSmartSessionId);
        return Task.FromResult(session is null
            ? new SessionCreationResult(false, Announcement: "Nie udało się utworzyć sesji Frontier Smart")
            : new SessionCreationResult(
                true,
                FrontierSmartSessionId,
                slot is { } number
                    ? $"Utworzono sesję Frontier Smart. Skrót: Ctrl+{number}."
                    : "Utworzono sesję Frontier Smart bez skrótu cyfrowego."));
    }

    public void ShowFrontierSmartDeviceManager()
    {
        var dialog = new FrontierSmartDevicesWindow(
            _state.FrontierSmart,
            _frontierSmartClient,
            _frontierSmartDiscovery,
            _frontierSmartSnapshots,
            _frontierSmartDiscoveredAddresses)
        {
            Owner = this
        };
        dialog.ShowDialog();
        ReplaceFrontierSmartSnapshots(dialog.Snapshots);
        ReplaceFrontierSmartDiscoveredAddresses(dialog.DiscoveredAddresses);
        if (dialog.Changed)
        {
            RefreshFrontierSmartSessionItems(_state.FrontierSmart.SelectedDeviceId);
            QueueStateSave(announceFailure: true);
        }
        if (_playerViewActive && IsFrontierSmartSession() && _sessions.Current.HasCurrentItem)
        {
            UpdatePlayerView(true);
            Dispatcher.BeginInvoke(FocusPlayerView, DispatcherPriority.ContextIdle);
        }
        else
        {
            RestoreMediaListFocusAfterRefresh();
        }
    }

    private void ReplaceFrontierSmartSnapshots(
        IReadOnlyDictionary<string, FrontierSmartSnapshot> snapshots)
    {
        _frontierSmartSnapshots.Clear();
        foreach (var (id, snapshot) in snapshots) _frontierSmartSnapshots[id] = snapshot;
    }

    private void ReplaceFrontierSmartDiscoveredAddresses(IEnumerable<string> addresses)
    {
        _frontierSmartDiscoveredAddresses.Clear();
        foreach (var address in addresses) _frontierSmartDiscoveredAddresses.Add(address);
    }

    private void RefreshFrontierSmartSessionItems(string? preferredDeviceId = null)
    {
        preferredDeviceId ??= IsFrontierSmartSession() ? SelectedItem?.Id : null;
        LoadPersistedFrontierSmart();
        var session = _sessions.FindSession(FrontierSmartSessionId);
        session?.ReplaceItems(_frontierSmartItems);
        if (session is not null)
        {
            var selected = session.Items.FirstOrDefault(item =>
                string.Equals(item.Id, preferredDeviceId ?? _state.FrontierSmart.SelectedDeviceId,
                    StringComparison.OrdinalIgnoreCase));
            if (selected is not null)
            {
                session.SelectItem(selected);
                if (_frontierSmartSnapshots.GetValueOrDefault(selected.Id) is { } snapshot)
                {
                    session.SetPosition(snapshot.Position ?? TimeSpan.Zero);
                    if (snapshot.IsPoweredOn == false)
                        session.StopPlayback();
                    else if (snapshot.PlaybackControl == (int)FrontierSmartPlaybackCommand.Pause
                             && session.IsPlaying)
                        session.TogglePlayback();
                    else if (snapshot.PlaybackControl == (int)FrontierSmartPlaybackCommand.Play)
                        session.Play(selected);
                }
            }
        }
        if (!IsFrontierSmartSession()) return;
        if (_playerViewActive)
        {
            UpdatePlayerView(true);
            UpdatePlaybackStatusBar();
            UpdateWindowTitle();
            return;
        }
        RefreshCurrentView(preferredItemId: preferredDeviceId);
        UpdateWindowTitle();
    }

    public async void RefreshFrontierSmartDevices() =>
        await RefreshFrontierSmartDevicesAsync(announceResult: true);

    private async Task RefreshFrontierSmartDevicesAsync(bool announceResult)
    {
        if (_frontierSmartRefreshInProgress) return;
        var devices = _state.FrontierSmart.Devices.ToArray();
        if (devices.Length == 0)
        {
            if (announceResult) Announce("Brak zapisanych urządzeń Frontier Smart. Ctrl+F5 otwiera wykrywanie i dodawanie urządzeń");
            return;
        }
        _frontierSmartRefreshInProgress = true;
        var gateEntered = false;
        try
        {
            await _frontierSmartOperationGate.WaitAsync(_frontierSmartCancellation.Token);
            gateEntered = true;
            var available = 0;
            var missingPin = 0;
            foreach (var device in devices)
            {
                if (!FrontierSmartPinStore.TryRead(device.Id, out var pin))
                {
                    missingPin++;
                    _frontierSmartSnapshots.Remove(device.Id);
                    continue;
                }
                try
                {
                    var snapshot = await _frontierSmartClient.ReadSnapshotAsync(
                        device.Address,
                        pin,
                        _frontierSmartCancellation.Token);
                    ApplyFrontierSmartSnapshot(device, snapshot);
                    available++;
                }
                catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
                {
                    _frontierSmartSnapshots.Remove(device.Id);
                    DiagnosticLog.Warning("frontier-refresh", $"Brak odpowiedzi {device.Address}: {exception.GetType().Name}.");
                }
            }
            RefreshFrontierSmartSessionItems(_state.FrontierSmart.SelectedDeviceId);
            QueueStateSave(announceFailure: true);
            if (announceResult)
            {
                Announce(missingPin > 0
                    ? $"Dostępne urządzenia Frontier Smart: {available} z {devices.Length}. Dla {missingPin} urządzeń trzeba ponownie podać PIN przez Ctrl+F5"
                    : available == devices.Length
                        ? devices.Length == 1 ? "Odświeżono urządzenie Frontier Smart" : $"Odświeżono urządzenia Frontier Smart: {available}"
                        : $"Dostępne urządzenia Frontier Smart: {available} z {devices.Length}");
            }
        }
        catch (OperationCanceledException) when (_frontierSmartCancellation.IsCancellationRequested)
        {
        }
        finally
        {
            if (gateEntered) _frontierSmartOperationGate.Release();
            _frontierSmartRefreshInProgress = false;
        }
    }

    private async Task RefreshActiveFrontierSmartDeviceOnEntryAsync()
    {
        if (_isClosing || !IsFrontierSmartSession() || !_sessions.Current.HasCurrentItem) return;
        await RefreshFrontierSmartDeviceAsync(_sessions.Current.CurrentItem.Id, announceFailure: false);
    }

    private async Task ActivateFrontierSmartDeviceAsync(MediaItem item)
    {
        var session = _sessions.FindSession(FrontierSmartSessionId);
        if (session is null || !session.SelectItem(item))
        {
            Announce("Nie można wybrać urządzenia Frontier Smart");
            return;
        }
        _state.FrontierSmart.SelectedDeviceId = item.Id;
        var snapshot = await RefreshFrontierSmartDeviceAsync(item.Id, announceFailure: true);
        if (snapshot is null || _isClosing) return;
        if (snapshot.IsPoweredOn == false && TryGetFrontierSmartDevice(item.Id, out var device)
            && FrontierSmartPinStore.TryRead(device.Id, out var pin))
        {
            try
            {
                await _frontierSmartClient.SetPowerAsync(device.Address, pin, true, _frontierSmartCancellation.Token);
                snapshot = await _frontierSmartClient.ReadSnapshotAsync(device.Address, pin, _frontierSmartCancellation.Token);
                ApplyFrontierSmartSnapshot(device, snapshot);
            }
            catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
            {
                Announce($"Wybrano {device.DisplayName}, ale nie udało się włączyć urządzenia");
            }
        }
        QueueStateSave(announceFailure: true);
        _playerFocusContextPrefix = $"Wybrano urządzenie {item.Title}";
        ShowPlayerView();
    }

    private async Task<FrontierSmartSnapshot?> RefreshFrontierSmartDeviceAsync(
        string deviceId,
        bool announceFailure)
    {
        if (!TryGetFrontierSmartDevice(deviceId, out var device))
        {
            if (announceFailure) Announce("Nie można odnaleźć zapisanego urządzenia Frontier Smart");
            return null;
        }
        if (!FrontierSmartPinStore.TryRead(device.Id, out var pin))
        {
            if (announceFailure) Announce($"Brak zapisanego PIN-u urządzenia {device.DisplayName}. Ctrl+F5 pozwala podać go ponownie");
            return null;
        }
        var gateEntered = false;
        try
        {
            await _frontierSmartOperationGate.WaitAsync(_frontierSmartCancellation.Token);
            gateEntered = true;
            var snapshot = await _frontierSmartClient.ReadSnapshotAsync(
                device.Address,
                pin,
                _frontierSmartCancellation.Token);
            if (_isClosing) return null;
            ApplyFrontierSmartSnapshot(device, snapshot);
            _state.FrontierSmart.SelectedDeviceId = device.Id;
            RefreshFrontierSmartSessionItems(device.Id);
            return snapshot;
        }
        catch (OperationCanceledException) when (_frontierSmartCancellation.IsCancellationRequested)
        {
            return null;
        }
        catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
        {
            DiagnosticLog.Warning("frontier-refresh", $"Brak odpowiedzi {device.Address}: {exception.GetType().Name}.");
            if (announceFailure) Announce($"Brak odpowiedzi urządzenia {device.DisplayName}. Sprawdź sieć i PIN przez Ctrl+F5");
            return null;
        }
        finally
        {
            if (gateEntered) _frontierSmartOperationGate.Release();
        }
    }

    private async Task ExecuteFrontierSmartTransportCommandAsync(string commandId)
    {
        if (!TryGetActiveFrontierSmartContext(out var device, out var pin, out var snapshot)) return;
        var gateEntered = false;
        try
        {
            await _frontierSmartOperationGate.WaitAsync(_frontierSmartCancellation.Token);
            gateEntered = true;
            snapshot ??= await _frontierSmartClient.ReadSnapshotAsync(device.Address, pin, _frontierSmartCancellation.Token);
            switch (commandId)
            {
                case CommandIds.PlayPause:
                    await _frontierSmartClient.SendPlaybackCommandAsync(
                        device.Address,
                        pin,
                        snapshot.PlaybackControl == (int)FrontierSmartPlaybackCommand.Play
                            ? FrontierSmartPlaybackCommand.Pause
                            : FrontierSmartPlaybackCommand.Play,
                        _frontierSmartCancellation.Token);
                    break;
                case CommandIds.Previous:
                    await _frontierSmartClient.SendPlaybackCommandAsync(device.Address, pin, FrontierSmartPlaybackCommand.Previous, _frontierSmartCancellation.Token);
                    break;
                case CommandIds.Next:
                    await _frontierSmartClient.SendPlaybackCommandAsync(device.Address, pin, FrontierSmartPlaybackCommand.Next, _frontierSmartCancellation.Token);
                    break;
                case CommandIds.ToggleMuteCurrentSession:
                    await _frontierSmartClient.SetMutedAsync(device.Address, pin, snapshot.IsMuted != true, _frontierSmartCancellation.Token);
                    break;
                case CommandIds.VolumeUp5:
                case CommandIds.VolumeDown5:
                case CommandIds.VolumeUp1:
                case CommandIds.VolumeDown1:
                    if (snapshot.VolumePercent is not { } volume || snapshot.VolumeStepCount is not { } steps)
                    {
                        Announce("Urządzenie nie podało zakresu głośności");
                        return;
                    }
                    var delta = commandId switch
                    {
                        CommandIds.VolumeUp5 => 5,
                        CommandIds.VolumeDown5 => -5,
                        CommandIds.VolumeUp1 => 1,
                        _ => -1
                    };
                    await _frontierSmartClient.SetVolumeStepAsync(
                        device.Address,
                        pin,
                        FrontierSmartVolume.FromPercent(Math.Clamp(volume + delta, 0, 100), steps),
                        _frontierSmartCancellation.Token);
                    break;
                case CommandIds.TrackStart:
                    await _frontierSmartClient.SetPlaybackPositionAsync(device.Address, pin, TimeSpan.Zero, _frontierSmartCancellation.Token);
                    break;
                case CommandIds.TrackEnd:
                    if (snapshot.Duration is not { } duration || duration <= TimeSpan.Zero)
                    {
                        Announce("Czas trwania bieżącego materiału jest nieznany");
                        return;
                    }
                    await _frontierSmartClient.SetPlaybackPositionAsync(device.Address, pin, duration, _frontierSmartCancellation.Token);
                    break;
                default:
                    Announce("To polecenie nie jest dostępne dla urządzenia Frontier Smart");
                    return;
            }
            var updated = await _frontierSmartClient.ReadSnapshotAsync(device.Address, pin, _frontierSmartCancellation.Token);
            ApplyFrontierSmartSnapshot(device, updated);
            RefreshFrontierSmartSessionItems(device.Id);
            AnnounceFrontierSmartCommandResult(commandId, updated);
            QueueStateSave(announceFailure: true);
        }
        catch (OperationCanceledException) when (_frontierSmartCancellation.IsCancellationRequested)
        {
        }
        catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
        {
            Announce($"Nie udało się wykonać polecenia na urządzeniu {device.DisplayName}");
            DiagnosticLog.Warning("frontier-command", $"Polecenie {commandId} nie powiodło się: {exception.GetType().Name}.");
        }
        finally
        {
            if (gateEntered) _frontierSmartOperationGate.Release();
        }
    }

    private async Task ShowFrontierSmartModesAsync()
    {
        if (!TryGetActiveFrontierSmartContext(out var device, out var pin, out var snapshot)) return;
        try
        {
            var modes = await _frontierSmartClient.ReadModesAsync(device.Address, pin, _frontierSmartCancellation.Token);
            if (modes.Count == 0)
            {
                Announce("Urządzenie nie udostępniło listy trybów");
                return;
            }
            var choices = modes.Select(mode => new FrontierSmartChoiceRow(
                mode.Key,
                mode.AccessibleLabel,
                mode.NavigationText,
                mode.Selectable)).ToArray();
            var dialog = new FrontierSmartChoiceWindow(
                $"Tryby — {device.DisplayName}",
                $"Wybierz tryb urządzenia {device.DisplayName}",
                choices,
                snapshot?.ModeIndex)
            {
                Owner = this
            };
            if (dialog.ShowDialog() != true || dialog.SelectedKey is not { } key)
            {
                RestoreFrontierSmartFocus();
                return;
            }
            await _frontierSmartClient.SetModeAsync(device.Address, pin, key, _frontierSmartCancellation.Token);
            var selected = modes.First(mode => mode.Key == key);
            var updated = await _frontierSmartClient.ReadSnapshotAsync(device.Address, pin, _frontierSmartCancellation.Token);
            ApplyFrontierSmartSnapshot(device, updated);
            RefreshFrontierSmartSessionItems(device.Id);
            Announce($"Wybrano tryb {selected.DisplayName}");
        }
        catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
        {
            Announce("Nie udało się odczytać lub zmienić trybu urządzenia Frontier Smart");
        }
        finally
        {
            RestoreFrontierSmartFocus();
        }
    }

    private async Task ShowFrontierSmartPresetsAsync()
    {
        if (!TryGetActiveFrontierSmartContext(out var device, out var pin, out _)) return;
        try
        {
            var presets = await _frontierSmartClient.ReadPresetsAsync(device.Address, pin, _frontierSmartCancellation.Token);
            if (presets.Count == 0)
            {
                Announce("W bieżącym trybie urządzenie nie udostępniło zapisanych presetów");
                return;
            }
            var choices = presets.Select(preset => new FrontierSmartChoiceRow(
                preset.Key,
                preset.AccessibleLabel,
                preset.NavigationText)).ToArray();
            var dialog = new FrontierSmartChoiceWindow(
                $"Presety — {device.DisplayName}",
                $"Wybierz preset urządzenia {device.DisplayName}",
                choices)
            {
                Owner = this
            };
            if (dialog.ShowDialog() != true || dialog.SelectedKey is not { } key)
            {
                RestoreFrontierSmartFocus();
                return;
            }
            await ActivateFrontierSmartPresetAsync(device, pin, presets.First(preset => preset.Key == key));
        }
        catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
        {
            Announce("Nie udało się odczytać lub uruchomić presetu urządzenia Frontier Smart");
        }
        finally
        {
            RestoreFrontierSmartFocus();
        }
    }

    private async Task ActivateFrontierSmartPresetNumberAsync(int oneBasedNumber)
    {
        if (!TryGetActiveFrontierSmartContext(out var device, out var pin, out _)) return;
        try
        {
            var presets = await _frontierSmartClient.ReadPresetsAsync(device.Address, pin, _frontierSmartCancellation.Token);
            var preset = presets.FirstOrDefault(candidate => candidate.Key + 1 == oneBasedNumber);
            if (preset is null)
            {
                Announce($"Preset {oneBasedNumber} jest pusty w bieżącym trybie urządzenia");
                return;
            }
            await ActivateFrontierSmartPresetAsync(device, pin, preset);
        }
        catch (Exception exception) when (IsFrontierSmartConnectionFailure(exception))
        {
            Announce($"Nie udało się uruchomić presetu {oneBasedNumber}");
        }
    }

    private async Task ActivateFrontierSmartPresetAsync(
        FrontierSmartDeviceSettings device,
        string pin,
        FrontierSmartPreset preset)
    {
        await _frontierSmartClient.ActivatePresetAsync(device.Address, pin, preset.Key, _frontierSmartCancellation.Token);
        var updated = await _frontierSmartClient.ReadSnapshotAsync(device.Address, pin, _frontierSmartCancellation.Token);
        ApplyFrontierSmartSnapshot(device, updated);
        RefreshFrontierSmartSessionItems(device.Id);
        Announce($"Uruchomiono {preset.AccessibleLabel}");
        QueueStateSave(announceFailure: true);
    }

    private bool TryGetActiveFrontierSmartContext(
        out FrontierSmartDeviceSettings device,
        out string pin,
        out FrontierSmartSnapshot? snapshot)
    {
        device = null!;
        var id = ActionItem?.Kind == MediaItemKind.Device ? ActionItem.Id : null;
        id ??= _sessions.Current.HasCurrentItem ? _sessions.Current.CurrentItem.Id : null;
        id ??= _state.FrontierSmart.SelectedDeviceId;
        if (id is null || !TryGetFrontierSmartDevice(id, out device))
        {
            pin = string.Empty;
            snapshot = null;
            Announce("Brak wybranego urządzenia Frontier Smart. Ctrl+F5 otwiera wykrywanie i dodawanie urządzeń");
            return false;
        }
        _state.FrontierSmart.SelectedDeviceId = device.Id;
        snapshot = _frontierSmartSnapshots.GetValueOrDefault(device.Id);
        if (FrontierSmartPinStore.TryRead(device.Id, out pin)) return true;
        Announce($"Brak zapisanego PIN-u urządzenia {device.DisplayName}. Ctrl+F5 pozwala podać go ponownie");
        return false;
    }

    private bool TryGetFrontierSmartDevice(string id, out FrontierSmartDeviceSettings device)
    {
        device = _state.FrontierSmart.Devices.FirstOrDefault(candidate =>
            string.Equals(candidate.Id, id, StringComparison.OrdinalIgnoreCase))!;
        return device is not null;
    }

    private void ApplyFrontierSmartSnapshot(
        FrontierSmartDeviceSettings device,
        FrontierSmartSnapshot snapshot)
    {
        device.DisplayName = string.IsNullOrWhiteSpace(snapshot.DisplayName)
            ? device.DisplayName
            : snapshot.DisplayName.Trim();
        device.Firmware = snapshot.FirmwareVersion?.Trim() ?? string.Empty;
        device.LastSeenUtcTicks = DateTime.UtcNow.Ticks;
        _frontierSmartSnapshots[device.Id] = snapshot;
    }

    private void AnnounceFrontierSmartInformation()
    {
        if (!TryGetActiveFrontierSmartContext(out var device, out _, out var snapshot)) return;
        if (snapshot is null)
        {
            Announce($"{device.DisplayName}. Stan jeszcze nieodświeżony. F5 odświeża urządzenie");
            return;
        }
        var parts = new List<string> { device.DisplayName, snapshot.PlaybackSummary };
        if (!string.IsNullOrWhiteSpace(snapshot.Artist)) parts.Add($"wykonawca {snapshot.Artist}");
        if (!string.IsNullOrWhiteSpace(snapshot.Album)) parts.Add($"album {snapshot.Album}");
        if (snapshot.VolumePercent is { } volume) parts.Add($"głośność {volume} procent");
        if (snapshot.Position is { } position) parts.Add($"czas {CommandRouter.FormatTime(position)}");
        Announce(string.Join(", ", parts));
    }

    private void UpdateFrontierSmartPlayerView(MediaItem deviceItem, bool updateAccessibleName)
    {
        _frontierSmartSnapshots.TryGetValue(deviceItem.Id, out var snapshot);
        var title = snapshot is null
            ? deviceItem.Title
            : !string.IsNullOrWhiteSpace(snapshot.Title)
                ? snapshot.Title
                : !string.IsNullOrWhiteSpace(snapshot.Description)
                    ? snapshot.Description
                    : deviceItem.Title;
        var secondary = snapshot is null
            ? Array.Empty<string>()
            : new[] { snapshot.Artist, snapshot.Album, snapshot.Description }
                .Where(value => !string.IsNullOrWhiteSpace(value)
                    && !string.Equals(value, title, StringComparison.CurrentCultureIgnoreCase))
                .Distinct(StringComparer.CurrentCultureIgnoreCase)
                .ToArray();
        var state = snapshot?.PlaybackSummary ?? "stan jeszcze nieodświeżony";
        if (snapshot?.VolumePercent is { } volume) state += $", głośność {volume}%";

        PlayerTitleText.Text = title;
        PlayerArtistText.Text = secondary.Length > 0
            ? string.Join(", ", secondary)
            : "Urządzenie Frontier Smart";
        PlayerSessionText.Text = $"Frontier Smart, {deviceItem.Title}";
        PlayerStateText.Text = state;
        UpdatePlayerVolumePresentation(snapshot?.VolumePercent);
        PlayerSpeedText.Visibility = Visibility.Collapsed;
        PlayerPreviousButton.Content = "Poprzedni element";
        PlayerNextButton.Content = "Następny element";
        foreach (var control in new FrameworkElement[]
                 {
                     PlayerRateDownButton,
                     PlayerRateUpButton,
                     PlayerRateResetButton,
                     PlayerAddBookmarkButton,
                     PlayerAddNamedBookmarkButton,
                     PlayerBookmarksButton
                 })
        {
            control.Visibility = Visibility.Collapsed;
        }
        PlayerSeekTimeButton.Visibility = Visibility.Collapsed;
        PlayerSeekPercentButton.Visibility = Visibility.Collapsed;
        PlayerTimeText.Text = snapshot is null
            ? "Stan czasu nieznany"
            : snapshot.Duration is { } total && total > TimeSpan.Zero
                ? $"{CommandRouter.FormatTime(snapshot.Position ?? TimeSpan.Zero)} z {CommandRouter.FormatTime(total)}"
                : snapshot.Position is { } position
                    ? CommandRouter.FormatTime(position)
                    : "Czas niedostępny";
        RadioRecordingButton.Visibility = Visibility.Collapsed;
        PlayerHelpText.Text = PlayerKeyboardHelpText();
        PlayerPlayPauseButton.Content = snapshot?.PlaybackControl == (int)FrontierSmartPlaybackCommand.Play
            ? "Wstrzymaj"
            : "Odtwórz";
        if (!updateAccessibleName) return;
        _playerFocusContextPrefix = null;
        AutomationProperties.SetName(
            PlayerPlayPauseButton,
            snapshot?.IsMuted == true ? $"{title}, wyciszone" : title);
        ApplyPlayerHelpTextToControl();
    }

    private void AnnounceFrontierSmartTime(string commandId)
    {
        if (!TryGetActiveFrontierSmartContext(out _, out _, out var snapshot) || snapshot is null)
        {
            Announce("Stan urządzenia nie jest jeszcze odświeżony");
            return;
        }
        var value = commandId switch
        {
            CommandIds.TimeElapsed => snapshot.Position,
            CommandIds.TimeRemaining when snapshot.Duration is { } duration && snapshot.Position is { } position => duration - position,
            CommandIds.TimeTotal => snapshot.Duration,
            _ => null
        };
        Announce(value is { } time && time >= TimeSpan.Zero
            ? CommandRouter.FormatTime(time)
            : "Czas jest niedostępny w bieżącym trybie urządzenia");
    }

    private void AnnounceFrontierSmartCommandResult(string commandId, FrontierSmartSnapshot snapshot)
    {
        if (commandId is CommandIds.VolumeUp5 or CommandIds.VolumeDown5 or CommandIds.VolumeUp1 or CommandIds.VolumeDown1)
        {
            if (snapshot.VolumePercent is { } volume) Announce($"{volume}%");
            return;
        }
        if (commandId == CommandIds.ToggleMuteCurrentSession)
        {
            Announce(snapshot.IsMuted == true ? "Wyciszono urządzenie" : "Przywrócono dźwięk urządzenia");
            return;
        }
        if (_state.Settings.Messages.PlaybackMessages) Announce(snapshot.PlaybackSummary);
    }

    private void RestoreFrontierSmartFocus()
    {
        if (_playerViewActive) Dispatcher.BeginInvoke(FocusPlayerView, DispatcherPriority.ContextIdle);
        else RestoreMediaListFocusAfterRefresh();
    }

    private static bool IsFrontierSmartTransportCommand(string commandId) => commandId is
        CommandIds.PlayPause or CommandIds.Previous or CommandIds.Next
        or CommandIds.VolumeUp5 or CommandIds.VolumeDown5
        or CommandIds.VolumeUp1 or CommandIds.VolumeDown1
        or CommandIds.ToggleMuteCurrentSession
        or CommandIds.TrackStart or CommandIds.TrackEnd;

    private static bool CommandAvailableInFrontierSmart(string commandId) =>
        IsTransientPreviewCommand(commandId)
        || CommandIds.TryParseRadioPreset(commandId, out _)
        || commandId.StartsWith("session.", StringComparison.Ordinal)
        || commandId.StartsWith("settings.", StringComparison.Ordinal)
        || commandId is CommandIds.ActivateSelected
            or CommandIds.PlayPause
            or CommandIds.Previous
            or CommandIds.Next
            or CommandIds.VolumeUp5
            or CommandIds.VolumeDown5
            or CommandIds.VolumeUp1
            or CommandIds.VolumeDown1
            or CommandIds.ToggleMuteCurrentSession
            or CommandIds.TrackStart
            or CommandIds.TrackEnd
            or CommandIds.TimeElapsed
            or CommandIds.TimeRemaining
            or CommandIds.TimeTotal
            or CommandIds.ItemProperties
            or CommandIds.CurrentBroadcastInformation
            or CommandIds.FilterCurrent
            or CommandIds.SearchCurrent
            or CommandIds.SearchAll
            or CommandIds.CommandPalette
            or CommandIds.Help
            or CommandIds.ContextHelp
            or CommandIds.KeyboardHelp
            or CommandIds.ManageFrontierSmartDevices
            or CommandIds.RefreshFrontierSmartDevices
            or CommandIds.ViewFrontierSmartModes
            or CommandIds.ViewFrontierSmartPresets
            or CommandIds.ViewRadioPresets
            or CommandIds.SelectAudioOutput;

    private static bool IsFrontierSmartConnectionFailure(Exception exception) => exception is
        FrontierSmartProtocolException or HttpRequestException or TaskCanceledException
        or IOException or SocketException or FormatException or ArgumentException;
}
