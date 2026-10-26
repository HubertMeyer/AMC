using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using AccessibleMediaController.Core.ShellIntegration;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;
using Microsoft.Win32;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Odczytuje i stosuje integrację bieżącego profilu z Eksploratorem Windows.
/// Wszystkie wpisy są w HKCU. Klient podaje wyłącznie identyfikatory grup z
/// <see cref="ShellIntegrationRules"/>; nie może przesłać klucza rejestru,
/// polecenia ani dowolnego rozszerzenia.
/// </summary>
internal sealed class LiteShellIntegrationCoordinator
{
    internal const string StatusOperation = "shellIntegration.status";
    internal const string ApplyOperation = "shellIntegration.apply";
    internal const string OpenDefaultAppsOperation = "shellIntegration.openDefaultApps";

    private const string ClassesRoot = @"Software\Classes";
    private const string RegisteredApplicationsKey = @"Software\RegisteredApplications";
    private const string ManagedValue = "ManagedByApplication";
    private const string ContextMenuValue = "ContextMenuEnabled";
    private const string OpenWithValue = "OpenWithEnabled";
    private const string ExtensionsValue = "SelectedExtensions";

    private readonly ShellIntegrationProfile _profile;
    private readonly string? _launcherPath;

    internal LiteShellIntegrationCoordinator(string? profileId, string? launcherPath = null)
    {
        _profile = ShellIntegrationRules.ProfileFor(profileId);
        _launcherPath = launcherPath ?? FindLauncherPath();
    }

    internal IReadOnlyDictionary<string, Func<LiteRequest, LiteEventSink, object?>> Handlers() =>
        new Dictionary<string, Func<LiteRequest, LiteEventSink, object?>>(StringComparer.Ordinal)
        {
            [StatusOperation] = (_, _) => Status(),
            [ApplyOperation] = (request, _) => Apply(request.Args),
            [OpenDefaultAppsOperation] = (_, _) => OpenWindowsDefaultAppsSettings()
        };

    private object Status()
    {
        try
        {
            var contextExtensions = ReadContextMenuExtensions();
            var openWithExtensions = ReadOpenWithExtensions();
            var selectedExtensions = ReadManagedExtensions()
                ?? contextExtensions.Union(openWithExtensions, StringComparer.OrdinalIgnoreCase)
                    .ToHashSet(StringComparer.OrdinalIgnoreCase);
            var groups = ShellIntegrationRules.Groups.Select(group => new
            {
                id = group.Id,
                name = group.Name,
                description = group.Description,
                extensions = group.Extensions,
                selected = group.Extensions.All(selectedExtensions.Contains)
            }).ToArray();
            var activeExtensions = contextExtensions
                .Union(openWithExtensions, StringComparer.OrdinalIgnoreCase)
                .Count();
            var contextEnabled = contextExtensions.Count > 0;
            var openWithEnabled = openWithExtensions.Count > 0
                && IsApplicationRegistered();
            var availabilityMessage = _launcherPath is null
                ? "Nie znaleziono programu uruchamiającego AMC. Integracji nie można teraz zmienić."
                : DescribeState(contextEnabled, openWithEnabled, activeExtensions);
            return new
            {
                success = true,
                available = _launcherPath is not null,
                displayName = _profile.DisplayName,
                contextMenuEnabled = contextEnabled,
                openWithEnabled,
                registeredExtensionCount = activeExtensions,
                groups,
                message = availabilityMessage
            };
        }
        catch (Exception exception) when (IsRegistryFailure(exception))
        {
            DiagnosticLog.Warning(
                "integracja-windows",
                "Nie udało się odczytać integracji: " + exception.Message);
            return new
            {
                success = false,
                available = false,
                displayName = _profile.DisplayName,
                contextMenuEnabled = false,
                openWithEnabled = false,
                registeredExtensionCount = 0,
                groups = ShellIntegrationRules.Groups.Select(group => new
                {
                    id = group.Id,
                    name = group.Name,
                    description = group.Description,
                    extensions = group.Extensions,
                    selected = false
                }).ToArray(),
                message = "Nie udało się odczytać integracji z Windows."
            };
        }
    }

