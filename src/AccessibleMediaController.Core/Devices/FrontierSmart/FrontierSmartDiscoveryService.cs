using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Xml;
using System.Xml.Linq;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public sealed record FrontierSmartDiscoveredDevice(
    string Address,
    string DisplayName,
    string FirmwareVersion);

public sealed class FrontierSmartDiscoveryService : IDisposable
{
    public const string LegacyServiceType =
        "urn:schemas-frontier-silicon-com:fs_reference:fsapi:1";
    public const string UndokServiceType =
        "urn:schemas-frontier-silicon-com:undok:fsapi:1";
    public const string ServiceType = LegacyServiceType;
    private const int MaximumDescriptionBytes = 64 * 1024;
    private static readonly string[] DiscoveryServiceTypes =
    [
        LegacyServiceType,
        UndokServiceType
    ];
    private static readonly IPEndPoint MulticastEndpoint =
        new(IPAddress.Parse("239.255.255.250"), 1900);

    private readonly Func<IReadOnlyList<IPAddress>> interfaceAddressProvider;
    private readonly Func<IPAddress, CancellationToken, Task<IReadOnlyList<string>>>
        responseProvider;
    private readonly HttpClient httpClient;

    public FrontierSmartDiscoveryService()
        : this(
            GetLocalInterfaceAddresses,
            DiscoverOnInterfaceAsync,
            new SocketsHttpHandler { AllowAutoRedirect = false })
    {
    }

    public FrontierSmartDiscoveryService(
        Func<IReadOnlyList<IPAddress>> interfaceAddressProvider,
        Func<IPAddress, CancellationToken, Task<IReadOnlyList<string>>> responseProvider,
        HttpMessageHandler descriptionHandler)
    {
        this.interfaceAddressProvider = interfaceAddressProvider
            ?? throw new ArgumentNullException(nameof(interfaceAddressProvider));
        this.responseProvider = responseProvider
            ?? throw new ArgumentNullException(nameof(responseProvider));
        httpClient = new HttpClient(
            descriptionHandler ?? throw new ArgumentNullException(nameof(descriptionHandler)),
            disposeHandler: true)
        {
            Timeout = Timeout.InfiniteTimeSpan
        };
    }

    public async Task<IReadOnlyList<FrontierSmartDiscoveredDevice>> DiscoverDevicesAsync(
        TimeSpan? duration = null,
        CancellationToken cancellationToken = default)
    {
        var localAddresses = interfaceAddressProvider()
            .Where(address => address.AddressFamily == AddressFamily.InterNetwork)
            .Distinct()
            .ToArray();
        if (localAddresses.Length == 0) localAddresses = [IPAddress.Any];

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(duration ?? TimeSpan.FromSeconds(3));
        var scans = localAddresses.Select(address => ScanInterfaceSafelyAsync(
            address,
            timeout.Token,
            cancellationToken));
        var scanResults = await Task.WhenAll(scans).ConfigureAwait(false);
        cancellationToken.ThrowIfCancellationRequested();

        if (scanResults.All(result => result.Failed))
            throw new IOException(
                "Nie udało się wysłać zapytania SSDP przez aktywne interfejsy sieciowe.");

        var candidates = scanResults
            .SelectMany(result => result.Responses)
            .Select(response => TryParseResponse(
                response, out var address, out var location)
                ? new DiscoveryCandidate(address, location!)
                : null)
            .Where(candidate => candidate is not null)
            .Cast<DiscoveryCandidate>()
            .DistinctBy(candidate => candidate.Address, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        var descriptions = await Task.WhenAll(candidates.Select(candidate =>
            DescribeCandidateSafelyAsync(candidate, cancellationToken)))
            .ConfigureAwait(false);
        cancellationToken.ThrowIfCancellationRequested();
        return descriptions
            .Where(device => device is not null)
            .Cast<FrontierSmartDiscoveredDevice>()
            .OrderBy(device => device.DisplayName, StringComparer.CurrentCultureIgnoreCase)
            .ThenBy(device => device.Address, StringComparer.OrdinalIgnoreCase)
            .ToArray();
    }

    public async Task<IReadOnlyList<string>> DiscoverAddressesAsync(
        TimeSpan? duration = null,
        CancellationToken cancellationToken = default) =>
        (await DiscoverDevicesAsync(duration, cancellationToken).ConfigureAwait(false))
        .Select(device => device.Address)
        .ToArray();

    public async Task<FrontierSmartDiscoveredDevice> IdentifyAddressAsync(
        string address,
        CancellationToken cancellationToken = default)
    {
        var normalized = FrontierSmartAddressPolicy.Normalize(address);
        var location = new UriBuilder(Uri.UriSchemeHttp, normalized, 80, "device").Uri;
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(3));
        return await ReadDescriptionAsync(
            new DiscoveryCandidate(normalized, location),
            timeout.Token).ConfigureAwait(false);
    }

