using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using AccessibleMediaController.PythonLauncher;
using AccessibleMediaController.PythonUpdater;

namespace AccessibleMediaController.PythonLauncher.Tests;

internal static class Program
{
    private static readonly (string Name, Action Run)[] Tests =
    [
        ("poprawny pakiet", ValidBundleIsAccepted),
        ("uszkodzony plik", CorruptStartupFileIsRejected),
        ("niezgodny protokół", WrongProtocolIsRejected),
        ("wyjście poza katalog", TraversalIsRejected),
        ("prywatny runtime bez PYTHONPATH i bez alertów pythonw", LaunchPlanUsesOnlyPrivateRuntime),
        ("diagnostyka przez python.exe", DiagnosticUsesConsoleRuntime),
        ("jedna instancja launchera", OnlyOneLauncherOwnsTheLease),
        ("launcher rozpoznaje obecną i starszą nazwę okna", LauncherRecognizesCurrentAndLegacyTitles),
        ("ta sama kompilacja tylko pokazuje okno", SameBuildOnlyActivates),
        ("nowa kompilacja prosi o bezpieczną podmianę", NewBuildRequestsSafeReplacement),
        ("kanoniczna instalacja wygrywa z nieznaną kopią", PreferredInstallationWins),
        ("aktualizator wykrywa wszystkie procesy instalacji", UpdaterRecognizesInstalledComponents),
        ("aktualizator wykrywa żywy proces z instalacji", UpdaterFindsRunningInstalledProcess),
        ("aktualizator zamyka tylko właściwe okno AMC", UpdaterTargetsOnlyInstalledAmcWindow),
    ];

    public static int Main()
    {
        var failures = 0;
        foreach (var (name, run) in Tests)
        {
            try
            {
                run();
                Console.WriteLine("OK: " + name);
            }
            catch (Exception exception)
            {
                failures++;
                Console.Error.WriteLine("NIEPOWODZENIE: " + name + ": " + exception.Message);
            }
        }
        Console.WriteLine(failures == 0
            ? $"Wszystkie testy launchera przeszły ({Tests.Length})."
            : $"Niepowodzenia launchera: {failures} z {Tests.Length}.");
        return failures == 0 ? 0 : 1;
    }

    private static void ValidBundleIsAccepted()
    {
        using var fixture = BundleFixture.Create();
        var verified = BundleVerifier.Verify(fixture.Root);
        Equal(Path.Combine(fixture.Root, "host", "amc_lite_host.exe"), verified.HostExecutable);
    }

    private static void CorruptStartupFileIsRejected()
    {
        using var fixture = BundleFixture.Create();
        File.AppendAllText(Path.Combine(fixture.Root, "app", "amc_wx_lite", "__main__.py"), "uszkodzenie");
        Throws("uszkodzony", () => BundleVerifier.Verify(fixture.Root));
    }

    private static void WrongProtocolIsRejected()
    {
        using var fixture = BundleFixture.Create(hostProtocolVersion: 2);
        Throws("wersja silnika", () => BundleVerifier.Verify(fixture.Root));
    }

    private static void TraversalIsRejected()
    {
        using var fixture = BundleFixture.Create(
            extraStartupFile: "../poza-" + Guid.NewGuid().ToString("N") + ".txt");
        Throws("poza folder", () => BundleVerifier.Verify(fixture.Root));
    }

    private static void LaunchPlanUsesOnlyPrivateRuntime()
    {
        using var fixture = BundleFixture.Create();
        var verified = BundleVerifier.Verify(fixture.Root);
        var oldPythonPath = Environment.GetEnvironmentVariable("PYTHONPATH");
        var oldOverride = Environment.GetEnvironmentVariable("AMC_WX_LITE_PYTHON");
        try
        {
            Environment.SetEnvironmentVariable("PYTHONPATH", "C:\\obcy-python");
            Environment.SetEnvironmentVariable("AMC_WX_LITE_PYTHON", "C:\\obcy.exe");
            var plan = PythonLaunchPlan.Create(verified, []);
            Equal(Path.Combine(fixture.Root, "runtime", "python.exe"), plan.StartInfo.FileName);
            Equal(false, plan.StartInfo.UseShellExecute);
            Equal(true, plan.StartInfo.CreateNoWindow);
            Equal(true, plan.StartInfo.RedirectStandardOutput);
            Equal(true, plan.StartInfo.RedirectStandardError);
            Equal(false, plan.ShowCapturedOutput);
            Equal(false, plan.StartInfo.Environment.ContainsKey("PYTHONPATH"));
            Equal(false, plan.StartInfo.Environment.ContainsKey("AMC_WX_LITE_PYTHON"));
            Equal(verified.HostExecutable, plan.StartInfo.Environment["AMC_LITE_HOST"]);
            Equal("-m", plan.StartInfo.ArgumentList[0]);
            Equal("amc_wx_lite", plan.StartInfo.ArgumentList[1]);
        }
        finally
        {
            Environment.SetEnvironmentVariable("PYTHONPATH", oldPythonPath);
            Environment.SetEnvironmentVariable("AMC_WX_LITE_PYTHON", oldOverride);
        }
    }

