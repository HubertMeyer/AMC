using System.Diagnostics;
using System.Runtime.InteropServices;

namespace AccessibleMediaController.PythonLauncher;

internal static class Program
{
    private const int InvalidBundle = 2;
    private const int StartFailed = 3;

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

            var plan = PythonLaunchPlan.Create(bundle, args);
            using var process = Process.Start(plan.StartInfo)
                ?? throw new InvalidOperationException("nie uruchomiono procesu interfejsu");

            Task<string>? output = null;
            Task<string>? error = null;
            if (plan.CaptureOutput)
            {
                output = process.StandardOutput.ReadToEndAsync();
                error = process.StandardError.ReadToEndAsync();
            }
            process.WaitForExit();

            if (plan.CaptureOutput)
            {
                Task.WaitAll(output!, error!);
                var details = string.Join(
                    Environment.NewLine,
                    new[] { output!.Result.Trim(), error!.Result.Trim() }
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

    private static void Show(string text, bool error)
    {
        MessageBox(
            IntPtr.Zero,
            text,
            "Diagnostyka AMC Python",
            error ? 0x10u : 0x40u);
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(
        IntPtr owner,
        string text,
        string caption,
        uint type);
}
