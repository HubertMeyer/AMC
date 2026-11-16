using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

/// <summary>Checks that every required top-level Spotify collection was read.</summary>
internal static class SpotifyCollectionCompletion
{
    internal static bool IsComplete(IEnumerable<MediaItemKind> updatedKinds)
    {
        ArgumentNullException.ThrowIfNull(updatedKinds);
        var tracks = false;
        var albums = false;
        var artists = false;
        var playlists = false;
        foreach (var kind in updatedKinds)
        {
            tracks |= kind == MediaItemKind.Track;
            albums |= kind == MediaItemKind.Album;
            artists |= kind == MediaItemKind.Artist;
            playlists |= kind == MediaItemKind.Playlist;
        }
        return tracks && albums && artists && playlists;
    }
}