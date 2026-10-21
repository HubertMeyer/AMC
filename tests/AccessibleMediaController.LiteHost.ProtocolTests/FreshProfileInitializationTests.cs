using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.LiteHost;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class FreshProfileInitializationTests
{
    public static void Run()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            "amc-fresh-profile-" + Guid.NewGuid().ToString("N"));
        try
        {
            var local = Path.Combine(root, "local", "AMC", "profile");
            var roaming = Path.Combine(root, "roaming", "AMC", "profile");
            var library = Path.Combine(local, "library.db");
            var podcasts = Path.Combine(local, "podcasts.db");
            var state = Path.Combine(roaming, "state.json");

            LiteFreshProfileInitializer.EnsureInitialized(library, podcasts, state);

            Assert.True(File.Exists(library), "swiezy profil tworzy library.db");
            Assert.True(File.Exists(podcasts), "swiezy profil tworzy podcasts.db");
            Assert.True(File.Exists(state), "swiezy profil tworzy state.json");

            var loaded = new ConfigurationStore(state, library, podcasts).LoadOrCreate();
            Assert.True(
                loaded.SchemaVersion == ConfigurationStore.CurrentSchemaVersion,
                "swiezy profil ma aktualny schemat");

            var stateBefore = File.ReadAllBytes(state);
            var libraryBefore = File.ReadAllBytes(library);
            var podcastsBefore = File.ReadAllBytes(podcasts);
            LiteFreshProfileInitializer.EnsureInitialized(library, podcasts, state);
            Assert.True(stateBefore.SequenceEqual(File.ReadAllBytes(state)),
                "ponowny start nie przepisuje state.json");
            Assert.True(libraryBefore.SequenceEqual(File.ReadAllBytes(library)),
                "ponowny start nie przepisuje library.db");
            Assert.True(podcastsBefore.SequenceEqual(File.ReadAllBytes(podcasts)),
                "ponowny start nie przepisuje podcasts.db");
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }

        Console.WriteLine("OK: swiezy profil hosta jest kompletny i idempotentny");
    }
}
