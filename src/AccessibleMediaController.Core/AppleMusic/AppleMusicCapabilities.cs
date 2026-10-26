using AccessibleMediaController.Core.Presentation;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.AppleMusic;

/// <summary>
/// Jedno zrodlo prawdy o funkcjach udostepnianych przez oficjalne Apple Music API.
/// Brak funkcji jest stanem uslugi, nie powodem do pokazywania martwego polecenia.
/// </summary>
public static class AppleMusicCapabilities
{
    private static readonly ArtistBrowseSection[] ArtistSections =
        [ArtistBrowseSection.Albums, ArtistBrowseSection.Tracks, ArtistBrowseSection.SimilarArtists];

    public static IReadOnlyList<ArtistBrowseSection> SupportedArtistSections => ArtistSections;

    public static bool CanAddToLibrary(MediaItemKind kind) => kind is
        MediaItemKind.Track or MediaItemKind.Album or MediaItemKind.Playlist or MediaItemKind.Video;

    // Apple dokumentuje POST do biblioteki, lecz nie publikuje odpowiedniego DELETE.
    public static bool CanRemoveFromLibrary(MediaItemKind kind) => false;

    public static bool CanAddToFavorites(MediaItemKind kind) => kind is
        MediaItemKind.Track or MediaItemKind.Album or MediaItemKind.Artist
            or MediaItemKind.Playlist or MediaItemKind.Video;

    // Favorites nie jest dawnym mechanizmem ratings; nie wolno kasowac ratingu
    // i przedstawic tego uzytkownikowi jako usuniecie z Favorites.
    public static bool CanRemoveFromFavorites(MediaItemKind kind) => false;

    public static bool CanCreatePlaylist => true;
    public static bool CanAppendPlaylistTracks => true;
    public static bool CanRemovePlaylistTracks => false;
    public static bool CanReorderPlaylistTracks => false;
    public static bool SupportsEmbeddedPlayback => true;

    public static string LibraryUnavailableReason(bool alreadyInLibrary) =>
        alreadyInLibrary
            ? "Apple Music API nie udostępnia usuwania elementu z biblioteki. Zrób to w aplikacji Apple Music."
            : "Tego rodzaju elementu Apple Music API nie pozwala dodać do biblioteki.";

    public static string FavoriteUnavailableReason(bool alreadyFavorite) =>
        alreadyFavorite
            ? "Apple Music API nie udostępnia usuwania z ulubionych. Zrób to w aplikacji Apple Music."
            : "Tego rodzaju elementu Apple Music API nie pozwala dodać do ulubionych.";
}
