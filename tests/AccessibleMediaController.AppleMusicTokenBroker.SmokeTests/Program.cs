using System.Net;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.AppleMusicTokenBroker;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

var tests = new (string Name, Func<Task> Run)[]
{
    ("brak konfiguracji", MissingConfigurationIsNotReady),
    ("niepełna konfiguracja", PartialConfigurationIsRejected),
    ("ograniczenia originu", InvalidOriginsAreRejected),
    ("zakres czasu życia", InvalidLifetimeIsRejected),
    ("walidacja klucza", InvalidKeyIsRejected),
    ("podpis ES256", TokenIsSignedAndScoped),
    ("kontrakt endpointu", EndpointRequiresAllowedOrigin),
    ("preflight CORS", CorsPreflightIsNarrow),
    ("HTTPS bez zaufanego proxy", UntrustedProxyCannotClaimHttps),
    ("HTTPS przez zaufane proxy", TrustedProxyCanTerminateTls),
    ("limit osobny dla klienta", RateLimitUsesForwardedClientAddress),
    ("stan nie ujawnia identyfikatorów", HealthDoesNotExposeIdentifiers)
};

var passed = 0;
foreach (var test in tests)
{
    try
    {
        await test.Run();
        passed++;
        Console.WriteLine($"OK {test.Name}");
    }
    catch (Exception error)
    {
        Console.Error.WriteLine($"FAIL {test.Name}: {error.Message}");
        return 1;
    }
}

Console.WriteLine($"Zaliczono {passed}/{tests.Length} testów brokera tokenów Apple Music.");
return 0;

static Task MissingConfigurationIsNotReady()
{
    var loaded = AppleMusicTokenOptions.Load(Configuration(new()));
    Assert(!loaded.IsConfigured, "pusta konfiguracja udaje gotową");
    return Task.CompletedTask;
}

static Task PartialConfigurationIsRejected()
{
    AssertThrows<InvalidOperationException>(() => AppleMusicTokenOptions.Load(Configuration(new()
    {
        ["APPLE_MUSIC_TEAM_ID"] = "TEAM123456"
    })));
    return Task.CompletedTask;
}

static Task InvalidOriginsAreRejected()
{
    using var fixture = KeyFixture.Create();
    foreach (var invalid in new[]
    {
        "http://applemusic.example.test",
        "https://applemusic.example.test/player",
        "https://applemusic.example.test,https://applemusic.example.test/"
    })
    {
        var values = fixture.Configuration();
        values["APPLE_MUSIC_ALLOWED_ORIGINS"] = invalid;
        AssertThrows<InvalidOperationException>(() =>
            AppleMusicTokenOptions.Load(Configuration(values)));
    }

    return Task.CompletedTask;
}

static Task InvalidLifetimeIsRejected()
{
    using var fixture = KeyFixture.Create();
    foreach (var invalid in new[] { "4", "1441", "godzina" })
    {
        var values = fixture.Configuration();
        values["APPLE_MUSIC_TOKEN_LIFETIME_MINUTES"] = invalid;
        AssertThrows<InvalidOperationException>(() =>
            AppleMusicTokenOptions.Load(Configuration(values)));
    }

    return Task.CompletedTask;
}

static Task InvalidKeyIsRejected()
{
    using var fixture = KeyFixture.Create("to nie jest klucz");
    AssertThrows<InvalidOperationException>(() =>
        AppleMusicTokenOptions.Load(Configuration(fixture.Configuration())));
    return Task.CompletedTask;
}

