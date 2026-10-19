using System.Text.Json;
using AccessibleMediaController.LiteHost;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class AccountSettingsStoreTests
{
    public static void Run()
    {
        var directory = Path.Combine(
            Path.GetTempPath(),
            "amc-account-settings-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            var path = Path.Combine(directory, "state.json");
            File.WriteAllText(path, """
            {
              "schemaVersion": 54,
              "radio": { "keep": "radio" },
              "spotify": { "clientId": "old", "futureField": "keep" }
            }
            """);

            LiteAccountSettingsStore.UpdateSection(
                path,
                "spotify",
                new AccountSettings("new", "playlist-modify-private"));

            using var document = JsonDocument.Parse(File.ReadAllText(path));
            var root = document.RootElement;
            var spotify = root.GetProperty("spotify");
            Check(root.GetProperty("radio").GetProperty("keep").GetString() == "radio",
                "zapis konta nadpisał obcą sekcję profilu");
            Check(spotify.GetProperty("clientId").GetString() == "new"
                && spotify.GetProperty("grantedScope").GetString() == "playlist-modify-private",
                "zapis konta nie utrwalił nowych pól");
            Check(spotify.GetProperty("futureField").GetString() == "keep",
                "zapis konta usunął nieznane pole przyszłej wersji");
            Check(File.Exists(path + ".bak"),
                "atomowy zapis konta nie pozostawił kopii poprzedniego profilu");
            Check(!File.Exists(path + ".account.tmp"),
                "po atomowym zapisie pozostał plik tymczasowy");
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private sealed record AccountSettings(string ClientId, string GrantedScope);

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
