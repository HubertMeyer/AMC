using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace AccessibleMediaController.Core.YouTube;

/// <summary>
/// Bezpieczny, niezależny od interfejsu fundament oficjalnego logowania
/// YouTube dla aplikacji komputerowej. Klasa nie otwiera przeglądarki, nie
/// uruchamia odbiornika i nie zapisuje tokenów. Buduje wyłącznie dane potrzebne
/// hostowi C# do późniejszego przepływu Authorization Code + PKCE.
/// </summary>
public static class YouTubeOAuthProtocol
{
    public const string ReadOnlyScope = "https://www.googleapis.com/auth/youtube.readonly";

    private static readonly Uri AuthorizationEndpoint =
        new("https://accounts.google.com/o/oauth2/v2/auth");

    public static YouTubeAuthorizationRequest CreateAuthorizationRequest(
        string clientId,
        Uri redirectUri)
    {
        var verifierEntropy = RandomNumberGenerator.GetBytes(32);
        var stateEntropy = RandomNumberGenerator.GetBytes(32);
        try
        {
            return CreateAuthorizationRequest(clientId, redirectUri, verifierEntropy, stateEntropy);
        }
        finally
        {
            CryptographicOperations.ZeroMemory(verifierEntropy);
            CryptographicOperations.ZeroMemory(stateEntropy);
        }
    }

