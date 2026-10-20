namespace AccessibleMediaController.Core.Sonos;

/// <summary>
/// Publiczna konfiguracja integracji Sonos współdzielona przez główne AMC i
/// bezokienny host wxPython. Klucz Control API identyfikuje aplikację i nie
/// jest sekretem; tokeny użytkownika nadal pozostają wyłącznie w magazynie
/// DPAPI bieżącego użytkownika Windows.
/// </summary>
public static class SonosIntegrationDefaults
{
    /// <summary>
    /// Bezpieczny, nieroutowalny placeholder wymagany przez kontrakt magazynu.
    /// Nie jest celem sieciowym: <see cref="BrokerAvailable"/> blokuje operacje
    /// przed utworzeniem klienta HTTP. Prawdziwy adres wolno wprowadzić dopiero
    /// razem z działającą publiczną usługą i odbiorem integracji Sonos.
    /// </summary>
    public const string BrokerOrigin = "https://sonos-login-not-configured.invalid/";

    public const bool BrokerAvailable = false;

    public const string BrokerUnavailableMessage =
        "Publiczna usługa logowania Sonos nie jest jeszcze skonfigurowana w tej wersji AMC.";

    public const string ControlApiKey = "b051a8f0-499c-4deb-9f66-843a752c36e4";
}
