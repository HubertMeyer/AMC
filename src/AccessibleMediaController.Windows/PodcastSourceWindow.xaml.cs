using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Windows;
using System.Windows.Input;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class PodcastSourceWindow : Window
{
    private readonly Func<Uri, CancellationToken, Task<PodcastFeedDocument>> _fetch;
    private readonly Func<Uri, CancellationToken, Task<YouTubeCollectionDocument>> _fetchYouTubeCollection;
    private readonly Func<string, CancellationToken, Task<ResolvedYouTubeAudioSource>> _resolveInternetMedia;
    private CancellationTokenSource? _checkCancellation;
    private bool _isBusy;

    internal PodcastSourceWindow(
        Func<Uri, CancellationToken, Task<PodcastFeedDocument>> fetch,
        Func<Uri, CancellationToken, Task<YouTubeCollectionDocument>> fetchYouTubeCollection,
        Func<string, CancellationToken, Task<ResolvedYouTubeAudioSource>> resolveInternetMedia)
    {
        ArgumentNullException.ThrowIfNull(fetch);
        ArgumentNullException.ThrowIfNull(fetchYouTubeCollection);
        ArgumentNullException.ThrowIfNull(resolveInternetMedia);
        _fetch = fetch;
        _fetchYouTubeCollection = fetchYouTubeCollection;
        _resolveInternetMedia = resolveInternetMedia;
        InitializeComponent();
        Title = "Nowy podcast, kanał YouTube lub medium internetowe";
        Loaded += (_, _) =>
        {
            FeedBox.Focus();
            Keyboard.Focus(FeedBox);
        };
    }

    public PodcastFeedDocument? Feed { get; private set; }
    public PodcastSourceKind SourceKind { get; private set; } = PodcastSourceKind.Rss;
    internal ResolvedYouTubeAudioSource? InternetMedia { get; private set; }
    public string CustomTitle => NameBox.Text.Trim();

    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (_isBusy) return;
        if (!TryGetFeedUri(out var address)) return;
        _checkCancellation?.Cancel();
        _checkCancellation?.Dispose();
        _checkCancellation = new CancellationTokenSource();
        Feed = null;
        SourceKind = PodcastSourceKind.Rss;
        InternetMedia = null;
        SetBusy(true);
        StatusText.Text = "Sprawdzanie adresu i dodawanie źródła…";
        try
        {
            if (YouTubeSourceResolver.IsYouTubeUrl(address.AbsoluteUri))
            {
                if (YouTubeCollectionClient.TryNormalizeCollectionAddress(
                        address,
                        out var collectionAddress,
                        out _))
                {
                    var collection = await _fetchYouTubeCollection(
                        collectionAddress,
                        _checkCancellation.Token);
                    Feed = collection.Feed;
                    SourceKind = collection.SourceKind;
                    InternetMedia = null;
                    var collectionKindLabel = collection.SourceKind == PodcastSourceKind.YouTubeChannel
                        ? "Kanał YouTube"
                        : "Playlista YouTube";
                    DiagnosticLog.Info(
                        "podcast-source",
                        $"Sprawdzono i zatwierdzono dodanie {collectionKindLabel.ToLowerInvariant()}: {collection.Feed.Title}; materiały: {collection.Feed.Episodes.Count}.");
                    AcceptSourceAndClose(
                        $"{collectionKindLabel} działa. Dodawanie: {collection.Feed.Title}. Materiały: {collection.Feed.Episodes.Count}.");
                    return;
                }
                var media = await _resolveInternetMedia(address.AbsoluteUri, _checkCancellation.Token);
                InternetMedia = media;
                Feed = null;
                SourceKind = PodcastSourceKind.PublicInternetMedia;
                var kind = media.IsLive ? "transmisja na żywo" : "materiał";
                var channel = string.IsNullOrWhiteSpace(media.Channel)
                    ? string.Empty
                    : $", kanał: {media.Channel}";
                AcceptSourceAndClose($"Publiczny {kind} działa. Dodawanie: {media.Title}{channel}.");
                return;
            }
            var feed = await _fetch(address, _checkCancellation.Token);
            Feed = feed;
            SourceKind = PodcastSourceKind.Rss;
            InternetMedia = null;
            var author = string.IsNullOrWhiteSpace(feed.Author) ? string.Empty : $", autor: {feed.Author}";
            if (feed.Episodes.Count == 0)
            {
                Feed = null;
                StatusText.Text = $"Kanał {feed.Title}{author} nie zawiera odtwarzalnych odcinków audio ani wideo.";
                FeedBox.Focus();
                Keyboard.Focus(FeedBox);
                FeedBox.SelectAll();
            }
            else
            {
                AcceptSourceAndClose($"Kanał działa. Dodawanie: {feed.Title}{author}. Odcinki: {feed.Episodes.Count}.");
            }
        }
        catch (OperationCanceledException)
        {
            if (IsVisible) StatusText.Text = "Dodawanie źródła anulowano.";
        }
        catch (Exception exception) when (exception is HttpRequestException
            or InvalidDataException
            or System.Xml.XmlException
            or ArgumentException
            or NotSupportedException
            or TimeoutException)
        {
            StatusText.Text = $"Nie można odczytać kanału: {exception.Message}";
            FeedBox.Focus();
            Keyboard.Focus(FeedBox);
            FeedBox.SelectAll();
        }
        finally
        {
            if (IsVisible) SetBusy(false);
        }
    }

    private bool TryGetFeedUri(out Uri address)
    {
        if (Uri.TryCreate(FeedBox.Text.Trim(), UriKind.Absolute, out var parsed)
            && parsed.Scheme is "http" or "https"
            && string.IsNullOrEmpty(parsed.UserInfo))
        {
            address = parsed;
            return true;
        }
        address = null!;
        StatusText.Text = "Wpisz pełny adres HTTP lub HTTPS bez nazwy użytkownika i hasła.";
        FeedBox.Focus();
        Keyboard.Focus(FeedBox);
        FeedBox.SelectAll();
        return false;
    }

    private void SetBusy(bool busy)
    {
        _isBusy = busy;
        AddButton.IsEnabled = !busy;
        AddButton.IsDefault = !busy;
        FeedBox.IsEnabled = !busy;
        NameBox.IsEnabled = !busy;
    }

    private void AcceptSourceAndClose(string status)
    {
        StatusText.Text = status;
        DiagnosticLog.Info(
            "podcast-source",
            $"Zatwierdzono jednoetapowe dodanie: {Feed?.Title ?? InternetMedia?.Title ?? "publiczne medium"}.");
        DialogResult = true;
    }

    private void Window_Closing(object? sender, CancelEventArgs e)
    {
        _checkCancellation?.Cancel();
        _checkCancellation?.Dispose();
        _checkCancellation = null;
    }
}
