using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace AccessibleMediaController.SonosBroker;

internal sealed class SonosOAuthGateway
{
    internal static readonly Uri AuthorizeEndpoint = new("https://api.sonos.com/login/v3/oauth");
    internal static readonly Uri TokenEndpoint = new("https://api.sonos.com/login/v3/oauth/access");
    internal const int MaximumResponseBytes = 64 * 1024;

    private readonly SonosBrokerOptions options;
    private readonly HttpClient http;

    internal SonosOAuthGateway(SonosBrokerOptions options, HttpClient http)
    {
        this.options = options ?? throw new ArgumentNullException(nameof(options));
        this.http = http ?? throw new ArgumentNullException(nameof(http));
    }

    internal Uri CreateAuthorizeUri(string state)
    {
        if (!SonosLoginSessionStore.IsPkceValue(state))
        {
            throw new ArgumentException("Nieprawidłowy stan logowania.", nameof(state));
        }

        var query = QueryString.Create(new Dictionary<string, string?>
        {
            ["client_id"] = options.ClientId,
            ["response_type"] = "code",
            ["state"] = state,
            ["scope"] = SonosBrokerOptions.Scope,
            ["redirect_uri"] = options.RedirectUri.AbsoluteUri
        });
        return new Uri(AuthorizeEndpoint.AbsoluteUri + query);
    }

    internal Task<OAuthResult> ExchangeCodeAsync(
        string code,
        CancellationToken cancellationToken) =>
        SendAsync(
            new Dictionary<string, string>
            {
                ["grant_type"] = "authorization_code",
                ["code"] = code,
                ["redirect_uri"] = options.RedirectUri.AbsoluteUri
            },
            fallbackRefreshToken: null,
            refreshOperation: false,
            cancellationToken);

    internal Task<OAuthResult> RefreshAsync(
        string refreshToken,
        CancellationToken cancellationToken) =>
        SendAsync(
            new Dictionary<string, string>
            {
                ["grant_type"] = "refresh_token",
                ["refresh_token"] = refreshToken
            },
            fallbackRefreshToken: refreshToken,
            refreshOperation: true,
            cancellationToken);

    private async Task<OAuthResult> SendAsync(
        IReadOnlyDictionary<string, string> fields,
        string? fallbackRefreshToken,
        bool refreshOperation,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, TokenEndpoint)
        {
            Content = new FormUrlEncodedContent(fields)
        };
        var credentials = Convert.ToBase64String(
            Encoding.UTF8.GetBytes(options.ClientId + ":" + options.ClientSecret));
        request.Headers.Authorization = new AuthenticationHeaderValue("Basic", credentials);
        request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

        try
        {
            using var response = await http.SendAsync(
                request,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken).ConfigureAwait(false);

            if (response.StatusCode == HttpStatusCode.TooManyRequests)
            {
                return new OAuthResult(OAuthStatus.RateLimited);
            }

            if (refreshOperation
                && response.StatusCode is HttpStatusCode.BadRequest or HttpStatusCode.Unauthorized)
            {
                return new OAuthResult(OAuthStatus.ReauthorizationRequired);
            }

            if ((int)response.StatusCode >= 500)
            {
                return new OAuthResult(OAuthStatus.TemporaryFailure);
            }

            if (response.StatusCode != HttpStatusCode.OK)
            {
                return new OAuthResult(OAuthStatus.InvalidResponse);
            }

            var body = await ReadBoundedAsync(response.Content, cancellationToken).ConfigureAwait(false);
            if (body is null || !TryReadTokens(body, fallbackRefreshToken, out var tokens))
            {
                return new OAuthResult(OAuthStatus.InvalidResponse);
            }

            return new OAuthResult(OAuthStatus.Success, tokens);
        }
        catch (OperationCanceledException)
        {
            return new OAuthResult(OAuthStatus.TemporaryFailure);
        }
        catch (HttpRequestException)
        {
            return new OAuthResult(OAuthStatus.TemporaryFailure);
        }
    }

    private static async Task<byte[]?> ReadBoundedAsync(
        HttpContent content,
        CancellationToken cancellationToken)
    {
        if (content.Headers.ContentLength is > MaximumResponseBytes)
        {
            return null;
        }

        await using var stream = await content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        using var memory = new MemoryStream();
        var buffer = new byte[8192];
        while (true)
        {
            var read = await stream.ReadAsync(buffer, cancellationToken).ConfigureAwait(false);
            if (read == 0)
            {
                return memory.ToArray();
            }

            if (memory.Length + read > MaximumResponseBytes)
            {
                return null;
            }

            memory.Write(buffer, 0, read);
        }
    }

    private static bool TryReadTokens(
        byte[] body,
        string? fallbackRefreshToken,
        out TokenResponse? tokens)
    {
        tokens = null;
        try
        {
            using var document = JsonDocument.Parse(body);
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object
                || !TryString(root, "access_token", 16 * 1024, out var accessToken)
                || !TryOptionalString(root, "token_type", 32, out var tokenType)
                || (tokenType is not null
                    && !string.Equals(tokenType.Trim(), "Bearer", StringComparison.OrdinalIgnoreCase))
                || !TryOptionalString(root, "refresh_token", 2048, out var refreshToken)
                || !TryOptionalString(root, "scope", 1024, out var scope)
                || !TryOptionalPositiveInt(root, "expires_in", out var expiresIn))
            {
                return false;
            }

            refreshToken ??= fallbackRefreshToken;
            if (string.IsNullOrEmpty(refreshToken))
            {
                return false;
            }

            tokens = new TokenResponse(
                accessToken!,
                "Bearer",
                expiresIn,
                refreshToken,
                scope);
            return true;
        }
        catch (JsonException)
        {
            return false;
        }
        catch (InvalidOperationException)
        {
            return false;
        }
    }

    private static bool TryString(
        JsonElement root,
        string property,
        int maximumLength,
        out string? value)
    {
        value = null;
        if (!root.TryGetProperty(property, out var element)
            || element.ValueKind != JsonValueKind.String)
        {
            return false;
        }

        value = element.GetString();
        return !string.IsNullOrEmpty(value) && value.Length <= maximumLength;
    }

    private static bool TryOptionalString(
        JsonElement root,
        string property,
        int maximumLength,
        out string? value)
    {
        value = null;
        if (!root.TryGetProperty(property, out var element))
        {
            return true;
        }

        if (element.ValueKind == JsonValueKind.Null)
        {
            return true;
        }

        if (element.ValueKind != JsonValueKind.String)
        {
            return false;
        }

        value = element.GetString();
        return value is not null && value.Length <= maximumLength;
    }

    private static bool TryOptionalPositiveInt(
        JsonElement root,
        string property,
        out int? value)
    {
        value = null;
        if (!root.TryGetProperty(property, out var element))
        {
            return true;
        }

        if (element.ValueKind != JsonValueKind.Number
            || !element.TryGetInt32(out var parsed)
            || parsed <= 0)
        {
            return false;
        }

        value = parsed;
        return true;
    }
}
