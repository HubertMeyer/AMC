using System.Net;
using System.Text;
using System.Text.Encodings.Web;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.RateLimiting;

namespace AccessibleMediaController.SonosBroker;

internal static class SonosBrokerApplication
{
    internal static WebApplication Build(string[] args)
    {
        var builder = WebApplication.CreateSlimBuilder(args);
        builder.WebHost.ConfigureKestrel(options => options.Limits.MaxRequestBodySize = 4096);
        // Standardowy log żądania ASP.NET zawiera cały query string. Callback
        // Sonosa niesie w nim krótkotrwały kod autoryzacyjny i state, dlatego
        // nie wolno emitować tych wpisów nawet przy zwykłym poziomie Info.
        builder.Logging.AddFilter("Microsoft.AspNetCore.Hosting.Diagnostics", LogLevel.None);
        // Klient OAuth wysyła kod, refresh token i nagłówek Basic w żądaniu POST.
        // Nawet po globalnym włączeniu Debug/Trace nie emitujemy diagnostyki
        // żądań HttpClient dla tego nazwanego klienta.
        builder.Logging.AddFilter("System.Net.Http.HttpClient.sonos-oauth", LogLevel.Warning);

        var configuration = SonosBrokerOptions.Load(builder.Configuration);
        var sessionOptions = configuration.Options;
        if (configuration.TrustedProxies.Count > 0)
        {
            builder.Services.Configure<ForwardedHeadersOptions>(options =>
            {
                options.ForwardedHeaders =
                    ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto;
                options.ForwardLimit = 1;
                options.RequireHeaderSymmetry = true;
                options.KnownNetworks.Clear();
                options.KnownProxies.Clear();
                foreach (var address in configuration.TrustedProxies)
                {
                    options.KnownProxies.Add(address);
                }
            });
        }

        builder.Services.AddSingleton(configuration);
        builder.Services.AddSingleton(TimeProvider.System);
        builder.Services.AddSingleton(new SonosLoginSessionStore(
            sessionOptions?.MaximumSessions ?? 1024));
        builder.Services.AddHostedService<ExpiredSessionCleanupService>();
        builder.Services.AddHttpClient("sonos-oauth", client =>
        {
            client.Timeout = TimeSpan.FromSeconds(20);
            client.MaxResponseContentBufferSize = SonosOAuthGateway.MaximumResponseBytes + 1;
        }).ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler
        {
            AllowAutoRedirect = false,
            UseCookies = false
        });
        builder.Services.AddRateLimiter(options =>
        {
            options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
            options.OnRejected = static async (context, cancellationToken) =>
                await context.HttpContext.Response.WriteAsJsonAsync(
                    new ErrorResponse("too_many_sessions"), cancellationToken);
            options.AddPolicy("login-start", context => FixedWindow(
                context, permitLimit: 10, TimeSpan.FromMinutes(1)));
            options.AddPolicy("login-result", context => FixedWindow(
                context, permitLimit: 30, TimeSpan.FromMinutes(1)));
            options.AddPolicy("login-refresh", context => FixedWindow(
                context, permitLimit: 12, TimeSpan.FromMinutes(1)));
        });

        var app = builder.Build();
        if (configuration.TrustedProxies.Count > 0)
        {
            // Nagłówki są honorowane tylko od jawnie wskazanych adresów proxy.
            // Middleware musi poprzedzać kontrolę HTTPS i limiter po adresie klienta.
            app.UseForwardedHeaders();
        }

        app.Use(async (context, next) =>
        {
            context.Response.Headers["Cache-Control"] = "no-store";
            context.Response.Headers["Pragma"] = "no-cache";
            context.Response.Headers["X-Content-Type-Options"] = "nosniff";
            context.Response.Headers["X-Frame-Options"] = "DENY";
            context.Response.Headers["Referrer-Policy"] = "no-referrer";
            if (!context.Request.IsHttps && !app.Environment.IsDevelopment())
            {
                context.Response.StatusCode = StatusCodes.Status400BadRequest;
                await context.Response.WriteAsJsonAsync(new ErrorResponse("https_required"));
                return;
            }

            await next(context);
        });
        app.UseRateLimiter();

        app.MapGet("/health", (SonosBrokerConfiguration state) =>
            Results.Json(new
            {
                status = "ok",
                sonos_configured = state.IsConfigured
            }));
        app.MapGet("/health/live", () => Results.Json(new { status = "ok" }));
        app.MapGet("/health/ready", (SonosBrokerConfiguration state) =>
            Results.Json(
                new
                {
                    status = state.IsConfigured ? "ready" : "not_configured",
                    sonos_configured = state.IsConfigured
                },
                statusCode: state.IsConfigured
                    ? StatusCodes.Status200OK
                    : StatusCodes.Status503ServiceUnavailable));

