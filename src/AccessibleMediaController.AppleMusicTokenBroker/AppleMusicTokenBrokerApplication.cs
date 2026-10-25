using System.Globalization;
using System.Net;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.RateLimiting;

namespace AccessibleMediaController.AppleMusicTokenBroker;

internal static class AppleMusicTokenBrokerApplication
{
    internal static WebApplication Build(string[] args)
    {
        var builder = WebApplication.CreateSlimBuilder(args);
        builder.WebHost.ConfigureKestrel(options => options.Limits.MaxRequestBodySize = 1024);

        var configuration = AppleMusicTokenOptions.Load(builder.Configuration);
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
        if (configuration.Options is { } tokenOptions)
        {
            builder.Services.AddSingleton(serviceProvider =>
                tokenOptions.CreateIssuer(serviceProvider.GetRequiredService<TimeProvider>()));
            builder.Services.AddCors(options => options.AddPolicy(
                "apple-music-player",
                policy => policy
                    .WithOrigins(tokenOptions.AllowedOrigins.ToArray())
                    .WithMethods("POST", "OPTIONS")
                    .AllowAnyHeader()));
        }
        else
        {
            builder.Services.AddCors(options => options.AddPolicy(
                "apple-music-player",
                policy => policy.WithOrigins("https://not-configured.invalid")));
        }

        builder.Services.AddRateLimiter(options =>
        {
            options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
            options.OnRejected = static async (context, cancellationToken) =>
                await context.HttpContext.Response.WriteAsJsonAsync(
                    new ErrorResponse("too_many_requests"), cancellationToken);
            options.AddPolicy("developer-token", context =>
            {
                var key = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
                return RateLimitPartition.GetFixedWindowLimiter(
                    key,
                    _ => new FixedWindowRateLimiterOptions
                    {
                        AutoReplenishment = true,
                        PermitLimit = 30,
                        QueueLimit = 0,
                        Window = TimeSpan.FromMinutes(1)
                    });
            });
        });

        var app = builder.Build();
        if (configuration.TrustedProxies.Count > 0)
        {
            app.UseForwardedHeaders();
        }

        app.Use(async (context, next) =>
        {
            context.Response.Headers["Cache-Control"] = "no-store";
            context.Response.Headers["Pragma"] = "no-cache";
            context.Response.Headers["X-Content-Type-Options"] = "nosniff";
            context.Response.Headers["X-Frame-Options"] = "DENY";
            context.Response.Headers["Referrer-Policy"] = "no-referrer";
            context.Response.Headers.Append("Vary", "Origin");
            if (!context.Request.IsHttps && !app.Environment.IsDevelopment())
            {
                context.Response.StatusCode = StatusCodes.Status400BadRequest;
                await context.Response.WriteAsJsonAsync(new ErrorResponse("https_required"));
                return;
            }

            await next(context);
        });
        app.UseCors("apple-music-player");
        app.UseRateLimiter();

        app.MapGet("/health/live", () => Results.Json(new { status = "ok" }));
        app.MapGet("/health/ready", (AppleMusicTokenBrokerConfiguration state) =>
            Results.Json(
                new
                {
                    status = state.IsConfigured ? "ready" : "not_configured",
                    apple_music_configured = state.IsConfigured
                },
                statusCode: state.IsConfigured
                    ? StatusCodes.Status200OK
                    : StatusCodes.Status503ServiceUnavailable));
        app.MapPost("/v1/developer-token", IssueToken)
            .RequireRateLimiting("developer-token");

        if (!configuration.IsConfigured)
        {
            app.Logger.LogWarning(
                "Usługa tokenów Apple Music działa bez konfiguracji; wydawanie tokenów pozostaje wyłączone.");
        }

        return app;
    }

    private static IResult IssueToken(
        HttpRequest request,
        AppleMusicTokenBrokerConfiguration configuration,
        IServiceProvider services)
    {
        if (configuration.Options is not { } options)
        {
            return Error(StatusCodes.Status503ServiceUnavailable, "server_not_configured");
        }

        if (request.ContentLength is > 0
            || request.Headers.TransferEncoding.Count > 0
            || !string.IsNullOrWhiteSpace(request.ContentType))
        {
            return Error(StatusCodes.Status400BadRequest, "invalid_body");
        }

        var origins = request.Headers.Origin;
        if (origins.Count != 1
            || !AppleMusicTokenOptions.TryNormalizeOrigin(origins[0], out var origin))
        {
            return Error(StatusCodes.Status400BadRequest, "missing_or_invalid_origin");
        }

        if (!options.IsAllowedOrigin(origin!))
        {
            return Error(StatusCodes.Status403Forbidden, "origin_not_allowed");
        }

        var issuer = services.GetRequiredService<AppleMusicDeveloperTokenIssuer>();
        var issued = issuer.Issue(origin!);
        return Results.Json(new DeveloperTokenResponse(
            issued.Value,
            issued.ExpiresAt.ToString("O", CultureInfo.InvariantCulture)));
    }

    private static IResult Error(int status, string code) =>
        Results.Json(new ErrorResponse(code), statusCode: status);
}
