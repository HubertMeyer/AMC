using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using AccessibleMediaController.Core.Playback;
using AccessibleMediaController.Core.Sessions;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.Wpf;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Oficjalny MusicKit on the Web działa jako niewidoczny silnik. Widoczne
/// sterowanie pozostaje natywne; tylko okno logowania Apple jest webowe.
/// </summary>
internal sealed class AppleMusicMediaOutput : IMediaOutput, IDisposable
{
    private const string VirtualHostName = "apple-music.amc.local";
    private readonly AppleMusicIntegrationService integration;
    private readonly WebView2 webView;
    private readonly CancellationTokenSource lifetime = new();
    private readonly TaskCompletionSource<bool> bridgeReady = new(
        TaskCreationOptions.RunContinuationsAsynchronously);
    private readonly SemaphoreSlim configurationGate = new(1, 1);
    private readonly object stateGate = new();
    private readonly List<Window> authorizationWindows = [];
    private Task? initialization;
    private TaskCompletionSource<bool>? configured;
    private TaskCompletionSource<string>? authorized;
    private string? configuredDeveloperToken;
    private string? configuredUserToken;
    private MediaItem? currentItem;
    private string? loadedItemId;
    private TimeSpan position;
    private bool preparing;
    private bool disposed;
    private int requestVersion;

    public AppleMusicMediaOutput(AppleMusicIntegrationService integration, WebView2 webView)
    {
        this.integration = integration;
        this.webView = webView;
    }

    public event EventHandler<MediaDurationAvailableEventArgs>? DurationAvailable;
    public event EventHandler<MediaOutputFailedEventArgs>? PlaybackFailed;
    public event EventHandler<MediaPlaybackEndedEventArgs>? PlaybackEnded;
    public event EventHandler<MediaPlaybackPreparingEventArgs>? PlaybackPreparing;
    public event EventHandler<MediaPlaybackStartedEventArgs>? PlaybackStarted;

    public string? LoadedItemId { get { lock (stateGate) return loadedItemId; } }
    public TimeSpan Position { get { lock (stateGate) return position; } }
    public bool IsPreparing { get { lock (stateGate) return preparing; } }
    public bool SupportsPlaybackRate => false;

