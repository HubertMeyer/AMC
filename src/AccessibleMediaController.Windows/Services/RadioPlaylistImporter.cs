using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;

namespace AccessibleMediaController.Windows.Services;

internal sealed record ImportedRadioStation(string Name, string StreamUrl);

internal sealed record RadioPlaylistImportResult(
    IReadOnlyList<ImportedRadioStation> Stations,
    int SkippedEntries);

internal static class RadioPlaylistImporter
{
    private const long MaximumPlaylistBytes = 4 * 1024 * 1024;
    private const int MaximumStations = 5_000;
    private const int MaximumStreamUrlLength = 4_096;
    private const int MaximumStationNameLength = 200;
    private const int MaximumParallelNameRequests = 16;
    // Żywe serwery oddają nagłówki w ułamku sekundy; dłuższy limit tylko
    // wydłuża ciszę po imporcie przez martwy adres i komunikat ginie.
    private static readonly TimeSpan NameRequestTimeout = TimeSpan.FromSeconds(2);
    private static readonly TimeSpan NameLookupBudget = TimeSpan.FromSeconds(20);
    private static readonly Encoding StrictUtf8 = new UTF8Encoding(false, true);

    public static RadioPlaylistImportResult Import(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var info = new FileInfo(path);
        if (!info.Exists) throw new FileNotFoundException("Nie znaleziono playlisty radia.", path);
        if (info.Length > MaximumPlaylistBytes)
        {
            throw new InvalidDataException("Playlista jest zbyt duża, aby bezpiecznie ją zaimportować.");
        }

        var text = File.ReadAllText(path, Encoding.UTF8);
        var extension = Path.GetExtension(path);
        IEnumerable<(string? Name, string? Url)> candidates = extension.ToLowerInvariant() switch
        {
            ".pls" => ParsePls(text),
            ".xspf" => ParseXspf(text),
            ".json" => ParseVRadioJson(text),
            _ => ParseM3u(text)
        };

        var stations = new List<(string? Name, string Url)>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var skipped = 0;
        foreach (var (name, url) in candidates.Take(MaximumStations + 1))
        {
            if (stations.Count >= MaximumStations)
            {
                skipped++;
                continue;
            }
            if (!TryNormalizeStreamUrl(url, out var normalizedUrl) || !seen.Add(normalizedUrl))
            {
                skipped++;
                continue;
            }

            stations.Add((name, normalizedUrl));
        }

        var names = ReadMissingNamesFromStreams(stations);
        return new RadioPlaylistImportResult(
            stations
                .Select((station, index) => new ImportedRadioStation(
                    NormalizeName(names[index], station.Url),
                    station.Url))
                .ToArray(),
            skipped);
    }

    /// <summary>
    /// Playlista z samymi adresami (M3U bez #EXTINF) nie niesie nazw stacji.
    /// Tak jak foobar2000 pytamy wtedy serwer: Icecast i SHOUTcast podają
    /// nazwę w nagłówku icy-name. Wystarczą same nagłówki, bez pobierania
    /// strumienia; gdy serwer milczy, zostaje nazwa hosta.
    /// </summary>
    private static string?[] ReadMissingNamesFromStreams(IReadOnlyList<(string? Name, string Url)> stations)
    {
        var names = stations.Select(station => station.Name).ToArray();
        var missing = Enumerable.Range(0, names.Length)
            .Where(index => string.IsNullOrWhiteSpace(names[index]))
            .ToArray();
        if (missing.Length == 0) return names;

        using var client = new HttpClient { Timeout = NameRequestTimeout };
        client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMediaController/0.1");
        using var budget = new CancellationTokenSource(NameLookupBudget);
        try
        {
            Parallel.ForEachAsync(
                    missing,
                    new ParallelOptions
                    {
                        MaxDegreeOfParallelism = MaximumParallelNameRequests,
                        CancellationToken = budget.Token
                    },
                    async (index, token) =>
                        names[index] = await ReadIcyNameAsync(client, stations[index].Url, token)
                            .ConfigureAwait(false))
                .GetAwaiter()
                .GetResult();
        }
        catch (OperationCanceledException)
        {
            // ponytail: jeden limit czasu na cały import; stacje niesprawdzone
            // w tym czasie zostają z nazwą hosta. Przy tysiącach stacji bez nazw
            // lepsze byłoby uzupełnianie nazw w tle po imporcie.
        }
        return names;
    }

