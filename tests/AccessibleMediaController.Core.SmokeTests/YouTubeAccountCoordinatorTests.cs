using System.Net;
using AccessibleMediaController.Core.YouTube;

internal static class YouTubeAccountCoordinatorTests
{
    private const string ClientId = "1234567890-example.apps.googleusercontent.com";
    private const string ClientSecret = "syntetyczny-sekret-klienta";
    private static readonly DateTimeOffset Now =
        new(2026, 10, 21, 15, 0, 0, TimeSpan.Zero);

    internal static void Run()
    {
        LoginStoresTokensOnlyAfterConfirmedCallback();
        DeniedLoginDoesNotReplaceStoredTokens();
        ExpiredTokenRefreshesAndIsStored();
        FreshTokenDoesNotUseNetwork();
        LogoutDeletesOnlyThisStore();
        DefaultLoginWindowSupportsAccessibleFlow();
        Console.WriteLine("OK: koordynator konta YouTube (6 scenariuszy)");
    }

    private static void LoginStoresTokensOnlyAfterConfirmedCallback()
    {
        var store = new MemoryStore();
        var handler = new TokenHandler(HttpStatusCode.OK,
            "{\"access_token\":\"access-po-logowaniu\",\"refresh_token\":\"refresh-po-logowaniu\",\"expires_in\":3600,\"scope\":\"https://www.googleapis.com/auth/youtube.readonly\"}");
        using var tokenClient = new YouTubeOAuthTokenClient(new HttpClient(handler));
        using var coordinator = new YouTubeAccountCoordinator(
            ClientId,
            ClientSecret,
            store,
            tokenClient,
            async (authorizationUri, cancellationToken) =>
            {
                Assert(store.Writes == 0, "Token zapisano przed potwierdzonym powrotem Google.");
                var query = ParseQuery(authorizationUri.Query);
                var callback = new UriBuilder(query["redirect_uri"])
                {
                    Query = "state=" + Uri.EscapeDataString(query["state"])
                        + "&code=syntetyczny-kod"
                }.Uri;
                _ = Task.Run(async () =>
                {
                    using var http = new HttpClient();
                    _ = await http.GetAsync(callback, cancellationToken).ConfigureAwait(false);
                }, cancellationToken);
                await Task.Yield();
                return true;
            },
            () => Now,
            TimeSpan.FromSeconds(5));

        var result = coordinator.LoginAsync(CancellationToken.None).GetAwaiter().GetResult();
        Assert(result.Succeeded && store.Writes == 1, "Logowanie nie zapisało jednego potwierdzonego zestawu.");
        Assert(store.Current?.AccessToken == "access-po-logowaniu", "Zapisano inny token dostępu.");
        Assert(coordinator.GetStatus().Message == "YouTube: zalogowano",
            "Stan konta po zalogowaniu nie jest użytkowy.");
    }

    private static void DeniedLoginDoesNotReplaceStoredTokens()
    {
        var original = Tokens("stary-access", "stary-refresh", Now.AddHours(1));
        var store = new MemoryStore(original);
        var handler = new TokenHandler(HttpStatusCode.OK, "{}");
        using var tokenClient = new YouTubeOAuthTokenClient(new HttpClient(handler));
        using var coordinator = new YouTubeAccountCoordinator(
            ClientId,
            ClientSecret,
            store,
            tokenClient,
            (authorizationUri, cancellationToken) =>
            {
                var query = ParseQuery(authorizationUri.Query);
                var callback = new UriBuilder(query["redirect_uri"])
                {
                    Query = "state=" + Uri.EscapeDataString(query["state"]) + "&error=access_denied"
                }.Uri;
                _ = Task.Run(async () =>
                {
                    using var http = new HttpClient();
                    _ = await http.GetAsync(callback, cancellationToken).ConfigureAwait(false);
                }, cancellationToken);
                return Task.FromResult(true);
            },
            () => Now,
            TimeSpan.FromSeconds(5));

        var result = coordinator.LoginAsync(CancellationToken.None).GetAwaiter().GetResult();
        Assert(!result.Succeeded && result.Message.Contains("anulowane", StringComparison.Ordinal),
            "Odmowa Google nie dostała użytkowego wyniku.");
        Assert(store.Writes == 0 && store.Current == original && handler.Requests == 0,
            "Anulowane logowanie zmieniło token albo wywołało punkt tokenów.");
    }

