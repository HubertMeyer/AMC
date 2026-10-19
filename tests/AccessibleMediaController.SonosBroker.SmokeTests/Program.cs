using System.Net;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.SonosBroker;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

var tests = new (string Name, Func<Task> Run)[]
{
    ("Brak sekretów uruchamia bezpieczny stan nieskonfigurowany", ConfigurationCanBeAbsent),
    ("Częściowa konfiguracja jest odrzucana", PartialConfigurationIsRejected),
    ("Publiczny adres i callback muszą mieć ten sam HTTPS origin", ConfigurationRequiresExactOrigin),
    ("Sesja PKCE jest jednorazowa", SessionIsOneTime),
    ("Zły verifier nie konsumuje gotowego wyniku", WrongVerifierDoesNotConsume),
    ("Powtórzony callback nie rozpoczyna drugiej wymiany", CallbackCannotStartTwice),
    ("Wygasła sesja znika", ExpiredSessionDisappears),
    ("Limit sesji jest ścisły także równolegle", CapacityIsStrict),
    ("Adres autoryzacji zawiera wyłącznie ustalony kontrakt Sonosa", AuthorizeUriIsExact),
    ("Wymiana kodu używa Basic i nie ujawnia sekretu w adresie", CodeExchangeIsServerSide),
    ("Odnowienie zachowuje stary refresh token, gdy Sonos go nie obraca", RefreshKeepsFallbackToken),
    ("Odmowa odnowienia wymaga ponownego logowania", RefreshInvalidGrantIsNamed),
    ("Endpointy start, odmowa i jednorazowy wynik są zgodne z klientem AMC", EndpointsMatchClientContract)
};

var failed = new List<string>();
foreach (var test in tests)
{
    try
    {
        await test.Run();
        Console.WriteLine("[OK] " + test.Name);
    }
    catch (Exception error)
    {
        failed.Add(test.Name + ": " + error.Message);
        Console.WriteLine("[BŁĄD] " + test.Name + ": " + error.Message);
    }
}

if (failed.Count > 0)
{
    Console.Error.WriteLine("Nieudane testy: " + failed.Count);
    return 1;
}

Console.WriteLine("Wszystkie testy brokera Sonos przeszły: " + tests.Length + ".");
return 0;

static Task ConfigurationCanBeAbsent()
{
    var state = SonosBrokerOptions.Load(Configuration(new Dictionary<string, string?>()));
    Assert(!state.IsConfigured, "pusta konfiguracja nie może pozorować gotowego brokera");
    return Task.CompletedTask;
}

static Task PartialConfigurationIsRejected()
{
    AssertThrows<InvalidOperationException>(() => SonosBrokerOptions.Load(Configuration(
        new Dictionary<string, string?> { ["SONOS_CLIENT_ID"] = "client" })));
    return Task.CompletedTask;
}

static Task ConfigurationRequiresExactOrigin()
{
    var good = SonosBrokerOptions.Load(Configuration(ValidConfiguration()));
    Assert(good.IsConfigured, "pełna konfiguracja powinna działać");
    Assert(good.Options!.RedirectUri.AbsoluteUri == "https://sonos.example.test/login/callback",
        "callback musi pozostać dokładny");

    var bad = ValidConfiguration();
    bad["SONOS_REDIRECT_URI"] = "https://other.example.test/login/callback";
    AssertThrows<InvalidOperationException>(() => SonosBrokerOptions.Load(Configuration(bad)));

    var subpath = ValidConfiguration();
    subpath["SONOS_BROKER_PUBLIC_ORIGIN"] = "https://sonos.example.test/broker/";
    subpath["SONOS_REDIRECT_URI"] = "https://sonos.example.test/broker/login/callback";
    AssertThrows<InvalidOperationException>(() => SonosBrokerOptions.Load(Configuration(subpath)));
    return Task.CompletedTask;
}

