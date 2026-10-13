using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Devices.WiiM;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteWiiMNetworkStreamMutationResult(
    string PreferredStreamId,
    string Title,
    int AddedCount,
    int UpdatedCount);

internal sealed record LiteWiiMNetworkStreamImportResult(
    string? PreferredStreamId,
    int AddedCount,
    int SkippedCount,
    int InvalidCount);

internal sealed record LiteWiiMNetworkStreamDisplayOrder(
    IReadOnlyList<WiiMNetworkStreamSettings> Streams,
    CollectionSortMode SortMode);

internal sealed record LiteWiiMNetworkStreamDraft(string Name, string Url);

internal static class LiteWiiMProfileMutation
{
    public static LiteWiiMNetworkStreamMutationResult Add(
        JsonObject root,
        string requestedName,
        string requestedUrl)
    {
        var name = CleanRequiredText(
            requestedName,
            "Nazwa strumienia nie może być pusta.");
        var url = NormalizeUrl(requestedUrl);
        var streams = EnsureNetworkStreams(root);
        var duplicate = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            WiiMPlaybackUriPolicy.TryNormalize(
                ReadText(stream, "streamUrl", "StreamUrl"),
                out var candidate)
            && string.Equals(candidate, url, StringComparison.OrdinalIgnoreCase));
        if (duplicate is not null)
        {
            duplicate["name"] = name;
            return new(
                ReadText(duplicate, "id", "Id"),
                name,
                AddedCount: 0,
                UpdatedCount: 1);
        }

