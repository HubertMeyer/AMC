using System.Net;
using System.Text.Json;

namespace AccessibleMediaController.Core.YouTube;

/// <summary>
/// Wąski klient oficjalnego punktu tokenów Google. Nie uruchamia
/// przeglądarki i nie zapisuje poświadczeń; właścicielem obu czynności będzie
/// koordynator konta w hoście C#.
/// </summary>
public sealed class YouTubeOAuthTokenClient : IDisposable
{
    private static readonly Uri TokenEndpoint = new("https://oauth2.googleapis.com/token");
    private static readonly Uri RevocationEndpoint = new("https://oauth2.googleapis.com/revoke");
    private readonly HttpClient _http;
    private readonly bool _ownsHttpClient;

    public YouTubeOAuthTokenClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
        _ownsHttpClient = httpClient is null;
    }

    public async Task<YouTubeTokenSet> ExchangeCodeAsync(
        string clientId,
        string clientSecret,
        Uri redirectUri,
        string code,
        string codeVerifier,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        var fields = YouTubeOAuthProtocol.CreateCodeExchangeFields(
            clientId, clientSecret, redirectUri, code, codeVerifier);
        return await SendAsync(
            TokenEndpoint, fields, clientId, now, null, null, cancellationToken).ConfigureAwait(false);
    }

    public async Task<YouTubeTokenSet> RefreshAsync(
        YouTubeTokenSet current,
        string clientSecret,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(current);
        var fields = YouTubeOAuthProtocol.CreateRefreshFields(
            current.ClientId, clientSecret, current.RefreshToken);
        return await SendAsync(
            TokenEndpoint,
            fields,
            current.ClientId,
            now,
            current.RefreshToken,
            current.Scope,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<YouTubeTokenSet> ExchangeCodeThroughBrokerAsync(
        Uri tokenBrokerEndpoint,
        string clientId,
        Uri redirectUri,
        string code,
        string codeVerifier,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        var endpoint = YouTubeOAuthProtocol.ValidateTokenBrokerEndpoint(tokenBrokerEndpoint);
        var fields = YouTubeOAuthProtocol.CreateBrokerCodeExchangeFields(
            clientId, redirectUri, code, codeVerifier);
        return await SendAsync(
            endpoint, fields, clientId, now, null, null, cancellationToken).ConfigureAwait(false);
    }

    public async Task<YouTubeTokenSet> RefreshThroughBrokerAsync(
        Uri tokenBrokerEndpoint,
        YouTubeTokenSet current,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(current);
        var endpoint = YouTubeOAuthProtocol.ValidateTokenBrokerEndpoint(tokenBrokerEndpoint);
        var fields = YouTubeOAuthProtocol.CreateBrokerRefreshFields(
            current.ClientId, current.RefreshToken);
        return await SendAsync(
            endpoint,
            fields,
            current.ClientId,
            now,
            current.RefreshToken,
            current.Scope,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task RevokeAsync(
        string token,
        CancellationToken cancellationToken)
    {
        var fields = YouTubeOAuthProtocol.CreateRevocationFields(token);
        using var response = await _http.PostAsync(
            RevocationEndpoint,
            new FormUrlEncodedContent(fields),
            cancellationToken).ConfigureAwait(false);
        if (response.IsSuccessStatusCode) return;

        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        // Google opisuje invalid_token jako token już wygasły albo wcześniej
        // cofnięty. Cel użytkownika jest wtedy osiągnięty i można bezpiecznie
        // zakończyć lokalne usuwanie.
        if (response.StatusCode == HttpStatusCode.BadRequest
            && string.Equals(
                ReadErrorCode(body),
                "invalid_token",
                StringComparison.OrdinalIgnoreCase))
            return;
        throw new InvalidOperationException(
            response.StatusCode == HttpStatusCode.TooManyRequests
                ? "Google chwilowo ograniczył cofanie dostępu YouTube. Spróbuj później."
                : "Nie udało się cofnąć dostępu YouTube w Google. Spróbuj ponownie.");
    }

    private async Task<YouTubeTokenSet> SendAsync(
        Uri endpoint,
        IReadOnlyDictionary<string, string> fields,
        string clientId,
        DateTimeOffset now,
        string? existingRefreshToken,
        string? existingScope,
        CancellationToken cancellationToken)
    {
        using var response = await _http.PostAsync(
            endpoint,
            new FormUrlEncodedContent(fields),
            cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(DescribeTokenFailure(response.StatusCode, body));
        return YouTubeOAuthProtocol.ReadTokenResponse(
            body, clientId, now, existingRefreshToken, existingScope);
    }

    private static string DescribeTokenFailure(HttpStatusCode statusCode, string body)
    {
        var code = ReadErrorCode(body);
        if (string.Equals(code, "invalid_grant", StringComparison.OrdinalIgnoreCase))
            return "Kod lub zapisane logowanie YouTube straciło ważność. Zaloguj się ponownie.";
        if (string.Equals(code, "invalid_client", StringComparison.OrdinalIgnoreCase))
            return "Ta wersja AMC nie ma prawidłowo skonfigurowanego logowania YouTube.";
        if (string.Equals(code, "unauthorized_client", StringComparison.OrdinalIgnoreCase))
            return "Klient OAuth YouTube ma niewłaściwy typ. Utwórz w Google klienta typu Aplikacja komputerowa.";
        if (string.Equals(code, "invalid_request", StringComparison.OrdinalIgnoreCase))
            return "Google odrzucił dane logowania YouTube. Sprawdź konfigurację klienta typu Aplikacja komputerowa.";
        if (string.Equals(code, "redirect_uri_mismatch", StringComparison.OrdinalIgnoreCase))
            return "Adres powrotu logowania YouTube nie pasuje do klienta OAuth. Użyj klienta typu Aplikacja komputerowa.";
        if (string.Equals(code, "access_denied", StringComparison.OrdinalIgnoreCase))
            return "Logowanie YouTube zostało anulowane na stronie Google.";
        if (statusCode == HttpStatusCode.TooManyRequests)
            return "Google chwilowo ograniczył liczbę prób logowania YouTube. Spróbuj później.";
        return statusCode is HttpStatusCode.BadRequest or HttpStatusCode.Unauthorized
            ? "Google odrzucił logowanie YouTube. Spróbuj zalogować się ponownie."
            : "Nie udało się połączyć z usługą logowania YouTube.";
    }

    private static string? ReadErrorCode(string body)
    {
        try
        {
            using var document = JsonDocument.Parse(body);
            return document.RootElement.TryGetProperty("error", out var error)
                ? error.GetString()?.Trim()
                : null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public void Dispose()
    {
        if (_ownsHttpClient) _http.Dispose();
    }
}
