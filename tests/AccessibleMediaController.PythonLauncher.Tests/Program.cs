using System.Security.Cryptography;
using System.Text.Json;
using AccessibleMediaController.PythonLauncher;

namespace AccessibleMediaController.PythonLauncher.Tests;

internal static class Program
{
    private static readonly (string Name, Action Run)[] Tests =
    [
        ("poprawny pakiet", ValidBundleIsAccepted),
        ("uszkodzony plik", CorruptStartupFileIsRejected),
        ("niezgodny protokół", WrongProtocolIsRejected),
        ("wyjście poza katalog", TraversalIsRejected),
        ("prywatny runtime bez PYTHONPATH", LaunchPlanUsesOnlyPrivateRuntime),
        ("diagnostyka przez python.exe", DiagnosticUsesConsoleRuntime),
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
            Equal(Path.Combine(fixture.Root, "runtime", "pythonw.exe"), plan.StartInfo.FileName);
            Equal(false, plan.StartInfo.UseShellExecute);
            Equal(true, plan.StartInfo.CreateNoWindow);
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
        Equal(true, plan.CaptureOutput);
        Equal(true, plan.StartInfo.RedirectStandardOutput);
        Equal("--sprawdz", plan.StartInfo.ArgumentList[2]);
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
