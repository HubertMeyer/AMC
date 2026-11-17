using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text.Json;
using AccessibleMediaController.Core.YouTube;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Ograniczony odczyt publicznej karty /streams kanału. Nie używa API Google,
/// konta, cookies ani parametrów językowych wymuszających zmianę tytułów.
/// </summary>
internal sealed class YouTubePublicBroadcastClient
{
    private const int MaximumItems = 50;
    private const int MaximumJsonCharacters = 4 * 1024 * 1024;

    internal async Task<IReadOnlyList<YouTubeBroadcast>> FetchAsync(
        Uri streamsAddress, CancellationToken cancellationToken = default)
    {
        var executable = YouTubeSourceResolver.FindExecutable()
            ?? throw new NotSupportedException(
                "Publiczne transmisje YouTube wymagają składnika yt-dlp. Wybierz Pomoc, Sprawdź składniki: FFmpeg i yt-dlp.");
        try
        {
            var result = await RunYtDlpAsync(executable, streamsAddress, cancellationToken)
                .ConfigureAwait(false);
            if (result.ExitCode != 0)
                throw new InvalidDataException("YouTube nie udostępnił obecnie transmisji tego kanału.");
            if (result.Output.Length == 0 || result.Output.Length > MaximumJsonCharacters)
                throw new InvalidDataException("YouTube zwrócił nieczytelną listę transmisji.");
            return ParseResult(result.Output);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException("YouTube nie odpowiedział w bezpiecznym czasie.");
        }
        catch (Win32Exception exception)
        {
            throw new InvalidDataException("Nie udało się uruchomić składnika yt-dlp.", exception);
        }
    }

    private static async Task<(int ExitCode, string Output)> RunYtDlpAsync(
        string executable, Uri address, CancellationToken cancellationToken)
    {
        var start = ExternalToolProcess.Create(executable);
        foreach (var argument in new[]
        {
            "--ignore-config", "--flat-playlist", "--no-warnings", "--force-ipv4",
            "--socket-timeout", "15", "--extractor-retries", "2",
            "--playlist-end", MaximumItems.ToString(CultureInfo.InvariantCulture),
            "--dump-single-json", "--", address.AbsoluteUri
        }) start.ArgumentList.Add(argument);
        using var process = Process.Start(start)
            ?? throw new InvalidDataException("Nie udało się uruchomić składnika yt-dlp.");
        process.StandardInput.Close();
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(60));
        using var termination = timeout.Token.Register(static state =>
        {
            try { if (!((Process)state!).HasExited) ((Process)state!).Kill(entireProcessTree: true); }
            catch (Exception) { }
        }, process);
        var output = process.StandardOutput.ReadToEndAsync(timeout.Token);
        var error = process.StandardError.ReadToEndAsync(timeout.Token);
        await process.WaitForExitAsync(timeout.Token).ConfigureAwait(false);
        _ = await error.ConfigureAwait(false);
        return (process.ExitCode, await output.ConfigureAwait(false));
    }

    internal static IReadOnlyList<YouTubeBroadcast> ParseResult(string json)
    {
        try
        {
            using var document = JsonDocument.Parse(json, new JsonDocumentOptions { MaxDepth = 64 });
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object || !root.TryGetProperty("entries", out var entries)
                || entries.ValueKind != JsonValueKind.Array)
                throw new InvalidDataException("YouTube zwrócił nieczytelną listę transmisji.");
            var defaultChannel = Clean(Read(root, "channel"), "Kanał YouTube", 300);
            var rows = new List<YouTubeBroadcast>();
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var entry in entries.EnumerateArray())
            {
                if (entry.ValueKind != JsonValueKind.Object || rows.Count >= MaximumItems) continue;
                var state = Read(entry, "live_status").ToLowerInvariant() switch
                {
                    "is_live" => YouTubeBroadcastState.Live,
                    "is_upcoming" => YouTubeBroadcastState.Upcoming,
                    _ => (YouTubeBroadcastState?)null
                };
                if (state is null) continue;
                var id = Read(entry, "id");
                if (id.Length is < 1 or > 128 || !id.All(c => char.IsAsciiLetterOrDigit(c) || c is '-' or '_')
                    || !seen.Add(id)) continue;
                var scheduled = state == YouTubeBroadcastState.Upcoming
                    ? ReadTimestamp(entry, "release_timestamp") : null;
                var actual = state == YouTubeBroadcastState.Live
                    ? ReadTimestamp(entry, "timestamp") : null;
                rows.Add(new YouTubeBroadcast(
                    id,
                    Clean(Read(entry, "title"), "Transmisja YouTube", 500),
                    Clean(First(Read(entry, "channel"), Read(entry, "uploader"), defaultChannel), "Kanał YouTube", 300),
                    new Uri($"https://www.youtube.com/watch?v={id}", UriKind.Absolute),
                    state.Value, scheduled, actual));
            }
            return rows;
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException("YouTube zwrócił nieczytelną listę transmisji.", exception);
        }
    }

    private static string Read(JsonElement item, string name) => item.TryGetProperty(name, out var value)
        && value.ValueKind == JsonValueKind.String ? value.GetString()?.Trim() ?? string.Empty : string.Empty;
    private static string First(params string[] values) => values.FirstOrDefault(value => value.Length > 0) ?? string.Empty;
    private static string Clean(string value, string fallback, int max) => string.Join(' ', value.Split(
        (char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)) is { Length: > 0 } text
        ? text.Length <= max ? text : text[..max].Trim() : fallback;
    private static DateTimeOffset? ReadTimestamp(JsonElement item, string name) => item.TryGetProperty(name, out var value)
        && value.ValueKind == JsonValueKind.Number
        && value.TryGetInt64(out var seconds) && seconds is > 0 and < 4_102_444_800
        ? DateTimeOffset.FromUnixTimeSeconds(seconds) : null;
}
