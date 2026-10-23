using System.Text.Json;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

internal static class LiteYouTubeDescriptionCoordinator
{
    internal const string Operation = "youtube.description";

    internal static object Read(JsonElement args)
    {
        var address = LiteArgs.RequireText(args, "address");
        var kind = LiteArgs.RequireText(args, "kind");
        var collection = kind switch
        {
            "video" => false,
            "collection" => true,
            _ => throw new LiteRequestException(
                "Rodzaj opisu YouTube musi oznaczać materiał albo kolekcję.")
        };
        using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(50));
        var result = new YouTubeDescriptionClient()
            .FetchAsync(address, collection, cancellation.Token)
            .GetAwaiter()
            .GetResult();
        return new { description = result.Description };
    }
}
