using System.Text.Json;
using AccessibleMediaController.Core.Configuration;
using AccessibleMediaController.Core.YouTube;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost.ProtocolTests;

internal static class YouTubeAccountContractTests
{
    internal static void Run()
    {
        AccountSurfaceNeverReturnsSecretsOrTechnicalIds();
        PreviewAndApplyRemainSeparateExplicitOperations();
        RestoreChoiceMustBeBoolean();
        BackendFailuresAreRedacted();
        KnownQuotaFailureRemainsSpecific();
        ActiveLoginCanBeCancelledWithoutLeakingTechnicalData();
        Console.WriteLine("OK: bezpieczny kontrakt konta YouTube (6 scenariuszy)");
    }

    private static void AccountSurfaceNeverReturnsSecretsOrTechnicalIds()
    {
        using var backend = new FakeBackend();
        using var coordinator = new LiteYouTubeAccountCoordinator(backend);
        var capabilities = Invoke(
            coordinator,
            LiteYouTubeAccountContract.CapabilitiesOperation);
        var status = Invoke(coordinator, LiteYouTubeAccountContract.StatusOperation);
        var login = Invoke(coordinator, LiteYouTubeAccountContract.LoginOperation);
        var logout = Invoke(coordinator, LiteYouTubeAccountContract.LogoutOperation);
        var json = LiteJson.Serialize(new[] { capabilities, status, login, logout });

        Check(backend.LoginCalls == 1 && backend.LogoutCalls == 1,
            "Jawne operacje konta nie dotarły dokładnie raz do właściciela tokenu.");
        Check(!json.Contains("tajny-token", StringComparison.Ordinal)
              && !json.Contains("refresh", StringComparison.OrdinalIgnoreCase)
              && !json.Contains("clientId", StringComparison.OrdinalIgnoreCase),
            "Dane logowania albo identyfikator klienta wyszły przez protokół.");
        Check(json.Contains("tylko do odczytu", StringComparison.Ordinal),
            "Możliwości nie opisują uczciwie zakresu konta.");
    }

    private static void PreviewAndApplyRemainSeparateExplicitOperations()
    {
        using var backend = new FakeBackend
        {
            Preview = new YouTubeSubscriptionSyncPlan(
                [
                    new YouTubeSubscriptionSyncAction(
                        YouTubeSubscriptionSyncActionKind.Add,
                        "UC-TECHNICZNY",
                        "  Kanał\r\npróby  ",
                        new Uri("https://www.youtube.com/channel/UC-TECHNICZNY/videos"),
                        null)
                ],
                AlreadyPresent: 2,
                Suppressed: 1,
                Duplicates: 0,
                Invalid: 0),
            Applied = new YouTubeSubscriptionSyncApplyResult(
                Added: 1,
                Restored: 0,
                AlreadyPresent: 2,
                Suppressed: 1,
                Duplicates: 0,
                Invalid: 0)
        };
        using var coordinator = new LiteYouTubeAccountCoordinator(backend);
        using var args = JsonDocument.Parse("""{"restoreSuppressed":false}""");

        var preview = Invoke(
            coordinator,
            LiteYouTubeAccountContract.SyncPreviewOperation,
            args.RootElement);
        Check(backend.PreviewCalls == 1 && backend.ApplyCalls == 0,
            "Podgląd sam zapisał synchronizację.");
        var previewJson = LiteJson.Serialize(preview);
        Check(previewJson.Contains("Kanał", StringComparison.Ordinal)
              && !previewJson.Contains("\\r", StringComparison.Ordinal)
              && !previewJson.Contains("\\n", StringComparison.Ordinal)
              && !previewJson.Contains("UC-TECHNICZNY", StringComparison.Ordinal)
              && !previewJson.Contains("youtube.com", StringComparison.OrdinalIgnoreCase),
            "Podgląd ujawnił techniczny identyfikator albo adres kanału.");

        var applied = Invoke(
            coordinator,
            LiteYouTubeAccountContract.SyncApplyOperation,
            args.RootElement);
        Check(backend.ApplyCalls == 1
              && applied is LiteYouTubeSyncApplyResult result
              && result.Added == 1,
            "Jawne zatwierdzenie nie wykonało osobnej operacji zapisu.");
    }

    private static void RestoreChoiceMustBeBoolean()
    {
        using var invalid = JsonDocument.Parse("""{"restoreSuppressed":"tak"}""");
        try
        {
            _ = LiteYouTubeAccountContract.ReadRestoreSuppressed(invalid.RootElement);
            throw new InvalidOperationException("Tekstowy wybór przywracania został zaakceptowany.");
        }
        catch (LiteRequestException exception)
        {
            Check(exception.Message.Contains("tak albo nie", StringComparison.Ordinal),
                "Odmowa nie ma użytkowego opisu.");
        }
    }

