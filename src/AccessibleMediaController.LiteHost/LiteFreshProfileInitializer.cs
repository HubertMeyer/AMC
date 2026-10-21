using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Tworzy komplet trzech magazynow nowego profilu zanim host udostepni
/// operacje zapisu. Samo przekazanie docelowych sciezek nie wystarcza:
/// pierwszy publiczny profil nie ma jeszcze state.json ani library.db.
/// </summary>
internal static class LiteFreshProfileInitializer
{
    public static void EnsureInitialized(
        string libraryDatabasePath,
        string podcastsDatabasePath,
        string statePath)
    {
        var library = Path.GetFullPath(libraryDatabasePath);
        var podcasts = Path.GetFullPath(podcastsDatabasePath);
        var state = Path.GetFullPath(statePath);
        if (File.Exists(library) && File.Exists(podcasts) && File.Exists(state))
            return;

        CreateParentDirectory(library);
        CreateParentDirectory(podcasts);
        CreateParentDirectory(state);

        // ConfigurationStore jest jedynym miejscem znajacym aktualny schemat,
        // wartosci domyslne i bezpieczne migracje. Nie tworzymy recznie
        // szczatkowego JSON-a ani pustych plikow SQLite.
        _ = new ConfigurationStore(state, library, podcasts).LoadOrCreate();

        if (!File.Exists(library) || !File.Exists(podcasts) || !File.Exists(state))
            throw new InvalidDataException(
                "Nie udało się przygotować kompletnego profilu AMC.");
    }

    private static void CreateParentDirectory(string path)
    {
        var directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(directory))
            Directory.CreateDirectory(directory);
    }
}
