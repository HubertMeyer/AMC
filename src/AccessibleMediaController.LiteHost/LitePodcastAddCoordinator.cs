using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Sprawdza i dodaje RSS, podcasty SoundCloud, kolekcje YouTube albo publiczne medium
/// tym samym torem co główne AMC. Do bazy trafia wyłącznie stabilny adres
/// strony; podpisany adres strumienia z yt-dlp nigdy nie jest zapisywany.
/// </summary>
internal sealed class LitePodcastAddCoordinator : IDisposable
{
    public const string Operation = "podcast.add";

    private readonly LitePodcastProgressStore _podcasts;
    private readonly LiteBookmarkStore? _bookmarks;
    private readonly PodcastFeedClient _rssClient = new();
    private readonly SoundCloudPodcastClient _soundCloudClient = new();
    private readonly FacebookPublicPageClient _facebookClient = new();
    private readonly YouTubeCollectionClient _youTubeClient = new();
    private int _addInProgress;

    public LitePodcastAddCoordinator(
        LitePodcastProgressStore podcasts,
        LiteBookmarkStore? bookmarks)
    {
        _podcasts = podcasts ?? throw new ArgumentNullException(nameof(podcasts));
        _bookmarks = bookmarks;
    }

    public object Add(JsonElement args)
    {
        if (Interlocked.CompareExchange(ref _addInProgress, 1, 0) != 0)
            throw new LiteRequestException("Dodawanie źródła już trwa.");

        try
        {
            var addressText = (LiteArgs.ReadText(args, "address") ?? string.Empty).Trim();
            var customTitle = LiteArgs.ReadText(args, "title")?.Trim();
            if (!Uri.TryCreate(addressText, UriKind.Absolute, out var address)
                || address.Scheme is not ("http" or "https")
                || !string.IsNullOrEmpty(address.UserInfo))
            {
                throw new LiteRequestException(
                    "Wpisz pełny adres HTTP lub HTTPS bez nazwy użytkownika i hasła.");
            }

            if (SoundCloudPodcastClient.IsSoundCloudAddress(address))
            {
                var feedAddress = _soundCloudClient.ResolveFeedAddressAsync(
                        address,
                        CancellationToken.None)
                    .GetAwaiter()
                    .GetResult();
                var soundCloudFeed = _rssClient.FetchAsync(
                        feedAddress,
                        CancellationToken.None)
                    .GetAwaiter()
                    .GetResult();
                if (soundCloudFeed.Episodes.Count == 0)
                {
                    throw new LiteRequestException(
                        $"Kanał {soundCloudFeed.Title} nie zawiera odtwarzalnych plików audio.");
                }
                return SourceResult(AddFeed(
                    soundCloudFeed,
                    customTitle,
                    PodcastSourceKind.SoundCloudPodcast));
            }
            if (SoundCloudPodcastClient.IsSoundCloudHost(address))
            {
                throw new LiteRequestException(
                    "Wpisz adres publicznego profilu SoundCloud albo jego kanału RSS, nie adres pojedynczego utworu lub playlisty.");
            }

            if (YouTubeSourceResolver.IsYouTubeUrl(addressText))
            {
                if (YouTubeCollectionClient.TryNormalizeCollectionAddress(
                        address,
                        out var collectionAddress,
                        out _))
                {
                    var collection = _youTubeClient.FetchAsync(
                            collectionAddress,
                            CancellationToken.None)
                        .GetAwaiter()
                        .GetResult();
                    return SourceResult(AddFeed(
                        collection.Feed,
                        customTitle,
                        collection.SourceKind));
                }

                var resolved = YouTubeSourceResolver.ResolveAudioAsync(
                        addressText,
                        CancellationToken.None)
                    .GetAwaiter()
                    .GetResult();
                var result = _podcasts.AddInternetMedia(
                    new PodcastInternetMediaSource(
                        resolved.PageUrl,
                        resolved.Title,
                        resolved.Channel,
                        resolved.Duration,
                        resolved.IsLive),
                    customTitle);
                return new
                {
                    subscriptionId = result.SubscriptionId,
                    preferredEpisodeId = result.EpisodeId,
                    title = result.Title,
                    sourceKind = "internetMedia",
                    sourceLabel = resolved.IsLive
                        ? "transmisja YouTube"
                        : "materiał YouTube",
                    added = result.AddedEpisode,
                    restored = false,
                    itemCount = 1
                };
            }

            if (PublicSocialVideoResolver.TryGetProvider(addressText, out var socialProvider))
            {
                var resolved = PublicSocialVideoResolver.ResolveAudioAsync(
                        addressText, CancellationToken.None)
                    .GetAwaiter().GetResult();
                var result = _podcasts.AddInternetMedia(
                    new PodcastInternetMediaSource(
                        resolved.PageUrl,
                        resolved.Title,
                        resolved.Channel,
                        resolved.Duration,
                        resolved.IsLive),
                    customTitle);
                return new
                {
                    subscriptionId = result.SubscriptionId,
                    preferredEpisodeId = result.EpisodeId,
                    title = result.Title,
                    sourceKind = "internetMedia",
                    sourceLabel = socialProvider == "Facebook"
                        ? "film z Facebooka"
                        : "film z Instagrama",
                    added = result.AddedEpisode,
                    restored = false,
                    itemCount = 1
                };
            }
            if (FacebookPublicPageClient.TryNormalizePageAddress(address, out var facebookPage))
            {
                var facebookFeed = _facebookClient.FetchAsync(facebookPage, CancellationToken.None)
                    .GetAwaiter().GetResult();
                return SourceResult(AddFeed(
                    facebookFeed, customTitle, PodcastSourceKind.FacebookPage));
            }
            if (address.IdnHost.Equals("facebook.com", StringComparison.OrdinalIgnoreCase)
                || address.IdnHost.EndsWith(".facebook.com", StringComparison.OrdinalIgnoreCase)
                || address.IdnHost.Equals("instagram.com", StringComparison.OrdinalIgnoreCase)
                || address.IdnHost.EndsWith(".instagram.com", StringComparison.OrdinalIgnoreCase))
            {
                throw new LiteRequestException(
                    "Podaj adres publicznej strony Facebooka albo pojedynczego filmu. Z Instagrama można dodać pojedynczy film lub rolkę.");
            }

            var feed = _rssClient.FetchAsync(address, CancellationToken.None)
                .GetAwaiter()
                .GetResult();
            if (feed.Episodes.Count == 0)
            {
                throw new LiteRequestException(
                    $"Kanał {feed.Title} nie zawiera odtwarzalnych odcinków audio ani wideo.");
            }
            return SourceResult(AddFeed(feed, customTitle, PodcastSourceKind.Rss));
        }
        catch (LiteRequestException)
        {
            throw;
        }
        catch (Exception exception) when (exception is HttpRequestException
            or InvalidDataException
            or System.Xml.XmlException
            or ArgumentException
            or OperationCanceledException
            or NotSupportedException
            or TimeoutException)
        {
            throw new LiteRequestException("Nie można dodać źródła: " + exception.Message);
        }
        finally
        {
            Volatile.Write(ref _addInProgress, 0);
        }
    }