    internal static YouTubeAuthorizationRequest CreateAuthorizationRequest(
        string clientId,
        Uri redirectUri,
        ReadOnlySpan<byte> verifierEntropy,
        ReadOnlySpan<byte> stateEntropy)
    {
        var normalizedClientId = ValidateClientId(clientId);
        ValidateRedirectUri(redirectUri);
        if (verifierEntropy.Length < 32 || stateEntropy.Length < 24)
            throw new ArgumentException("Dane losowe logowania YouTube są zbyt krótkie.");

        var verifier = Base64Url(verifierEntropy);
        var challenge = CreateChallenge(verifier);
        var state = Base64Url(stateEntropy);
        var parameters = new Dictionary<string, string>
        {
            ["client_id"] = normalizedClientId,
            ["redirect_uri"] = redirectUri.AbsoluteUri,
            ["response_type"] = "code",
            ["scope"] = ReadOnlyScope,
            ["code_challenge"] = challenge,
            ["code_challenge_method"] = "S256",
            ["state"] = state,
            ["access_type"] = "offline",
            ["include_granted_scopes"] = "true"
        };
        var query = string.Join('&', parameters.Select(pair =>
            $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}"));
        var authorizationUri = new UriBuilder(AuthorizationEndpoint) { Query = query }.Uri;
        return new YouTubeAuthorizationRequest(authorizationUri, redirectUri, verifier, state);
    }

    public static IReadOnlyDictionary<string, string> CreateCodeExchangeFields(
        string clientId,
        string clientSecret,
        Uri redirectUri,
        string code,
        string codeVerifier)
    {
        var normalizedClientId = ValidateClientId(clientId);
        var normalizedClientSecret = ValidateClientSecret(clientSecret);
        ValidateRedirectUri(redirectUri);
        if (string.IsNullOrWhiteSpace(code))
            throw new ArgumentException("Google nie przekazał kodu logowania.", nameof(code));
        ValidateVerifier(codeVerifier);
        return new Dictionary<string, string>
        {
            ["client_id"] = normalizedClientId,
            ["client_secret"] = normalizedClientSecret,
            ["code"] = code.Trim(),
            ["code_verifier"] = codeVerifier,
            ["grant_type"] = "authorization_code",
            ["redirect_uri"] = redirectUri.AbsoluteUri
        };
    }

    public static IReadOnlyDictionary<string, string> CreateRefreshFields(
        string clientId,
        string clientSecret,
        string refreshToken)
    {
        var normalizedClientId = ValidateClientId(clientId);
        var normalizedClientSecret = ValidateClientSecret(clientSecret);
        if (string.IsNullOrWhiteSpace(refreshToken))
            throw new ArgumentException("Brak zapisanego odświeżenia logowania YouTube.", nameof(refreshToken));
        return new Dictionary<string, string>
        {
            ["client_id"] = normalizedClientId,
            ["client_secret"] = normalizedClientSecret,
            ["refresh_token"] = refreshToken,
            ["grant_type"] = "refresh_token"
        };
    }

    public static YouTubeTokenSet ReadTokenResponse(
        string json,
        string clientId,
        DateTimeOffset now,
        string? existingRefreshToken = null,
        string? existingScope = null)
    {
        var normalizedClientId = ValidateClientId(clientId);
        try
        {
            using var document = JsonDocument.Parse(json);
            var root = document.RootElement;
            var accessToken = root.TryGetProperty("access_token", out var access)
                ? access.GetString()
                : null;
            var refreshToken = root.TryGetProperty("refresh_token", out var refresh)
                ? refresh.GetString()
                : existingRefreshToken;
            var returnedScope = root.TryGetProperty("scope", out var scope)
                ? scope.GetString()
                : null;
            var grantedScope = string.IsNullOrWhiteSpace(returnedScope)
                ? existingScope ?? ReadOnlyScope
                : returnedScope.Trim();
            var expiresIn = root.TryGetProperty("expires_in", out var expires)
                && expires.TryGetInt32(out var seconds)
                    ? Math.Clamp(seconds, 60, 86_400)
                    : 3_600;

            if (string.IsNullOrWhiteSpace(accessToken) || string.IsNullOrWhiteSpace(refreshToken))
                throw new InvalidDataException("Google zwrócił niepełne dane logowania YouTube.");
            return new YouTubeTokenSet(
                accessToken,
                refreshToken,
                now.AddSeconds(expiresIn),
                grantedScope,
                normalizedClientId);
        }
        catch (JsonException)
        {
            // Treść odpowiedzi może zawierać token lub dane konta. Nigdy nie
            // dołączamy jej do komunikatu ani wyjątku.
            throw new InvalidDataException("Google zwrócił nieczytelną odpowiedź logowania YouTube.");
        }
    }

    public static string DescribeAuthorizationError(string? error)
    {
        if (string.Equals(error?.Trim(), "access_denied", StringComparison.OrdinalIgnoreCase))
            return "Logowanie YouTube zostało anulowane na stronie Google.";
        return "Logowanie YouTube nie zostało ukończone. Spróbuj ponownie.";
    }

    public static string CreateChallenge(string verifier)
    {
        ValidateVerifier(verifier);
        return Base64Url(SHA256.HashData(Encoding.ASCII.GetBytes(verifier)));
    }

    private static string ValidateClientId(string clientId)
    {
        var normalized = clientId?.Trim() ?? string.Empty;
        if (normalized.Length is < 20 or > 512
            || !normalized.EndsWith(".apps.googleusercontent.com", StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                "Logowanie YouTube nie jest jeszcze skonfigurowane dla tej wersji AMC.");
        }
        return normalized;
    }

    private static string ValidateClientSecret(string clientSecret)
    {
        var normalized = clientSecret?.Trim() ?? string.Empty;
        if (normalized.Length is < 8 or > 512
            || normalized.Any(character => char.IsWhiteSpace(character) || char.IsControl(character)))
        {
            throw new InvalidOperationException(
                "Logowanie YouTube nie jest jeszcze w pełni skonfigurowane dla tej wersji AMC.");
        }
        return normalized;
    }

    private static void ValidateRedirectUri(Uri redirectUri)
    {
        ArgumentNullException.ThrowIfNull(redirectUri);
        if (redirectUri.Scheme != Uri.UriSchemeHttp
            || !string.Equals(redirectUri.Host, "127.0.0.1", StringComparison.Ordinal)
            || redirectUri.IsDefaultPort
            || !string.IsNullOrEmpty(redirectUri.UserInfo)
            || !string.IsNullOrEmpty(redirectUri.Query)
            || !string.IsNullOrEmpty(redirectUri.Fragment))
        {
            throw new InvalidOperationException(
                "Adres powrotu YouTube musi używać lokalnego adresu 127.0.0.1 i przydzielonego portu.");
        }
    }

    private static void ValidateVerifier(string verifier)
    {
        if (string.IsNullOrWhiteSpace(verifier)
            || verifier.Length is < 43 or > 128
            || verifier.Any(character => !(char.IsAsciiLetterOrDigit(character)
                || character is '-' or '.' or '_' or '~')))
        {
            throw new ArgumentException("Nieprawidłowe zabezpieczenie PKCE logowania YouTube.");
        }
    }

    private static string Base64Url(ReadOnlySpan<byte> bytes) =>
        Convert.ToBase64String(bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_');
}

public sealed record YouTubeAuthorizationRequest(
    Uri AuthorizationUri,
    Uri RedirectUri,
    string CodeVerifier,
    string State);

public sealed record YouTubeTokenSet(
    string AccessToken,
    string RefreshToken,
    DateTimeOffset ExpiresAtUtc,
    string Scope,
    string ClientId);
