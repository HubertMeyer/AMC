using AccessibleMediaController.Core.YouTube;

internal static class YouTubeOAuthFoundationTests
{
    private const string ClientId =
        "1234567890-example.apps.googleusercontent.com";

    internal static void Run()
    {
        BuildsReadOnlyPkceRequestWithoutSecret();
        RejectsUnsafeCallbackAddresses();
        BuildsTokenRequestsWithoutClientSecret();
        PreservesRefreshTokenAndScope();
        DoesNotEchoMalformedResponse();
        Console.WriteLine("OK: bezpieczny fundament oficjalnego logowania YouTube (5 scenariuszy)");
    }

    private static void BuildsReadOnlyPkceRequestWithoutSecret()
    {
        var verifierEntropy = Enumerable.Range(0, 32).Select(value => (byte)value).ToArray();
        var stateEntropy = Enumerable.Range(32, 32).Select(value => (byte)value).ToArray();
        var callback = new Uri("http://127.0.0.1:49321/youtube/callback/");
        var request = YouTubeOAuthProtocol.CreateAuthorizationRequest(
            ClientId,
            callback,
            verifierEntropy,
            stateEntropy);
        var query = ParseQuery(request.AuthorizationUri.Query);

        Assert(request.CodeVerifier.Length == 43, "PKCE nie ma bezpiecznej długości.");
        Assert(request.State.Length >= 32, "Stan OAuth nie ma bezpiecznej długości.");
        Assert(query.GetValueOrDefault("scope") == YouTubeOAuthProtocol.ReadOnlyScope,
            "Pierwszy etap żąda innego zakresu niż tylko odczyt YouTube.");
        Assert(query.GetValueOrDefault("code_challenge_method") == "S256",
            "Żądanie nie wymusza PKCE S256.");
        Assert(query.GetValueOrDefault("code_challenge")
               == YouTubeOAuthProtocol.CreateChallenge(request.CodeVerifier),
            "Wyzwanie PKCE nie odpowiada weryfikatorowi.");
        Assert(query.GetValueOrDefault("access_type") == "offline",
            "Żądanie nie prosi o możliwość bezpiecznego odświeżenia sesji.");
        Assert(query.GetValueOrDefault("redirect_uri") == callback.AbsoluteUri,
            "Adres powrotu został zmieniony.");
        Assert(!request.AuthorizationUri.AbsoluteUri.Contains("client_secret", StringComparison.OrdinalIgnoreCase)
               && !request.AuthorizationUri.AbsoluteUri.Contains(request.CodeVerifier, StringComparison.Ordinal),
            "Adres logowania ujawnia sekret klienta albo weryfikator PKCE.");
    }

    private static void RejectsUnsafeCallbackAddresses()
    {
        foreach (var value in new[]
                 {
                     "http://localhost:49321/youtube/callback/",
                     "https://127.0.0.1:49321/youtube/callback/",
                     "http://example.com:49321/youtube/callback/",
                     "http://127.0.0.1/youtube/callback/"
                 })
        {
            var rejected = false;
            try
            {
                YouTubeOAuthProtocol.CreateAuthorizationRequest(ClientId, new Uri(value));
            }
            catch (InvalidOperationException)
            {
                rejected = true;
            }
            Assert(rejected, "Przyjęto niebezpieczny adres powrotu: " + value);
        }
    }

    private static void BuildsTokenRequestsWithoutClientSecret()
    {
        var callback = new Uri("http://127.0.0.1:49321/youtube/callback/");
        var verifier = Convert.ToBase64String(new byte[32]).TrimEnd('=').Replace('+', '-').Replace('/', '_');
        var exchange = YouTubeOAuthProtocol.CreateCodeExchangeFields(
            ClientId, callback, "syntetyczny-kod", verifier);
        var refresh = YouTubeOAuthProtocol.CreateRefreshFields(ClientId, "syntetyczne-odswiezenie");

        Assert(exchange.GetValueOrDefault("grant_type") == "authorization_code"
               && exchange.GetValueOrDefault("code_verifier") == verifier,
            "Wymiana kodu nie zachowuje PKCE.");
        Assert(refresh.GetValueOrDefault("grant_type") == "refresh_token",
            "Odświeżenie ma nieprawidłowy rodzaj żądania.");
        Assert(!exchange.ContainsKey("client_secret") && !refresh.ContainsKey("client_secret"),
            "Klient desktop próbowałby wysłać sekret klienta.");
    }

    private static void PreservesRefreshTokenAndScope()
    {
        var now = new DateTimeOffset(2026, 10, 21, 12, 0, 0, TimeSpan.Zero);
        var tokens = YouTubeOAuthProtocol.ReadTokenResponse(
            "{\"access_token\":\"nowy-access\",\"expires_in\":3600}",
            ClientId,
            now,
            existingRefreshToken: "trwale-odswiezenie",
            existingScope: YouTubeOAuthProtocol.ReadOnlyScope);

        Assert(tokens.RefreshToken == "trwale-odswiezenie",
            "Odświeżenie wymazało wcześniej zapisany refresh token.");
        Assert(tokens.Scope == YouTubeOAuthProtocol.ReadOnlyScope,
            "Odświeżenie wymazało przyznany zakres.");
        Assert(tokens.ExpiresAtUtc == now.AddHours(1),
            "Nieprawidłowo obliczono ważność tokenu.");
    }

    private static void DoesNotEchoMalformedResponse()
    {
        const string marker = "SEKRET-NIE-MOZE-BYC-W-WYJATKU";
        try
        {
            YouTubeOAuthProtocol.ReadTokenResponse("{" + marker, ClientId, DateTimeOffset.UtcNow);
            throw new InvalidOperationException("Nieczytelna odpowiedź została przyjęta.");
        }
        catch (InvalidDataException exception)
        {
            Assert(!exception.ToString().Contains(marker, StringComparison.Ordinal),
                "Wyjątek ujawnił treść odpowiedzi serwera.");
        }
    }

    private static Dictionary<string, string> ParseQuery(string query) =>
        query.TrimStart('?')
            .Split('&', StringSplitOptions.RemoveEmptyEntries)
            .Select(part => part.Split('=', 2))
            .ToDictionary(
                pair => Uri.UnescapeDataString(pair[0].Replace('+', ' ')),
                pair => pair.Length == 2
                    ? Uri.UnescapeDataString(pair[1].Replace('+', ' '))
                    : string.Empty,
                StringComparer.Ordinal);

    private static void Assert(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
