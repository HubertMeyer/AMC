using System.Net.Http;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class MainWindow
{
    private static readonly HttpClient YouTubeGoogleFeedHttpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(20)
    };

    private readonly YouTubeGoogleIntegrationService _youTubeGoogleIntegration = new();
    private readonly YouTubeChannelFeedClient _youTubeGoogleFeedClient =
        new(static () => YouTubeGoogleFeedHttpClient);

    public void ShowYouTubeAccountManager()
    {
        var returnToPlayer = _playerViewActive;
        var dialog = new YouTubeGoogleAccountWindow(
            _youTubeGoogleIntegration,
            ImportYouTubeGoogleLibraryAsync)
        {
            Owner = this
        };
        dialog.ShowDialog();
        if (returnToPlayer && _playerViewActive && IsActive)
        {
            UpdatePlayerView(true);
            FocusPlayerView();
        }
        else
        {
            RestoreMediaListFocusAfterRefresh();
        }
    }

    private async Task<YouTubeGoogleImportSummary> ImportYouTubeGoogleLibraryAsync(
        YouTubeAccountLibrary library,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(library);
        var channelDocuments = await FetchYouTubeSubscriptionFeedsAsync(
            library.Subscriptions,
            cancellationToken);
        cancellationToken.ThrowIfCancellationRequested();
        if (_isClosing) throw new OperationCanceledException(cancellationToken);

        CapturePodcastState();
        var channelsImported = 0;
        var playlistsImported = 0;
        var materialsImported = 0;
        foreach (var channel in channelDocuments.Where(result => result.Feed is not null))
        {
            var update = PodcastLibraryUpdater.Apply(
                _state.Podcasts,
                channel.Feed!,
                channel.Subscription.Title,
                DateTime.UtcNow,
                _state.Bookmarks,
                PodcastSourceKind.YouTubeChannel,
                addToLibrary: true);
            if (update.AddedSubscription)
            {
                update.Subscription.RefreshIntervalMinutes =
                    DefaultRefreshIntervalMinutes(PodcastSourceKind.YouTubeChannel);
            }
            channelsImported++;
            materialsImported += channel.Feed!.Episodes.Count;
        }

        foreach (var playlist in library.Playlists)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var feed = CreateYouTubePlaylistFeed(playlist);
            var update = PodcastLibraryUpdater.Apply(
                _state.Podcasts,
                feed,
                playlist.Title,
                DateTime.UtcNow,
                _state.Bookmarks,
                PodcastSourceKind.YouTubePlaylist,
                addToLibrary: true);
            if (update.AddedSubscription)
            {
                update.Subscription.RefreshIntervalMinutes =
                    DefaultRefreshIntervalMinutes(PodcastSourceKind.YouTubePlaylist);
            }
            playlistsImported++;
            materialsImported += feed.Episodes.Count;
        }

        ReloadPodcastSessionItems();
        QueueStateSave(announceFailure: true);
        if (string.Equals(_sessions.Current.Id, "podcasts", StringComparison.Ordinal))
        {
            _currentView = "Biblioteka";
            GetSessionNavigationState("podcasts").CurrentView = _currentView;
            RefreshCurrentView();
            PrepareViewFocusContext(
                $"Import YouTube zakończony. Kanały: {channelsImported}; playlisty: {playlistsImported}; materiały: {materialsImported}");
        }

        var failures = channelDocuments.Count(result => result.Feed is null);
        DiagnosticLog.Info(
            "youtube-google-import",
            $"Import konta YouTube zakończony; kanały: {channelsImported}; playlisty: {playlistsImported}; materiały: {materialsImported}; niepowodzenia: {failures}.");
        return new YouTubeGoogleImportSummary(
            channelsImported,
            playlistsImported,
            materialsImported,
            failures);
    }

    private async Task<IReadOnlyList<YouTubeSubscriptionFeedResult>> FetchYouTubeSubscriptionFeedsAsync(
        IReadOnlyList<YouTubeAccountSubscription> subscriptions,
        CancellationToken cancellationToken)
    {
        using var gate = new SemaphoreSlim(4, 4);
        var tasks = subscriptions.Select(async subscription =>
        {
            await gate.WaitAsync(cancellationToken).ConfigureAwait(false);
            try
            {
                var feedAddress = YouTubeChannelFeedClient.TryBuildFeedAddress(
                    subscription.ChannelId,
                    isChannel: true);
                if (feedAddress is null)
                    return new YouTubeSubscriptionFeedResult(subscription, null);
                var entries = await _youTubeGoogleFeedClient.FetchEntriesAsync(
                    feedAddress,
                    cancellationToken).ConfigureAwait(false);
                return entries.Count == 0
                    ? new YouTubeSubscriptionFeedResult(subscription, null)
                    : new YouTubeSubscriptionFeedResult(
                        subscription,
                        CreateYouTubeChannelFeed(subscription, entries));
            }
            finally
            {
                gate.Release();
            }
        }).ToArray();
        return await Task.WhenAll(tasks).ConfigureAwait(false);
    }

    private static PodcastFeedDocument CreateYouTubeChannelFeed(
        YouTubeAccountSubscription subscription,
        IReadOnlyDictionary<string, YouTubeFeedEntry> entries)
    {
        var feedId = $"youtube-channel:{subscription.ChannelId}";
        var homepage = new Uri(
            $"https://www.youtube.com/channel/{Uri.EscapeDataString(subscription.ChannelId)}",
            UriKind.Absolute);
        var collectionPage = new Uri(homepage, "videos");
        var episodes = entries.Select(pair =>
        {
            var videoId = pair.Key;
            var page = new Uri(
                $"https://www.youtube.com/watch?v={Uri.EscapeDataString(videoId)}",
                UriKind.Absolute);
            return new PodcastFeedEpisode(
                $"{feedId}:{videoId}",
                videoId,
                pair.Value.Title.Length > 0 ? pair.Value.Title : "Materiał YouTube",
                subscription.Title,
                string.Empty,
                pair.Value.Published,
                TimeSpan.Zero,
                page,
                page,
                "video/youtube",
                null);
        }).ToArray();
        return new PodcastFeedDocument(
            feedId,
            subscription.Title,
            subscription.Title,
            string.Empty,
            collectionPage,
            homepage,
            episodes);
    }

    private static PodcastFeedDocument CreateYouTubePlaylistFeed(YouTubeAccountPlaylist playlist)
    {
        var feedId = $"youtube-playlist:{playlist.PlaylistId}";
        var page = new Uri(
            $"https://www.youtube.com/playlist?list={Uri.EscapeDataString(playlist.PlaylistId)}",
            UriKind.Absolute);
        var episodes = playlist.Videos.Select(video =>
        {
            var videoPage = new Uri(
                $"https://www.youtube.com/watch?v={Uri.EscapeDataString(video.VideoId)}",
                UriKind.Absolute);
            return new PodcastFeedEpisode(
                $"{feedId}:{video.VideoId}",
                video.VideoId,
                video.Title,
                video.ChannelTitle,
                string.Empty,
                video.Published,
                TimeSpan.Zero,
                videoPage,
                videoPage,
                "video/youtube",
                null);
        }).ToArray();
        return new PodcastFeedDocument(
            feedId,
            playlist.Title,
            playlist.ChannelTitle,
            playlist.PrivacyStatus.Equals("private", StringComparison.OrdinalIgnoreCase)
                ? "Prywatna playlista zalogowanego konta YouTube. Dostępność odtwarzania poszczególnych materiałów zależy od YouTube."
                : string.Empty,
            page,
            page,
            episodes);
    }

    private sealed record YouTubeSubscriptionFeedResult(
        YouTubeAccountSubscription Subscription,
        PodcastFeedDocument? Feed);
}
