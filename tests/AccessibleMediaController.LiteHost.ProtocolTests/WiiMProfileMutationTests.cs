using System.Text.Json.Nodes;
using AccessibleMediaController.LiteHost;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class WiiMProfileMutationTests
{
    public static void Run()
    {
        AddUpdatesDuplicateAndCreatesNewStream();
        EditRejectsDuplicateAddress();
        RemoveCleansDeviceMemoryAndOrders();
        ImportPreservesPlaylistOrderAndSkipsDuplicates();
        SortAndExportUseTheSameVisibleOrder();
        MoveAndPlaceRequireAndPersistCustomOrder();
        Console.WriteLine("WiiMProfileMutationTests: OK");
    }

    private static void AddUpdatesDuplicateAndCreatesNewStream()
    {
        var root = Profile();
        var updated = LiteWiiMProfileMutation.Add(
            root,
            "Radio Poznań poprawione",
            " https://radio.invalid/poznan ");
        Assert.Equal("stream-1", updated.PreferredStreamId,
            "duplikat adresu zachowuje identyfikator");
        Assert.True(updated.UpdatedCount == 1 && updated.AddedCount == 0,
            "duplikat adresu jest aktualizacją, nie drugim wpisem");
        Assert.Equal(
            "Radio Poznań poprawione",
            Streams(root)[0]!["name"]!.GetValue<string>(),
            "aktualizacja zapisuje nazwę użytkownika");

        var added = LiteWiiMProfileMutation.Add(
            root,
            "Radio Opole",
            "https://radio.invalid/opole");
        Assert.True(
            added.AddedCount == 1
            && added.PreferredStreamId.StartsWith("wiim:stream:", StringComparison.Ordinal),
            "nowy adres otrzymuje stabilny identyfikator AMC");
        Assert.True(Streams(root).Count == 3,
            "nowy adres dopisuje dokładnie jeden strumień");
    }

    private static void EditRejectsDuplicateAddress()
    {
        var root = Profile();
        try
        {
            LiteWiiMProfileMutation.Edit(
                root,
                "stream-1",
                "Duplikat",
                "https://radio.invalid/drugi");
            throw new InvalidOperationException(
                "edycja przyjęła adres zapisany przy innym strumieniu");
        }
        catch (LiteRequestException exception)
        {
            Assert.True(
                exception.Message.Contains("Radio Drugie", StringComparison.Ordinal),
                "komunikat duplikatu używa nazwy użytkowej");
        }

        var edited = LiteWiiMProfileMutation.Edit(
            root,
            "stream-1",
            "Radio Nowe",
            "https://radio.invalid/nowe");
        Assert.Equal("Radio Nowe", edited.Title,
            "edycja zwraca nazwę przeznaczoną do komunikatu");
        Assert.Equal(
            "https://radio.invalid/nowe",
            Streams(root)[0]!["streamUrl"]!.GetValue<string>(),
            "edycja zapisuje znormalizowany adres");
    }

    private static void RemoveCleansDeviceMemoryAndOrders()
    {
        var root = Profile();
        var titles = LiteWiiMProfileMutation.Remove(root, ["stream-1"]);
        Assert.True(titles.SequenceEqual(["Radio Poznań"]),
            "usunięcie zwraca wyłącznie nazwę użytkową");
        Assert.True(Streams(root).Count == 1,
            "usunięcie usuwa tylko wskazany strumień");
        var device = (JsonObject)((JsonArray)root["wiiM"]!["devices"]!)[0]!;
        Assert.True(device["lastActivatedNetworkStreamId"] is null,
            "urządzenie nie pamięta usuniętego strumienia");
        var orders = (JsonArray)root["collectionOrders"]!
            ["libraryItemIdsBySession"]!["wiim"]!;
        Assert.True(
            orders.Count == 1 && orders[0]!.GetValue<string>() == "stream-2",
            "kolejność własna nie przechowuje usuniętego identyfikatora");
    }

    private static void ImportPreservesPlaylistOrderAndSkipsDuplicates()
    {
        var root = Profile();
        var result = LiteWiiMProfileMutation.Import(
            root,
            [
                new LiteWiiMNetworkStreamDraft(
                    "Duplikat",
                    "https://radio.invalid/poznan"),
                new LiteWiiMNetworkStreamDraft(
                    "Żuraw",
                    "https://radio.invalid/zuraw"),
                new LiteWiiMNetworkStreamDraft(
                    "Alfa",
                    "https://radio.invalid/alfa")
            ],
            parserSkipped: 1);
        Assert.True(result.AddedCount == 2 && result.SkippedCount == 2,
            "import liczy nowe wpisy, duplikaty i błędy parsera");
        var visible = LiteWiiMProfileMutation.OrderForDisplay(root);
        Assert.True(
            visible.Streams.Take(2).Select(stream => stream.Name)
                .SequenceEqual(["Żuraw", "Alfa"]),
            "widok najnowszych zachowuje kolejność partii z playlisty");
    }

    private static void SortAndExportUseTheSameVisibleOrder()
    {
        var root = Profile();
        var sorted = LiteWiiMProfileMutation.SetSortMode(
            root,
            AccessibleMediaController.Core.Configuration.CollectionSortMode.Alphabetical);
        Assert.True(
            sorted.Streams.Select(stream => stream.Name)
                .SequenceEqual(["Radio Drugie", "Radio Poznań"]),
            "sortowanie alfabetyczne używa nazw widocznych dla użytkownika");

        var directory = Path.Combine(
            Path.GetTempPath(),
            "amc-wiim-export-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            var path = Path.Combine(directory, "strumienie.m3u");
            var result = LiteWiiMNetworkStreamExport.Write(root, path);
            var text = File.ReadAllText(path);
            Assert.True(result.ExportedCount == 2,
                "eksport podaje liczbę zapisanych strumieni");
            Assert.True(
                text.IndexOf("Radio Drugie", StringComparison.Ordinal)
                < text.IndexOf("Radio Poznań", StringComparison.Ordinal),
                "eksport zachowuje dokładnie porządek widoczny w AMC");
            Assert.True(
                !text.Contains("stream-1", StringComparison.Ordinal)
                && text.Contains("https://radio.invalid/poznan", StringComparison.Ordinal),
                "eksport zawiera adresy odtwarzania, ale nie identyfikatory AMC");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static void MoveAndPlaceRequireAndPersistCustomOrder()
    {
        var root = Profile();
        try
        {
            LiteWiiMProfileMutation.Move(root, ["stream-2"], -1);
            throw new InvalidOperationException(
                "przenoszenie zadziałało poza kolejnością własną");
        }
        catch (LiteRequestException exception)
        {
            Assert.True(exception.Message.Contains("Alt 3", StringComparison.Ordinal),
                "odmowa wskazuje użytkownikowi sposób włączenia kolejności własnej");
        }

        LiteWiiMProfileMutation.SetSortMode(
            root,
            AccessibleMediaController.Core.Configuration.CollectionSortMode.Custom);
        var moved = LiteWiiMProfileMutation.Move(root, ["stream-2"], -1);
        Assert.True(moved.PreferredStreamId == "stream-2" && moved.Position == 1,
            "Alt+strzałka przesuwa wskazany strumień o jedną pozycję");
        Assert.True(
            LiteWiiMProfileMutation.OrderForDisplay(root).Streams
                .Select(stream => stream.Id)
                .SequenceEqual(["stream-2", "stream-1"]),
            "zmieniona kolejność jest od razu kolejnością widoczną");

        var placed = LiteWiiMProfileMutation.PlaceBefore(
            root,
            ["stream-1"],
            "stream-2");
        Assert.True(placed.PreferredStreamId == "stream-1" && placed.Position == 1,
            "Ctrl+V wstawia wycięty strumień przed wskazanym celem");
        var stored = (JsonArray)root["collectionOrders"]!
            ["libraryItemIdsBySession"]!["wiim"]!;
        Assert.True(
            stored.Select(value => value!.GetValue<string>())
                .SequenceEqual(["stream-1", "stream-2"]),
            "Ctrl+V zapisuje kolejność własną w istniejącym magazynie profilu");
    }

    private static JsonObject Profile() => new()
    {
        ["wiiM"] = new JsonObject
        {
            ["devices"] = new JsonArray
            {
                new JsonObject
                {
                    ["id"] = "device-1",
                    ["lastActivatedNetworkStreamId"] = "stream-1"
                }
            },
            ["networkStreams"] = new JsonArray
            {
                Stream("stream-1", "Radio Poznań", "https://radio.invalid/poznan"),
                Stream("stream-2", "Radio Drugie", "https://radio.invalid/drugi")
            }
        },
        ["collectionOrders"] = new JsonObject
        {
            ["libraryAddedItemIdsBySession"] = new JsonObject
            {
                ["wiim"] = new JsonArray("stream-1", "stream-2")
            },
            ["libraryItemIdsBySession"] = new JsonObject
            {
                ["wiim"] = new JsonArray("stream-1", "stream-2")
            }
        }
    };

    private static JsonObject Stream(string id, string name, string url) => new()
    {
        ["id"] = id,
        ["name"] = name,
        ["streamUrl"] = url,
        ["addedUtcTicks"] = 1
    };

    private static JsonArray Streams(JsonObject root) =>
        (JsonArray)root["wiiM"]!["networkStreams"]!;
}