static Task TokenIsSignedAndScoped()
{
    var moment = new DateTimeOffset(2026, 10, 25, 16, 0, 0, TimeSpan.Zero);
    using var fixture = KeyFixture.Create();
    var options = AppleMusicTokenOptions.Load(
        Configuration(fixture.Configuration())).Options!;
    using var issuer = options.CreateIssuer(new FixedTimeProvider(moment));
    var issued = issuer.Issue(KeyFixture.AllowedOrigin);
    var parts = issued.Value.Split('.');
    Assert(parts.Length == 3, "JWT nie ma trzech części");

    using var header = JsonDocument.Parse(Base64UrlDecode(parts[0]));
    using var payload = JsonDocument.Parse(Base64UrlDecode(parts[1]));
    Assert(header.RootElement.GetProperty("alg").GetString() == "ES256", "zły algorytm");
    Assert(header.RootElement.GetProperty("kid").GetString() == KeyFixture.KeyId, "zły kid");
    Assert(payload.RootElement.GetProperty("iss").GetString() == KeyFixture.TeamId, "zły issuer");
    Assert(payload.RootElement.GetProperty("iat").GetInt64() == moment.ToUnixTimeSeconds(), "zły iat");
    Assert(payload.RootElement.GetProperty("exp").GetInt64()
        == moment.AddHours(1).ToUnixTimeSeconds(), "zły exp");
    Assert(payload.RootElement.GetProperty("origin")[0].GetString()
        == KeyFixture.AllowedOrigin, "token nie jest ograniczony do originu");
    Assert(issued.ExpiresAt == moment.AddHours(1), "odpowiedź ma inny termin niż JWT");

    var signature = Base64UrlDecode(parts[2]);
    var valid = fixture.Key.VerifyData(
        Encoding.ASCII.GetBytes(parts[0] + "." + parts[1]),
        signature,
        HashAlgorithmName.SHA256,
        DSASignatureFormat.IeeeP1363FixedFieldConcatenation);
    Assert(valid, "podpisu nie da się potwierdzić kluczem publicznym");
    Assert(!issued.Value.Contains("PRIVATE", StringComparison.Ordinal), "JWT zawiera tekst klucza");
    return Task.CompletedTask;
}

static async Task EndpointRequiresAllowedOrigin()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartDevelopment(fixture);

    using var missing = await running.Client.PostAsync("/v1/developer-token", null);
    Assert(missing.StatusCode == HttpStatusCode.BadRequest, "brak originu nie został odrzucony");
    Assert(await ErrorCode(missing) == "missing_or_invalid_origin", "zły kod braku originu");

    using var deniedRequest = new HttpRequestMessage(HttpMethod.Post, "/v1/developer-token");
    deniedRequest.Headers.TryAddWithoutValidation("Origin", "https://attacker.example");
    using var denied = await running.Client.SendAsync(deniedRequest);
    Assert(denied.StatusCode == HttpStatusCode.Forbidden, "obcy origin nie został odrzucony");

    using var bodyRequest = TokenRequest();
    bodyRequest.Content = JsonContent.Create(new { unexpected = true });
    using var body = await running.Client.SendAsync(bodyRequest);
    Assert(body.StatusCode == HttpStatusCode.BadRequest, "ciało żądania zostało przyjęte");

    using var accepted = await running.Client.SendAsync(TokenRequest());
    Assert(accepted.StatusCode == HttpStatusCode.OK, "dozwolony origin nie dostał tokenu");
    Assert(accepted.Headers.TryGetValues("Access-Control-Allow-Origin", out var cors)
        && cors.Single() == KeyFixture.AllowedOrigin, "brak wąskiego CORS");
    using var response = JsonDocument.Parse(await accepted.Content.ReadAsByteArrayAsync());
    var token = response.RootElement.GetProperty("developer_token").GetString();
    var expires = response.RootElement.GetProperty("expires_at").GetString();
    Assert(!string.IsNullOrWhiteSpace(token) && !string.IsNullOrWhiteSpace(expires),
        "odpowiedź nie zawiera tokenu i terminu");
}

