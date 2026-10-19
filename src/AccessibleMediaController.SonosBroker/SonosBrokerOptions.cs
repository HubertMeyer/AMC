namespace AccessibleMediaController.SonosBroker;

internal sealed record SonosBrokerOptions(
    Uri PublicOrigin,
    string ClientId,
    string ClientSecret,
    Uri RedirectUri,
    TimeSpan SessionLifetime,
    int MaximumSessions)
{
    internal const string Scope = "playback-control-all";
    internal const string CallbackPath = "/login/callback";

    internal static SonosBrokerConfiguration Load(IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(configuration);

        var originText = configuration["SONOS_BROKER_PUBLIC_ORIGIN"];
        var clientId = configuration["SONOS_CLIENT_ID"];
        var clientSecret = configuration["SONOS_CLIENT_SECRET"];
        var redirectText = configuration["SONOS_REDIRECT_URI"];

        var supplied = new[] { originText, clientId, clientSecret, redirectText }
            .Count(value => !string.IsNullOrWhiteSpace(value));
        if (supplied == 0)
        {
            return SonosBrokerConfiguration.Unconfigured;
        }

        if (supplied != 4
            || !TryHttpsOrigin(originText, out var origin)
            || !string.Equals(origin!.AbsolutePath, "/", StringComparison.Ordinal)
            || !TryHttpsUri(redirectText, out var redirect)
            || !string.Equals(redirect!.AbsolutePath, CallbackPath, StringComparison.Ordinal)
            || !string.IsNullOrEmpty(redirect.Query)
            || !string.IsNullOrEmpty(redirect.Fragment)
            || !SameOrigin(origin, redirect)
            || string.IsNullOrWhiteSpace(clientId)
            || string.IsNullOrWhiteSpace(clientSecret)
            || clientId.Length > 512
            || clientSecret.Length > 2048)
        {
            throw new InvalidOperationException(
                "Konfiguracja brokera Sonos jest niepełna albo nieprawidłowa.");
        }

        var expectedRedirect = new Uri(origin!, CallbackPath.TrimStart('/'));
        if (!string.Equals(expectedRedirect.AbsoluteUri, redirect.AbsoluteUri, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Adres powrotu Sonos musi wskazywać dokładnie publiczny adres brokera.");
        }

        return new SonosBrokerConfiguration(new SonosBrokerOptions(
            origin!,
            clientId,
            clientSecret,
            redirect,
            TimeSpan.FromMinutes(10),
            1024));
    }

    private static bool TryHttpsOrigin(string? value, out Uri? uri)
    {
        uri = null;
        if (!TryHttpsUri(value, out var parsed)
            || !string.IsNullOrEmpty(parsed!.Query)
            || !string.IsNullOrEmpty(parsed.Fragment))
        {
            return false;
        }

        var path = parsed.AbsolutePath.EndsWith('/')
            ? parsed.AbsolutePath
            : parsed.AbsolutePath + "/";
        uri = new UriBuilder(parsed) { Path = path }.Uri;
        return true;
    }

    private static bool TryHttpsUri(string? value, out Uri? uri)
    {
        uri = null;
        if (string.IsNullOrWhiteSpace(value)
            || !Uri.TryCreate(value.Trim(), UriKind.Absolute, out var parsed)
            || !string.Equals(parsed.Scheme, Uri.UriSchemeHttps, StringComparison.Ordinal)
            || string.IsNullOrEmpty(parsed.Host)
            || !string.IsNullOrEmpty(parsed.UserInfo))
        {
            return false;
        }

        uri = parsed;
        return true;
    }

    private static bool SameOrigin(Uri left, Uri right) =>
        string.Equals(left.Scheme, right.Scheme, StringComparison.Ordinal)
        && string.Equals(left.Host, right.Host, StringComparison.OrdinalIgnoreCase)
        && left.Port == right.Port;
}

internal sealed record SonosBrokerConfiguration(SonosBrokerOptions? Options)
{
    internal static SonosBrokerConfiguration Unconfigured { get; } =
        new((SonosBrokerOptions?)null);

    internal bool IsConfigured => Options is not null;
}
