using System.Security.Cryptography;
using System.Text.Json;
using AccessibleMediaController.ReleaseProfiles;

namespace AccessibleMediaController.PythonLauncher;

internal sealed class BundleManifest
{
    public int BundleFormatVersion { get; set; }
    public int InterfaceVersion { get; set; }
    public int HostProtocolVersion { get; set; }
    public string Application { get; set; } = "";
    public string BuildLabel { get; set; } = "";
    public string EntryPoint { get; set; } = "";
    public string PythonModule { get; set; } = "";
    public string HostFolder { get; set; } = "";
    public int ReleaseProfileSchema { get; set; }
    public string ReleaseProfile { get; set; } = "";
    public string ProductId { get; set; } = "";
    public string DisplayName { get; set; } = "";
    public string InstallId { get; set; } = "";
    public string UpdateChannel { get; set; } = "";
    public string UiStateFolder { get; set; } = "";
    public string RoamingProfileFolder { get; set; } = "";
    public string LocalProfileFolder { get; set; } = "";
    public string CacheFolder { get; set; } = "";
    public string LogFolder { get; set; } = "";
    public string CredentialNamespace { get; set; } = "";
    public List<string> Sessions { get; set; } = [];
    public List<string> Capabilities { get; set; } = [];
    public List<string> Files { get; set; } = [];
    public List<string> StartupFiles { get; set; } = [];
    public Dictionary<string, string> FileHashes { get; set; } =
        new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, long> FileSizes { get; set; } =
        new(StringComparer.OrdinalIgnoreCase);
}

internal sealed record VerifiedBundle(
    string Root,
    string HostExecutable,
    BundleManifest Manifest,
    ReleaseProfileDescriptor Profile);

internal static class BundleVerifier
{
    internal const int SupportedBundleFormat = 1;
    internal const int SupportedInterfaceVersion = 1;
    internal const int SupportedHostProtocolVersion = 1;
    private const int MaxManifestBytes = 8 * 1024 * 1024;

