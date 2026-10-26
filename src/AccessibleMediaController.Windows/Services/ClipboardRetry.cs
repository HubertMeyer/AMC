using System.Runtime.InteropServices;
using System.Windows;

namespace AccessibleMediaController.Windows.Services;

internal static class ClipboardRetry
{
    private static readonly int[] RetryDelaysMilliseconds = [0, 20, 40, 80, 160, 250];

    public static bool TrySetText(string text, out string errorMessage)
    {
        ArgumentNullException.ThrowIfNull(text);
        // Text is a native clipboard format. The dedicated WPF API avoids the
        // generic object-serialization path, which can attempt BinaryFormatter
        // after earlier multi-format clipboard operations in the same process.
        return TrySetWithRetry(
            () => Clipboard.SetText(text, TextDataFormat.UnicodeText),
            DataFormats.UnicodeText,
            out errorMessage);
    }

    public static bool TrySetDataObject(object data, out string errorMessage)
    {
        ArgumentNullException.ThrowIfNull(data);
        var dataDescription = DescribeData(data);
        return TrySetWithRetry(
            () => Clipboard.SetDataObject(data, true),
            dataDescription,
            out errorMessage);
    }

    private static bool TrySetWithRetry(
        Action write,
        string dataDescription,
        out string errorMessage)
    {
        Exception? lastError = null;
        for (var attempt = 0; attempt < RetryDelaysMilliseconds.Length; attempt++)
        {
            var delay = RetryDelaysMilliseconds[attempt];
            if (delay > 0) Thread.Sleep(delay);
            try
            {
                write();
                DiagnosticLog.Info(
                    "clipboard",
                    attempt == 0
                        ? $"Zapisano schowek: {dataDescription}."
                        : $"Zapisano schowek po {attempt + 1} próbach: {dataDescription}.");
                errorMessage = string.Empty;
                return true;
            }
            catch (Exception exception) when (
                exception is ExternalException or InvalidOperationException or NotSupportedException)
            {
                lastError = exception;
            }
        }

        var code = lastError is ExternalException external
            ? $" Kod 0x{external.ErrorCode:X8}."
            : string.Empty;
        errorMessage = lastError is NotSupportedException
            ? "Nie udało się zapisać danych w bezpiecznym formacie schowka. Spróbuj ponownie."
            : $"Schowek jest zajęty przez inną aplikację. Spróbuj ponownie.{code}";
        DiagnosticLog.Error(
            "clipboard",
            $"Nie udało się zapisać schowka po {RetryDelaysMilliseconds.Length} próbach: {dataDescription}.",
            lastError);
        return false;
    }

    private static string DescribeData(object data)
    {
        if (data is not IDataObject dataObject) return data.GetType().Name;
        try
        {
            var formats = dataObject.GetFormats(false);
            return formats.Length == 0 ? "brak formatów" : string.Join(", ", formats);
        }
        catch (Exception exception) when (exception is ExternalException or InvalidOperationException)
        {
            return data.GetType().Name;
        }
    }
}
