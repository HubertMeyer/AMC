using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Jedna stacja przekazana przez okno dodawania albo wspólny importer AMC.
/// Id pozostaje własnością hosta; frontend nie tworzy identyfikatorów profilu.
/// </summary>
internal sealed record LiteRadioStationDraft(string Name, string Url);

/// <summary>
/// Wynik wąskiej zmiany Biblioteki radia. Pola liczbowe służą do krótkiego,
/// użytkowego komunikatu, a identyfikator wyłącznie do przywrócenia fokusu.
/// </summary>
internal sealed record LiteRadioLibraryMutationResult(
    [property: JsonPropertyName("addedCount")] int AddedCount,
    [property: JsonPropertyName("promotedCount")] int PromotedCount,
    [property: JsonPropertyName("updatedCount")] int UpdatedCount,
    [property: JsonPropertyName("skippedCount")] int SkippedCount,
    [property: JsonPropertyName("preferredStationId")] string? PreferredStationId,
    [property: JsonPropertyName("preferredStationName")] string? PreferredStationName,
    [property: JsonIgnore] IReadOnlyList<string> ChangedStationIds)
{
    [JsonIgnore]
    public bool Changed => ChangedStationIds.Count > 0;
}

/// <summary>
/// Wspólne reguły dodawania i importu stacji, zgodne z głównym AMC.
/// Klasa zmienia wyłącznie przekazany węzeł JSON; zapis atomowy i kolejność
/// w SQLite pozostają odpowiedzialnością <see cref="LiteProfileMutationStore"/>.
/// </summary>
internal static class LiteRadioLibraryMutation
{
    public static LiteRadioLibraryMutationResult Apply(
        JsonObject root,
        IReadOnlyList<LiteRadioStationDraft> drafts,
        int parserSkipped,
        bool updateExistingTitles)
    {
        if (root["radio"]?["stations"] is not JsonArray stations)
            throw new InvalidDataException("Profil AMC nie zawiera listy stacji.");

        var existingByUrl = new Dictionary<string, JsonObject>(StringComparer.OrdinalIgnoreCase);
        foreach (var group in stations
                     .OfType<JsonObject>()
                     .Select(station => (Station: station, Url: Text(station, "streamUrl", "StreamUrl")))
                     .Where(entry => entry.Url.Length > 0)
                     .GroupBy(entry => entry.Url, StringComparer.OrdinalIgnoreCase))
        {
            existingByUrl[group.Key] = group
                .Select(entry => entry.Station)
                .FirstOrDefault(station => Boolean(station, "isInLibrary", "IsInLibrary"))
                ?? group.First().Station;
        }

        var added = new List<string>();
        var promoted = new List<string>();
        var updated = new List<string>();
        var changedNames = new Dictionary<string, string>(StringComparer.Ordinal);
        var skipped = Math.Max(0, parserSkipped);

        foreach (var draft in drafts)
        {
            if (existingByUrl.TryGetValue(draft.Url, out var existing))
            {
                var existingId = Text(existing, "id", "Id");
                if (existingId.Length == 0)
                {
                    skipped++;
                    continue;
                }

                if (updateExistingTitles)
                {
                    existing["name"] = draft.Name;
                    existing["streamUrl"] = draft.Url;
                    existing["hasCustomTitle"] = true;
                    existing["isInLibrary"] = true;
                    updated.Add(existingId);
                    changedNames[existingId] = draft.Name;
                    continue;
                }

                if (Boolean(existing, "isInLibrary", "IsInLibrary"))
                {
                    skipped++;
                    continue;
                }

                existing["isInLibrary"] = true;
                promoted.Add(existingId);
                changedNames[existingId] = Text(existing, "name", "Name");
                continue;
            }

            var idPrefix = updateExistingTitles ? "radio:custom:" : "radio:imported:";
            var newId = idPrefix + Guid.NewGuid().ToString("N");
            var station = new JsonObject
            {
                ["id"] = newId,
                ["name"] = draft.Name,
                ["streamUrl"] = draft.Url,
                ["hasCustomTitle"] = true,
                ["isFavorite"] = false,
                ["isInLibrary"] = true,
                ["isInQueue"] = false,
                ["isPlayNext"] = false,
                ["isCustom"] = true,
                ["isBitrateEstimated"] = false
            };
            stations.Add(station);
            existingByUrl[draft.Url] = station;
            added.Add(newId);
            changedNames[newId] = draft.Name;
        }

        var preferred = updateExistingTitles
            ? updated.FirstOrDefault() ?? added.FirstOrDefault()
            : promoted.FirstOrDefault() ?? added.FirstOrDefault();
        var changedIds = updated.Concat(promoted).Concat(added).Distinct(StringComparer.Ordinal).ToArray();
        return new LiteRadioLibraryMutationResult(
            added.Count,
            promoted.Count,
            updated.Count,
            skipped,
            preferred,
            preferred is not null && changedNames.TryGetValue(preferred, out var name) ? name : null,
            changedIds);
    }

    private static string Text(JsonObject value, string first, string second) =>
        value[first]?.GetValue<string?>()?.Trim()
        ?? value[second]?.GetValue<string?>()?.Trim()
        ?? string.Empty;

    private static bool Boolean(JsonObject value, string first, string second)
    {
        foreach (var name in new[] { first, second })
        {
            if (value[name] is JsonValue json && json.TryGetValue<bool>(out var result))
                return result;
        }
        return false;
    }
}
