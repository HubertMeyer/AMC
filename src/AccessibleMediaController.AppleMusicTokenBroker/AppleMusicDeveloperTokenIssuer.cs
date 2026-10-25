using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace AccessibleMediaController.AppleMusicTokenBroker;

internal sealed class AppleMusicDeveloperTokenIssuer : IDisposable
{
    private readonly AppleMusicTokenOptions _options;
    private readonly TimeProvider _timeProvider;
    private readonly ECDsa _key;
    private readonly object _gate = new();

    internal AppleMusicDeveloperTokenIssuer(
        AppleMusicTokenOptions options,
        string privateKeyPem,
        TimeProvider timeProvider)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _timeProvider = timeProvider ?? throw new ArgumentNullException(nameof(timeProvider));
        _key = ECDsa.Create();
        _key.ImportFromPem(privateKeyPem);
    }

    internal IssuedDeveloperToken Issue(string origin)
    {
        if (!_options.IsAllowedOrigin(origin))
        {
            throw new ArgumentOutOfRangeException(nameof(origin));
        }

        var issuedAt = _timeProvider.GetUtcNow();
        var expiresAt = issuedAt.Add(_options.TokenLifetime);
        var header = JsonSerializer.SerializeToUtf8Bytes(new Dictionary<string, object>
        {
            ["alg"] = "ES256",
            ["kid"] = _options.KeyId
        });
        var payload = JsonSerializer.SerializeToUtf8Bytes(new Dictionary<string, object>
        {
            ["iss"] = _options.TeamId,
            ["iat"] = issuedAt.ToUnixTimeSeconds(),
            ["exp"] = expiresAt.ToUnixTimeSeconds(),
            ["origin"] = new[] { origin }
        });
        var signingInput = Base64Url(header) + "." + Base64Url(payload);
        byte[] signature;
        lock (_gate)
        {
            signature = _key.SignData(
                Encoding.ASCII.GetBytes(signingInput),
                HashAlgorithmName.SHA256,
                DSASignatureFormat.IeeeP1363FixedFieldConcatenation);
        }

        return new IssuedDeveloperToken(
            signingInput + "." + Base64Url(signature),
            expiresAt);
    }

    public void Dispose() => _key.Dispose();

    private static string Base64Url(byte[] value) =>
        Convert.ToBase64String(value)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
}
