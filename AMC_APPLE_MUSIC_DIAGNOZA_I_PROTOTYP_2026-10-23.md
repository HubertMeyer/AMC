# AMC i Apple Music — diagnoza oraz prototyp, 23.10.2026

## Aktualizacja po wdrożeniu interfejsu, 23.10.2026

Ta aktualizacja zastępuje wcześniejsze zdanie w sekcji „Prototyp w kodzie”, że
nie ma jeszcze okna konta, magazynu tokenów, hosta MusicKit ani rzeczywistej
drogi odtwarzania.

W AMC Test są już:

- dostępne okno „Konto Apple Music” pod Ctrl+F5 w sesji Apple Music;
- developer token i Music User Token przechowywane wyłącznie w Menedżerze
  poświadczeń Windows;
- oficjalne logowanie MusicKit on the Web w osobnym, widocznym oknie;
- ukryty przed fokusem i NVDA host WebView2 jako silnik odtwarzania;
- stronicowane pobieranie biblioteki, wyszukiwanie Ctrl+F oraz wyszukiwanie
  globalne;
- otwieranie albumów, playlist i wykonawców Enterem;
- prawa strzałka z albumami, utworami, podobnymi wykonawcami oraz powiązanym
  albumem albo wykonawcą;
- odtwarzanie utworów i teledysków przez MusicKit;
- realne dodawanie do biblioteki i ulubionych. Dla próby usunięcia AMC mówi
  wprost o ograniczeniu API;
- generator developer tokenu i osobna instrukcja dla osoby z rolą Apple
  Developer Account Holder albo Admin.

Wciąż nie jest potwierdzone logowanie i chronione odtwarzanie na prawdziwym
koncie. To ograniczenie środowiska testowego, nie wynik testu syntetycznego:
zgodność DRM WebView2 musi zostać sprawdzona przez użytkownika z aktywną
subskrypcją Apple Music.

## Wniosek

Apple Music może działać w AMC bez przekazywania każdego utworu do zewnętrznej
aplikacji Apple Music. Oficjalna droga dla Windows to Apple Music API do danych
oraz MusicKit on the Web do logowania użytkownika i pełnego odtwarzania w
izolowanym WebView2. Widoczny interfejs nadal może być w pełni natywny i
dostępny; host webowy jest wyłącznie silnikiem konta i dźwięku.

Nie należy automatyzować strony music.apple.com ani przechwytywać jej DRM.
Nie należy też umieszczać prywatnego klucza `.p8` w repozytorium lub instalatorze.

## Warunki pierwszego uruchomienia

1. Właściciel aplikacji AMC potrzebuje konta Apple Developer z Media ID i
   kluczem Media Services.
2. Z klucza powstaje podpisany developer token JWT. Token może być ważny
   najwyżej sześć miesięcy. Klucz prywatny pozostaje poza klientem.
3. MusicKit on the Web pokazuje oficjalne logowanie Apple i uzyskuje Music User
   Token dla konkretnego użytkownika i urządzenia. Użytkownik końcowy nie
   wkleja własnego tokenu.
4. Docelowo AMC powinien pobierać krótko ważny developer token z małej usługi
   AMC. Prototyp przyjmuje gotowy token w pamięci; nie zapisuje klucza `.p8`.

## Potwierdzone możliwości oficjalnego API

| Funkcja | Stan | Uwagi dla AMC |
|---|---|---|
| katalog, wyszukiwanie | tak | utwory, albumy, wykonawcy, playlisty, teledyski |
| biblioteka użytkownika | tak | wymaga Music User Token |
| album → utwory | tak | bez zmiany interfejsu AMC |
| wykonawca → albumy, utwory, podobni | tak | views: `full-albums`, `top-songs`, `similar-artists` |
| playlista → utwory | tak | katalogowa i biblioteczna |
| dodaj do biblioteki | tak | odpowiedź 202 może być asynchroniczna |
| usuń z biblioteki | brak publicznego endpointu | Ctrl+Shift+L nie może udawać pełnego przełącznika |
| dodaj do ulubionych | tak | oficjalny endpoint Favorites |
| usuń z ulubionych | brak publicznego endpointu | kasowanie dawnego ratingu nie jest tym samym |
| utwórz playlistę | tak | biblioteczna playlista użytkownika |
| dodaj utwory do playlisty | tak | tylko playlista z `canEdit=true` |
| usuń / przestaw utwory playlisty | brak w publicznym API | polecenia ukryć lub opisać jako niedostępne |
| pełne odtwarzanie w AMC | tak, MusicKit on the Web | wymaga ważnych tokenów i zgody użytkownika |

## Prototyp w kodzie

- `AppleMusicApiClient` obsługuje wyszukiwanie katalogu, pierwszy odczyt
  biblioteki, otwieranie albumu/playlisty/wykonawcy, dodanie do biblioteki i
  Favorites, utworzenie playlisty i dopisanie utworów.
- `AppleMusicCapabilities` jest jednym źródłem prawdy o tym, których poleceń
  wolno użyć. W szczególności nie reklamuje operacji DELETE, których Apple nie
  udostępnia.