static async Task CorsPreflightIsNarrow()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartDevelopment(fixture);
    using var request = new HttpRequestMessage(HttpMethod.Options, "/v1/developer-token");
    request.Headers.TryAddWithoutValidation("Origin", KeyFixture.AllowedOrigin);
    request.Headers.TryAddWithoutValidation("Access-Control-Request-Method", "POST");
    using var response = await running.Client.SendAsync(request);
    Assert(response.StatusCode == HttpStatusCode.NoContent, "preflight nie zwrócił 204");
    Assert(response.Headers.TryGetValues("Access-Control-Allow-Origin", out var origins)
        && origins.Single() == KeyFixture.AllowedOrigin, "preflight ma zły origin");
    Assert(response.Headers.TryGetValues("Access-Control-Allow-Methods", out var methods)
        && methods.Any(value => value.Contains("POST", StringComparison.Ordinal)),
        "preflight nie dopuszcza POST");
}

static async Task UntrustedProxyCannotClaimHttps()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartProduction(fixture, trustedProxy: false);
    using var request = new HttpRequestMessage(HttpMethod.Get, "/health/ready");
    request.Headers.TryAddWithoutValidation("X-Forwarded-For", "198.51.100.10");
    request.Headers.TryAddWithoutValidation("X-Forwarded-Proto", "https");
    using var response = await running.Client.SendAsync(request);
    Assert(response.StatusCode == HttpStatusCode.BadRequest, "obce proxy ominęło HTTPS");
    Assert(await ErrorCode(response) == "https_required", "odmowa HTTPS ma zły kod");
}

static async Task TrustedProxyCanTerminateTls()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartProduction(fixture, trustedProxy: true);
    using var request = new HttpRequestMessage(HttpMethod.Get, "/health/ready");
    request.Headers.TryAddWithoutValidation("X-Forwarded-For", "198.51.100.10");
    request.Headers.TryAddWithoutValidation("X-Forwarded-Proto", "https");
    using var response = await running.Client.SendAsync(request);
    Assert(response.StatusCode == HttpStatusCode.OK, "zaufane proxy nie przekazało HTTPS");
}

static async Task RateLimitUsesForwardedClientAddress()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartProduction(fixture, trustedProxy: true);
    for (var attempt = 0; attempt < 30; attempt++)
    {
        using var response = await running.Client.SendAsync(
            TokenRequest("198.51.100.10", forwardedHttps: true));
        Assert(response.StatusCode == HttpStatusCode.OK, "klient przed limitem nie dostał tokenu");
    }

    using var limited = await running.Client.SendAsync(
        TokenRequest("198.51.100.10", forwardedHttps: true));
    Assert(limited.StatusCode == HttpStatusCode.TooManyRequests, "brak limitu 30 na minutę");

    using var other = await running.Client.SendAsync(
        TokenRequest("198.51.100.11", forwardedHttps: true));
    Assert(other.StatusCode == HttpStatusCode.OK, "limit przeszedł na innego klienta");
}

static async Task HealthDoesNotExposeIdentifiers()
{
    using var fixture = KeyFixture.Create();
    await using var running = await RunningBroker.StartDevelopment(fixture);
    using var response = await running.Client.GetAsync("/health/ready");
    var body = await response.Content.ReadAsStringAsync();
    Assert(response.StatusCode == HttpStatusCode.OK, "gotowa usługa nie zwróciła 200");
    Assert(!body.Contains(KeyFixture.TeamId, StringComparison.Ordinal)
        && !body.Contains(KeyFixture.KeyId, StringComparison.Ordinal)
        && !body.Contains(KeyFixture.AllowedOrigin, StringComparison.Ordinal),
        "stan ujawnia konfigurację integracji");
}

static HttpRequestMessage TokenRequest(
    string? forwardedFor = null,
    bool forwardedHttps = false)
{
    var request = new HttpRequestMessage(HttpMethod.Post, "/v1/developer-token");
    request.Headers.TryAddWithoutValidation("Origin", KeyFixture.AllowedOrigin);
    if (forwardedFor is not null)
    {
        request.Headers.TryAddWithoutValidation("X-Forwarded-For", forwardedFor);
    }
    if (forwardedHttps)
    {
        request.Headers.TryAddWithoutValidation("X-Forwarded-Proto", "https");
    }
    return request;
}

