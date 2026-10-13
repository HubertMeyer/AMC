using System.Text.Json.Nodes;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.LiteHost;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class SonosOwnStreamsMutationTests
{
    public static void Run()
    {
        AddUpdatesDuplicateAndRemembersNewStream();
        EditRejectsDuplicateAddress();
        RemoveCleansBothOrders();
        ImportUsesTheSharedSonosRules();
        SortModeUsesTheOriginalSonosViewKey();
        Console.WriteLine("SonosOwnStreamsMutationTests: OK");
    }

    private static void AddUpdatesDuplicateAndRemembersNewStream()
    {
        var root = Profile();
        var updated = LiteSonosOwnStreamsMutation.Add(
            root,
            "Radio Poznań poprawione",
            " https://radio.invalid/poznan ");
        Assert.Equal("stream-1", updated.PreferredStreamId,
            "duplikat adresu zachowuje identyfikator");
        Assert.True(updated.UpdatedCount == 1 && updated.AddedCount == 0,
            "duplikat adresu aktualizuje wpis zamiast go powielać");

        var added = LiteSonosOwnStreamsMutation.Add(
            root,
            "Radio Opole",
            "https://radio.invalid/opole");
        Assert.True(added.AddedCount == 1 && added.PreferredStreamId.Length == 32,
            "nowa stacja dostaje stabilny identyfikator AMC");
        Assert.True(Streams(root).Count == 3,
            "dodanie zapisuje dokładnie jedną stację");
        Assert.True(Order(root, custom: false).Last()!.GetValue<string>()
                    == added.PreferredStreamId,
            "chronologia dopisuje nową stację na końcu");
    }

    private static void EditRejectsDuplicateAddress()
    {
        var root = Profile();
        try
        {
            LiteSonosOwnStreamsMutation.Edit(
                root,
                "stream-1",
                "Duplikat",
                "https://radio.invalid/drugi");
            throw new InvalidOperationException(
                "edycja przyjęła adres zapisany przy innej stacji");
        }
        catch (LiteRequestException exception)
        {
            Assert.True(exception.Message.Contains("Radio Drugie", StringComparison.Ordinal),
                "komunikat duplikatu używa nazwy użytkowej");
        }

        var edited = LiteSonosOwnStreamsMutation.Edit(
            root,
            "stream-1",
            "Radio Nowe",
            "https://radio.invalid/nowe");
        Assert.Equal("Radio Nowe", edited.Title,
            "edycja zwraca nazwę do komunikatu");
        var editInfo = LiteSonosOwnStreamsMutation.ReadForEdit(root, "stream-1");
        Assert.Equal("https://radio.invalid/nowe", editInfo.StreamUrl,
            "adres wraca tylko jawną drogą edycji");
    }

    private static void RemoveCleansBothOrders()
    {
        var root = Profile();
        var titles = LiteSonosOwnStreamsMutation.Remove(root, ["stream-1"]);
        Assert.True(titles.SequenceEqual(["Radio Poznań"]),
            "usunięcie zwraca nazwę użytkową");
        Assert.True(Streams(root).Count == 1,
            "usunięcie zostawia pozostałą stację");
        Assert.True(Order(root, custom: false).Count == 1
                    && Order(root, custom: true).Count == 1,
            "usunięcie czyści chronologię i kolejność własną");
    }

    private static void ImportUsesTheSharedSonosRules()
    {
        var root = Profile();
        var result = LiteSonosOwnStreamsMutation.Import(
            root,
            [
                new LiteSonosOwnStreamDraft(
                    "Duplikat",
                    "https://radio.invalid/poznan"),
                new LiteSonosOwnStreamDraft(
                    "Żuraw",
                    "https://radio.invalid/zuraw"),
                new LiteSonosOwnStreamDraft("Plik lokalny", "file:///C:/sekret.mp3")
            ],
            parserSkipped: 1);
        Assert.True(result.AddedCount == 1 && result.SkippedCount == 3,
            "import liczy duplikat, odrzucony adres i błąd parsera");
        Assert.True(Streams(root).Count == 3,
            "import dopisuje tylko prawidłową nową stację");
    }

    private static void SortModeUsesTheOriginalSonosViewKey()
    {
        var root = Profile();
        LiteSonosOwnStreamsMutation.SetSortMode(root, CollectionSortMode.Alphabetical);
        Assert.Equal(
            "Alphabetical",
            root["sessionNavigation"]!["sessions"]!["sonos"]!
                ["collectionSortModes"]!["Moje stacje"]!.GetValue<string>(),
            "sortowanie zapisuje ten sam klucz widoku co główne AMC");
    }

    private static JsonObject Profile() => new()
    {
        ["sonos"] = new JsonObject
        {
            ["ownStreams"] = new JsonArray
            {
                Stream("stream-1", "Radio Poznań", "https://radio.invalid/poznan"),
                Stream("stream-2", "Radio Drugie", "https://radio.invalid/drugi")
            }
        },
        ["collectionOrders"] = new JsonObject
        {
            ["libraryAddedItemIdsBySession"] = new JsonObject
            {
                ["sonos|Moje stacje"] = new JsonArray("stream-1", "stream-2")
            },
            ["libraryItemIdsBySession"] = new JsonObject
            {
                ["sonos|Moje stacje"] = new JsonArray("stream-1", "stream-2")
            }
        }
    };

    private static JsonObject Stream(string id, string name, string url) => new()
    {
        ["id"] = id,
        ["name"] = name,
        ["streamUrl"] = url
    };

    private static JsonArray Streams(JsonObject root) =>
        (JsonArray)root["sonos"]!["ownStreams"]!;

    private static JsonArray Order(JsonObject root, bool custom) =>
        (JsonArray)root["collectionOrders"]![
            custom ? "libraryItemIdsBySession" : "libraryAddedItemIdsBySession"]!
            ["sonos|Moje stacje"]!;
}
