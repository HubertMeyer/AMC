using System.Text.Json;
using AccessibleMediaController.Core.YouTube;

namespace AccessibleMediaController.LiteHost.Protocol;

internal static class LiteYouTubeAccountContract
{
    internal const string CapabilitiesOperation = "youtube.accountCapabilities";
    internal const string StatusOperation = "youtube.accountStatus";
    internal const string LoginOperation = "youtube.accountLogin";
    internal const string CancelLoginOperation = "youtube.accountCancelLogin";
    internal const string LogoutOperation = "youtube.accountLogout";
    internal const string SyncPreviewOperation = "youtube.subscriptionSyncPreview";
    internal const string SyncApplyOperation = "youtube.subscriptionSyncApply";

    internal static bool ReadRestoreSuppressed(JsonElement args)
    {
        if (args.ValueKind is JsonValueKind.Undefined or JsonValueKind.Null)
            return false;
        if (args.ValueKind != JsonValueKind.Object)
            throw new LiteRequestException("Nieprawidłowe ustawienia synchronizacji YouTube.");
        if (!args.TryGetProperty("restoreSuppressed", out var value)) return false;
        return value.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            _ => throw new LiteRequestException(
                "Wybór przywracania kanałów YouTube musi mieć wartość tak albo nie.")
        };
    }

    internal static LiteYouTubeSyncPreviewResult CreatePreview(
        YouTubeSubscriptionSyncPlan plan)
    {
        ArgumentNullException.ThrowIfNull(plan);
        var labels = plan.Actions
            .Select(action => CleanLabel(action.Title))
            .Take(200)
            .ToArray();
        var additions = plan.Actions.Count(action =>
            action.Kind == YouTubeSubscriptionSyncActionKind.Add);
        var restores = plan.Actions.Count - additions;
        var message = additions + restores == 0
            ? "Subskrypcje YouTube są już zgodne z Biblioteką AMC."
            : $"Do zapisania: nowe kanały {additions}, przywracane {restores}.";
        return new LiteYouTubeSyncPreviewResult(
            additions,
            restores,
            plan.AlreadyPresent,
            plan.Suppressed,
            plan.Duplicates,
            plan.Invalid,
            labels,
            message);
    }

    internal static LiteYouTubeSyncApplyResult CreateApply(
        YouTubeSubscriptionSyncApplyResult result)
    {
        ArgumentNullException.ThrowIfNull(result);
        var message = result.Changed == 0
            ? "Biblioteka AMC nie wymagała zmian."
            : $"Zapisano kanały YouTube: nowe {result.Added}, przywrócone {result.Restored}.";
        return new LiteYouTubeSyncApplyResult(
            result.Added,
            result.Restored,
            result.AlreadyPresent,
            result.Suppressed,
            result.Duplicates,
            result.Invalid,
            message);
    }

    private static string CleanLabel(string? value)
    {
        var normalized = string.Join(' ', (value ?? string.Empty)
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        if (normalized.Length == 0) return "Kanał YouTube";
        return normalized.Length <= 500 ? normalized : normalized[..500].Trim();
    }
}

internal sealed record LiteYouTubeAccountCapabilities(
    bool Available,
    bool ReadOnly,
    bool SeparateProfileCredentials,
    string Message);

internal sealed record LiteYouTubeAccountState(
    bool Connected,
    string Message);

internal sealed record LiteYouTubeAccountActionResult(
    bool Succeeded,
    string Message);

internal sealed record LiteYouTubeSyncPreviewResult(
    int Additions,
    int Restores,
    int AlreadyPresent,
    int Suppressed,
    int Duplicates,
    int Invalid,
    IReadOnlyList<string> ChannelLabels,
    string Message);

internal sealed record LiteYouTubeSyncApplyResult(
    int Added,
    int Restored,
    int AlreadyPresent,
    int Suppressed,
    int Duplicates,
    int Invalid,
    string Message);
