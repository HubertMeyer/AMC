using AccessibleMediaController.Core.Spotify;

namespace AccessibleMediaController.Core.Playback;

public static class PlaybackShufflePolicy
{
    public static bool SupportsSession(string? sessionId) =>
        string.Equals(sessionId, "local", StringComparison.OrdinalIgnoreCase)
        || string.Equals(sessionId, "podcasts", StringComparison.OrdinalIgnoreCase)
        || SpotifyPlaybackSettingsResolver.IsSpotifySession(sessionId);

    public static string GetActionLabel(bool shuffleEnabled) => shuffleEnabled
        ? "Wyłącz odtwarzanie losowe"
        : "Włącz odtwarzanie losowe";
}
