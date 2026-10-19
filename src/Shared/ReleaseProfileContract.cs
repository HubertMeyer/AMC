namespace AccessibleMediaController.ReleaseProfiles;

internal sealed record ReleaseProfileDescriptor(
    string ProfileId,
    string ProductId,
    string DisplayName,
    string InstallId,
    string UpdateChannel,
    string UiStateFolder,
    string RoamingProfileFolder,
    string LocalProfileFolder,
    string CacheFolder,
    string LogFolder,
    string CredentialNamespace,
    IReadOnlyList<string> Sessions,
    IReadOnlyList<string> Capabilities,
    string LauncherMutexName,
    string UpdaterMutexName,
    string UpdaterHelperFolder,
    string UpdaterHelperExecutablePrefix,
    string PreferredInstallationFolder,
    IReadOnlyList<string> AcceptedWindowTitles);

/// <summary>
/// Closed, versioned release profile catalog shared by the launcher and
/// updater. A manifest may select a profile, but it may not redefine any of
/// its isolation or capability fields.
/// </summary>
internal static class ReleaseProfileContract
{
    internal const int SupportedSchema = 1;

    private static readonly string[] CommonCapabilities =
    [
        "session.files",
        "session.radio",
        "session.podcasts-youtube",
        "session.wiim",
        "recording",
        "schedules",
        "bookmarks",
        "chapters",
        "command-palette",
        "keyboard-help",
        "problem-report-local",
    ];

    internal static readonly ReleaseProfileDescriptor Test = new(
        "test",
        "org.accessible-media-controller.test",
        "AMC Test",
        "AMC.Test.win-x64",
        "test",
        "AMC-wx-Lite",
        "AccessibleMediaController",
        "AccessibleMediaController",
        "AMC-wx-Lite/cache",
        "AMC-wx-Lite/logs",
        "AccessibleMediaController.Test",
        ["files", "radio", "podcasts", "tidal", "wiim", "sonos", "spotify"],
        CommonCapabilities.Concat(
        [
            "session.sonos",
            "session.spotify",
            "session.tidal",
            "spotify.playlists",
            "experimental",
        ]).ToArray(),
        @"Local\AccessibleMultimediaController.PythonLauncher.SingleInstance",
        @"Local\AccessibleMultimediaController.PythonUpdater.Test.SingleInstance",
        "AMC-Python/Updater",
        "AMC-Python-Updater",
        "AMC Python",
        ["AMC Test", "AMC Python"]);

    internal static readonly ReleaseProfileDescriptor Public = new(
        "public",
        "org.accessible-media-controller.public",
        "AMC",
        "AMC.Public.win-x64",
        "stable",
        "AMC/ui",
        "AMC/profile",
        "AMC/profile",
        "AMC/cache",
        "AMC/logs",
        "AccessibleMediaController.Public",
        ["files", "radio", "podcasts", "wiim"],
        CommonCapabilities,
        @"Local\AccessibleMultimediaController.PythonLauncher.Public.SingleInstance",
        @"Local\AccessibleMultimediaController.PythonUpdater.Public.SingleInstance",
        "AMC/Updater",
        "AMC-Updater",
        "AMC",
        ["AMC"]);

    internal static ReleaseProfileDescriptor Validate(
        int schema,
        string profileId,
        string productId,
        string displayName,
        string installId,
        string updateChannel,
        string uiStateFolder,
        string roamingProfileFolder,
        string localProfileFolder,
        string cacheFolder,
        string logFolder,
        string credentialNamespace,
        IReadOnlyList<string>? sessions,
        IReadOnlyList<string>? capabilities)
    {
        if (schema != SupportedSchema)
            throw new InvalidDataException("wersja profilu wydania nie jest obsługiwana");
        var expected = profileId switch
        {
            "test" => Test,
            "public" => Public,
            _ => throw new InvalidDataException("manifest wskazuje nieznany profil wydania"),
        };

        Require(expected.ProductId, productId, "identyfikator produktu");
        Require(expected.DisplayName, displayName, "nazwa wydania");
        Require(expected.InstallId, installId, "identyfikator instalacji");
        Require(expected.UpdateChannel, updateChannel, "kanał aktualizacji");
        Require(expected.UiStateFolder, uiStateFolder, "folder interfejsu");
        Require(expected.RoamingProfileFolder, roamingProfileFolder, "folder ustawień");
        Require(expected.LocalProfileFolder, localProfileFolder, "folder danych lokalnych");
        Require(expected.CacheFolder, cacheFolder, "folder pamięci podręcznej");
        Require(expected.LogFolder, logFolder, "folder dzienników");
        Require(expected.CredentialNamespace, credentialNamespace, "przestrzeń poświadczeń");
        RequireSequence(expected.Sessions, sessions, "lista sesji");
        RequireSequence(expected.Capabilities, capabilities, "lista możliwości");
        return expected;
    }

    internal static bool IsWindowTitle(ReleaseProfileDescriptor profile, string title) =>
        profile.AcceptedWindowTitles.Any(productName =>
            string.Equals(title, productName, StringComparison.Ordinal)
            || title.StartsWith(productName + " — ", StringComparison.Ordinal));

    private static void Require(string expected, string actual, string field)
    {
        if (!string.Equals(expected, actual, StringComparison.Ordinal))
            throw new InvalidDataException($"profil wydania ma nieprawidłowe pole: {field}");
    }

    private static void RequireSequence(
        IReadOnlyList<string> expected,
        IReadOnlyList<string>? actual,
        string field)
    {
        if (actual is null || !expected.SequenceEqual(actual, StringComparer.Ordinal))
            throw new InvalidDataException($"profil wydania ma nieprawidłowe pole: {field}");
    }
}
