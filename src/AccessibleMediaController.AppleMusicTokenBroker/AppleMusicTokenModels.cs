using System.Text.Json.Serialization;

namespace AccessibleMediaController.AppleMusicTokenBroker;

internal sealed record DeveloperTokenResponse(
    [property: JsonPropertyName("developer_token")] string DeveloperToken,
    [property: JsonPropertyName("expires_at")] string ExpiresAt);

internal sealed record ErrorResponse(
    [property: JsonPropertyName("error")] string Error);

internal sealed record IssuedDeveloperToken(string Value, DateTimeOffset ExpiresAt);