    private object Apply(JsonElement args)
    {
        if (_launcherPath is null)
        {
            return new
            {
                success = false,
                message = "Nie znaleziono programu uruchamiającego AMC. Niczego nie zmieniono.",
                registeredExtensionCount = 0
            };
        }

        var contextMenu = LiteArgs.ReadBool(args, "contextMenuEnabled", false);
        var openWith = LiteArgs.ReadBool(args, "openWithEnabled", false);
        var groupIds = ReadGroupIds(args);
        var knownIds = ShellIntegrationRules.Groups
            .Select(group => group.Id)
            .ToHashSet(StringComparer.Ordinal);
        if (groupIds.Any(id => !knownIds.Contains(id)))
            throw new LiteRequestException("Wybrano nieznaną grupę typów plików.");

        var selectedExtensions = ShellIntegrationRules.Groups
            .Where(group => groupIds.Contains(group.Id))
            .SelectMany(group => group.Extensions)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        try
        {
            foreach (var extension in ShellIntegrationRules.AllExtensions)
            {
                RemoveContextMenu(extension);
                RemoveOpenWith(extension);
            }
            RemoveApplicationRegistration();

            if (contextMenu)
            {
                foreach (var extension in selectedExtensions)
                    RegisterContextMenu(extension, _launcherPath);
            }
            if (openWith)
            {
                RegisterApplication(selectedExtensions);
                foreach (var extension in selectedExtensions)
                    RegisterOpenWith(extension, _launcherPath);
            }

            SaveManagedSelection(contextMenu, openWith, selectedExtensions);
            NotifyShell();
            var activeCount = (contextMenu || openWith) ? selectedExtensions.Length : 0;
            var message = DescribeState(contextMenu, openWith, activeCount);
            DiagnosticLog.Info("integracja-windows", message);
            return new { success = true, message, registeredExtensionCount = activeCount };
        }
        catch (Exception exception) when (IsRegistryFailure(exception))
        {
            DiagnosticLog.Error(
                "integracja-windows",
                "Nie udało się zastosować integracji z Windows.",
                exception);
            return new
            {
                success = false,
                message = "Nie udało się zastosować integracji z Windows: " + exception.Message,
                registeredExtensionCount = 0
            };
        }
    }

    private static HashSet<string> ReadGroupIds(JsonElement args)
    {
        var result = new HashSet<string>(StringComparer.Ordinal);
        if (args.ValueKind != JsonValueKind.Object
            || !args.TryGetProperty("groupIds", out var values)
            || values.ValueKind != JsonValueKind.Array)
            return result;
        foreach (var value in values.EnumerateArray())
        {
            if (value.ValueKind != JsonValueKind.String) continue;
            var id = value.GetString();
            if (!string.IsNullOrWhiteSpace(id)) result.Add(id);
        }
        return result;
    }