    private static void BackendFailuresAreRedacted()
    {
        const string secret = "Bearer tajny-token kod=sekret";
        using var backend = new FakeBackend
        {
            Failure = new InvalidOperationException(secret)
        };
        using var coordinator = new LiteYouTubeAccountCoordinator(backend);
        try
        {
            _ = Invoke(coordinator, LiteYouTubeAccountContract.SyncPreviewOperation);
            throw new InvalidOperationException("Awaria backendu nie została zgłoszona.");
        }
        catch (LiteRequestException exception)
        {
            Check(!exception.Message.Contains(secret, StringComparison.Ordinal)
                  && exception.Message == "Nie udało się sprawdzić subskrypcji YouTube.",
                "Surowy błąd backendu wyszedł przez protokół.");
        }
    }

    private static void KnownQuotaFailureRemainsSpecific()
    {
        const string message = "Wyczerpano dzienny limit YouTube. Spróbuj później.";
        using var backend = new FakeBackend
        {
            Failure = new InvalidOperationException(message)
        };
        using var coordinator = new LiteYouTubeAccountCoordinator(backend);
        try
        {
            _ = Invoke(coordinator, LiteYouTubeAccountContract.SyncPreviewOperation);
            throw new InvalidOperationException("Błąd limitu nie został zgłoszony.");
        }
        catch (LiteRequestException exception)
        {
            Check(exception.Message == message,
                "Znany bezpieczny błąd limitu został zastąpiony ogólnym komunikatem.");
        }
    }

    private static void ActiveLoginCanBeCancelledWithoutLeakingTechnicalData()
    {
        using var backend = new FakeBackend { WaitForCancellation = true };
        using var coordinator = new LiteYouTubeAccountCoordinator(backend);
        var login = Task.Run(() => Invoke(
            coordinator,
            LiteYouTubeAccountContract.LoginOperation));
        Check(backend.LoginStarted.Wait(TimeSpan.FromSeconds(2)),
            "Testowe logowanie nie rozpoczęło oczekiwania.");

        var cancelled = Invoke(
            coordinator,
            LiteYouTubeAccountContract.CancelLoginOperation);
        Check(login.Wait(TimeSpan.FromSeconds(2)),
            "Anulowane logowanie nie zakończyło oczekiwania.");
        var json = LiteJson.Serialize(new[] { cancelled, login.Result });
        Check(json.Contains("Anulowano oczekiwanie", StringComparison.Ordinal)
              && !json.Contains("CancellationToken", StringComparison.Ordinal)
              && !json.Contains("TaskCanceled", StringComparison.Ordinal),
            "Anulowanie ujawniło techniczny stan albo nie ma użytkowego opisu.");
    }

    private static object Invoke(
        LiteYouTubeAccountCoordinator coordinator,
        string operation,
        JsonElement args = default)
    {
        var handler = coordinator.Handlers()[operation];
        return handler(
            new LiteRequest { Id = "test", Op = operation, Args = args },
            new LiteEventSink(_ => { }))!;
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private sealed class FakeBackend : ILiteYouTubeAccountBackend
    {
        internal int LoginCalls { get; private set; }
        internal int LogoutCalls { get; private set; }
        internal int PreviewCalls { get; private set; }
        internal int ApplyCalls { get; private set; }
        internal Exception? Failure { get; init; }
        internal bool WaitForCancellation { get; init; }
        internal ManualResetEventSlim LoginStarted { get; } = new(false);
        internal YouTubeSubscriptionSyncPlan Preview { get; init; } = new([], 0, 0, 0, 0);
        internal YouTubeSubscriptionSyncApplyResult Applied { get; init; } = new(0, 0, 0, 0, 0, 0);

        public YouTubeAccountStatus GetStatus() =>
            new(true, "YouTube: zalogowano", DateTimeOffset.UtcNow.AddHours(1));

        public Task<YouTubeAccountOperationResult> LoginAsync(CancellationToken cancellationToken)
        {
            LoginCalls++;
            LoginStarted.Set();
            if (WaitForCancellation)
                return Task.Delay(Timeout.InfiniteTimeSpan, cancellationToken)
                    .ContinueWith<YouTubeAccountOperationResult>(
                        _ => throw new OperationCanceledException(cancellationToken),
                        CancellationToken.None,
                        TaskContinuationOptions.ExecuteSynchronously,
                        TaskScheduler.Default);
            return Task.FromResult(new YouTubeAccountOperationResult(true, "Zalogowano do YouTube."));
        }

        public Task<YouTubeAccountOperationResult> LogoutAsync(CancellationToken cancellationToken)
        {
            LogoutCalls++;
            return Task.FromResult(new YouTubeAccountOperationResult(true, "Wylogowano z YouTube."));
        }

        public Task<YouTubeSubscriptionSyncPlan> PreviewAsync(
            bool restoreSuppressed,
            CancellationToken cancellationToken)
        {
            PreviewCalls++;
            if (Failure is not null) throw Failure;
            return Task.FromResult(Preview);
        }

        public Task<YouTubeSubscriptionSyncApplyResult> ApplyAsync(
            bool restoreSuppressed,
            CancellationToken cancellationToken)
        {
            ApplyCalls++;
            if (Failure is not null) throw Failure;
            return Task.FromResult(Applied);
        }

        public void Dispose()
        {
            LoginStarted.Dispose();
        }
    }
}