static Task SessionIsOneTime()
{
    var now = DateTimeOffset.Parse("2026-10-19T02:00:00Z");
    var (verifier, challenge) = Pkce();
    var store = new SonosLoginSessionStore(4);
    var created = store.Create(challenge, now, TimeSpan.FromMinutes(10));
    Assert(created.Status == SessionCreateStatus.Success, "sesja nie powstała");
    Assert(store.ReadOnce(created.SessionId, verifier, now).Status == SessionReadStatus.Pending,
        "przed callbackiem wynik ma być oczekujący");
    Assert(store.BeginCallback(created.State, now) == CallbackBeginStatus.Started,
        "callback nie rozpoczął się");
    var tokens = Tokens("refresh-1");
    Assert(store.StoreCallback(created.State, SessionReadStatus.Success, tokens, now)
        == CallbackStoreStatus.Stored, "wynik nie został zapisany");
    var first = store.ReadOnce(created.SessionId, verifier, now);
    Assert(first.Status == SessionReadStatus.Success && first.Tokens?.AccessToken == "access",
        "pierwszy odbiór nie zwrócił tokenu");
    Assert(store.ReadOnce(created.SessionId, verifier, now).Status == SessionReadStatus.Unknown,
        "drugi odbiór nie może zwrócić tokenu");
    return Task.CompletedTask;
}

static Task WrongVerifierDoesNotConsume()
{
    var now = DateTimeOffset.UtcNow;
    var (verifier, challenge) = Pkce();
    var store = new SonosLoginSessionStore(4);
    var created = store.Create(challenge, now, TimeSpan.FromMinutes(10));
    store.BeginCallback(created.State, now);
    store.StoreCallback(created.State, SessionReadStatus.Success, Tokens("refresh"), now);
    var wrong = new string('A', 43);
    if (wrong == verifier)
    {
        wrong = new string('B', 43);
    }

    Assert(store.ReadOnce(created.SessionId, wrong, now).Status == SessionReadStatus.ProofMismatch,
        "zły verifier powinien być nazwany");
    Assert(store.ReadOnce(created.SessionId, verifier, now).Status == SessionReadStatus.Success,
        "zły verifier nie może skonsumować poprawnego wyniku");
    return Task.CompletedTask;
}

static Task CallbackCannotStartTwice()
{
    var now = DateTimeOffset.UtcNow;
    var (_, challenge) = Pkce();
    var store = new SonosLoginSessionStore(4);
    var created = store.Create(challenge, now, TimeSpan.FromMinutes(10));
    Assert(store.BeginCallback(created.State, now) == CallbackBeginStatus.Started,
        "pierwszy callback powinien ruszyć");
    Assert(store.BeginCallback(created.State, now) == CallbackBeginStatus.AlreadyStarted,
        "drugi callback musi zostać zatrzymany przed wymianą kodu");
    return Task.CompletedTask;
}

static Task ExpiredSessionDisappears()
{
    var now = DateTimeOffset.UtcNow;
    var (verifier, challenge) = Pkce();
    var store = new SonosLoginSessionStore(1);
    var created = store.Create(challenge, now, TimeSpan.FromSeconds(1));
    Assert(store.ReadOnce(created.SessionId, verifier, now.AddSeconds(1)).Status
        == SessionReadStatus.Unknown, "wygasła sesja nadal istnieje");
    Assert(store.Create(challenge, now.AddSeconds(1), TimeSpan.FromMinutes(1)).Status
        == SessionCreateStatus.Success, "wygasła sesja nadal zajmuje limit");
    return Task.CompletedTask;
}

static Task CapacityIsStrict()
{
    var now = DateTimeOffset.UtcNow;
    var (_, challenge) = Pkce();
    var store = new SonosLoginSessionStore(1);
    var results = new SessionCreateResult[20];
    Parallel.For(0, results.Length, index =>
        results[index] = store.Create(challenge, now, TimeSpan.FromMinutes(1)));
    Assert(results.Count(item => item.Status == SessionCreateStatus.Success) == 1,
        "równoległe starty przekroczyły limit jednej sesji");
    return Task.CompletedTask;
}

