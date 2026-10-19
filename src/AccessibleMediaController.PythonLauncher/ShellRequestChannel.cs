using System.IO.Pipes;
using System.Text;
using AccessibleMediaController.Core.ShellIntegration;
using AccessibleMediaController.ReleaseProfiles;

namespace AccessibleMediaController.PythonLauncher;

internal sealed class ShellRequestChannel : IDisposable
{
    private const int MaximumLineLength = 64 * 1024;
    private readonly CancellationTokenSource _cancellation = new();
    private readonly Task _server;

    private ShellRequestChannel(string pipeName, Action<string> forward)
    {
        _server = Task.Run(() => ServeAsync(pipeName, forward, _cancellation.Token));
    }

    internal static string PipeName(ReleaseProfileDescriptor profile) =>
        "AccessibleMultimediaController.Shell." + profile.ProfileId;

    internal static ShellRequestChannel Start(
        ReleaseProfileDescriptor profile,
        Action<string> forward) =>
        new(PipeName(profile), forward);

    internal static bool TrySend(
        ReleaseProfileDescriptor profile,
        ShellLaunchRequest request,
        int timeoutMilliseconds = 5_000)
    {
        if (!request.HasFiles)
            return false;
        try
        {
            using var client = new NamedPipeClientStream(
                ".",
                PipeName(profile),
                PipeDirection.InOut,
                PipeOptions.Asynchronous);
            client.Connect(Math.Max(1, timeoutMilliseconds));
            using var writer = new StreamWriter(
                client,
                new UTF8Encoding(false),
                leaveOpen: true)
            {
                AutoFlush = true,
            };
            using var reader = new StreamReader(
                client,
                Encoding.UTF8,
                detectEncodingFromByteOrderMarks: false,
                leaveOpen: true);
            writer.WriteLine(ShellIntegrationRules.EncodeHandoff(request));
            return string.Equals(reader.ReadLine(), "ok", StringComparison.Ordinal);
        }
        catch (Exception exception) when (
            exception is IOException
                or TimeoutException
                or UnauthorizedAccessException
                or InvalidOperationException)
        {
            return false;
        }
    }

    private static async Task ServeAsync(
        string pipeName,
        Action<string> forward,
        CancellationToken cancellation)
    {
        while (!cancellation.IsCancellationRequested)
        {
            try
            {
                using var server = new NamedPipeServerStream(
                    pipeName,
                    PipeDirection.InOut,
                    1,
                    PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
                await server.WaitForConnectionAsync(cancellation).ConfigureAwait(false);
                using var reader = new StreamReader(
                    server,
                    Encoding.UTF8,
                    detectEncodingFromByteOrderMarks: false,
                    leaveOpen: true);
                using var writer = new StreamWriter(
                    server,
                    new UTF8Encoding(false),
                    leaveOpen: true)
                {
                    AutoFlush = true,
                };
                var line = await reader.ReadLineAsync(cancellation).ConfigureAwait(false);
                if (string.IsNullOrWhiteSpace(line) || line.Length > MaximumLineLength)
                {
                    await writer.WriteLineAsync("error").ConfigureAwait(false);
                    continue;
                }
                _ = ShellIntegrationRules.DecodeHandoff(line);
                forward(line);
                await writer.WriteLineAsync("ok").ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception) when (
                exception is IOException
                    or InvalidDataException
                    or UnauthorizedAccessException
                    or ObjectDisposedException)
            {
                // Pojedynczy uszkodzony klient nie zamyka kanału profilu.
            }
        }
    }

    public void Dispose()
    {
        _cancellation.Cancel();
        try
        {
            _server.Wait(1_000);
        }
        catch (AggregateException exception) when (
            exception.InnerExceptions.All(inner => inner is OperationCanceledException))
        {
        }
        finally
        {
            _cancellation.Dispose();
        }
    }
}
