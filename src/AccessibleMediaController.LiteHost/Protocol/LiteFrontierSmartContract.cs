using System.Globalization;
using System.Text.Json;
using AccessibleMediaController.Core.Devices.FrontierSmart;

namespace AccessibleMediaController.LiteHost.Protocol;

public static class LiteFrontierSmartContract
{
    public const string DevicesOperation = "frontierSmart.devices";
    public const string DiscoverOperation = "frontierSmart.discover";
    public const string AddOperation = "frontierSmart.add";
    public const string RemoveOperation = "frontierSmart.remove";
    public const string SelectOperation = "frontierSmart.select";
    public const string SnapshotOperation = "frontierSmart.snapshot";
    public const string TransportOperation = "frontierSmart.transport";
    public const string ModesOperation = "frontierSmart.modes";
    public const string SetModeOperation = "frontierSmart.modeSet";
    public const string PresetsOperation = "frontierSmart.presets";
    public const string ActivatePresetOperation = "frontierSmart.presetActivate";

    public static string ReadDeviceId(JsonElement args) =>
        LiteArgs.RequireText(args, "deviceId").Trim();

    public static string ReadAddress(JsonElement args) =>
        LiteArgs.RequireText(args, "address").Trim();

    public static string ReadPin(JsonElement args) =>
        LiteArgs.RequireText(args, "pin").Trim();

    public static string ReadTransportCommand(JsonElement args)
    {
        var command = LiteArgs.RequireText(args, "command").Trim();
        if (command is not (
                "toggle" or "previous" or "next" or "setVolume"
                or "volumeUp5" or "volumeDown5" or "volumeUp1" or "volumeDown1"
                or "toggleMute" or "togglePower"))
        {
            throw new LiteRequestException(
                "Nieznane polecenie sterowania urządzeniem Frontier Smart.");
        }
        return command;
    }

    public static int ReadVolume(JsonElement args)
    {
        if (!args.TryGetProperty("volume", out var raw)
            || raw.ValueKind != JsonValueKind.Number
            || !raw.TryGetInt32(out var volume)
            || volume is < 0 or > 100)
        {
            throw new LiteRequestException("Głośność musi być liczbą od 0 do 100.");
        }
        return volume;
    }

    public static uint ReadKey(JsonElement args, string property, string message)
    {
        if (!args.TryGetProperty(property, out var raw)
            || raw.ValueKind != JsonValueKind.Number
            || !raw.TryGetUInt32(out var key))
        {
            throw new LiteRequestException(message);
        }
        return key;
    }

    public static object CreateDevicesResult(FrontierSmartSettings settings, string? message = null)
    {
        var selected = settings.SelectedDeviceId;
        var items = settings.Devices
            .Where(device => device.Id.Length > 0
                && FrontierSmartAddressPolicy.TryNormalize(device.Address, out _))
            .Select(device => new
            {
                itemId = "frontier-smart:" + device.Id,
                deviceId = device.Id,
                title = UserTitle(device),
                detail = string.IsNullOrWhiteSpace(device.FirmwareVersion)
                    ? "Radio zgodne z FSAPI"
                    : "Firmware " + Clean(device.FirmwareVersion),
                selected = string.Equals(
                    device.Id, selected, StringComparison.OrdinalIgnoreCase)
            })
            .ToArray();
        return new { items, selectedDeviceId = selected ?? string.Empty, message = message ?? string.Empty };
    }

    public static object CreateSnapshotResult(
        FrontierSmartDeviceSettings device,
        FrontierSmartSnapshot snapshot,
        string? message = null)
    {
        var title = FirstUseful(snapshot.Title, snapshot.Description, snapshot.DisplayName, UserTitle(device));
        var subtitle = FirstUseful(snapshot.Artist, snapshot.Album, snapshot.Description);
        var playbackState = snapshot.IsPoweredOn == false
            ? "wyłączone"
            : snapshot.PlaybackStatus switch
            {
                1 => "buforowanie",
                2 => "odtwarzanie",
                3 => "pauza",
                _ => snapshot.IsPoweredOn == true ? "włączone" : "stan nieznany"
            };
        return new
        {
            itemId = "frontier-smart:" + device.Id,
            deviceId = device.Id,
            deviceTitle = UserTitle(device),
            title,
            subtitle,
            artist = Clean(snapshot.Artist),
            album = Clean(snapshot.Album),
            playbackState,
            poweredOn = snapshot.IsPoweredOn,
            volume = snapshot.VolumePercent,
            muted = snapshot.IsMuted == true,
            modeKey = snapshot.ModeIndex,
            positionSeconds = snapshot.Position?.TotalSeconds,
            durationSeconds = snapshot.Duration is { } duration && duration > TimeSpan.Zero
                ? duration.TotalSeconds
                : (double?)null,
            message = string.IsNullOrWhiteSpace(message)
                ? SnapshotMessage(title, playbackState, snapshot)
                : message.Trim()
        };
    }

    public static object CreateModesResult(
        FrontierSmartDeviceSettings device,
        FrontierSmartSnapshot snapshot,
        IReadOnlyList<FrontierSmartMode> modes)
    {
        var items = modes.Select(mode => new
        {
            key = mode.Key,
            value = mode.Key.ToString(CultureInfo.InvariantCulture),
            label = Clean(mode.AccessibleLabel),
            selected = snapshot.ModeIndex == mode.Key,
            enabled = mode.Selectable
        }).ToArray();
        return new
        {
            deviceId = device.Id,
            deviceTitle = UserTitle(device),
            selectedKey = snapshot.ModeIndex,
            items
        };
    }

    public static object CreatePresetsResult(
        FrontierSmartDeviceSettings device,
        IReadOnlyList<FrontierSmartPreset> presets)
    {
        var items = presets.Select(preset => new
        {
            itemId = $"frontier-smart-preset:{preset.Key}",
            presetKey = preset.Key,
            label = Clean(preset.AccessibleLabel),
            name = Clean(preset.DisplayName)
        }).ToArray();
        return new { deviceId = device.Id, deviceTitle = UserTitle(device), items };
    }

    private static string SnapshotMessage(
        string title,
        string playbackState,
        FrontierSmartSnapshot snapshot)
    {
        var parts = new List<string> { title, playbackState };
        if (snapshot.IsMuted == true) parts.Add("wyciszone");
        if (snapshot.VolumePercent is { } volume) parts.Add($"głośność {volume}%");
        return string.Join(", ", parts.Where(value => value.Length > 0));
    }

    private static string UserTitle(FrontierSmartDeviceSettings device) =>
        Clean(device.DisplayName).Length > 0
            ? Clean(device.DisplayName)
            : "Urządzenie Frontier Smart";

    private static string FirstUseful(params string?[] values) =>
        values.Select(Clean).FirstOrDefault(value => value.Length > 0)
        ?? "Urządzenie Frontier Smart";

    private static string Clean(string? value)
    {
        var text = (value ?? string.Empty).Trim();
        if (text.Length > 240) text = text[..240];
        return new string(text.Where(character => !char.IsControl(character)).ToArray());
    }
}

public sealed class FrontierSmartSettings
{
    public List<FrontierSmartDeviceSettings> Devices { get; set; } = [];
    public string? SelectedDeviceId { get; set; }
}

public sealed class FrontierSmartDeviceSettings
{
    public string Id { get; set; } = string.Empty;
    public string Address { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string FirmwareVersion { get; set; } = string.Empty;
    public long LastSeenUtcTicks { get; set; }
}
