using System.Globalization;
using System.Text;
using AccessibleMediaController.Core.Sessions;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Searches a small, reviewed directory of public SoundCloud profiles whose
/// RSS feeds contain ordinary podcast audio files. This intentionally avoids
/// scraping SoundCloud's private web client identifier or shipping an
/// application secret in AMC. New entries must be verified with the live RSS
/// smoke test before they are added here.
/// </summary>
internal sealed class SoundCloudPodcastDirectoryClient
{
    private static readonly DirectoryEntry[] Entries =
    [
        new(
            "152970424",
            "Freta10",
            "Dominikanie Warszawa-Freta",
            "https://feeds.soundcloud.com/users/soundcloud:users:152970424/sounds.rss",
            "https://soundcloud.com/freta10",
            "soundcloud freta10 dominikanie warszawa freta klasztor kazania rekolekcje"),
        new(
            "146144347",
            "Dominikanie Służew",
            "Warszawa",
            "https://feeds.soundcloud.com/users/soundcloud:users:146144347/sounds.rss",
            "https://soundcloud.com/dominikanie_sluzew",
            "soundcloud dominikanie sluzew służew warszawa kazania rekolekcje wyklady wykłady"),
        new(
            "88645852",
            "Dominikanie – Rzeszów",
            "Rzeszów",
            "https://feeds.soundcloud.com/users/soundcloud:users:88645852/sounds.rss",
            "https://soundcloud.com/dominikanie-rzeszow",
            "soundcloud dominikanie rzeszow rzeszów kazania rekolekcje")
    ];

    internal Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var terms = Normalize(query)
            .Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (terms.Length == 0)
            return Task.FromResult<IReadOnlyList<MediaItem>>([]);

        var results = Entries
            .Where(entry => terms.All(term => entry.NormalizedSearchText.Contains(
                term,
                StringComparison.Ordinal)))
            .Select(entry => entry.ToMediaItem())
            .ToArray();
        return Task.FromResult<IReadOnlyList<MediaItem>>(results);
    }

    private static string Normalize(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return string.Empty;
        var decomposed = value.Trim().Normalize(NormalizationForm.FormD);
        var normalized = new StringBuilder(decomposed.Length);
        var pendingSpace = false;
        foreach (var character in decomposed)
        {
            if (CharUnicodeInfo.GetUnicodeCategory(character)
                == UnicodeCategory.NonSpacingMark)
            {
                continue;
            }
            if (char.IsLetterOrDigit(character))
            {
                if (pendingSpace && normalized.Length > 0) normalized.Append(' ');
                var lower = char.ToLowerInvariant(character);
                normalized.Append(lower == 'ł' ? 'l' : lower);
                pendingSpace = false;
            }
            else
            {
                pendingSpace = true;
            }
        }
        return normalized.ToString();
    }

    private sealed record DirectoryEntry(
        string PublicId,
        string Title,
        string Artist,
        string FeedAddress,
        string ProfileAddress,
        string SearchText)
    {
        internal string NormalizedSearchText { get; } = Normalize(SearchText);

        internal MediaItem ToMediaItem() => new()
        {
            Id = $"podcast-directory:soundcloud:{PublicId}",
            Title = Title,
            Artist = Artist,
            Kind = MediaItemKind.Podcast,
            Source = FeedAddress,
            PublicUri = ProfileAddress,
            Tags = "SoundCloud, podcast",
            ExternalId = $"soundcloud:{PublicId}",
            IsAvailable = true,
            IsInLibrary = false
        };
    }
}
