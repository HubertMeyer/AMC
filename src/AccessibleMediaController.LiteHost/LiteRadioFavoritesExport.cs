using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Radio;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteRadioFavoritesExportResult(
    [property: JsonPropertyName("exportedCount")] int ExportedCount);

/// <summary>
/// Buduje przenośny eksport Ulubionych radia z profilu AMC. Do pliku trafia
/// wyłącznie nazwa widoczna dla użytkownika i stabilny adres HTTP(S), nigdy
/// identyfikator AMC ani chwilowy adres rozwiązany przez odtwarzacz.
/// </summary>
internal static class LiteRadioFavoritesExport
{
    public static IReadOnlyList<RadioFavoritePlaylistEntry> SelectEntries(
        JsonObject root,
        IReadOnlyList<string> customOrder,
        IReadOnlyList<string> addedOrder)
    {
        ArgumentNullException.ThrowIfNull(root);
        ArgumentNullException.ThrowIfNull(customOrder);
        ArgumentNullException.ThrowIfNull(addedOrder);

        if (root["radio"]?["stations"] is not JsonArray stations) return [];
        var candidates = stations
            .OfType<JsonObject>()
            .Select((station, index) => ReadCandidate(station, index))
            .Where(candidate => candidate is not null)
            .Cast<Candidate>()
            .ToArray();

        return ReadSortMode(root) switch
        {
            RadioFavoritesSortMode.Alphabetical => candidates
                .OrderBy(candidate => candidate.Name, StringComparer.CurrentCultureIgnoreCase)
                .ThenBy(candidate => candidate.Id, StringComparer.Ordinal)
                .Select(ToEntry)
                .ToArray(),
            RadioFavoritesSortMode.Custom => Order(candidates, customOrder)
                .Select(ToEntry)
                .ToArray(),
            _ => Order(candidates, addedOrder)
                .Reverse()
                .Select(ToEntry)
                .ToArray()
        };
    }

    public static LiteRadioFavoritesExportResult Write(
        JsonObject root,
        IReadOnlyList<string> customOrder,
        IReadOnlyList<string> addedOrder,
        string destinationPath)
    {
        var entries = SelectEntries(root, customOrder, addedOrder);
        if (entries.Count == 0)
            throw new InvalidDataException(
                "Ulubione nie zawierają stacji, które można wyeksportować");

        var destination = Path.GetFullPath(destinationPath);
        var directory = Path.GetDirectoryName(destination)
            ?? throw new IOException("Nie można ustalić folderu docelowego.");
        var temporary = Path.Combine(
            directory,
            $".{Path.GetFileName(destination)}.{Guid.NewGuid():N}.tmp");
        try
        {
            var bytes = string.Equals(
                Path.GetExtension(destination), ".json", StringComparison.OrdinalIgnoreCase)
                ? RadioFavoritesPlaylistWriter.WriteVRadioJson(entries)
                : RadioFavoritesPlaylistWriter.Write(entries);
            using (var output = new FileStream(
                       temporary,
                       FileMode.CreateNew,
                       FileAccess.Write,
                       FileShare.None,
                       bufferSize: 16_384,
                       FileOptions.WriteThrough))
            {
                output.Write(bytes);
                output.Flush(flushToDisk: true);
            }
            File.Move(temporary, destination, overwrite: true);
            temporary = string.Empty;
            return new LiteRadioFavoritesExportResult(entries.Count);
        }
        finally
        {
            if (temporary.Length > 0)
            {
                try { File.Delete(temporary); }
                catch (Exception exception) when (exception is IOException
                    or UnauthorizedAccessException) { }
            }
        }
    }

    private static Candidate? ReadCandidate(JsonObject station, int index)
    {
        if (!ReadBoolean(station, "isFavorite", "IsFavorite")) return null;
        var id = ReadText(station, "id", "Id");
        var name = ReadText(station, "name", "Name");
        var address = ReadText(station, "streamUrl", "StreamUrl");
        if (id.Length == 0
            || !Uri.TryCreate(address, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || !string.IsNullOrWhiteSpace(uri.UserInfo))
        {
            return null;
        }
        return new Candidate(id, name, address, index);
    }

    private static IReadOnlyList<Candidate> Order(
        IReadOnlyList<Candidate> candidates,
        IReadOnlyList<string> storedOrder)
    {
        var indices = storedOrder
            .Select((id, index) => (id, index))
            .GroupBy(pair => pair.id, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First().index, StringComparer.Ordinal);
        return candidates
            .OrderBy(candidate => indices.GetValueOrDefault(candidate.Id, int.MaxValue))
            .ThenBy(candidate => candidate.OriginalIndex)
            .ToArray();
    }

    private static RadioFavoritesSortMode ReadSortMode(JsonObject root)
    {
        var node = root["sessionNavigation"]?["sessions"]?["radio"]?
            ["collectionSortModes"]?["Ulubione"];
        if (node is JsonValue value)
        {
            if (value.TryGetValue<string>(out var text)
                && Enum.TryParse<RadioFavoritesSortMode>(text, ignoreCase: true, out var parsed))
            {
                return parsed;
            }
            if (value.TryGetValue<int>(out var number)
                && Enum.IsDefined(typeof(RadioFavoritesSortMode), number))
            {
                return (RadioFavoritesSortMode)number;
            }
        }
        return RadioFavoritesSortMode.AddedNewest;
    }

    private static RadioFavoritePlaylistEntry ToEntry(Candidate candidate) =>
        new(candidate.Name, candidate.Address);

    private static string ReadText(JsonObject value, string first, string second) =>
        value[first]?.GetValue<string?>()?.Trim()
        ?? value[second]?.GetValue<string?>()?.Trim()
        ?? string.Empty;

    private static bool ReadBoolean(JsonObject value, string first, string second)
    {
        foreach (var name in new[] { first, second })
        {
            if (value[name] is JsonValue json && json.TryGetValue<bool>(out var result))
                return result;
        }
        return false;
    }

    private sealed record Candidate(
        string Id,
        string Name,
        string Address,
        int OriginalIndex);

    private enum RadioFavoritesSortMode
    {
        AddedNewest,
        Alphabetical,
        Custom
    }
}
