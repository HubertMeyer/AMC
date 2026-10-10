using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;

namespace AccessibleMediaController.PythonUpdater;

internal static class Program
{
    private const int Success = 0;
    private const int BadArguments = 2;
    private const int AppStillRunning = 3;
    private const int InvalidPackage = 4;
    private const int InstallFailed = 5;

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            var options = Options.Parse(args);
            if (options is null)
            {
                Show("Podaj folder przygotowanej aktualizacji i folder AMC Python.\n\n"
                     + "AMC-Python-Updater.exe --source KATALOG --target KATALOG "
                     + "[--wait-pid NUMER] [--launch PLIK] [--silent]", true);
                return BadArguments;
            }

            // Windows nie pozwala niezawodnie podmienić uruchomionego pliku
            // wykonywalnego. Gdy aktualizator startuje z katalogu AMC, najpierw
            // uruchamiamy jego roboczą kopię poza katalogiem instalacji. Dzięki
            // temu paczka może również bezpiecznie zaktualizować sam updater.
            if (RelaunchOutsideInstallation(options, args))
                return Success;

            if (!WaitForApplication(options.WaitPid))
            {
                Show("Aktualizacja nie została rozpoczęta, ponieważ AMC Python nadal działa. "
                     + "Może trwać nagrywanie. Zatrzymaj je i spróbuj ponownie.", true);
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
            Show("Pakiet aktualizacji został odrzucony: " + exception.Message, true);
            return InvalidPackage;
        }
        catch (Exception exception)
        {
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
        var helper = Path.Combine(helperDirectory, "AMC-Python-Updater.exe");
        File.Copy(current, helper, overwrite: true);

        var start = new ProcessStartInfo
        {
            FileName = helper,
            WorkingDirectory = helperDirectory,
            UseShellExecute = false,
        };
        foreach (var argument in args)
            start.ArgumentList.Add(argument);
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
        if (!File.Exists(Path.Combine(target, "AMC-wx-Lite.cmd")))
            throw new InvalidDataException("folder docelowy nie zawiera AMC Python");

        var manifestPath = Path.Combine(source, "bundle-manifest.json");
        if (!File.Exists(manifestPath)) throw new InvalidDataException("brak bundle-manifest.json");
        var manifest = JsonSerializer.Deserialize<Manifest>(
            File.ReadAllText(manifestPath),
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
            ?? throw new InvalidDataException("pusty manifest");
        if (manifest.Files is null || manifest.Files.Count == 0)
            throw new InvalidDataException("manifest nie zawiera plików");
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
                string? saved = null;
                if (File.Exists(destination))
                {
                    saved = ResolveInside(backup, relative, mustExist: false);
                    Directory.CreateDirectory(Path.GetDirectoryName(saved)!);
                    File.Copy(destination, saved, overwrite: true);
                }
                replaced.Add((destination, saved));
                File.Move(prepared, destination, overwrite: true);
            }

            File.Copy(
                Path.Combine(source, "bundle-manifest.json"),
                Path.Combine(target, "bundle-manifest.json"),
                overwrite: true);
            Directory.Delete(transaction, recursive: true);
        }
        catch
        {
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
                    // Pierwotny błąd jest ważniejszy; zachowana kopia zostaje
                    // w folderze .aktualizacja-* do ręcznego odzyskania.
                }
            }
            throw;
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
        public List<string> Files { get; set; } = [];
        public Dictionary<string, string> FileHashes { get; set; } =
            new(StringComparer.OrdinalIgnoreCase);
    }

    private sealed record Options(
        string Source,
        string Target,
        int? WaitPid,
        string? Launch,
        bool Silent)
    {
        public static Options? Parse(string[] args)
        {
            string? source = null;
            string? target = null;
            string? launch = null;
            int? waitPid = null;
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
                ? new Options(Path.GetFullPath(source), Path.GetFullPath(target), waitPid, launch, silent)
                : null;
        }
    }
}
