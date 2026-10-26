using System.Net;
using AccessibleMediaController.Core.Devices.FrontierSmart;

var tests = new (string Name, Func<Task> Run)[]
{
    ("adresy lokalne", TestAddressPolicy),
    ("kodowanie URI", TestUriEncoding),
    ("parser wartości", TestValueParser),
    ("parser wielu wartości", TestMultipleParser),
    ("tryby i etykiety", TestModes),
    ("presety i etykiety", TestPresets),
    ("przeliczanie głośności", TestVolume),
    ("odpowiedź SSDP", TestSsdp),
    ("klient i brak identyfikatora sesji", TestClient),
    ("zgodność ze starszym firmware bez GET_MULTIPLE", TestSnapshotFallback),
    ("zgodność z błędem FSAPI zamiast GET_MULTIPLE", TestSnapshotFallbackFromFsApiStatus),
    ("minimalne sprawdzenie tożsamości", TestIdentityProbe),
    ("błąd polecenia", TestRejectedCommand)
};

var failures = 0;
foreach (var (name, run) in tests)
{
    try
    {
        await run();
        Console.WriteLine($"OK: {name}");
    }
    catch (Exception exception)
    {
        failures++;
        Console.Error.WriteLine($"BŁĄD: {name}: {exception.GetType().Name}: {exception.Message}");
    }
}
Console.WriteLine($"Frontier Smart: {tests.Length - failures}/{tests.Length} testów zaliczonych.");
return failures == 0 ? 0 : 1;

static Task TestAddressPolicy()
{
    True(FrontierSmartAddressPolicy.TryNormalize("192.168.1.25", out var local));
    Equal("192.168.1.25", local);
    True(FrontierSmartAddressPolicy.TryNormalize("10.0.0.7", out _));
    True(FrontierSmartAddressPolicy.TryNormalize("fe80::1", out _));
    False(FrontierSmartAddressPolicy.TryNormalize("8.8.8.8", out _));
    False(FrontierSmartAddressPolicy.TryNormalize("radio.example", out _));
    return Task.CompletedTask;
}

static Task TestUriEncoding()
{
    var uri = FrontierSmartClient.CreateSetUri(
        "192.168.1.25",
        "1234",
        FrontierSmartNodes.FriendlyName,
        "Radio & kuchnia");
    Equal("/fsapi/SET/netRemote.sys.info.friendlyName", uri.AbsolutePath);
    True(uri.Query.Contains("pin=1234", StringComparison.Ordinal));
    True(uri.Query.Contains("value=Radio%20%26%20kuchnia", StringComparison.Ordinal));
    False(uri.Query.Contains("sid=", StringComparison.OrdinalIgnoreCase));
    return Task.CompletedTask;
}

static Task TestValueParser()
{
    const string xml = "<fsapiResponse><status>FS_OK</status><value><u8>7</u8></value></fsapiResponse>";
    var value = FrontierSmartXmlParser.ParseValue(FrontierSmartNodes.Volume, xml);
    True(value.Success);
    Equal("u8", value.ValueType);
    Equal(7, value.AsInt32());
    return Task.CompletedTask;
}

static Task TestMultipleParser()
{
    const string xml = "<fsapiGetMultipleResponse>"
        + "<fsapiResponse><node>netRemote.sys.power</node><status>FS_OK</status><value><u8>1</u8></value></fsapiResponse>"
        + "<fsapiResponse><node>netRemote.play.info.album</node><status>FS_NODE_DOES_NOT_EXIST</status></fsapiResponse>"
        + "</fsapiGetMultipleResponse>";
    var values = FrontierSmartXmlParser.ParseMultiple(xml);
    Equal(true, values[FrontierSmartNodes.Power].AsBoolean());
    False(values[FrontierSmartNodes.PlayAlbum].Success);
    return Task.CompletedTask;
}

