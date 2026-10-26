using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Oficjalny przepływ OAuth dla aplikacji desktopowej: przeglądarka systemowa,
/// losowy port pętli zwrotnej, state i PKCE S256. AMC nie widzi hasła Google.
/// </summary>
internal sealed class YouTubeGoogleOAuthClient(HttpClient? httpClient = null) : IDisposable
{
    internal const string RequestedScope = "https://www.googleapis.com/auth/youtube.readonly";
    private static readonly Uri AuthorizationEndpoint = new("https://accounts.google.com/o/oauth2/v2/auth");
    private static readonly Uri TokenEndpoint = new("https://oauth2.googleapis.com/token");
    private readonly HttpClient http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
    private readonly bool ownsHttpClient = httpClient is null;

    public async Task<YouTubeGoogleCredentialSet> AuthorizeAsync(
        string clientId,
        CancellationToken cancellationToken)
    {
        ValidateClientId(clientId);
        var pkce = Pkce.Create();
        var state = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant();
        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var port = ((IPEndPoint)listener.LocalEndpoint).Port;
        var redirectUri = new Uri($"http://127.0.0.1:{port}/", UriKind.Absolute);
        var authorizationUri = BuildAuthorizationUri(clientId, redirectUri, pkce.Challenge, state);

        DiagnosticLog.Info("youtube-google-auth", "Rozpoczęto oficjalne logowanie Google dla YouTube.");
        Process.Start(new ProcessStartInfo(authorizationUri.AbsoluteUri) { UseShellExecute = true });
        var callback = await ReceiveCallbackAsync(listener, redirectUri, state, cancellationToken)
            .ConfigureAwait(false);
        if (!string.IsNullOrWhiteSpace(callback.Error))
            throw new InvalidOperationException(DescribeAuthorizationError(callback.Error));
        if (string.IsNullOrWhiteSpace(callback.Code))
            throw new InvalidOperationException("Google nie przekazał kodu logowania.");

        return await ExchangeCodeAsync(
            clientId,
            redirectUri,
            callback.Code,
            pkce.Verifier,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<YouTubeGoogleCredentialSet> RefreshAsync(
        YouTubeGoogleCredentialSet current,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(current);
        ValidateClientId(current.ClientId);
        if (string.IsNullOrWhiteSpace(current.RefreshToken))
            throw new InvalidOperationException("Zapisane logowanie YouTube nie ma tokenu odświeżania. Zaloguj konto ponownie.");

        using var response = await http.PostAsync(
            TokenEndpoint,
            new FormUrlEncodedContent(new Dictionary<string, string>
            {
                ["client_id"] = current.ClientId,
                ["grant_type"] = "refresh_token",
                ["refresh_token"] = current.RefreshToken
            }),
            cancellationToken).ConfigureAwait(false);
        return await ReadTokensAsync(
            response,
            current.ClientId,
            current.RefreshToken,
            current.Scope,
            current.AccountDisplayName,
            cancellationToken).ConfigureAwait(false);
    }

    internal static Uri BuildAuthorizationUri(
        string clientId,
        Uri redirectUri,
        string challenge,
        string state)
    {
        ValidateClientId(clientId);
        if (!redirectUri.IsLoopback || redirectUri.Scheme != Uri.UriSchemeHttp)
            throw new ArgumentException("Adres powrotu Google musi być lokalnym adresem HTTP.", nameof(redirectUri));
        var parameters = new Dictionary<string, string>
        {
            ["response_type"] = "code",
            ["client_id"] = clientId.Trim(),
            ["redirect_uri"] = redirectUri.AbsoluteUri,
            ["scope"] = RequestedScope,
            ["code_challenge"] = challenge,
            ["code_challenge_method"] = "S256",
            ["state"] = state,
            ["access_type"] = "offline",
            ["prompt"] = "consent",
            ["include_granted_scopes"] = "true"
        };
        var query = string.Join('&', parameters.Select(pair =>
            $"{Uri.EscapeDataString(pair.Key)}={Uri.EscapeDataString(pair.Value)}"));
        return new UriBuilder(AuthorizationEndpoint) { Query = query }.Uri;
    }

    private async Task<YouTubeGoogleCredentialSet> ExchangeCodeAsync(
        string clientId,
        Uri redirectUri,
        string code,
        string verifier,
        CancellationToken cancellationToken)
    {
        using var response = await http.PostAsync(
            TokenEndpoint,
            new FormUrlEncodedContent(new Dictionary<string, string>
            {
                ["client_id"] = clientId.Trim(),
                ["code"] = code,
                ["code_verifier"] = verifier,
                ["grant_type"] = "authorization_code",
                ["redirect_uri"] = redirectUri.AbsoluteUri
            }),
            cancellationToken).ConfigureAwait(false);
        return await ReadTokensAsync(
            response,
            clientId.Trim(),
            null,
            RequestedScope,
            string.Empty,
            cancellationToken).ConfigureAwait(false);
    }

    private static async Task<YouTubeGoogleCredentialSet> ReadTokensAsync(
        HttpResponseMessage response,
        string clientId,
        string? existingRefreshToken,
        string existingScope,
        string accountDisplayName,
        CancellationToken cancellationToken)
    {
        if (!response.IsSuccessStatusCode)
        {
            var error = await ReadErrorAsync(response, cancellationToken).ConfigureAwait(false);
            DiagnosticLog.Warning(
                "youtube-google-auth",
                $"Google odrzucił żądanie tokenu: HTTP {(int)response.StatusCode}; {error}.");
            throw new InvalidOperationException(DescribeTokenError(error));
        }

        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        using var document = await JsonDocument.ParseAsync(stream, cancellationToken: cancellationToken).ConfigureAwait(false);
        var root = document.RootElement;
        var accessToken = ReadString(root, "access_token");
        var refreshToken = ReadString(root, "refresh_token");
        if (refreshToken.Length == 0) refreshToken = existingRefreshToken ?? string.Empty;
        var scope = ReadString(root, "scope");
        if (scope.Length == 0) scope = existingScope;
        var expiresIn = root.TryGetProperty("expires_in", out var expires)
            && expires.TryGetInt32(out var seconds)
                ? Math.Max(60, seconds)
                : 3600;
        if (accessToken.Length == 0 || refreshToken.Length == 0)
            throw new InvalidDataException("Google zwrócił niepełne dane logowania.");

        DiagnosticLog.Info("youtube-google-auth", "Google zaakceptował logowanie YouTube; tokeny zapisano poza konfiguracją AMC.");
        return new YouTubeGoogleCredentialSet(
            clientId,
            accessToken,
            refreshToken,
            DateTimeOffset.UtcNow.AddSeconds(expiresIn),
            scope,
            accountDisplayName);
    }

    private static async Task<AuthorizationCallback> ReceiveCallbackAsync(
        TcpListener listener,
        Uri redirectUri,
        string expectedState,
        CancellationToken cancellationToken)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromMinutes(5));
        using var client = await listener.AcceptTcpClientAsync(timeout.Token).ConfigureAwait(false);
        await using var stream = client.GetStream();
        using var reader = new StreamReader(stream, Encoding.ASCII, false, 4096, leaveOpen: true);
        var requestLine = await reader.ReadLineAsync(timeout.Token).ConfigureAwait(false) ?? string.Empty;
        string? header;
        do { header = await reader.ReadLineAsync(timeout.Token).ConfigureAwait(false); }
        while (!string.IsNullOrEmpty(header));

        var target = requestLine.Split(' ', StringSplitOptions.RemoveEmptyEntries).ElementAtOrDefault(1);
        var callbackUri = Uri.TryCreate(
                redirectUri.GetLeftPart(UriPartial.Authority) + target,
                UriKind.Absolute,
                out var parsed)
            ? parsed
            : null;
        var query = callbackUri is null ? [] : ParseQuery(callbackUri.Query);
        var validState = query.TryGetValue("state", out var returnedState)
            && CryptographicOperations.FixedTimeEquals(
                Encoding.UTF8.GetBytes(returnedState),
                Encoding.UTF8.GetBytes(expectedState));
        var success = callbackUri is not null
            && callbackUri.IsLoopback
            && callbackUri.Port == redirectUri.Port
            && validState
            && query.ContainsKey("code");
        var message = success
            ? "Logowanie YouTube zakończone. Możesz zamknąć tę kartę i wrócić do AMC."
            : "Logowanie YouTube nie zostało ukończone. Wróć do AMC i spróbuj ponownie.";
        var body = $"<!doctype html><html lang=\"pl\"><meta charset=\"utf-8\"><title>AMC — YouTube</title><body><h1>{message}</h1></body></html>";
        var bodyBytes = Encoding.UTF8.GetBytes(body);
        var responseBytes = Encoding.ASCII.GetBytes(
            "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
            + $"Content-Length: {bodyBytes.Length}\r\nConnection: close\r\n\r\n");
        await stream.WriteAsync(responseBytes, timeout.Token).ConfigureAwait(false);
        await stream.WriteAsync(bodyBytes, timeout.Token).ConfigureAwait(false);
        await stream.FlushAsync(timeout.Token).ConfigureAwait(false);

        if (!validState) return new AuthorizationCallback(null, "nieprawidłowe zabezpieczenie sesji");
        return new AuthorizationCallback(
            query.GetValueOrDefault("code"),
            query.GetValueOrDefault("error_description") ?? query.GetValueOrDefault("error"));
    }

