using System.Text.RegularExpressions;

namespace AccessibleMediaController.PythonLauncher;

internal enum ExistingInstanceAction
{
    Activate,
    RequestSafeReplacement,
}

/// <summary>
/// Decides whether a second AMC.exe start means "show the running window" or
/// "replace an older build".  The visible build label is intentional user
/// text; no process path, object representation or internal identifier reaches
/// the accessible window title.
/// </summary>
internal static partial class ExistingInstancePolicy
{
    private const string BuildMarker = ", kompilacja ";

    [GeneratedRegex(
        @"^\d{4}\.\d{2}\.\d{2}(?:-[0-9a-f]{7,12}){0,2}(?:-robocza)?$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex BuildLabelPattern();

    internal static ExistingInstanceAction Decide(
        string requestedBuildLabel,
        string existingWindowTitle,
        string requestedPackageRoot,
        string? existingPackageRoot,
        string preferredInstallationFolder)
    {
        var requested = NormalizeBuildLabel(requestedBuildLabel);
        var existing = BuildLabelFromWindowTitle(existingWindowTitle);
        if (requested.Length > 0
            && string.Equals(requested, existing, StringComparison.OrdinalIgnoreCase))
            return ExistingInstanceAction.Activate;

        // Replacing files in the same installation while its old process is
        // still alive is the ordinary updater scenario.  The title describes
        // the loaded code, so a different label here really means old memory.
        if (SameDirectory(requestedPackageRoot, existingPackageRoot))
            return ExistingInstanceAction.RequestSafeReplacement;

        // Only the stable, user-facing installation may supersede an arbitrary
        // test-output copy.  Starting an old test package must never close the
        // canonical AMC Python and silently downgrade the application.
        if (IsPreferredInstallation(requestedPackageRoot, preferredInstallationFolder)
            && !IsPreferredInstallation(existingPackageRoot, preferredInstallationFolder))
            return ExistingInstanceAction.RequestSafeReplacement;

        return ExistingInstanceAction.Activate;
    }

    internal static string BuildLabelFromWindowTitle(string title)
    {
        if (string.IsNullOrWhiteSpace(title))
            return "";
        var marker = title.LastIndexOf(BuildMarker, StringComparison.Ordinal);
        return marker < 0
            ? ""
            : NormalizeBuildLabel(title[(marker + BuildMarker.Length)..]);
    }

    internal static string NormalizeBuildLabel(string? value)
    {
        var label = value?.Trim() ?? "";
        return BuildLabelPattern().IsMatch(label) ? label : "";
    }

    private static bool SameDirectory(string first, string? second)
    {
        if (string.IsNullOrWhiteSpace(first) || string.IsNullOrWhiteSpace(second))
            return false;
        try
        {
            return string.Equals(
                Path.GetFullPath(first).TrimEnd(Path.DirectorySeparatorChar),
                Path.GetFullPath(second).TrimEnd(Path.DirectorySeparatorChar),
                StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception exception) when (
            exception is ArgumentException or NotSupportedException or PathTooLongException)
        {
            return false;
        }
    }

    private static bool IsPreferredInstallation(string? root, string preferredFolder)
    {
        if (string.IsNullOrWhiteSpace(root))
            return false;
        try
        {
            return string.Equals(
                Path.GetFileName(Path.GetFullPath(root).TrimEnd(
                    Path.DirectorySeparatorChar,
                    Path.AltDirectorySeparatorChar)),
                preferredFolder,
                StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception exception) when (
            exception is ArgumentException or NotSupportedException or PathTooLongException)
        {
            return false;
        }
    }
}
