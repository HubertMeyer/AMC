using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Wspólny dla AMC i AMC Test aktualizator składników multimedialnych.
/// Same binaria są współdzielone, ale ustawienie automatycznej kontroli jest
/// odczytywane z profilu procesu. Żaden token ani baza profilu nie jest tu
/// kopiowana pomiędzy wydaniami.
/// </summary>
internal sealed class LiteComponentUpdateCoordinator
{
    internal const string StatusOperation = "components.status";
    internal const string UpdateOperation = "components.update";
    internal const string AutomaticOperation = "components.updateAutomatic";

    private readonly string? _statePath;

    internal LiteComponentUpdateCoordinator(string? statePath)
    {
        _statePath = statePath;
    }

    internal IReadOnlyDictionary<string, Func<LiteRequest, LiteEventSink, object?>> Handlers() =>
        new Dictionary<string, Func<LiteRequest, LiteEventSink, object?>>(StringComparer.Ordinal)
        {
            [StatusOperation] = (_, _) => Status(performed: false, changed: false, success: true,
                "Odczytano stan składników."),
            [UpdateOperation] = (_, _) => Update(manual: true),
            [AutomaticOperation] = (_, _) => Update(manual: false)
        };

    private object Update(bool manual)
    {
        var policy = LiteComponentUpdatePolicy.Read(_statePath);
        if (!manual && !policy.CheckAutomatically)
        {
            return Status(
                performed: false,
                changed: false,
                success: true,
                "Automatyczne sprawdzanie składników jest wyłączone.");
        }

        var now = DateTimeOffset.UtcNow;
        var ffmpegBefore = FfmpegComponentManager.GetStatus();
        var ytDlpBefore = YtDlpComponentManager.GetStatus();
        var checkFfmpeg = manual || LiteComponentUpdatePolicy.IsDue(ffmpegBefore.CheckedAtUtc, now);
        var checkYtDlp = manual || LiteComponentUpdatePolicy.IsDue(ytDlpBefore.CheckedAtUtc, now);
        if (!checkFfmpeg && !checkYtDlp)
        {
            return Status(
                performed: false,
                changed: false,
                success: true,
                "Składniki były sprawdzane w ciągu ostatnich 24 godzin.");
        }

        var installAvailable = manual || policy.DownloadAutomatically;
        FfmpegComponentUpdateResult? ffmpegResult = null;
        YtDlpComponentUpdateResult? ytDlpResult = null;
        if (checkFfmpeg)
        {
            ffmpegResult = FfmpegComponentManager.CheckAndUpdateAsync(
                    installAvailable,
                    cancellationToken: CancellationToken.None)
                .GetAwaiter()
                .GetResult();
        }
        if (checkYtDlp)
        {
            ytDlpResult = YtDlpComponentManager.CheckAndUpdateAsync(
                    installAvailable,
                    cancellationToken: CancellationToken.None)
                .GetAwaiter()
                .GetResult();
        }

        var messages = new[] { ffmpegResult?.Message, ytDlpResult?.Message }
            .Where(static message => !string.IsNullOrWhiteSpace(message));
        return Status(
            performed: true,
            changed: (ffmpegResult?.Changed ?? false) || (ytDlpResult?.Changed ?? false),
            success: (ffmpegResult?.Success ?? true) && (ytDlpResult?.Success ?? true),
            string.Join(" ", messages));
    }

    private static object Status(bool performed, bool changed, bool success, string message)
    {
        var ffmpeg = FfmpegComponentManager.GetStatus();
        var ytDlp = YtDlpComponentManager.GetStatus();
        return new
        {
            success,
            performed,
            changed,
            complete = ffmpeg.Installed && ytDlp.Installed,
            ffmpegInstalled = ffmpeg.Installed,
            ytDlpInstalled = ytDlp.Installed,
            ffmpeg = ffmpeg.UserFacingText,
            ytDlp = ytDlp.UserFacingText,
            message
        };
    }
}
