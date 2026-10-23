using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;

namespace AccessibleMediaController.Core.YouTube;

/// <summary>
/// Jednorazowy odbiornik odpowiedzi OAuth na losowym porcie 127.0.0.1.
/// Nie zna tokenów i nie otwiera przeglądarki. Kod autoryzacyjny pozostaje w
/// pamięci procesu hosta C# i nie jest umieszczany w stronie odpowiedzi.
/// </summary>
public sealed class YouTubeOAuthLoopbackReceiver : IDisposable
{
    private const string CallbackPath = "/youtube/callback/";
    private const int MaxRequestLineCharacters = 4096;
    private const int MaxHeaderCharacters = 16_384;
    private readonly TcpListener _listener;
    private bool _used;

    private YouTubeOAuthLoopbackReceiver(TcpListener listener, Uri redirectUri)
    {
        _listener = listener;
        RedirectUri = redirectUri;
    }

    public Uri RedirectUri { get; }

    public static YouTubeOAuthLoopbackReceiver Start()
    {
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start(1);
        var endpoint = (IPEndPoint)listener.LocalEndpoint;
        return new YouTubeOAuthLoopbackReceiver(
            listener,
            new Uri($"http://127.0.0.1:{endpoint.Port}{CallbackPath}"));
    }

    public async Task<YouTubeAuthorizationCallback> ReceiveAsync(
        string expectedState,
        CancellationToken cancellationToken)
    {
        if (_used) throw new InvalidOperationException("Odbiornik logowania YouTube został już użyty.");
        _used = true;
        if (string.IsNullOrWhiteSpace(expectedState) || expectedState.Length > 256)
            throw new ArgumentException("Nieprawidłowe zabezpieczenie sesji logowania YouTube.");

        using var client = await _listener.AcceptTcpClientAsync(cancellationToken).ConfigureAwait(false);
        _listener.Stop();
        if (client.Client.RemoteEndPoint is not IPEndPoint remote || !IPAddress.IsLoopback(remote.Address))
            return YouTubeAuthorizationCallback.Failure("Nieprawidłowe źródło odpowiedzi logowania YouTube.");

        await using var stream = client.GetStream();
        using var reader = new StreamReader(
            stream, Encoding.ASCII, detectEncodingFromByteOrderMarks: false, 4096, leaveOpen: true);
        var requestLine = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false)
            ?? string.Empty;
        var headerCharacters = 0;
        while (true)
        {
            var header = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
            if (string.IsNullOrEmpty(header)) break;
            headerCharacters += header.Length;
            if (headerCharacters > MaxHeaderCharacters)
            {
                await SendResponseAsync(stream, success: false, cancellationToken).ConfigureAwait(false);
                return YouTubeAuthorizationCallback.Failure("Odpowiedź logowania YouTube była zbyt duża.");
            }
        }

        var callback = ParseRequestLine(requestLine, expectedState);
        await SendResponseAsync(stream, callback.Succeeded, cancellationToken).ConfigureAwait(false);
        return callback;
    }

    private YouTubeAuthorizationCallback ParseRequestLine(string requestLine, string expectedState)
    {
        if (requestLine.Length is 0 or > MaxRequestLineCharacters)
            return YouTubeAuthorizationCallback.Failure("Nieprawidłowa odpowiedź logowania YouTube.");
        var parts = requestLine.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length < 3 || !string.Equals(parts[0], "GET", StringComparison.Ordinal))
            return YouTubeAuthorizationCallback.Failure("Nieprawidłowa odpowiedź logowania YouTube.");
        if (!Uri.TryCreate(RedirectUri.GetLeftPart(UriPartial.Authority) + parts[1], UriKind.Absolute, out var uri)
            || !string.Equals(uri.AbsolutePath, CallbackPath, StringComparison.Ordinal))
            return YouTubeAuthorizationCallback.Failure("Nieprawidłowy adres powrotu logowania YouTube.");

        var query = ParseQuery(uri.Query);
        if (query is null
            || !query.TryGetValue("state", out var actualState)
            || !FixedTimeEquals(actualState, expectedState))
            return YouTubeAuthorizationCallback.Failure("Nieprawidłowe zabezpieczenie sesji logowania YouTube.");
        if (query.TryGetValue("error", out var error))
            return YouTubeAuthorizationCallback.Failure(
                YouTubeOAuthProtocol.DescribeAuthorizationError(error));
        if (!query.TryGetValue("code", out var code) || string.IsNullOrWhiteSpace(code) || code.Length > 4096)
            return YouTubeAuthorizationCallback.Failure("Google nie przekazał kodu logowania YouTube.");
        return YouTubeAuthorizationCallback.Success(code);
    }

    private static Dictionary<string, string>? ParseQuery(string query)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        try
        {
            foreach (var part in query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries))
            {
                var pair = part.Split('=', 2);
                var key = Uri.UnescapeDataString(pair[0].Replace('+', ' '));
                var value = pair.Length == 2
                    ? Uri.UnescapeDataString(pair[1].Replace('+', ' '))
                    : string.Empty;
                if (key.Length > 128 || value.Length > 4096 || !result.TryAdd(key, value)) return null;
            }
            return result;
        }
        catch (UriFormatException)
        {
            return null;
        }
    }

    private static bool FixedTimeEquals(string actual, string expected)
    {
        var actualBytes = Encoding.UTF8.GetBytes(actual);
        var expectedBytes = Encoding.UTF8.GetBytes(expected);
        try
        {
            return actualBytes.Length == expectedBytes.Length
                && CryptographicOperations.FixedTimeEquals(actualBytes, expectedBytes);
        }
        finally
        {
            CryptographicOperations.ZeroMemory(actualBytes);
            CryptographicOperations.ZeroMemory(expectedBytes);
        }
    }

    private static async Task SendResponseAsync(
        NetworkStream stream,
        bool success,
        CancellationToken cancellationToken)
    {
        var message = success
            ? "Google przekazał zgodę do AMC. AMC jeszcze kończy logowanie. "
                + "Możesz zamknąć tę kartę i sprawdzić wynik w aplikacji."
            : "Logowanie nie zostało ukończone. Wróć do AMC i spróbuj ponownie.";
        var body = "<!doctype html><html lang=\"pl\"><meta charset=\"utf-8\">"
            + "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            + "<title>AMC — YouTube</title><body><h1>" + message + "</h1></body></html>";
        var bytes = Encoding.UTF8.GetBytes(body);
        var headers = Encoding.ASCII.GetBytes(
            "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
            + "Cache-Control: no-store\r\nPragma: no-cache\r\nX-Content-Type-Options: nosniff\r\n"
            + $"Content-Length: {bytes.Length}\r\nConnection: close\r\n\r\n");
        await stream.WriteAsync(headers, cancellationToken).ConfigureAwait(false);
        await stream.WriteAsync(bytes, cancellationToken).ConfigureAwait(false);
        await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
    }

    public void Dispose() => _listener.Stop();
}

public sealed record YouTubeAuthorizationCallback(bool Succeeded, string? Code, string Message)
{
    internal static YouTubeAuthorizationCallback Success(string code) =>
        new(true, code, "Logowanie YouTube zakończone.");

    internal static YouTubeAuthorizationCallback Failure(string message) =>
        new(false, null, message);
}
