using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

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

    [STAThread]
    private static int Main(string[] args)
    {
        var silentRequested = args.Any(argument =>
            string.Equals(argument, "--silent", StringComparison.OrdinalIgnoreCase));
        try
        {
            var options = Options.Parse(args);
            if (options is null)
            {
                if (!silentRequested)
                {
                    Show("Podaj folder przygotowanej aktualizacji i folder AMC Python.\n\n"
                         + "AMC-Python-Updater.exe --source KATALOG --target KATALOG "
                         + "[--wait-pid NUMER] [--launch PLIK] [--silent]", true);
                }
                return BadArguments;
            }

            // Windows nie pozwala niezawodnie podmienić uruchomionego pliku
            // wykonywalnego. Gdy aktualizator startuje z katalogu AMC, najpierw
            // uruchamiamy jego roboczą kopię poza katalogiem instalacji. Dzięki
            // temu paczka może również bezpiecznie zaktualizować sam updater.
            if (RelaunchOutsideInstallation(options, args))
                return Success;

            // Kopia robocza nie może dotknąć pliku starego aktualizatora,
            // dopóki proces-rodzic nadal go wykonuje. Samo Process.Start i
            // natychmiastowy return powodowały na Windows wyścig: pomocnik
            // dochodził do AMC-Python-Updater.exe przed faktycznym wyjściem
            // rodzica, a następnie cała transakcja poprawnie się wycofywała.
            if (!WaitForApplication(options.WaitUpdaterPid))
            {
                if (!options.Silent)
                {
                    Show("Aktualizacja nie została rozpoczęta, ponieważ poprzedni "
                         + "proces aktualizatora nie zakończył się.", true);
                }
                return AppStillRunning;
            }

            if (!WaitForApplication(options.WaitPid))
            {
                if (!options.Silent)
                {
                    Show("Aktualizacja nie została rozpoczęta, ponieważ AMC Python nadal działa. "
                         + "Może trwać nagrywanie. Zatrzymaj je i spróbuj ponownie.", true);
                }
                return AppStillRunning;
            }

            var manifest = LoadAndVerify(options.Source, options.Target);
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
                Show("Aktualizacja AMC Python została zainstalowana.", false);
            }
            return Success;
        }
        catch (InvalidDataException exception)
        {
            Console.Error.WriteLine("Pakiet aktualizacji został odrzucony: " + exception);
            if (!silentRequested)
                Show("Pakiet aktualizacji został odrzucony: " + exception.Message, true);
            return InvalidPackage;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Nie udało się zainstalować aktualizacji AMC Python: " + exception);
            if (!silentRequested)
                Show("Nie udało się zainstalować aktualizacji AMC Python: " + exception.Message, true);
            return InstallFailed;
        }
    }

    private static bool RelaunchOutsideInstallation(Options options, string[] args)
    {
        var current = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(current) || !IsInside(options.Target, current))
            return false;

        var helperDirectory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "AMC-Python",
            "Updater");
        Directory.CreateDirectory(helperDirectory);
        // Stala nazwa pomocnika byla druga blokada: poprzedni alert albo
        // skaner mogl nadal trzymac ten jeden plik i kolejna proba konczyla
        // sie jeszcze przed transakcja. Stare kopie sprzatamy best effort, a
        // kazde uruchomienie dostaje wlasna nazwe.
        foreach (var oldHelper in Directory.EnumerateFiles(
                     helperDirectory,
                     "AMC-Python-Updater*.exe"))
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
            $"AMC-Python-Updater-{Guid.NewGuid():N}.exe");
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

    private static Manifest LoadAndVerify(string source, string target)
    {
        source = Path.GetFullPath(source);
        target = Path.GetFullPath(target);
        if (!Directory.Exists(source)) throw new InvalidDataException("nie ma folderu źródłowego");
        if (!Directory.Exists(target)) throw new InvalidDataException("nie ma folderu programu");
        if (string.Equals(source.TrimEnd('\\'), target.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("źródło i folder programu są tym samym miejscem");
        if (!File.Exists(Path.Combine(target, "AMC.exe")))
            throw new InvalidDataException("folder docelowy nie zawiera AMC Python");

        var manifestPath = Path.Combine(source, "bundle-manifest.json");
        if (!File.Exists(manifestPath)) throw new InvalidDataException("brak bundle-manifest.json");
        var manifest = JsonSerializer.Deserialize<Manifest>(
            File.ReadAllText(manifestPath),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
            ?? throw new InvalidDataException("pusty manifest");
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

        foreach (var relative in manifest.Files)
        {
            var path = ResolveInside(source, relative, mustExist: true);
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

    private static void Show(string text, bool error)
    {
        MessageBox(IntPtr.Zero, text, "Aktualizator AMC Python", error ? 0x10u : 0x40u);
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(IntPtr owner, string text, string caption, uint type);

    private sealed class Manifest
    {
        public int BundleFormatVersion { get; set; }
        public int InterfaceVersion { get; set; }
        public int HostProtocolVersion { get; set; }
        public string Application { get; set; } = "";
        public string EntryPoint { get; set; } = "";
        public List<string> Files { get; set; } = [];
        public Dictionary<string, string> FileHashes { get; set; } =
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