    public void Play(MediaItem item, TimeSpan position, int volume, double playbackRate)
    {
        if (!TryPlaybackResource(item, out var type, out var id))
        {
            var message = item.ExternalId?.StartsWith("library-", StringComparison.Ordinal) == true
                ? "Ten element biblioteki Apple Music nie ma katalogowego identyfikatora potrzebnego MusicKit do odtwarzania w AMC. Otwórz go w aplikacji Apple Music."
                : "Apple Music odtwarza w AMC pojedyncze utwory i teledyski. Otwórz album albo playlistę i wybierz element.";
            PlaybackFailed?.Invoke(this, new MediaOutputFailedEventArgs(
                item,
                message));
            return;
        }
        int version;
        lock (stateGate)
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            version = ++requestVersion;
            currentItem = item;
            loadedItemId = item.Id;
            this.position = position < TimeSpan.Zero ? TimeSpan.Zero : position;
            preparing = true;
        }
        PlaybackPreparing?.Invoke(this, new MediaPlaybackPreparingEventArgs(item, false));
        _ = StartPlaybackAsync(item, type, id, position, volume, version, lifetime.Token);
    }

    public void Pause() => PostCommand(new { type = "pause" });

    public void Stop()
    {
        lock (stateGate)
        {
            requestVersion++;
            currentItem = null;
            loadedItemId = null;
            position = TimeSpan.Zero;
            preparing = false;
        }
        PostCommand(new { type = "stop" });
    }

    public void Seek(TimeSpan value)
    {
        var normalized = value < TimeSpan.Zero ? TimeSpan.Zero : value;
        lock (stateGate) position = normalized;
        PostCommand(new { type = "seek", position = normalized.TotalSeconds });
    }

    public void SetVolume(int volume) => PostCommand(new
    {
        type = "volume",
        volume = Math.Clamp(volume, 0, 100) / 100d
    });

    public void SetPlaybackRate(double playbackRate) { }

    public async Task<string> AuthorizeAsync(
        string developerToken,
        string? existingUserToken,
        CancellationToken cancellationToken)
    {
        await EnsureConfiguredAsync(developerToken, existingUserToken, cancellationToken);
        var completion = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
        lock (stateGate) authorized = completion;
        PostCommand(new { type = "authorize" });
        return await completion.Task.WaitAsync(TimeSpan.FromMinutes(5), cancellationToken);
    }

    public void Unauthorize()
    {
        configuredUserToken = null;
        PostCommand(new { type = "unauthorize" });
    }

    private async Task StartPlaybackAsync(
        MediaItem item,
        string resourceType,
        string resourceId,
        TimeSpan startPosition,
        int volume,
        int version,
        CancellationToken cancellationToken)
    {
        try
        {
            var credentials = integration.RequireCredentials(requireUserToken: true);
            await EnsureConfiguredAsync(
                credentials.DeveloperToken,
                credentials.MusicUserToken,
                cancellationToken).ConfigureAwait(false);
            if (!IsCurrent(version, item.Id)) return;
            await webView.Dispatcher.InvokeAsync(() =>
                webView.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(new
                {
                    type = "play",
                    requestVersion = version,
                    itemId = item.Id,
                    resourceType,
                    resourceId,
                    position = Math.Max(0, startPosition.TotalSeconds),
                    volume = Math.Clamp(volume, 0, 100) / 100d
                })), DispatcherPriority.Send, cancellationToken);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { }
        catch (Exception exception)
        {
            RaiseOnUi(() => HandlePlaybackFailure(item, FriendlyFailure(exception.Message)));
        }
    }

    private async Task EnsureConfiguredAsync(
        string developerToken,
        string? userToken,
        CancellationToken cancellationToken)
    {
        await EnsureInitialization().ConfigureAwait(false);
        await bridgeReady.Task.WaitAsync(cancellationToken).ConfigureAwait(false);
        await configurationGate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (string.Equals(configuredDeveloperToken, developerToken, StringComparison.Ordinal)
                && string.Equals(configuredUserToken, userToken, StringComparison.Ordinal)) return;
            var completion = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
            lock (stateGate) configured = completion;
            await webView.Dispatcher.InvokeAsync(() =>
                webView.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(new
                {
                    type = "configure",
                    developerToken,
                    musicUserToken = userToken,
                    build = typeof(AppleMusicMediaOutput).Assembly.GetName().Version?.ToString() ?? "test"
                })), DispatcherPriority.Send, cancellationToken);
            await completion.Task.WaitAsync(TimeSpan.FromSeconds(45), cancellationToken);
            configuredDeveloperToken = developerToken;
            configuredUserToken = userToken;
        }
        finally
        {
            configurationGate.Release();
        }
    }

    private Task EnsureInitialization()
    {
        lock (stateGate)
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            return initialization ??= InitializeAsync();
        }
    }

    private async Task InitializeAsync()
    {
        try
        {
            var folder = Path.Combine(AppContext.BaseDirectory, "apple-music-player");
            if (!File.Exists(Path.Combine(folder, "index.html"))
                || !File.Exists(Path.Combine(folder, "bridge.js")))
            {
                throw new FileNotFoundException("W instalacji AMC brakuje składników odtwarzacza Apple Music.");
            }
            var profile = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "AccessibleMediaController", "WebView2", "AppleMusic");
            Directory.CreateDirectory(profile);
            var environment = await CoreWebView2Environment.CreateAsync(userDataFolder: profile);
            await webView.EnsureCoreWebView2Async(environment);
            if (disposed) return;
            var core = webView.CoreWebView2;
            core.Settings.AreBrowserAcceleratorKeysEnabled = false;
            core.Settings.AreDefaultContextMenusEnabled = false;
            core.Settings.AreDevToolsEnabled = false;
            core.Settings.IsStatusBarEnabled = false;
            core.Settings.IsZoomControlEnabled = false;
            core.Settings.IsWebMessageEnabled = true;
            await HeadlessPlaybackWebViewPolicy.ApplyAsync(core);
            core.WebMessageReceived += Core_WebMessageReceived;
            core.ProcessFailed += Core_ProcessFailed;
            core.NewWindowRequested += Core_NewWindowRequested;
            core.SetVirtualHostNameToFolderMapping(
                VirtualHostName, folder, CoreWebView2HostResourceAccessKind.DenyCors);
            core.Navigate($"https://{VirtualHostName}/index.html");
        }
        catch (Exception exception) when (exception is FileNotFoundException
            or DirectoryNotFoundException or UnauthorizedAccessException
            or WebView2RuntimeNotFoundException or InvalidOperationException or COMException)
        {
            bridgeReady.TrySetException(exception);
            DiagnosticLog.Error("apple-music-player", "Nie przygotowano MusicKit on the Web.", exception);
        }
    }

    private void Core_WebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        try
        {
            using var document = JsonDocument.Parse(e.WebMessageAsJson);
            var root = document.RootElement;
            var type = Text(root, "type");
            switch (type)
            {
                case "ready":
                    bridgeReady.TrySetResult(true);
                    break;
                case "configured":
                    lock (stateGate) configured?.TrySetResult(true);
                    break;
                case "authorized":
                    var token = Text(root, "musicUserToken");
                    if (string.IsNullOrWhiteSpace(token))
                        throw new InvalidOperationException("Apple Music nie zwrócił tokenu użytkownika.");
                    configuredUserToken = token;
                    lock (stateGate) authorized?.TrySetResult(token);
                    CloseAuthorizationWindows();
                    break;
                case "progress":
                    ApplyProgress(root);
                    break;
                case "started":
                    if (CurrentItem(root) is { } started)
                    {
                        lock (stateGate) preparing = false;
                        PlaybackStarted?.Invoke(this, new MediaPlaybackStartedEventArgs(started));
                    }
                    break;
                case "ended":
                    if (CurrentItem(root) is { } ended)
                    {
                        lock (stateGate)
                        {
                            preparing = false;
                            loadedItemId = null;
                        }
                        PlaybackEnded?.Invoke(this, new MediaPlaybackEndedEventArgs(ended));
                    }
                    break;
                case "error":
                    HandleBridgeError(root);
                    break;
            }
        }
        catch (Exception exception) when (exception is JsonException or InvalidOperationException)
        {
            DiagnosticLog.Warning("apple-music-player",
                $"Odrzucono komunikat MusicKit: {exception.GetType().Name}.");
        }
    }

    private void ApplyProgress(JsonElement root)
    {
        var item = CurrentItem(root);
        if (item is null) return;
        var seconds = Number(root, "position");
        var duration = Number(root, "duration");
        lock (stateGate)
        {
            if (seconds >= 0) position = TimeSpan.FromSeconds(seconds);
        }
        if (duration > 0 && Math.Abs(item.Duration.TotalSeconds - duration) >= 1)
        {
            item.Duration = TimeSpan.FromSeconds(duration);
            DurationAvailable?.Invoke(this, new MediaDurationAvailableEventArgs(item, item.Duration, 0));
        }
    }

    private void HandleBridgeError(JsonElement root)
    {
        var message = FriendlyFailure(Text(root, "message"));
        var scope = Text(root, "scope");
        if (scope == "configure")
        {
            lock (stateGate) configured?.TrySetException(new InvalidOperationException(message));
            return;
        }
        if (scope == "authorize")
        {
            lock (stateGate) authorized?.TrySetException(new InvalidOperationException(message));
            CloseAuthorizationWindows();
            return;
        }
        if (CurrentItem(root) is { } item) HandlePlaybackFailure(item, message);
    }

    private async void Core_NewWindowRequested(object? sender, CoreWebView2NewWindowRequestedEventArgs e)
    {
        var deferral = e.GetDeferral();
        try
        {
            var popup = new WebView2();
            var close = new Button { Content = "Zamknij logowanie", Margin = new Thickness(8) };
            AutomationProperties.SetName(close, "Zamknij logowanie Apple Music");
            var panel = new DockPanel();
            DockPanel.SetDock(close, Dock.Bottom);
            panel.Children.Add(close);
            panel.Children.Add(popup);
            var window = new Window
            {
                Title = "Logowanie Apple Music",
                Width = 720,
                Height = 760,
                MinWidth = 520,
                MinHeight = 520,
                Content = panel,
                Owner = Application.Current?.MainWindow,
                WindowStartupLocation = WindowStartupLocation.CenterOwner
            };
            close.Click += (_, _) => window.Close();
            window.Closed += (_, _) => authorizationWindows.Remove(window);
            await popup.EnsureCoreWebView2Async(webView.CoreWebView2.Environment);
            popup.CoreWebView2.Settings.AreDevToolsEnabled = false;
            popup.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            e.NewWindow = popup.CoreWebView2;
            e.Handled = true;
            authorizationWindows.Add(window);
            deferral.Complete();
            window.Show();
            popup.Focus();
            Keyboard.Focus(popup);
        }
        catch (Exception exception)
        {
            e.Handled = true;
            deferral.Complete();
            lock (stateGate) authorized?.TrySetException(new InvalidOperationException(
                "Nie udało się otworzyć oficjalnego logowania Apple Music.", exception));
        }
    }

    private void Core_ProcessFailed(object? sender, CoreWebView2ProcessFailedEventArgs e)
    {
        var exception = new InvalidOperationException("Proces MusicKit został nieoczekiwanie zatrzymany.");
        bridgeReady.TrySetException(exception);
        lock (stateGate)
        {
            configured?.TrySetException(exception);
            authorized?.TrySetException(exception);
        }
        if (currentItem is { } item) HandlePlaybackFailure(item, exception.Message);
    }

    private bool IsCurrent(int version, string itemId)
    {
        lock (stateGate)
            return !disposed && requestVersion == version
                && string.Equals(loadedItemId, itemId, StringComparison.Ordinal);
    }

    private MediaItem? CurrentItem(JsonElement root)
    {
        if (!root.TryGetProperty("requestVersion", out var versionElement)
            || !versionElement.TryGetInt32(out var version)
            || !IsCurrent(version, Text(root, "itemId"))) return null;
        lock (stateGate) return currentItem;
    }

    private void HandlePlaybackFailure(MediaItem item, string message)
    {
        lock (stateGate)
        {
            if (!string.Equals(currentItem?.Id, item.Id, StringComparison.Ordinal)) return;
            preparing = false;
            loadedItemId = null;
        }
        PlaybackFailed?.Invoke(this, new MediaOutputFailedEventArgs(item, message));
    }

    private void PostCommand(object command)
    {
        if (disposed || !bridgeReady.Task.IsCompletedSuccessfully) return;
        var json = JsonSerializer.Serialize(command);
        _ = webView.Dispatcher.InvokeAsync(() =>
        {
            if (!disposed && webView.CoreWebView2 is not null)
                webView.CoreWebView2.PostWebMessageAsJson(json);
        }, DispatcherPriority.Send);
    }

    private void CloseAuthorizationWindows()
    {
        RaiseOnUi(() =>
        {
            foreach (var window in authorizationWindows.ToArray()) window.Close();
            authorizationWindows.Clear();
        });
    }

    private void RaiseOnUi(Action action)
    {
        if (webView.Dispatcher.CheckAccess()) action();
        else _ = webView.Dispatcher.InvokeAsync(action, DispatcherPriority.Send);
    }

    internal static string FriendlyFailure(string? raw)
    {
        var message = new string((raw ?? string.Empty)
            .Where(character => !char.IsControl(character))
            .ToArray()).Trim();
        if (message.Contains("authorize", StringComparison.OrdinalIgnoreCase)
            || message.Contains("token", StringComparison.OrdinalIgnoreCase)
            || message.Contains("401", StringComparison.Ordinal))
            return "Logowanie Apple Music wygasło albo zostało odrzucone. Otwórz Konto Apple Music przez Ctrl+F5.";
        if (message.Contains("subscription", StringComparison.OrdinalIgnoreCase)
            || message.Contains("subscriber", StringComparison.OrdinalIgnoreCase))
            return "To konto nie ma aktywnej subskrypcji Apple Music wymaganej do pełnego odtwarzania.";
        if (message.Contains("drm", StringComparison.OrdinalIgnoreCase)
            || message.Contains("key system", StringComparison.OrdinalIgnoreCase))
            return "Silnik WebView2 nie uruchomił chronionego odtwarzania Apple Music na tym komputerze.";
        if (message.Contains("://", StringComparison.Ordinal)) message = "szczegóły pominięto";
        if (message.Length > 200) message = message[..200];
        return message.Length == 0
            ? "Nie udało się odtworzyć elementu Apple Music."
            : $"Nie udało się wykonać operacji Apple Music. {message}";
    }

    private static string Text(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString() ?? string.Empty
            : string.Empty;

    private static double Number(JsonElement element, string name) =>
        element.TryGetProperty(name, out var value)
        && value.ValueKind == JsonValueKind.Number
        && value.TryGetDouble(out var number)
        && double.IsFinite(number)
            ? number
            : 0;

    internal static bool TryPlaybackResource(MediaItem item, out string type, out string id)
    {
        type = string.Empty;
        id = string.Empty;
        var parts = item.ExternalId?.Split(':', 2);
        if (parts is not { Length: 2 } || string.IsNullOrWhiteSpace(parts[1])) return false;
        if (item.Kind == MediaItemKind.Track && parts[0] == "songs"
            || item.Kind == MediaItemKind.Video && parts[0] == "music-videos")
        {
            type = parts[0];
            id = parts[1];
            return true;
        }
        return false;
    }

    public void Dispose()
    {
        lock (stateGate)
        {
            if (disposed) return;
            disposed = true;
        }
        CloseAuthorizationWindows();
        lifetime.Cancel();
        lifetime.Dispose();
        configurationGate.Dispose();
    }
}
