using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Resolves a public SoundCloud profile to the creator's public podcast RSS.
/// The RSS contains ordinary enclosure addresses, so playback and downloads
/// use AMC's existing podcast pipeline instead of the SoundCloud web player.
/// </summary>
internal sealed partial class SoundCloudPodcastClient : IDisposable
{
    private const int MaximumRedirects = 5;
    private const int MaximumProfileBytes = 2 * 1024 * 1024;
    private static readonly TimeSpan DefaultTimeout = TimeSpan.FromSeconds(15);
    private static readonly HashSet<string> ReservedFirstSegments = new(
        [
            "charts", "discover", "jobs", "login", "messages", "mobile",
            "popular", "search", "settings", "signin", "signup", "stream",
            "terms-of-use", "upload", "you"
        ],
        StringComparer.OrdinalIgnoreCase);

    private readonly HttpClient _client;
    private readonly TimeSpan _timeout;

    public SoundCloudPodcastClient()
        : this(new HttpClientHandler
        {
            AllowAutoRedirect = false,
            AutomaticDecompression = DecompressionMethods.GZip
                | DecompressionMethods.Deflate
                | DecompressionMethods.Brotli,
            UseCookies = false
        })
    {
    }

    internal SoundCloudPodcastClient(
        HttpMessageHandler handler,
        TimeSpan? timeout = null)
    {
        _client = new HttpClient(handler, disposeHandler: true);
        _timeout = timeout ?? DefaultTimeout;
        _client.DefaultRequestHeaders.UserAgent.ParseAdd(
            "AccessibleMultimediaController/0.1");
    }

