using AccessibleMediaController.Core.Sonos;
using AccessibleMediaController.Windows.Services;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// Bezokienny właściciel konta Sonos dla hosta wxPython. Składa dokładnie te
/// same elementy Core i ten sam magazyn DPAPI co główne AMC, ale nie zależy od
/// WPF i nie udostępnia poświadczeń protokołowi ani Pythonowi.
/// </summary>
internal sealed class LiteSonosAccountOwner :
    ISonosGroupSessionBackend,
    ISonosFavoritesSessionBackend,
    ISonosFavoriteLoadSessionBackend,
    ISonosPlaylistsSessionBackend,
    ISonosPlaylistLoadSessionBackend,
    ISonosOwnStreamsSessionBackend,
    ISonosAccountBoundBackend,
    ILiteSonosAccountBackend,
    IDisposable
{
    private readonly object gate = new();
    private SonosLoginClient? loginClient;
    private SonosAccountCoordinator? coordinator;
    private SonosControlApiClient? controlClient;
    private SonosControlApiDeviceApi? deviceApi;
    private SonosControlApiGroupApi? groupApi;
    private bool disposed;

    public SonosAccountSnapshot? AccountSnapshot
    {
        get
        {
            lock (gate) return coordinator?.Snapshot;
        }
    }

    public SonosAccountSnapshot ReadAccountSnapshot(out Uri? pendingAuthorizeUri) =>
        EnsureCoordinator().ReadLoginStatus(out pendingAuthorizeUri);

    public Task<SonosAccountLoginStartResult> BeginLoginAsync(
        CancellationToken cancellationToken) =>
        EnsureCoordinator().BeginLoginAsync(cancellationToken);

    public Task<SonosAccountLoginCheckResult> CheckLoginAsync(
        CancellationToken cancellationToken) =>
        EnsureCoordinator().CheckLoginAsync(cancellationToken);

    public SonosAccountSnapshot CancelPendingLogin() =>
        EnsureCoordinator().CancelPendingLogin();

    public Task<SonosAccountRefreshResult> RefreshAccountAsync(
        CancellationToken cancellationToken) =>
        EnsureCoordinator().RefreshAsync(cancellationToken);

    public SonosAccountPersistRetryResult RetryPersist() =>
        EnsureCoordinator().RetryPersist();

    public SonosAccountDisconnectResult DisconnectAccount() =>
        EnsureCoordinator().Disconnect();

    public Task<SonosHouseholdsReadResult> ReadHouseholdsAsync(
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadHouseholdsAsync(EnsureDeviceApi(), cancellationToken);

    public Task<SonosGroupsReadResult> ReadGroupsAsync(
        string householdId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadGroupsAsync(
            EnsureDeviceApi(), householdId, cancellationToken);

    public Task<SonosGroupReadResult<SonosGroupPlaybackStatus>> ReadGroupPlaybackAsync(
        string? groupId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadGroupPlaybackAsync(
            EnsureGroupApi(), groupId, cancellationToken);

    public Task<SonosGroupReadResult<SonosGroupMetadata>> ReadGroupMetadataAsync(
        string? groupId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadGroupMetadataAsync(
            EnsureGroupApi(), groupId, cancellationToken);

    public Task<SonosGroupReadResult<SonosGroupVolume>> ReadGroupVolumeAsync(
        string? groupId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadGroupVolumeAsync(
            EnsureGroupApi(), groupId, cancellationToken);

    public Task<SonosGroupCommandResult> SendGroupCommandAsync(
        string? groupId,
        SonosGroupCommand command,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().SendGroupCommandAsync(
            EnsureGroupApi(), groupId, command, cancellationToken);

    public Task<SonosGroupCommandResult> SeekRelativeAsync(
        string? groupId,
        int deltaMillis,
        string? itemId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().SeekRelativeAsync(
            EnsureGroupApi(), groupId, deltaMillis, itemId, cancellationToken);

    public Task<SonosGroupCommandResult> SetGroupVolumeAsync(
        string? groupId,
        int volume,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().SetGroupVolumeAsync(
            EnsureGroupApi(), groupId, volume, cancellationToken);

    public Task<SonosGroupCommandResult> SetGroupMuteAsync(
        string? groupId,
        bool muted,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().SetGroupMuteAsync(
            EnsureGroupApi(), groupId, muted, cancellationToken);

    public Task<SonosFavoritesReadResult> ReadFavoritesAsync(
        string? householdId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadFavoritesAsync(
            EnsureControlClient(), householdId, cancellationToken);

    public Task<SonosGroupCommandResult> LoadFavoriteAsync(
        string? groupId,
        string? favoriteId,
        SonosFavoriteQueueAction action,
        bool playOnCompletion,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().LoadFavoriteAsync(
            EnsureControlClient(), groupId, favoriteId,
            action, playOnCompletion, cancellationToken);

    public Task<SonosPlaylistsReadResult> ReadPlaylistsAsync(
        string? householdId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().ReadPlaylistsAsync(
            EnsureControlClient(), householdId, cancellationToken);

    public Task<SonosGroupCommandResult> LoadPlaylistAsync(
        string? groupId,
        string? playlistId,
        SonosFavoriteQueueAction action,
        bool playOnCompletion,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().LoadPlaylistAsync(
            EnsureControlClient(), groupId, playlistId,
            action, playOnCompletion, cancellationToken);

    public Task<SonosSessionCreateResult> CreateSessionAsync(
        string? groupId,
        SonosSessionRequest request,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().CreateSessionAsync(
            EnsureControlClient(), groupId, request, cancellationToken);

    public Task<SonosStreamUrlLoadResult> LoadStreamUrlAsync(
        string? sessionId,
        string? streamUrl,
        bool playOnCompletion,
        string? itemId,
        CancellationToken cancellationToken) =>
        EnsureCoordinator().LoadStreamUrlAsync(
            EnsureControlClient(), sessionId, streamUrl,
            playOnCompletion, itemId, cancellationToken);

    private SonosAccountCoordinator EnsureCoordinator()
    {
        lock (gate)
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            if (coordinator is not null) return coordinator;
            if (!SonosLoginBrokerConfiguration.TryCreate(
                    SonosIntegrationDefaults.BrokerOrigin,
                    out var broker)
                || broker is null)
            {
                throw new InvalidOperationException(
                    "Wbudowany adres logowania Sonos jest nieprawidłowy.");
            }

            loginClient = new SonosLoginClient(broker);
            var store = new SonosDpapiCredentialStore(
                broker, SonosDpapiCredentialStore.DefaultFilePath());
            coordinator = new SonosAccountCoordinator(
                new SonosLoginClientGateway(loginClient),
                store,
                broker.Origin.AbsoluteUri);
            coordinator.RestoreOnce();
            return coordinator;
        }
    }

    private SonosControlApiClient EnsureControlClient()
    {
        lock (gate)
        {
            ObjectDisposedException.ThrowIf(disposed, this);
            if (controlClient is not null) return controlClient;
            controlClient = new SonosControlApiClient(
                SonosControlApiConfiguration.CreateDefault(
                    SonosIntegrationDefaults.ControlApiKey));
            deviceApi = new SonosControlApiDeviceApi(controlClient);
            groupApi = new SonosControlApiGroupApi(controlClient);
            return controlClient;
        }
    }

    private ISonosDeviceApi EnsureDeviceApi()
    {
        EnsureControlClient();
        lock (gate)
        {
            return deviceApi ?? throw new InvalidOperationException(
                "Klient odczytu urządzeń Sonos nie został utworzony.");
        }
    }

    private ISonosGroupApi EnsureGroupApi()
    {
        EnsureControlClient();
        lock (gate)
        {
            return groupApi ?? throw new InvalidOperationException(
                "Klient sterowania grupą Sonos nie został utworzony.");
        }
    }

    public void Dispose()
    {
        SonosAccountCoordinator? oldCoordinator;
        SonosLoginClient? oldLogin;
        SonosControlApiClient? oldControl;
        lock (gate)
        {
            if (disposed) return;
            disposed = true;
            oldCoordinator = coordinator;
            oldLogin = loginClient;
            oldControl = controlClient;
            coordinator = null;
            loginClient = null;
            controlClient = null;
            deviceApi = null;
            groupApi = null;
        }
        oldCoordinator?.Dispose();
        oldLogin?.Dispose();
        oldControl?.Dispose();
    }
}
