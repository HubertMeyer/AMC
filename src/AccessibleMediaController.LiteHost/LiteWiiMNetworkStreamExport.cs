using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using AccessibleMediaController.Core.Devices.WiiM;

namespace AccessibleMediaController.LiteHost;

internal sealed record LiteWiiMNetworkStreamExportResult(
    [property: JsonPropertyName("exportedCount")] int ExportedCount);

internal static class LiteWiiMNetworkStreamExport
{
    public static LiteWiiMNetworkStreamExportResult Write(
        JsonObject root,
        string destinationPath)
    {
        var streams = LiteWiiMProfileMutation.OrderForDisplay(root).Streams;
        if (streams.Count == 0)
            throw new InvalidDataException("Lista strumieni WiiM w AMC jest pusta");

        var destination = Path.GetFullPath(destinationPath);
        var directory = Path.GetDirectoryName(destination)
            ?? throw new IOException("Nie można ustalić folderu docelowego.");
        var temporary = Path.Combine(
            directory,
            $".{Path.GetFileName(destination)}.{Guid.NewGuid():N}.tmp");
        try
        {
            var bytes = WiiMNetworkStreamPlaylistWriter.Write(streams);
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
            return new(streams.Count);
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
