using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using AccessibleMediaController.ReleaseProfiles;

namespace AccessibleMediaController.PythonUpdater;

internal static class Program
{
    // Proces, skaner antywirusowy albo indeksator potrafi jeszcze przez ulamek
    // sekundy trzymac zamkniety plik EXE. Jedna natychmiastowa proba powodowala
    // poprawne wycofanie calej aktualizacji dokladnie na pliku aktualizatora.
    private static readonly TimeSpan FileReplacementTimeout = TimeSpan.FromSeconds(10);
    private static readonly TimeSpan FileReplacementRetryDelay = TimeSpan.FromMilliseconds(200);

    private const int SupportedBundleFormat = 1;
    private const int SupportedInterfaceVersion = 1;
    private const int SupportedHostProtocolVersion = 1;
    private const int Success = 0;
    private const int BadArguments = 2;
    private const int AppStillRunning = 3;
    private const int InvalidPackage = 4;
    private const int InstallFailed = 5;
    private const int UpdaterAlreadyRunning = 6;

    [STAThread]
    private static int Main(string[] args)
    {
        ReleaseProfileDescriptor? profile = null;
        var silentRequested = args.Any(argument =>
            string.Equals(argument, "--silent", StringComparison.OrdinalIgnoreCase));
        try
        {
            var options = Options.Parse(args);
            if (options is null)
            {
                if (!silentRequested)
                {
                    Show(null, "Podaj folder przygotowanej aktualizacji i folder programu.\n\n"
                         + "AMC-Python-Updater.exe --source KATALOG --target KATALOG "
                         + "[--wait-pid NUMER] [--launch PLIK] [--silent]", true);
                }
                return BadArguments;
            }

            profile = LoadReleaseProfile(options.Source);

            // Windows nie pozwala niezawodnie podmienić uruchomionego pliku
            // wykonywalnego. Gdy aktualizator startuje z katalogu AMC, najpierw
            // uruchamiamy jego roboczą kopię poza katalogiem instalacji. Dzięki
            // temu paczka może również bezpiecznie zaktualizować sam updater.
            if (RelaunchOutsideInstallation(options, args, profile))
                return Success;

            using var updaterInstance = UpdaterInstanceLease.TryAcquire(
                profile.UpdaterMutexName);
            if (!updaterInstance.IsOwner)
            {
                if (!options.Silent)
                    Show(profile, $"Aktualizator {profile.DisplayName} już działa.", true);
                return UpdaterAlreadyRunning;
            }

            // Kopia robocza nie może dotknąć pliku starego aktualizatora,
            // dopóki proces-rodzic nadal go wykonuje. Samo Process.Start i
            // natychmiastowy return powodowały na Windows wyścig: pomocnik
            // dochodził do AMC-Python-Updater.exe przed faktycznym wyjściem
            // rodzica, a następnie cała transakcja poprawnie się wycofywała.
            if (!WaitForApplication(options.WaitUpdaterPid))
            {
                Console.Error.WriteLine(
                    "Aktualizacja zatrzymana: nie zakończył się proces-rodzic aktualizatora.");
                if (!options.Silent)
                {
                    Show(profile, "Aktualizacja nie została rozpoczęta, ponieważ poprzedni "
                         + "proces aktualizatora nie zakończył się.", true);
                }
                return AppStillRunning;
            }

            // Najpierw sprawdzamy całą paczkę. Wadliwa albo niezgodna
            // aktualizacja nie może bez potrzeby zamknąć działającego AMC.
            var manifest = LoadAndVerify(options.Source, options.Target, profile);

            // Zwykłe WM_CLOSE uruchamia tę samą ścieżkę co Alt+F4. Interfejs
            // sprawdza żywy stan nagrywania i może bezpiecznie odmówić. Nigdy
            // nie zabijamy procesu i nie podmieniamy plików, dopóki choć jeden
            // składnik z katalogu instalacji nadal działa.
            if (!SafeApplicationStop.RequestAndWait(
                    options.Target,
                    profile,
                    options.WaitPid,
                    TimeSpan.FromSeconds(30)))
            {
                var blockers = InstalledProcessGuard.RunningComponents(
                    options.Target);
                Console.Error.WriteLine(
                    blockers.Count == 0
                        ? "Aktualizacja zatrzymana: wskazany proces AMC nadal istnieje."
                        : "Aktualizacja zatrzymana przez składniki instalacji: "
                          + string.Join(
                              "; ",
                              blockers.Select(item =>
                                  $"PID {item.ProcessId}: {item.Executable}")));
                if (!options.Silent)
                {
                    Show(profile, $"Aktualizacja nie została rozpoczęta, ponieważ {profile.DisplayName} nadal działa. "
                         + "Może trwać nagrywanie. Zatrzymaj je i spróbuj ponownie.", true);
                }
                return AppStillRunning;
            }
            // --wait-pid pilnuje procesu, który uruchomił aktualizację, ale
            // nie obejmuje osieroconego runtime\python.exe ani hosta audio.
            // Sprawdzamy cały katalog PRZED utworzeniem .aktualizacja-*.
            // Odmowa nie zostawia więc kopii transakcji i nie dochodzi do
            // częściowej podmiany działającej wersji.
            if (InstalledProcessGuard.HasRunningComponent(options.Target))
            {
                if (!options.Silent)
                {
                    Show(profile, $"Aktualizacja nie została rozpoczęta, ponieważ {profile.DisplayName} "
                         + "lub jeden z jego składników nadal działa. Może trwać "
                         + "nagrywanie. Zamknij program bezpiecznie i spróbuj ponownie.", true);
                }
                return AppStillRunning;
            }
            ApplyPackage(options.Source, options.Target, manifest.Files);

            if (!string.IsNullOrWhiteSpace(options.Launch))
            {
                var launch = ResolveInside(options.Target, options.Launch, mustExist: true);
                Process.Start(new ProcessStartInfo
                {
                    FileName = launch,
                    WorkingDirectory = options.Target,
                    UseShellExecute = true,
                });
            }

            if (!options.Silent)
            {
                Show(profile, $"Aktualizacja {profile.DisplayName} została zainstalowana.", false);
            }
            return Success;
        }
        catch (InvalidDataException exception)
        {
            Console.Error.WriteLine("Pakiet aktualizacji został odrzucony: " + exception);
            if (!silentRequested)
                Show(profile, "Pakiet aktualizacji został odrzucony: " + exception.Message, true);
            return InvalidPackage;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(
                $"Nie udało się zainstalować aktualizacji {profile?.DisplayName ?? "AMC"}: "
                + exception);
            if (!silentRequested)
                Show(
                    profile,
                    $"Nie udało się zainstalować aktualizacji {profile?.DisplayName ?? "AMC"}: "
                    + exception.Message,
                    true);
            return InstallFailed;
        }
    }

