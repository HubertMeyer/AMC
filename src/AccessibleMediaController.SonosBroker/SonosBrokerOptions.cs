using System.Net;

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

        var trustedProxies = LoadTrustedProxies(configuration["SONOS_TRUSTED_PROXIES"]);
        var originText = configuration["SONOS_BROKER_PUBLIC_ORIGIN"];
        var clientId = configuration["SONOS_CLIENT_ID"];
        var clientSecret = LoadClientSecret(configuration);
        var redirectText = configuration["SONOS_REDIRECT_URI"];

        var supplied = new[] { originText, clientId, clientSecret, redirectText }
            .Count(value => !string.IsNullOrWhiteSpace(value));
        if (supplied == 0)
        {
            return new SonosBrokerConfiguration(null, trustedProxies);
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

        return new SonosBrokerConfiguration(
            new SonosBrokerOptions(
                origin!,
                clientId,
                clientSecret,
                redirect,
                TimeSpan.FromMinutes(10),
                1024),
            trustedProxies);
    }

    private static string? LoadClientSecret(IConfiguration configuration)
    {
        var direct = configuration["SONOS_CLIENT_SECRET"];
        var filePath = configuration["SONOS_CLIENT_SECRET_FILE"];
        var hasDirect = !string.IsNullOrWhiteSpace(direct);
        var hasFile = !string.IsNullOrWhiteSpace(filePath);

        if (hasDirect && hasFile)
        {
            throw new InvalidOperationException(
                "Sekret Sonosa może pochodzić tylko z jednego źródła wdrożeniowego.");
        }

        if (!hasFile)
        {
            return direct;
        }

        if (!Path.IsPathFullyQualified(filePath!))
        {
            throw new InvalidOperationException(
                "Plik sekretu Sonosa musi mieć bezwzględną ścieżkę.");
        }

        try
        {
            var file = new FileInfo(filePath!);
            if (!file.Exists || file.Length is <= 0 or > 4096)
            {
                throw new InvalidOperationException(
                    "Plik sekretu Sonosa nie istnieje albo ma nieprawidłowy rozmiar.");
            }

            var value = File.ReadAllText(file.FullName).TrimEnd('\r', '\n');
            if (string.IsNullOrWhiteSpace(value)
                || value.Length > 2048
                || value.Any(character => character is '\r' or '\n' or '\0'))
            {
                throw new InvalidOperationException(
                    "Plik sekretu Sonosa ma nieprawidłową zawartość.");
            }

            return value;
        }
        catch (InvalidOperationException)
        {
            throw;
        }
        catch (Exception error) when (error is IOException
            or UnauthorizedAccessException
            or System.Security.SecurityException)
        {
            throw new InvalidOperationException(
                "Nie można bezpiecznie odczytać pliku sekretu Sonosa.");
        }
    }

    private static IReadOnlyList<IPAddress> LoadTrustedProxies(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return Array.Empty<IPAddress>();
        }

        var entries = value.Split(',', StringSplitOptions.TrimEntries);
        if (entries.Length > 16
            || entries.Any(string.IsNullOrWhiteSpace))
        {
            throw new InvalidOperationException(
                "Lista zaufanych reverse proxy Sonos jest nieprawidłowa.");
        }

        var addresses = new List<IPAddress>(entries.Length);
        foreach (var entry in entries)
        {
            if (!IPAddress.TryParse(entry, out var address)
                || address.Equals(IPAddress.Any)
                || address.Equals(IPAddress.IPv6Any)
                || address.Equals(IPAddress.None)
                || address.Equals(IPAddress.IPv6None))
            {
                throw new InvalidOperationException(
                    "Lista zaufanych reverse proxy Sonos jest nieprawidłowa.");
            }

            if (!addresses.Contains(address))
            {
                addresses.Add(address);
            }
        }

        return addresses.AsReadOnly();
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

internal sealed record SonosBrokerConfiguration(
    SonosBrokerOptions? Options,
    IReadOnlyList<IPAddress> TrustedProxies)
{
    internal static SonosBrokerConfiguration Unconfigured { get; } =
        new(null, Array.Empty<IPAddress>());

    internal bool IsConfigured => Options is not null;
}