static Task TestModes()
{
    const string xml = "<fsapiResponse><status>FS_OK</status>"
        + "<item key=\"0\"><field name=\"id\"><c8_array>IR</c8_array></field>"
        + "<field name=\"selectable\"><u8>1</u8></field><field name=\"label\"><c8_array>Radio internetowe</c8_array></field>"
        + "<field name=\"streamable\"><u8>1</u8></field><field name=\"modetype\"><u8>0</u8></field></item>"
        + "<item key=\"1\"><field name=\"id\"><c8_array>DMR</c8_array></field>"
        + "<field name=\"selectable\"><u8>0</u8></field><field name=\"label\"><c8_array>Odbiornik multimediów</c8_array></field></item>"
        + "<listend/></fsapiResponse>";
    var modes = FrontierSmartXmlParser.ParseModes(xml);
    Equal(2, modes.Count);
    Equal("Radio internetowe", modes[0].ToString());
    Equal("Odbiornik multimediów, niedostępny do bezpośredniego wyboru", modes[1].ToString());
    return Task.CompletedTask;
}

static Task TestPresets()
{
    const string xml = "<fsapiResponse><status>FS_OK</status>"
        + "<item key=\"0\"><field name=\"name\"><c8_array>Polskie Radio Dwójka</c8_array></field></item>"
        + "<listend/></fsapiResponse>";
    var presets = FrontierSmartXmlParser.ParsePresets(xml);
    Equal(1, presets.Count);
    Equal("Polskie Radio Dwójka, preset 1", presets[0].ToString());
    return Task.CompletedTask;
}

static Task TestVolume()
{
    Equal(40, FrontierSmartVolume.ToPercent(8, 21));
    Equal(8, FrontierSmartVolume.FromPercent(40, 21));
    Equal("40 procent, krok 8 z 20", FrontierSmartVolume.AccessibleLabel(8, 21));
    Equal(null, FrontierSmartVolume.ToPercent(1, 1));
    return Task.CompletedTask;
}

static Task TestSsdp()
{
    const string response = "HTTP/1.1 200 OK\r\n"
        + "ST: urn:schemas-frontier-silicon-com:fs_reference:fsapi:1\r\n"
        + "LOCATION: http://192.168.1.44:80/device\r\n\r\n";
    True(FrontierSmartDiscoveryService.TryParseResponse(response, out var address));
    Equal("192.168.1.44", address);
    False(FrontierSmartDiscoveryService.TryParseResponse(
        response.Replace(FrontierSmartDiscoveryService.ServiceType, "urn:schemas-upnp-org:device:MediaRenderer:1"),
        out _));
    const string withoutLocation = "HTTP/1.1 200 OK\r\n"
        + "USN: uuid:test::urn:schemas-frontier-silicon-com:fs_reference:fsapi:1\r\n\r\n";
    True(FrontierSmartDiscoveryService.TryParseResponse(
        withoutLocation,
        IPAddress.Parse("192.168.1.45"),
        out var responseAddress));
    Equal("192.168.1.45", responseAddress);
    return Task.CompletedTask;
}

static async Task TestClient()
{
    const string xml = "<fsapiResponse><status>FS_OK</status><value><c8_array>Radio w kuchni</c8_array></value></fsapiResponse>";
    var handler = new FakeHandler(request =>
    {
        False(request.RequestUri!.Query.Contains("sid=", StringComparison.OrdinalIgnoreCase));
        return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(xml) };
    });
    using var client = new FrontierSmartClient(handler);
    var value = await client.GetAsync("192.168.1.25", "1234", FrontierSmartNodes.FriendlyName);
    Equal("Radio w kuchni", value.Value);
}

static async Task TestRejectedCommand()
{
    const string xml = "<fsapiResponse><status>FS_NODE_BLOCKED</status></fsapiResponse>";
    using var client = new FrontierSmartClient(new FakeHandler(_ =>
        new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(xml) }));
    try
    {
        await client.SetPowerAsync("192.168.1.25", "1234", true);
        throw new InvalidOperationException("Oczekiwano wyjątku protokołu.");
    }
    catch (FrontierSmartProtocolException exception)
    {
        Equal("FS_NODE_BLOCKED", exception.Status);
    }
}

