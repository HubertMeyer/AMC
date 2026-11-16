using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class SpotifyCollectionCompletionTests
{
    internal static void Run()
    {
        AcceptsCompleteCollectionWithPodcastCategories();
        RejectsMissingRequiredCategory();
    }

    private static void AcceptsCompleteCollectionWithPodcastCategories()
    {
        Check(SpotifyCollectionCompletion.IsComplete([
                MediaItemKind.Track,
                MediaItemKind.Album,
                MediaItemKind.Artist,
                MediaItemKind.Playlist,
                MediaItemKind.Podcast,
                MediaItemKind.Episode,
            ]),
            "all four required Spotify collection categories plus podcasts were incorrectly marked incomplete");
    }

    private static void RejectsMissingRequiredCategory()
    {
        Check(!SpotifyCollectionCompletion.IsComplete([
                MediaItemKind.Track,
                MediaItemKind.Album,
                MediaItemKind.Artist,
                MediaItemKind.Podcast,
                MediaItemKind.Episode,
            ]),
            "a missing required playlist category was accepted as a complete collection");
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
