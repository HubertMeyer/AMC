using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Wąski, atomowy zapis jednej sekcji konta w profilu używanym przez LiteHost.
/// Nie ładuje i nie zapisuje całego modelu AMC, dzięki czemu logowanie nie
/// może nadpisać równoległych ustawień radia, harmonogramów ani sesji.
/// </summary>
internal static class LiteAccountSettingsStore
{
    private static readonly object Gate = new();
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Converters = { new JsonStringEnumConverter() }
    };

    public static void UpdateSection<T>(string statePath, string sectionName, T settings)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(statePath);
        ArgumentException.ThrowIfNullOrWhiteSpace(sectionName);
        ArgumentNullException.ThrowIfNull(settings);

        lock (Gate)
        {
            var path = Path.GetFullPath(statePath);
            if (!File.Exists(path))
                throw new InvalidOperationException("Nie znaleziono profilu AMC.");

            JsonObject root;
            try
            {
                using var stream = new FileStream(
                    path,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete);
                root = JsonNode.Parse(stream) as JsonObject
                    ?? throw new InvalidOperationException("Profil AMC jest uszkodzony.");
            }
            catch (JsonException exception)
            {
                throw new InvalidOperationException("Profil AMC jest uszkodzony.", exception);
            }

            var fresh = JsonSerializer.SerializeToNode(settings, JsonOptions) as JsonObject
                ?? throw new InvalidOperationException("Nie można przygotować ustawień konta do zapisu.");
            var section = FindObject(root, sectionName) ?? new JsonObject();
            foreach (var property in fresh)
                section[property.Key] = property.Value?.DeepClone();
            root[ExistingPropertyName(root, sectionName) ?? sectionName] = section;

            var directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrWhiteSpace(directory)) Directory.CreateDirectory(directory);
            var temporaryPath = path + ".account.tmp";
            File.WriteAllText(temporaryPath, root.ToJsonString(JsonOptions));
            if (File.Exists(path))
                File.Replace(temporaryPath, path, path + ".bak", true);
            else
                File.Move(temporaryPath, path);
        }
    }

    private static JsonObject? FindObject(JsonObject root, string name)
    {
        var existing = ExistingPropertyName(root, name);
        return existing is null ? null : root[existing] as JsonObject;
    }

    private static string? ExistingPropertyName(JsonObject root, string name) =>
        root.Select(property => property.Key).FirstOrDefault(key =>
            string.Equals(key, name, StringComparison.OrdinalIgnoreCase));
}
