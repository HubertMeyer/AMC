using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sonos;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteSonosOwnStreamMutationResult(
    string PreferredStreamId,
    string Title,
    int AddedCount,
    int UpdatedCount);

internal sealed record LiteSonosOwnStreamImportResult(
    string? PreferredStreamId,
    int AddedCount,
    int SkippedCount,
    int InvalidCount);

internal sealed record LiteSonosOwnStreamDraft(string Name, string Url);

/// <summary>
/// Wąskie modyfikacje lokalnych „Moich stacji” Sonosa. Operacje dotyczą tylko
/// profilu AMC; nie zmieniają Ulubionych ani playlist na koncie Sonos.
/// </summary>
internal static class LiteSonosOwnStreamsMutation
{
    public static LiteSonosOwnStreamMutationResult Add(
        JsonObject root,
        string requestedName,
        string requestedUrl)
    {
        var name = CleanRequiredText(requestedName, "Nazwa stacji nie może być pusta.");
        var url = CleanUrl(requestedUrl);
        var streams = EnsureOwnStreams(root);
        var duplicate = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            string.Equals(
                ReadText(stream, "streamUrl", "StreamUrl"),
                url,
                StringComparison.OrdinalIgnoreCase));
        if (duplicate is not null)
        {
            duplicate["name"] = name;
            var duplicateId = ReadText(duplicate, "id", "Id");
            NormalizeOrders(root);
            return new(duplicateId, name, AddedCount: 0, UpdatedCount: 1);
        }

