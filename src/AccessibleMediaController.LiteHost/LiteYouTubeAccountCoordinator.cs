using System.Text.Json;
using AccessibleMediaController.Core.YouTube;
using AccessibleMediaController.LiteHost.Protocol;

namespace AccessibleMediaController.LiteHost;

internal interface ILiteYouTubeAccountBackend : IDisposable
{
    YouTubeAccountStatus GetStatus();
    Task<YouTubeAccountOperationResult> LoginAsync(CancellationToken cancellationToken);
    Task<YouTubeAccountOperationResult> LogoutAsync(CancellationToken cancellationToken);
    Task<YouTubeSubscriptionSyncPlan> PreviewAsync(
        bool restoreSuppressed,
        CancellationToken cancellationToken);
    Task<YouTubeSubscriptionSyncApplyResult> ApplyAsync(
        bool restoreSuppressed,
        CancellationToken cancellationToken);
}

/// <summary>
/// Wąska powierzchnia protokołu konta YouTube. Żaden wynik nie zawiera tokenu,
/// kodu, identyfikatora klienta, identyfikatora konta ani technicznego ID kanału.
/// </summary>
internal sealed class LiteYouTubeAccountCoordinator(
    ILiteYouTubeAccountBackend backend) : IDisposable
{
    private static readonly HashSet<string> SafeBackendMessages = new(StringComparer.Ordinal)
    {
        "Najpierw zaloguj się do YouTube.",
        "Najpierw sprawdź aktualne subskrypcje YouTube i zatwierdź ten sam zakres zmian.",
        "Logowanie YouTube straciło ważność. Zaloguj się ponownie.",
        "Kod lub zapisane logowanie YouTube straciło ważność. Zaloguj się ponownie.",
        "To konto Google nie ma jeszcze kanału YouTube.",
        "Wyczerpano dzienny limit YouTube. Spróbuj później.",
        "YouTube chwilowo ograniczył liczbę żądań. Spróbuj później.",
        "YouTube odmówił dostępu do subskrypcji tego konta.",
        "Nie udało się pobrać subskrypcji YouTube.",
        "Lista subskrypcji YouTube jest zbyt duża, aby bezpiecznie pobrać ją w jednym przebiegu.",
        "YouTube zwrócił powtarzającą się stronę subskrypcji.",
        "YouTube zwrócił nieprawidłowy znacznik strony subskrypcji.",
        "YouTube zwrócił nieczytelną listę subskrypcji.",
        "Google zwrócił niepełne dane logowania YouTube.",
        "Google zwrócił nieczytelną odpowiedź logowania YouTube.",
        "Ta wersja AMC nie ma prawidłowo skonfigurowanego logowania YouTube.",
        "Logowanie YouTube zostało anulowane na stronie Google.",
        "Google chwilowo ograniczył liczbę prób logowania YouTube. Spróbuj później.",
        "Google odrzucił logowanie YouTube. Spróbuj zalogować się ponownie.",
        "Nie udało się połączyć z usługą logowania YouTube.",
        "Biblioteka zawiera sprzeczny rekord kanału YouTube. Nie zapisano synchronizacji.",
        "Biblioteka zmieniła się przed przywróceniem kanału YouTube. Nie zapisano synchronizacji."
    };

    private readonly ILiteYouTubeAccountBackend _backend = backend
        ?? throw new ArgumentNullException(nameof(backend));
    private readonly object _loginGate = new();
    private CancellationTokenSource? _loginCancellation;

    internal IReadOnlyDictionary<string, Func<LiteRequest, LiteEventSink, object?>> Handlers() =>
        new Dictionary<string, Func<LiteRequest, LiteEventSink, object?>>(StringComparer.Ordinal)
        {
            [LiteYouTubeAccountContract.CapabilitiesOperation] = (_, _) =>
                new LiteYouTubeAccountCapabilities(
                    true,
                    true,
                    true,
                    "Konto YouTube jest dostępne tylko do odczytu."),
            [LiteYouTubeAccountContract.StatusOperation] = (_, _) => Status(),
            [LiteYouTubeAccountContract.LoginOperation] = (_, _) => Login(),
            [LiteYouTubeAccountContract.CancelLoginOperation] = (_, _) => CancelLogin(),
            [LiteYouTubeAccountContract.LogoutOperation] = (_, _) => Logout(),
            [LiteYouTubeAccountContract.SyncPreviewOperation] = (request, _) =>
                Preview(request.Args),
            [LiteYouTubeAccountContract.SyncApplyOperation] = (request, _) =>
                Apply(request.Args)
        };

    private object Status()
    {
        try
        {
            var status = _backend.GetStatus();
            return new LiteYouTubeAccountState(status.Connected, status.Message);
        }
        catch
        {
            return new LiteYouTubeAccountState(
                false,
                "Nie można teraz sprawdzić logowania YouTube.");
        }
    }

    private object Login()
    {
        CancellationTokenSource cancellation;
        lock (_loginGate)
        {
            if (_loginCancellation is not null)
                return new LiteYouTubeAccountActionResult(
                    false,
                    "Logowanie YouTube już trwa.");
            cancellation = new CancellationTokenSource();
            _loginCancellation = cancellation;
        }
        try
        {
            var result = _backend.LoginAsync(cancellation.Token)
                .GetAwaiter().GetResult();
            return new LiteYouTubeAccountActionResult(result.Succeeded, result.Message);
        }
        catch (OperationCanceledException) when (cancellation.IsCancellationRequested)
        {
            return new LiteYouTubeAccountActionResult(
                false,
                "Anulowano oczekiwanie na logowanie YouTube.");
        }
        catch (Exception exception)
        {
            throw SafeFailure(exception, "Nie udało się zalogować do YouTube.");
        }
        finally
        {
            lock (_loginGate)
            {
                if (ReferenceEquals(_loginCancellation, cancellation))
                    _loginCancellation = null;
            }
            cancellation.Dispose();
        }
    }

    private object CancelLogin()
    {
        CancellationTokenSource? cancellation;
        lock (_loginGate)
            cancellation = _loginCancellation;
        if (cancellation is null)
            return new LiteYouTubeAccountActionResult(
                false,
                "Logowanie YouTube nie jest teraz aktywne.");
        cancellation.Cancel();
        return new LiteYouTubeAccountActionResult(
            true,
            "Anulowano oczekiwanie na logowanie YouTube.");
    }

    private object Logout()
    {
        try
        {
            var result = _backend.LogoutAsync(CancellationToken.None)
                .GetAwaiter().GetResult();
            return new LiteYouTubeAccountActionResult(result.Succeeded, result.Message);
        }
        catch (Exception exception)
        {
            throw SafeFailure(exception, "Nie udało się wylogować z YouTube.");
        }
    }

    private object Preview(JsonElement args)
    {
        var restore = LiteYouTubeAccountContract.ReadRestoreSuppressed(args);
        try
        {
            var plan = _backend.PreviewAsync(restore, CancellationToken.None)
                .GetAwaiter().GetResult();
            return LiteYouTubeAccountContract.CreatePreview(plan);
        }
        catch (Exception exception)
        {
            throw SafeFailure(exception, "Nie udało się sprawdzić subskrypcji YouTube.");
        }
    }

    private object Apply(JsonElement args)
    {
        var restore = LiteYouTubeAccountContract.ReadRestoreSuppressed(args);
        try
        {
            var result = _backend.ApplyAsync(restore, CancellationToken.None)
                .GetAwaiter().GetResult();
            return LiteYouTubeAccountContract.CreateApply(result);
        }
        catch (Exception exception)
        {
            throw SafeFailure(exception, "Nie udało się zapisać subskrypcji YouTube.");
        }
    }

    private static LiteRequestException SafeFailure(Exception exception, string fallback)
    {
        if (exception is InvalidOperationException or InvalidDataException
            && SafeBackendMessages.Contains(exception.Message))
            return new LiteRequestException(exception.Message);
        if (exception is TimeoutException or OperationCanceledException)
            return new LiteRequestException("YouTube nie odpowiedział w bezpiecznym czasie.");
        if (exception is HttpRequestException)
            return new LiteRequestException("Nie udało się połączyć z YouTube.");
        return new LiteRequestException(fallback);
    }

    public void Dispose()
    {
        lock (_loginGate)
            _loginCancellation?.Cancel();
        _backend.Dispose();
    }
}