    public static bool TryParseResponse(string response, out string address) =>
        TryParseResponse(response, out address, out _);

    public static bool TryParseResponse(
        string response,
        out string address,
        out Uri? location)
    {
        address = string.Empty;
        location = null;
        string? locationValue = null;
        string? serviceType = null;
        foreach (var line in response.Split(
                     ['\r', '\n'], StringSplitOptions.RemoveEmptyEntries))
        {
            var separator = line.IndexOf(':');
            if (separator <= 0) continue;
            var name = line[..separator].Trim();
            var value = line[(separator + 1)..].Trim();
            if (name.Equals("LOCATION", StringComparison.OrdinalIgnoreCase))
                locationValue = value;
            if (name.Equals("ST", StringComparison.OrdinalIgnoreCase))
                serviceType = value;
        }
        if (string.IsNullOrWhiteSpace(serviceType)
            || !DiscoveryServiceTypes.Contains(
                serviceType,
                StringComparer.OrdinalIgnoreCase))
        {
            return false;
        }
        if (!Uri.TryCreate(locationValue, UriKind.Absolute, out var parsedLocation)
            || parsedLocation.Scheme is not ("http" or "https")
            || !FrontierSmartAddressPolicy.TryNormalize(
                parsedLocation.Host, out var normalizedAddress))
        {
            return false;
        }
        address = normalizedAddress;
        location = parsedLocation;
        return true;
    }

    public static bool TryParseDescription(
        string xml,
        string expectedAddress,
        out FrontierSmartDiscoveredDevice? device)
    {
        device = null;
        if (!FrontierSmartAddressPolicy.TryNormalize(
                expectedAddress, out var normalizedAddress))
        {
            return false;
        }
        try
        {
            using var text = new StringReader(xml);
            using var reader = XmlReader.Create(text, new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit,
                XmlResolver = null,
                MaxCharactersInDocument = MaximumDescriptionBytes
            });
            var document = XDocument.Load(reader, LoadOptions.None);
            if (!string.Equals(
                    document.Root?.Name.LocalName,
                    "netRemote",
                    StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }

            var friendlyName = CleanDescriptionValue(FirstElementValue(
                document, "friendlyName"));
            var firmware = CleanDescriptionValue(FirstElementValue(
                document, "version"));
            var webFsApi = FirstElementValue(document, "webfsapi");
            if (friendlyName.Length == 0
                || !Uri.TryCreate(webFsApi, UriKind.Absolute, out var apiUri)
                || apiUri.Scheme is not ("http" or "https")
                || !FrontierSmartAddressPolicy.TryNormalize(
                    apiUri.Host, out var apiAddress)
                || !string.Equals(
                    apiAddress, normalizedAddress, StringComparison.OrdinalIgnoreCase)
                || !apiUri.AbsolutePath.StartsWith(
                    "/fsapi", StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }

            device = new FrontierSmartDiscoveredDevice(
                normalizedAddress,
                friendlyName,
                firmware);
            return true;
        }
        catch (XmlException)
        {
            return false;
        }
    }

    private static async Task<IReadOnlyList<string>> DiscoverOnInterfaceAsync(
        IPAddress localAddress,
        CancellationToken cancellationToken)
    {
        var responses = new List<string>();
        using var socket = new UdpClient(new IPEndPoint(localAddress, 0));
        socket.Client.SetSocketOption(
            SocketOptionLevel.IP, SocketOptionName.MulticastTimeToLive, 2);
        // Starsze moduły Frontier odpowiadają na fs_reference, a nowsze
        // urządzenia sterowane przez UNDOK (m.in. Teufel RADIO 3SIXTY)
        // reklamują wyłącznie undok:fsapi. Dwie krótkie serie ograniczają
        // utratę pojedynczego pakietu w Wi-Fi bez skanowania całej podsieci.
        for (var attempt = 0; attempt < 2; attempt++)
        {
            foreach (var serviceType in DiscoveryServiceTypes)
            {
                var message = Encoding.ASCII.GetBytes(
                    "M-SEARCH * HTTP/1.1\r\n" +
                    "HOST: 239.255.255.250:1900\r\n" +
                    "MAN: \"ssdp:discover\"\r\n" +
                    "MX: 2\r\n" +
                    $"ST: {serviceType}\r\n\r\n");
                await socket.SendAsync(message, MulticastEndpoint, cancellationToken)
                    .ConfigureAwait(false);
            }
            if (attempt == 0)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(250), cancellationToken)
                    .ConfigureAwait(false);
            }
        }
        while (!cancellationToken.IsCancellationRequested)
        {
            UdpReceiveResult result;
            try
            {
                result = await socket.ReceiveAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            responses.Add(Encoding.UTF8.GetString(result.Buffer));
        }
        return responses;
    }