    private static bool RelaunchOutsideInstallation(
        Options options,
        string[] args,
        ReleaseProfileDescriptor profile)
    {
        var current = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(current) || !IsInside(options.Target, current))
            return false;

        var helperDirectory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            profile.UpdaterHelperFolder.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(helperDirectory);
        // Stala nazwa pomocnika byla druga blokada: poprzedni alert albo
        // skaner mogl nadal trzymac ten jeden plik i kolejna proba konczyla
        // sie jeszcze przed transakcja. Stare kopie sprzatamy best effort, a
        // kazde uruchomienie dostaje wlasna nazwe.
        foreach (var oldHelper in Directory.EnumerateFiles(
                     helperDirectory,
                     profile.UpdaterHelperExecutablePrefix + "*.exe"))
        {
            try
            {
                File.Delete(oldHelper);
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException)
            {
                // Dzialajacy stary pomocnik moze jeszcze konczyc poprzednia
                // probe. Unikalna nazwa ponizej nie musi na niego czekac.
            }
        }
        var helper = Path.Combine(
            helperDirectory,
            $"{profile.UpdaterHelperExecutablePrefix}-{Guid.NewGuid():N}.exe");
        File.Copy(current, helper, overwrite: true);

        var start = new ProcessStartInfo
        {
            FileName = helper,
            WorkingDirectory = helperDirectory,
            UseShellExecute = false,
        };
        foreach (var argument in args)
            start.ArgumentList.Add(argument);
        // Ten wewnętrzny identyfikator jest niezależny od --wait-pid
        // właściwej aplikacji. Pomocnik musi zaczekać na oba procesy.
        start.ArgumentList.Add("--wait-updater-pid");
        start.ArgumentList.Add(Environment.ProcessId.ToString());
        Process.Start(start);
        return true;
    }

    private static bool WaitForApplication(int? pid)
    {
        if (pid is null || pid <= 0) return true;
        try
        {
            using var process = Process.GetProcessById(pid.Value);
            return process.WaitForExit(30_000);
        }
        catch (ArgumentException)
        {
            return true;
        }
    }

    private static ReleaseProfileDescriptor LoadReleaseProfile(string source) =>
        ResolveReleaseProfile(ReadManifest(source));

    private static Manifest ReadManifest(string root)
    {
        root = Path.GetFullPath(root);
        if (!Directory.Exists(root))
            throw new InvalidDataException("nie ma folderu pakietu");
        var manifestPath = Path.Combine(root, "bundle-manifest.json");
        if (!File.Exists(manifestPath))
            throw new InvalidDataException("brak bundle-manifest.json");
        if (new FileInfo(manifestPath).Length > 8 * 1024 * 1024)
            throw new InvalidDataException("bundle-manifest.json jest zbyt duży");
        try
        {
            return JsonSerializer.Deserialize<Manifest>(
                File.ReadAllText(manifestPath),
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                ?? throw new InvalidDataException("pusty manifest");
        }
        catch (JsonException)
        {
            throw new InvalidDataException("bundle-manifest.json ma nieprawidłowy format");
        }
    }

    private static ReleaseProfileDescriptor ResolveReleaseProfile(Manifest manifest) =>
        ReleaseProfileContract.Validate(
            manifest.ReleaseProfileSchema,
            manifest.ReleaseProfile,
            manifest.ProductId,
            manifest.DisplayName,
            manifest.InstallId,
            manifest.UpdateChannel,
            manifest.UiStateFolder,
            manifest.RoamingProfileFolder,
            manifest.LocalProfileFolder,
            manifest.CacheFolder,
            manifest.LogFolder,
            manifest.CredentialNamespace,
            manifest.Sessions,
            manifest.Capabilities);

    internal static Manifest LoadAndVerify(
        string source,
        string target,
        ReleaseProfileDescriptor expectedProfile)
    {
        source = Path.GetFullPath(source);
        target = Path.GetFullPath(target);
        if (!Directory.Exists(source)) throw new InvalidDataException("nie ma folderu źródłowego");
        if (!Directory.Exists(target)) throw new InvalidDataException("nie ma folderu programu");
        if (string.Equals(source.TrimEnd('\\'), target.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("źródło i folder programu są tym samym miejscem");
        if (!File.Exists(Path.Combine(target, "AMC.exe")))
            throw new InvalidDataException(
                $"folder docelowy nie zawiera {expectedProfile.DisplayName}");

        var manifest = ReadManifest(source);
        var sourceProfile = ResolveReleaseProfile(manifest);
        if (!string.Equals(
                sourceProfile.InstallId,
                expectedProfile.InstallId,
                StringComparison.Ordinal))
            throw new InvalidDataException("profil pakietu zmienił się podczas uruchamiania aktualizacji");
        ValidateInstalledProfile(target, sourceProfile);
        if (manifest.Files is null || manifest.Files.Count == 0)
            throw new InvalidDataException("manifest nie zawiera plików");
        if (manifest.BundleFormatVersion != SupportedBundleFormat
            || manifest.InterfaceVersion != SupportedInterfaceVersion
            || manifest.HostProtocolVersion != SupportedHostProtocolVersion)
            throw new InvalidDataException("wersje składników aktualizacji nie są zgodne");
        if (!string.Equals(manifest.Application, "AMC Python", StringComparison.Ordinal)
            || !string.Equals(manifest.EntryPoint, "AMC.exe", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("manifest dotyczy innego programu");
        if (!manifest.Files.Contains("AMC.exe", StringComparer.OrdinalIgnoreCase))
            throw new InvalidDataException("aktualizacja nie zawiera AMC.exe");
        if (manifest.FileHashes is null || manifest.FileHashes.Count != manifest.Files.Count)
            throw new InvalidDataException("manifest nie zawiera sum wszystkich plików");
        if (manifest.FileSizes is not null
            && manifest.FileSizes.Count > 0
            && manifest.FileSizes.Count != manifest.Files.Count)
            throw new InvalidDataException("manifest nie zawiera rozmiarów wszystkich plików");

        foreach (var relative in manifest.Files)
        {
            var path = ResolveInside(source, relative, mustExist: true);
            if (manifest.FileSizes is { Count: > 0 }
                && (!manifest.FileSizes.TryGetValue(relative, out var expectedSize)
                    || expectedSize < 0
                    || new FileInfo(path).Length != expectedSize))
                throw new InvalidDataException($"niezgodny rozmiar pliku {relative}");
            if (!manifest.FileHashes.TryGetValue(relative, out var expected)
                || expected.Length != 64)
                throw new InvalidDataException($"brak sumy SHA-256 dla {relative}");
            var actual = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
            if (!string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"niezgodna suma SHA-256 pliku {relative}");
            _ = ResolveInside(target, relative, mustExist: false);
        }
        return manifest;
    }

    private static void ValidateInstalledProfile(
        string target,
        ReleaseProfileDescriptor sourceProfile)
    {
        var installed = ReadManifest(target);
        if (installed.ReleaseProfileSchema == 0
            && string.IsNullOrWhiteSpace(installed.ReleaseProfile))
        {
            var folder = Path.GetFileName(
                Path.GetFullPath(target).TrimEnd(
                    Path.DirectorySeparatorChar,
                    Path.AltDirectorySeparatorChar));
            if (sourceProfile != ReleaseProfileContract.Test
                || !string.Equals(folder, "AMC Python", StringComparison.OrdinalIgnoreCase)
                || !string.Equals(installed.Application, "AMC Python", StringComparison.Ordinal)
                || !string.Equals(installed.EntryPoint, "AMC.exe", StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException(
                    "starsza instalacja nie ma zgodnej tożsamości profilu wydania");
            return;
        }

        ReleaseProfileContract.ValidateCompatibleInstalled(
            sourceProfile,
            installed.ReleaseProfileSchema,
            installed.ReleaseProfile,
            installed.ProductId,
            installed.DisplayName,
            installed.InstallId,
            installed.UpdateChannel,
            installed.UiStateFolder,
            installed.RoamingProfileFolder,
            installed.LocalProfileFolder,
            installed.CacheFolder,
            installed.LogFolder,
            installed.CredentialNamespace,
            installed.Sessions,
            installed.Capabilities);
    }

    private static void ApplyPackage(string source, string target, IReadOnlyList<string> files)
    {
        var transaction = Path.Combine(target, ".aktualizacja-" + Guid.NewGuid().ToString("N"));
        var staged = Path.Combine(transaction, "nowe");
        var backup = Path.Combine(transaction, "kopia");
        Directory.CreateDirectory(staged);
        var replaced = new List<(string Destination, string? Backup)>();
        try
        {
            foreach (var relative in files)
            {
                var input = ResolveInside(source, relative, mustExist: true);
                var prepared = ResolveInside(staged, relative, mustExist: false);
                Directory.CreateDirectory(Path.GetDirectoryName(prepared)!);
                File.Copy(input, prepared, overwrite: true);
            }

            foreach (var relative in files)
            {
                var prepared = ResolveInside(staged, relative, mustExist: true);
                var destination = ResolveInside(target, relative, mustExist: false);
                Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
                // Nie ruszaj pliku, ktory juz ma dokladnie oczekiwana tresc.
                // W szczegolnosci niezmieniony AMC.exe moze byc chroniony
                // przez Windows albo skaner, mimo ze aplikacja juz nie
                // dziala. Dotychczas aktualizator bez potrzeby usuwal taki
                // plik i wycofywal cala poprawna aktualizacje interfejsu.
                if (File.Exists(destination)
                    && FilesHaveSameContent(prepared, destination))
                {
                    File.Delete(prepared);
                    continue;
                }
                string? saved = null;
                if (File.Exists(destination))
                {
                    saved = ResolveInside(backup, relative, mustExist: false);
                    Directory.CreateDirectory(Path.GetDirectoryName(saved)!);
                    File.Copy(destination, saved, overwrite: true);
                }
                replaced.Add((destination, saved));
                ReplacePreparedFile(prepared, destination, relative);
            }

            File.Copy(
                Path.Combine(source, "bundle-manifest.json"),
                Path.Combine(target, "bundle-manifest.json"),
                overwrite: true);
            Directory.Delete(transaction, recursive: true);
        }
        catch
        {
            var rollbackComplete = true;
            for (var index = replaced.Count - 1; index >= 0; index--)
            {
                var (destination, saved) = replaced[index];
                try
                {
                    if (saved is not null && File.Exists(saved))
                        File.Copy(saved, destination, overwrite: true);
                    else if (File.Exists(destination))
                        File.Delete(destination);
                }
                catch
                {
                    rollbackComplete = false;
                    // Pierwotny błąd jest ważniejszy; zachowana kopia zostaje
                    // w folderze .aktualizacja-* do ręcznego odzyskania.
                }
            }
            // Gdy kazdy plik wrocil na miejsce, katalog transakcji nie jest
            // juz kopia ratunkowa. Dotad pojedyncza chwilowa blokada zostawiala
            // ponad sto megabajtow po kazdej probie aktualizacji.
            if (rollbackComplete)
            {
                try
                {
                    Directory.Delete(transaction, recursive: true);
                }
                catch
                {
                    // Nie zaslaniamy pierwotnego bledu aktualizacji tylko tym,
                    // ze system jeszcze nie pozwolil posprzatac katalogu.
                }
            }
            throw;
        }
    }

    private static bool FilesHaveSameContent(string first, string second)
    {
        if (new FileInfo(first).Length != new FileInfo(second).Length)
            return false;

        using var firstStream = new FileStream(
            first,
            FileMode.Open,
            FileAccess.Read,
            FileShare.ReadWrite | FileShare.Delete);
        using var secondStream = new FileStream(
            second,
            FileMode.Open,
            FileAccess.Read,
            FileShare.ReadWrite | FileShare.Delete);
        var firstHash = SHA256.HashData(firstStream);
        var secondHash = SHA256.HashData(secondStream);
        return CryptographicOperations.FixedTimeEquals(firstHash, secondHash);
    }

    private static void ReplacePreparedFile(
        string prepared,
        string destination,
        string relative)
    {
        var deadline = DateTime.UtcNow + FileReplacementTimeout;
        while (true)
        {
            try
            {
                // File.Move(..., overwrite: true) na Windows potrafi odmowic
                // zastapienia pliku EXE. Kopia poprzedniej wersji juz istnieje,
                // wiec usuniecie i przeniesienie pozostaja transakcyjne.
                if (File.Exists(destination)) File.Delete(destination);
                File.Move(prepared, destination);
                return;
            }
            catch (Exception exception) when (
                exception is IOException or UnauthorizedAccessException)
            {
                if (DateTime.UtcNow >= deadline)
                {
                    throw new IOException(
                        $"nie można podmienić pliku {relative}: {exception.Message}",
                        exception);
                }
                Thread.Sleep(FileReplacementRetryDelay);
            }
        }
    }

    private static string ResolveInside(string root, string relative, bool mustExist)
    {
        if (string.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative))
            throw new InvalidDataException("manifest zawiera nieprawidłową ścieżkę");
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)
                       + Path.DirectorySeparatorChar;
        var full = Path.GetFullPath(Path.Combine(fullRoot, relative.Replace('/', Path.DirectorySeparatorChar)));
        if (!full.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("manifest próbuje wyjść poza folder aktualizacji");
        if (mustExist && !File.Exists(full))
            throw new InvalidDataException($"brak pliku {relative}");
        return full;
    }

    private static bool IsInside(string root, string path)
    {
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)
                       + Path.DirectorySeparatorChar;
        var fullPath = Path.GetFullPath(path);
        return fullPath.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase);
    }

    private static void Show(
        ReleaseProfileDescriptor? profile,
        string text,
        bool error)
    {
        MessageBox(
            IntPtr.Zero,
            text,
            "Aktualizator " + (profile?.DisplayName ?? "AMC"),
            error ? 0x10u : 0x40u);
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(IntPtr owner, string text, string caption, uint type);

    internal sealed class Manifest
    {
        public int BundleFormatVersion { get; set; }
        public int InterfaceVersion { get; set; }
        public int HostProtocolVersion { get; set; }
        public string Application { get; set; } = "";
        public string EntryPoint { get; set; } = "";
        public int ReleaseProfileSchema { get; set; }
        public string ReleaseProfile { get; set; } = "";
        public string ProductId { get; set; } = "";
        public string DisplayName { get; set; } = "";
        public string InstallId { get; set; } = "";
        public string UpdateChannel { get; set; } = "";
        public string UiStateFolder { get; set; } = "";
        public string RoamingProfileFolder { get; set; } = "";
        public string LocalProfileFolder { get; set; } = "";
        public string CacheFolder { get; set; } = "";
        public string LogFolder { get; set; } = "";
        public string CredentialNamespace { get; set; } = "";
        public List<string> Sessions { get; set; } = [];
        public List<string> Capabilities { get; set; } = [];
        public List<string> Files { get; set; } = [];
        public Dictionary<string, string> FileHashes { get; set; } =
            new(StringComparer.OrdinalIgnoreCase);
        public Dictionary<string, long> FileSizes { get; set; } =
            new(StringComparer.OrdinalIgnoreCase);
    }

    private sealed record Options(
        string Source,
        string Target,
        int? WaitPid,
        int? WaitUpdaterPid,
        string? Launch,
        bool Silent)
    {
        public static Options? Parse(string[] args)
        {
            string? source = null;
            string? target = null;
            string? launch = null;
            int? waitPid = null;
            int? waitUpdaterPid = null;
            var silent = false;
            for (var index = 0; index < args.Length; index++)
            {
                switch (args[index].ToLowerInvariant())
                {
                    case "--source" when index + 1 < args.Length:
                        source = args[++index];
                        break;
                    case "--target" when index + 1 < args.Length:
                        target = args[++index];
                        break;
                    case "--wait-pid" when index + 1 < args.Length
                        && int.TryParse(args[++index], out var parsed):
                        waitPid = parsed;
                        break;
                    case "--wait-updater-pid" when index + 1 < args.Length
                        && int.TryParse(args[++index], out var parsedUpdater):
                        waitUpdaterPid = parsedUpdater;
                        break;
                    case "--launch" when index + 1 < args.Length:
                        launch = args[++index];
                        break;
                    case "--silent":
                        silent = true;
                        break;
                    default:
                        return null;
                }
            }
            return source is not null && target is not null
                ? new Options(
                    Path.GetFullPath(source),
                    Path.GetFullPath(target),
                    waitPid,
                    waitUpdaterPid,
                    launch,
                    silent)
                : null;
        }
    }
}