    private static void DiagnosticUsesConsoleRuntime()
    {
        using var fixture = BundleFixture.Create();
        var plan = PythonLaunchPlan.Create(
            BundleVerifier.Verify(fixture.Root),
            ["--sprawdz"]);
        Equal(Path.Combine(fixture.Root, "runtime", "python.exe"), plan.StartInfo.FileName);
        Equal(true, plan.ShowCapturedOutput);
        Equal(true, plan.StartInfo.RedirectStandardOutput);
        Equal(true, plan.StartInfo.RedirectStandardError);
        Equal("--sprawdz", plan.StartInfo.ArgumentList[2]);
    }

    private static void OnlyOneLauncherOwnsTheLease()
    {
        var name = @"Local\AMC-Python-Launcher-Test-" + Guid.NewGuid().ToString("N");
        using var first = LauncherInstanceLease.TryAcquire(name);
        Equal(true, first.IsOwner);

        var secondOwns = Task.Run(() =>
        {
            using var second = LauncherInstanceLease.TryAcquire(name);
            return second.IsOwner;
        }).GetAwaiter().GetResult();
        Equal(false, secondOwns);

        first.Dispose();
        var thirdOwns = Task.Run(() =>
        {
            using var third = LauncherInstanceLease.TryAcquire(name);
            return third.IsOwner;
        }).GetAwaiter().GetResult();
        Equal(true, thirdOwns);
    }

    private static void SameBuildOnlyActivates()
    {
        Equal(
            ExistingInstanceAction.Activate,
            ExistingInstancePolicy.Decide(
                "2026.10.14-1fe0f900-a1b2c3d4",
                "AMC Python — wersja 0.1.0, kompilacja 2026.10.14-1fe0f900-a1b2c3d4",
                @"D:\Projekty Codex\AMC Python",
                @"D:\Projekty Codex\AMC Python"));
    }

    private static void LauncherRecognizesCurrentAndLegacyTitles()
    {
        Equal(true, ProductIdentity.IsMainWindowTitle(
            "AMC Test — 18.10.2026, 13:30"));
        Equal(true, ProductIdentity.IsMainWindowTitle(
            "AMC Python — 18.10.2026, 13:29"));
        Equal(false, ProductIdentity.IsMainWindowTitle(
            "Diagnostyka AMC Test"));
    }

    private static void NewBuildRequestsSafeReplacement()
    {
        Equal(
            ExistingInstanceAction.RequestSafeReplacement,
            ExistingInstancePolicy.Decide(
                "2026.10.14-1fe0f900-a1b2c3d4",
                "AMC Python — wersja 0.1.0, kompilacja 2026.10.14-1fe0f900-e5f6a7b8",
                @"D:\Projekty Codex\AMC Python",
                @"D:\Projekty Codex\AMC Python"));
    }

    private static void PreferredInstallationWins()
    {
        Equal(
            ExistingInstanceAction.RequestSafeReplacement,
            ExistingInstancePolicy.Decide(
                "2026.10.13-6c48ebf",
                "AMC Python — wersja 0.1.0",
                @"D:\Projekty Codex\AMC Python",
                @"D:\Projekty Codex\wydanie testowe"));
        Equal(
            ExistingInstanceAction.Activate,
            ExistingInstancePolicy.Decide(
                "RuntimeObject { Id = tajne }",
                "AMC Python — wersja 0.1.0, kompilacja RuntimeObject { Id = tajne }",
                @"D:\Projekty Codex\wydanie testowe",
                @"D:\Projekty Codex\AMC Python"));
    }

    private static void UpdaterRecognizesInstalledComponents()
    {
        var root = Path.Combine("D:\\", "Projekty Codex", "AMC Python");
        Equal(true, InstalledProcessGuard.IsInsideInstallation(
            root, Path.Combine(root, "AMC.exe")));
        Equal(true, InstalledProcessGuard.IsInsideInstallation(
            root, Path.Combine(root, "runtime", "python.exe")));
        Equal(true, InstalledProcessGuard.IsInsideInstallation(
            root, Path.Combine(root, "host", "amc_lite_host.exe")));
        Equal(true, InstalledProcessGuard.IsInsideInstallation(
            root.ToUpperInvariant(), Path.Combine(root.ToLowerInvariant(), "AMC.exe")));
        Equal(false, InstalledProcessGuard.IsInsideInstallation(
            root, Path.Combine("D:\\", "Projekty Codex", "AMC Python stary", "AMC.exe")));
        Equal(false, InstalledProcessGuard.IsInsideInstallation(root, null));
    }

