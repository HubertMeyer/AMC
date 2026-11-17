using System.IO.Compression;
using System.Text;
using System.Text.Json;
using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Core.Podcasts;

/// <summary>
/// Parses only public YouTube channel subscriptions from local interchange
/// files. It deliberately does not read watch history, playlists, accounts or
/// any private export data, and it never performs a network request.
/// </summary>
public static class YouTubeSubscriptionFileImport
{
    public const int MaximumEntries = 1_000;
    public const int MaximumTextCharacters = 4 * 1024 * 1024;
    public const int MaximumZipInputBytes = 64 * 1024 * 1024;
    public const int MaximumZipEntries = 128;
    public const int MaximumZipPathDepth = 8;

    public static IReadOnlyList<PodcastOpmlEntry> ParseCsv(string csv)
    {
        ArgumentNullException.ThrowIfNull(csv);
        EnsureTextLimit(csv);
        var rows = CsvRows(csv).ToArray();
        if (rows.Length == 0) return [];
        var header = rows[0]
            .Select((value, index) => new { Name = value.Trim(), Index = index })
            .ToDictionary(value => value.Name, value => value.Index, StringComparer.OrdinalIgnoreCase);
        if (!header.TryGetValue("Channel Id", out var idIndex)
            || !header.TryGetValue("Channel Title", out var titleIndex))
        {
            throw new InvalidDataException(
                "Plik CSV nie ma nagłówków subskrypcji YouTube „Channel Id” i „Channel Title”.");
        }

        var result = new List<PodcastOpmlEntry>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        foreach (var row in rows.Skip(1))
        {
            if (idIndex >= row.Count || titleIndex >= row.Count) continue;
            Add(result, known, row[idIndex], row[titleIndex]);
            if (result.Count >= MaximumEntries) break;
        }
        return result;
    }

    /// <summary>Reads the documented NewPipe "previous export" JSON shape.</summary>
    public static IReadOnlyList<PodcastOpmlEntry> ParseJson(string json)
    {
        ArgumentNullException.ThrowIfNull(json);
        EnsureTextLimit(json);
        using var document = JsonDocument.Parse(json, new JsonDocumentOptions
        {
            MaxDepth = 32,
            CommentHandling = JsonCommentHandling.Disallow,
            AllowTrailingCommas = false
        });
        if (document.RootElement.ValueKind != JsonValueKind.Object
            || !document.RootElement.TryGetProperty("subscriptions", out var subscriptions)
            || subscriptions.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidDataException("Plik JSON nie jest eksportem subskrypcji NewPipe.");
        }

        var result = new List<PodcastOpmlEntry>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        foreach (var subscription in subscriptions.EnumerateArray())
        {
            if (subscription.ValueKind != JsonValueKind.Object) continue;
            if (subscription.TryGetProperty("service_id", out var service)
                && service.ValueKind == JsonValueKind.Number
                && service.TryGetInt32(out var serviceId)
                && serviceId != 0)
            {
                continue;
            }
            var channelUrl = ReadString(subscription, "url");
            if (TryChannelId(channelUrl, out var id))
            {
                Add(result, known, id, ReadString(subscription, "name"));
            }
            else
            {
                // FreeTube's documented profile records retain subscriptions
                // as { id, name } rather than NewPipe's { url, name }.
                Add(result, known, ReadString(subscription, "id"), ReadString(subscription, "name"));
            }
            if (result.Count >= MaximumEntries) break;
        }
        return result;
    }

