using System.Text.Json;
using System.ComponentModel;
using System.Net;
using System.Net.Sockets;
using AccessibleMediaController.Core.Devices.FrontierSmart;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class FrontierSmartContractTests
{
    public static void Run()
    {
        AddressPolicyAcceptsOnlyLocalIpAddresses();
        DiscoveryAcceptsLegacyAndUndokServiceTypes();
        DiscoveryRequiresVerifiedDescriptionAndUserFacingName();
        DiscoveryUsesAllInterfacesAndSurvivesPartialFailure();
        DiscoveryHonorsTimeoutAndCancellation();
        SnapshotFallsBackWhenDeviceRejectsGetMultiple();
        PresetsEnableNavigationAndWaitUntilItIsReady();
        XmlParserReadsTypedValuesAndRejectsDtd();
        ListsUseOnlyIntentionalLabels();
        DeviceAndSnapshotResultsDoNotExposeAddressOrRuntimeTypes();
        TransportAndNumericArgumentsAreStrict();
        PinDeletionFailsClosedExceptWhenCredentialIsAlreadyMissing();
    }

    private static void PinDeletionFailsClosedExceptWhenCredentialIsAlreadyMissing()
    {
        LiteFrontierSmartPinStore.ThrowIfDeleteFailed(true, 5);
        LiteFrontierSmartPinStore.ThrowIfDeleteFailed(false, 1168);

        Win32Exception? failure = null;
        try
        {
            LiteFrontierSmartPinStore.ThrowIfDeleteFailed(false, 5);
        }
        catch (Win32Exception error)
        {
            failure = error;
        }

        Check(failure is not null && failure.NativeErrorCode == 5,
            "błąd usunięcia poświadczenia został zignorowany");
        Check(failure!.Message.StartsWith(
                "Nie udało się bezpiecznie usunąć PIN-u urządzenia.",
                StringComparison.Ordinal),
            "błąd usunięcia PIN-u nie ma bezpiecznego komunikatu użytkowego");
    }

    private static void SnapshotFallsBackWhenDeviceRejectsGetMultiple()
    {
        var handler = new GetMultipleRejectedHandler();
        using var client = new FrontierSmartClient(handler);

        var snapshot = client.ReadSnapshotAsync("192.168.0.132", "1234")
            .GetAwaiter().GetResult();

        Check(handler.MultipleRequests == 1,
            "klient nie spróbował zbiorczego odczytu FSAPI");
        Check(handler.SingleRequests > 1,
            "odmowa GET_MULTIPLE nie uruchomiła pojedynczych GET");
        Check(snapshot.DisplayName == "Radio testowe",
            "fallback pojedynczych GET zgubił nazwę urządzenia");
    }

    private static void PresetsEnableNavigationAndWaitUntilItIsReady()
    {
        var handler = new NavigationRequiredPresetHandler();
        using var client = new FrontierSmartClient(handler);

        var presets = client.ReadPresetsAsync("192.168.0.132", "1234")
            .GetAwaiter().GetResult();

        Check(presets.Count == 1 && presets[0].DisplayName == "Trójka",
            "odczyt po przygotowaniu nawigacji zgubił preset");
        Check(handler.Paths.SequenceEqual(new[]
            {
                "/fsapi/GET/netRemote.nav.state",
                "/fsapi/SET/netRemote.nav.state",
                "/fsapi/GET/netRemote.nav.status",
                "/fsapi/GET/netRemote.nav.status",
                "/fsapi/LIST_GET_NEXT/netRemote.nav.presets/-1"
            }),
            "lista presetów została pobrana przed włączeniem i przygotowaniem nawigacji");
        Check(handler.NavigationEnableHadValueOne,
            "włączenie nawigacji nie przekazało wartości 1");
    }

    private static void DiscoveryAcceptsLegacyAndUndokServiceTypes()
    {
        foreach (var serviceType in new[]
                 {
                     FrontierSmartDiscoveryService.LegacyServiceType,
                     FrontierSmartDiscoveryService.UndokServiceType
                 })
        {
            var response =
                "HTTP/1.1 200 OK\r\n"
                + "LOCATION: http://192.168.0.132:80/device\r\n"
                + $"ST: {serviceType}\r\n\r\n";
            Check(FrontierSmartDiscoveryService.TryParseResponse(
                    response, out var address),
                $"odrzucono odpowiedź SSDP {serviceType}");
            Check(address == "192.168.0.132",
                "wykrywanie nie zachowało lokalnego adresu radia");
        }

        const string unrelated =
            "HTTP/1.1 200 OK\r\n"
            + "LOCATION: http://192.168.0.132:49152/description.xml\r\n"
            + "ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n";
        Check(!FrontierSmartDiscoveryService.TryParseResponse(
                unrelated, out _),
            "wykrywanie przyjęło niezwiązany renderer UPnP");

        const string missingServiceType =
            "HTTP/1.1 200 OK\r\n"
            + "LOCATION: http://192.168.0.132:80/device\r\n\r\n";
        Check(!FrontierSmartDiscoveryService.TryParseResponse(
                missingServiceType, out _),
            "wykrywanie przyjęło odpowiedź bez potwierdzonego typu usługi");
    }

    private static void DiscoveryRequiresVerifiedDescriptionAndUserFacingName()
    {
        const string description =
            "<netRemote><friendlyName>Teufel RADIO 3SIXTY</friendlyName>"
            + "<version>ir-mmi-FS2026-0500-088</version>"
            + "<webfsapi>http://192.168.0.132:80/fsapi</webfsapi></netRemote>";
        Check(FrontierSmartDiscoveryService.TryParseDescription(
                description, "192.168.0.132", out var device)
              && device?.DisplayName == "Teufel RADIO 3SIXTY"
              && device.FirmwareVersion == "ir-mmi-FS2026-0500-088",
            "opis urządzenia nie zwrócił użytkowej nazwy i firmware");

        const string wrongAddress =
            "<netRemote><friendlyName>Fałszywe radio</friendlyName>"
            + "<webfsapi>http://192.168.0.200/fsapi</webfsapi></netRemote>";
        Check(!FrontierSmartDiscoveryService.TryParseDescription(
                wrongAddress, "192.168.0.132", out _),
            "opis z obcą bazą FSAPI został uznany za wykryte urządzenie");

        const string withDtd =
            "<!DOCTYPE x [<!ENTITY y SYSTEM \"file:///C:/Windows/win.ini\">]>"
            + "<netRemote><friendlyName>&y;</friendlyName>"
            + "<webfsapi>http://192.168.0.132/fsapi</webfsapi></netRemote>";
        Check(!FrontierSmartDiscoveryService.TryParseDescription(
                withDtd, "192.168.0.132", out _),
            "parser opisu urządzenia przyjął DTD");

        var json = JsonSerializer.Serialize(
            LiteFrontierSmartContract.CreateDiscoveryResult(
                [device!], "Wykryto urządzenie Teufel RADIO 3SIXTY."));
        using var payload = JsonDocument.Parse(json);
        var item = payload.RootElement.GetProperty("items")[0];
        Check(item.GetProperty("label").GetString() == "Teufel RADIO 3SIXTY"
              && !item.GetProperty("label").GetString()!.Contains("192.168."),
            "etykieta wyniku wykrywania zawiera adres zamiast użytkowej nazwy");
    }

    private static void DiscoveryUsesAllInterfacesAndSurvivesPartialFailure()
    {
        var first = IPAddress.Parse("192.168.10.2");
        var second = IPAddress.Parse("192.168.20.2");
        var calls = new List<IPAddress>();
        using var discovery = new FrontierSmartDiscoveryService(
            () => [first, second],
            (address, _) =>
            {
                calls.Add(address);
                if (address.Equals(first)) throw new SocketException();
                IReadOnlyList<string> responses =
                [
                    "HTTP/1.1 200 OK\r\n"
                    + "LOCATION: http://192.168.20.50/device\r\n"
                    + $"ST: {FrontierSmartDiscoveryService.UndokServiceType}\r\n\r\n"
                ];
                return Task.FromResult(responses);
            },
            new DeviceDescriptionHandler());

        var devices = discovery.DiscoverDevicesAsync(TimeSpan.FromMilliseconds(50))
            .GetAwaiter().GetResult();

        Check(calls.Count == 2 && calls.Contains(first) && calls.Contains(second),
            "wykrywanie nie użyło wszystkich aktywnych interfejsów");
        Check(devices.Count == 1
              && devices[0].DisplayName == "Radio z drugiego interfejsu",
            "awaria jednego interfejsu zgubiła prawidłowy wynik drugiego");
    }

    private static void DiscoveryHonorsTimeoutAndCancellation()
    {
        static async Task<IReadOnlyList<string>> WaitForCancellation(
            IPAddress _, CancellationToken cancellationToken)
        {
            await Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken);
            return [];
        }

        using var discovery = new FrontierSmartDiscoveryService(
            () => [IPAddress.Parse("192.168.30.2")],
            WaitForCancellation,
            new DeviceDescriptionHandler());
        var timedOut = discovery.DiscoverDevicesAsync(
            TimeSpan.FromMilliseconds(20)).GetAwaiter().GetResult();
        Check(timedOut.Count == 0,
            "ograniczony timeout wykrywania nie zwrócił pustego wyniku");

        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();
        try
        {
            discovery.DiscoverDevicesAsync(
                TimeSpan.FromSeconds(1), cancellation.Token)
                .GetAwaiter().GetResult();
            throw new InvalidOperationException(
                "anulowane wykrywanie zakończyło się jak zwykły pusty wynik");
        }
        catch (OperationCanceledException)
        {
        }
    }

    private static void AddressPolicyAcceptsOnlyLocalIpAddresses()
    {
        foreach (var accepted in new[]
                 {
                     "192.168.1.55", "10.20.30.40", "172.16.0.8", "127.0.0.1", "fe80::1"
                 })
        {
            Check(FrontierSmartAddressPolicy.TryNormalize(accepted, out _),
                $"odrzucono lokalny adres {accepted}");
        }
        foreach (var rejected in new[]
                 {
                     "8.8.8.8", "1.1.1.1", "radio.example", "https://192.168.1.55"
                 })
        {
            Check(!FrontierSmartAddressPolicy.TryNormalize(rejected, out _),
                $"przyjęto zewnętrzny albo niejawny adres {rejected}");
        }
    }

    private static void XmlParserReadsTypedValuesAndRejectsDtd()
    {
        var value = FrontierSmartXmlParser.ParseValue(
            FrontierSmartNodes.Volume,
            """<fsapiResponse><status>FS_OK</status><value><u8>17</u8></value></fsapiResponse>""");
        Check(value.Success && value.AsInt32() == 17 && value.ValueType == "u8",
            "parser nie odczytał typowanej wartości FSAPI");

        try
        {
            FrontierSmartXmlParser.ParseValue(
                FrontierSmartNodes.PlayName,
                """<!DOCTYPE x [<!ENTITY y SYSTEM "file:///C:/Windows/win.ini">]><fsapiResponse><status>FS_OK</status><value><c8_array>&y;</c8_array></value></fsapiResponse>""");
            throw new InvalidOperationException("parser przyjął DTD w odpowiedzi urządzenia");
        }
        catch (System.Xml.XmlException)
        {
        }
    }

    private static void ListsUseOnlyIntentionalLabels()
    {
        var modes = FrontierSmartXmlParser.ParseModes(
            """<fsapiResponse><status>FS_OK</status><item key="0"><field name="id"><c8_array>ir</c8_array></field><field name="label"><c8_array>Radio internetowe</c8_array></field><field name="selectable"><u8>1</u8></field><field name="streamable"><u8>1</u8></field><field name="modetype"><u8>0</u8></field></item></fsapiResponse>""");
        Check(modes.Count == 1 && modes[0].AccessibleLabel == "Radio internetowe",
            "tryb nie ma celowej etykiety użytkowej");

        var presets = FrontierSmartXmlParser.ParsePresets(
            """<fsapiResponse><status>FS_OK</status><item key="0"><field name="name"><c8_array>Trójka</c8_array></field></item></fsapiResponse>""");
        Check(presets.Count == 1 && presets[0].AccessibleLabel == "Trójka, preset 1",
            "preset nie ma celowej etykiety użytkowej");
    }

    private static void DeviceAndSnapshotResultsDoNotExposeAddressOrRuntimeTypes()
    {
        var device = new FrontierSmartDeviceSettings
        {
            Id = "technical-device-id",
            Address = "192.168.1.55",
            DisplayName = "Radio w salonie",
            FirmwareVersion = "ir-mmi-FS2026-0500-088"
        };
        var settings = new FrontierSmartSettings
        {
            SelectedDeviceId = device.Id,
            Devices = [device]
        };
        var devicesJson = JsonSerializer.Serialize(
            LiteFrontierSmartContract.CreateDevicesResult(settings));
        using var devices = JsonDocument.Parse(devicesJson);
        var item = devices.RootElement.GetProperty("items")[0];
        Check(item.GetProperty("title").GetString() == "Radio w salonie",
            "lista zgubiła nazwę urządzenia");
        Check(item.GetProperty("detail").GetString()
              == "Firmware ir-mmi-FS2026-0500-088",
            "lista zgubiła użytkowy opis firmware");
        Check(!devicesJson.Contains("192.168.1.55", StringComparison.Ordinal)
              && !devicesJson.Contains("FrontierSmartDeviceSettings", StringComparison.Ordinal),
            "adres albo typ obiektu wyciekł do listy urządzeń");

        var snapshot = new FrontierSmartSnapshot(
            "Radio w salonie", "radio-id", "firmware", true,
            8, 21, false, 0, 1, 2,
            "Trójka", "Audycja", "Polskie Radio", "", 
            TimeSpan.FromMinutes(60), TimeSpan.FromSeconds(15));
        var snapshotJson = JsonSerializer.Serialize(
            LiteFrontierSmartContract.CreateSnapshotResult(device, snapshot));
        using var payload = JsonDocument.Parse(snapshotJson);
        Check(payload.RootElement.GetProperty("title").GetString() == "Trójka",
            "migawka zgubiła tytuł");
        Check(payload.RootElement.GetProperty("volume").GetInt32() == 40,
            "migawka nie przeliczyła kroków głośności na procent");
        Check(payload.RootElement.GetProperty("playbackState").GetString()
              == "odtwarzanie",
            "migawka nie zmapowała stanu odtwarzania");
        Check(!snapshotJson.Contains("192.168.1.55", StringComparison.Ordinal)
              && !snapshotJson.Contains("FrontierSmartSnapshot", StringComparison.Ordinal),
            "adres albo typ obiektu wyciekł do migawki");
    }

    private static void TransportAndNumericArgumentsAreStrict()
    {
        foreach (var command in new[]
                 {
                     "toggle", "previous", "next", "setVolume", "volumeUp5",
                     "volumeDown5", "volumeUp1", "volumeDown1", "toggleMute", "togglePower"
                 })
        {
            using var accepted = JsonDocument.Parse(
                $$"""{"deviceId":"device-1","command":"{{command}}"}""");
            Check(LiteFrontierSmartContract.ReadTransportCommand(accepted.RootElement)
                  == command,
                $"odrzucono polecenie {command}");
        }
        using var invalidCommand = JsonDocument.Parse(
            """{"deviceId":"device-1","command":"shell"}""");
        ExpectLiteError(
            () => LiteFrontierSmartContract.ReadTransportCommand(invalidCommand.RootElement),
            "przyjęto nieznane polecenie transportu");

        using var acceptedVolume = JsonDocument.Parse("""{"volume":37}""");
        Check(LiteFrontierSmartContract.ReadVolume(acceptedVolume.RootElement) == 37,
            "odrzucono prawidłową głośność");
        using var invalidVolume = JsonDocument.Parse("""{"volume":137}""");
        ExpectLiteError(
            () => LiteFrontierSmartContract.ReadVolume(invalidVolume.RootElement),
            "przyjęto głośność poza zakresem");
    }

    private static void ExpectLiteError(Action action, string message)
    {
        try
        {
            action();
            throw new InvalidOperationException(message);
        }
        catch (LiteRequestException)
        {
        }
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed class DeviceDescriptionHandler : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            var address = request.RequestUri?.Host ?? "192.168.20.50";
            var name = address == "192.168.20.50"
                ? "Radio z drugiego interfejsu"
                : "Radio testowe";
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    $"<netRemote><friendlyName>{name}</friendlyName>"
                    + "<version>firmware-test</version>"
                    + $"<webfsapi>http://{address}/fsapi</webfsapi></netRemote>")
            });
        }
    }

    private sealed class GetMultipleRejectedHandler : HttpMessageHandler
    {
        public int MultipleRequests { get; private set; }
        public int SingleRequests { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            if (request.RequestUri?.AbsolutePath.EndsWith(
                    "/GET_MULTIPLE", StringComparison.Ordinal) is true)
            {
                MultipleRequests++;
                return Task.FromResult(new HttpResponseMessage(
                    System.Net.HttpStatusCode.BadRequest));
            }

            SingleRequests++;
            var value = request.RequestUri?.AbsolutePath.EndsWith(
                    FrontierSmartNodes.FriendlyName, StringComparison.Ordinal) is true
                ? "Radio testowe"
                : "1";
            return Task.FromResult(new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(
                    $"<fsapiResponse><status>FS_OK</status><value><c8_array>{value}</c8_array></value></fsapiResponse>")
            });
        }
    }

    private sealed class NavigationRequiredPresetHandler : HttpMessageHandler
    {
        private int statusReads;

        public List<string> Paths { get; } = [];
        public bool NavigationEnableHadValueOne { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            var uri = request.RequestUri
                ?? throw new InvalidOperationException("Żądanie testowe nie ma adresu.");
            Paths.Add(uri.AbsolutePath);
            string body;
            if (uri.AbsolutePath.EndsWith(
                    "/GET/netRemote.nav.state", StringComparison.Ordinal))
            {
                body = Value("0");
            }
            else if (uri.AbsolutePath.EndsWith(
                         "/SET/netRemote.nav.state", StringComparison.Ordinal))
            {
                NavigationEnableHadValueOne = uri.Query.Contains(
                    "value=1", StringComparison.Ordinal);
                body = Status();
            }
            else if (uri.AbsolutePath.EndsWith(
                         "/GET/netRemote.nav.status", StringComparison.Ordinal))
            {
                statusReads++;
                body = statusReads >= 2
                    ? Value("1")
                    : "<fsapiResponse><status>FS_NODE_BLOCKED</status></fsapiResponse>";
            }
            else if (uri.AbsolutePath.EndsWith(
                         "/LIST_GET_NEXT/netRemote.nav.presets/-1",
                         StringComparison.Ordinal))
            {
                body = """<fsapiResponse><status>FS_OK</status><item key="0"><field name="name"><c8_array>Trójka</c8_array></field></item></fsapiResponse>""";
            }
            else
            {
                return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
            }
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(body)
            });
        }

        private static string Value(string value) =>
            $"<fsapiResponse><status>FS_OK</status><value><u8>{value}</u8></value></fsapiResponse>";

        private static string Status() =>
            "<fsapiResponse><status>FS_OK</status></fsapiResponse>";
    }
}