    private static Dictionary<string, string> ParseQuery(string query) =>
        query.TrimStart('?')
            .Split('&', StringSplitOptions.RemoveEmptyEntries)
            .Select(part => part.Split('=', 2))
            .ToDictionary(
                pair => Uri.UnescapeDataString(pair[0].Replace('+', ' ')),
                pair => pair.Length > 1
                    ? Uri.UnescapeDataString(pair[1].Replace('+', ' '))
                    : string.Empty,
                StringComparer.Ordinal);

    private static async Task<string> ReadErrorAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        try
        {
            var content = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            using var document = JsonDocument.Parse(content);
            var root = document.RootElement;
            var error = ReadString(root, "error");
            var description = ReadString(root, "error_description");
            return string.Join(", ", new[] { error, description }.Where(value => value.Length > 0));
        }
        catch
        {
            return $"HTTP {(int)response.StatusCode}";
        }
    }

    private static string DescribeAuthorizationError(string error)
    {
        if (error.Contains("access_denied", StringComparison.OrdinalIgnoreCase))
            return "Logowanie Google zostało anulowane na stronie logowania.";
        return "Logowanie Google nie zostało ukończone. Sprawdź konfigurację aplikacji desktopowej i spróbuj ponownie.";
    }

    private static string DescribeTokenError(string error)
    {
        if (error.Contains("invalid_grant", StringComparison.OrdinalIgnoreCase))
            return "Zapisane logowanie Google straciło ważność. Zaloguj konto YouTube ponownie.";
        if (error.Contains("invalid_client", StringComparison.OrdinalIgnoreCase))
            return "Google nie rozpoznał identyfikatora aplikacji desktopowej. Sprawdź Client ID.";
        return "Google odrzucił logowanie YouTube. Spróbuj zalogować konto ponownie.";
    }

    private static string ReadString(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()?.Trim() ?? string.Empty
            : string.Empty;

    private static void ValidateClientId(string clientId)
    {
        if (!YouTubeGoogleCredentialStore.IsValidClientId(clientId))
        {
            throw new InvalidOperationException(
                "Wpisz identyfikator klienta Google typu Aplikacja na komputer. Powinien kończyć się na .apps.googleusercontent.com.");
        }
    }

    public void Dispose()
    {
        if (ownsHttpClient) http.Dispose();
    }

    private sealed record AuthorizationCallback(string? Code, string? Error);

    private sealed record Pkce(string Verifier, string Challenge)
    {
        public static Pkce Create()
        {
            var verifier = Base64Url(RandomNumberGenerator.GetBytes(64));
            var challenge = Base64Url(SHA256.HashData(Encoding.ASCII.GetBytes(verifier)));
            return new Pkce(verifier, challenge);
        }

        private static string Base64Url(byte[] bytes) => Convert.ToBase64String(bytes)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
    }
}