static Task AuthorizeUriIsExact()
{
    var options = Options();
    using var http = new HttpClient(new ScriptedHandler(_ =>
        new HttpResponseMessage(HttpStatusCode.InternalServerError)));
    var gateway = new SonosOAuthGateway(options, http);
    var state = new string('S', 43);
    var uri = gateway.CreateAuthorizeUri(state);
    Assert(uri.GetLeftPart(UriPartial.Path) == "https://api.sonos.com/login/v3/oauth",
        "użyto innego endpointu autoryzacji");
    var query = Microsoft.AspNetCore.WebUtilities.QueryHelpers.ParseQuery(uri.Query);
    Assert(query["client_id"] == "client-id", "brak client_id");
    Assert(query["state"] == state, "stan został zmieniony");
    Assert(query["scope"] == "playback-control-all", "zły zakres");
    Assert(query["redirect_uri"] == "https://sonos.example.test/login/callback", "zły callback");
    Assert(!uri.AbsoluteUri.Contains("client-secret", StringComparison.Ordinal),
        "sekret trafił do adresu przeglądarki");
    return Task.CompletedTask;
}

static async Task CodeExchangeIsServerSide()
{
    HttpRequestMessage? captured = null;
    string? form = null;
    using var http = new HttpClient(new ScriptedHandler(async request =>
    {
        captured = request;
        form = await request.Content!.ReadAsStringAsync();
        return Json(HttpStatusCode.OK,
            "{\"access_token\":\"access\",\"token_type\":\"Bearer\",\"expires_in\":86400,\"refresh_token\":\"refresh\",\"scope\":\"playback-control-all\"}");
    }));
    var result = await new SonosOAuthGateway(Options(), http)
        .ExchangeCodeAsync("authorization-code", CancellationToken.None);
    Assert(result.Status == OAuthStatus.Success, "wymiana kodu nie zakończyła się sukcesem");
    Assert(captured!.RequestUri == SonosOAuthGateway.TokenEndpoint, "zły endpoint tokenu");
    Assert(captured.Headers.Authorization?.Scheme == "Basic", "brak uwierzytelnienia Basic");
    Assert(captured.RequestUri!.Query.Length == 0, "sekret lub kod trafił do query");
    Assert(form!.Contains("grant_type=authorization_code", StringComparison.Ordinal)
        && form.Contains("code=authorization-code", StringComparison.Ordinal),
        "brak danych wymiany w formularzu POST");
}

static async Task RefreshKeepsFallbackToken()
{
    using var http = new HttpClient(new ScriptedHandler(_ => Json(HttpStatusCode.OK,
        "{\"access_token\":\"new-access\",\"token_type\":\"Bearer\",\"expires_in\":86400}")));
    var result = await new SonosOAuthGateway(Options(), http)
        .RefreshAsync("old-refresh", CancellationToken.None);
    Assert(result.Status == OAuthStatus.Success
        && result.Tokens?.RefreshToken == "old-refresh",
        "brak rotacji nie zachował działającego refresh tokenu");
}

static async Task RefreshInvalidGrantIsNamed()
{
    using var http = new HttpClient(new ScriptedHandler(_ =>
        Json(HttpStatusCode.BadRequest, "{\"error\":\"invalid_grant\"}")));
    var result = await new SonosOAuthGateway(Options(), http)
        .RefreshAsync("old-refresh", CancellationToken.None);
    Assert(result.Status == OAuthStatus.ReauthorizationRequired,
        "odmowa dostawcy nie została rozpoznana");
}