        app.MapPost("/login/start", StartAsync).RequireRateLimiting("login-start");
        app.MapGet(SonosBrokerOptions.CallbackPath, CallbackAsync);
        app.MapPost("/login/result", ResultAsync).RequireRateLimiting("login-result");
        app.MapPost("/login/refresh", RefreshAsync).RequireRateLimiting("login-refresh");

        if (!configuration.IsConfigured)
        {
            app.Logger.LogWarning(
                "Broker Sonos działa bez konfiguracji dostępu; logowanie pozostaje wyłączone.");
        }

        return app;
    }

    private static RateLimitPartition<string> FixedWindow(
        HttpContext context,
        int permitLimit,
        TimeSpan window)
    {
        var key = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
        return RateLimitPartition.GetFixedWindowLimiter(key, _ => new FixedWindowRateLimiterOptions
        {
            AutoReplenishment = true,
            PermitLimit = permitLimit,
            QueueLimit = 0,
            Window = window
        });
    }

    private static async Task<IResult> StartAsync(
        HttpRequest request,
        SonosBrokerConfiguration configuration,
        SonosLoginSessionStore sessions,
        IHttpClientFactory clients,
        CancellationToken cancellationToken)
    {
        if (configuration.Options is not { } options)
        {
            return Error(StatusCodes.Status503ServiceUnavailable, "server_not_configured");
        }

        var body = await ReadBodyAsync<StartRequest>(request, cancellationToken);
        if (body is null)
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_body");
        }

        if (!string.Equals(body.CodeChallengeMethod, "S256", StringComparison.Ordinal))
        {
            return Error(StatusCodes.Status400BadRequest, "unsupported_challenge_method");
        }

        if (!SonosLoginSessionStore.IsPkceValue(body.CodeChallenge))
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_code_challenge");
        }

        var created = sessions.Create(
            body.CodeChallenge!, DateTimeOffset.UtcNow, options.SessionLifetime);
        if (created.Status != SessionCreateStatus.Success)
        {
            return Error(StatusCodes.Status429TooManyRequests, "too_many_sessions");
        }

        var gateway = new SonosOAuthGateway(options, clients.CreateClient("sonos-oauth"));
        var authorizeUri = gateway.CreateAuthorizeUri(created.State!);
        return Results.Json(new StartResponse(
            created.SessionId!,
            authorizeUri.AbsoluteUri,
            checked((int)options.SessionLifetime.TotalSeconds)));
    }

    private static async Task<IResult> CallbackAsync(
        HttpRequest request,
        SonosBrokerConfiguration configuration,
        SonosLoginSessionStore sessions,
        IHttpClientFactory clients,
        CancellationToken cancellationToken)
    {
        if (configuration.Options is not { } options)
        {
            return CallbackPage(
                "Logowanie Sonos jest obecnie niedostępne.",
                StatusCodes.Status503ServiceUnavailable);
        }

        var state = request.Query["state"].ToString();
        var error = request.Query["error"].ToString();
        var code = request.Query["code"].ToString();
        if (!SonosLoginSessionStore.IsPkceValue(state))
        {
            return CallbackPage(
                "Nie można dopasować tej odpowiedzi do rozpoczętego logowania.",
                StatusCodes.Status400BadRequest);
        }

        var began = sessions.BeginCallback(state, DateTimeOffset.UtcNow);
        if (began != CallbackBeginStatus.Started)
        {
            return CallbackPage(
                "Ta próba logowania wygasła albo została już zakończona.",
                StatusCodes.Status400BadRequest);
        }

        SessionReadStatus resultStatus;
        TokenResponse? tokens = null;
        if (!string.IsNullOrEmpty(error))
        {
            resultStatus = string.Equals(error, "access_denied", StringComparison.Ordinal)
                ? SessionReadStatus.Denied
                : SessionReadStatus.InvalidCallback;
        }
        else if (string.IsNullOrEmpty(code) || code.Length > 4096)
        {
            resultStatus = SessionReadStatus.InvalidCallback;
        }
        else
        {
            var gateway = new SonosOAuthGateway(options, clients.CreateClient("sonos-oauth"));
            var exchange = await gateway.ExchangeCodeAsync(code, cancellationToken);
            resultStatus = exchange.Status == OAuthStatus.Success
                ? SessionReadStatus.Success
                : SessionReadStatus.TokenExchangeFailed;
            tokens = exchange.Tokens;
        }

        var stored = sessions.StoreCallback(
            state, resultStatus, tokens, DateTimeOffset.UtcNow);
        return stored == CallbackStoreStatus.Stored
            ? CallbackPage(
                resultStatus == SessionReadStatus.Success
                    ? "Logowanie Sonos zakończone. Wróć do AMC i wybierz sprawdzenie wyniku."
                    : "Logowanie Sonos nie zostało zakończone. Wróć do AMC, aby zobaczyć wynik.",
                StatusCodes.Status200OK)
            : CallbackPage(
                "Ta próba logowania wygasła albo została już zakończona.",
                StatusCodes.Status400BadRequest);
    }

    private static async Task<IResult> ResultAsync(
        HttpRequest request,
        SonosBrokerConfiguration configuration,
        SonosLoginSessionStore sessions,
        CancellationToken cancellationToken)
    {
        if (!configuration.IsConfigured)
        {
            return Error(StatusCodes.Status503ServiceUnavailable, "server_not_configured");
        }

        var body = await ReadBodyAsync<ResultRequest>(request, cancellationToken);
        if (body is null)
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_body");
        }

        if (!SonosLoginSessionStore.IsPkceValue(body.CodeVerifier))
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_code_verifier");
        }

        var result = sessions.ReadOnce(
            body.SessionId, body.CodeVerifier, DateTimeOffset.UtcNow);
        return result.Status switch
        {
            SessionReadStatus.Success when result.Tokens is not null => Results.Json(result.Tokens),
            SessionReadStatus.ProofMismatch => Error(StatusCodes.Status403Forbidden, "verifier_mismatch"),
            SessionReadStatus.Denied => Error(StatusCodes.Status400BadRequest, "access_denied"),
            SessionReadStatus.InvalidCallback => Error(StatusCodes.Status400BadRequest, "invalid_callback"),
            SessionReadStatus.TokenExchangeFailed => Error(StatusCodes.Status400BadRequest, "token_exchange_failed"),
            _ => Error(StatusCodes.Status404NotFound, "unknown_session")
        };
    }

    private static async Task<IResult> RefreshAsync(
        HttpRequest request,
        SonosBrokerConfiguration configuration,
        IHttpClientFactory clients,
        CancellationToken cancellationToken)
    {
        if (configuration.Options is not { } options)
        {
            return Error(StatusCodes.Status503ServiceUnavailable, "server_not_configured");
        }

        var body = await ReadBodyAsync<RefreshRequest>(request, cancellationToken);
        if (body is null)
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_body");
        }

        if (!IsRefreshTokenAcceptable(body.RefreshToken))
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_refresh_token");
        }

        var gateway = new SonosOAuthGateway(options, clients.CreateClient("sonos-oauth"));
        var result = await gateway.RefreshAsync(body.RefreshToken!, cancellationToken);
        return result.Status switch
        {
            OAuthStatus.Success when result.Tokens is not null => Results.Json(result.Tokens),
            OAuthStatus.ReauthorizationRequired =>
                Error(StatusCodes.Status401Unauthorized, "reauthorization_required"),
            OAuthStatus.RateLimited =>
                Error(StatusCodes.Status429TooManyRequests, "refresh_rate_limited"),
            OAuthStatus.TemporaryFailure =>
                Error(StatusCodes.Status503ServiceUnavailable, "refresh_unavailable"),
            _ => Error(StatusCodes.Status502BadGateway, "provider_bad_payload")
        };
    }

    private static bool IsRefreshTokenAcceptable(string? value)
    {
        if (string.IsNullOrEmpty(value))
        {
            return false;
        }

        if (value.Any(character => character < 0x20
            || character == 0x7f
            || character is >= '\u0080' and <= '\u009f'))
        {
            return false;
        }

        try
        {
            return new UTF8Encoding(false, true).GetByteCount(value) <= 2048;
        }
        catch (EncoderFallbackException)
        {
            return false;
        }
    }

    private static async Task<T?> ReadBodyAsync<T>(
        HttpRequest request,
        CancellationToken cancellationToken)
        where T : class
    {
        try
        {
            return await request.ReadFromJsonAsync<T>(cancellationToken);
        }
        catch (BadHttpRequestException)
        {
            return null;
        }
        catch (System.Text.Json.JsonException)
        {
            return null;
        }
    }

    private static IResult Error(int statusCode, string code) =>
        Results.Json(new ErrorResponse(code), statusCode: statusCode);

    private static IResult CallbackPage(string message, int statusCode)
    {
        var safe = HtmlEncoder.Default.Encode(message);
        var html = "<!doctype html><html lang=\"pl\"><head><meta charset=\"utf-8\">"
            + "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            + "<title>Logowanie Sonos</title></head><body><main><h1>Logowanie Sonos</h1><p>"
            + safe
            + "</p></main></body></html>";
        return Results.Content(html, "text/html; charset=utf-8", Encoding.UTF8, statusCode);
    }
}

internal sealed class ExpiredSessionCleanupService(
    SonosLoginSessionStore sessions,
    TimeProvider timeProvider) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromMinutes(1), timeProvider);
        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            sessions.RemoveExpired(timeProvider.GetUtcNow());
        }
    }
}
