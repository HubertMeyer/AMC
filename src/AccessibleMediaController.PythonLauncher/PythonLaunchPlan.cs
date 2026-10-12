using System.Diagnostics;

namespace AccessibleMediaController.PythonLauncher;

internal sealed record PythonLaunchPlan(ProcessStartInfo StartInfo, bool CaptureOutput)
{
    internal static PythonLaunchPlan Create(
        VerifiedBundle bundle,
        IReadOnlyList<string> arguments)
    {
        var diagnostic = arguments.Any(argument =>
            string.Equals(argument, "--sprawdz", StringComparison.OrdinalIgnoreCase)
            || string.Equals(argument, "--check", StringComparison.OrdinalIgnoreCase));
        var runtime = Path.Combine(
            bundle.Root,
            "runtime",
            diagnostic ? "python.exe" : "pythonw.exe");
        if (!File.Exists(runtime))
            throw new InvalidDataException("w pakiecie brakuje prywatnego środowiska Pythona");

        var start = new ProcessStartInfo
        {
            FileName = runtime,
            WorkingDirectory = bundle.Root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = diagnostic,
            RedirectStandardError = diagnostic,
        };
        start.ArgumentList.Add("-m");
        start.ArgumentList.Add(bundle.Manifest.PythonModule);
        foreach (var argument in arguments)
            start.ArgumentList.Add(argument);

        // Embeddable Python otrzymuje app z pliku python*._pth. Nie dziedziczy
        // przypadkowego interpretera ani PYTHONPATH z terminala użytkownika.
        start.Environment.Remove("PYTHONPATH");
        start.Environment.Remove("AMC_WX_LITE_PYTHON");
        start.Environment["AMC_LITE_HOST"] = bundle.HostExecutable;
        start.Environment["PYTHONUTF8"] = "1";
        return new PythonLaunchPlan(start, diagnostic);
    }
}
