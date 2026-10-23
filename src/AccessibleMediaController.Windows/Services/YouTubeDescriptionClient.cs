using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Text.Json;

namespace AccessibleMediaController.Windows.Services;

internal sealed record YouTubeDescriptionResult(string Description);

/// <summary>
/// Reads one public, user-facing description from YouTube through the bundled
/// yt-dlp component. No browser cookies or Google account credentials are
/// requested. The stable page address is the only value passed to the tool.
/// </summary>
internal sealed class YouTubeDescriptionClient
{
    private const int MaximumJsonCharacters = 8 * 1024 * 1024;
    private const int MaximumDescriptionCharacters = 50_000;

    internal async Task<YouTubeDescriptionResult> FetchAsync(
        string address,
        bool collection,
        CancellationToken cancellationToken = default)
    {
        if (!YouTubeSourceResolver.IsYouTubeUrl(address))
            throw new InvalidDataException("Adres nie prowadzi do YouTube.");

        var executable = YouTubeSourceResolver.FindExecutable()
            ?? throw new NotSupportedException(
                "Opisy YouTube wymagają składnika yt-dlp. Wybierz Pomoc, Sprawdź składniki: FFmpeg i yt-dlp.");
        var start = ExternalToolProcess.Create(executable);
        var arguments = new List<string>
        {
            "--ignore-config",
            "--no-warnings",
            "--skip-download",
            "--ignore-no-formats-error",
            "--force-ipv4",
            "--socket-timeout", "15",
            "--extractor-retries", "2"
        };
        if (collection)
        {
            // One flat entry is enough to make yt-dlp return the container
            // metadata without resolving every video in a large collection.
            arguments.AddRange(["--flat-playlist", "--playlist-end", "1"]);
        }
        else
        {
            arguments.Add("--no-playlist");
        }
        arguments.AddRange(["--dump-single-json", "--", address.Trim()]);
        foreach (var argument in arguments) start.ArgumentList.Add(argument);

        Process? process = null;
        try
        {
            process = Process.Start(start)
                ?? throw new InvalidDataException("Nie udało się uruchomić składnika yt-dlp.");
            process.StandardInput.Close();
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(45));
            using var termination = timeout.Token.Register(
                static state =>
                {
                    try
                    {
                        var running = (Process)state!;
                        if (!running.HasExited) running.Kill(entireProcessTree: true);
                    }
                    catch (Exception)
                    {
                    }
                },
                process);
            var outputTask = process.StandardOutput.ReadToEndAsync(timeout.Token);
            var errorTask = process.StandardError.ReadToEndAsync(timeout.Token);
            await process.WaitForExitAsync(timeout.Token).ConfigureAwait(false);
            var output = await outputTask.ConfigureAwait(false);
            var error = await errorTask.ConfigureAwait(false);
            if (process.ExitCode != 0)
            {
                DiagnosticLog.Warning(
                    "youtube-description",
                    $"yt-dlp zakończył odczyt opisu kodem {process.ExitCode}: {error.Trim()}");
                throw new InvalidDataException(YouTubeErrorTranslator.Describe(error));
            }
            if (output.Length == 0 || output.Length > MaximumJsonCharacters)
                throw new InvalidDataException("YouTube zwrócił nieprawidłowe dane opisu.");
            return ParseResult(output);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException("YouTube nie odpowiedział w bezpiecznym czasie.");
        }
        catch (Win32Exception exception)
        {
            throw new InvalidDataException(
                "Nie udało się uruchomić składnika yt-dlp.",
                exception);
        }
        finally
        {
            process?.Dispose();
        }
    }

    internal static YouTubeDescriptionResult ParseResult(string json)
    {
        try
        {
            using var document = JsonDocument.Parse(
                json,
                new JsonDocumentOptions { MaxDepth = 64 });
            var root = document.RootElement;
            var description = root.ValueKind == JsonValueKind.Object
                && root.TryGetProperty("description", out var value)
                && value.ValueKind == JsonValueKind.String
                    ? value.GetString() ?? string.Empty
                    : string.Empty;
            return new YouTubeDescriptionResult(CleanDescription(description));
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException(
                "YouTube zwrócił nieprawidłowe dane opisu.",
                exception);
        }
    }

    private static string CleanDescription(string value)
    {
        var normalized = value
            .Replace("\0", " ", StringComparison.Ordinal)
            .Replace("\r\n", "\n", StringComparison.Ordinal)
            .Replace('\r', '\n');
        var lines = normalized.Split('\n')
            .Select(line => string.Join(' ', line.Split(
                (char[]?)null,
                StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)))
            .ToList();
        while (lines.Count > 0 && lines[0].Length == 0) lines.RemoveAt(0);
        while (lines.Count > 0 && lines[^1].Length == 0) lines.RemoveAt(lines.Count - 1);
        var result = string.Join('\n', lines);
        return result.Length <= MaximumDescriptionCharacters
            ? result
            : result[..MaximumDescriptionCharacters].TrimEnd();
    }
}
