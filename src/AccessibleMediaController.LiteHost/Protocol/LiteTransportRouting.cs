namespace AccessibleMediaController.LiteHost.Protocol;

internal readonly record struct LiteTransportTarget(string SessionId, string Engine);

/// <summary>
/// Jawne mapowanie sesji interfejsu na niezależne lokalne tory audio.
/// Brak sessionId jest zachowany wyłącznie dla zgodności ze starszym klientem.
/// </summary>
internal static class LiteTransportRouting
{
    internal static LiteTransportTarget Resolve(
        string? requestedSessionId,
        string legacyActiveEngine,
        bool filesItemIsEpisode)
    {
        var requested = requestedSessionId?.Trim();
        if (!string.IsNullOrWhiteSpace(requested))
        {
            return requested switch
            {
                "radio" => new("radio", "radio"),
                "files" => new("files", "files"),
                "podcasts" => new("podcasts", "files"),
                "spotify" => new("spotify", "spotify"),
                _ => throw new LiteRequestException(
                    "Transport obsługuje sesje Pliki, Podcasty, Radio i Spotify.")
            };
        }

        return legacyActiveEngine switch
        {
            "radio" => new("radio", "radio"),
            "spotify" => new("spotify", "spotify"),
            _ => new(filesItemIsEpisode ? "podcasts" : "files", "files")
        };
    }
}
