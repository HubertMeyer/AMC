using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class TransportRoutingTests
{
    public static void Run()
    {
        ExplicitSessionsChooseTheirOwnEngine();
        LegacyCallsKeepTheLastEngine();
        UnknownSessionIsRejected();
        Console.WriteLine("TransportRoutingTests: OK");
    }

    private static void ExplicitSessionsChooseTheirOwnEngine()
    {
        var radio = LiteTransportRouting.Resolve("radio", "files", false);
        var files = LiteTransportRouting.Resolve("files", "radio", true);
        var podcasts = LiteTransportRouting.Resolve("podcasts", "radio", false);
        Assert.True(radio == new LiteTransportTarget("radio", "radio"),
            "Radio ma własny tor niezależnie od ostatniego polecenia.");
        Assert.True(files == new LiteTransportTarget("files", "files"),
            "Pliki mają własny tor niezależnie od Radia.");
        Assert.True(podcasts == new LiteTransportTarget("podcasts", "files"),
            "Podcasty używają lokalnego toru plikowego, ale zachowują nazwę sesji.");
    }

    private static void LegacyCallsKeepTheLastEngine()
    {
        Assert.True(
            LiteTransportRouting.Resolve(null, "radio", false)
                == new LiteTransportTarget("radio", "radio"),
            "Stary klient bez sessionId zachowuje ostatnie Radio.");
        Assert.True(
            LiteTransportRouting.Resolve(null, "files", true)
                == new LiteTransportTarget("podcasts", "files"),
            "Stary klient rozpoznaje odcinek na torze plikowym.");
    }

    private static void UnknownSessionIsRejected()
    {
        try
        {
            LiteTransportRouting.Resolve("tidal", "files", false);
            throw new InvalidOperationException("Nieznana sesja nie została odrzucona.");
        }
        catch (LiteRequestException)
        {
        }
    }
}