        var id = Guid.NewGuid().ToString("N");
        streams.Add(new JsonObject
        {
            ["id"] = id,
            ["name"] = name,
            ["streamUrl"] = url
        });
        NormalizeOrders(root);
        return new(id, name, AddedCount: 1, UpdatedCount: 0);
    }

    public static LiteSonosOwnStreamMutationResult Edit(
        JsonObject root,
        string streamId,
        string requestedName,
        string requestedUrl)
    {
        var id = CleanRequiredText(streamId, "Nie wskazano stacji Sonos do zmiany.");
        var name = CleanRequiredText(requestedName, "Nazwa stacji nie może być pusta.");
        var url = CleanUrl(requestedUrl);
        var streams = EnsureOwnStreams(root);
        var saved = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            string.Equals(ReadText(stream, "id", "Id"), id, StringComparison.Ordinal))
            ?? throw new LiteRequestException(
                "Nie można odnaleźć tej stacji na zapisanej liście AMC.");
        var duplicate = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            !ReferenceEquals(stream, saved)
            && string.Equals(
                ReadText(stream, "streamUrl", "StreamUrl"),
                url,
                StringComparison.OrdinalIgnoreCase));
        if (duplicate is not null)
            throw new LiteRequestException(
                "Ten adres jest już zapisany jako: "
                + ReadText(duplicate, "name", "Name"));

        saved["name"] = name;
        saved["streamUrl"] = url;
        return new(id, name, AddedCount: 0, UpdatedCount: 1);
    }

    public static SonosOwnStreamSettings ReadForEdit(JsonObject root, string streamId)
    {
        var id = CleanRequiredText(streamId, "Nie wskazano stacji Sonos do zmiany.");
        return ReadStreams(root).FirstOrDefault(stream =>
                   string.Equals(stream.Id, id, StringComparison.Ordinal))
               ?? throw new LiteRequestException(
                   "Nie można odnaleźć tej stacji na zapisanej liście AMC.");
    }

    public static string[] Remove(JsonObject root, IReadOnlyCollection<string> streamIds)
    {
        var ids = streamIds
            .Select(value => value?.Trim() ?? string.Empty)
            .Where(value => value.Length > 0)
            .Distinct(StringComparer.Ordinal)
            .ToArray();
        if (ids.Length == 0)
            throw new LiteRequestException("Wybierz stację Sonos do usunięcia.");

        var streams = EnsureOwnStreams(root);
        var titles = streams.OfType<JsonObject>()
            .Where(stream => ids.Contains(ReadText(stream, "id", "Id"), StringComparer.Ordinal))
            .Select(stream => ReadText(stream, "name", "Name"))
            .Where(title => title.Length > 0)
            .ToArray();
        if (titles.Length == 0)
            throw new LiteRequestException(
                "Nie można odnaleźć wybranych stacji na zapisanej liście AMC.");

        for (var index = streams.Count - 1; index >= 0; index--)
        {
            if (streams[index] is JsonObject stream
                && ids.Contains(ReadText(stream, "id", "Id"), StringComparer.Ordinal))
                streams.RemoveAt(index);
        }
        RemoveOrderIds(root, ids);
        return titles;
    }

    public static LiteSonosOwnStreamImportResult Import(
        JsonObject root,
        IReadOnlyList<LiteSonosOwnStreamDraft> requestedStreams,
        int parserSkipped)
    {
        if (requestedStreams.Count > 10_000)
            throw new LiteRequestException(
                "Playlista może zawierać najwyżej 10000 stacji.");
        var before = ReadStreams(root);
        var existingIds = before.Select(stream => stream.Id)
            .ToHashSet(StringComparer.Ordinal);
        var merged = SonosOwnStreamsImport.Merge(
            before,
            requestedStreams.Select(stream =>
                new SonosOwnStreamsImportEntry(stream.Name, stream.Url)));
        if (merged.Added > 0)
        {
            WriteStreams(root, merged.Stations);
            NormalizeOrders(root);
        }
        var preferred = merged.Stations.FirstOrDefault(stream =>
            !existingIds.Contains(stream.Id))?.Id;
        var invalid = Math.Max(0, parserSkipped) + merged.SkippedInvalidAddresses;
        return new(
            preferred,
            merged.Added,
            invalid + merged.SkippedDuplicates,
            invalid);
    }

    public static CollectionSortMode SetSortMode(
        JsonObject root,
        CollectionSortMode mode)
    {
        var modes = EnsureObject(
            EnsureObject(
                EnsureObject(
                    EnsureObject(root, "sessionNavigation"),
                    "sessions"),
                "sonos"),
            "collectionSortModes");
        modes[SonosOwnStreamsOrder.ViewName] = mode.ToString();
        NormalizeOrders(root);
        return mode;
    }

    private static void NormalizeOrders(JsonObject root)
    {
        var streams = ReadStreams(root);
        var orders = ReadOrders(root);
        SonosOwnStreamsOrder.EnsureAddedOrder(orders, streams);
        SonosOwnStreamsOrder.EnsureCustomOrder(orders, streams);
        WriteOrderIds(root, custom: false,
            orders.LibraryAddedItemIdsBySession[SonosOwnStreamsOrder.StorageKey]);
        WriteOrderIds(root, custom: true,
            orders.LibraryItemIdsBySession[SonosOwnStreamsOrder.StorageKey]);
    }

    private static CollectionOrderSettings ReadOrders(JsonObject root)
    {
        var result = new CollectionOrderSettings();
        result.LibraryAddedItemIdsBySession[SonosOwnStreamsOrder.StorageKey] =
            ReadOrderIds(root, custom: false).ToList();
        result.LibraryItemIdsBySession[SonosOwnStreamsOrder.StorageKey] =
            ReadOrderIds(root, custom: true).ToList();
        return result;
    }

    private static IReadOnlyList<SonosOwnStreamSettings> ReadStreams(JsonObject root) =>
        EnsureOwnStreams(root)
            .OfType<JsonObject>()
            .Select(stream => new SonosOwnStreamSettings
            {
                Id = ReadText(stream, "id", "Id"),
                Name = ReadText(stream, "name", "Name"),
                StreamUrl = ReadText(stream, "streamUrl", "StreamUrl")
            })
            .Where(stream => stream.Id.Length > 0)
            .ToArray();

    private static void WriteStreams(
        JsonObject root,
        IEnumerable<SonosOwnStreamSettings> streams)
    {
        var values = new JsonArray();
        foreach (var stream in streams)
        {
            values.Add(new JsonObject
            {
                ["id"] = stream.Id,
                ["name"] = stream.Name,
                ["streamUrl"] = stream.StreamUrl
            });
        }
        EnsureSonos(root)["ownStreams"] = values;
    }

    private static string CleanUrl(string? requestedUrl)
    {
        var url = requestedUrl?.Trim() ?? string.Empty;
        if (SonosStreamUrlPolicy.IsAcceptable(url)) return url;
        throw new LiteRequestException(
            "Nie można zapisać tego adresu stacji Sonos.");
    }

    private static string CleanRequiredText(string? value, string message)
    {
        var cleaned = value?.Trim() ?? string.Empty;
        return cleaned.Length > 0 ? cleaned : throw new LiteRequestException(message);
    }

    private static JsonObject EnsureSonos(JsonObject root)
    {
        if (root["sonos"] is JsonObject current) return current;
        if (root["Sonos"] is JsonObject legacy) return legacy;
        var created = new JsonObject();
        root["sonos"] = created;
        return created;
    }

    private static JsonArray EnsureOwnStreams(JsonObject root)
    {
        var sonos = EnsureSonos(root);
        if (sonos["ownStreams"] is JsonArray current) return current;
        if (sonos["OwnStreams"] is JsonArray legacy) return legacy;
        var created = new JsonArray();
        sonos["ownStreams"] = created;
        return created;
    }

    private static JsonObject EnsureObject(JsonObject parent, string name)
    {
        if (parent[name] is JsonObject current) return current;
        var created = new JsonObject();
        parent[name] = created;
        return created;
    }

    private static IReadOnlyList<string> ReadOrderIds(JsonObject root, bool custom)
    {
        var name = custom
            ? "libraryItemIdsBySession"
            : "libraryAddedItemIdsBySession";
        if (root["collectionOrders"]?[name]?[SonosOwnStreamsOrder.StorageKey]
            is not JsonArray values)
            return [];
        return values
            .OfType<JsonValue>()
            .Select(value => value.TryGetValue<string>(out var text) ? text.Trim() : string.Empty)
            .Where(value => value.Length > 0)
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }

    private static void WriteOrderIds(
        JsonObject root,
        bool custom,
        IEnumerable<string> values)
    {
        var name = custom
            ? "libraryItemIdsBySession"
            : "libraryAddedItemIdsBySession";
        var bySession = EnsureObject(EnsureObject(root, "collectionOrders"), name);
        bySession[SonosOwnStreamsOrder.StorageKey] = new JsonArray(
            values
                .Where(value => !string.IsNullOrWhiteSpace(value))
                .Distinct(StringComparer.Ordinal)
                .Select(value => (JsonNode?)JsonValue.Create(value.Trim()))
                .ToArray());
    }

    private static void RemoveOrderIds(
        JsonObject root,
        IReadOnlyCollection<string> removedIds)
    {
        if (root["collectionOrders"] is not JsonObject orders) return;
        foreach (var propertyName in new[]
                 {
                     "libraryAddedItemIdsBySession",
                     "libraryItemIdsBySession"
                 })
        {
            if (orders[propertyName] is not JsonObject bySession
                || bySession[SonosOwnStreamsOrder.StorageKey] is not JsonArray values)
                continue;
            for (var index = values.Count - 1; index >= 0; index--)
            {
                var value = values[index]?.GetValue<string?>()?.Trim();
                if (value is not null && removedIds.Contains(value, StringComparer.Ordinal))
                    values.RemoveAt(index);
            }
        }
    }

    private static string ReadText(JsonObject source, params string[] names)
    {
        foreach (var name in names)
        {
            if (source[name] is not JsonValue value) continue;
            if (value.TryGetValue<string>(out var text)
                && !string.IsNullOrWhiteSpace(text))
                return text.Trim();
        }
        return string.Empty;
    }
}
