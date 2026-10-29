using System.ComponentModel;
using System.Diagnostics;
using System.IO;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Resolves one public Facebook or Instagram video. Profile URLs are deliberately
/// excluded: neither provider supplies an anonymous, reliable video feed here.
/// </summary>
internal static class PublicSocialVideoResolver
{
    internal static bool TryGetProvider(string? address, out string provider)
    {
        provider = string.Empty;
        if (!Uri.TryCreate(address?.Trim(), UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https")
            || !string.IsNullOrEmpty(uri.UserInfo)) return false;

        var host = uri.IdnHost.TrimEnd('.');
        var path = uri.AbsolutePath.Trim('/');
        if (host.Equals("facebook.com", StringComparison.OrdinalIgnoreCase)
            || host.EndsWith(".facebook.com", StringComparison.OrdinalIgnoreCase)
            || host.Equals("fb.watch", StringComparison.OrdinalIgnoreCase))
        {
            if (host.Equals("fb.watch", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/videos/", StringComparison.OrdinalIgnoreCase)
                || path.StartsWith("reel/", StringComparison.OrdinalIgnoreCase)
                || path.StartsWith("watch", StringComparison.OrdinalIgnoreCase)
                    && uri.Query.Contains("v=", StringComparison.OrdinalIgnoreCase)
                || path.Equals("video.php", StringComparison.OrdinalIgnoreCase)
                    && uri.Query.Contains("v=", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/posts/", StringComparison.OrdinalIgnoreCase))
            {
                provider = "Facebook";
                return true;
            }
            return false;
        }

        if (host.Equals("instagram.com", StringComparison.OrdinalIgnoreCase)
            || host.EndsWith(".instagram.com", StringComparison.OrdinalIgnoreCase))
        {
            var parts = path.Split('/', StringSplitOptions.RemoveEmptyEntries);
            var kindIndex = parts.Length >= 3 ? 1 : 0;
            var kind = parts.Length >= kindIndex + 2
                && (parts[kindIndex].Equals("p", StringComparison.OrdinalIgnoreCase)
                    || parts[kindIndex].Equals("reel", StringComparison.OrdinalIgnoreCase)
                    || parts[kindIndex].Equals("reels", StringComparison.OrdinalIgnoreCase)
                    || parts[kindIndex].Equals("tv", StringComparison.OrdinalIgnoreCase));
            if (kind)
            {
                provider = "Instagram";
                return true;
            }
        }
        return false;
    }

    internal static bool IsVideoUrl(string? address) => TryGetProvider(address, out _);

    internal static async Task<ResolvedYouTubeAudioSource> ResolveAudioAsync(
        string pageUrl,
        CancellationToken cancellationToken)
    {
        if (!TryGetProvider(pageUrl, out var provider))
            throw new InvalidDataException("Wpisz adres pojedynczego filmu lub rolki z Facebooka albo Instagrama.");
        var executable = YouTubeSourceResolver.FindExecutable()
            ?? throw new NotSupportedException(
                "Odtwarzanie publicznych filmów wymaga składnika yt-dlp. Wybierz Pomoc, Sprawdź składniki: FFmpeg i yt-dlp.");
        var start = ExternalToolProcess.Create(executable);
        foreach (var argument in new[]
        {
            "--ignore-config", "--no-playlist", "--no-warnings",
            "--force-ipv4", "--socket-timeout", "20", "--retries", "2",
            "--fragment-retries", "2", "--extractor-retries", "2",
            "--format", "bestaudio/best[acodec!=none]/best",
            "--dump-single-json", "--", pageUrl.Trim()
        }) start.ArgumentList.Add(argument);

        Process? process = null;
        try
        {
            process = Process.Start(start)
                ?? throw new InvalidDataException("Nie udało się uruchomić składnika yt-dlp.");
            process.StandardInput.Close();
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(75));
            using var termination = timeout.Token.Register(static state =>
            {
                try
                {
                    var running = (Process)state!;
                    if (!running.HasExited) running.Kill(entireProcessTree: true);
                }
                catch (Exception) { }
            }, process);
            var outputTask = process.StandardOutput.ReadToEndAsync(timeout.Token);
            var errorTask = process.StandardError.ReadToEndAsync(timeout.Token);
            await process.WaitForExitAsync(timeout.Token).ConfigureAwait(false);
            var output = await outputTask.ConfigureAwait(false);
            var error = await errorTask.ConfigureAwait(false);
            if (process.ExitCode != 0)
            {
                DiagnosticLog.Warning("social-video",
                    $"yt-dlp zakończył się kodem {process.ExitCode} dla {provider}: {error.Trim()}");
                var reason = error.Contains("Cannot parse data", StringComparison.OrdinalIgnoreCase)
                    || error.Contains("Unable to extract", StringComparison.OrdinalIgnoreCase)
                        ? "Nie udało się odczytać danych filmu. Sprawdź aktualizację składnika yt-dlp."
                        : error.Contains("login", StringComparison.OrdinalIgnoreCase)
                            || error.Contains("private", StringComparison.OrdinalIgnoreCase)
                                ? "Ten film może wymagać logowania albo nie być publicznie dostępny."
                                : "Nie udało się odczytać filmu. Sprawdź adres i spróbuj ponownie później.";
                throw new InvalidDataException($"{provider}: {reason}");
            }
            if (output.Length == 0 || output.Length > 8 * 1024 * 1024)
                throw new InvalidDataException($"{provider} zwrócił nieprawidłowe dane filmu.");
            return YouTubeSourceResolver.ParseResult(
                pageUrl.Trim(), output, requireLive: false, sourceLabel: provider);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            throw new TimeoutException($"{provider} nie odpowiedział w bezpiecznym czasie.");
        }
        catch (Win32Exception exception)
        {
            throw new InvalidDataException("Nie udało się uruchomić składnika yt-dlp.", exception);
        }
        finally
        {
            process?.Dispose();
        }
    }
}
