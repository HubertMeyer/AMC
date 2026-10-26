using System.Globalization;

namespace AccessibleMediaController.Core.Sessions;

public static class MediaCatalogSearch
{
    public static IReadOnlyList<MediaSearchResult> Search(
        IEnumerable<DemoMediaSession> sessions,
        string query)
    {
        var words = query.Trim().Split(
            ' ',
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        if (words.Length == 0) return [];

        var compareInfo = CultureInfo.CurrentCulture.CompareInfo;
        var results = new List<MediaSearchResult>();
        foreach (var session in sessions)
        {
            foreach (var item in session.Items)
            {
                if (Matches(compareInfo, words, session.DisplayName, item))
                {
                    results.Add(new MediaSearchResult(session, item));
                }
            }
        }
        return results;
    }

    public static bool Matches(string sessionDisplayName, MediaItem item, string query)
    {
        var words = query.Trim().Split(
            ' ',
            StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        return words.Length > 0
            && Matches(CultureInfo.CurrentCulture.CompareInfo, words, sessionDisplayName, item);
    }

    private static bool Matches(
        CompareInfo compareInfo,
        IReadOnlyList<string> words,
        string sessionDisplayName,
        MediaItem item)
    {
        var searchableText = $"{item.Title} {item.Artist} {item.KindLabel} {sessionDisplayName} "
            + $"{item.Country} {item.Language} {item.Tags} {item.Codec}";
        return words.All(word => compareInfo.IndexOf(
            searchableText,
            word,
            CompareOptions.IgnoreCase | CompareOptions.IgnoreNonSpace) >= 0);
    }
}

public sealed record MediaSearchResult(DemoMediaSession Session, MediaItem Item);