    private HashSet<string> ReadContextMenuExtensions()
    {
        var found = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var extension in ShellIntegrationRules.AllExtensions)
        {
            using var command = Registry.CurrentUser.OpenSubKey(
                ContextCommandPath(extension, "open"));
            var text = command?.GetValue(null) as string;
            if (CommandTargetsCurrentLauncher(text)) found.Add(extension);
        }
        return found;
    }

    private HashSet<string> ReadOpenWithExtensions()
    {
        var found = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var extension in ShellIntegrationRules.AllExtensions)
        {
            var className = _profile.ClassNameFor(extension);
            using var openWith = Registry.CurrentUser.OpenSubKey(
                $@"{ClassesRoot}\{extension}\OpenWithProgids");
            if (openWith is null
                || !openWith.GetValueNames().Contains(className, StringComparer.OrdinalIgnoreCase))
                continue;
            using var command = Registry.CurrentUser.OpenSubKey(
                $@"{ClassesRoot}\{className}\shell\open\command");
            if (CommandTargetsCurrentLauncher(command?.GetValue(null) as string))
                found.Add(extension);
        }
        return found;
    }

    private HashSet<string>? ReadManagedExtensions()
    {
        using var settings = Registry.CurrentUser.OpenSubKey(_profile.SettingsPath);
        if (settings?.GetValue(ManagedValue) is not int managed || managed != 1)
            return null;
        var raw = settings.GetValue(ExtensionsValue) as string ?? string.Empty;
        return raw.Split('|', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(ShellIntegrationRules.NormalizeExtension)
            .Where(extension => extension is not null
                && ShellIntegrationRules.AllExtensions.Contains(
                    extension, StringComparer.OrdinalIgnoreCase))
            .Select(extension => extension!)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
    }

    private bool IsApplicationRegistered()
    {
        using var registered = Registry.CurrentUser.OpenSubKey(RegisteredApplicationsKey);
        return string.Equals(
            registered?.GetValue(_profile.RegisteredApplication) as string,
            _profile.CapabilitiesPath,
            StringComparison.OrdinalIgnoreCase);
    }

    private bool CommandTargetsCurrentLauncher(string? command) =>
        _launcherPath is not null
        && !string.IsNullOrWhiteSpace(command)
        && command.Contains(_launcherPath, StringComparison.OrdinalIgnoreCase);

    private void RegisterContextMenu(string extension, string launcher)
    {
        WriteVerb(extension, "open", _profile.OpenLabel, $"\"{launcher}\" \"%1\"");
        WriteVerb(
            extension,
            "queue",
            _profile.QueueLabel,
            $"\"{launcher}\" {ShellIntegrationRules.QueueSwitch} \"%1\"");
    }

    private void WriteVerb(string extension, string key, string label, string command)
    {
        var root = ContextVerbPath(extension, key);
        using var verb = Registry.CurrentUser.CreateSubKey(root);
        verb.SetValue(null, label);
        verb.SetValue("Icon", _launcherPath + ",0");
        using var commandKey = verb.CreateSubKey("command");
        commandKey.SetValue(null, command);
    }

    private void RemoveContextMenu(string extension)
    {
        var root = $@"{ClassesRoot}\SystemFileAssociations\{extension}\shell\{_profile.VerbPrefix}";
        Registry.CurrentUser.DeleteSubKeyTree(root + "open", throwOnMissingSubKey: false);
        Registry.CurrentUser.DeleteSubKeyTree(root + "queue", throwOnMissingSubKey: false);
    }

    private void RegisterOpenWith(string extension, string launcher)
    {
        var className = _profile.ClassNameFor(extension);
        using (var extensionKey = Registry.CurrentUser.CreateSubKey(
            $@"{ClassesRoot}\{extension}\OpenWithProgids"))
        {
            extensionKey.SetValue(className, string.Empty);
        }
        using var classKey = Registry.CurrentUser.CreateSubKey($@"{ClassesRoot}\{className}");
        classKey.SetValue(
            null,
            $"Plik {extension[1..].ToUpperInvariant()} ({_profile.DisplayName})");
        using (var icon = classKey.CreateSubKey("DefaultIcon"))
            icon.SetValue(null, launcher + ",0");
        using var open = classKey.CreateSubKey(@"shell\open");
        open.SetValue(null, _profile.OpenLabel);
        using var command = open.CreateSubKey("command");
        command.SetValue(null, $"\"{launcher}\" \"%1\"");
    }

    private void RemoveOpenWith(string extension)
    {
        var className = _profile.ClassNameFor(extension);
        using (var openWith = Registry.CurrentUser.OpenSubKey(
            $@"{ClassesRoot}\{extension}\OpenWithProgids", writable: true))
        {
            openWith?.DeleteValue(className, throwOnMissingValue: false);
        }
        Registry.CurrentUser.DeleteSubKeyTree(
            $@"{ClassesRoot}\{className}", throwOnMissingSubKey: false);
    }

    private void RegisterApplication(IReadOnlyList<string> extensions)
    {
        using (var capabilities = Registry.CurrentUser.CreateSubKey(_profile.CapabilitiesPath))
        {
            capabilities.SetValue("ApplicationName", _profile.DisplayName);
            capabilities.SetValue(
                "ApplicationDescription",
                "Dostępny odtwarzacz i organizator multimediów");
            using var associations = capabilities.CreateSubKey("FileAssociations");
            foreach (var extension in extensions)
                associations.SetValue(extension, _profile.ClassNameFor(extension));
        }
        using var registered = Registry.CurrentUser.CreateSubKey(RegisteredApplicationsKey);
        registered.SetValue(_profile.RegisteredApplication, _profile.CapabilitiesPath);
    }

    private void RemoveApplicationRegistration()
    {
        using (var registered = Registry.CurrentUser.OpenSubKey(
            RegisteredApplicationsKey, writable: true))
        {
            registered?.DeleteValue(_profile.RegisteredApplication, throwOnMissingValue: false);
        }
        Registry.CurrentUser.DeleteSubKeyTree(
            _profile.CapabilitiesPath, throwOnMissingSubKey: false);
    }

    private void SaveManagedSelection(
        bool contextMenu,
        bool openWith,
        IEnumerable<string> extensions)
    {
        using var settings = Registry.CurrentUser.CreateSubKey(_profile.SettingsPath);
        settings.SetValue(ManagedValue, 1, RegistryValueKind.DWord);
        settings.SetValue(ContextMenuValue, contextMenu ? 1 : 0, RegistryValueKind.DWord);
        settings.SetValue(OpenWithValue, openWith ? 1 : 0, RegistryValueKind.DWord);
        settings.SetValue(ExtensionsValue, string.Join('|', extensions));
    }

    private object OpenWindowsDefaultAppsSettings()
    {
        var addresses = new[]
        {
            "ms-settings:defaultapps?registeredAppUser="
                + Uri.EscapeDataString(_profile.RegisteredApplication),
            "ms-settings:defaultapps"
        };
        foreach (var address in addresses)
        {
            try
            {
                Process.Start(new ProcessStartInfo(address) { UseShellExecute = true });
                return new
                {
                    success = true,
                    message = "Otwarto ustawienia aplikacji domyślnych Windows."
                };
            }
            catch (Exception exception) when (exception is System.ComponentModel.Win32Exception
                or InvalidOperationException
                or PlatformNotSupportedException)
            {
                DiagnosticLog.Warning(
                    "integracja-windows",
                    $"Nie udało się otworzyć adresu {address}: {exception.Message}");
            }
        }
        return new
        {
            success = false,
            message = "Nie udało się otworzyć ustawień aplikacji domyślnych Windows."
        };
    }

    private string ContextVerbPath(string extension, string key) =>
        $@"{ClassesRoot}\SystemFileAssociations\{extension}\shell\{_profile.VerbPrefix}{key}";

    private string ContextCommandPath(string extension, string key) =>
        ContextVerbPath(extension, key) + @"\command";

    private static string DescribeState(bool contextMenu, bool openWith, int count) =>
        $"Menu kontekstowe: {(contextMenu ? "włączone" : "wyłączone")}; "
        + $"Otwórz za pomocą: {(openWith ? "włączone" : "wyłączone")}. "
        + $"Wybrano {count} typów plików.";

    private static string? FindLauncherPath()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        for (var level = 0; directory is not null && level < 8; level++)
        {
            var candidate = Path.Combine(directory.FullName, "AMC.exe");
            if (File.Exists(candidate)) return Path.GetFullPath(candidate);
            directory = directory.Parent;
        }
        return null;
    }

    private static bool IsRegistryFailure(Exception exception) =>
        exception is UnauthorizedAccessException
            or System.Security.SecurityException
            or IOException;

    private static void NotifyShell()
    {
        try
        {
            SHChangeNotify(0x08000000, 0x1000, IntPtr.Zero, IntPtr.Zero);
        }
        catch (Exception exception) when (exception is DllNotFoundException
            or EntryPointNotFoundException)
        {
            DiagnosticLog.Warning(
                "integracja-windows",
                "Nie udało się odświeżyć Eksploratora: " + exception.Message);
        }
    }

    [DllImport("shell32.dll", SetLastError = true)]
    private static extern void SHChangeNotify(
        uint eventId, uint flags, IntPtr item1, IntPtr item2);
}
