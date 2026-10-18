namespace AccessibleMediaController.PythonLauncher;

internal static class ProductIdentity
{
    internal const string DisplayName = "AMC Test";
    internal const string LegacyDisplayName = "AMC Python";

    internal static bool IsMainWindowTitle(string title) =>
        IsProductWindowTitle(title, DisplayName)
        || IsProductWindowTitle(title, LegacyDisplayName);

    private static bool IsProductWindowTitle(string title, string productName) =>
        string.Equals(title, productName, StringComparison.Ordinal)
        || title.StartsWith(productName + " — ", StringComparison.Ordinal);
}
