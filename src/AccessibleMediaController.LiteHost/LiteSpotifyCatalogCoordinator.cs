using System.Text.Json;
using AccessibleMediaController.Core.Sessions;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

/// <summary>
/// The only Spotify surface exposed by LiteHost in the first integration
/// stage. It never starts authentication and contains no write operation.
/// </summary>
internal sealed class LiteSpotifyCatalogCoordinator(
    ILiteSpotifyReadOnlyBackend backend) : IDisposable
{
    private readonly object _collectionGate = new();
    private IReadOnlyList<MediaItem> _collectionSnapshot = backend.CachedCollection;
    private bool _collectionRefreshAttempted;

    public object Capabilities() => LiteSpotifyCatalogContract.CreateCapabilities();

    public object AccountStatus()
    {
        try
        {
            return LiteSpotifyCatalogContract.CreateAccountStatus(backend.ReadAccountStatus());
        }
        catch
        {
            // Credential Manager and account errors must never escape through
            // exception.Message. At this boundary even the exception type is
            // deliberately discarded.
            return LiteSpotifyCatalogContract.CreateAccountStatus(
                new LiteSpotifyAccountProbe(
                    CatalogConfigured: true,
                    CatalogConnected: null,
                    AccountDisplayName: string.Empty,
                    AccountProduct: string.Empty,
                    PlaybackConnected: null));
        }
    }

    public object CollectionRoot() => LiteSpotifyCatalogContract.CreateCollectionRoot();

    public object CollectionView(JsonElement args)
    {
        var view = LiteSpotifyCatalogContract.ReadCollectionView(args);
        lock (_collectionGate)
        {
            var warning = string.Empty;
            LiteSpotifyAccountProbe account;
            try
            {
                account = backend.ReadAccountStatus();
            }
            catch
            {
                account = new LiteSpotifyAccountProbe(
                    true, null, string.Empty, string.Empty, null);
            }

            // The legacy profile already contains a durable collection cache.
            // Showing one category must not first synchronize every saved
            // track, album, artist, playlist and podcast: a real profile with
            // thousands of tracks needs over a minute for that operation and
            // consumes all concurrent host slots when Enter is repeated.
            // Use the populated snapshot immediately.  A network refresh is
            // retained only as the fallback for a profile with no cache.
            if (!_collectionRefreshAttempted
                && _collectionSnapshot.Count == 0
                && account.CatalogConnected == true)
            {
                _collectionRefreshAttempted = true;
                try
                {
                    var refreshed = backend.RefreshCollectionAsync(CancellationToken.None)
                        .GetAwaiter()
                        .GetResult();
                    _collectionSnapshot = refreshed.Items;
                    if (refreshed.HadWarnings)
                    {
                        warning = "Nie wszystkie części kolekcji Spotify udało się odświeżyć.";
                    }
                }
                catch (Exception exception)
                {
                    warning = SafeFailure(exception, LiteSpotifyCatalogContract.CollectionViewOperation)
                        + " Pokazano ostatni zapis.";
                }
            }
            else if (!account.CatalogConfigured)
            {
                warning = "Katalog Spotify nie jest skonfigurowany. Pokazano ostatni zapis.";
            }
            else if (account.CatalogConnected == false)
            {
                warning = "Katalog Spotify nie jest połączony. Pokazano ostatni zapis.";
            }
            else if (account.CatalogConnected is null)
            {
                warning = "Nie można sprawdzić połączenia katalogu Spotify. Pokazano ostatni zapis.";
            }

            return LiteSpotifyCatalogContract.CreateCollectionViewResult(
                view,
                _collectionSnapshot,
                warning);
        }
    }

    public object Search(JsonElement args)
    {
        var query = LiteSpotifyCatalogContract.ReadSearchQuery(args);
        EnsureCatalogReady();
        try
        {
            var items = backend.SearchAsync(query, CancellationToken.None)
                .GetAwaiter()
                .GetResult();
            return LiteSpotifyCatalogContract.CreateSearchResult(items);
        }
        catch (Exception exception)
        {
            throw SafeRequestException(exception, LiteSpotifyCatalogContract.SearchOperation);
        }
    }

    public object ContainerItems(JsonElement args)
    {
        var request = LiteSpotifyCatalogContract.ReadContainerRequest(args);
        EnsureCatalogReady();
        try
        {
            var result = backend.GetContainerItemsAsync(request, CancellationToken.None)
                .GetAwaiter()
                .GetResult();
            return LiteSpotifyCatalogContract.CreateContainerResult(
                request,
                result.Items,
                result.Available,
                result.HasMore);
        }
        catch (Exception exception)
        {
            throw SafeRequestException(
                exception,
                LiteSpotifyCatalogContract.ContainerItemsOperation);
        }
    }

    private void EnsureCatalogReady()
    {
        LiteSpotifyAccountProbe account;
        try
        {
            account = backend.ReadAccountStatus();
        }
        catch
        {
            throw new LiteRequestException(
                LiteSpotifyCatalogContract.FailureMessage(
                    LiteSpotifyFailureReason.Unknown,
                    LiteSpotifyCatalogContract.AccountStatusOperation));
        }
        if (!account.CatalogConfigured)
        {
            throw new LiteRequestException(
                LiteSpotifyCatalogContract.FailureMessage(
                    LiteSpotifyFailureReason.NotConfigured,
                    LiteSpotifyCatalogContract.AccountStatusOperation));
        }
        if (account.CatalogConnected != true)
        {
            var reason = account.CatalogConnected == false
                ? LiteSpotifyFailureReason.NotConnected
                : LiteSpotifyFailureReason.Unknown;
            throw new LiteRequestException(
                LiteSpotifyCatalogContract.FailureMessage(
                    reason,
                    LiteSpotifyCatalogContract.AccountStatusOperation));
        }
    }

    private static LiteRequestException SafeRequestException(
        Exception exception,
        string operation) => new(SafeFailure(exception, operation));

    private static string SafeFailure(Exception exception, string operation)
    {
        var actual = exception is AggregateException aggregate
            ? aggregate.Flatten().InnerExceptions.FirstOrDefault() ?? exception
            : exception;
        var reason = actual switch
        {
            LiteSpotifyBackendException backendException => backendException.Reason,
            OperationCanceledException => LiteSpotifyFailureReason.Cancelled,
            HttpRequestException => LiteSpotifyFailureReason.Network,
            TimeoutException => LiteSpotifyFailureReason.Timeout,
            _ => LiteSpotifyFailureReason.Unknown
        };
        return LiteSpotifyCatalogContract.FailureMessage(reason, operation);
    }

    public void Dispose() => backend.Dispose();
}

internal interface ILiteSpotifyReadOnlyBackend : IDisposable
{
    IReadOnlyList<MediaItem> CachedCollection { get; }

    LiteSpotifyAccountProbe ReadAccountStatus();

    Task<LiteSpotifyCollectionRefresh> RefreshCollectionAsync(
        CancellationToken cancellationToken);

    Task<IReadOnlyList<MediaItem>> SearchAsync(
        string query,
        CancellationToken cancellationToken);

    Task<LiteSpotifyContainerBackendResult> GetContainerItemsAsync(
        LiteSpotifyContainerRequest request,
        CancellationToken cancellationToken);
}

internal sealed record LiteSpotifyCollectionRefresh(
    IReadOnlyList<MediaItem> Items,
    bool HadWarnings);

internal sealed record LiteSpotifyContainerBackendResult(
    IReadOnlyList<MediaItem> Items,
    bool Available,
    bool HasMore = false);

internal sealed class LiteSpotifyBackendException(
    LiteSpotifyFailureReason reason,
    Exception? innerException = null)
    : Exception("Spotify backend failure.", innerException)
{
    public LiteSpotifyFailureReason Reason { get; } = reason;
}