    private PodcastSourceAddResult AddFeed(
        PodcastFeedDocument feed,
        string? customTitle,
        PodcastSourceKind sourceKind)
    {
        if (_bookmarks is not null
            && feed.Episodes.Any(episode => episode.Chapters is { Count: > 0 }))
        {
            return _bookmarks.MutateBookmarks(bookmarks =>
                _podcasts.AddSource(feed, customTitle, sourceKind, bookmarks));
        }
        return _podcasts.AddSource(feed, customTitle, sourceKind);
    }

    private static object SourceResult(PodcastSourceAddResult result) => new
    {
        subscriptionId = result.SubscriptionId,
        preferredEpisodeId = (string?)null,
        title = result.Title,
        sourceKind = result.SourceKind switch
        {
            PodcastSourceKind.YouTubeChannel => "youtubeChannel",
            PodcastSourceKind.YouTubePlaylist => "youtubePlaylist",
            PodcastSourceKind.SoundCloudPodcast => "soundcloudPodcast",
            PodcastSourceKind.FacebookPage => "facebookPage",
            _ => "rss"
        },
        sourceLabel = result.SourceKind switch
        {
            PodcastSourceKind.YouTubeChannel => "kanał YouTube",
            PodcastSourceKind.YouTubePlaylist => "playlista YouTube",
            PodcastSourceKind.SoundCloudPodcast => "podcast SoundCloud",
            PodcastSourceKind.FacebookPage => "strona Facebooka",
            _ => "podcast"
        },
        added = result.AddedSubscription,
        restored = result.RestoredSubscription,
        itemCount = result.AvailableEpisodes
    };

    public void Dispose()
    {
        _rssClient.Dispose();
        _soundCloudClient.Dispose();
        _facebookClient.Dispose();
    }
}