    internal async Task<Uri> ResolveFeedAddressAsync(
        Uri address,
        CancellationToken cancellationToken = default)
    {
        if (TryNormalizeFeedAddress(address, out var feedAddress))
            return feedAddress;
        if (!TryNormalizeProfileAddress(address, out var profileAddress))
        {
            throw new InvalidDataException(
                "Adres SoundCloud musi prowadzić do publicznego profilu albo jego kanału RSS.");
        }

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(
            cancellationToken);
        timeout.CancelAfter(_timeout);
        var current = profileAddress;
        for (var redirect = 0; ; redirect++)
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, current);
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("text/html"));
            using var response = await _client.SendAsync(
                    request,
                    HttpCompletionOption.ResponseHeadersRead,
                    timeout.Token)
                .ConfigureAwait(false);
            if (IsRedirect(response.StatusCode))
            {
                if (redirect >= MaximumRedirects)
                    throw new InvalidDataException(
                        "Profil SoundCloud przekierowuje zbyt wiele razy.");
                var location = response.Headers.Location
                    ?? throw new InvalidDataException(
                        "Przekierowanie profilu SoundCloud nie zawiera adresu docelowego.");
                var redirected = location.IsAbsoluteUri
                    ? location
                    : new Uri(current, location);
                if (!TryNormalizeProfileAddress(redirected, out current))
                {
                    throw new InvalidDataException(
                        "Profil SoundCloud przekierował poza publiczny serwis SoundCloud.");
                }
                continue;
            }
            if (!response.IsSuccessStatusCode)
            {
                throw new HttpRequestException(
                    $"SoundCloud zwrócił kod {(int)response.StatusCode}.",
                    null,
                    response.StatusCode);
            }
            if (response.Content.Headers.ContentLength is > MaximumProfileBytes)
            {
                throw new InvalidDataException(
                    "Strona profilu SoundCloud jest zbyt duża.");
            }

            var html = await ReadLimitedTextAsync(response, timeout.Token)
                .ConfigureAwait(false);
            var profileSlug = Uri.UnescapeDataString(
                current.Segments[1].Trim('/'));
            var userId = ExtractProfileUserId(html, profileSlug)
                ?? throw new InvalidDataException(
                    "SoundCloud nie udostępnił kanału RSS dla tego profilu.");
            return BuildFeedAddress(userId);
        }
    }

    internal static bool IsSoundCloudSearchResult(MediaItem? item) =>
        Uri.TryCreate(item?.Source, UriKind.Absolute, out var address)
        && IsSoundCloudAddress(address);

    internal static bool IsSoundCloudAddress(Uri? address) =>
        TryNormalizeFeedAddress(address, out _)
        || TryNormalizeProfileAddress(address, out _);

    internal static bool IsSoundCloudHost(Uri? address) =>
        address is not null
        && address.IsAbsoluteUri
        && (IsProfileHost(address.Host)
            || address.Host.Equals(
                "feeds.soundcloud.com",
                StringComparison.OrdinalIgnoreCase));

    internal static bool TryNormalizeProfileAddress(
        Uri? address,
        out Uri normalized)
    {
        normalized = null!;
        if (address is null
            || !address.IsAbsoluteUri
            || address.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(address.UserInfo)
            || !IsProfileHost(address.Host))
        {
            return false;
        }
        var segments = address.AbsolutePath.Split(
            '/',
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (segments.Length != 1
            || segments[0].Length is < 1 or > 200
            || ReservedFirstSegments.Contains(Uri.UnescapeDataString(segments[0])))
        {
            return false;
        }
        normalized = new Uri(
            "https://soundcloud.com/" + Uri.EscapeDataString(
                Uri.UnescapeDataString(segments[0])));
        return true;
    }

    internal static bool TryNormalizeFeedAddress(Uri? address, out Uri normalized)
    {
        normalized = null!;
        if (address is null
            || !address.IsAbsoluteUri
            || address.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(address.UserInfo)
            || !address.Host.Equals("feeds.soundcloud.com", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        var match = FeedPathRegex().Match(address.AbsolutePath);
        if (!match.Success) return false;
        normalized = BuildFeedAddress(match.Groups["id"].Value);
        return true;
    }

    private static Uri BuildFeedAddress(string userId) => new(
        $"https://feeds.soundcloud.com/users/soundcloud:users:{userId}/sounds.rss");

    private static bool IsProfileHost(string host) =>
        host.Equals("soundcloud.com", StringComparison.OrdinalIgnoreCase)
        || host.Equals("www.soundcloud.com", StringComparison.OrdinalIgnoreCase)
        || host.Equals("m.soundcloud.com", StringComparison.OrdinalIgnoreCase);

    private static string? ExtractProfileUserId(string html, string profileSlug)
    {
        var hydration = HydrationRegex().Match(html);
        if (!hydration.Success) return null;
        try
        {
            using var document = JsonDocument.Parse(hydration.Groups["json"].Value);
            if (document.RootElement.ValueKind != JsonValueKind.Array) return null;
            foreach (var entry in document.RootElement.EnumerateArray())
            {
                if (!entry.TryGetProperty("hydratable", out var hydratable)
                    || !string.Equals(
                        hydratable.GetString(),
                        "user",
                        StringComparison.OrdinalIgnoreCase)
                    || !entry.TryGetProperty("data", out var data)
                    || data.ValueKind != JsonValueKind.Object
                    || !data.TryGetProperty("permalink", out var permalink)
                    || !string.Equals(
                        permalink.GetString(),
                        profileSlug,
                        StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                if (data.TryGetProperty("urn", out var urn))
                {
                    var match = UserUrnRegex().Match(urn.GetString() ?? string.Empty);
                    if (match.Success) return match.Groups["id"].Value;
                }
                if (data.TryGetProperty("id", out var id))
                {
                    var value = id.ValueKind switch
                    {
                        JsonValueKind.Number => id.GetRawText(),
                        JsonValueKind.String => id.GetString(),
                        _ => null
                    };
                    if (value is not null && UserIdRegex().IsMatch(value)) return value;
                }
            }
        }
        catch (JsonException)
        {
            return null;
        }
        return null;
    }

    private static async Task<string> ReadLimitedTextAsync(
        HttpResponseMessage response,
        CancellationToken cancellationToken)
    {
        await using var source = await response.Content
            .ReadAsStreamAsync(cancellationToken)
            .ConfigureAwait(false);
        await using var buffer = new MemoryStream();
        var block = new byte[16 * 1024];
        var total = 0;
        while (true)
        {
            var read = await source.ReadAsync(block, cancellationToken)
                .ConfigureAwait(false);
            if (read == 0) break;
            total += read;
            if (total > MaximumProfileBytes)
            {
                throw new InvalidDataException(
                    "Strona profilu SoundCloud jest zbyt duża.");
            }
            await buffer.WriteAsync(block.AsMemory(0, read), cancellationToken)
                .ConfigureAwait(false);
        }
        return Encoding.UTF8.GetString(buffer.GetBuffer(), 0, total);
    }

    private static bool IsRedirect(HttpStatusCode status) => status is
        HttpStatusCode.MovedPermanently
        or HttpStatusCode.Found
        or HttpStatusCode.SeeOther
        or HttpStatusCode.TemporaryRedirect
        or HttpStatusCode.PermanentRedirect;

    public void Dispose() => _client.Dispose();

    [GeneratedRegex(
        "^/users/soundcloud:users:(?<id>[0-9]{1,20})/sounds\\.rss$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex FeedPathRegex();

    [GeneratedRegex(
        "window\\.__sc_hydration\\s*=\\s*(?<json>\\[.*?\\]);\\s*</script>",
        RegexOptions.Singleline | RegexOptions.CultureInvariant)]
    private static partial Regex HydrationRegex();

    [GeneratedRegex(
        "^soundcloud:users:(?<id>[0-9]{1,20})$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex UserUrnRegex();

    [GeneratedRegex("^[0-9]{1,20}$", RegexOptions.CultureInvariant)]
    private static partial Regex UserIdRegex();
}
