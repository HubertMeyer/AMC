using System.ComponentModel;
using System.IO;
using System.Windows;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

/// <summary>
/// Dedicated, modal confirmation and progress surface for destructive clip
/// removal. Keeping the whole operation in this window prevents focus from
/// falling back to the player (and its Play/Pause button) while FFmpeg is still
/// editing the file.
/// </summary>
public partial class AudioClipRemovalWindow : Controls.AccessibleWindow
{
    private readonly AudioClipRemovalRequest _request;
    private readonly bool _keepBackup;
    private readonly Action _beforeRemoval;
    private CancellationTokenSource? _cancellation;
    private bool _working;
    private bool _allowClose;
    private int _lastAnnouncedPercent = -10;
    private string _lastProgressPhase = string.Empty;

    public AudioClipRemovalWindow(
        string sourcePath,
        string sourceTitle,
        TimeSpan start,
        TimeSpan end,
        TimeSpan sourceDuration,
        bool keepBackup,
        Action beforeRemoval)
    {
        InitializeComponent();
        _request = new AudioClipRemovalRequest(sourcePath, start, end, sourceDuration);
        _keepBackup = keepBackup;
        _beforeRemoval = beforeRemoval ?? throw new ArgumentNullException(nameof(beforeRemoval));

        SelectionText.Text = $"{sourceTitle}. Do usunięcia: od {start:c} do {end:c}.";
        System.Windows.Automation.AutomationProperties.SetName(SelectionText, SelectionText.Text);

        var backupNotice = keepBackup
            ? "Kopia poprzedniej wersji zostanie zachowana po edycji obok pliku."
            : "Kopia poprzedniej wersji zostanie usunięta po sprawdzeniu wyniku.";
        RemovalRulesText.Text =
            "Usunięcie zmieni oryginalny plik i zatrzyma jego odtwarzanie. "
            + "Dźwięk nie będzie ponownie kompresowany; w formatach stratnych granice mogą zostać "
            + "dopasowane do najbliższej ramki kodeka. "
            + backupNotice
            + " Przy błędzie albo niepewnym wyniku oryginał pozostanie bez zmian.";
        System.Windows.Automation.AutomationProperties.SetName(RemovalRulesText, RemovalRulesText.Text);
        System.Windows.Automation.AutomationProperties.SetHelpText(
            RemoveButton,
            SelectionText.Text + " " + RemovalRulesText.Text);
    }

    internal AudioClipRemovalResult? Result { get; private set; }
    internal bool OperationStarted { get; private set; }

    private void Window_Loaded(object sender, RoutedEventArgs e) => CancelButton.Focus();

    private async void Remove_Click(object sender, RoutedEventArgs e)
    {
        if (_working) return;

        _working = true;
        OperationStarted = true;
        RemoveButton.IsEnabled = false;
        RemovalProgress.Value = 0;
        RemovalProgress.Visibility = Visibility.Visible;
        RemovalStatus.Text = "Przygotowywanie bezpiecznej kopii roboczej…";
        _lastAnnouncedPercent = -10;
        _lastProgressPhase = string.Empty;
        CancelButton.Content = "_Przerwij";
        _cancellation = new CancellationTokenSource();

        try
        {
            _beforeRemoval();
            var progress = new Progress<double>(value =>
            {
                if (!_working) return;
                RemovalProgress.Value = Math.Clamp(value * 100d, 0d, 100d);
                var percent = Math.Clamp((int)Math.Round(RemovalProgress.Value), 0, 100);
                var phase = percent switch
                {
                    < 80 => "Przygotowywanie pliku bez zaznaczonego fragmentu",
                    < 92 => "Łączenie pozostałych części",
                    < 100 => "Sprawdzanie gotowego pliku",
                    _ => "Kończenie usuwania"
                };
                if (!string.Equals(phase, _lastProgressPhase, StringComparison.Ordinal)
                    || percent >= _lastAnnouncedPercent + 10)
                {
                    RemovalStatus.Text = $"{phase}: {percent}%.";
                    _lastProgressPhase = phase;
                    _lastAnnouncedPercent = percent;
                }
            });
            var token = _cancellation.Token;
            Result = await Task.Run(
                () => AudioClipOriginalEditor.RemoveAsync(
                    _request,
                    progress,
                    token,
                    keepBackup: _keepBackup),
                token);

            RemovalProgress.Value = 100;
            RemovalStatus.Text = "Fragment usunięty. "
                + AudioClipAppendWindow.DescribeBackupOutcome(_keepBackup, Result.BackupPath);
            _allowClose = true;
            DialogResult = true;
        }
        catch (OperationCanceledException)
        {
            RemovalStatus.Text = "Usuwanie przerwane. Oryginalny plik nie został zmieniony.";
            DiagnosticLog.Info("audio-clip", "Anulowano usuwanie fragmentu z oryginalnego pliku.");
        }
        catch (Exception exception) when (exception is IOException
            or UnauthorizedAccessException
            or InvalidDataException
            or InvalidOperationException
            or NotSupportedException
            or ArgumentException)
        {
            DiagnosticLog.Error("audio-clip", "Nie udało się usunąć fragmentu z oryginalnego pliku.", exception);
            RemovalStatus.Text = exception.Message;
            AccessibleDialog.Show(
                this,
                exception.Message,
                "Nie udało się usunąć fragmentu",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        finally
        {
            _working = false;
            _cancellation?.Dispose();
            _cancellation = null;
            RemoveButton.IsEnabled = true;
            CancelButton.Content = "_Anuluj";
            if (!_allowClose) RemoveButton.Focus();
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        if (_working)
        {
            RemovalStatus.Text = "Przerywanie usuwania…";
            _cancellation?.Cancel();
            return;
        }

        _allowClose = true;
        DialogResult = false;
    }

    private void Window_Closing(object? sender, CancelEventArgs e)
    {
        if (_allowClose || !_working) return;
        e.Cancel = true;
        RemovalStatus.Text = "Przerywanie usuwania…";
        _cancellation?.Cancel();
    }
}
