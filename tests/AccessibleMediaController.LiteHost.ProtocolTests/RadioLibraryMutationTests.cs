using System.Text.Json.Nodes;
using AccessibleMediaController.LiteHost;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class RadioLibraryMutationTests
{
    public static void Run()
    {
        ManualAddUpdatesDuplicateAndCreatesNewStation();
        ImportPromotesCatalogStationAndPreservesItsName();
        Console.WriteLine("RadioLibraryMutationTests: OK");
    }

    private static void ManualAddUpdatesDuplicateAndCreatesNewStation()
    {
        var root = Profile(
            Station("radio:old", "Stara nazwa", "https://radio.invalid/live", inLibrary: false));

        var updated = LiteRadioLibraryMutation.Apply(
            root,
            [new LiteRadioStationDraft("Nowa nazwa", "https://radio.invalid/live")],
            parserSkipped: 0,
            updateExistingTitles: true);

        var station = Stations(root).Single();
        Assert.True(updated.UpdatedCount == 1 && updated.AddedCount == 0,
            "ręczne dodanie tego samego adresu aktualizuje istniejącą stację");
        Assert.Equal("radio:old", updated.PreferredStationId,
            "fokus po aktualizacji wraca na istniejącą stację");
        Assert.Equal("Nowa nazwa", station["name"]?.GetValue<string>(),
            "ręczne dodanie zapisuje nową nazwę");
        Assert.True(station["hasCustomTitle"]?.GetValue<bool>() == true
                    && station["isInLibrary"]?.GetValue<bool>() == true,
            "zaktualizowana stacja ma własną nazwę i wraca do Biblioteki");

        var added = LiteRadioLibraryMutation.Apply(
            root,
            [new LiteRadioStationDraft("Nowe radio", "https://radio.invalid/new")],
            parserSkipped: 0,
            updateExistingTitles: true);
        var created = Stations(root).Single(value =>
            value["streamUrl"]?.GetValue<string>() == "https://radio.invalid/new");
        Assert.True(added.AddedCount == 1
                    && added.PreferredStationId?.StartsWith("radio:custom:", StringComparison.Ordinal) == true,
            "nowy ręczny wpis otrzymuje identyfikator stacji własnej");
        Assert.True(created["isCustom"]?.GetValue<bool>() == true
                    && created["isInLibrary"]?.GetValue<bool>() == true,
            "nowa stacja jest własna i widoczna w Bibliotece");
    }

    private static void ImportPromotesCatalogStationAndPreservesItsName()
    {
        var root = Profile(
            Station("radio:catalog", "Bogata nazwa katalogowa", "https://radio.invalid/catalog", inLibrary: false),
            Station("radio:saved", "Już zapisana", "https://radio.invalid/saved", inLibrary: true));

        var result = LiteRadioLibraryMutation.Apply(
            root,
            [
                new LiteRadioStationDraft("Nazwa z playlisty", "https://radio.invalid/catalog"),
                new LiteRadioStationDraft("Duplikat", "https://radio.invalid/saved"),
                new LiteRadioStationDraft("Nowa", "https://radio.invalid/new"),
                new LiteRadioStationDraft("Nowa drugi raz", "https://radio.invalid/new")
            ],
            parserSkipped: 2,
            updateExistingTitles: false);

        var catalog = Stations(root).Single(value =>
            value["id"]?.GetValue<string>() == "radio:catalog");
        Assert.True(result.PromotedCount == 1 && result.AddedCount == 1,
            "import przywraca katalogową stację i dodaje tylko jeden nowy adres");
        Assert.True(result.SkippedCount == 4,
            "wynik sumuje błędy parsera i duplikaty Biblioteki oraz playlisty");
        Assert.Equal("radio:catalog", result.PreferredStationId,
            "po imporcie pierwszeństwo fokusu ma przywrócona stacja");
        Assert.Equal("Bogata nazwa katalogowa", catalog["name"]?.GetValue<string>(),
            "import nie zastępuje bogatej nazwy katalogowej nazwą z pliku");
        Assert.True(catalog["isInLibrary"]?.GetValue<bool>() == true,
            "istniejąca stacja katalogowa zostaje włączona do Biblioteki");
    }

    private static JsonObject Profile(params JsonObject[] stations) => new()
    {
        ["radio"] = new JsonObject
        {
            ["stations"] = new JsonArray(stations.Select(station => (JsonNode)station).ToArray())
        }
    };

    private static JsonObject Station(string id, string name, string url, bool inLibrary) => new()
    {
        ["id"] = id,
        ["name"] = name,
        ["streamUrl"] = url,
        ["hasCustomTitle"] = false,
        ["isInLibrary"] = inLibrary
    };

    private static IEnumerable<JsonObject> Stations(JsonObject root) =>
        ((JsonArray)root["radio"]!["stations"]!).OfType<JsonObject>();
}
