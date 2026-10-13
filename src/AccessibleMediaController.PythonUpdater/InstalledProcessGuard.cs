using System.Diagnostics;

namespace AccessibleMediaController.PythonUpdater;

/// <summary>
/// Chroni transakcję aktualizacji przed procesami uruchomionymi z katalogu
/// instalacji. Sam PID launchera nie wystarcza: po awarii albo ręcznym
/// uruchomieniu mogą nadal działać prywatny Python lub host dźwięku.
/// </summary>
internal static class InstalledProcessGuard
{
    internal static bool HasRunningComponent(string installationRoot)
        => RunningComponents(installationRoot).Count > 0;

    internal static IReadOnlyList<RunningInstalledComponent> RunningComponents(
        string installationRoot)
    {
        var result = new List<RunningInstalledComponent>();
        foreach (var process in Process.GetProcesses())
        {
            using (process)
            {
                if (process.Id == Environment.ProcessId)
                    continue;
                try
                {
                    var executable = process.MainModule?.FileName;
                    if (IsInsideInstallation(installationRoot, executable))
                    {
                        result.Add(new RunningInstalledComponent(
                            process.Id,
                            executable!));
                    }
                }
                catch (Exception exception) when (
                    exception is InvalidOperationException
                    or System.ComponentModel.Win32Exception
                    or NotSupportedException)
                {
                    // Obcy lub chroniony proces nie jest składnikiem, którego
                    // to narzędzie potrafi wiarygodnie przypisać do AMC.
                }
            }
        }
        return result;
    }

    internal static bool IsInsideInstallation(string installationRoot, string? executable)
    {
        if (string.IsNullOrWhiteSpace(installationRoot)
            || string.IsNullOrWhiteSpace(executable))
            return false;
        var root = Path.GetFullPath(installationRoot)
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        var path = Path.GetFullPath(executable);
        return path.StartsWith(root, StringComparison.OrdinalIgnoreCase);
    }
}

internal readonly record struct RunningInstalledComponent(
    int ProcessId,
    string Executable);
