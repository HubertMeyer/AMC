using System.Globalization;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Text;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public sealed class FrontierSmartClient : IDisposable
{
    private const int MaximumResponseBytes = 1024 * 1024;
    private static readonly string[] SnapshotNodes =
    [
        FrontierSmartNodes.FriendlyName,
        FrontierSmartNodes.RadioId,
        FrontierSmartNodes.FirmwareVersion,
        FrontierSmartNodes.Power,
        FrontierSmartNodes.Volume,
        FrontierSmartNodes.VolumeSteps,
        FrontierSmartNodes.Mute,
        FrontierSmartNodes.Mode,
        FrontierSmartNodes.PlaybackControl,
        FrontierSmartNodes.PlayName,
        FrontierSmartNodes.PlayText,
        FrontierSmartNodes.PlayArtist,
        FrontierSmartNodes.PlayAlbum,
        FrontierSmartNodes.PlayDuration,
        FrontierSmartNodes.PlayPosition
    ];

    private readonly HttpClient client;
    private readonly bool ownsClient;

    public FrontierSmartClient()
    {
        var handler = new SocketsHttpHandler
        {
            AllowAutoRedirect = false,
            ConnectTimeout = TimeSpan.FromSeconds(3),
            PooledConnectionLifetime = TimeSpan.FromMinutes(2)
        };
        client = CreateClient(handler);
        ownsClient = true;
    }

    public FrontierSmartClient(HttpMessageHandler handler)
    {
        ArgumentNullException.ThrowIfNull(handler);
        client = CreateClient(handler);
        ownsClient = true;
    }

    public FrontierSmartClient(HttpClient client)
    {
        this.client = client ?? throw new ArgumentNullException(nameof(client));
        ownsClient = false;
    }

    public async Task<FrontierSmartSnapshot> ReadSnapshotAsync(
        string address,
        string pin,
        CancellationToken cancellationToken = default)
    {
        IReadOnlyDictionary<string, FrontierSmartValue> values;
        try
        {
            values = await GetMultipleAsync(address, pin, SnapshotNodes, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (HttpRequestException exception) when (exception.StatusCode == HttpStatusCode.NotFound)
        {
            // Starsze odmiany firmware nie zawsze udostępniają GET_MULTIPLE.
            // Pojedyncze GET-y są wolniejsze, ale nie tworzą sesji FSAPI i nie
            // unieważniają połączenia aplikacji UNDOK/SmartRadio użytkownika.
            values = await ReadSnapshotNodesIndividuallyAsync(address, pin, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (FormatException)
        {
            // Część starszych urządzeń odpowiada na GET_MULTIPLE zwykłym
            // fsapiResponse z błędem zamiast kodu HTTP 404. Pojedyncze GET-y
            // pozostają z nimi zgodne.
            values = await ReadSnapshotNodesIndividuallyAsync(address, pin, cancellationToken)
                .ConfigureAwait(false);
        }

        var duration = Milliseconds(Value(FrontierSmartNodes.PlayDuration).AsUInt32());
        var position = Milliseconds(Value(FrontierSmartNodes.PlayPosition).AsUInt32());
        return new FrontierSmartSnapshot(
            Text(FrontierSmartNodes.FriendlyName, "Urządzenie Frontier Smart"),
            Text(FrontierSmartNodes.RadioId),
            Text(FrontierSmartNodes.FirmwareVersion),
            Value(FrontierSmartNodes.Power).AsBoolean(),
            Value(FrontierSmartNodes.Volume).AsInt32(),
            Value(FrontierSmartNodes.VolumeSteps).AsInt32(),
            Value(FrontierSmartNodes.Mute).AsBoolean(),
            Value(FrontierSmartNodes.Mode).AsUInt32(),
            Value(FrontierSmartNodes.PlaybackControl).AsInt32(),
            Text(FrontierSmartNodes.PlayName),
            Text(FrontierSmartNodes.PlayText),
            Text(FrontierSmartNodes.PlayArtist),
            Text(FrontierSmartNodes.PlayAlbum),
            duration,
            position);

        FrontierSmartValue Value(string node) => values.GetValueOrDefault(node)
            ?? new FrontierSmartValue(node, "FS_NODE_DOES_NOT_EXIST", null, null);

        string Text(string node, string fallback = "")
        {
            var value = Value(node);
            return value.Success && !string.IsNullOrWhiteSpace(value.Value)
                ? value.Value.Trim()
                : fallback;
        }
    }

    public async Task<FrontierSmartIdentity> ReadIdentityAsync(
        string address,
        string pin,
        CancellationToken cancellationToken = default)
    {
        var name = await GetAsync(address, pin, FrontierSmartNodes.FriendlyName, cancellationToken)
            .ConfigureAwait(false);
        if (!name.Success)
        {
            throw new FrontierSmartProtocolException(
                "Urządzenie nie potwierdziło podstawowych danych Frontier Smart.",
                name.Status);
        }

        var radioId = await ReadOptionalTextAsync(
                address,
                pin,
                FrontierSmartNodes.RadioId,
                cancellationToken)
            .ConfigureAwait(false);
        var firmware = await ReadOptionalTextAsync(
                address,
                pin,
                FrontierSmartNodes.FirmwareVersion,
                cancellationToken)
            .ConfigureAwait(false);
        return new FrontierSmartIdentity(
            string.IsNullOrWhiteSpace(name.Value) ? $"Frontier Smart {address}" : name.Value.Trim(),
            radioId,
            firmware);
    }

    public async Task<IReadOnlyList<FrontierSmartMode>> ReadModesAsync(
        string address,
        string pin,
        CancellationToken cancellationToken = default)
    {
        var xml = await SendAsync(
                CreateListUri(address, pin, FrontierSmartNodes.ValidModes, -1, 100),
                cancellationToken)
            .ConfigureAwait(false);
        return FrontierSmartXmlParser.ParseModes(xml);
    }

    public async Task<IReadOnlyList<FrontierSmartPreset>> ReadPresetsAsync(
        string address,
        string pin,
        CancellationToken cancellationToken = default)
    {
        var xml = await SendAsync(
                CreateListUri(address, pin, FrontierSmartNodes.Presets, -1, 100),
                cancellationToken)
            .ConfigureAwait(false);
        return FrontierSmartXmlParser.ParsePresets(xml);
    }

    public async Task<FrontierSmartValue> GetAsync(
        string address,
        string pin,
        string node,
        CancellationToken cancellationToken = default)
    {
        var xml = await SendAsync(CreateGetUri(address, pin, node), cancellationToken)
            .ConfigureAwait(false);
        return FrontierSmartXmlParser.ParseValue(node, xml);
    }

    public async Task<IReadOnlyDictionary<string, FrontierSmartValue>> GetMultipleAsync(
        string address,
        string pin,
        IReadOnlyCollection<string> nodes,
        CancellationToken cancellationToken = default)
    {
        if (nodes.Count == 0) throw new ArgumentException("Podaj co najmniej jeden węzeł FSAPI.", nameof(nodes));
        var uri = CreateMultipleUri(address, pin, nodes);
        var xml = await SendAsync(uri, cancellationToken).ConfigureAwait(false);
        return FrontierSmartXmlParser.ParseMultiple(xml);
    }

    public Task SetPowerAsync(string address, string pin, bool enabled, CancellationToken cancellationToken = default) =>
        SetAsync(address, pin, FrontierSmartNodes.Power, enabled ? "1" : "0", cancellationToken);

    public Task SetMutedAsync(string address, string pin, bool muted, CancellationToken cancellationToken = default) =>
        SetAsync(address, pin, FrontierSmartNodes.Mute, muted ? "1" : "0", cancellationToken);

    public Task SetVolumeStepAsync(string address, string pin, int step, CancellationToken cancellationToken = default)
    {
        if (step is < 0 or > 255) throw new ArgumentOutOfRangeException(nameof(step));
        return SetAsync(
            address,
            pin,
            FrontierSmartNodes.Volume,
            step.ToString(CultureInfo.InvariantCulture),
            cancellationToken);
    }

    public Task SetModeAsync(string address, string pin, uint modeKey, CancellationToken cancellationToken = default) =>
        SetAsync(
            address,
            pin,
            FrontierSmartNodes.Mode,
            modeKey.ToString(CultureInfo.InvariantCulture),
            cancellationToken);

    public Task SendPlaybackCommandAsync(
        string address,
        string pin,
        FrontierSmartPlaybackCommand command,
        CancellationToken cancellationToken = default)
    {
        if (!Enum.IsDefined(command)) throw new ArgumentOutOfRangeException(nameof(command));
        return SetAsync(
            address,
            pin,
            FrontierSmartNodes.PlaybackControl,
            ((int)command).ToString(CultureInfo.InvariantCulture),
            cancellationToken);
    }

    public Task ActivatePresetAsync(
        string address,
        string pin,
        uint presetKey,
        CancellationToken cancellationToken = default) =>
        SetAsync(
            address,
            pin,
            FrontierSmartNodes.SelectPreset,
            presetKey.ToString(CultureInfo.InvariantCulture),
            cancellationToken);

    public Task SetPlaybackPositionAsync(
        string address,
        string pin,
        TimeSpan position,
        CancellationToken cancellationToken = default)
    {
        if (position < TimeSpan.Zero || position.TotalMilliseconds > uint.MaxValue)
            throw new ArgumentOutOfRangeException(nameof(position));
        return SetAsync(
            address,
            pin,
            FrontierSmartNodes.PlayPosition,
            ((uint)Math.Round(position.TotalMilliseconds, MidpointRounding.AwayFromZero))
                .ToString(CultureInfo.InvariantCulture),
            cancellationToken);
    }

    public async Task SetAsync(
        string address,
        string pin,
        string node,
        string value,
        CancellationToken cancellationToken = default)
    {
        var xml = await SendAsync(CreateSetUri(address, pin, node, value), cancellationToken)
            .ConfigureAwait(false);
        var status = FrontierSmartXmlParser.ParseStatus(xml);
        if (!status.Equals("FS_OK", StringComparison.Ordinal))
            throw new FrontierSmartProtocolException("Urządzenie Frontier Smart odrzuciło polecenie.", status);
    }

    public static Uri CreateGetUri(string address, string pin, string node) =>
        CreateNodeUri(address, pin, "GET", node, null);

    public static Uri CreateSetUri(string address, string pin, string node, string value) =>
        CreateNodeUri(address, pin, "SET", node, value);

    public static Uri CreateListUri(string address, string pin, string node, int start, int maximumItems)
    {
        var normalized = FrontierSmartAddressPolicy.Normalize(address);
        ValidatePin(pin);
        ValidateNode(node);
        if (start < -1) throw new ArgumentOutOfRangeException(nameof(start));
        if (maximumItems is < 1 or > 1000) throw new ArgumentOutOfRangeException(nameof(maximumItems));
        var builder = new UriBuilder(Uri.UriSchemeHttp, normalized)
        {
            Path = $"/fsapi/LIST_GET_NEXT/{node}/{start.ToString(CultureInfo.InvariantCulture)}",
            Query = $"pin={Uri.EscapeDataString(pin)}&maxItems={maximumItems.ToString(CultureInfo.InvariantCulture)}"
        };
        return builder.Uri;
    }

    public static Uri CreateMultipleUri(
        string address,
        string pin,
        IEnumerable<string> nodes)
    {
        var normalized = FrontierSmartAddressPolicy.Normalize(address);
        ValidatePin(pin);
        var nodeArray = nodes.Distinct(StringComparer.Ordinal).ToArray();
        if (nodeArray.Length == 0) throw new ArgumentException("Podaj co najmniej jeden węzeł FSAPI.", nameof(nodes));
        foreach (var node in nodeArray) ValidateNode(node);
        var query = new StringBuilder($"pin={Uri.EscapeDataString(pin)}");
        foreach (var node in nodeArray)
            query.Append("&node=").Append(Uri.EscapeDataString(node));
        var builder = new UriBuilder(Uri.UriSchemeHttp, normalized)
        {
            Path = "/fsapi/GET_MULTIPLE",
            Query = query.ToString()
        };
        return builder.Uri;
    }

    public void Dispose()
    {
        if (ownsClient) client.Dispose();
    }

    private static HttpClient CreateClient(HttpMessageHandler handler)
    {
        var result = new HttpClient(handler)
        {
            Timeout = TimeSpan.FromSeconds(6),
            MaxResponseContentBufferSize = MaximumResponseBytes
        };
        result.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("AMC", "0.1"));
        return result;
    }

    private async Task<string> SendAsync(Uri uri, CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, uri)
        {
            Version = HttpVersion.Version11,
            VersionPolicy = HttpVersionPolicy.RequestVersionOrLower
        };
        using var response = await client.SendAsync(
                request,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken)
            .ConfigureAwait(false);
        if (response.StatusCode == HttpStatusCode.Forbidden)
            throw new FrontierSmartProtocolException("Urządzenie odrzuciło PIN.");
        response.EnsureSuccessStatusCode();
        return await ReadBoundedResponseAsync(response, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<string> ReadBoundedResponseAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        if (response.Content.Headers.ContentLength is > MaximumResponseBytes)
            throw new IOException("Odpowiedź urządzenia Frontier Smart jest zbyt duża.");
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken)
            .ConfigureAwait(false);
        using var memory = new MemoryStream();
        var buffer = new byte[8192];
        while (true)
        {
            var count = await stream.ReadAsync(buffer, cancellationToken).ConfigureAwait(false);
            if (count == 0) break;
            if (memory.Length + count > MaximumResponseBytes)
                throw new IOException("Odpowiedź urządzenia Frontier Smart jest zbyt duża.");
            memory.Write(buffer, 0, count);
        }
        return Encoding.UTF8.GetString(memory.ToArray()).TrimStart('\uFEFF');
    }

    private static Uri CreateNodeUri(string address, string pin, string operation, string node, string? value)
    {
        var normalized = FrontierSmartAddressPolicy.Normalize(address);
        ValidatePin(pin);
        ValidateNode(node);
        var query = $"pin={Uri.EscapeDataString(pin)}";
        if (value is not null) query += $"&value={Uri.EscapeDataString(value)}";
        var builder = new UriBuilder(Uri.UriSchemeHttp, normalized)
        {
            Path = $"/fsapi/{operation}/{node}",
            Query = query
        };
        return builder.Uri;
    }

    private static void ValidatePin(string pin)
    {
        if (string.IsNullOrWhiteSpace(pin)
            || pin.Length > 16
            || pin.Any(character => !char.IsAsciiDigit(character)))
        {
            throw new ArgumentException("PIN urządzenia musi zawierać od 1 do 16 cyfr.", nameof(pin));
        }
    }

    private static void ValidateNode(string node)
    {
        if (string.IsNullOrWhiteSpace(node)
            || node.Length > 200
            || node.Any(character => !(char.IsAsciiLetterOrDigit(character) || character is '.' or '_' or '-')))
        {
            throw new ArgumentException("Nieprawidłowa nazwa węzła FSAPI.", nameof(node));
        }
    }

    private static TimeSpan? Milliseconds(uint? value) =>
        value is null ? null : TimeSpan.FromMilliseconds(value.Value);

    private async Task<IReadOnlyDictionary<string, FrontierSmartValue>> ReadSnapshotNodesIndividuallyAsync(
        string address,
        string pin,
        CancellationToken cancellationToken)
    {
        var fallback = new Dictionary<string, FrontierSmartValue>(StringComparer.Ordinal);
        foreach (var node in SnapshotNodes)
        {
            try
            {
                fallback[node] = await GetAsync(address, pin, node, cancellationToken)
                    .ConfigureAwait(false);
            }
            catch (HttpRequestException exception) when (exception.StatusCode == HttpStatusCode.NotFound)
            {
                fallback[node] = new FrontierSmartValue(node, "FS_NODE_DOES_NOT_EXIST", null, null);
            }
        }
        return fallback;
    }

    private async Task<string> ReadOptionalTextAsync(
        string address,
        string pin,
        string node,
        CancellationToken cancellationToken)
    {
        try
        {
            var value = await GetAsync(address, pin, node, cancellationToken).ConfigureAwait(false);
            return value.Success && !string.IsNullOrWhiteSpace(value.Value)
                ? value.Value.Trim()
                : string.Empty;
        }
        catch (HttpRequestException exception) when (exception.StatusCode == HttpStatusCode.NotFound)
        {
            return string.Empty;
        }
    }
}

public static class FrontierSmartAddressPolicy
{
    public static bool TryNormalize(string? value, out string normalized)
    {
        normalized = string.Empty;
        if (string.IsNullOrWhiteSpace(value)
            || !IPAddress.TryParse(value.Trim().Trim('[', ']'), out var address)
            || !IsLocal(address))
        {
            return false;
        }
        normalized = address.ToString();
        return true;
    }

    public static string Normalize(string value)
    {
        if (!TryNormalize(value, out var normalized))
            throw new ArgumentException("Podaj lokalny adres IP urządzenia Frontier Smart.", nameof(value));
        return normalized;
    }

    public static bool IsLocal(IPAddress address)
    {
        if (IPAddress.IsLoopback(address)) return true;
        if (address.IsIPv4MappedToIPv6) address = address.MapToIPv4();
        var bytes = address.GetAddressBytes();
        if (address.AddressFamily == AddressFamily.InterNetwork)
        {
            return bytes[0] == 10
                || bytes[0] == 172 && bytes[1] is >= 16 and <= 31
                || bytes[0] == 192 && bytes[1] == 168
                || bytes[0] == 169 && bytes[1] == 254;
        }
        return address.AddressFamily == AddressFamily.InterNetworkV6
            && (address.IsIPv6LinkLocal || (bytes[0] & 0xFE) == 0xFC);
    }
}
