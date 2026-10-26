using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

internal static class YouTubeVideoDownloadPolicy
{
    internal static string SaveAsLabel(bool isYouTubeVideo) =>
        isYouTubeVideo ? "Zapisz wideo jako" : "Zapisz odcinek audio jako";

    internal static bool TryResolvePageUrl(
        MediaItem? item,
        PodcastEpisodeSettings? episode,
        out string pageUrl)
    {
        pageUrl = string.Empty;
        if (item?.Kind != MediaItemKind.Episode) return false;

        var resolved = new[]
            {
                episode?.PageUrl,
                episode?.MediaUrl,
                item.PublicUri,
                item.Source
            }
            .FirstOrDefault(YouTubeSourceResolver.IsYouTubeUrl);
        if (string.IsNullOrWhiteSpace(resolved)) return false;

        pageUrl = resolved.Trim();
        return true;
    }
}
