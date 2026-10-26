using System.IO;
using System.Net;
using System.Net.Http;

namespace AccessibleMediaController.Windows.Services;

internal sealed record RadioPlaylistNameEnrichmentResult(
    RadioPlaylistImportResult Playlist,
    int NamesReadFromServers,
    int NamesWithoutDescription,
    int NamesNotProbed);

/// <summary>
/// Completes unnamed playlist rows from the user-facing station name exposed by
/// an Icecast/Shoutcast server. The operation is bounded so a large or stale
/// playlist cannot freeze the import surface or open thousands of connections.
/// </summary>
internal static class RadioPlaylistNameEnricher
{
    internal const int MaximumAutomaticNameProbes = 64;
    private const int MaximumConcurrentNameProbes = 6;

    internal static Task<RadioPlaylistNameEnrichmentResult> EnrichAsync(
        RadioPlaylistImportResult playlist,
        TimeSpan totalTimeout) =>
        EnrichAsync(
            playlist,
            totalTimeout,
            RadioStationNameProbe.TryReadAsync,
            MaximumAutomaticNameProbes,
            MaximumConcurrentNameProbes);

    internal static async Task<RadioPlaylistNameEnrichmentResult> EnrichAsync(
        RadioPlaylistImportResult playlist,
        TimeSpan totalTimeout,
        Func<string, CancellationToken, Task<string?>> probe,
        int maximumProbes,
        int maximumConcurrency)
    {
        ArgumentNullException.ThrowIfNull(playlist);
        ArgumentNullException.ThrowIfNull(probe);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(maximumProbes);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(maximumConcurrency);
        if (totalTimeout <= TimeSpan.Zero) throw new ArgumentOutOfRangeException(nameof(totalTimeout));

        var stations = playlist.Stations.ToArray();
        var missingNameIndexes = stations
            .Select((station, index) => (station, index))
            .Where(entry => !entry.station.HasDescriptiveName)
            .Select(entry => entry.index)
            .ToArray();
        if (missingNameIndexes.Length == 0)
        {
            return new RadioPlaylistNameEnrichmentResult(playlist, 0, 0, 0);
        }

        var indexesToProbe = missingNameIndexes.Take(maximumProbes).ToArray();
        var namesRead = 0;
        using var timeout = new CancellationTokenSource(totalTimeout);
        using var concurrency = new SemaphoreSlim(maximumConcurrency, maximumConcurrency);
        var tasks = indexesToProbe.Select(async index =>
        {
            var entered = false;
            try
            {
                await concurrency.WaitAsync(timeout.Token).ConfigureAwait(false);
                entered = true;
                var candidate = await probe(stations[index].StreamUrl, timeout.Token)
                    .ConfigureAwait(false);
                var normalized = RadioPlaylistImporter.NormalizeSuppliedName(candidate);
                if (normalized is null) return;
                stations[index] = stations[index] with
                {
                    Name = normalized,
                    HasDescriptiveName = true
                };
                Interlocked.Increment(ref namesRead);
            }
            catch (Exception exception) when (IsExpectedProbeFailure(exception))
            {
                // An unavailable server must not turn a valid local import into
                // an error. The intentional host-based fallback remains visible.
            }
            finally
            {
                if (entered) concurrency.Release();
            }
        }).ToArray();
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return new RadioPlaylistNameEnrichmentResult(
            new RadioPlaylistImportResult(stations, playlist.SkippedEntries),
            namesRead,
            missingNameIndexes.Length - namesRead,
            Math.Max(0, missingNameIndexes.Length - indexesToProbe.Length));
    }

    private static bool IsExpectedProbeFailure(Exception exception) => exception is
        HttpRequestException or IOException or InvalidDataException or
        ArgumentException or OperationCanceledException or TimeoutException;
}

/// <summary>
/// Reads response headers only. It does not wait for audio or ICY track-title
/// blocks, because those describe the current programme rather than the station.
/// </summary>
internal static class RadioStationNameProbe
{
    private static readonly TimeSpan PerStationTimeout = TimeSpan.FromSeconds(4);
    private static readonly HttpClient Client = CreateClient();
    private static readonly string[] StationNameHeaders =
        ["icy-name", "ice-name", "x-audiocast-name"];

    internal static async Task<string?> TryReadAsync(
        string source,
        CancellationToken cancellationToken)
    {
        if (!Uri.TryCreate(source, UriKind.Absolute, out var uri)
            || uri.Scheme is not ("http" or "https"))
        {
            return null;
        }

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(PerStationTimeout);
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, uri);
            request.Headers.TryAddWithoutValidation("Icy-MetaData", "0");
            request.Headers.TryAddWithoutValidation("Range", "bytes=0-0");
            using var response = await Client.SendAsync(
                    request,
                    HttpCompletionOption.ResponseHeadersRead,
                    timeout.Token)
                .ConfigureAwait(false);
            if (!response.IsSuccessStatusCode) return null;
            return ReadNameFromHeaders(response);
        }
        catch (Exception exception) when (exception is HttpRequestException
            or IOException
            or OperationCanceledException
            or InvalidDataException)
        {
            return null;
        }
    }

    internal static string? ReadNameFromHeaders(HttpResponseMessage response)
    {
        ArgumentNullException.ThrowIfNull(response);
        foreach (var headerName in StationNameHeaders)
        {
            if (!response.Headers.TryGetValues(headerName, out var values)
                && !response.Content.Headers.TryGetValues(headerName, out values))
            {
                continue;
            }
            foreach (var value in values)
            {
                var normalized = RadioPlaylistImporter.NormalizeSuppliedName(value);
                if (normalized is not null) return normalized;
            }
        }
        return null;
    }

    private static HttpClient CreateClient()
    {
        var handler = new SocketsHttpHandler
        {
            AllowAutoRedirect = true,
            MaxAutomaticRedirections = 5,
            AutomaticDecompression = DecompressionMethods.All,
            ConnectTimeout = PerStationTimeout,
            PooledConnectionLifetime = TimeSpan.FromMinutes(5)
        };
        var client = new HttpClient(handler) { Timeout = Timeout.InfiniteTimeSpan };
        client.DefaultRequestHeaders.UserAgent.ParseAdd("AccessibleMultimediaController/0.1");
        return client;
    }
}
