using System.Text;
using AccessibleMediaController.Core.YouTube;
using AccessibleMediaController.Windows.Services;

internal static class YouTubeCredentialBoundaryTests
{
    internal static void Run()
    {
        var testTarget = YouTubeCredentialStore.TargetNameForReleaseProfile("test");
        var publicTarget = YouTubeCredentialStore.TargetNameForReleaseProfile("public");
        Assert(testTarget != publicTarget, "AMC Test i AMC dostały ten sam magazyn konta YouTube.");
        Assert(testTarget.Contains("/test/", StringComparison.Ordinal)
               && publicTarget.Contains("/public/", StringComparison.Ordinal),
            "Nazwa magazynu nie wiąże poświadczeń z profilem wydania.");

        var rejected = false;
        try { _ = YouTubeCredentialStore.ForReleaseProfile("nieznany"); }
        catch (InvalidOperationException) { rejected = true; }
        Assert(rejected, "Nieznany profil dostałby wspólny magazyn poświadczeń.");

        var original = new YouTubeTokenSet(
            "syntetyczny-access",
            "syntetyczny-refresh",
            new DateTimeOffset(2026, 10, 21, 14, 0, 0, TimeSpan.Zero),
            YouTubeOAuthProtocol.ReadOnlyScope,
            "1234567890-example.apps.googleusercontent.com");
        var bytes = YouTubeCredentialStore.Serialize(original);
        try
        {
            Assert(YouTubeCredentialStore.TryDeserialize(bytes, out var restored)
                   && restored == original,
                "Magazyn nie odtwarza pełnego zestawu tokenów.");
        }
        finally
        {
            System.Security.Cryptography.CryptographicOperations.ZeroMemory(bytes);
        }

        Assert(!YouTubeCredentialStore.TryDeserialize(
                Encoding.UTF8.GetBytes("{\"AccessToken\":\"tylko-jedno-pole\"}"), out _),
            "Magazyn przyjął niepełny rekord poświadczeń.");
        Assert(!YouTubeCredentialStore.TryDeserialize(new byte[2561], out _),
            "Magazyn przyjął rekord przekraczający bezpieczny limit Windows.");

        Console.WriteLine("OK: poświadczenia YouTube są rozdzielone dla AMC Test i AMC (6 sprawdzeń)");
    }

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
