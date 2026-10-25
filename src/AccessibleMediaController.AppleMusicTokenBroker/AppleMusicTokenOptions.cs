using System.Globalization;
using System.Net;
using System.Security.Cryptography;

namespace AccessibleMediaController.AppleMusicTokenBroker;

internal sealed class AppleMusicTokenOptions
{
    private readonly string _privateKeyPem;

    private AppleMusicTokenOptions(
        string teamId,
        string keyId,
        string privateKeyPem,
        IReadOnlyList<string> allowedOrigins,
        TimeSpan tokenLifetime)
    {
        TeamId = teamId;
        KeyId = keyId;
        _privateKeyPem = privateKeyPem;
        AllowedOrigins = allowedOrigins;
        TokenLifetime = tokenLifetime;
    }

    internal string TeamId { get; }

    internal string KeyId { get; }

    internal IReadOnlyList<string> AllowedOrigins { get; }

    internal TimeSpan TokenLifetime { get; }

    internal AppleMusicDeveloperTokenIssuer CreateIssuer(TimeProvider timeProvider) =>
        new(this, _privateKeyPem, timeProvider);

    internal bool IsAllowedOrigin(string origin) =>
        AllowedOrigins.Contains(origin, StringComparer.OrdinalIgnoreCase);

    internal static AppleMusicTokenBrokerConfiguration Load(IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(configuration);

        var trustedProxies = LoadTrustedProxies(configuration["APPLE_MUSIC_TRUSTED_PROXIES"]);
        var teamId = configuration["APPLE_MUSIC_TEAM_ID"]?.Trim();
        var keyId = configuration["APPLE_MUSIC_KEY_ID"]?.Trim();
        var keyFile = configuration["APPLE_MUSIC_PRIVATE_KEY_FILE"]?.Trim();
        var originsText = configuration["APPLE_MUSIC_ALLOWED_ORIGINS"];
        var lifetimeText = configuration["APPLE_MUSIC_TOKEN_LIFETIME_MINUTES"];

        var supplied = new[] { teamId, keyId, keyFile, originsText }
            .Count(value => !string.IsNullOrWhiteSpace(value));
        if (supplied == 0)
        {
            return new AppleMusicTokenBrokerConfiguration(null, trustedProxies);
        }

        if (supplied != 4
            || !IsAppleIdentifier(teamId)
            || !IsAppleIdentifier(keyId)
            || !TryLoadOrigins(originsText, out var origins))
        {
            throw new InvalidOperationException(
                "Konfiguracja tokenów Apple Music jest niepełna albo nieprawidłowa.");
        }

        var tokenLifetime = LoadTokenLifetime(lifetimeText);
        var privateKeyPem = LoadPrivateKey(keyFile!);
        ValidatePrivateKey(privateKeyPem);

        return new AppleMusicTokenBrokerConfiguration(
            new AppleMusicTokenOptions(
                teamId!,
                keyId!,
                privateKeyPem,
                origins!,
                tokenLifetime),
            trustedProxies);
    }

    internal static bool TryNormalizeOrigin(string? value, out string? origin)
    {
        origin = null;
        if (string.IsNullOrWhiteSpace(value)
            || !Uri.TryCreate(value.Trim(), UriKind.Absolute, out var parsed)
            || !string.Equals(parsed.Scheme, Uri.UriSchemeHttps, StringComparison.Ordinal)
            || string.IsNullOrEmpty(parsed.Host)
            || !string.IsNullOrEmpty(parsed.UserInfo)
            || parsed.AbsolutePath != "/"
            || !string.IsNullOrEmpty(parsed.Query)
            || !string.IsNullOrEmpty(parsed.Fragment))
        {
            return false;
        }

        origin = parsed.GetLeftPart(UriPartial.Authority);
        return true;
    }

    private static bool IsAppleIdentifier(string? value) =>
        value is { Length: 10 }
        && value.All(character =>
            character is >= 'A' and <= 'Z' or >= '0' and <= '9');

    private static bool TryLoadOrigins(
        string? value,
        out IReadOnlyList<string>? origins)
    {
        origins = null;
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var entries = value.Split(',', StringSplitOptions.TrimEntries);
        if (entries.Length is 0 or > 16 || entries.Any(string.IsNullOrWhiteSpace))
        {
            return false;
        }

        var normalized = new List<string>(entries.Length);
        foreach (var entry in entries)
        {
            if (!TryNormalizeOrigin(entry, out var origin)
                || normalized.Contains(origin!, StringComparer.OrdinalIgnoreCase))
            {
                return false;
            }

            normalized.Add(origin!);
        }

        origins = normalized.AsReadOnly();
        return true;
    }

    private static TimeSpan LoadTokenLifetime(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return TimeSpan.FromMinutes(60);
        }

        if (!int.TryParse(
                value,
                NumberStyles.None,
                CultureInfo.InvariantCulture,
                out var minutes)
            || minutes is < 5 or > 1440)
        {
            throw new InvalidOperationException(
                "Czas życia tokenu Apple Music musi mieścić się od 5 do 1440 minut.");
        }

        return TimeSpan.FromMinutes(minutes);
    }

    private static string LoadPrivateKey(string filePath)
    {
        if (!Path.IsPathFullyQualified(filePath))
        {
            throw new InvalidOperationException(
                "Plik klucza Apple Music musi mieć bezwzględną ścieżkę.");
        }

        try
        {
            var file = new FileInfo(filePath);
            if (!file.Exists || file.Length is <= 0 or > 16_384)
            {
                throw new InvalidOperationException(
                    "Plik klucza Apple Music nie istnieje albo ma nieprawidłowy rozmiar.");
            }

            var value = File.ReadAllText(file.FullName);
            if (string.IsNullOrWhiteSpace(value) || value.Contains('\0'))
            {
                throw new InvalidOperationException(
                    "Plik klucza Apple Music ma nieprawidłową zawartość.");
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
                "Nie można bezpiecznie odczytać pliku klucza Apple Music.");
        }
    }

    private static void ValidatePrivateKey(string privateKeyPem)
    {
        try
        {
            using var key = ECDsa.Create();
            key.ImportFromPem(privateKeyPem);
            if (key.KeySize != 256)
            {
                throw new InvalidOperationException(
                    "Klucz Apple Music nie jest kluczem EC P-256.");
            }
        }
        catch (InvalidOperationException)
        {
            throw;
        }
        catch (Exception error) when (error is ArgumentException
            or CryptographicException)
        {
            throw new InvalidOperationException(
                "Plik klucza Apple Music nie zawiera prawidłowego klucza prywatnego ES256.");
        }
    }

    private static IReadOnlyList<IPAddress> LoadTrustedProxies(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return Array.Empty<IPAddress>();
        }

        var entries = value.Split(',', StringSplitOptions.TrimEntries);
        if (entries.Length > 16 || entries.Any(string.IsNullOrWhiteSpace))
        {
            throw new InvalidOperationException(
                "Lista zaufanych reverse proxy Apple Music jest nieprawidłowa.");
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
                    "Lista zaufanych reverse proxy Apple Music jest nieprawidłowa.");
            }

            if (!addresses.Contains(address))
            {
                addresses.Add(address);
            }
        }

        return addresses.AsReadOnly();
    }
}

internal sealed record AppleMusicTokenBrokerConfiguration(
    AppleMusicTokenOptions? Options,
    IReadOnlyList<IPAddress> TrustedProxies)
{
    internal bool IsConfigured => Options is not null;
}
