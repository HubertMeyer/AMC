using System.Diagnostics;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.YouTube;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Produkcyjny właściciel tokenu i świeżego podglądu. Zapis jest możliwy tylko
/// po podglądzie nie starszym niż dziesięć minut i dla tego samego wyboru
/// jawnego przywracania usuniętych kanałów.
/// </summary>
internal sealed class LiteYouTubeWindowsAccountBackend : ILiteYouTubeAccountBackend
{
    private static readonly TimeSpan PreviewLifetime = TimeSpan.FromMinutes(10);
    private readonly YouTubeAccountCoordinator _account;
    private readonly YouTubeSubscriptionClient _subscriptions = new();
    private readonly PodcastLibraryMutationStore _podcasts;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private PreviewSnapshot? _preview;
    private bool _disposed;

    internal LiteYouTubeWindowsAccountBackend(
        string clientId,
        string releaseProfile,
        string podcastsDatabasePath)
    {
        _podcasts = new PodcastLibraryMutationStore(
            Path.GetFullPath(podcastsDatabasePath));
        _account = new YouTubeAccountCoordinator(
            clientId,
            YouTubeCredentialStore.ForReleaseProfile(releaseProfile),
            new YouTubeOAuthTokenClient(),
            OpenAuthorizationPageAsync);
    }

    public YouTubeAccountStatus GetStatus() => _account.GetStatus();

    public async Task<YouTubeAccountOperationResult> LoginAsync(
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            var result = await _account.LoginAsync(cancellationToken).ConfigureAwait(false);
            if (result.Succeeded) _preview = null;
            return result;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<YouTubeAccountOperationResult> LogoutAsync(
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            var result = await _account.LogoutAsync(cancellationToken).ConfigureAwait(false);
            _preview = null;
            return result;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<YouTubeSubscriptionSyncPlan> PreviewAsync(
        bool restoreSuppressed,
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            var token = await _account.GetAccessTokenAsync(cancellationToken)
                .ConfigureAwait(false);
            var remote = await _subscriptions.ReadAllAsync(token, cancellationToken)
                .ConfigureAwait(false);
            var plan = _podcasts.PreviewYouTubeSubscriptions(remote, restoreSuppressed);
            _preview = new PreviewSnapshot(
                remote.ToArray(),
                restoreSuppressed,
                DateTimeOffset.UtcNow);
            return plan;
        }
        finally
        {
            _gate.Release();
        }
    }

    public async Task<YouTubeSubscriptionSyncApplyResult> ApplyAsync(
        bool restoreSuppressed,
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_preview is not { } preview
                || preview.RestoreSuppressed != restoreSuppressed
                || DateTimeOffset.UtcNow - preview.CreatedAtUtc > PreviewLifetime)
            {
                throw new InvalidOperationException(
                    "Najpierw sprawdź aktualne subskrypcje YouTube i zatwierdź ten sam zakres zmian.");
            }
            var result = _podcasts.ApplyYouTubeSubscriptions(
                preview.Subscriptions,
                restoreSuppressed);
            _preview = null;
            return result;
        }
        finally
        {
            _gate.Release();
        }
    }

    private static Task<bool> OpenAuthorizationPageAsync(
        Uri address,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        try
        {
            return Task.FromResult(Process.Start(new ProcessStartInfo
            {
                FileName = address.AbsoluteUri,
                UseShellExecute = true
            }) is not null);
        }
        catch (Exception exception) when (exception is InvalidOperationException
            or System.ComponentModel.Win32Exception)
        {
            return Task.FromResult(false);
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _preview = null;
        _gate.Dispose();
        _subscriptions.Dispose();
        _account.Dispose();
    }

    private sealed record PreviewSnapshot(
        IReadOnlyList<YouTubeSubscription> Subscriptions,
        bool RestoreSuppressed,
        DateTimeOffset CreatedAtUtc);
}
