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
    private readonly HttpClient _http;
    private readonly bool _ownsHttpClient;

    public YouTubeOAuthTokenClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
        _ownsHttpClient = httpClient is null;
    }

    public async Task<YouTubeTokenSet> ExchangeCodeAsync(
        string clientId,
        Uri redirectUri,
        string code,
        string codeVerifier,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        var fields = YouTubeOAuthProtocol.CreateCodeExchangeFields(
            clientId, redirectUri, code, codeVerifier);
        return await SendAsync(
            fields, clientId, now, null, null, cancellationToken).ConfigureAwait(false);
    }

    public async Task<YouTubeTokenSet> RefreshAsync(
        YouTubeTokenSet current,
        DateTimeOffset now,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(current);
        var fields = YouTubeOAuthProtocol.CreateRefreshFields(
            current.ClientId, current.RefreshToken);
        return await SendAsync(
            fields,
            current.ClientId,
            now,
            current.RefreshToken,
            current.Scope,
            cancellationToken).ConfigureAwait(false);
    }

    private async Task<YouTubeTokenSet> SendAsync(
        IReadOnlyDictionary<string, string> fields,
        string clientId,
        DateTimeOffset now,
        string? existingRefreshToken,
        string? existingScope,
        CancellationToken cancellationToken)
    {
        using var response = await _http.PostAsync(
            TokenEndpoint,
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
