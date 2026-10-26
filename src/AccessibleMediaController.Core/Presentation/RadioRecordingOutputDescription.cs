using AccessibleMediaController.Core.Configuration;

namespace AccessibleMediaController.Core.Presentation;

/// <summary>
/// Zwięzły, użytkowy opis wyniku nagrywania. Nie zawiera nazwy źródła ani
/// technicznych identyfikatorów, bo nazwa stacji jest już podana przez wiersz.
/// </summary>
public static class RadioRecordingOutputDescription
{
    public static string Format(
        RadioRecordingFormat format,
        int bitrateKbps,
        string? filePathOrName,
        string? outputFolder,
        bool usesDefaultFolder)
    {
        var quality = format switch
        {
            RadioRecordingFormat.Mp3 or RadioRecordingFormat.Aac =>
                $"{Math.Max(1, bitrateKbps)} kb/s",
            RadioRecordingFormat.Flac => "FLAC",
            RadioRecordingFormat.Wav => "WAV",
            RadioRecordingFormat.Original => "oryginalny strumień",
            _ => "format nieznany"
        };
        var fileName = FileName(filePathOrName);
        var file = fileName is null ? "plik przygotowywany" : $"plik {fileName}";
        var folder = usesDefaultFolder || string.IsNullOrWhiteSpace(outputFolder)
            ? "folder domyślny"
            : outputFolder.Trim();
        return $"{quality}, {file}, {folder}";
    }

    public static string ExampleFileName(string baseName, RadioRecordingFormat format) =>
        format switch
        {
            RadioRecordingFormat.Mp3 => $"{baseName}.mp3",
            RadioRecordingFormat.Aac => $"{baseName}.m4a",
            RadioRecordingFormat.Flac => $"{baseName}.flac",
            RadioRecordingFormat.Wav => $"{baseName}.wav",
            _ => baseName
        };

    private static string? FileName(string? filePathOrName)
    {
        if (string.IsNullOrWhiteSpace(filePathOrName)) return null;
        var value = filePathOrName.Trim();
        var fileName = Path.GetFileName(value);
        return string.IsNullOrWhiteSpace(fileName) ? value : fileName;
    }
}
