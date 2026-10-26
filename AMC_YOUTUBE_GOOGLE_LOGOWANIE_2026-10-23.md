# AMC Test — logowanie Google/YouTube, 2026-10-23

## Zachowanie użytkowe

- W sesji **Podcasty i YouTube** `Ctrl+F5` otwiera **Konto YouTube i import z
  Google**.
- Logowanie używa oficjalnej strony Google w zwykłej przeglądarce, losowego
  lokalnego portu, `state` i PKCE S256.
- Zakres dostępu jest tylko do odczytu: `youtube.readonly`.
- AMC pobiera stronicowane listy subskrypcji, własnych playlist i do 100
  materiałów z każdej playlisty.
- Kanały są uzupełniane z publicznego feedu Atom YouTube, do 15 najnowszych
  materiałów. Import jest równoległy najwyżej dla czterech feedów.
- Import scala dane z istniejącą Biblioteką. Nie usuwa źródeł już zapisanych.
- `Ctrl+Windows+F5` z wtyczki NVDA i pozycja w menu Plik nadal odświeżają
  wszystkie podcasty, kanały i playlisty.

## Dostępność i komunikaty

- Polecenie, menu, paleta, pomoc klawiatury i rzeczywisty routing korzystają z
  jednego identyfikatora `ManageYouTubeConnection`.
- Client ID, przyciski, status konta i akcja importu mają jawne etykiety UI
  Automation. Do NVDA nie trafiają typy kontrolek, nazwy rekordów ani tokeny.
- Po zapisie fokus przechodzi do logowania, po logowaniu i imporcie wraca na
  odpowiedni przycisk, a po błędzie na kontrolkę wymagającą poprawy.
- Okno mówi wprost, że Data API nie jest mechanizmem autoryzacji odtwarzacza i
  nie omija ograniczeń YouTube.

## Bezpieczeństwo

- Do AMC wpisuje się publiczny Client ID aplikacji desktopowej. Sekret klienta
  nie jest potrzebny.
- Client ID i tokeny są przechowywane w Menedżerze poświadczeń Windows, pod
  osobnym celem `AccessibleMediaController/YouTubeGoogle`.
- Token dostępu jest wysyłany wyłącznie w nagłówku `Authorization: Bearer`.
- Hasło, ciasteczka, plik `client_secret*.json` i tokeny nie trafiają do
  konfiguracji AMC, kopii ustawień ani dziennika.

## Testy i rzeczywiste wyniki

- `dotnet build` projektu Windows, Debug, bez przywracania pakietów: **zaliczone,
  0 ostrzeżeń, 0 błędów**.
- Nowy zestaw `--youtube-google-ui`: **zaliczony**. Sprawdza adres OAuth i PKCE,
  brak sekretu, zakres tylko do odczytu, stronicowanie subskrypcji i playlist,
  token poza adresem URL, menu, paletę, pomoc, Ctrl+F5 oraz etykiety NVDA.
- Test korzysta z kontrolowanego serwera zastępczego. Nie otwiera przeglądarki
  i nie używa prawdziwego konta.

## Ograniczenia i dalsza próba

- Prawdziwe logowanie, ekran zgody, odświeżenie tokenu po czasie oraz import
  dużego rzeczywistego konta wymagają Client ID i ręcznej próby użytkownika.
- Prywatna playlista może być widoczna dzięki API, lecz prywatny lub inaczej
  zablokowany film może nie zagrać w istniejącym torze `yt-dlp`.
- Dla publicznego wydania Google może wymagać weryfikacji ekranu zgody i
  zakresu YouTube. Obecna praca pozostaje wyłącznie w profilu AMC Test.

## Wersja i commit

- Wspólny pakiet AMC Test: `0.1.0-alpha.425`; instalacja zakończona kodem 0,
  a suma zainstalowanego programu jest identyczna z sumą programu w pakiecie.
- Prawdziwego logowania Google i importu nie uruchamiano bez Client ID.
- Commit: nieutworzony. Repozytorium zawierało wcześniej liczne niezależne,
  niezatwierdzone zmiany i nie wolno ich mieszać w automatycznym commicie.