    private static async Task<string?> ReadIcyNameAsync(
        HttpClient client,
        string url,
        CancellationToken cancellationToken)
    {
        string? raw;
        try
        {
            using var response = await client
                .GetAsync(url, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
                .ConfigureAwait(false);
            raw = response.Headers.TryGetValues("icy-name", out var values) ? values.FirstOrDefault() : null;
        }
        catch (HttpRequestException exception) when (exception.HttpRequestError == HttpRequestError.InvalidResponse)
        {
            // SHOUTcast v1 odpowiada „ICY 200 OK”, którego HttpClient nie przyjmuje.
            raw = await ReadShoutcastV1NameAsync(new Uri(url), cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception) when (exception is HttpRequestException
            or IOException
            or OperationCanceledException)
        {
            return null;
        }

        // Część serwerów wysyła zaślepkę, np. „-”; to nie jest nazwa.
        if (raw is null || !raw.Any(char.IsLetterOrDigit)) return null;
        // Nagłówki czytamy jako Latin-1, a Icecast zwykle wysyła UTF-8;
        // bez tego „Złote Przeboje” byłyby krzakami.
        try
        {
            return StrictUtf8.GetString(Encoding.Latin1.GetBytes(raw));
        }
        catch (DecoderFallbackException)
        {
            return raw;
        }
    }

    private static async Task<string?> ReadShoutcastV1NameAsync(Uri uri, CancellationToken cancellationToken)
    {
        if (uri.Scheme != Uri.UriSchemeHttp) return null;
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(NameRequestTimeout);
        try
        {
            using var tcp = new System.Net.Sockets.TcpClient();
            await tcp.ConnectAsync(uri.Host, uri.Port, timeout.Token).ConfigureAwait(false);
            var stream = tcp.GetStream();
            await stream.WriteAsync(
                    Encoding.ASCII.GetBytes(
                        $"GET {uri.PathAndQuery} HTTP/1.0\r\nHost: {uri.Authority}\r\n"
                        + "User-Agent: AccessibleMediaController/0.1\r\n\r\n"),
                    timeout.Token)
                .ConfigureAwait(false);
            var buffer = new byte[16 * 1024];
            var length = 0;
            while (length < buffer.Length
                && buffer.AsSpan(0, length).IndexOf("\r\n\r\n"u8) < 0)
            {
                var read = await stream.ReadAsync(buffer.AsMemory(length), timeout.Token).ConfigureAwait(false);
                if (read == 0) break;
                length += read;
            }
            var lines = Encoding.Latin1.GetString(buffer, 0, length).Split("\r\n");
            if (!lines[0].StartsWith("ICY ", StringComparison.Ordinal)) return null;
            return lines
                .TakeWhile(line => line.Length > 0)
                .FirstOrDefault(line => line.StartsWith("icy-name:", StringComparison.OrdinalIgnoreCase))?
                ["icy-name:".Length..]
                .Trim();
        }
        catch (Exception exception) when (exception is System.Net.Sockets.SocketException
            or IOException
            or OperationCanceledException)
        {
            return null;
        }
    }

    private static IEnumerable<(string? Name, string? Url)> ParseM3u(string text)
    {
        if (SplitLines(text).Any(line => line.TrimStart().StartsWith("#EXT-X-", StringComparison.OrdinalIgnoreCase)))
        {
            throw new InvalidDataException("Wybrany plik jest manifestem jednej transmisji HLS, a nie listą stacji.");
        }
        string? pendingName = null;
        foreach (var rawLine in SplitLines(text))
        {
            var line = rawLine.Trim().TrimStart('\uFEFF');
            if (line.Length == 0) continue;
            if (line.StartsWith("#EXTINF", StringComparison.OrdinalIgnoreCase))
            {
                var comma = line.IndexOf(',');
                pendingName = comma >= 0 && comma + 1 < line.Length
                    ? line[(comma + 1)..]
                    : null;
                continue;
            }
            if (line.StartsWith('#')) continue;
            yield return (pendingName, line);
            pendingName = null;
        }
    }

    private static IEnumerable<(string? Name, string? Url)> ParsePls(string text)
    {
        var files = new Dictionary<int, string>();
        var titles = new Dictionary<int, string>();
        foreach (var rawLine in SplitLines(text))
        {
            var line = rawLine.Trim();
            var equals = line.IndexOf('=');
            if (equals <= 0) continue;
            var key = line[..equals].Trim();
            var value = line[(equals + 1)..].Trim();
            if (TryReadIndexedKey(key, "File", out var fileIndex)) files[fileIndex] = value;
            else if (TryReadIndexedKey(key, "Title", out var titleIndex)) titles[titleIndex] = value;
        }

        foreach (var (index, url) in files.OrderBy(pair => pair.Key))
        {
            yield return (titles.GetValueOrDefault(index), url);
        }
    }

    private static IEnumerable<(string? Name, string? Url)> ParseXspf(string text)
    {
        using var stringReader = new StringReader(text);
        using var xmlReader = XmlReader.Create(stringReader, new XmlReaderSettings
        {
            DtdProcessing = DtdProcessing.Prohibit,
            XmlResolver = null,
            MaxCharactersInDocument = MaximumPlaylistBytes
        });
        var document = XDocument.Load(xmlReader, LoadOptions.None);
        foreach (var track in document.Descendants().Where(element => element.Name.LocalName == "track"))
        {
            var location = track.Elements().FirstOrDefault(element => element.Name.LocalName == "location")?.Value;
            var title = track.Elements().FirstOrDefault(element => element.Name.LocalName == "title")?.Value;
            yield return (title, location);
        }
    }

    private static IEnumerable<(string? Name, string? Url)> ParseVRadioJson(string text)
    {
        using var document = JsonDocument.Parse(text, new JsonDocumentOptions
        {
            AllowTrailingCommas = true,
            CommentHandling = JsonCommentHandling.Skip,
            MaxDepth = 64
        });
        if (document.RootElement.ValueKind != JsonValueKind.Object
            || !document.RootElement.TryGetProperty("stations", out var stations)
            || stations.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidDataException("Plik JSON nie zawiera listy stacji VRadio.");
        }

        foreach (var station in stations.EnumerateArray())
        {
            if (station.ValueKind != JsonValueKind.Object) continue;
            var name = TryGetString(station, "name");
            if (!station.TryGetProperty("streams", out var streams)
                || streams.ValueKind != JsonValueKind.Array)
            {
                yield return (name, null);
                continue;
            }

            string? selectedUrl = null;
            foreach (var stream in streams.EnumerateArray())
            {
                if (stream.ValueKind != JsonValueKind.Object) continue;
                var candidate = TryGetString(stream, "url");
                if (!TryNormalizeStreamUrl(candidate, out selectedUrl)) continue;
                break;
            }
            yield return (name, selectedUrl);
        }
    }

    private static string? TryGetString(JsonElement element, string propertyName) =>
        element.TryGetProperty(propertyName, out var property)
        && property.ValueKind == JsonValueKind.String
            ? property.GetString()
            : null;

    private static bool TryReadIndexedKey(string key, string prefix, out int index)
    {
        index = 0;
        return key.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)
            && int.TryParse(key.AsSpan(prefix.Length), out index)
            && index > 0;
    }

    private static bool TryNormalizeStreamUrl(string? value, out string normalized)
    {
        normalized = string.Empty;
        if (string.IsNullOrWhiteSpace(value) || value.Length > MaximumStreamUrlLength) return false;
        var trimmed = value.Trim();
        if (trimmed.Any(character => char.IsControl(character) || char.IsWhiteSpace(character))) return false;
        if (!Uri.TryCreate(trimmed, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || string.IsNullOrWhiteSpace(uri.Host))
        {
            return false;
        }
        normalized = uri.AbsoluteUri;
        return true;
    }

    private static string NormalizeName(string? value, string streamUrl)
    {
        var builder = new StringBuilder();
        var previousWasSpace = false;
        foreach (var character in value ?? string.Empty)
        {
            if (char.IsControl(character) || character == '\uFFFC') continue;
            if (char.IsWhiteSpace(character))
            {
                if (builder.Length > 0 && !previousWasSpace) builder.Append(' ');
                previousWasSpace = true;
                continue;
            }
            builder.Append(character);
            previousWasSpace = false;
            if (builder.Length >= MaximumStationNameLength) break;
        }
        var name = builder.ToString().Trim();
        if (name.Length > 0) return name;
        return Uri.TryCreate(streamUrl, UriKind.Absolute, out var uri) && uri.Host.Length > 0
            ? uri.Host
            : "Stacja radiowa";
    }

    private static IEnumerable<string> SplitLines(string text) =>
        text.Replace("\r\n", "\n", StringComparison.Ordinal).Replace('\r', '\n').Split('\n');
}
