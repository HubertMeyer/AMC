using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Podcasts;
using AccessibleMediaController.LiteHost.Protocol;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Import i eksport OPML przez wspólne parsery Core. Python dostaje wyłącznie
/// gotowe etykiety użytkowe i wybór użytkownika; nie interpretuje XML-u ani
/// nie zapisuje bazy Podcastów.
/// </summary>
internal sealed class LitePodcastOpmlCoordinator : IDisposable
{
    public const string InspectOperation = "podcast.opml.inspect";
    public const string ImportOperation = "podcast.opml.import";
    public const string ExportOperation = "podcast.opml.export";
    public const string ExportYouTubeOperation = "podcast.youtube.export";

    private const int MaximumParallelFetches = 4;
    private readonly LitePodcastProgressStore _podcasts;
    private readonly LiteBookmarkStore? _bookmarks;
    private readonly PodcastFeedClient _rssClient = new();
    private int _importInProgress;

    public LitePodcastOpmlCoordinator(
        LitePodcastProgressStore podcasts,
        LiteBookmarkStore? bookmarks)
    {
        _podcasts = podcasts ?? throw new ArgumentNullException(nameof(podcasts));
        _bookmarks = bookmarks;
    }

    public object Inspect(JsonElement args)
    {
        var entries = ReadEntries(LiteArgs.RequirePath(args, "path"));
        return new
        {
            count = entries.Count,
            entries = entries.Select(entry => new
            {
                title = entry.Title,
                feedUrl = entry.FeedUri.AbsoluteUri,
                label = entry.Label,
                sourceKind = SourceKindName(entry.SourceKind)
            }).ToArray()
        };
    }

    public object Import(JsonElement args)
    {
        if (Interlocked.CompareExchange(ref _importInProgress, 1, 0) != 0)
            throw new LiteRequestException("Import podcastów już trwa.");

        try
        {
            var entries = ReadEntries(LiteArgs.RequirePath(args, "path"));
            var selected = ReadSelectedFeeds(args);
            var chosen = entries
                .Where(entry => selected.Contains(entry.FeedUri.AbsoluteUri))
                .ToArray();
            if (chosen.Length == 0)
                throw new LiteRequestException("Zaznacz co najmniej jeden podcast do importu.");

            using var concurrency = new SemaphoreSlim(MaximumParallelFetches);
            var tasks = chosen.Select(async entry =>
            {
                await concurrency.WaitAsync().ConfigureAwait(false);
                try
                {
                    if (entry.SourceKind is PodcastSourceKind.YouTubeChannel
                        or PodcastSourceKind.YouTubePlaylist)
                    {
                        // Import zapisuje wyłącznie trwałą tożsamość kolekcji.
                        // Nie uruchamia setek yt-dlp ani pobrań; zwykłe
                        // odświeżanie YouTube uzupełni materiały później.
                        _podcasts.AddSource(
                            CreateYouTubePlaceholder(entry),
                            entry.Title,
                            entry.SourceKind,
                            preserveExistingTitle: true,
                            preserveExistingMetadata: true);
                        return true;
                    }

                    var feed = await _rssClient.FetchAsync(
                        entry.FeedUri,
                        CancellationToken.None).ConfigureAwait(false);
                    if (feed.Episodes.Count == 0) return false;
                    if (_bookmarks is not null
                        && feed.Episodes.Any(episode => episode.Chapters is { Count: > 0 }))
                    {
                        _bookmarks.MutateBookmarks(bookmarks =>
                            _podcasts.AddSource(
                                feed,
                                entry.Title,
                                PodcastSourceKind.Rss,
                                bookmarks,
                                preserveExistingTitle: true));
                    }
                    else
                    {
                        _podcasts.AddSource(
                            feed,
                            entry.Title,
                            PodcastSourceKind.Rss,
                            preserveExistingTitle: true);
                    }
                    return true;
                }
                catch (Exception exception)
                {
                    // Jeden wadliwy kanał nie przerywa całego importu. Pełny
                    // AMC ma tę samą semantykę: wynik podaje liczbę sukcesów
                    // i niepowodzeń, a szczegóły techniczne zostają w logu.
                    Console.Error.WriteLine(
                        $"[lite-host] import OPML, {entry.Label}: {exception.Message}");
                    return false;
                }
                finally
                {
                    concurrency.Release();
                }
            }).ToArray();
            var results = Task.WhenAll(tasks).GetAwaiter().GetResult();
            var imported = results.Count(success => success);
            return new
            {
                selected = chosen.Length,
                imported,
                failed = chosen.Length - imported
            };
        }
        finally
        {
            Volatile.Write(ref _importInProgress, 0);
        }
    }