static async Task EndpointsMatchClientContract()
{
    var args = new[]
    {
        "--environment", "Development",
        "--SONOS_BROKER_PUBLIC_ORIGIN", "https://sonos.example.test/",
        "--SONOS_CLIENT_ID", "client-id",
        "--SONOS_CLIENT_SECRET", "client-secret",
        "--SONOS_REDIRECT_URI", "https://sonos.example.test/login/callback"
    };
    await using var app = SonosBrokerApplication.Build(args);
    app.Urls.Add("http://127.0.0.1:0");
    await app.StartAsync();
    try
    {
        var addresses = app.Services.GetRequiredService<IServer>()
            .Features.Get<IServerAddressesFeature>()!.Addresses;
        var address = addresses.Single();
        using var client = new HttpClient { BaseAddress = new Uri(address) };
        var (verifier, challenge) = Pkce();

        using var start = await client.PostAsJsonAsync("/login/start",
            new { code_challenge = challenge, code_challenge_method = "S256" });
        Assert(start.StatusCode == HttpStatusCode.OK, "start nie zwrócił 200");
        using var startJson = JsonDocument.Parse(await start.Content.ReadAsByteArrayAsync());
        var sessionId = startJson.RootElement.GetProperty("session_id").GetString()!;
        var authorize = new Uri(startJson.RootElement.GetProperty("authorize_url").GetString()!);
        var state = Microsoft.AspNetCore.WebUtilities.QueryHelpers.ParseQuery(authorize.Query)["state"].ToString();

        using var callback = await client.GetAsync(
            "/login/callback?error=access_denied&state=" + Uri.EscapeDataString(state));
        Assert(callback.StatusCode == HttpStatusCode.OK, "odmowa Sonosa nie została zapisana");
        var page = await callback.Content.ReadAsStringAsync();
        Assert(page.Contains("Logowanie Sonos", StringComparison.Ordinal)
            && !page.Contains(sessionId, StringComparison.Ordinal),
            "strona callbacku ujawnia techniczny identyfikator");

        using var result = await client.PostAsJsonAsync("/login/result",
            new { session_id = sessionId, code_verifier = verifier });
        Assert(result.StatusCode == HttpStatusCode.BadRequest, "odmowa nie zwróciła 400");
        Assert(await ErrorCode(result) == "access_denied", "odmowa ma zły kod");

        using var replay = await client.PostAsJsonAsync("/login/result",
            new { session_id = sessionId, code_verifier = verifier });
        Assert(replay.StatusCode == HttpStatusCode.NotFound
            && await ErrorCode(replay) == "unknown_session",
            "wynik nie był jednorazowy");
    }
    finally
    {
        await app.StopAsync();
    }
}

static IConfiguration Configuration(Dictionary<string, string?> values) =>
    new ConfigurationBuilder().AddInMemoryCollection(values).Build();

static Dictionary<string, string?> ValidConfiguration() => new()
{
    ["SONOS_BROKER_PUBLIC_ORIGIN"] = "https://sonos.example.test/",
    ["SONOS_CLIENT_ID"] = "client-id",
    ["SONOS_CLIENT_SECRET"] = "client-secret",
    ["SONOS_REDIRECT_URI"] = "https://sonos.example.test/login/callback"
};

static SonosBrokerOptions Options() => SonosBrokerOptions.Load(Configuration(ValidConfiguration())).Options!;

static (string Verifier, string Challenge) Pkce()
{
    var verifier = Base64Url(RandomNumberGenerator.GetBytes(32));
    var challenge = Base64Url(SHA256.HashData(Encoding.ASCII.GetBytes(verifier)));
    return (verifier, challenge);
}

static string Base64Url(byte[] value) =>
    Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');

static TokenResponse Tokens(string refresh) =>
    new("access", "Bearer", 86400, refresh, "playback-control-all");

static HttpResponseMessage Json(HttpStatusCode status, string content) => new(status)
{
    Content = new StringContent(content, Encoding.UTF8, "application/json")
};

static async Task<string?> ErrorCode(HttpResponseMessage response)
{
    using var document = JsonDocument.Parse(await response.Content.ReadAsByteArrayAsync());
    return document.RootElement.GetProperty("error").GetString();
}

static void Assert(bool condition, string message)
{
    if (!condition)
    {
        throw new InvalidOperationException(message);
    }
}

static void AssertThrows<T>(Action action)
    where T : Exception
{
    try
    {
        action();
    }
    catch (T)
    {
        return;
    }

    throw new InvalidOperationException("Nie zgłoszono oczekiwanego wyjątku " + typeof(T).Name + ".");
}

internal sealed class ScriptedHandler(
    Func<HttpRequestMessage, Task<HttpResponseMessage>> responder) : HttpMessageHandler
{
    internal ScriptedHandler(Func<HttpRequestMessage, HttpResponseMessage> responder)
        : this(request => Task.FromResult(responder(request)))
    {
    }

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken) => responder(request);
}
