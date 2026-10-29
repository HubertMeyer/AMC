using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using AccessibleMediaController.Core.Podcasts;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Experimental, anonymous reader for recent public Facebook Page video posts.
/// Facebook does not document this endpoint; a changed response is an explicit
/// refresh failure, never an empty feed that could mislead the user.
/// </summary>
internal sealed class FacebookPublicPageClient : IDisposable
{
    private const int MaximumResponseBytes = 4 * 1024 * 1024;
    private const int MaximumPosts = 30;
    private const string QueryName = "ProfileCometTimelineFeedRefetchQuery";
    private const string QueryId = "28844200915213260";

    // Query provider variables adapted from RSSHub's Facebook route (MIT license):
    // https://github.com/DIYgod/RSSHub/blob/master/lib/routes/facebook/utils.ts
    // These may change independently of AMC and are confined to this client.
    private const string ProviderVariablesJson = """
        {"__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider":false,"__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider":false,"__relay_internal__pv__CometFeedStory_enable_reactor_facepilerelayprovider":false,"__relay_internal__pv__CometFeedStory_enable_social_bubblesrelayprovider":false,"__relay_internal__pv__CometFeedStory_enable_post_permalink_white_space_clickrelayprovider":false,"__relay_internal__pv__CometUFICommentActionLinksRewriteEnabledrelayprovider":false,"__relay_internal__pv__CometUFICommentAvatarStickerAnimatedImagerelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__TestPilotShouldIncludeDemoAdUseCaserelayprovider":false,"__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider":false,"__relay_internal__pv__CometUFI_dedicated_comment_routable_dialog_gkrelayprovider":true,"__relay_internal__pv__FBReels_enable_view_dubbed_audio_type_gkrelayprovider":false,"__relay_internal__pv__CometFeedShareMedia_shouldPrefetchShareImagerelayprovider":false,"__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider":false,"__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider":true,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__CometUFICommentAutoTranslationTyperelayprovider":"AUTO_TRANSLATE","__relay_internal__pv__CometUFIShareActionMigrationrelayprovider":true,"__relay_internal__pv__CometUFISingleLineUFIrelayprovider":false,"__relay_internal__pv__relay_provider_comet_ufi_ssr_seo_deferrelayprovider":true,"__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider":false,"__relay_internal__pv__GroupsCometGYSJFeedItemHeightrelayprovider":150,"__relay_internal__pv__StoriesShouldEnablePhotosensitiveContentWarningrelayprovider":false,"__relay_internal__pv__ShouldEnableBakedInTextStoriesrelayprovider":false,"__relay_internal__pv__StoriesShouldIncludeFbNotesrelayprovider":false}
        """;

    private readonly HttpClient _http = new(new HttpClientHandler
    {
        AutomaticDecompression = System.Net.DecompressionMethods.All
    })
    {
        Timeout = TimeSpan.FromSeconds(25)
    };

    internal FacebookPublicPageClient()
    {
        _http.DefaultRequestHeaders.UserAgent.ParseAdd(
            "Mozilla/5.0 (Windows NT 10.0; Microsoft Windows 10.0.26300; pl-PL) PowerShell/7.6.5");
    }

    internal static bool TryNormalizePageAddress(Uri address, out Uri normalized)
    {
        normalized = null!;
        if (address.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(address.UserInfo)
            || !(address.IdnHost.Equals("facebook.com", StringComparison.OrdinalIgnoreCase)
                || address.IdnHost.EndsWith(".facebook.com", StringComparison.OrdinalIgnoreCase)))
            return false;
        var segments = address.AbsolutePath.Split('/', StringSplitOptions.RemoveEmptyEntries);
        if (segments.Length != 1 || !string.IsNullOrEmpty(address.Query)) return false;
        var name = segments[0];
        if (!Regex.IsMatch(name, "^[A-Za-z0-9._-]{2,100}$", RegexOptions.CultureInvariant)
            || name is "watch" or "reel" or "reels" or "videos" or "video.php"
                or "posts" or "groups" or "events" or "profile.php") return false;
        normalized = new Uri("https://www.facebook.com/" + name + "/");
        return true;
    }