    public object Export(JsonElement args)
    {
        var path = NormalizePath(LiteArgs.RequirePath(args, "path"));
        var directory = Path.GetDirectoryName(path);
        if (string.IsNullOrWhiteSpace(directory) || !Directory.Exists(directory))
            throw new LiteRequestException("Folder docelowy eksportu OPML nie istnieje.");
        var entries = _podcasts.GetOpmlEntries();
        if (entries.Count == 0)
            throw new LiteRequestException("Biblioteka nie zawiera podcastów RSS do eksportu.");
        try
        {
            File.WriteAllBytes(path, PodcastOpmlWriter.Write(entries));
            return new { count = entries.Count, path };
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or NotSupportedException
            or ArgumentException)
        {
            throw new LiteRequestException("Nie można zapisać pliku OPML: " + exception.Message);
        }
    }

    public object ExportYouTube(JsonElement args)
    {
        var path = NormalizePath(LiteArgs.RequirePath(args, "path"));
        var directory = Path.GetDirectoryName(path);
        if (string.IsNullOrWhiteSpace(directory) || !Directory.Exists(directory))
            throw new LiteRequestException("Folder docelowy eksportu YouTube nie istnieje.");
        var collections = _podcasts.GetYouTubeCollectionsForExport();
        if (collections.Count == 0)
        {
            throw new LiteRequestException(
                "Biblioteka nie zawiera kanałów ani playlist YouTube, które można wyeksportować.");
        }

        var asOpml = string.Equals(
            Path.GetExtension(path),
            ".opml",
            StringComparison.OrdinalIgnoreCase);
        var channelCount = collections.Count(entry => entry.IsChannel);
        if (!asOpml && channelCount == 0)
        {
            throw new LiteRequestException(
                "Plik subskrypcji YouTube obejmuje tylko kanały, a biblioteka zawiera same playlisty. Wybierz zapis do OPML.");
        }
        try
        {
            File.WriteAllBytes(
                path,
                asOpml
                    ? YouTubeSubscriptionsExporter.WriteFeedOpml(collections)
                    : YouTubeSubscriptionsExporter.WriteTakeoutCsv(collections));
            return new
            {
                format = asOpml ? "opml" : "csv",
                exported = asOpml ? collections.Count : channelCount,
                skippedPlaylists = asOpml ? 0 : collections.Count - channelCount,
                path
            };
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or NotSupportedException
            or ArgumentException)
        {
            throw new LiteRequestException("Nie można zapisać pliku: " + exception.Message);
        }
    }

    private static IReadOnlyList<PodcastOpmlEntry> ReadEntries(string path)
    {
        var fullPath = NormalizePath(path);
        if (!File.Exists(fullPath))
            throw new LiteRequestException("Nie znaleziono wskazanego pliku importu.");
        try
        {
            var info = new FileInfo(fullPath);
            var maximumBytes = Path.GetExtension(fullPath).Equals(".zip", StringComparison.OrdinalIgnoreCase)
                ? YouTubeSubscriptionFileImport.MaximumZipInputBytes
                : YouTubeSubscriptionFileImport.MaximumTextCharacters;
            if (info.Length > maximumBytes)
                throw new LiteRequestException("Plik importu jest zbyt duży.");

            IReadOnlyList<PodcastOpmlEntry> entries;
            switch (Path.GetExtension(fullPath).ToLowerInvariant())
            {
                case ".csv":
                    entries = YouTubeSubscriptionFileImport.ParseCsv(File.ReadAllText(fullPath));
                    break;
                case ".zip":
                    using (var stream = File.OpenRead(fullPath))
                        entries = YouTubeSubscriptionFileImport.ParseZip(stream);
                    break;
                case ".json":
                    entries = YouTubeSubscriptionFileImport.ParseJson(File.ReadAllText(fullPath));
                    break;
                case ".db" when Path.GetFileName(fullPath).Equals("profiles.db", StringComparison.OrdinalIgnoreCase):
                    entries = YouTubeSubscriptionFileImport.ParseFreeTubeDatabase(File.ReadAllText(fullPath));
                    break;
                case ".opml":
                case ".xml":
                    entries = PodcastOpmlParser.Parse(File.ReadAllText(fullPath));
                    break;
                default:
                    throw new LiteRequestException(
                        "Obsługiwane są OPML, YouTube Takeout subscriptions.csv/ZIP, NewPipe JSON oraz FreeTube profiles.db.");
            }
            if (entries.Count == 0)
                throw new LiteRequestException("Plik importu nie zawiera obsługiwanych źródeł podcastów ani kanałów YouTube.");
            return entries;
        }
        catch (LiteRequestException)
        {
            throw;
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or InvalidDataException
            or System.Xml.XmlException
            or JsonException)
        {
            throw new LiteRequestException("Nie można odczytać pliku importu: " + exception.Message);
        }
    }

