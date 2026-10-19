using AccessibleMediaController.Core.ShellIntegration;

namespace AccessibleMediaController.PythonLauncher;

internal sealed class ShellLaunchRequestException(string message) : Exception(message);

internal static class ShellLaunchRequestContract
{
    internal const int MaximumFiles = 100;

    internal static ShellLaunchRequest ParseAndValidate(
        IEnumerable<string>? arguments,
        Func<string, bool>? fileExists = null)
    {
        var parsed = ShellIntegrationRules.ParseArguments(arguments);
        if (!parsed.HasFiles)
            return parsed;
        if (parsed.Files.Count > MaximumFiles)
            throw new ShellLaunchRequestException("Wybrano zbyt wiele plików.");
        if (!parsed.AddToQueue && parsed.Files.Count != 1)
            throw new ShellLaunchRequestException("Jednocześnie można otworzyć jeden plik.");

        var exists = fileExists ?? File.Exists;
        var normalized = new List<string>(parsed.Files.Count);
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var candidate in parsed.Files)
        {
            string path;
            try
            {
                path = Path.GetFullPath(candidate);
            }
            catch (Exception exception) when (
                exception is ArgumentException or NotSupportedException or PathTooLongException)
            {
                throw new ShellLaunchRequestException("Podano nieprawidłową ścieżkę pliku.");
            }
            if (!Path.IsPathFullyQualified(path) || !exists(path))
                throw new ShellLaunchRequestException("Nie znaleziono lokalnego pliku.");
            var extension = ShellIntegrationRules.NormalizeExtension(Path.GetExtension(path));
            if (extension is null
                || !ShellIntegrationRules.AllExtensions.Contains(
                    extension,
                    StringComparer.OrdinalIgnoreCase))
            {
                throw new ShellLaunchRequestException("Ten typ pliku nie jest obsługiwany przez AMC.");
            }
            if (seen.Add(path))
                normalized.Add(path);
        }

        return new ShellLaunchRequest(normalized, parsed.AddToQueue);
    }
}
