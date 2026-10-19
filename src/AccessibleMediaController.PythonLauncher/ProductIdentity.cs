using AccessibleMediaController.ReleaseProfiles;

namespace AccessibleMediaController.PythonLauncher;

internal static class ProductIdentity
{
    internal static bool IsMainWindowTitle(
        ReleaseProfileDescriptor profile,
        string title) =>
        ReleaseProfileContract.IsWindowTitle(profile, title);
}
