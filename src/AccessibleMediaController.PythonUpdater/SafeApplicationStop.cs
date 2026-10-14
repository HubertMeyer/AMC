using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace AccessibleMediaController.PythonUpdater;

/// <summary>
/// Prosi działające okno AMC Python o zwykłe zamknięcie i czeka na zwolnienie
/// plików instalacji. Nie kończy procesów wymuszenie. Dzięki temu obsługa
/// EVT_CLOSE może odmówić podczas nagrywania albo przy niepewnym stanie hosta.
/// </summary>
internal static class SafeApplicationStop
{
    private const uint CloseMessage = 0x0010u; // WM_CLOSE
    private static readonly TimeSpan PollDelay = TimeSpan.FromMilliseconds(100);

    internal static bool RequestAndWait(
        string installationRoot,
        int? expectedProcessId,
        TimeSpan timeout)
    {
        RequestCloseForInstallation(installationRoot);
        var deadline = DateTime.UtcNow + timeout;
        while (true)
        {
            if (!IsProcessAlive(expectedProcessId)
                && !InstalledProcessGuard.HasRunningComponent(installationRoot))
                return true;
            if (DateTime.UtcNow >= deadline)
                return false;
            Thread.Sleep(PollDelay);
        }
    }

    internal static bool IsCandidateWindow(
        string installationRoot,
        string? executable,
        string? title) =>
        InstalledProcessGuard.IsInsideInstallation(installationRoot, executable)
        && !string.IsNullOrWhiteSpace(title)
        && (string.Equals(title, "AMC Python", StringComparison.Ordinal)
            || title.StartsWith("AMC Python — ", StringComparison.Ordinal));

    private static void RequestCloseForInstallation(string installationRoot)
    {
        EnumWindows((window, _) =>
        {
            var title = ReadWindowTitle(window);
            GetWindowThreadProcessId(window, out var processId);
            var executable = ExecutableForProcess(processId);
            if (IsCandidateWindow(installationRoot, executable, title))
                PostMessage(window, CloseMessage, IntPtr.Zero, IntPtr.Zero);
            return true;
        }, IntPtr.Zero);
    }

    private static bool IsProcessAlive(int? processId)
    {
        if (processId is null || processId <= 0)
            return false;
        try
        {
            using var process = Process.GetProcessById(processId.Value);
            return !process.HasExited;
        }
        catch (ArgumentException)
        {
            return false;
        }
        catch (InvalidOperationException)
        {
            return false;
        }
    }

    private static string? ExecutableForProcess(uint processId)
    {
        if (processId == 0)
            return null;
        try
        {
            using var process = Process.GetProcessById((int)processId);
            return process.MainModule?.FileName;
        }
        catch (Exception exception) when (
            exception is ArgumentException
                or InvalidOperationException
                or NotSupportedException
                or System.ComponentModel.Win32Exception)
        {
            return null;
        }
    }

    private static string? ReadWindowTitle(IntPtr window)
    {
        var length = GetWindowTextLength(window);
        if (length <= 0)
            return null;
        var text = new StringBuilder(length + 1);
        return GetWindowText(window, text, text.Capacity) > 0
            ? text.ToString()
            : null;
    }

    private delegate bool EnumWindowsProc(IntPtr windowHandle, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr parameter);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowTextLength(IntPtr windowHandle);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(
        IntPtr windowHandle,
        StringBuilder text,
        int maximumCount);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(
        IntPtr windowHandle,
        out uint processId);

    [DllImport("user32.dll")]
    private static extern bool PostMessage(
        IntPtr windowHandle,
        uint message,
        IntPtr wordParameter,
        IntPtr longParameter);
}
