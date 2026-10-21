using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;

namespace AccessibleMediaController.Core.Devices.FrontierSmart;

public sealed class FrontierSmartDiscoveryService
{
    public const string ServiceType =
        "urn:schemas-frontier-silicon-com:fs_reference:fsapi:1";
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
        timeout.CancelAfter(duration ?? TimeSpan.FromSeconds(3));
        var tasks = localAddresses.Select(address =>
            DiscoverOnInterfaceAsync(address, addresses, timeout.Token));
        try
        {
            await Task.WhenAll(tasks).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            // Zwykły koniec ograniczonego okna wykrywania.
        }
        return addresses.OrderBy(address => address, StringComparer.OrdinalIgnoreCase).ToArray();
    }

    public static bool TryParseResponse(string response, out string address)
    {
        address = string.Empty;
        string? location = null;
        string? serviceType = null;
        foreach (var line in response.Split(['\r', '\n'], StringSplitOptions.RemoveEmptyEntries))
        {
            var separator = line.IndexOf(':');
            if (separator <= 0) continue;
            var name = line[..separator].Trim();
            var value = line[(separator + 1)..].Trim();
            if (name.Equals("LOCATION", StringComparison.OrdinalIgnoreCase)) location = value;
            if (name.Equals("ST", StringComparison.OrdinalIgnoreCase)) serviceType = value;
        }
        if (!string.IsNullOrWhiteSpace(serviceType)
            && !serviceType.Equals(ServiceType, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        if (!Uri.TryCreate(location, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https"))
        {
            return false;
        }
        return FrontierSmartAddressPolicy.TryNormalize(uri.Host, out address);
    }

    private static async Task DiscoverOnInterfaceAsync(
        IPAddress localAddress,
        HashSet<string> addresses,
        CancellationToken cancellationToken)
    {
        using var socket = new UdpClient(new IPEndPoint(localAddress, 0));
        socket.Client.SetSocketOption(
            SocketOptionLevel.IP, SocketOptionName.MulticastTimeToLive, 2);
        var message = Encoding.ASCII.GetBytes(
            "M-SEARCH * HTTP/1.1\r\n" +
            "HOST: 239.255.255.250:1900\r\n" +
            "MAN: \"ssdp:discover\"\r\n" +
            "MX: 2\r\n" +
            $"ST: {ServiceType}\r\n\r\n");
        await socket.SendAsync(message, MulticastEndpoint, cancellationToken)
            .ConfigureAwait(false);
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
            if (!TryParseResponse(response, out var address)) continue;
            lock (addresses) addresses.Add(address);
        }
    }
}