        var id = $"wiim:stream:{Guid.NewGuid():N}";
        streams.Add(new JsonObject
        {
            ["id"] = id,
            ["name"] = name,
            ["streamUrl"] = url,
            ["addedUtcTicks"] = DateTime.UtcNow.Ticks
        });
        return new(id, name, AddedCount: 1, UpdatedCount: 0);
    }

    public static LiteWiiMNetworkStreamMutationResult Edit(
        JsonObject root,
        string streamId,
        string requestedName,
        string requestedUrl)
    {
        var id = CleanRequiredText(
            streamId,
            "Nie wskazano strumienia WiiM do zmiany.");
        var name = CleanRequiredText(
            requestedName,
            "Nazwa strumienia nie może być pusta.");
        var url = NormalizeUrl(requestedUrl);
        var streams = EnsureNetworkStreams(root);
        var saved = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            string.Equals(ReadText(stream, "id", "Id"), id, StringComparison.Ordinal))
            ?? throw new LiteRequestException(
                "Nie można odnaleźć tego strumienia na zapisanej liście AMC.");
        var duplicate = streams.OfType<JsonObject>().FirstOrDefault(stream =>
            !ReferenceEquals(stream, saved)
            && WiiMPlaybackUriPolicy.TryNormalize(
                ReadText(stream, "streamUrl", "StreamUrl"),
                out var candidate)
            && string.Equals(candidate, url, StringComparison.OrdinalIgnoreCase));
        if (duplicate is not null)
            throw new LiteRequestException(
                "Ten adres jest już zapisany jako: "
                + ReadText(duplicate, "name", "Name"));

        saved["name"] = name;
        saved["streamUrl"] = url;
        return new(id, name, AddedCount: 0, UpdatedCount: 1);
    }

    public static string[] Remove(JsonObject root, IReadOnlyCollection<string> streamIds)
    {
        var ids = streamIds
            .Select(value => value?.Trim() ?? "")
            .Where(value => value.Length > 0)
            .Distinct(StringComparer.Ordinal)
            .ToArray();
        if (ids.Length == 0)
            throw new LiteRequestException(
                "Wybierz zapisany strumień WiiM do usunięcia.");

        var wiiM = EnsureWiiM(root);
        var streams = EnsureNetworkStreams(root);
        var titles = streams.OfType<JsonObject>()
            .Where(stream => ids.Contains(
                ReadText(stream, "id", "Id"),
                StringComparer.Ordinal))
            .Select(stream => ReadText(stream, "name", "Name"))
            .Where(title => title.Length > 0)
            .ToArray();
        if (titles.Length == 0)
            throw new LiteRequestException(
                "Nie można odnaleźć wybranych strumieni na zapisanej liście AMC.");

        for (var index = streams.Count - 1; index >= 0; index--)
        {
            if (streams[index] is JsonObject stream
                && ids.Contains(ReadText(stream, "id", "Id"), StringComparer.Ordinal))
                streams.RemoveAt(index);
        }
        if (wiiM["devices"] is JsonArray devices)
        {
            foreach (var device in devices.OfType<JsonObject>())
            {
                var remembered = ReadText(
                    device,
                    "lastActivatedNetworkStreamId",
                    "LastActivatedNetworkStreamId");
                if (ids.Contains(remembered, StringComparer.Ordinal))
                    device["lastActivatedNetworkStreamId"] = null;
            }
        }
        RemoveOrderIds(root, ids);
        return titles;
    }

    public static LiteWiiMNetworkStreamImportResult Import(
        JsonObject root,
        IReadOnlyList<LiteWiiMNetworkStreamDraft> requestedStreams,
        int parserSkipped)
    {
        if (requestedStreams.Count > 10_000)
            throw new LiteRequestException(
                "Playlista może zawierać najwyżej 10000 strumieni.");
        var streams = EnsureNetworkStreams(root);
        var existingUrls = streams.OfType<JsonObject>()
            .Select(stream => ReadText(stream, "streamUrl", "StreamUrl"))
            .Select(url => WiiMPlaybackUriPolicy.TryNormalize(url, out var normalized)
                ? normalized
                : "")
            .Where(url => url.Length > 0)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        var added = new List<string>();
        var invalid = Math.Max(0, parserSkipped);
        var duplicates = 0;
        foreach (var requested in requestedStreams)
        {
            if (!WiiMPlaybackUriPolicy.TryNormalize(requested.Url, out var url))
            {
                invalid++;
                continue;
            }
            if (!existingUrls.Add(url))
            {
                duplicates++;
                continue;
            }
            var name = string.IsNullOrWhiteSpace(requested.Name)
                ? Uri.TryCreate(url, UriKind.Absolute, out var uri)
                    ? uri.Host
                    : "Strumień WiiM"
                : requested.Name.Trim();
            var id = $"wiim:stream:{Guid.NewGuid():N}";
            streams.Add(new JsonObject
            {
                ["id"] = id,
                ["name"] = name,
                ["streamUrl"] = url,
                ["addedUtcTicks"] = DateTime.UtcNow.Ticks
            });
            added.Add(id);
        }

        if (added.Count > 0)
        {
            var all = ReadStreams(root);
            var remembered = ReadOrderIds(root, custom: false);
            if (remembered.Count == 0)
            {
                remembered = all
                    .OrderBy(stream => stream.AddedUtcTicks)
                    .ThenBy(stream => stream.Id, StringComparer.Ordinal)
                    .Select(stream => stream.Id)
                    .ToArray();
            }
            WriteOrderIds(
                root,
                custom: false,
                WiiMNetworkStreamOrdering.RememberImportedBatch(
                    all,
                    remembered,
                    added));
        }
        return new(
            added.FirstOrDefault(),
            added.Count,
            invalid + duplicates,
            invalid);
    }

    public static LiteWiiMNetworkStreamDisplayOrder OrderForDisplay(JsonObject root)
    {
        var mode = ReadSortMode(root);
        var streams = ReadStreams(root);
        var result = WiiMNetworkStreamOrdering.OrderForDisplay(
            streams,
            mode,
            EffectiveOrderIds(root, streams, mode));
        return new(result.Streams, mode);
    }

    public static LiteWiiMNetworkStreamDisplayOrder SetSortMode(
        JsonObject root,
        CollectionSortMode mode)
    {
        var modes = EnsureObject(
            EnsureObject(
                EnsureObject(
                    EnsureObject(root, "sessionNavigation"),
                    "sessions"),
                "wiim"),
            "collectionSortModes");
        modes["Biblioteka"] = mode.ToString();
        var streams = ReadStreams(root);
        var result = WiiMNetworkStreamOrdering.OrderForDisplay(
            streams,
            mode,
            EffectiveOrderIds(root, streams, mode));
        WriteOrderIds(
            root,
            custom: mode is CollectionSortMode.Custom,
            result.NormalizedItemIds);
        return new(result.Streams, mode);
    }

    private static string NormalizeUrl(string requestedUrl)
    {
        if (WiiMPlaybackUriPolicy.TryNormalize(requestedUrl, out var url))
            return url;
        throw new LiteRequestException(
            "Nie można zapisać tego adresu strumienia WiiM.");
    }

    private static string CleanRequiredText(string? value, string message)
    {
        var cleaned = value?.Trim() ?? "";
        return cleaned.Length > 0 ? cleaned : throw new LiteRequestException(message);
    }

    private static JsonObject EnsureWiiM(JsonObject root)
    {
        if (root["wiiM"] is JsonObject current) return current;
        if (root["WiiM"] is JsonObject legacy) return legacy;
        var created = new JsonObject();
        root["wiiM"] = created;
        return created;
    }

    private static JsonArray EnsureNetworkStreams(JsonObject root)
    {
        var wiiM = EnsureWiiM(root);
        if (wiiM["networkStreams"] is JsonArray current) return current;
        if (wiiM["NetworkStreams"] is JsonArray legacy) return legacy;
        var created = new JsonArray();
        wiiM["networkStreams"] = created;
        return created;
    }

    private static JsonObject EnsureObject(JsonObject parent, string name)
    {
        if (parent[name] is JsonObject current) return current;
        var created = new JsonObject();
        parent[name] = created;
        return created;
    }

    private static IReadOnlyList<WiiMNetworkStreamSettings> ReadStreams(JsonObject root) =>
        EnsureNetworkStreams(root)
            .OfType<JsonObject>()
            .Select(stream => new WiiMNetworkStreamSettings
            {
                Id = ReadText(stream, "id", "Id"),
                Name = ReadText(stream, "name", "Name"),
                StreamUrl = ReadText(stream, "streamUrl", "StreamUrl"),
                AddedUtcTicks = ReadLong(stream, "addedUtcTicks", "AddedUtcTicks")
            })
            .Where(stream => stream.Id.Length > 0)
            .ToArray();

    private static CollectionSortMode ReadSortMode(JsonObject root)
    {
        var value = root["sessionNavigation"]?["sessions"]?["wiim"]?
            ["collectionSortModes"]?["Biblioteka"];
        if (value is JsonValue json)
        {
            if (json.TryGetValue<string>(out var text)
                && Enum.TryParse<CollectionSortMode>(
                    text,
                    ignoreCase: true,
                    out var parsed))
                return parsed;
            if (json.TryGetValue<int>(out var number)
                && Enum.IsDefined(typeof(CollectionSortMode), number))
                return (CollectionSortMode)number;
        }
        return CollectionSortMode.AddedNewest;
    }

    private static IReadOnlyList<string> ReadOrderIds(JsonObject root, bool custom)
    {
        var name = custom
            ? "libraryItemIdsBySession"
            : "libraryAddedItemIdsBySession";
        if (root["collectionOrders"]?[name]?["wiim"] is not JsonArray values)
            return [];
        return values
            .OfType<JsonValue>()
            .Select(value => value.TryGetValue<string>(out var text) ? text.Trim() : "")
            .Where(value => value.Length > 0)
            .Distinct(StringComparer.Ordinal)
            .ToArray();
    }

    private static IReadOnlyList<string> EffectiveOrderIds(
        JsonObject root,
        IReadOnlyList<WiiMNetworkStreamSettings> streams,
        CollectionSortMode mode)
    {
        var ids = ReadOrderIds(root, custom: mode is CollectionSortMode.Custom);
        if (ids.Count > 0 || mode is not CollectionSortMode.AddedNewest)
            return ids;
        return streams
            .OrderBy(stream => stream.AddedUtcTicks)
            .ThenBy(stream => stream.Id, StringComparer.Ordinal)
            .Select(stream => stream.Id)
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
        var bySession = EnsureObject(
            EnsureObject(root, "collectionOrders"),
            name);
        bySession["wiim"] = new JsonArray(
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
                || bySession["wiim"] is not JsonArray values)
                continue;
            for (var index = values.Count - 1; index >= 0; index--)
            {
                var value = values[index]?.GetValue<string?>()?.Trim();
                if (value is not null
                    && removedIds.Contains(value, StringComparer.Ordinal))
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
        return "";
    }

    private static long ReadLong(JsonObject source, params string[] names)
    {
        foreach (var name in names)
        {
            if (source[name] is JsonValue value
                && value.TryGetValue<long>(out var number))
                return number;
        }
        return 0;
    }
}
