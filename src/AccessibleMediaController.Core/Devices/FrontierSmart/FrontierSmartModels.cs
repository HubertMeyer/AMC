using System.Globalization;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public static class FrontierSmartNodes
{
    public const string FriendlyName = "netRemote.sys.info.friendlyName";
    public const string RadioId = "netRemote.sys.info.radioId";
    public const string FirmwareVersion = "netRemote.sys.info.version";
    public const string Power = "netRemote.sys.power";
    public const string Volume = "netRemote.sys.audio.volume";
    public const string VolumeSteps = "netRemote.sys.caps.volumeSteps";
    public const string Mute = "netRemote.sys.audio.mute";
    public const string Mode = "netRemote.sys.mode";
    public const string ValidModes = "netRemote.sys.caps.validModes";
    public const string PlaybackControl = "netRemote.play.control";
    public const string PlayName = "netRemote.play.info.name";
    public const string PlayText = "netRemote.play.info.text";
    public const string PlayArtist = "netRemote.play.info.artist";
    public const string PlayAlbum = "netRemote.play.info.album";
    public const string PlayDuration = "netRemote.play.info.duration";
    public const string PlayPosition = "netRemote.play.position";
    public const string Presets = "netRemote.nav.presets";
    public const string SelectPreset = "netRemote.nav.action.selectPreset";
}

public sealed record FrontierSmartValue(
    string Node,
    string Status,
    string? ValueType,
    string? Value)
{
    public bool Success => string.Equals(Status, "FS_OK", StringComparison.Ordinal);

    public int? AsInt32()
    {
        return int.TryParse(Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var result)
            ? result
            : null;
    }

    public uint? AsUInt32()
    {
        return uint.TryParse(Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out var result)
            ? result
            : null;
    }

    public bool? AsBoolean()
    {
        return AsInt32() switch
        {
            0 => false,
            1 => true,
            _ => null
        };
    }
}

public sealed record FrontierSmartMode(
    uint Key,
    string Id,
    string DisplayName,
    bool Selectable,
    bool Streamable,
    uint ModeType)
{
    public string AccessibleLabel => Selectable
        ? DisplayName
        : $"{DisplayName}, niedostępny do bezpośredniego wyboru";

    public string NavigationText => DisplayName;

    public override string ToString() => AccessibleLabel;
}

public sealed record FrontierSmartPreset(uint Key, string DisplayName)
{
    public string AccessibleLabel => $"{DisplayName}, preset {Key + 1}";

    public string NavigationText => DisplayName;

    public override string ToString() => AccessibleLabel;
}

public sealed record FrontierSmartIdentity(
    string DisplayName,
    string RadioId,
    string FirmwareVersion);

public sealed record FrontierSmartSnapshot(
    string DisplayName,
    string RadioId,
    string FirmwareVersion,
    bool? IsPoweredOn,
    int? VolumeStep,
    int? VolumeStepCount,
    bool? IsMuted,
    uint? ModeIndex,
    int? PlaybackControl,
    string Title,
    string Description,
    string Artist,
    string Album,
    TimeSpan? Duration,
    TimeSpan? Position)
{
    public int? VolumePercent => FrontierSmartVolume.ToPercent(VolumeStep, VolumeStepCount);

    public string PlaybackSummary
    {
        get
        {
            var state = IsPoweredOn switch
            {
                false => "wyłączone",
                true when IsMuted == true => "włączone, wyciszone",
                true => "włączone",
                _ => "stan zasilania nieznany"
            };
            var item = string.IsNullOrWhiteSpace(Title) ? Description : Title;
            return string.IsNullOrWhiteSpace(item) ? state : $"{state}, {item}";
        }
    }
}

public enum FrontierSmartPlaybackCommand
{
    Play = 1,
    Pause = 2,
    Next = 3,
    Previous = 4
}

public static class FrontierSmartVolume
{
    public static int? ToPercent(int? step, int? stepCount)
    {
        if (step is null || stepCount is null || stepCount <= 1) return null;
        var maximumStep = stepCount.Value - 1;
        var boundedStep = Math.Clamp(step.Value, 0, maximumStep);
        return (int)Math.Round(
            boundedStep * 100d / maximumStep,
            MidpointRounding.AwayFromZero);
    }

    public static int FromPercent(int percent, int stepCount)
    {
        if (stepCount <= 1) throw new ArgumentOutOfRangeException(nameof(stepCount));
        var maximumStep = stepCount - 1;
        return (int)Math.Round(
            Math.Clamp(percent, 0, 100) * maximumStep / 100d,
            MidpointRounding.AwayFromZero);
    }

    public static string AccessibleLabel(int step, int stepCount)
    {
        var percent = ToPercent(step, stepCount)
            ?? throw new ArgumentOutOfRangeException(nameof(stepCount));
        return $"{percent} procent, krok {Math.Clamp(step, 0, stepCount - 1)} z {stepCount - 1}";
    }
}

public sealed class FrontierSmartProtocolException : IOException
{
    public FrontierSmartProtocolException(string message, string? status = null)
        : base(message)
    {
        Status = status;
    }

    public string? Status { get; }
}