    private async Task<FrontierSmartDiscoveredDevice?> DescribeCandidateSafelyAsync(
        DiscoveryCandidate candidate,
        CancellationToken cancellationToken)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(2));
        try
        {
            return await ReadDescriptionAsync(candidate, timeout.Token)
                .ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            return null;
        }
        catch (Exception exception) when (IsExpectedDescriptionFailure(exception))
        {
            return null;
        }
    }

    private async Task<FrontierSmartDiscoveredDevice> ReadDescriptionAsync(
        DiscoveryCandidate candidate,
        CancellationToken cancellationToken)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, candidate.Location);
        using var response = await httpClient.SendAsync(
            request,
            HttpCompletionOption.ResponseHeadersRead,
            cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        if (response.Content.Headers.ContentLength is > MaximumDescriptionBytes)
            throw new IOException("Opis urządzenia Frontier Smart jest zbyt duży.");

        await using var stream = await response.Content.ReadAsStreamAsync(
            cancellationToken).ConfigureAwait(false);
        using var memory = new MemoryStream();
        var buffer = new byte[8192];
        while (true)
        {
            var read = await stream.ReadAsync(buffer, cancellationToken)
                .ConfigureAwait(false);
            if (read == 0) break;
            if (memory.Length + read > MaximumDescriptionBytes)
                throw new IOException("Opis urządzenia Frontier Smart jest zbyt duży.");
            memory.Write(buffer, 0, read);
        }
        var xml = Encoding.UTF8.GetString(memory.ToArray());
        if (!TryParseDescription(xml, candidate.Address, out var device)
            || device is null)
        {
            throw new FormatException(
                "Odpowiedź nie jest potwierdzonym opisem urządzenia Frontier Smart.");
        }
        return device;
    }

    private async Task<InterfaceScanResult> ScanInterfaceSafelyAsync(
        IPAddress address,
        CancellationToken timeoutToken,
        CancellationToken callerToken)
    {
        try
        {
            var responses = await responseProvider(address, timeoutToken)
                .ConfigureAwait(false);
            return new InterfaceScanResult(responses, Failed: false);
        }
        catch (OperationCanceledException) when (!callerToken.IsCancellationRequested)
        {
            return new InterfaceScanResult([], Failed: false);
        }
        catch (Exception exception) when (exception is SocketException
            or NetworkInformationException or IOException)
        {
            return new InterfaceScanResult([], Failed: true);
        }
    }

    private static IReadOnlyList<IPAddress> GetLocalInterfaceAddresses() =>
        NetworkInterface.GetAllNetworkInterfaces()
            .Where(adapter => adapter.OperationalStatus == OperationalStatus.Up
                && adapter.NetworkInterfaceType is not NetworkInterfaceType.Loopback
                && adapter.NetworkInterfaceType is not NetworkInterfaceType.Tunnel)
            .SelectMany(adapter => adapter.GetIPProperties().UnicastAddresses)
            .Select(entry => entry.Address)
            .Where(address => address.AddressFamily == AddressFamily.InterNetwork)
            .Distinct()
            .ToArray();

    private static string? FirstElementValue(XDocument document, string localName) =>
        document.Descendants().FirstOrDefault(element => string.Equals(
            element.Name.LocalName,
            localName,
            StringComparison.OrdinalIgnoreCase))?.Value;

    private static string CleanDescriptionValue(string? value)
    {
        var text = new string((value ?? string.Empty)
            .Trim()
            .Where(character => !char.IsControl(character))
            .ToArray());
        return text.Length > 128 ? text[..128] : text;
    }

    private static bool IsExpectedDescriptionFailure(Exception exception) =>
        exception is HttpRequestException or IOException or FormatException
            or ArgumentException;

    public void Dispose() => httpClient.Dispose();

    private sealed record DiscoveryCandidate(string Address, Uri Location);
    private sealed record InterfaceScanResult(
        IReadOnlyList<string> Responses,
        bool Failed);
}