    /// <summary>
    /// Reads a FreeTube NeDB subscriptions database. Each non-empty line must
    /// be one JSON record with a <c>subscriptions</c> array; history records
    /// have no such array and are ignored.
    /// </summary>
    public static IReadOnlyList<PodcastOpmlEntry> ParseFreeTubeDatabase(string database)
    {
        ArgumentNullException.ThrowIfNull(database);
        EnsureTextLimit(database);
        var result = new List<PodcastOpmlEntry>();
        var known = new HashSet<string>(StringComparer.Ordinal);
        using var reader = new StringReader(database);
        string? line;
        while ((line = reader.ReadLine()) is not null)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            if (line.Length > MaximumTextCharacters)
                throw new InvalidDataException("Wiersz bazy FreeTube jest zbyt duży.");
            using var document = JsonDocument.Parse(line, new JsonDocumentOptions { MaxDepth = 32 });
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object
                || !root.TryGetProperty("subscriptions", out var subscriptions)
                || subscriptions.ValueKind != JsonValueKind.Array)
            {
                continue;
            }
            foreach (var subscription in subscriptions.EnumerateArray())
            {
                if (subscription.ValueKind != JsonValueKind.Object) continue;
                Add(result, known, ReadString(subscription, "id"), ReadString(subscription, "name"));
                if (result.Count >= MaximumEntries) return result;
            }
        }
        return result;
    }

    /// <summary>
    /// Reads only a Takeout <c>subscriptions.csv</c> entry directly from the
    /// archive. Nothing is extracted to disk and no HTML is interpreted.
    /// </summary>
    public static IReadOnlyList<PodcastOpmlEntry> ParseZip(Stream stream)
    {
        ArgumentNullException.ThrowIfNull(stream);
        using var archive = new ZipArchive(stream, ZipArchiveMode.Read, leaveOpen: true);
        if (archive.Entries.Count > MaximumZipEntries)
            throw new InvalidDataException("Archiwum ma zbyt wiele plików.");
        ZipArchiveEntry? subscriptions = null;
        foreach (var entry in archive.Entries)
        {
            ValidateZipEntry(entry);
            if (IsTakeoutSubscriptionsEntry(entry.FullName))
            {
                if (subscriptions is not null)
                    throw new InvalidDataException("Archiwum zawiera więcej niż jeden plik subscriptions.csv.");
                subscriptions = entry;
            }
        }
        if (subscriptions is null)
            throw new InvalidDataException("Archiwum nie zawiera pliku subskrypcji YouTube subscriptions.csv.");
        if (subscriptions.Length > MaximumTextCharacters)
            throw new InvalidDataException("Plik subscriptions.csv w archiwum jest zbyt duży.");
        if (subscriptions.CompressedLength <= 0
            || subscriptions.Length > subscriptions.CompressedLength * 100L)
        {
            throw new InvalidDataException("Archiwum ma niedopuszczalny współczynnik kompresji.");
        }
        using var text = new StreamReader(subscriptions.Open(), Encoding.UTF8, detectEncodingFromByteOrderMarks: true);
        return ParseCsv(ReadBounded(text));
    }

    public static bool TryCreateFromFeedUri(
        Uri feedUri,
        string? title,
        out PodcastOpmlEntry entry)
    {
        entry = null!;
        if (feedUri.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(feedUri.UserInfo)
            || !(feedUri.IdnHost.Equals("youtube.com", StringComparison.OrdinalIgnoreCase)
                || feedUri.IdnHost.Equals("www.youtube.com", StringComparison.OrdinalIgnoreCase))
            || !feedUri.AbsolutePath.Equals("/feeds/videos.xml", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        var query = ParseQuery(feedUri.Query);
        if (query.TryGetValue("channel_id", out var channelId) && IsChannelId(channelId))
        {
            entry = Create(channelId, title);
            return true;
        }
        if (query.TryGetValue("playlist_id", out var playlistId) && IsSafeIdentifier(playlistId))
        {
            var id = playlistId.Trim();
            var homepage = new Uri($"https://www.youtube.com/playlist?list={Uri.EscapeDataString(id)}", UriKind.Absolute);
            entry = new PodcastOpmlEntry(
                NormalizeTitle(title) is { Length: > 0 } normalizedTitle ? normalizedTitle : "Playlista YouTube",
                homepage,
                homepage,
                PodcastSourceKind.YouTubePlaylist);
            return true;
        }
        return false;
    }

    private static void Add(
        List<PodcastOpmlEntry> result,
        HashSet<string> known,
        string? channelId,
        string? title)
    {
        if (!IsChannelId(channelId)) return;
        var id = channelId!.Trim();
        if (!known.Add(id)) return;
        result.Add(Create(id, title));
    }

    private static PodcastOpmlEntry Create(string channelId, string? title)
    {
        var id = channelId.Trim();
        var normalizedTitle = NormalizeTitle(title);
        var homepage = new Uri($"https://www.youtube.com/channel/{Uri.EscapeDataString(id)}", UriKind.Absolute);
        return new PodcastOpmlEntry(
            normalizedTitle.Length == 0 ? "Kanał YouTube" : normalizedTitle,
            new Uri(homepage.AbsoluteUri.TrimEnd('/') + "/videos", UriKind.Absolute),
            homepage,
            PodcastSourceKind.YouTubeChannel);
    }

    private static bool TryChannelId(string? value, out string channelId)
    {
        channelId = string.Empty;
        if (!Uri.TryCreate(value?.Trim(), UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(uri.UserInfo)
            || !(uri.IdnHost.Equals("youtube.com", StringComparison.OrdinalIgnoreCase)
                || uri.IdnHost.Equals("www.youtube.com", StringComparison.OrdinalIgnoreCase)))
        {
            return false;
        }
        var segments = uri.AbsolutePath.Split('/', StringSplitOptions.RemoveEmptyEntries);
        if (segments.Length < 2 || !segments[0].Equals("channel", StringComparison.OrdinalIgnoreCase))
            return false;
        if (!IsChannelId(segments[1])) return false;
        channelId = segments[1];
        return true;
    }

    private static bool IsChannelId(string? value) =>
        !string.IsNullOrWhiteSpace(value)
        && value.Trim().StartsWith("UC", StringComparison.Ordinal)
        && IsSafeIdentifier(value);

    private static bool IsSafeIdentifier(string? value) =>
        !string.IsNullOrWhiteSpace(value)
        && value.Trim().Length is >= 4 and <= 160
        && value.Trim().All(character => char.IsAsciiLetterOrDigit(character) || character is '_' or '-');

    private static string? ReadString(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString()
            : null;

    private static string NormalizeTitle(string? value)
    {
        var cleaned = new string((value ?? string.Empty)
            .Where(character => !char.IsControl(character))
            .ToArray());
        var normalized = string.Join(' ', cleaned
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        return normalized.Length <= 300 ? normalized : normalized[..300].TrimEnd();
    }

    private static Dictionary<string, string> ParseQuery(string query)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var pair in query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries))
        {
            var split = pair.Split('=', 2);
            var key = Uri.UnescapeDataString(split[0]);
            if (key.Length == 0 || result.ContainsKey(key)) continue;
            result[key] = split.Length == 2 ? Uri.UnescapeDataString(split[1]) : string.Empty;
        }
        return result;
    }

    private static IEnumerable<IReadOnlyList<string>> CsvRows(string text)
    {
        var row = new List<string>();
        var field = new StringBuilder();
        var quoted = false;
        for (var index = 0; index < text.Length; index++)
        {
            var character = text[index];
            if (character == '"')
            {
                if (quoted && index + 1 < text.Length && text[index + 1] == '"')
                {
                    field.Append('"');
                    index++;
                }
                else quoted = !quoted;
                continue;
            }
            if (character == ',' && !quoted)
            {
                row.Add(field.ToString());
                field.Clear();
                continue;
            }
            if ((character == '\r' || character == '\n') && !quoted)
            {
                if (character == '\r' && index + 1 < text.Length && text[index + 1] == '\n') index++;
                row.Add(field.ToString());
                field.Clear();
                if (row.Any(value => value.Length > 0)) yield return row;
                row = new List<string>();
                continue;
            }
            field.Append(character);
        }
        if (quoted) throw new InvalidDataException("CSV subskrypcji ma niezamknięte pole tekstowe.");
        row.Add(field.ToString());
        if (row.Any(value => value.Length > 0)) yield return row;
    }

    private static void ValidateZipEntry(ZipArchiveEntry entry)
    {
        var parts = entry.FullName.Replace('\\', '/').Split('/', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length > MaximumZipPathDepth
            || parts.Any(part => part is "." or ".." || part.Contains('\0')))
        {
            throw new InvalidDataException("Archiwum ma niedozwoloną ścieżkę pliku.");
        }
    }

    private static bool IsTakeoutSubscriptionsEntry(string path)
    {
        var parts = path.Replace('\\', '/').Split('/', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length >= 2
            && parts[^1].Equals("subscriptions.csv", StringComparison.OrdinalIgnoreCase)
            && parts[^2].Equals("subscriptions", StringComparison.OrdinalIgnoreCase);
    }

    private static string ReadBounded(TextReader reader)
    {
        var buffer = new char[8192];
        var builder = new StringBuilder();
        int read;
        while ((read = reader.Read(buffer, 0, buffer.Length)) > 0)
        {
            if (builder.Length + read > MaximumTextCharacters)
                throw new InvalidDataException("Plik subskrypcji jest zbyt duży.");
            builder.Append(buffer, 0, read);
        }
        return builder.ToString();
    }

    private static void EnsureTextLimit(string value)
    {
        if (value.Length > MaximumTextCharacters)
            throw new InvalidDataException("Plik subskrypcji jest zbyt duży.");
    }
}
