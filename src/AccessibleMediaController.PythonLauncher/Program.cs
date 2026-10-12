using System.Diagnostics;
using System.Runtime.InteropServices;

namespace AccessibleMediaController.PythonLauncher;

internal static class Program
{
    private const int InvalidBundle = 2;
    private const int StartFailed = 3;
    private const string MainWindowTitle = "AMC Python";

    [STAThread]
    private static int Main(string[] args)
    {
        var silentBundleCheck = args.Any(argument => string.Equals(
            argument,
            "--sprawdz-pakiet-cicho",
            StringComparison.OrdinalIgnoreCase));
        try
        {
            var bundle = BundleVerifier.Verify(AppContext.BaseDirectory);
            if (silentBundleCheck)
                return 0;
            if (args.Any(argument => string.Equals(
                argument,
                "--sprawdz-pakiet",
                StringComparison.OrdinalIgnoreCase)))
            {
                Show("Pakiet AMC Python jest kompletny i zgodny.", false);
                return 0;
            }

            using var instance = LauncherInstanceLease.TryAcquire();
            if (!instance.IsOwner)
            {
                ActivateExistingWindow();
                return 0;
            }

            var plan = PythonLaunchPlan.Create(bundle, args);
            using var process = Process.Start(plan.StartInfo)
                ?? throw new InvalidOperationException("nie uruchomiono procesu interfejsu");

            // Strumienie czytamy od razu także podczas zwykłej pracy. Bez
            // tego dłuższy komunikat mógłby zapełnić bufor i zatrzymać proces.
            // Przechwycenie stderr zapobiega modalnym alertom pythonw.
            var output = process.StandardOutput.ReadToEndAsync();
            var error = process.StandardError.ReadToEndAsync();
            process.WaitForExit();
            Task.WaitAll(output, error);

            var outputText = output.Result.Trim();
            var errorText = error.Result.Trim();
            AppendProcessLog(outputText, errorText, process.ExitCode);

            if (plan.ShowCapturedOutput)
            {
                var details = string.Join(
                    Environment.NewLine,
                    new[] { outputText, errorText }
                        .Where(text => !string.IsNullOrWhiteSpace(text)));
                Show(
                    string.IsNullOrWhiteSpace(details)
                        ? "Sprawdzenie AMC Python nie zwróciło informacji."
                        : details,
                    process.ExitCode != 0);
            }
            else if (process.ExitCode != 0)
            {
                Show(
                    "AMC Python zakończył uruchamianie z błędem. "
                    + "Uruchom AMC.exe z parametrem --sprawdz, aby sprawdzić pakiet.",
                    true);
            }
            return process.ExitCode;
        }
        catch (InvalidDataException exception)
        {
            if (!silentBundleCheck)
            {
                Show(
                    "Nie można uruchomić AMC Python, ponieważ pakiet jest "
                    + "niekompletny lub niezgodny: " + exception.Message + ".\n\n"
                    + "Uruchom ponownie instalator albo zastosuj pełną aktualizację.",
                    true);
            }
            return InvalidBundle;
        }
        catch
        {
            if (!silentBundleCheck)
            {
                Show(
                    "Nie udało się uruchomić AMC Python. Pakiet nie został zmieniony. "
                    + "Uruchom ponownie instalator albo zastosuj pełną aktualizację.",
                    true);
            }
            return StartFailed;
        }
    }

    private static void AppendProcessLog(string output, string error, int exitCode)
    {
        if (string.IsNullOrWhiteSpace(output)
            && string.IsNullOrWhiteSpace(error)
            && exitCode == 0)
            return;
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "AMC-wx-Lite",
                "logs");
            Directory.CreateDirectory(root);
            var text = string.Join(
                Environment.NewLine,
                new[]
                {
                    $"{DateTimeOffset.Now:O} Kod zakończenia interfejsu: {exitCode}",
                    string.IsNullOrWhiteSpace(output) ? null : "Wyjście:\n" + Limit(output),
                    string.IsNullOrWhiteSpace(error) ? null : "Błędy:\n" + Limit(error),
                    "",
                }.Where(value => value is not null));
            File.AppendAllText(Path.Combine(root, "launcher.log"), text);
        }
        catch
        {
            // Dziennik nie może przeszkodzić w uruchomieniu ani zamknięciu AMC.
        }
    }

    private static string Limit(string text)
    {
        const int maximum = 16_384;
        return text.Length <= maximum ? text : text[^maximum..];
    }

    private static void Show(string text, bool error)
    {
        MessageBox(
            IntPtr.Zero,
            text,
            "Diagnostyka AMC Python",
            error ? 0x10u : 0x40u);
    }

    private static void ActivateExistingWindow()
    {
        // Drugie uruchomienie jest bezpiecznym poleceniem "pokaż AMC".
        // Okno może dopiero powstawać, dlatego czekamy krótko zamiast
        // uruchamiać drugi interpreter i drugi silnik audio.
        for (var attempt = 0; attempt < 50; attempt++)
        {
            var handle = FindWindow(null, MainWindowTitle);
            if (handle != IntPtr.Zero)
            {
                ShowWindow(handle, 3); // SW_MAXIMIZE
                BringWindowToTop(handle);
                SetForegroundWindow(handle);
                return;
            }
            Thread.Sleep(100);
        }
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(
        IntPtr owner,
        string text,
        string caption,
        uint type);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr FindWindow(string? className, string windowName);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr windowHandle, int command);

    [DllImport("user32.dll")]
    private static extern bool BringWindowToTop(IntPtr windowHandle);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr windowHandle);
}