static async Task TestSnapshotFallback()
{
    var requests = new List<Uri>();
    var handler = new FakeHandler(request =>
    {
        requests.Add(request.RequestUri!);
        if (request.RequestUri!.AbsolutePath.EndsWith("/GET_MULTIPLE", StringComparison.Ordinal))
            return new HttpResponseMessage(HttpStatusCode.NotFound);
        var node = request.RequestUri.AbsolutePath.Split('/').Last();
        var value = node switch
        {
            FrontierSmartNodes.FriendlyName => "Radio testowe",
            FrontierSmartNodes.RadioId => "ABC123",
            FrontierSmartNodes.Power => "1",
            _ => "0"
        };
        var type = node is FrontierSmartNodes.FriendlyName or FrontierSmartNodes.RadioId
            ? "c8_array"
            : "u32";
        var xml = $"<fsapiResponse><status>FS_OK</status><value><{type}>{value}</{type}></value></fsapiResponse>";
        return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(xml) };
    });
    using var client = new FrontierSmartClient(handler);
    var snapshot = await client.ReadSnapshotAsync("192.168.1.25", "1234");
    Equal("Radio testowe", snapshot.DisplayName);
    Equal("ABC123", snapshot.RadioId);
    Equal(true, snapshot.IsPoweredOn);
    True(requests.Count > 2);
    False(requests.Any(uri => uri.Query.Contains("sid=", StringComparison.OrdinalIgnoreCase)));
}

static async Task TestSnapshotFallbackFromFsApiStatus()
{
    var requests = new List<Uri>();
    var handler = new FakeHandler(request =>
    {
        requests.Add(request.RequestUri!);
        if (request.RequestUri!.AbsolutePath.EndsWith("/GET_MULTIPLE", StringComparison.Ordinal))
        {
            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    "<fsapiResponse><status>FS_NODE_DOES_NOT_EXIST</status></fsapiResponse>")
            };
        }
        var node = request.RequestUri.AbsolutePath.Split('/').Last();
        var value = node switch
        {
            FrontierSmartNodes.FriendlyName => "Starsze radio",
            FrontierSmartNodes.RadioId => "OLD-1",
            FrontierSmartNodes.Power => "1",
            _ => "0"
        };
        var type = node is FrontierSmartNodes.FriendlyName or FrontierSmartNodes.RadioId
            ? "c8_array"
            : "u32";
        return new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                $"<fsapiResponse><status>FS_OK</status><value><{type}>{value}</{type}></value></fsapiResponse>")
        };
    });
    using var client = new FrontierSmartClient(handler);
    var snapshot = await client.ReadSnapshotAsync("192.168.1.25", "1234");
    Equal("Starsze radio", snapshot.DisplayName);
    Equal("OLD-1", snapshot.RadioId);
    True(requests.Count > 2);
}

static async Task TestIdentityProbe()
{
    var requests = new List<Uri>();
    using var client = new FrontierSmartClient(new FakeHandler(request =>
    {
        requests.Add(request.RequestUri!);
        var node = request.RequestUri!.AbsolutePath.Split('/').Last();
        var xml = node switch
        {
            FrontierSmartNodes.FriendlyName =>
                "<fsapiResponse><status>FS_OK</status><value><c8_array>Teufel Radio</c8_array></value></fsapiResponse>",
            FrontierSmartNodes.RadioId =>
                "<fsapiResponse><status>FS_OK</status><value><c8_array>RADIO-60</c8_array></value></fsapiResponse>",
            _ => "<fsapiResponse><status>FS_NODE_DOES_NOT_EXIST</status></fsapiResponse>"
        };
        return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(xml) };
    }));
    var identity = await client.ReadIdentityAsync("192.168.1.25", "1234");
    Equal("Teufel Radio", identity.DisplayName);
    Equal("RADIO-60", identity.RadioId);
    Equal(string.Empty, identity.FirmwareVersion);
    Equal(3, requests.Count);
}

static void True(bool value)
{
    if (!value) throw new InvalidOperationException("Oczekiwano wartości prawda.");
}

static void False(bool value) => True(!value);

static void Equal<T>(T expected, T actual)
{
    if (!EqualityComparer<T>.Default.Equals(expected, actual))
        throw new InvalidOperationException($"Oczekiwano „{expected}”, otrzymano „{actual}”.");
}

sealed class FakeHandler(Func<HttpRequestMessage, HttpResponseMessage> responseFactory) : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken) =>
        Task.FromResult(responseFactory(request));
}