    private static PodcastFeedDocument CreateYouTubePlaceholder(PodcastOpmlEntry entry)
    {
        var uri = entry.FeedUri;
        var identifier = entry.SourceKind switch
        {
            PodcastSourceKind.YouTubeChannel => uri.AbsolutePath
                .Split('/', StringSplitOptions.RemoveEmptyEntries)
                .SkipWhile(segment => !segment.Equals("channel", StringComparison.OrdinalIgnoreCase))
                .Skip(1)
                .FirstOrDefault(),
            PodcastSourceKind.YouTubePlaylist => uri.Query
                .TrimStart('?')
                .Split('&', StringSplitOptions.RemoveEmptyEntries)
                .Select(pair => pair.Split('=', 2))
                .Where(pair => pair.Length == 2 && pair[0].Equals("list", StringComparison.OrdinalIgnoreCase))
                .Select(pair => Uri.UnescapeDataString(pair[1]))
                .FirstOrDefault(),
            _ => null
        };
        if (string.IsNullOrWhiteSpace(identifier))
            throw new InvalidDataException("Kanał lub playlista YouTube nie ma poprawnej trwałej tożsamości.");
        var kind = entry.SourceKind == PodcastSourceKind.YouTubeChannel ? "channel" : "playlist";
        return new PodcastFeedDocument(
            $"youtube-{kind}:{identifier}",
            entry.Title,
            string.Empty,
            string.Empty,
            uri,
            entry.HomepageUri,
            []);
    }

    private static string SourceKindName(PodcastSourceKind sourceKind) => sourceKind switch
    {
        PodcastSourceKind.YouTubeChannel => "youtubeChannel",
        PodcastSourceKind.YouTubePlaylist => "youtubePlaylist",
        _ => "rss"
    };

    private static HashSet<string> ReadSelectedFeeds(JsonElement args)
    {
        if (args.ValueKind != JsonValueKind.Object
            || !args.TryGetProperty("feedUrls", out var values)
            || values.ValueKind != JsonValueKind.Array)
        {
            throw new LiteRequestException("Brak listy podcastów wybranych do importu.");
        }
        var result = new HashSet<string>(StringComparer.Ordinal);
        foreach (var value in values.EnumerateArray())
        {
            if (result.Count >= PodcastOpmlParser.MaximumEntries)
                throw new LiteRequestException("Wybrano zbyt wiele podcastów do importu.");
            if (value.ValueKind != JsonValueKind.String) continue;
            var text = value.GetString()?.Trim();
            if (string.IsNullOrWhiteSpace(text) || text.Length > LiteArgs.MaximumTextLength)
                continue;
            result.Add(text);
        }
        return result;
    }

    private static string NormalizePath(string path)
    {
        try
        {
            return Path.GetFullPath(path);
        }
        catch (Exception exception) when (exception is ArgumentException
            or NotSupportedException
            or PathTooLongException)
        {
            throw new LiteRequestException("Wskazana ścieżka pliku OPML jest niepoprawna.");
        }
    }

    public void Dispose() => _rssClient.Dispose();
}
