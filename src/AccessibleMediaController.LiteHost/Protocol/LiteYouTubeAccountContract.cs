using System.Text.Json;
using System.Text.Json.Serialization;
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
    internal const string BroadcastsOperation = "youtube.channelBroadcasts";

    internal static LiteYouTubeBroadcastRequest ReadBroadcastRequest(JsonElement args)
    {
        if (args.ValueKind != JsonValueKind.Object
            || !args.TryGetProperty("subscriptionId", out var idValue)
            || idValue.ValueKind != JsonValueKind.String)
            throw new LiteRequestException("Wybierz kanał YouTube z Biblioteki.");
        var subscriptionId = idValue.GetString()?.Trim() ?? string.Empty;
        if (subscriptionId.Length is < 1 or > 512)
            throw new LiteRequestException("Wybierz kanał YouTube z Biblioteki.");
        var forceRefresh = false;
        if (args.TryGetProperty("refresh", out var refresh))
            forceRefresh = refresh.ValueKind switch
            {
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                _ => throw new LiteRequestException(
                    "Wybór odświeżenia transmisji musi mieć wartość tak albo nie.")
            };
        return new LiteYouTubeBroadcastRequest(subscriptionId, forceRefresh);
    }

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

    internal static LiteYouTubeBroadcastList CreateBroadcasts(
        IReadOnlyList<YouTubeBroadcast> rows)
    {
        ArgumentNullException.ThrowIfNull(rows);
        return new LiteYouTubeBroadcastList(
            rows.Select(row => new LiteYouTubeBroadcast(
                CleanLabel(row.Title),
                CleanLabel(row.ChannelTitle),
                row.PageUri.AbsoluteUri,
                row.State == YouTubeBroadcastState.Live ? "live" : "upcoming",
                row.ScheduledStartUtc,
                row.ActualStartUtc)).ToArray(),
            rows.Count == 0
                ? "Brak trwających i zaplanowanych transmisji."
                : $"Transmisje: {rows.Count}.");
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
    [property: JsonPropertyName("available")] bool Available,
    [property: JsonPropertyName("readOnly")] bool ReadOnly,
    [property: JsonPropertyName("separateProfileCredentials")] bool SeparateProfileCredentials,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeAccountState(
    [property: JsonPropertyName("connected")] bool Connected,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeAccountActionResult(
    [property: JsonPropertyName("succeeded")] bool Succeeded,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeSyncPreviewResult(
    [property: JsonPropertyName("additions")] int Additions,
    [property: JsonPropertyName("restores")] int Restores,
    [property: JsonPropertyName("alreadyPresent")] int AlreadyPresent,
    [property: JsonPropertyName("suppressed")] int Suppressed,
    [property: JsonPropertyName("duplicates")] int Duplicates,
    [property: JsonPropertyName("invalid")] int Invalid,
    [property: JsonPropertyName("channelLabels")] IReadOnlyList<string> ChannelLabels,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeSyncApplyResult(
    [property: JsonPropertyName("added")] int Added,
    [property: JsonPropertyName("restored")] int Restored,
    [property: JsonPropertyName("alreadyPresent")] int AlreadyPresent,
    [property: JsonPropertyName("suppressed")] int Suppressed,
    [property: JsonPropertyName("duplicates")] int Duplicates,
    [property: JsonPropertyName("invalid")] int Invalid,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeBroadcastRequest(
    string SubscriptionId,
    bool ForceRefresh);

internal sealed record LiteYouTubeBroadcastList(
    [property: JsonPropertyName("items")] IReadOnlyList<LiteYouTubeBroadcast> Items,
    [property: JsonPropertyName("message")] string Message);

internal sealed record LiteYouTubeBroadcast(
    [property: JsonPropertyName("title")] string Title,
    [property: JsonPropertyName("channelTitle")] string ChannelTitle,
    [property: JsonPropertyName("pageUrl")] string PageUrl,
    [property: JsonPropertyName("state")] string State,
    [property: JsonPropertyName("scheduledStartUtc")] DateTimeOffset? ScheduledStartUtc,
    [property: JsonPropertyName("actualStartUtc")] DateTimeOffset? ActualStartUtc);
