using System.ComponentModel;
using System.Globalization;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Devices.FrontierSmart;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

internal sealed class LiteFrontierSmartCoordinator : IDisposable
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = true
    };

    private readonly object gate = new();
    private readonly string statePath;
    private readonly FrontierSmartClient client;
    private readonly FrontierSmartDiscoveryService discovery;
    private readonly LiteFrontierSmartPinStore pins;

    public LiteFrontierSmartCoordinator(string statePath, string releaseProfile)
    {
        this.statePath = Path.GetFullPath(statePath);
        client = new FrontierSmartClient();
        discovery = new FrontierSmartDiscoveryService();
        pins = new LiteFrontierSmartPinStore(releaseProfile);
    }

    public object ListDevices()
    {
        lock (gate)
            return LiteFrontierSmartContract.CreateDevicesResult(ReadSettings());
    }

    public object Discover()
    {
        try
        {
            var addresses = discovery.DiscoverAddressesAsync(TimeSpan.FromSeconds(3))
                .GetAwaiter().GetResult();
            return new
            {
                items = addresses.Select(address => new
                {
                    address,
                    label = "Urządzenie pod adresem " + address
                }).ToArray(),
                message = addresses.Count == 0
                    ? "Nie wykryto urządzenia. Możesz wpisać lokalny adres IP ręcznie."
                    : addresses.Count == 1
                        ? "Wykryto jedno urządzenie."
                        : $"Wykryto urządzenia: {addresses.Count}."
            };
        }
        catch (Exception exception) when (IsExpectedFailure(exception))
        {
            throw new LiteRequestException(
                "Nie udało się wykryć urządzeń. Wpisz lokalny adres IP ręcznie.");
        }
    }

    public object AddOrUpdate(JsonElement args)
    {
        var address = LiteFrontierSmartContract.ReadAddress(args);
        var pin = LiteFrontierSmartContract.ReadPin(args);
        FrontierSmartSnapshot snapshot;
        try
        {
            snapshot = client.ReadSnapshotAsync(address, pin).GetAwaiter().GetResult();
        }
        catch (FrontierSmartProtocolException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (Exception exception) when (IsExpectedFailure(exception))
        {
            throw new LiteRequestException(
                "Urządzenie Frontier Smart nie odpowiedziało. Sprawdź adres, PIN i połączenie z tą samą siecią.");
        }

        lock (gate)
        {
            var settings = ReadSettings();
            var normalizedAddress = FrontierSmartAddressPolicy.Normalize(address);
            var deviceId = StableDeviceId(snapshot.RadioId, normalizedAddress);
            var existing = settings.Devices.FirstOrDefault(device =>
                string.Equals(device.Id, deviceId, StringComparison.OrdinalIgnoreCase)
                || string.Equals(device.Address, normalizedAddress, StringComparison.OrdinalIgnoreCase));
            var previousPin = string.Empty;
            var hadPreviousPin = existing is not null && pins.TryRead(existing.Id, out previousPin);
            var target = existing ?? new FrontierSmartDeviceSettings { Id = deviceId };
            target.Id = deviceId;
            target.Address = normalizedAddress;
            target.DisplayName = CleanName(snapshot.DisplayName);
            target.FirmwareVersion = CleanFirmware(snapshot.FirmwareVersion);
            target.LastSeenUtcTicks = DateTime.UtcNow.Ticks;
            if (existing is null) settings.Devices.Add(target);
            settings.SelectedDeviceId = target.Id;

            try
            {
                pins.Write(target.Id, pin);
                WriteSettings(settings);
            }
            catch (Exception exception) when (exception is IOException
                or UnauthorizedAccessException or JsonException or Win32Exception
                or LiteRequestException)
            {
                try
                {
                    if (hadPreviousPin) pins.Write(target.Id, previousPin);
                    else pins.Delete(target.Id);
                }
                catch
                {
                    // Raportujemy pierwotny błąd. PIN nadal nie trafia do profilu ani logu.
                }
                throw new LiteRequestException(
                    "Nie udało się bezpiecznie zapisać urządzenia Frontier Smart.");
            }
            finally
            {
                if (previousPin.Length > 0) previousPin = string.Empty;
            }

            return LiteFrontierSmartContract.CreateDevicesResult(
                settings,
                $"Zapisano i sprawdzono urządzenie {target.DisplayName}.");
        }
    }

    public object Remove(JsonElement args)
    {
        var deviceId = LiteFrontierSmartContract.ReadDeviceId(args);
        lock (gate)
        {
            var settings = ReadSettings();
            var device = ResolveDevice(settings, deviceId);
            settings.Devices.Remove(device);
            if (string.Equals(
                    settings.SelectedDeviceId, device.Id, StringComparison.OrdinalIgnoreCase))
            {
                settings.SelectedDeviceId = settings.Devices.FirstOrDefault()?.Id;
            }
            WriteSettings(settings);
            pins.Delete(device.Id);
            return LiteFrontierSmartContract.CreateDevicesResult(
                settings,
                $"Usunięto urządzenie {UserTitle(device)} z AMC.");
        }
    }

    public object Select(JsonElement args)
    {
        var deviceId = LiteFrontierSmartContract.ReadDeviceId(args);
        lock (gate)
        {
            var settings = ReadSettings();
            var device = ResolveDevice(settings, deviceId);
            settings.SelectedDeviceId = device.Id;
            WriteSettings(settings);
            return LiteFrontierSmartContract.CreateDevicesResult(
                settings,
                $"Wybrano urządzenie {UserTitle(device)}.");
        }
    }

    public object Snapshot(JsonElement args)
    {
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(
                ReadSettings(), LiteFrontierSmartContract.ReadDeviceId(args));
            return LiteFrontierSmartContract.CreateSnapshotResult(
                device, ReadSnapshot(device, pin));
        }
    }

    public object Transport(JsonElement args)
    {
        var deviceId = LiteFrontierSmartContract.ReadDeviceId(args);
        var command = LiteFrontierSmartContract.ReadTransportCommand(args);
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(ReadSettings(), deviceId);
            try
            {
                var before = ReadSnapshot(device, pin);
                var message = command switch
                {
                    "toggle" => TogglePlayback(device, pin, before),
                    "previous" => SendPlayback(device, pin, FrontierSmartPlaybackCommand.Previous, "Poprzedni element"),
                    "next" => SendPlayback(device, pin, FrontierSmartPlaybackCommand.Next, "Następny element"),
                    "toggleMute" => SetMuted(device, pin, before.IsMuted != true),
                    "togglePower" => SetPower(device, pin, before.IsPoweredOn != true),
                    _ => SetVolume(device, pin, before, RequestedVolume(args, command, before))
                };
                Thread.Sleep(TimeSpan.FromMilliseconds(160));
                return LiteFrontierSmartContract.CreateSnapshotResult(
                    device, ReadSnapshot(device, pin), message);
            }
            catch (LiteRequestException)
            {
                throw;
            }
            catch (FrontierSmartProtocolException exception)
            {
                throw new LiteRequestException(exception.Message);
            }
            catch (Exception exception) when (IsExpectedFailure(exception))
            {
                throw new LiteRequestException(
                    $"Nie udało się sterować urządzeniem {UserTitle(device)}.");
            }
        }
    }

    public object Modes(JsonElement args)
    {
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(
                ReadSettings(), LiteFrontierSmartContract.ReadDeviceId(args));
            try
            {
                var snapshot = ReadSnapshot(device, pin);
                var modes = client.ReadModesAsync(device.Address, pin)
                    .GetAwaiter().GetResult();
                return LiteFrontierSmartContract.CreateModesResult(device, snapshot, modes);
            }
            catch (LiteRequestException)
            {
                throw;
            }
            catch (Exception exception) when (IsExpectedFailure(exception))
            {
                throw new LiteRequestException(
                    "Urządzenie nie udostępniło listy trybów.");
            }
        }
    }

    public object SetMode(JsonElement args)
    {
        var deviceId = LiteFrontierSmartContract.ReadDeviceId(args);
        var key = LiteFrontierSmartContract.ReadKey(
            args, "modeKey", "Nie wskazano trybu Frontier Smart.");
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(ReadSettings(), deviceId);
            try
            {
                var modes = client.ReadModesAsync(device.Address, pin)
                    .GetAwaiter().GetResult();
                var mode = modes.FirstOrDefault(candidate => candidate.Key == key);
                if (mode is null || !mode.Selectable)
                    throw new LiteRequestException(
                        "Wybrany tryb nie jest dostępny w tym urządzeniu.");
                client.SetModeAsync(device.Address, pin, key).GetAwaiter().GetResult();
                Thread.Sleep(TimeSpan.FromMilliseconds(300));
                return LiteFrontierSmartContract.CreateSnapshotResult(
                    device,
                    ReadSnapshot(device, pin),
                    $"Wybrano tryb {mode.DisplayName}.");
            }
            catch (LiteRequestException)
            {
                throw;
            }
            catch (Exception exception) when (IsExpectedFailure(exception))
            {
                throw new LiteRequestException("Nie udało się zmienić trybu urządzenia.");
            }
        }
    }

    public object Presets(JsonElement args)
    {
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(
                ReadSettings(), LiteFrontierSmartContract.ReadDeviceId(args));
            try
            {
                var presets = client.ReadPresetsAsync(device.Address, pin)
                    .GetAwaiter().GetResult();
                return LiteFrontierSmartContract.CreatePresetsResult(device, presets);
            }
            catch (LiteRequestException)
            {
                throw;
            }
            catch (Exception exception) when (IsExpectedFailure(exception))
            {
                throw new LiteRequestException(
                    "Urządzenie nie udostępniło presetów w bieżącym trybie.");
            }
        }
    }

    public object ActivatePreset(JsonElement args)
    {
        var deviceId = LiteFrontierSmartContract.ReadDeviceId(args);
        var key = LiteFrontierSmartContract.ReadKey(
            args, "presetKey", "Nie wskazano presetu Frontier Smart.");
        lock (gate)
        {
            var (device, pin) = ResolveDeviceAndPin(ReadSettings(), deviceId);
            try
            {
                var presets = client.ReadPresetsAsync(device.Address, pin)
                    .GetAwaiter().GetResult();
                var preset = presets.FirstOrDefault(candidate => candidate.Key == key)
                    ?? throw new LiteRequestException(
                        "Wybrany preset nie jest już dostępny w urządzeniu.");
                client.ActivatePresetAsync(device.Address, pin, key)
                    .GetAwaiter().GetResult();
                Thread.Sleep(TimeSpan.FromMilliseconds(300));
                return LiteFrontierSmartContract.CreateSnapshotResult(
                    device,
                    ReadSnapshot(device, pin),
                    $"Uruchomiono {preset.DisplayName}, preset {preset.Key + 1}.");
            }
            catch (LiteRequestException)
            {
                throw;
            }
            catch (Exception exception) when (IsExpectedFailure(exception))
            {
                throw new LiteRequestException("Nie udało się uruchomić presetu urządzenia.");
            }
        }
    }

    private string TogglePlayback(
        FrontierSmartDeviceSettings device,
        string pin,
        FrontierSmartSnapshot before)
    {
        var pause = before.PlaybackStatus == 2;
        client.SendPlaybackCommandAsync(
                device.Address,
                pin,
                pause ? FrontierSmartPlaybackCommand.Pause : FrontierSmartPlaybackCommand.Play)
            .GetAwaiter().GetResult();
        return pause ? "Pauza" : "Odtwarzanie";
    }

    private string SendPlayback(
        FrontierSmartDeviceSettings device,
        string pin,
        FrontierSmartPlaybackCommand command,
        string message)
    {
        client.SendPlaybackCommandAsync(device.Address, pin, command)
            .GetAwaiter().GetResult();
        return message;
    }

    private string SetMuted(FrontierSmartDeviceSettings device, string pin, bool muted)
    {
        client.SetMutedAsync(device.Address, pin, muted).GetAwaiter().GetResult();
        return muted ? "Wyciszono" : "Włączono dźwięk";
    }

    private string SetPower(FrontierSmartDeviceSettings device, string pin, bool poweredOn)
    {
        client.SetPowerAsync(device.Address, pin, poweredOn).GetAwaiter().GetResult();
        return poweredOn ? "Włączono urządzenie" : "Wyłączono urządzenie";
    }

    private string SetVolume(
        FrontierSmartDeviceSettings device,
        string pin,
        FrontierSmartSnapshot before,
        int volume)
    {
        if (before.VolumeStepCount is not { } steps || steps <= 1)
            throw new LiteRequestException(
                "Urządzenie nie podało liczby kroków głośności.");
        client.SetVolumeStepAsync(
                device.Address, pin, FrontierSmartVolume.FromPercent(volume, steps))
            .GetAwaiter().GetResult();
        return $"Głośność {volume}%";
    }

    private static int RequestedVolume(
        JsonElement args,
        string command,
        FrontierSmartSnapshot before)
    {
        if (command == "setVolume") return LiteFrontierSmartContract.ReadVolume(args);
        var delta = command switch
        {
            "volumeUp5" => 5,
            "volumeDown5" => -5,
            "volumeUp1" => 1,
            "volumeDown1" => -1,
            _ => throw new LiteRequestException("Nieznane polecenie głośności.")
        };
        return Math.Clamp((before.VolumePercent ?? 0) + delta, 0, 100);
    }

    private FrontierSmartSnapshot ReadSnapshot(
        FrontierSmartDeviceSettings device,
        string pin)
    {
        try
        {
            return client.ReadSnapshotAsync(device.Address, pin).GetAwaiter().GetResult();
        }
        catch (FrontierSmartProtocolException exception)
        {
            throw new LiteRequestException(exception.Message);
        }
        catch (Exception exception) when (IsExpectedFailure(exception))
        {
            throw new LiteRequestException(
                $"Brak odpowiedzi urządzenia {UserTitle(device)}.");
        }
    }

    private (FrontierSmartDeviceSettings Device, string Pin) ResolveDeviceAndPin(
        FrontierSmartSettings settings,
        string deviceId)
    {
        var device = ResolveDevice(settings, deviceId);
        if (!pins.TryRead(device.Id, out var pin))
            throw new LiteRequestException(
                "Brakuje zapisanego PIN-u. Otwórz Urządzenia Frontier Smart i zapisz urządzenie ponownie.");
        return (device, pin);
    }

    private static FrontierSmartDeviceSettings ResolveDevice(
        FrontierSmartSettings settings,
        string deviceId)
    {
        var device = settings.Devices.FirstOrDefault(candidate => string.Equals(
            candidate.Id, deviceId, StringComparison.OrdinalIgnoreCase));
        if (device is null)
            throw new LiteRequestException(
                "Nie można odnaleźć zapisanego urządzenia Frontier Smart.");
        if (!FrontierSmartAddressPolicy.TryNormalize(device.Address, out _))
            throw new LiteRequestException(
                "Zapisane urządzenie Frontier Smart ma nieprawidłowy adres.");
        return device;
    }

    private FrontierSmartSettings ReadSettings()
    {
        try
        {
            using var stream = new FileStream(
                statePath, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            using var document = JsonDocument.Parse(stream);
            if (document.RootElement.ValueKind != JsonValueKind.Object
                || !TryGetProperty(
                    document.RootElement, out var section, "frontierSmart", "FrontierSmart")
                || section.ValueKind != JsonValueKind.Object)
            {
                return new FrontierSmartSettings();
            }
            var settings = JsonSerializer.Deserialize<FrontierSmartSettings>(
                section.GetRawText(), JsonOptions) ?? new FrontierSmartSettings();
            settings.Devices = settings.Devices
                .Where(device => !string.IsNullOrWhiteSpace(device.Id)
                    && FrontierSmartAddressPolicy.TryNormalize(device.Address, out _))
                .DistinctBy(device => device.Id, StringComparer.OrdinalIgnoreCase)
                .ToList();
            if (settings.SelectedDeviceId is not null
                && settings.Devices.All(device => !string.Equals(
                    device.Id,
                    settings.SelectedDeviceId,
                    StringComparison.OrdinalIgnoreCase)))
            {
                settings.SelectedDeviceId = settings.Devices.FirstOrDefault()?.Id;
            }
            return settings;
        }
        catch (FileNotFoundException)
        {
            throw new LiteRequestException(
                "Nie znaleziono profilu AMC potrzebnego do obsługi Frontier Smart.");
        }
        catch (JsonException)
        {
            throw new LiteRequestException(
                "Profil AMC z urządzeniami Frontier Smart jest uszkodzony.");
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            throw new LiteRequestException(
                "Nie można teraz odczytać urządzeń Frontier Smart z profilu AMC.");
        }
    }

    private void WriteSettings(FrontierSmartSettings settings)
    {
        JsonObject root;
        try
        {
            root = JsonNode.Parse(File.ReadAllText(statePath)) as JsonObject
                ?? throw new JsonException();
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException or JsonException)
        {
            throw new LiteRequestException("Nie można odczytać profilu AMC do zapisu.");
        }

        root["frontierSmart"] = JsonSerializer.SerializeToNode(settings, JsonOptions);
        var temporaryPath = statePath + ".frontier-smart.tmp";
        var directory = Path.GetDirectoryName(statePath);
        if (string.IsNullOrWhiteSpace(directory))
            throw new LiteRequestException("Nie można ustalić folderu profilu AMC.");
        try
        {
            Directory.CreateDirectory(directory);
            File.WriteAllText(temporaryPath, root.ToJsonString(JsonOptions));
            if (File.Exists(statePath))
                File.Replace(temporaryPath, statePath, statePath + ".bak", true);
            else
                File.Move(temporaryPath, statePath);
        }
        finally
        {
            try
            {
                if (File.Exists(temporaryPath)) File.Delete(temporaryPath);
            }
            catch
            {
                // Nie maskuj wyniku właściwego zapisu.
            }
        }
    }

    private static string StableDeviceId(string radioId, string address)
    {
        var identity = string.IsNullOrWhiteSpace(radioId) ? address : radioId.Trim();
        var digest = SHA256.HashData(Encoding.UTF8.GetBytes(identity));
        return "fs-" + Convert.ToHexString(digest)[..24].ToLowerInvariant();
    }

    private static string CleanName(string? value)
    {
        var text = CleanText(value, 128);
        return text.Length > 0 ? text : "Urządzenie Frontier Smart";
    }

    private static string CleanFirmware(string? value) => CleanText(value, 128);

    private static string CleanText(string? value, int maximum)
    {
        var text = new string((value ?? string.Empty)
            .Trim()
            .Where(character => !char.IsControl(character))
            .ToArray());
        return text.Length > maximum ? text[..maximum] : text;
    }

    private static string UserTitle(FrontierSmartDeviceSettings device) =>
        string.IsNullOrWhiteSpace(device.DisplayName)
            ? "Urządzenie Frontier Smart"
            : device.DisplayName.Trim();

    private static bool IsExpectedFailure(Exception exception) =>
        exception is HttpRequestException or TaskCanceledException or IOException
            or FormatException or ArgumentException or SocketException
            or NetworkInformationException;

    private static bool TryGetProperty(
        JsonElement source,
        out JsonElement value,
        params string[] names)
    {
        if (source.ValueKind == JsonValueKind.Object)
        {
            foreach (var name in names)
                if (source.TryGetProperty(name, out value)) return true;
        }
        value = default;
        return false;
    }

    public void Dispose() => client.Dispose();
}
