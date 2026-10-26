# AMC — nazwy stacji z prostych playlist M3U, 26.10.2026

## Status i zakres

- Kanoniczne repozytorium: `D:\Projekty Codex\Accessible Multimedia Controller`.
- Profil roboczy: **AMC Test**; numer pozostaje `0.1.0-alpha.427`.
- Zakres: import playlisty w sesji **Radio internetowe** przez **Plik > Importuj stacje z playlisty…** albo `Ctrl+O`.
- Stan: źródła zmienione, projekt testowy skompilowany, izolowany test regresji zaliczony, rzeczywista playlista zgłaszającego sprawdzona przez nowy kod.
- Nie wykonano: ręcznego testu NVDA, uruchomienia okna AMC ani publikacji GitHub.
- Commit: nie wykonano w ramach tego zadania.

## Korekta oznaczenia wersji

Korekta użytkownika z 26.10.2026: określenie `alpha.428` użyte wcześniej w tym
zadaniu było błędne. Zastępuje ono wcześniejszą decyzję asystenta z 26.10.2026
o samodzielnym podniesieniu numeru wersji. Zmiana należy do bieżących źródeł
**AMC Test**, zachowuje numer `0.1.0-alpha.427` i nie tworzy nowego wydania
publicznego.

Po korekcie ponownie skompilowano projekt testowy. Kompilacja zakończyła się
bez ostrzeżeń i błędów, a `ProductVersion` wynikowego
`AccessibleMediaController.dll` wynosi `0.1.0-alpha.427`. Izolowany test importu
playlisty ponownie zakończył się powodzeniem. W tym pierwszym kroku nie
zbudowano instalatora i nie zmieniono zainstalowanej kopii AMC Test. Późniejsze
scalenie wszystkich uzgodnionych funkcji zostało zbudowane i zainstalowane;
szczegóły oraz sumy zawiera
`AKTUALIZACJA_AMC_TEST_0.1.0-alpha.427_2026-10-26.md`.

## Korekta wcześniejszej decyzji

Korekta użytkownika z 26.10.2026 zastępuje dotychczasowe założenie, że wpis M3U
bez `#EXTINF` ma pozostać wyłącznie z nazwą hosta. Foobar2000 potrafi w takim
przypadku skorzystać z nazwy zwracanej przez serwer. AMC również próbuje odczytać
użytkową nazwę `icy-name`, ale zachowuje ograniczenia czasu i liczby połączeń.

## Zachowanie użytkowe

1. Nazwa zapisana w `#EXTINF`, PLS, XSPF albo JSON ma pierwszeństwo i nie jest
   zastępowana przez serwer.
2. Dla wpisu zawierającego tylko URL AMC pobiera same nagłówki odpowiedzi i
   sprawdza `icy-name`, `ice-name` oraz `x-audiocast-name`.
3. AMC nie czeka na dźwięk ani dynamiczny `StreamTitle`, ponieważ ten opisuje
   audycję lub utwór, a nie stację.
4. Pusta nazwa, pojedynczy myślnik, pełny URL i tekst techniczny nie stają się
   etykietą listy. Bez nazwy pozostaje krótki host, na przykład
   `stream3.polskieradio.pl`.
5. Nazwy istniejących stacji katalogowych nadal nie są nadpisywane przy
   ponownym imporcie tego samego adresu.

## Limity i bezpieczeństwo

- najwyżej 64 automatyczne sondy nazw na jeden import;
- najwyżej 6 równoległych połączeń;
- najwyżej 4 sekundy na jedną stację;
- najwyżej 12 sekund na cały etap odczytu nazw;
- tylko HTTP albo HTTPS, do pięciu przekierowań;
- odpowiedź jest zamykana po nagłówkach, bez świadomego pobierania transmisji;
- awaria lub przekroczenie czasu nie unieważnia lokalnego importu;
- log zawiera tylko liczniki, bez URL-i i podpisanych parametrów zapytania.

## Komunikaty czytnika ekranu

- podczas sondowania: `Odczytuję nazwy stacji z serwerów`;
- po imporcie komunikat zachowuje dotychczasowe liczby dodanych, włączonych i
  pominiętych pozycji, a ponadto podaje `Nazwy odczytane z serwerów: N` oraz,
  gdy potrzeba, `Nazwy zastępcze: N`;
