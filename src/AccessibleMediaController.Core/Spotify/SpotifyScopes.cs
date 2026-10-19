namespace AccessibleMediaController.Core.Spotify;

/// <summary>
/// Zakresy uprawnień Spotify, o które prosi AMC.
///
/// Rozdzielone celowo na trzy grupy, bo mają różne uzasadnienie wobec
/// użytkownika i różne skutki przy odmowie:
///
/// PLAYBACK - bez nich wbudowany odtwarzacz (Web Playback SDK) nie wstanie
/// w ogóle. "streaming" wymaga konta Premium; "user-read-email" oraz
/// "user-read-private" są wymagane przez sam SDK do potwierdzenia rodzaju
/// konta, nie przez AMC do czegokolwiek innego.
///
/// LIBRARY - czytanie kolekcji. Brak tych zakresów daje puste listy, ale
/// odtwarzanie działa.
///
/// CONTROL - sterowanie i stan odtwarzania przez Web API (przenoszenie
/// odtwarzania na urządzenie AMC, czytanie co gra). Bez nich zostaje
/// sterowanie wyłącznie wewnątrz SDK.
///
/// MEMBERSHIP - zapis do biblioteki konta: Ulubione (Ctrl+Shift+U), Biblioteka
/// (Ctrl+Shift+L) i usuwanie z kolekcji (Delete). Spotify od 2026 obsługuje to
/// jednym punktem "/me/library", który dla utworów i albumów wymaga
/// "user-library-modify", a dla obserwowanych wykonawców "user-follow-modify".
///
/// PLAYLISTS - tworzenie natywnych playlist Spotify i dodawanie do nich
/// utworów lub odcinków. Oba zakresy są jawne, bo AMC pozwala wybrać playlistę
/// prywatną albo publiczną. Starsze logowanie bez tych zakresów pozostaje
/// ważne do odczytu i odtwarzania, ale przed zapisem wymaga ponownej zgody.
/// </summary>
public static class SpotifyScopes
{
    public static readonly string[] Playback =
    [
        "streaming",
        "user-read-email",
        "user-read-private"
    ];

    public static readonly string[] Library =
    [
        "user-library-read",
        "user-follow-read",
        "playlist-read-private",
        "playlist-read-collaborative"
    ];

    public static readonly string[] Control =
    [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing"
    ];

    /// <summary>
    /// Zapis do biblioteki konta. Tylko te dwa: "user-library-modify" obsługuje
    /// utwory, albumy, odcinki, podcasty i audiobooki, "user-follow-modify"
    /// obserwowanych wykonawców. Zakresy playlist są niżej osobną grupą,
    /// ponieważ nie dotyczą przynależności do Biblioteki ani Ulubionych.
    /// </summary>
    public static readonly string[] Membership =
    [
        "user-library-modify",
        "user-follow-modify"
    ];

    public static readonly string[] Playlists =
    [
        "playlist-modify-private",
        "playlist-modify-public"
    ];

    /// <summary>Pełny zestaw w kolejności grup, rozdzielony spacjami.</summary>
    public static string Requested { get; } =
        string.Join(' ', Playback.Concat(Library).Concat(Control).Concat(Membership).Concat(Playlists));

    /// <summary>
    /// Czy przyznany zakres pozwala uruchomić wbudowany odtwarzacz.
    /// Spotify potrafi przyznać część zakresów, a "streaming" pomija dla
    /// konta bez Premium - wtedy trzeba to powiedzieć wprost, zamiast
    /// pokazywać odtwarzacz, który nigdy nie zagra.
    /// </summary>
    public static bool AllowsPlayback(string? grantedScope) =>
        Contains(grantedScope, "streaming");

    public static bool AllowsLibrary(string? grantedScope) =>
        Contains(grantedScope, "user-library-read");

    public static bool AllowsRemoteControl(string? grantedScope) =>
        Contains(grantedScope, "user-modify-playback-state");

    /// <summary>
    /// Czy przyznany zakres pozwala ZAPISAĆ pozycję w bibliotece konta.
    /// Rozdzielone po rodzaju pozycji, bo Spotify potrafi przyznać jeden zakres
    /// bez drugiego, a wtedy część skrótów działa, a część nie. Ogłoszenie
    /// sukcesu bez odpowiedniego zakresu byłoby kłamstwem wobec użytkownika:
    /// pozycja nie znalazłaby się w koncie.
    /// </summary>
    public static bool AllowsLibraryWrite(string? grantedScope) =>
        Contains(grantedScope, "user-library-modify");

    public static bool AllowsFollowWrite(string? grantedScope) =>
        Contains(grantedScope, "user-follow-modify");

    public static bool AllowsPlaylistWrite(string? grantedScope, bool isPublic) =>
        Contains(
            grantedScope,
            isPublic ? "playlist-modify-public" : "playlist-modify-private");

    public static IReadOnlyList<string> MissingPlaylistScopes(string? grantedScope)
    {
        var granted = Split(grantedScope);
        return Playlists
            .Where(scope => !granted.Contains(scope, StringComparer.Ordinal))
            .ToArray();
    }

    /// <summary>
    /// Zakres wymagany do zapisu dla danego typu adresu URI Spotify
    /// ("track", "album", "artist", ...). Null oznacza typ, którego AMC nie
    /// zapisuje (playlisty do czasu wprowadzenia funkcji zmiany playlist).
    /// </summary>
    public static string? WriteScopeForUriType(string? uriType) => uriType switch
    {
        "track" or "album" or "episode" or "show" or "audiobook" => "user-library-modify",
        "artist" or "user" => "user-follow-modify",
        _ => null
    };

    public static bool AllowsWriteForUriType(string? grantedScope, string? uriType) =>
        WriteScopeForUriType(uriType) is { } scope && Contains(grantedScope, scope);

    /// <summary>
    /// Zakresy zapisu, których brakuje w przyznanej liście. Pusta lista znaczy,
    /// że ponowne logowanie nie jest potrzebne.
    /// </summary>
    public static IReadOnlyList<string> MissingMembershipScopes(string? grantedScope)
    {
        var granted = Split(grantedScope);
        return Membership
            .Where(scope => !granted.Contains(scope, StringComparer.Ordinal))
            .ToArray();
    }

    public static IReadOnlyList<string> Missing(string? grantedScope)
    {
        var granted = Split(grantedScope);
        return Split(Requested)
            .Where(scope => !granted.Contains(scope, StringComparer.Ordinal))
            .ToArray();
    }

    private static bool Contains(string? scope, string expected) =>
        Split(scope).Contains(expected, StringComparer.Ordinal);

    private static string[] Split(string? scope) =>
        string.IsNullOrWhiteSpace(scope)
            ? []
            : scope.Split(' ', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}
