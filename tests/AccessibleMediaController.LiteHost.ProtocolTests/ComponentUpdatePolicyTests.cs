using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class ComponentUpdatePolicyTests
{
    public static void Run()
    {
        MissingProfileUsesSafeDefaults();
        SavedChoicesAreReadWithoutMigratingTheProfile();
        ExplicitOverridesWinWithoutWritingTheProfile();
        CheckIsDueAfterTwentyFourHours();
        Console.WriteLine("ComponentUpdatePolicyTests: OK");
    }

    private static void ExplicitOverridesWinWithoutWritingTheProfile()
    {
        using var document = System.Text.Json.JsonDocument.Parse("""
            {
              "checkAutomatically": false,
              "downloadAutomatically": true
            }
            """);
        var policy = LiteComponentUpdatePolicy.Resolve(null, document.RootElement);
        Assert.True(!policy.CheckAutomatically, "jawny wybór wxPython wyłącza sprawdzanie");
        Assert.True(policy.DownloadAutomatically, "jawny wybór wxPython włącza pobieranie");

        using var invalid = System.Text.Json.JsonDocument.Parse("""
            {
              "checkAutomatically": "false"
            }
            """);
        var inherited = LiteComponentUpdatePolicy.Resolve(null, invalid.RootElement);
        Assert.True(inherited.CheckAutomatically, "nieprawidłowy typ nie zmienia wartości odziedziczonej");
        Assert.True(inherited.DownloadAutomatically, "brak pola zachowuje wartość odziedziczoną");
    }

    private static void MissingProfileUsesSafeDefaults()
    {
        var policy = LiteComponentUpdatePolicy.Read(null);
        Assert.True(policy.CheckAutomatically, "świeża instalacja sprawdza składniki");
        Assert.True(policy.DownloadAutomatically, "świeża instalacja pobiera składniki");
    }

    private static void SavedChoicesAreReadWithoutMigratingTheProfile()
    {
        var root = Path.Combine(Path.GetTempPath(), "amc-component-policy-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        var path = Path.Combine(root, "state.json");
        try
        {
            File.WriteAllText(path, """
                {
                  "Settings": {
                    "Updates": {
                      "CheckAutomatically": false,
                      "DownloadAutomatically": false
                    }
                  }
                }
                """);
            var before = File.ReadAllText(path);
            var policy = LiteComponentUpdatePolicy.Read(path);
            Assert.True(!policy.CheckAutomatically, "profil może wyłączyć sprawdzanie");
            Assert.True(!policy.DownloadAutomatically, "profil może wyłączyć pobieranie");
            Assert.True(File.ReadAllText(path) == before, "odczyt nie zapisuje ani nie migruje profilu");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private static void CheckIsDueAfterTwentyFourHours()
    {
        var now = new DateTimeOffset(2026, 10, 20, 12, 0, 0, TimeSpan.Zero);
        Assert.True(LiteComponentUpdatePolicy.IsDue(null, now), "brak kontroli jest terminem kontroli");
        Assert.True(
            !LiteComponentUpdatePolicy.IsDue(now.Subtract(TimeSpan.FromHours(23)), now),
            "świeża kontrola nie powtarza sieci");
        Assert.True(
            LiteComponentUpdatePolicy.IsDue(now.Subtract(TimeSpan.FromHours(25)), now),
            "stara kontrola jest ponawiana");
    }
}