- lista otrzymuje wyłącznie znormalizowaną nazwę użytkową albo krótki host, nie
  obiekt środowiska uruchomieniowego, identyfikator polecenia ani pełny URL.

Fokus jest przywracany istniejącą drogą importu dopiero po zakończeniu etapu
nazw i odświeżeniu Biblioteki. Zmiana nie dodaje nowego menu ani skrótu, więc
nie zmienia katalogu poleceń, pomocy `Ctrl+F1`, pełnej pomocy ani palety.

## Różnice między powierzchniami

- **Radio internetowe:** automatyczne uzupełnianie nazw jest włączone.
- **WiiM — Strumienie sieciowe:** nadal korzysta z nazw zapisanych w pliku albo
  zastępczego hosta; ten import nie został objęty zgłoszeniem.
- **Sonos — Moje stacje:** nadal korzysta z nazw zapisanych w pliku albo
  zastępczego hosta; jego synchroniczny dialog nie został zmieniony.
- **Odtwarzanie:** dynamiczny tytuł ICY nadal trafia do „Teraz odtwarzane” i nie
  zastępuje nazwy stacji.

## Rzeczywisty wynik dla `radiafoobar.m3u`

- wiersze URL w pliku: 18;
- unikalne prawidłowe adresy przyjęte przez AMC: 17;
- nazwy odczytane przez nowy kod z serwerów: 14;
- nazwy zastępcze z hosta: 3;
- wpisy pominięte z powodu limitu sond: 0.

Przykładowe rozpoznane nazwy: `Radio Afera 98,6 MHz`, `Radio Nowy Swiat`,
`RMF24`, `jazzkultura`, `Rockserwis.fm [mp3]`,
`Dark Ambient Radio - Muzak for the Final Elevation` i `Mikrofon`.

## Testy i rzeczywiste wyniki

1. Kompilacja:

   `dotnet build tests\AccessibleMediaController.Windows.SmokeTests\AccessibleMediaController.Windows.SmokeTests.csproj --configuration Release --no-restore --disable-build-servers -m:1`

   Wynik: kod wyjścia 0, 0 ostrzeżeń, 0 błędów.

2. Izolowany test regresji:

   `dotnet run --project tests\AccessibleMediaController.Windows.SmokeTests\AccessibleMediaController.Windows.SmokeTests.csproj --configuration Release --no-build --no-restore --disable-build-servers -- --radio-playlist-import`

   Wynik: kod wyjścia 0, `OK: bezpieczny import M3U, PLS, XSPF i VRadio JSON`.

3. Rzeczywista playlista:

   `dotnet run --project tests\AccessibleMediaController.Windows.SmokeTests\AccessibleMediaController.Windows.SmokeTests.csproj --configuration Release --no-build --no-restore --disable-build-servers -- --radio-playlist-import-live <ścieżka-do-pliku>`

   Wynik: kod wyjścia 0; 17 wpisów, 14 nazw z serwerów, 3 nazwy zastępcze,
   0 wpisów niesprawdzonych.

Test automatyczny dowodzi także, że wpis z `#EXTINF` nie jest sondowany, URL
zwrócony jako `icy-name` nie wycieka do etykiety oraz że liczniki odpowiadają
rzeczywistemu wynikowi.

## Ograniczenia i dalsza weryfikacja

- Serwery zwracające wyłącznie niestandardowy wiersz stanu `ICY 200 OK` mogą nie
  zostać rozpoznane przez tę lekką sondę HTTP; import nadal przyjmie ich adres.
- Serwer może nie podawać nazwy, zwracać myślnik albo być chwilowo niedostępny.
- Pozycje powyżej limitu 64 zachowują nazwę hosta.
- Przed wydaniem instalatora należy uruchomić pełny zestaw testów Windows oraz
  wykonać ręczny test NVDA: początkowy fokus, komunikat postępu, strzałki po
  wynikowej liście, powrót fokusu i ponowny import.
- Zmiana modelu konfiguracji ani migracja danych nie są potrzebne.

