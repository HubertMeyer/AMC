using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.Spotify;

/// <summary>
/// Wspólna bramka elementów odtwarzanych przez oba silniki Spotify.
/// Kontenery nigdy nie są zamieniane na przypadkowy utwór, a odcinek zachowuje
/// właściwy typ URI. Modelowe identyfikatory pozostają poza tekstem interfejsu.
/// </summary>
public static class SpotifyPlaybackItemContract
{
    public static string? Rejection(MediaItem item)
    {
        ArgumentNullException.ThrowIfNull(item);
        if (item.Kind is MediaItemKind.Album or MediaItemKind.Artist
            or MediaItemKind.Playlist or MediaItemKind.Podcast)
        {
            return item.Kind == MediaItemKind.Podcast
                ? "To jest podcast. Otwórz go strzałką w prawo i wybierz odcinek."
                : "To jest album, wykonawca lub playlista. Otwórz ją strzałką w prawo i wybierz utwór.";
        }
        if (item.Kind is not (MediaItemKind.Track or MediaItemKind.Episode)
            || string.IsNullOrWhiteSpace(PlaybackUri(item)))
        {
            return "Tego elementu Spotify nie można odtworzyć w AMC.";
        }
        return null;
    }

    public static string PlaybackUri(MediaItem item)
    {
        ArgumentNullException.ThrowIfNull(item);
        var source = item.Source?.Trim() ?? string.Empty;
        if (source.StartsWith("spotify:track:", StringComparison.Ordinal)
            || source.StartsWith("spotify:episode:", StringComparison.Ordinal))
        {
            return source;
        }
        var externalId = item.ExternalId?.Trim() ?? string.Empty;
        if (externalId.Length == 0) return string.Empty;
        var type = item.Kind == MediaItemKind.Episode ? "episode" : "track";
        return $"spotify:{type}:{externalId}";
    }

    /// <summary>Krótki tekst diagnostyczny bez adresów i znaków sterujących.</summary>
    public static string SafeDiagnostic(string? value)
    {
        var text = new string((value ?? string.Empty)
            .Where(character => !char.IsControl(character))
            .ToArray())
            .Trim();
        if (text.Contains("://", StringComparison.Ordinal))
            return "szczegóły pominięto";
        return text.Length <= 200 ? text : text[..200];
    }
}