- Model oddziela identyfikatory techniczne od etykiet mówionych przez NVDA.
- Testy używają wyłącznie syntetycznego `HttpMessageHandler`; nie wysyłają
  danych do Apple i nie wymagają konta.

Ten akapit opisuje stan pierwszego przyrostu i został zastąpiony przez
„Aktualizację po wdrożeniu interfejsu” na początku dokumentu. Nadal nie
uruchamiano logowania z prawdziwym Apple ID.

## Następny bezpieczny przyrost

1. Przekazać osobie z rolą Apple Developer plik
   `INSTRUKCJA_PRZYGOTOWANIA_APPLE_MUSIC_PL.md`.
2. W AMC Test wkleić wyłącznie gotowy JWT, zalogować konto użytkownika i pobrać
   bibliotekę.
3. Sprawdzić ręcznie z NVDA: pierwsze logowanie, ponowne otwarcie, strzałki,
   Enter, Escape, menu kontekstowe, powrót fokusu, wygaśnięcie obu tokenów i brak
   subskrypcji.
4. Potwierdzić pełne odtwarzanie DRM, pauzę, przewijanie, głośność, automatyczny
   następny utwór i zachowanie po uśpieniu komputera.
5. Dopiero po tych wynikach rozważyć usługę wydającą krótkotrwałe developer
   tokeny użytkownikom końcowym. Prywatny klucz nadal nie może trafić do klienta.

## Źródła Apple sprawdzone 23.10.2026

- https://developer.apple.com/musickit/
- https://developer.apple.com/documentation/applemusicapi/
- https://developer.apple.com/documentation/applemusicapi/user-authentication-for-musickit
- https://developer.apple.com/documentation/applemusicapi/generating-developer-tokens
- https://developer.apple.com/documentation/applemusicapi/handling-resource-representation-and-relationships
- https://developer.apple.com/documentation/applemusicapi/add-a-resource-to-a-library
- https://developer.apple.com/documentation/applemusicapi/add-resource-to-favorites
- https://developer.apple.com/documentation/applemusicapi/create-a-new-library-playlist
- https://developer.apple.com/documentation/applemusicapi/add-tracks-to-a-library-playlist

## Stan weryfikacji

- zmiany źródłowe: wykonane;
- test celowany: `dotnet run --project tests/AccessibleMediaController.Core.SmokeTests --configuration Release --no-restore -- --apple-music-prototype` — kod 0, `Apple Music prototype: OK`;
- cały zestaw Core: `dotnet run --project tests/AccessibleMediaController.Core.SmokeTests --configuration Release --no-build --no-restore --disable-build-servers` — kod 0;
- pełny build: `dotnet build AccessibleMediaController.sln --configuration Release --no-restore --disable-build-servers -m:1` — kod 0, 0 ostrzeżeń, 0 błędów;
- instalacja: nie wykonano;
- prawdziwe konto i odtwarzanie: nie wykonano;
- wersja źródeł: `0.1.0-alpha.424`;
- punkt wyjścia Git: `16dce37`; bez nowego commitu w tym zadaniu.

### Stan po aktualizacji interfejsu

- zmiany źródłowe: wykonane;
- kompilacja Windows Debug: kod 0, 0 ostrzeżeń, 0 błędów;
- test modelu API:
  `dotnet run --project tests/AccessibleMediaController.Core.SmokeTests --no-build -- --apple-music-prototype`
  — kod 0, `Apple Music prototype: OK`;
- test dostępnego interfejsu:
  `dotnet run --project tests/AccessibleMediaController.Windows.SmokeTests --no-build -- --apple-music-ui`
  — kod 0;
- generator JWT: sprawdzony na jednorazowym kluczu nistP256; utworzył
  trzyczęściowy JWT z 64-bajtowym podpisem ES256; klucz i token testowy usunięto;
- instalacja AMC Test: jeszcze nie wykonano;
- prawdziwe konto, subskrypcja i DRM: jeszcze nie sprawdzono;
- wydanie publiczne: nie wykonano i nie jest dozwolone na tym etapie;
- wersja przed następnym pakietem testowym: `0.1.0-alpha.424`;
- commit: jeszcze nie utworzono.

### Aktualizacja po zbudowaniu pakietu 0.1.0-alpha.425 — 23.10.2026

Ten punkt zastępuje wcześniejsze wpisy „instalacja nie wykonana” i „wersja
przed następnym pakietem 0.1.0-alpha.424”.

- rozwiązanie Release: kod 0, 0 ostrzeżeń, 0 błędów;
- pełny zestaw Core Release: kod 0;
- `--apple-music-prototype` i `--apple-music-ui`: kod 0;
- pakiet zawiera `apple-music-player/index.html` i `bridge.js`;
- AMC Test `0.1.0-alpha.425` zainstalowano kodem 0 w
  `C:\Users\micha\AppData\Local\Programs\AMC`;
- zainstalowany program ma ProductVersion `0.1.0-alpha.425` i sumę identyczną z
  programem w pakiecie;
- programu po instalacji nie uruchamiano automatycznie;
- prawdziwe konto Apple, subskrypcja i DRM nadal nie zostały sprawdzone;
- wydania publicznego i commitu nadal nie wykonano.
