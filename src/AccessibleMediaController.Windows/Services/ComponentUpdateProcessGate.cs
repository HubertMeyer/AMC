using System.IO;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Międzyprocesowa bramka wspólnych składników AMC i AMC Test.
/// Uchwyt pliku jest zwalniany także po awarii procesu, w przeciwieństwie do
/// licznika nazwanego semafora, który mógłby pozostać trwale zmniejszony.
/// </summary>
internal sealed class ComponentUpdateProcessGate : IDisposable
{
    private readonly FileStream _lockStream;

    private ComponentUpdateProcessGate(FileStream lockStream)
    {
        _lockStream = lockStream;
    }

    internal static async Task<ComponentUpdateProcessGate> EnterAsync(
        string componentName,
        CancellationToken cancellationToken)
    {
        var safeName = componentName switch
        {
            "ffmpeg" => "ffmpeg",
            "yt-dlp" => "yt-dlp",
            _ => throw new ArgumentOutOfRangeException(nameof(componentName))
        };
        var root = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "AccessibleMediaController",
            "components",
            ".locks");
        Directory.CreateDirectory(root);
        var path = Path.Combine(root, safeName + ".lock");

        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                var stream = new FileStream(
                    path,
                    FileMode.OpenOrCreate,
                    FileAccess.ReadWrite,
                    FileShare.None,
                    bufferSize: 1,
                    FileOptions.WriteThrough);
                return new ComponentUpdateProcessGate(stream);
            }
            catch (IOException)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(250), cancellationToken)
                    .ConfigureAwait(false);
            }
        }
    }

    public void Dispose() => _lockStream.Dispose();
}
