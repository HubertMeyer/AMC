using System.Globalization;
using System.Text;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Core.Presentation;

/// <summary>
/// Wybiera wystarczająco pewne dopasowanie rozpoznanego utworu w katalogu
/// usługi. Pierwszy wynik wyszukiwania nie jest automatycznie uznawany za
/// właściwy: tytuł i wykonawca muszą do siebie pasować.
/// </summary>
public static class RecognizedTrackMatchSelector
{
    public static MediaItem? SelectBest(
        RadioRecognizedTrackSettings recognized,
        IEnumerable<MediaItem> candidates)
    {
        ArgumentNullException.ThrowIfNull(recognized);
        ArgumentNullException.ThrowIfNull(candidates);

        var ranked = candidates
            .Where(item => item.Kind == MediaItemKind.Track
                && !string.IsNullOrWhiteSpace(item.ExternalId))
            .Select(item => (Item: item, Score: Score(recognized, item)))
            .Where(result => result.Score >= MinimumScore(recognized))
            .OrderByDescending(result => result.Score)
            .ThenByDescending(result => result.Item.IsAvailable)
            .ThenBy(result => result.Item.Title, StringComparer.CurrentCultureIgnoreCase)
            .ToArray();

        return ranked.FirstOrDefault().Item;
    }

    internal static double ScoreForTests(
        RadioRecognizedTrackSettings recognized,
        MediaItem candidate) => Score(recognized, candidate);

    private static double MinimumScore(RadioRecognizedTrackSettings recognized) =>
        string.IsNullOrWhiteSpace(recognized.Artist) ? 55d : 82d;

    private static double Score(
        RadioRecognizedTrackSettings recognized,
        MediaItem candidate)
    {
        var title = Similarity(recognized.Title, candidate.Title);
        var hasRecognizedArtist = !string.IsNullOrWhiteSpace(recognized.Artist);
        var artist = hasRecognizedArtist
            ? Similarity(recognized.Artist, candidate.Artist)
            : 1d;
        if (title < 0.72d) return 0d;
        if (hasRecognizedArtist && artist < 0.50d) return 0d;

        var album = string.IsNullOrWhiteSpace(recognized.Album)
            || string.IsNullOrWhiteSpace(candidate.RelatedAlbumTitle)
                ? 0d
                : Similarity(recognized.Album, candidate.RelatedAlbumTitle);
        return title * 60d + (hasRecognizedArtist ? artist * 35d : 0d) + album * 5d;
    }

    private static double Similarity(string? left, string? right)
    {
        var first = Fold(left);
        var second = Fold(right);
        if (first.Length == 0 || second.Length == 0) return 0d;
        if (string.Equals(first, second, StringComparison.Ordinal)) return 1d;

        if (first.Length >= 5 && second.Length >= 5
            && (first.Contains(second, StringComparison.Ordinal)
                || second.Contains(first, StringComparison.Ordinal)))
        {
            return 0.90d;
        }

        var firstTokens = first.Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .ToHashSet(StringComparer.Ordinal);
        var secondTokens = second.Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .ToHashSet(StringComparer.Ordinal);
        if (firstTokens.Count == 0 || secondTokens.Count == 0) return 0d;
        var common = firstTokens.Count(secondTokens.Contains);
        return (2d * common) / (firstTokens.Count + secondTokens.Count);
    }

    private static string Fold(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return string.Empty;
        var builder = new StringBuilder(value.Length);
        var pendingSpace = false;
        foreach (var character in value.Trim().Normalize(NormalizationForm.FormD))
        {
            if (CharUnicodeInfo.GetUnicodeCategory(character) == UnicodeCategory.NonSpacingMark)
                continue;
            var folded = character switch
            {
                'ł' or 'Ł' => 'l',
                _ => char.ToLowerInvariant(character)
            };
            if (char.IsLetterOrDigit(folded))
            {
                if (pendingSpace && builder.Length > 0) builder.Append(' ');
                builder.Append(folded);
                pendingSpace = false;
            }
            else pendingSpace = true;
        }
        return builder.ToString();
    }
}

public static class RecognizedTrackNavigationPolicy
{
    public static string? PreferredItemId(
        IEnumerable<MediaItem> items,
        string? preferredExternalId) => string.IsNullOrWhiteSpace(preferredExternalId)
        ? null
        : items.FirstOrDefault(item => string.Equals(
            item.ExternalId,
            preferredExternalId,
            StringComparison.Ordinal))?.Id;
}