    internal async Task<PodcastFeedDocument> FetchAsync(Uri address, CancellationToken cancellationToken)
    {
        if (!TryNormalizePageAddress(address, out var page))
            throw new InvalidDataException("Podaj adres publicznej strony Facebooka, na przykład https://www.facebook.com/buremisie/.");
        try
        {
            var id = await ResolvePageIdAsync(page, cancellationToken).ConfigureAwait(false);
            var response = await FetchPostsAsync(id, cancellationToken).ConfigureAwait(false);
            return ParseResponse(response, page, id);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException("Facebook nie odpowiedział w bezpiecznym czasie.");
        }
    }

    private async Task<string> ResolvePageIdAsync(Uri page, CancellationToken cancellationToken)
    {
        var url = "https://www.facebook.com/plugins/page.php?href="
            + Uri.EscapeDataString(page.AbsoluteUri);
        using var response = await _http.GetAsync(url, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        var html = await ReadBoundedAsync(response, cancellationToken).ConfigureAwait(false);
        var index = html.IndexOf("initializeClickLoggers", StringComparison.Ordinal);
        var window = index >= 0 ? html[index..Math.Min(html.Length, index + 500)] : html;
        var match = Regex.Match(window, """false,\\?"(?<id>\d{8,20})""");
        if (!match.Success)
            match = Regex.Match(html, """\\?"pageID\\?"\s*:\s*\\?"(?<id>\d{8,20})""");
        if (!match.Success)
            throw new InvalidDataException("Facebook nie udostępnił identyfikatora tej publicznej strony.");
        return match.Groups["id"].Value;
    }

    private async Task<string> FetchPostsAsync(string id, CancellationToken cancellationToken)
    {
        var lsd = Convert.ToBase64String(RandomNumberGenerator.GetBytes(16))
            .TrimEnd('=').Replace('+', '-').Replace('/', '_');
        var jazoest = "2" + lsd.Sum(character => (int)character);
        using var provider = JsonDocument.Parse(ProviderVariablesJson);
        var variables = new Dictionary<string, object?>();
        foreach (var property in provider.RootElement.EnumerateObject())
        {
            variables.Add(property.Name, property.Value.ValueKind switch
            {
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                JsonValueKind.Number => property.Value.GetInt32(),
                _ => property.Value.GetString()
            });
        }
        variables["id"] = id;
        variables["feedLocation"] = "TIMELINE";
        variables["feedbackSource"] = 0;
        variables["omitPinnedPost"] = true;
        variables["privacySelectorRenderLocation"] = "COMET_STREAM";
        variables["renderLocation"] = "timeline";
        variables["run_with_continuation_key"] = false;
        variables["stream_count"] = 1;
        variables["count"] = MaximumPosts;
        variables["cursor"] = null;
        variables["scale"] = 1;
        variables["useDefaultActor"] = false;

        using var content = new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["lsd"] = lsd,
            ["jazoest"] = jazoest,
            ["fb_api_req_friendly_name"] = QueryName,
            ["variables"] = JsonSerializer.Serialize(variables),
            ["doc_id"] = QueryId
        });
        using var request = new HttpRequestMessage(HttpMethod.Post, "https://www.facebook.com/api/graphql/")
        {
            Content = content
        };
        request.Headers.TryAddWithoutValidation("x-fb-lsd", lsd);
        request.Headers.TryAddWithoutValidation("accept-language", "en-US");
        using var response = await _http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            throw new InvalidDataException(
                "Facebook odmówił odczytu publicznych wpisów. Spróbuj ponownie później.");
        }
        return await ReadBoundedAsync(response, cancellationToken).ConfigureAwait(false);
    }

    private static async Task<string> ReadBoundedAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        if (response.Content.Headers.ContentLength is > MaximumResponseBytes)
            throw new InvalidDataException("Facebook zwrócił zbyt dużo danych.");
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        using var buffer = new MemoryStream();
        var block = new byte[16 * 1024];
        int read;
        while ((read = await stream.ReadAsync(block, cancellationToken).ConfigureAwait(false)) > 0)
        {
            if (buffer.Length + read > MaximumResponseBytes)
                throw new InvalidDataException("Facebook zwrócił zbyt dużo danych.");
            buffer.Write(block, 0, read);
        }
        return Encoding.UTF8.GetString(buffer.ToArray());
    }

    internal static PodcastFeedDocument ParseResponse(string text, Uri page, string id)
    {
        if (text.Length == 0 || text[0] == '<')
            throw new InvalidDataException(
                "Facebook zwrócił stronę zamiast listy wpisów. Spróbuj ponownie później.");
        var firstLine = text.Split('\n', 2)[0];
        try
        {
            using var document = JsonDocument.Parse(firstLine);
            var root = document.RootElement;
            if (!TryProperty(root, "data", out var data)
                || !TryProperty(data, "node", out var node)
                || !TryProperty(node, "timeline_list_feed_units", out var feed)
                || !TryProperty(feed, "edges", out var edges)
                || edges.ValueKind != JsonValueKind.Array)
                throw new InvalidDataException("Facebook nie udostępnił listy wpisów tej strony. Spróbuj ponownie później.");

            var title = "Strona Facebooka " + page.AbsolutePath.Trim('/');
            var episodes = new List<PodcastFeedEpisode>();
            foreach (var edge in edges.EnumerateArray())
            {
                if (!TryProperty(edge, "node", out var storyNode)) continue;
                if (TryProperty(storyNode, "actors", out var actors)
                    && actors.ValueKind == JsonValueKind.Array && actors.GetArrayLength() > 0)
                {
                    var actor = ReadText(actors[0], "name");
                    if (!string.IsNullOrWhiteSpace(actor)) title = Clean(actor, 160);
                }
                if (!TryProperty(storyNode, "comet_sections", out var sections)
                    || !TryProperty(sections, "content", out var content)
                    || !TryProperty(content, "story", out var story)
                    || !TryProperty(story, "attachments", out var attachments)
                    || !TryFindVideoId(attachments, out var videoId)) continue;

                var videoUrl = new Uri("https://www.facebook.com/" + page.AbsolutePath.Trim('/')
                    + "/videos/" + videoId + "/");
                DateTimeOffset? published = null;
                if (TryProperty(storyNode, "creation_time", out var timestamp)
                    && timestamp.TryGetInt64(out var seconds))
                    published = DateTimeOffset.FromUnixTimeSeconds(seconds);
                var message = ReadText(story, "message", "text");
                var episodeTitle = !string.IsNullOrWhiteSpace(message) && message.Trim().Length >= 6
                    ? Clean(message, 160)
                    : "Film z Facebooka" + (published is { } date ? " — " + date.ToString("dd.MM.yyyy") : "");
                episodes.Add(new PodcastFeedEpisode(
                    "facebook-video:" + videoId,
                    videoId,
                    episodeTitle,
                    title,
                    Clean(message, 3000),
                    published,
                    TimeSpan.Zero,
                    videoUrl,
                    videoUrl,
                    null,
                    null));
            }
            return new PodcastFeedDocument(
                "facebook-page:" + id,
                title,
                title,
                "Najnowsze publicznie dostępne filmy strony Facebooka. Odświeżanie ręczne; lista może być niepełna.",
                page,
                page,
                episodes);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException("Facebook zwrócił nieprawidłowe dane strony.", exception);
        }
    }

    private static bool TryFindVideoId(JsonElement value, out string id)
    {
        id = string.Empty;
        if (value.ValueKind == JsonValueKind.Object)
        {
            if (ReadText(value, "__typename") == "Video")
            {
                var candidate = ReadText(value, "id");
                if (candidate.Length is >= 8 and <= 20 && candidate.All(char.IsAsciiDigit))
                {
                    id = candidate;
                    return true;
                }
            }
            foreach (var child in value.EnumerateObject())
                if (TryFindVideoId(child.Value, out id)) return true;
        }
        else if (value.ValueKind == JsonValueKind.Array)
        {
            foreach (var child in value.EnumerateArray())
                if (TryFindVideoId(child, out id)) return true;
        }
        return false;
    }

    private static bool TryProperty(JsonElement element, string name, out JsonElement value)
    {
        if (element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out value)) return true;
        value = default;
        return false;
    }

    private static string ReadText(JsonElement element, params string[] path)
    {
        foreach (var name in path)
            if (!TryProperty(element, name, out element)) return string.Empty;
        return element.ValueKind == JsonValueKind.String ? element.GetString() ?? string.Empty : string.Empty;
    }

    private static string Clean(string? value, int maximum)
    {
        var normalized = string.Join(' ', (value ?? string.Empty)
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
        return normalized[..Math.Min(maximum, normalized.Length)];
    }

    public void Dispose() => _http.Dispose();
}
