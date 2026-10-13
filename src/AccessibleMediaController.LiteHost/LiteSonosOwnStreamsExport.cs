using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Radio;
using AccessibleMediaController.Core.Sonos;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteSonosOwnStreamsExportResult(
    [property: JsonPropertyName("exportedCount")] int ExportedCount);

internal static class LiteSonosOwnStreamsExport
{
    public static LiteSonosOwnStreamsExportResult Write(
        JsonObject root,
        string destinationPath)
    {
        var streams = LiteSonosOwnStreamsMutation.OrderForDisplay(root).Streams
            .Where(stream => SonosStreamUrlPolicy.IsAcceptable(stream.StreamUrl))
            .DistinctBy(stream => stream.StreamUrl.Trim(), StringComparer.OrdinalIgnoreCase)
            .ToArray();
        if (streams.Length == 0)
            throw new InvalidDataException("Lista własnych stacji Sonosa w AMC jest pusta");

        var destination = Path.GetFullPath(destinationPath);
        var directory = Path.GetDirectoryName(destination)
            ?? throw new IOException("Nie można ustalić folderu docelowego.");
        var temporary = Path.Combine(
            directory,
            $".{Path.GetFileName(destination)}.{Guid.NewGuid():N}.tmp");
        try
        {
            var bytes = RadioFavoritesPlaylistWriter.Write(streams.Select(stream =>
                new RadioFavoritePlaylistEntry(stream.Name, stream.StreamUrl)));
            using (var output = new FileStream(
                       temporary,
                       FileMode.CreateNew,
                       FileAccess.Write,
                       FileShare.None,
                       bufferSize: 16_384,
                       FileOptions.WriteThrough))
            {
                output.Write(bytes);
                output.Flush(flushToDisk: true);
            }
            File.Move(temporary, destination, overwrite: true);
            temporary = string.Empty;
            return new(streams.Length);
        }
        finally
        {
            if (temporary.Length > 0)
            {
                try { File.Delete(temporary); }
                catch (Exception exception) when (exception is IOException
                    or UnauthorizedAccessException) { }
            }
        }
    }
}
