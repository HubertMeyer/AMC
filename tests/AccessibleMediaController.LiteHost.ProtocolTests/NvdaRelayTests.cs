using System.Text.Json;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class NvdaRelayTests
{
    public static void Run()
    {
        ReplyCompletesOnlyTheMatchingRequest();
        UnknownReplyIsRejectedWithoutChangingAnotherRequest();
        CancellationRemovesPendingRequest();
        Console.WriteLine("NvdaRelayTests: OK");
    }

    private static void ReplyCompletesOnlyTheMatchingRequest()
    {
        using var relay = new LiteNvdaRelay();
        var lines = new List<string>();
        var events = new LiteEventSink(lines.Add);
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(2));

        var pending = relay.RequestAsync("status", events, deadline.Token);
        Assert.True(lines.Count == 1, "jedno polecenie tworzy jedno zdarzenie dla frontendu");
        using var eventDocument = JsonDocument.Parse(lines[0]);
        var root = eventDocument.RootElement;
        Assert.Equal(LiteNvdaRelay.EventName, root.GetProperty("event").GetString(),
            "nazwa zdarzenia jest stała i wersjonowana przez potok");
        var data = root.GetProperty("data");
        Assert.Equal("status", data.GetProperty("command").GetString(),
            "do frontendu trafia tylko polecenie z białej listy serwera");
        var requestId = data.GetProperty("requestId").GetString()!;

        var reply = Request(
            "odpowiedz",
            LiteNvdaRelay.ReplyOperation,
            $$"""{"requestId":"{{requestId}}","ok":true,"message":"Radio, odtwarzanie"}""");
        var accepted = relay.Reply(reply, events);
        Assert.True(JsonSerializer.Serialize(accepted).Contains("true", StringComparison.Ordinal),
            "odpowiedź istniejącego żądania zostaje przyjęta");
        var result = pending.GetAwaiter().GetResult();
        Assert.True(result.Ok, "stan powodzenia przechodzi bez zmiany");
        Assert.Equal("Radio, odtwarzanie", result.Message,
            "do dodatku trafia wyłącznie przygotowany tekst użytkowy");
    }

    private static void UnknownReplyIsRejectedWithoutChangingAnotherRequest()
    {
        using var relay = new LiteNvdaRelay();
        var lines = new List<string>();
        var events = new LiteEventSink(lines.Add);
        using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(2));
        var pending = relay.RequestAsync("context", events, deadline.Token);
        using var eventDocument = JsonDocument.Parse(lines[0]);
        var requestId = eventDocument.RootElement.GetProperty("data").GetProperty("requestId").GetString()!;

        var foreign = Request(
            "obca",
            LiteNvdaRelay.ReplyOperation,
            """{"requestId":"nieistniejace","ok":true,"message":"Nie ten wynik"}""");
        var rejected = JsonSerializer.Serialize(relay.Reply(foreign, events));
        Assert.True(rejected.Contains("false", StringComparison.Ordinal),
            "obcy identyfikator nie może zakończyć żadnego polecenia");
        Assert.True(!pending.IsCompleted, "właściwe żądanie nadal czeka na własną odpowiedź");

        relay.Reply(Request(
            "wlasciwa",
            LiteNvdaRelay.ReplyOperation,
            $$"""{"requestId":"{{requestId}}","ok":true,"message":"Radio, Biblioteka"}"""), events);
        Assert.Equal("Radio, Biblioteka", pending.GetAwaiter().GetResult().Message,
            "właściwa odpowiedź nadal dochodzi po odrzuceniu obcej");
    }

    private static void CancellationRemovesPendingRequest()
    {
        using var relay = new LiteNvdaRelay();
        var lines = new List<string>();
        var events = new LiteEventSink(lines.Add);
        using var cancellation = new CancellationTokenSource();
        var pending = relay.RequestAsync("nowPlaying", events, cancellation.Token);
        using var eventDocument = JsonDocument.Parse(lines[0]);
        var requestId = eventDocument.RootElement.GetProperty("data").GetProperty("requestId").GetString()!;
        cancellation.Cancel();
        try
        {
            pending.GetAwaiter().GetResult();
            throw new InvalidOperationException("anulowane żądanie nie może zakończyć się powodzeniem");
        }
        catch (OperationCanceledException) { }

        var late = JsonSerializer.Serialize(relay.Reply(Request(
            "spozniona",
            LiteNvdaRelay.ReplyOperation,
            $$"""{"requestId":"{{requestId}}","ok":true,"message":"Za późno"}"""), events));
        Assert.True(late.Contains("false", StringComparison.Ordinal),
            "spóźniona odpowiedź po limicie jest odrzucana, nie przechodzi do następnej komendy");
    }

    private static LiteRequest Request(string id, string operation, string argsJson)
    {
        var outcome = LiteRequestReader.Read(
            $$"""{"id":"{{id}}","op":"{{operation}}","args":{{argsJson}}}""");
        Assert.True(outcome.IsRequest, "próba testowa jest poprawnym zadaniem protokołu");
        return outcome.Request!;
    }
}
