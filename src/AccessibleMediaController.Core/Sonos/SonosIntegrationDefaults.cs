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
    /// Stały publiczny origin wspólnego brokera AMC. Sekret integracji pozostaje
    /// wyłącznie na serwerze; klient zna tylko origin i publiczny klucz Control API.
    /// </summary>
    public const string BrokerOrigin = "https://sonos.stareaudycje.pl/";

    public const bool BrokerAvailable = true;

    public const string BrokerUnavailableMessage =
        "Publiczna usługa logowania Sonos nie jest jeszcze skonfigurowana w tej wersji AMC.";

    public const string ControlApiKey = "b051a8f0-499c-4deb-9f66-843a752c36e4";
}
