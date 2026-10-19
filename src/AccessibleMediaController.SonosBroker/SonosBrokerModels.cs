using System.Text.Json.Serialization;

namespace AccessibleMediaController.SonosBroker;

internal sealed record StartRequest(
    [property: JsonPropertyName("code_challenge")] string? CodeChallenge,
    [property: JsonPropertyName("code_challenge_method")] string? CodeChallengeMethod);

internal sealed record ResultRequest(
    [property: JsonPropertyName("session_id")] string? SessionId,
    [property: JsonPropertyName("code_verifier")] string? CodeVerifier);

internal sealed record RefreshRequest(
    [property: JsonPropertyName("refresh_token")] string? RefreshToken);

internal sealed record StartResponse(
    [property: JsonPropertyName("session_id")] string SessionId,
    [property: JsonPropertyName("authorize_url")] string AuthorizeUrl,
    [property: JsonPropertyName("expires_in")] int ExpiresIn);

internal sealed record TokenResponse(
    [property: JsonPropertyName("access_token")] string AccessToken,
    [property: JsonPropertyName("token_type")] string TokenType,
    [property: JsonPropertyName("expires_in")] int? ExpiresIn,
    [property: JsonPropertyName("refresh_token")] string RefreshToken,
    [property: JsonPropertyName("scope")] string? Scope);

internal sealed record ErrorResponse(
    [property: JsonPropertyName("error")] string Error);

internal enum SessionCreateStatus
{
    Success,
    CapacityReached
}

internal sealed record SessionCreateResult(
    SessionCreateStatus Status,
    string? SessionId,
    string? State,
    DateTimeOffset ExpiresAtUtc);

internal enum SessionReadStatus
{
    Pending,
    Success,
    Denied,
    InvalidCallback,
    TokenExchangeFailed,
    Unknown,
    ProofMismatch
}

internal sealed record SessionReadResult(SessionReadStatus Status, TokenResponse? Tokens = null);

internal enum CallbackStoreStatus
{
    Stored,
    Unknown,
    AlreadyCompleted
}

internal enum CallbackBeginStatus
{
    Started,
    Unknown,
    AlreadyStarted
}

internal enum OAuthStatus
{
    Success,
    ReauthorizationRequired,
    RateLimited,
    TemporaryFailure,
    InvalidResponse
}

internal sealed record OAuthResult(OAuthStatus Status, TokenResponse? Tokens = null);
