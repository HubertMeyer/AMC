using System.Windows;
using AccessibleMediaController.Windows.Controls;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

internal sealed record YouTubeGoogleImportSummary(
    int ChannelsImported,
    int PlaylistsImported,
    int MaterialsImported,
    int FailedSources);

public partial class YouTubeGoogleAccountWindow : AccessibleWindow
{
    private readonly YouTubeGoogleIntegrationService integration;
    private readonly Func<YouTubeAccountLibrary, CancellationToken, Task<YouTubeGoogleImportSummary>> importLibrary;
    private readonly CancellationTokenSource lifetime = new();

    internal YouTubeGoogleAccountWindow(
        YouTubeGoogleIntegrationService integration,
        Func<YouTubeAccountLibrary, CancellationToken, Task<YouTubeGoogleImportSummary>> importLibrary)
    {
        this.integration = integration;
        this.importLibrary = importLibrary;
        InitializeComponent();
    }

    private void Window_Loaded(object sender, RoutedEventArgs e)
    {
        if (integration.TryGetCredentials(out var credentials) && credentials is not null)
        {
            ClientIdBox.Text = credentials.ClientId;
            if (credentials.HasLogin)
            {
                SetStatus(credentials.AccountDisplayName.Length > 0
                    ? $"Zalogowano: {credentials.AccountDisplayName}. Możesz importować subskrypcje i playlisty."
                    : "Konto Google jest zalogowane. Możesz importować subskrypcje i playlisty.");
                ImportButton.Focus();
            }
            else
            {
                SetStatus("Client ID jest zapisany. Wybierz Zaloguj kontem Google.");
                LoginButton.Focus();
            }
        }
        else
        {
            SetStatus("Brak konfiguracji. Wklej Client ID typu Aplikacja na komputer i wybierz Zapisz Client ID.");
            ClientIdBox.Focus();
        }
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            integration.SaveClientId(ClientIdBox.Text);
            SetStatus("Zapisano Client ID w Menedżerze poświadczeń Windows. Teraz wybierz Zaloguj kontem Google.");
            LoginButton.Focus();
        }
        catch (Exception exception)
        {
            SetStatus($"Nie zapisano Client ID. {exception.Message}");
            ClientIdBox.Focus();
            ClientIdBox.SelectAll();
        }
    }

    private async void Login_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            integration.SaveClientId(ClientIdBox.Text);
            SetBusy(true, "Otwieranie oficjalnej strony logowania Google w zwykłej przeglądarce…");
            var account = await integration.AuthorizeAsync(lifetime.Token);
            SetStatus($"Zalogowano: {account}. Możesz importować subskrypcje i playlisty.");
            ImportButton.Focus();
        }
        catch (OperationCanceledException) when (lifetime.IsCancellationRequested) { }
        catch (Exception exception)
        {
            SetStatus($"Nie zalogowano konta Google. {exception.Message}");
            LoginButton.Focus();
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async void Import_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            SetBusy(true, "Pobieranie subskrypcji i playlist YouTube. Przy dużym koncie może to potrwać kilka minut…");
            var library = await integration.ReadLibraryAsync(lifetime.Token);
            var summary = await importLibrary(library, lifetime.Token);
            var failures = summary.FailedSources > 0
                ? $" Nie udało się odczytać źródeł: {summary.FailedSources}."
                : string.Empty;
            SetStatus(
                $"Import zakończony. Kanały: {summary.ChannelsImported}; playlisty: {summary.PlaylistsImported}; materiały: {summary.MaterialsImported}.{failures}");
            ImportButton.Focus();
        }
        catch (OperationCanceledException) when (lifetime.IsCancellationRequested) { }
        catch (Exception exception)
        {
            SetStatus($"Nie ukończono importu YouTube. {exception.Message}");
            ImportButton.Focus();
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void SignOut_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            integration.SignOut();
            SetStatus("Wylogowano konto Google z AMC. Zapisany Client ID pozostaje gotowy do ponownego logowania.");
            LoginButton.Focus();
        }
        catch (Exception exception)
        {
            SetStatus($"Nie wylogowano konta Google. {exception.Message}");
            SignOutButton.Focus();
        }
    }

    private void Remove_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show(
                this,
                "Usunąć Client ID i tokeny logowania YouTube z Menedżera poświadczeń Windows? Zaimportowana biblioteka pozostanie w AMC.",
                "Usuń konfigurację YouTube",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question) != MessageBoxResult.Yes)
        {
            RemoveButton.Focus();
            return;
        }

        try
        {
            integration.RemoveConfiguration();
            ClientIdBox.Clear();
            SetStatus("Usunięto konfigurację i logowanie YouTube. Zaimportowana biblioteka AMC nie została usunięta.");
            ClientIdBox.Focus();
        }
        catch (Exception exception)
        {
            SetStatus($"Nie usunięto konfiguracji YouTube. {exception.Message}");
            RemoveButton.Focus();
        }
    }

    private void SetBusy(bool busy, string? status = null)
    {
        SaveButton.IsEnabled = !busy;
        LoginButton.IsEnabled = !busy;
        ImportButton.IsEnabled = !busy;
        SignOutButton.IsEnabled = !busy;
        RemoveButton.IsEnabled = !busy;
        ClientIdBox.IsEnabled = !busy;
        if (!string.IsNullOrWhiteSpace(status)) SetStatus(status);
    }

    private void SetStatus(string message) => StatusText.Announce(message);

    private void Window_Closed(object? sender, EventArgs e)
    {
        lifetime.Cancel();
        lifetime.Dispose();
    }
}