    internal static VerifiedBundle Verify(string packageRoot, bool verifyAllFiles = false)
    {
        var root = Path.GetFullPath(packageRoot);
        var manifestPath = Path.Combine(root, "bundle-manifest.json");
        if (!File.Exists(manifestPath))
            throw new InvalidDataException("brakuje manifestu pakietu");
        if (new FileInfo(manifestPath).Length > MaxManifestBytes)
            throw new InvalidDataException("manifest pakietu jest zbyt duży");

        BundleManifest manifest;
        try
        {
            manifest = JsonSerializer.Deserialize<BundleManifest>(
                File.ReadAllText(manifestPath),
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                ?? throw new InvalidDataException("manifest pakietu jest pusty");
        }
        catch (JsonException)
        {
            throw new InvalidDataException("manifest pakietu ma nieprawidłowy format");
        }

        if (manifest.BundleFormatVersion != SupportedBundleFormat)
            throw new InvalidDataException("wersja formatu pakietu nie jest obsługiwana");
        if (manifest.InterfaceVersion != SupportedInterfaceVersion)
            throw new InvalidDataException("wersja interfejsu nie pasuje do uruchamiacza");
        if (manifest.HostProtocolVersion != SupportedHostProtocolVersion)
            throw new InvalidDataException("wersja silnika nie pasuje do interfejsu");
        if (!string.Equals(manifest.Application, "AMC Python", StringComparison.Ordinal))
            throw new InvalidDataException("manifest dotyczy innego programu");
        if (!string.Equals(manifest.EntryPoint, "AMC.exe", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("manifest wskazuje inny plik uruchamiający");
        if (!string.Equals(manifest.PythonModule, "amc_wx_lite", StringComparison.Ordinal))
            throw new InvalidDataException("manifest wskazuje inny moduł interfejsu");
        if (!IsSingleFolderName(manifest.HostFolder))
            throw new InvalidDataException("manifest wskazuje nieprawidłowy folder silnika");
        var profile = ReleaseProfileContract.Validate(
            manifest.ReleaseProfileSchema,
            manifest.ReleaseProfile,
            manifest.ProductId,
            manifest.DisplayName,
            manifest.InstallId,
            manifest.UpdateChannel,
            manifest.UiStateFolder,
            manifest.RoamingProfileFolder,
            manifest.LocalProfileFolder,
            manifest.CacheFolder,
            manifest.LogFolder,
            manifest.CredentialNamespace,
            manifest.Sessions,
            manifest.Capabilities);
        if (manifest.Files.Count == 0 || manifest.StartupFiles.Count == 0)
            throw new InvalidDataException("manifest nie zawiera kompletnej listy startowej");

        var files = new HashSet<string>(manifest.Files, StringComparer.OrdinalIgnoreCase);
        if (files.Count != manifest.Files.Count)
            throw new InvalidDataException("manifest zawiera powtórzone pliki");
        if (manifest.FileHashes.Count != files.Count)
            throw new InvalidDataException("manifest nie zawiera sum wszystkich plików");
        if (manifest.FileSizes.Count > 0 && manifest.FileSizes.Count != files.Count)
            throw new InvalidDataException("manifest nie zawiera rozmiarów wszystkich plików");
        if (verifyAllFiles && manifest.FileSizes.Count != files.Count)
            throw new InvalidDataException("pełne sprawdzenie wymaga rozmiaru każdego pliku");

        var required = new[]
        {
            "AMC.exe",
            "runtime/python.exe",
            "runtime/pythonw.exe",
            "app/amc_wx_lite/__main__.py",
            $"{manifest.HostFolder}/amc_lite_host.exe",
        };
        var startup = new HashSet<string>(manifest.StartupFiles, StringComparer.OrdinalIgnoreCase);
        foreach (var relative in required)
        {
            if (!startup.Contains(relative))
                throw new InvalidDataException($"manifest nie obejmuje pliku startowego {relative}");
        }

        var filesToVerify = verifyAllFiles ? manifest.Files : manifest.StartupFiles;
        foreach (var relative in filesToVerify)
        {
            if (!files.Contains(relative))
                throw new InvalidDataException($"plik {relative} nie należy do pakietu");
            if (!manifest.FileHashes.TryGetValue(relative, out var expected)
                || !IsSha256(expected))
                throw new InvalidDataException($"brakuje sumy SHA-256 pliku {relative}");
            var path = ResolveInside(root, relative, mustExist: true);
            var info = new FileInfo(path);
            if (manifest.FileSizes.TryGetValue(relative, out var expectedSize)
                && (expectedSize < 0 || info.Length != expectedSize))
                throw new InvalidDataException(
                    $"plik {relative} jest uszkodzony: ma nieprawidłowy rozmiar");
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
            var actual = Convert.ToHexString(SHA256.HashData(stream));
            if (!string.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException($"plik {relative} jest uszkodzony");
        }

        var hostExecutable = ResolveInside(
            root,
            $"{manifest.HostFolder}/amc_lite_host.exe",
            mustExist: true);
        return new VerifiedBundle(root, hostExecutable, manifest, profile);
    }

    private static bool IsSingleFolderName(string value) =>
        !string.IsNullOrWhiteSpace(value)
        && !Path.IsPathRooted(value)
        && Path.GetFileName(value) == value
        && value is not "." and not "..";

    private static bool IsSha256(string value) =>
        value.Length == 64 && value.All(Uri.IsHexDigit);

    private static string ResolveInside(string root, string relative, bool mustExist)
    {
        if (string.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative))
            throw new InvalidDataException("manifest zawiera nieprawidłową ścieżkę");
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)
                       + Path.DirectorySeparatorChar;
        var normalized = relative.Replace('/', Path.DirectorySeparatorChar);
        var full = Path.GetFullPath(Path.Combine(fullRoot, normalized));
        if (!full.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("manifest próbuje wyjść poza folder programu");
        if (mustExist && !File.Exists(full))
            throw new InvalidDataException($"brakuje pliku startowego {relative}");
        return full;
    }
}
