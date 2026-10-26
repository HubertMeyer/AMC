using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public interface IFrontierSmartDiscoveryService
{
    Task<IReadOnlyList<string>> DiscoverAddressesAsync(
        TimeSpan? duration = null,
        CancellationToken cancellationToken = default);
}

public sealed class FrontierSmartDiscoveryService : IFrontierSmartDiscoveryService
{
    public const string ServiceType = "urn:schemas-frontier-silicon-com:fs_reference:fsapi:1";
    private static readonly string[] SearchTargets = [ServiceType, "ssdp:all"];
    private static readonly IPEndPoint MulticastEndpoint =
        new(IPAddress.Parse("239.255.255.250"), 1900);

    public async Task<IReadOnlyList<string>> DiscoverAddressesAsync(
        TimeSpan? duration = null,
        CancellationToken cancellationToken = default)
    {
        var addresses = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var localAddresses = NetworkInterface.GetAllNetworkInterfaces()
            .Where(adapter => adapter.OperationalStatus == OperationalStatus.Up
                && adapter.NetworkInterfaceType is not NetworkInterfaceType.Loopback
                && adapter.NetworkInterfaceType is not NetworkInterfaceType.Tunnel)
            .SelectMany(adapter => adapter.GetIPProperties().UnicastAddresses)
            .Select(entry => entry.Address)
            .Where(address => address.AddressFamily == AddressFamily.InterNetwork)
            .Distinct()
            .ToArray();
        if (localAddresses.Length == 0) localAddresses = [IPAddress.Any];

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(duration ?? TimeSpan.FromSeconds(5));
        var tasks = localAddresses.Select(address =>
            DiscoverOnInterfaceSafelyAsync(address, addresses, timeout.Token));
        await Task.WhenAll(tasks).ConfigureAwait(false);
        cancellationToken.ThrowIfCancellationRequested();
        return addresses.OrderBy(address => address, StringComparer.OrdinalIgnoreCase).ToArray();
    }

    public static bool TryParseResponse(string response, out string address) =>
        TryParseResponse(response, null, out address);

    public static bool TryParseResponse(
        string response,
        IPAddress? responseAddress,
        out string address)
    {
        address = string.Empty;
        string? location = null;
        string? serviceType = null;
        string? uniqueServiceName = null;
        foreach (var line in response.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries))
        {
            var separator = line.IndexOf(':');
            if (separator <= 0) continue;
            var name = line[..separator].Trim();
            var value = line[(separator + 1)..].Trim();
            if (name.Equals("LOCATION", StringComparison.OrdinalIgnoreCase)) location = value;
            if (name.Equals("ST", StringComparison.OrdinalIgnoreCase)) serviceType = value;
            if (name.Equals("USN", StringComparison.OrdinalIgnoreCase)) uniqueServiceName = value;
        }
        var identifiesFsApi = serviceType?.Equals(ServiceType, StringComparison.OrdinalIgnoreCase) == true
            || uniqueServiceName?.Contains(ServiceType, StringComparison.OrdinalIgnoreCase) == true;
        if (!identifiesFsApi)
        {
            return false;
        }
        if (Uri.TryCreate(location, UriKind.Absolute, out var uri)
            && uri.Scheme is "http" or "https"
            && FrontierSmartAddressPolicy.TryNormalize(uri.Host, out address))
        {
            return true;
        }
        return responseAddress is not null
            && FrontierSmartAddressPolicy.TryNormalize(responseAddress.ToString(), out address);
    }

    private static async Task DiscoverOnInterfaceSafelyAsync(
        IPAddress localAddress,
        HashSet<string> addresses,
        CancellationToken cancellationToken)
    {
        try
        {
            await DiscoverOnInterfaceAsync(localAddress, addresses, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            // Zwykły koniec ograniczonego okna wykrywania.
        }
        catch (SocketException)
        {
            // Niedostępna karta, filtr multicastu albo profil zapory nie może
            // unieważnić odpowiedzi odebranych na pozostałych interfejsach.
        }
        catch (ObjectDisposedException)
        {
            // Gniazdo mogło zostać zamknięte przez anulowanie okna.
        }
    }

    private static async Task DiscoverOnInterfaceAsync(
        IPAddress localAddress,
        HashSet<string> addresses,
        CancellationToken cancellationToken)
    {
        using var socket = new UdpClient(new IPEndPoint(localAddress, 0));
        socket.Client.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.MulticastTimeToLive, 2);
        var sendTask = SendSearchBurstsAsync(socket, cancellationToken);
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
            var response = Encoding.UTF8.GetString(result.Buffer);
            if (!TryParseResponse(response, result.RemoteEndPoint.Address, out var address)) continue;
            lock (addresses) addresses.Add(address);
        }
        await ObserveSendTaskAsync(sendTask).ConfigureAwait(false);
    }

    private static async Task SendSearchBurstsAsync(
        UdpClient socket,
        CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < 3; attempt++)
        {
            foreach (var target in SearchTargets)
            {
                var message = Encoding.ASCII.GetBytes(
                    "M-SEARCH * HTTP/1.1\r\n" +
                    "HOST: 239.255.255.250:1900\r\n" +
                    "MAN: \"ssdp:discover\"\r\n" +
                    "MX: 2\r\n" +
                    $"ST: {target}\r\n\r\n");
                await socket.SendAsync(message, MulticastEndpoint, cancellationToken)
                    .ConfigureAwait(false);
            }
            if (attempt < 2)
                await Task.Delay(TimeSpan.FromMilliseconds(650), cancellationToken)
                    .ConfigureAwait(false);
        }
    }

    private static async Task ObserveSendTaskAsync(Task sendTask)
    {
        try
        {
            await sendTask.ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
        }
    }
}