    private static void ExpiredTokenRefreshesAndIsStored()
    {
        var store = new MemoryStore(Tokens("stary-access", "trwaly-refresh", Now.AddMinutes(-1)));
        var handler = new TokenHandler(HttpStatusCode.OK,
            "{\"access_token\":\"odswiezony-access\",\"expires_in\":3600}");
        using var tokenClient = new YouTubeOAuthTokenClient(new HttpClient(handler));
        using var coordinator = Coordinator(store, tokenClient);

        var access = coordinator.GetAccessTokenAsync(CancellationToken.None).GetAwaiter().GetResult();
        Assert(access == "odswiezony-access" && store.Writes == 1 && handler.Requests == 1,
            "Wygasły token nie został odświeżony dokładnie raz.");
        Assert(store.Current?.RefreshToken == "trwaly-refresh",
            "Odświeżenie utraciło trwały refresh token.");
    }

    private static void FreshTokenDoesNotUseNetwork()
    {
        var store = new MemoryStore(Tokens("swiezy-access", "refresh", Now.AddHours(1)));
        var handler = new TokenHandler(HttpStatusCode.InternalServerError, "{}");
        using var tokenClient = new YouTubeOAuthTokenClient(new HttpClient(handler));
        using var coordinator = Coordinator(store, tokenClient);

        var access = coordinator.GetAccessTokenAsync(CancellationToken.None).GetAwaiter().GetResult();
        Assert(access == "swiezy-access" && handler.Requests == 0 && store.Writes == 0,
            "Świeży token niepotrzebnie uruchomił sieć albo zapis.");
    }

    private static void LogoutDeletesOnlyThisStore()
    {
        var store = new MemoryStore(Tokens("access", "refresh", Now.AddHours(1)));
        var handler = new TokenHandler(HttpStatusCode.OK, "{}");
        using var tokenClient = new YouTubeOAuthTokenClient(new HttpClient(handler));
        using var coordinator = Coordinator(store, tokenClient);

        var result = coordinator.LogoutAsync(CancellationToken.None).GetAwaiter().GetResult();
        Assert(result.Succeeded && store.Deletes == 1 && store.Current is null,
            "Wylogowanie nie usunęło dokładnie bieżącego magazynu.");
        Assert(!coordinator.GetStatus().Connected, "Po wylogowaniu konto nadal jest przedstawiane jako połączone.");
    }

    private static void DefaultLoginWindowSupportsAccessibleFlow()
    {
        Assert(YouTubeAccountCoordinator.DefaultLoginTimeout >= TimeSpan.FromMinutes(15),
            "Domyślne okno logowania jest zbyt krótkie dla dostępnego przepływu Google.");
        Assert(YouTubeAccountCoordinator.DefaultLoginTimeout
               <= YouTubeAccountCoordinator.MaximumLoginTimeout,
            "Domyślne okno logowania przekracza dozwoloną granicę bezpieczeństwa.");
    }

    private static YouTubeAccountCoordinator Coordinator(
        MemoryStore store,
        YouTubeOAuthTokenClient tokenClient) =>
        new(
            ClientId,
            ClientSecret,
            store,
            tokenClient,
            (_, _) => Task.FromResult(false),
            () => Now);

    private static YouTubeTokenSet Tokens(string access, string refresh, DateTimeOffset expires) =>
        new(access, refresh, expires, YouTubeOAuthProtocol.ReadOnlyScope, ClientId);

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

    private sealed class MemoryStore(YouTubeTokenSet? initial = null) : IYouTubeCredentialStore
    {
        internal YouTubeTokenSet? Current { get; private set; } = initial;
        internal int Writes { get; private set; }
        internal int Deletes { get; private set; }

        public bool TryRead(out YouTubeTokenSet? tokens)
        {
            tokens = Current;
            return tokens is not null;
        }

        public void Write(YouTubeTokenSet tokens)
        {
            Current = tokens;
            Writes++;
        }

        public void Delete()
        {
            Current = null;
            Deletes++;
        }
    }

    private sealed class TokenHandler(HttpStatusCode statusCode, string responseBody) : HttpMessageHandler
    {
        internal int Requests { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            Requests++;
            return Task.FromResult(new HttpResponseMessage(statusCode)
            {
                Content = new StringContent(responseBody)
            });
        }
    }
}
