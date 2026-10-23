using System.Net;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeOAuthFoundationTests
{
    private const string ClientId =
        "1234567890-example.apps.googleusercontent.com";
    private const string ClientSecret = "syntetyczny-sekret-klienta";

    internal static void Run()
    {
        BuildsReadOnlyPkceRequestWithoutSecret();
        RejectsUnsafeCallbackAddresses();
        BuildsTokenRequestsWithRequiredClientSecret();
        PreservesRefreshTokenAndScope();
        DoesNotEchoMalformedResponse();
        ExchangesCodeThroughOfficialEndpoint();
        RefreshesWithoutLosingRefreshToken();
        SanitizesTokenEndpointErrors();
        ExplainsDesktopClientConfigurationErrors();
        ReceivesValidLoopbackCallbackWithoutEchoingCode();
        RejectsWrongLoopbackState();
        Console.WriteLine("OK: bezpieczny fundament oficjalnego logowania YouTube (11 scenariuszy)");
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

    private static void BuildsTokenRequestsWithRequiredClientSecret()
    {
        var callback = new Uri("http://127.0.0.1:49321/youtube/callback/");
        var verifier = Convert.ToBase64String(new byte[32]).TrimEnd('=').Replace('+', '-').Replace('/', '_');
        var exchange = YouTubeOAuthProtocol.CreateCodeExchangeFields(
            ClientId, ClientSecret, callback, "syntetyczny-kod", verifier);
        var refresh = YouTubeOAuthProtocol.CreateRefreshFields(
            ClientId, ClientSecret, "syntetyczne-odswiezenie");

        Assert(exchange.GetValueOrDefault("grant_type") == "authorization_code"
               && exchange.GetValueOrDefault("code_verifier") == verifier,
            "Wymiana kodu nie zachowuje PKCE.");
        Assert(refresh.GetValueOrDefault("grant_type") == "refresh_token",
            "Odświeżenie ma nieprawidłowy rodzaj żądania.");
        Assert(exchange.GetValueOrDefault("client_secret") == ClientSecret
               && refresh.GetValueOrDefault("client_secret") == ClientSecret,
            "Punkt tokenów nie dostał sekretu wymaganego przez tego klienta desktopowego.");
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

    private static void ExchangesCodeThroughOfficialEndpoint()
    {
        var handler = new TokenHandler(
            HttpStatusCode.OK,
            "{\"access_token\":\"syntetyczny-access\",\"refresh_token\":\"syntetyczny-refresh\",\"expires_in\":3600,\"scope\":\"https://www.googleapis.com/auth/youtube.readonly\"}");
        using var client = new YouTubeOAuthTokenClient(new HttpClient(handler));
        var verifier = Convert.ToBase64String(new byte[32]).TrimEnd('=').Replace('+', '-').Replace('/', '_');
        var callback = new Uri("http://127.0.0.1:49321/youtube/callback/");
        var tokens = client.ExchangeCodeAsync(
                ClientId, ClientSecret, callback, "syntetyczny-kod", verifier,
                new DateTimeOffset(2026, 10, 21, 12, 0, 0, TimeSpan.Zero),
                CancellationToken.None)
            .GetAwaiter().GetResult();
        var form = ParseQuery(handler.Body);

        Assert(handler.RequestUri?.AbsoluteUri == "https://oauth2.googleapis.com/token",
            "Wymiana kodu używa innego punktu niż oficjalny punkt tokenów Google.");
        Assert(form.GetValueOrDefault("code") == "syntetyczny-kod"
               && form.GetValueOrDefault("code_verifier") == verifier,
            "Transport nie przekazał kodu i weryfikatora PKCE.");
        Assert(form.GetValueOrDefault("client_secret") == ClientSecret,
            "Transport nie wysłał sekretu wymaganego przez klienta Google.");
        Assert(tokens.RefreshToken == "syntetyczny-refresh", "Nie odczytano refresh tokenu.");
    }

    private static void RefreshesWithoutLosingRefreshToken()
    {
        var handler = new TokenHandler(
            HttpStatusCode.OK,
            "{\"access_token\":\"nowy-access\",\"expires_in\":1800}");
        using var client = new YouTubeOAuthTokenClient(new HttpClient(handler));
        var current = new YouTubeTokenSet(
            "stary-access", "trwale-odswiezenie", DateTimeOffset.UtcNow.AddMinutes(-1),
            YouTubeOAuthProtocol.ReadOnlyScope, ClientId);
        var refreshed = client.RefreshAsync(
                current, ClientSecret, DateTimeOffset.UtcNow, CancellationToken.None)
            .GetAwaiter().GetResult();
        var form = ParseQuery(handler.Body);

        Assert(form.GetValueOrDefault("refresh_token") == current.RefreshToken,
            "Transport nie przekazał refresh tokenu.");
        Assert(!form.ContainsKey("scope"),
            "Odświeżenie próbowałoby po cichu rozszerzyć zakres uprawnień.");
        Assert(refreshed.RefreshToken == current.RefreshToken,
            "Odpowiedź bez nowego refresh tokenu wylogowałaby konto.");
    }

    private static void SanitizesTokenEndpointErrors()
    {
        const string marker = "SEKRET-Z-ODPOWIEDZI";
        var handler = new TokenHandler(
            HttpStatusCode.BadRequest,
            "{\"error\":\"invalid_grant\",\"error_description\":\"" + marker + "\"}");
        using var client = new YouTubeOAuthTokenClient(new HttpClient(handler));
        var current = new YouTubeTokenSet(
            "access", "refresh", DateTimeOffset.UtcNow.AddMinutes(-1),
            YouTubeOAuthProtocol.ReadOnlyScope, ClientId);
        try
        {
            client.RefreshAsync(
                    current, ClientSecret, DateTimeOffset.UtcNow, CancellationToken.None)
                .GetAwaiter().GetResult();
            throw new InvalidOperationException("Odrzucona odpowiedź została przyjęta.");
        }
        catch (InvalidOperationException exception)
        {
            Assert(!exception.ToString().Contains(marker, StringComparison.Ordinal),
                "Błąd punktu tokenów ujawnił treść odpowiedzi.");
            Assert(exception.Message.Contains("Zaloguj się ponownie", StringComparison.Ordinal),
                "Błąd invalid_grant nie dostał użytkowego komunikatu.");
        }
    }

    private static void ExplainsDesktopClientConfigurationErrors()
    {
        foreach (var (code, expected) in new[]
                 {
                     ("unauthorized_client", "Aplikacja komputerowa"),
                     ("invalid_request", "Aplikacja komputerowa"),
                     ("redirect_uri_mismatch", "Aplikacja komputerowa")
                 })
        {
            var handler = new TokenHandler(
                HttpStatusCode.BadRequest,
                $"{{\"error\":\"{code}\",\"error_description\":\"SEKRET\"}}");
            using var client = new YouTubeOAuthTokenClient(new HttpClient(handler));
            var verifier = Convert.ToBase64String(new byte[32])
                .TrimEnd('=').Replace('+', '-').Replace('/', '_');
            try
            {
                client.ExchangeCodeAsync(
                        ClientId,
                        ClientSecret,
                        new Uri("http://127.0.0.1:49321/youtube/callback/"),
                        "kod",
                        verifier,
                        DateTimeOffset.UtcNow,
                        CancellationToken.None)
                    .GetAwaiter().GetResult();
                throw new InvalidOperationException("Odrzucona konfiguracja została przyjęta.");
            }
            catch (InvalidOperationException exception)
            {
                Assert(exception.Message.Contains(expected, StringComparison.Ordinal),
                    $"Kod {code} nie wyjaśnia wymaganego typu klienta.");
                Assert(!exception.ToString().Contains("SEKRET", StringComparison.Ordinal),
                    $"Kod {code} ujawnił opis odpowiedzi Google.");
            }
        }
    }

    private static void ReceivesValidLoopbackCallbackWithoutEchoingCode()
    {
        using var receiver = YouTubeOAuthLoopbackReceiver.Start();
        var request = YouTubeOAuthProtocol.CreateAuthorizationRequest(ClientId, receiver.RedirectUri);
        const string code = "kod-ktory-nie-moze-wrocic-w-html";
        var receiveTask = receiver.ReceiveAsync(request.State, CancellationToken.None);
        using var http = new HttpClient();
        var uri = new UriBuilder(receiver.RedirectUri)
        {
            Query = "state=" + Uri.EscapeDataString(request.State)
                + "&code=" + Uri.EscapeDataString(code)
        }.Uri;
        var response = http.GetAsync(uri).GetAwaiter().GetResult();
        var page = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
        var callback = receiveTask.GetAwaiter().GetResult();

        Assert(callback.Succeeded && callback.Code == code,
            "Lokalny odbiornik nie przekazał prawidłowego kodu hostowi.");
        Assert(!page.Contains(code, StringComparison.Ordinal)
               && page.Contains("AMC jeszcze kończy logowanie", StringComparison.Ordinal)
               && page.Contains("sprawdzić wynik w aplikacji", StringComparison.Ordinal),
            "Strona powrotu ujawniła kod albo nie podała użytkowej instrukcji.");
        Assert(response.Headers.CacheControl?.NoStore == true,
            "Strona powrotu mogłaby zostać zapisana w pamięci podręcznej.");
    }

    private static void RejectsWrongLoopbackState()
    {
        using var receiver = YouTubeOAuthLoopbackReceiver.Start();
        var receiveTask = receiver.ReceiveAsync("oczekiwany-stan-bezpieczenstwa", CancellationToken.None);
        using var http = new HttpClient();
        var uri = new UriBuilder(receiver.RedirectUri)
        {
            Query = "state=obcy-stan&code=obcy-kod"
        }.Uri;
        _ = http.GetAsync(uri).GetAwaiter().GetResult();
        var callback = receiveTask.GetAwaiter().GetResult();

        Assert(!callback.Succeeded && callback.Code is null,
            "Odbiornik przyjął odpowiedź z obcej sesji OAuth.");
        Assert(callback.Message.Contains("zabezpieczenie sesji", StringComparison.Ordinal),
            "Odrzucenie obcej sesji nie ma użytkowego komunikatu.");
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

    private sealed class TokenHandler(HttpStatusCode statusCode, string responseBody) : HttpMessageHandler
    {
        internal Uri? RequestUri { get; private set; }
        internal string Body { get; private set; } = string.Empty;

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            RequestUri = request.RequestUri;
            Body = request.Content is null
                ? string.Empty
                : await request.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            return new HttpResponseMessage(statusCode)
            {
                Content = new StringContent(responseBody)
            };
        }
    }
}
