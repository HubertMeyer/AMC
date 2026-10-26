using System.Windows;
using AccessibleMediaController.Windows.Controls;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.Windows;

public partial class AppleMusicAccountWindow : AccessibleWindow
{
    private readonly AppleMusicIntegrationService integration;
    private readonly AppleMusicMediaOutput output;
    private readonly Func<Task> synchronizeLibrary;
    private readonly CancellationTokenSource lifetime = new();

    internal AppleMusicAccountWindow(
        AppleMusicIntegrationService integration,
        AppleMusicMediaOutput output,
        Func<Task> synchronizeLibrary)
    {
        this.integration = integration;
        this.output = output;
        this.synchronizeLibrary = synchronizeLibrary;
        InitializeComponent();
    }

    public event EventHandler? AccountChanged;

    private void Window_Loaded(object sender, RoutedEventArgs e)
    {
        StorefrontBox.Text = "pl";
        if (integration.TryGetCredentials(out var credentials) && credentials is not null)
        {
            StorefrontBox.Text = credentials.Storefront;
            SetStatus(string.IsNullOrWhiteSpace(credentials.MusicUserToken)
                ? "Token deweloperski jest zapisany. Konto użytkownika nie jest zalogowane."
                : "Token deweloperski i logowanie użytkownika są zapisane bezpiecznie.");
        }
        else
        {
            SetStatus("Brak konfiguracji. Wklej gotowy developer token JWT i wybierz Zapisz i sprawdź token.");
        }
        DeveloperTokenBox.Focus();
    }

    private async void Save_Click(object sender, RoutedEventArgs e)
    {
        await SaveAndValidateAsync();
    }

    private async void Login_Click(object sender, RoutedEventArgs e)
    {
        if (!await EnsureDeveloperTokenAsync()) return;
        try
        {
            SetBusy(true, "Otwieranie oficjalnego logowania Apple Music…");
            var credentials = integration.RequireCredentials(requireUserToken: false);
            var token = await output.AuthorizeAsync(
                credentials.DeveloperToken,
                credentials.MusicUserToken,
                lifetime.Token);
            integration.SaveMusicUserToken(token);
            AccountChanged?.Invoke(this, EventArgs.Empty);
            SetStatus("Zalogowano konto Apple Music. Możesz pobrać bibliotekę.");
        }
        catch (OperationCanceledException) when (lifetime.IsCancellationRequested) { }
        catch (Exception exception)
        {
            SetStatus($"Nie zalogowano konta Apple Music. {exception.Message}");
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async void Sync_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            _ = integration.RequireCredentials(requireUserToken: true);
            SetBusy(true, "Pobieranie biblioteki Apple Music…");
            await synchronizeLibrary();
            SetStatus("Biblioteka Apple Music jest gotowa.");
        }
        catch (Exception exception)
        {
            SetStatus($"Nie pobrano biblioteki Apple Music. {exception.Message}");
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
            output.Unauthorize();
            integration.SignOut();
            AccountChanged?.Invoke(this, EventArgs.Empty);
            SetStatus("Wylogowano konto użytkownika. Token deweloperski pozostaje zapisany.");
        }
        catch (Exception exception)
        {
            SetStatus($"Nie wylogowano konta Apple Music. {exception.Message}");
        }
    }

    private void Remove_Click(object sender, RoutedEventArgs e)
    {
        if (MessageBox.Show(
                this,
                "Usunąć token deweloperski i logowanie użytkownika Apple Music z Menedżera poświadczeń Windows?",
                "Usuń konfigurację Apple Music",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question) != MessageBoxResult.Yes) return;
        output.Unauthorize();
        integration.RemoveConfiguration();
        DeveloperTokenBox.Clear();
        AccountChanged?.Invoke(this, EventArgs.Empty);
        SetStatus("Usunięto konfigurację i logowanie Apple Music.");
    }

    private async Task<bool> EnsureDeveloperTokenAsync()
    {
        if (!string.IsNullOrWhiteSpace(DeveloperTokenBox.Password))
            return await SaveAndValidateAsync();
        if (integration.IsConfigured) return true;
        SetStatus("Najpierw wklej developer token JWT i wybierz Zapisz i sprawdź token.");
        DeveloperTokenBox.Focus();
        return false;
    }

    private async Task<bool> SaveAndValidateAsync()
    {
        var token = DeveloperTokenBox.Password.Trim();
        if (token.Length == 0 && integration.TryGetCredentials(out var existing) && existing is not null)
            token = existing.DeveloperToken;
        var storefront = StorefrontBox.Text.Trim().ToLowerInvariant();
        if (!AppleMusicCredentialStore.IsDeveloperToken(token))
        {
            SetStatus("Wklej gotowy developer token JWT. Nie wklejaj pliku ani zawartości klucza .p8.");
            DeveloperTokenBox.Focus();
            return false;
        }
        if (!AppleMusicCredentialStore.IsStorefront(storefront))
        {
            SetStatus("Kod katalogu musi mieć dwie litery. Dla Polski wpisz pl.");
            StorefrontBox.Focus();
            return false;
        }
        try
        {
            SetBusy(true, "Sprawdzanie tokenu deweloperskiego Apple Music…");
            await integration.ValidateDeveloperTokenAsync(token, storefront, lifetime.Token);
            integration.SaveDeveloperToken(token, storefront);
            DeveloperTokenBox.Clear();
            AccountChanged?.Invoke(this, EventArgs.Empty);
            SetStatus("Token deweloperski jest poprawny i zapisany bezpiecznie.");
            return true;
        }
        catch (Exception exception)
        {
            SetStatus($"Token deweloperski nie został zapisany. {exception.Message}");
            return false;
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void SetBusy(bool busy, string? status = null)
    {
        SaveButton.IsEnabled = !busy;
        LoginButton.IsEnabled = !busy;
        SyncButton.IsEnabled = !busy;
        SignOutButton.IsEnabled = !busy;
        RemoveButton.IsEnabled = !busy;
        if (status is not null) SetStatus(status);
    }

    private void SetStatus(string message) => StatusText.Announce(message);

    private void Window_Closed(object? sender, EventArgs e)
    {
        lifetime.Cancel();
        lifetime.Dispose();
    }
}