static IConfiguration Configuration(Dictionary<string, string?> values) =>
    new ConfigurationBuilder().AddInMemoryCollection(values).Build();

static byte[] Base64UrlDecode(string value)
{
    var padded = value.Replace('-', '+').Replace('_', '/');
    padded += new string('=', (4 - padded.Length % 4) % 4);
    return Convert.FromBase64String(padded);
}

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

internal sealed class FixedTimeProvider(DateTimeOffset value) : TimeProvider
{
    public override DateTimeOffset GetUtcNow() => value;
}

internal sealed class KeyFixture : IDisposable
{
    internal const string TeamId = "TEAM123456";
    internal const string KeyId = "KEY1234567";
    internal const string AllowedOrigin = "https://applemusic.example.test";

    private KeyFixture(ECDsa key, string directory, string path)
    {
        Key = key;
        Directory = directory;
        Path = path;
    }

    internal ECDsa Key { get; }

    private string Directory { get; }

    private string Path { get; }

    internal static KeyFixture Create(string? content = null)
    {
        var directory = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            "amc-apple-music-token-tests-" + Guid.NewGuid().ToString("N"));
        System.IO.Directory.CreateDirectory(directory);
        var path = System.IO.Path.Combine(directory, "AuthKey_TEST.p8");
        var key = ECDsa.Create(ECCurve.NamedCurves.nistP256);
        File.WriteAllText(path, content ?? key.ExportPkcs8PrivateKeyPem());
        return new KeyFixture(key, directory, path);
    }

    internal Dictionary<string, string?> Configuration(bool trustedProxy = false) => new()
    {
        ["APPLE_MUSIC_TEAM_ID"] = TeamId,
        ["APPLE_MUSIC_KEY_ID"] = KeyId,
        ["APPLE_MUSIC_PRIVATE_KEY_FILE"] = Path,
        ["APPLE_MUSIC_ALLOWED_ORIGINS"] = AllowedOrigin,
        ["APPLE_MUSIC_TRUSTED_PROXIES"] = trustedProxy ? "127.0.0.1" : null
    };

    public void Dispose()
    {
        Key.Dispose();
        if (System.IO.Directory.Exists(Directory))
        {
            System.IO.Directory.Delete(Directory, recursive: true);
        }
    }
}

internal sealed class RunningBroker : IAsyncDisposable
{
    private readonly WebApplication _application;

    private RunningBroker(WebApplication application, HttpClient client)
    {
        _application = application;
        Client = client;
    }

    internal HttpClient Client { get; }

    internal static Task<RunningBroker> StartDevelopment(KeyFixture fixture) =>
        Start(fixture, "Development", trustedProxy: false);

    internal static Task<RunningBroker> StartProduction(
        KeyFixture fixture,
        bool trustedProxy) => Start(fixture, "Production", trustedProxy);

    private static async Task<RunningBroker> Start(
        KeyFixture fixture,
        string environment,
        bool trustedProxy)
    {
        var args = new List<string>
        {
            "--environment", environment,
            "--Logging:LogLevel:Default", "Warning"
        };
        foreach (var pair in fixture.Configuration(trustedProxy))
        {
            if (pair.Value is not null)
            {
                args.Add("--" + pair.Key);
                args.Add(pair.Value);
            }
        }

        var application = AppleMusicTokenBrokerApplication.Build(args.ToArray());
        application.Urls.Add("http://127.0.0.1:0");
        await application.StartAsync();
        var address = application.Services.GetRequiredService<IServer>()
            .Features.Get<IServerAddressesFeature>()!.Addresses.Single();
        return new RunningBroker(
            application,
            new HttpClient { BaseAddress = new Uri(address) });
    }

    public async ValueTask DisposeAsync()
    {
        Client.Dispose();
        await _application.StopAsync();
        await _application.DisposeAsync();
    }
}