    private static void UpdaterFindsRunningInstalledProcess()
    {
        var root = Path.Combine(
            Path.GetTempPath(), "amc-updater-process-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        var command = Environment.GetEnvironmentVariable("ComSpec")
            ?? Path.Combine(Environment.SystemDirectory, "cmd.exe");
        var installedCommand = Path.Combine(root, "runtime", "amc-test-process.exe");
        Directory.CreateDirectory(Path.GetDirectoryName(installedCommand)!);
        File.Copy(command, installedCommand);
        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = installedCommand,
            UseShellExecute = false,
            CreateNoWindow = true,
            ArgumentList = { "/d", "/c", "ping -n 30 127.0.0.1 > nul" },
        }) ?? throw new InvalidOperationException("Nie uruchomiono procesu próbnego.");
        try
        {
            var deadline = DateTime.UtcNow.AddSeconds(5);
            while (!InstalledProcessGuard.HasRunningComponent(root))
            {
                if (process.HasExited || DateTime.UtcNow >= deadline)
                    throw new InvalidOperationException(
                        "Nie wykryto żywego procesu uruchomionego z instalacji.");
                Thread.Sleep(50);
            }
            var blockers = InstalledProcessGuard.RunningComponents(root);
            Equal(1, blockers.Count);
            Equal(process.Id, blockers[0].ProcessId);
            Equal(true, InstalledProcessGuard.IsInsideInstallation(
                root,
                blockers[0].Executable));
        }
        finally
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                process.WaitForExit(5_000);
            }
            Directory.Delete(root, recursive: true);
        }
    }

    private static void UpdaterTargetsOnlyInstalledAmcWindow()
    {
        var root = Path.Combine("D:\\", "Projekty Codex", "AMC Python");
        var runtime = Path.Combine(root, "runtime", "python.exe");
        Equal(true, SafeApplicationStop.IsCandidateWindow(
            root,
            runtime,
            "AMC Test — 18.10.2026, 13:30"));
        Equal(true, SafeApplicationStop.IsCandidateWindow(
            root,
            runtime,
            "AMC Python — wersja 0.1.0, kompilacja 2026.10.13-test"));
        Equal(true, SafeApplicationStop.IsCandidateWindow(
            root,
            runtime,
            "AMC Python — 14.10.2026, 18:52"));
        Equal(true, SafeApplicationStop.IsCandidateWindow(root, runtime, "AMC Python"));
        Equal(false, SafeApplicationStop.IsCandidateWindow(
            root,
            Path.Combine("D:\\", "Projekty Codex", "inna kopia", "runtime", "python.exe"),
            "AMC Python — wersja 0.1.0, kompilacja 2026.10.13-test"));
        Equal(false, SafeApplicationStop.IsCandidateWindow(
            root,
            runtime,
            "AMC Python - techniczne okno pomocnicze"));
    }

    private static void Throws(string expected, Action action)
    {
        try
        {
            action();
        }
        catch (InvalidDataException exception) when (
            exception.Message.Contains(expected, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }
        throw new InvalidOperationException("Nie otrzymano oczekiwanej odmowy: " + expected);
    }

    private static void Equal<T>(T expected, T actual)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException($"Oczekiwano {expected}, otrzymano {actual}");
    }

    private sealed class BundleFixture : IDisposable
    {
        public string Root { get; }

        private readonly string? _outsidePath;

        private BundleFixture(string root, string? outsidePath = null)
        {
            Root = root;
            _outsidePath = outsidePath;
        }

        public static BundleFixture Create(
            int hostProtocolVersion = 1,
            string? extraStartupFile = null)
        {
            var root = Path.Combine(Path.GetTempPath(), "amc-launcher-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(root);
            string? outsidePath = null;
            var files = new[]
            {
                "AMC.exe",
                "runtime/python.exe",
                "runtime/pythonw.exe",
                "app/amc_wx_lite/__main__.py",
                "host/amc_lite_host.exe",
            }.ToList();
            if (extraStartupFile is not null)
            {
                files.Add(extraStartupFile);
                outsidePath = Path.GetFullPath(Path.Combine(root, extraStartupFile));
                File.WriteAllText(outsidePath, "poza");
            }
            foreach (var relative in files.Where(path => !path.StartsWith("..", StringComparison.Ordinal)))
            {
                var path = Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar));
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllText(path, "plik:" + relative);
            }
            var hashes = files.ToDictionary(
                relative => relative,
                relative =>
                {
                    var path = Path.GetFullPath(Path.Combine(
                        root,
                        relative.Replace('/', Path.DirectorySeparatorChar)));
                    return Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
                },
                StringComparer.OrdinalIgnoreCase);
            var manifest = new
            {
                bundleFormatVersion = 1,
                interfaceVersion = 1,
                hostProtocolVersion,
                application = "AMC Python",
                buildLabel = "2026.10.13-6c48ebf",
                entryPoint = "AMC.exe",
                pythonModule = "amc_wx_lite",
                hostFolder = "host",
                files,
                startupFiles = files,
                fileHashes = hashes,
            };
            File.WriteAllText(
                Path.Combine(root, "bundle-manifest.json"),
                JsonSerializer.Serialize(manifest));
            return new BundleFixture(root, outsidePath);
        }

        public void Dispose()
        {
            if (Directory.Exists(Root))
                Directory.Delete(Root, recursive: true);
            if (_outsidePath is not null && File.Exists(_outsidePath))
                File.Delete(_outsidePath);
        }
    }
}
