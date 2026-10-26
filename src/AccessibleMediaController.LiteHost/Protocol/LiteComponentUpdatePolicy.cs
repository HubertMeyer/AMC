using System.Text.Json;

namespace AccessibleMediaController.LiteHost.Protocol;

/// <summary>
/// Wąski, tylko do odczytu kontrakt ustawień aktualizacji składników.
/// LiteHost nie zapisuje całego profilu i nie uruchamia jego migracji.
/// </summary>
internal sealed record LiteComponentUpdatePolicy(
    bool CheckAutomatically,
    bool DownloadAutomatically)
{
    internal static LiteComponentUpdatePolicy Read(string? statePath)
    {
        // Świeży profil zachowuje dotychczasowe wartości domyślne AMC.
        var fallback = new LiteComponentUpdatePolicy(true, true);
        if (string.IsNullOrWhiteSpace(statePath) || !File.Exists(statePath)) return fallback;

        try
        {
            using var document = JsonDocument.Parse(File.ReadAllText(statePath));
            if (!TryGetProperty(document.RootElement, "Settings", out var settings)
                || !TryGetProperty(settings, "Updates", out var updates))
            {
                return fallback;
            }

            return new LiteComponentUpdatePolicy(
                ReadBoolean(updates, "CheckAutomatically", fallback.CheckAutomatically),
                ReadBoolean(updates, "DownloadAutomatically", fallback.DownloadAutomatically));
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or JsonException)
        {
            // Uszkodzony albo chwilowo zajęty profil nie może wyłączyć
            // składników potrzebnych świeżej instalacji.
            return fallback;
        }
    }

    internal static LiteComponentUpdatePolicy Resolve(string? statePath, JsonElement args)
    {
        var inherited = Read(statePath);
        return new LiteComponentUpdatePolicy(
            LiteArgs.ReadBool(args, "checkAutomatically", inherited.CheckAutomatically),
            LiteArgs.ReadBool(args, "downloadAutomatically", inherited.DownloadAutomatically));
    }

    internal static bool IsDue(DateTimeOffset? checkedAtUtc, DateTimeOffset nowUtc) =>
        checkedAtUtc is not { } checkedAt
        || checkedAt < nowUtc.Subtract(TimeSpan.FromHours(24));

    private static bool ReadBoolean(JsonElement owner, string name, bool fallback)
    {
        return TryGetProperty(owner, name, out var value)
            && value.ValueKind is JsonValueKind.True or JsonValueKind.False
                ? value.GetBoolean()
                : fallback;
    }

    private static bool TryGetProperty(JsonElement owner, string name, out JsonElement value)
    {
        if (owner.ValueKind == JsonValueKind.Object)
        {
            foreach (var property in owner.EnumerateObject())
            {
                if (string.Equals(property.Name, name, StringComparison.OrdinalIgnoreCase))
                {
                    value = property.Value;
                    return true;
                }
            }
        }
        value = default;
        return false;
    }
}
