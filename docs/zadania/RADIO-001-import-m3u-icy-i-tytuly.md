# RADIO-001 — import M3U z nazwami ICY i tytuły bieżącej audycji

## Status

W trakcie — kod źródłowy i celowane testy są zaliczone. Poprawka nie została
jeszcze spakowana, zainstalowana ani opublikowana. Następnym uzgodnionym etapem
jest kandydat AMC Public do odbioru przez Huberta Meyera (`HubertMeyer`, podpis
commitów `cinkciarzpl`); dopiero po pozytywnym odbiorze ten sam commit ma zostać
wydany w profilu AMC Test.

## Zakres

- import nazw stacji z `icy-name` dla list M3U zawierających same adresy;
- uzupełnianie wcześniejszej nazwy będącej wyłącznie hostem bez nadpisywania
  nazwy nadanej przez użytkownika;
- odczyt `StreamTitle` z radia MP3, AAC i AAC+ oraz czytelny tytuł okna dla
  `NVDA+T`;
- weryfikacja PR #2 Huberta na załączonej playliście `radiafoobar.m3u`;
- poprawa niezależnej blokady kompilacji w kliencie publicznych stron
  Facebooka, która uniemożliwiała potwierdzenie projektu Windows.

## Materiał do dokumentacji użytkownika

Playlista M3U może zawierać same adresy transmisji, bez nazw stacji. Podczas
importu AMC pyta serwer radia o nagłówek `icy-name`. Jeśli serwer poda nazwę,
AMC zapisuje ją zamiast technicznej nazwy hosta. Ponowny import może w ten
sposób uzupełnić wcześniejszą nazwę-host, ale nie zastępuje własnej nazwy
użytkownika.

Podczas odtwarzania kompatybilnej transmisji MP3, AAC albo AAC+ AMC odczytuje
metadane bieżącego utworu lub audycji. `NVDA+T` podaje wtedy profil AMC, nazwę
stacji i bieżący tytuł. Jeżeli stacja nie wysyła tych danych, AMC nie wymyśla
nazwy ani tytułu.

## Uzasadnienie i decyzje

- 2026-10-29: PR #2 był oparty na właściwej aplikacji wxPython, ale deklaracja
  instalacji w AMC Public z godziny 01:36 nie mogła dotyczyć tych commitów:
  tag wydania powstał o 01:35, a commity PR-u po 16:13. Źródło, build,
  instalacja i publikacja są dlatego zapisane jako osobne stany.
- 2026-10-29: pierwotne 16 równoległych zapytań z limitem 2 sekund gubiło
  prawidłowe nazwy, gdy playlista zawierała kilka kanałów tego samego
  dostawcy. Limit zmieniono na 4 równoległe połączenia i 5 sekund na nagłówki,
  przy zachowaniu wspólnego budżetu 20 sekund na import.
- Import jest wykonywany w zadaniu tła interfejsu. Dłuższy limit nie blokuje
  klawiatury ani czytnika ekranu.
- AMC Public i AMC Test są profilami jednego kodu. Uzgodniona kolejność oznacza
  dwa osobne buildy tego samego zaakceptowanego commitu: najpierw Public do
  odbioru Huberta, potem Test. Nie powstaje osobna kopia źródeł Public.
- Nie komentowano i nie aktualizowano zewnętrznego PR-u bez osobnej decyzji
  użytkownika. W tym etapie nie wykonano instalacji ani publikacji.

## Testy i wynik

- Załączona lista: 18 wierszy, 17 unikalnych stacji, 1 prawidłowo pominięty
  duplikat. Kod z PR #2 nadawał czytelne nazwy 13 stacjom; po korekcie 15.
- Dwa pozostałe wpisy uczciwie zachowują nazwę hosta: adres
  `89.171.29.222:8000` nie odpowiedział także po 10 sekundach, a strumień
  `an1ugyygzk8uv` sam zwrócił `icy-name: -`.
- `Choral Works - ClassicalRadio.com Premium` oraz
  `Piano Jazz - JAZZRADIO.com Premium`, wcześniej zgubione przez zbyt agresywny
  limit, zostały odczytane na tej samej playliście po korekcie.
- Projekt `AccessibleMediaController.Windows.SmokeTests`, Release: kompilacja
  udana, 0 ostrzeżeń, 0 błędów.
- `--radio-icy-only`: 3/3 — własne połączenie ICY z przekierowaniem i tytułem,
  starszy strumień ICY MP3 oraz import M3U/PLS/XSPF/VRadio. Test importu obejmuje
  odpowiedź serwera po 2,5 sekundy, czyli po dawnym limicie.
- Projekt `AccessibleMediaController.LiteHost.ProtocolTests`, Release:
  kompilacja udana, 0 ostrzeżeń, 0 błędów; `--radio-library`: zaliczone.
- Właściwy `AccessibleMediaController.LiteHost`, Release: kompilacja udana,
  0 ostrzeżeń, 0 błędów.
- Celowane testy Pythona stanu, pełnej kopii, tytułu radia i tłumaczeń:
  90 zaliczonych, 1 kontrolowanie pominięty.
- Nie uruchamiano pełnej regresji ani widocznego interfejsu.

## Znane ograniczenia

- Serwer bez odpowiedzi albo z pustym lub zastępczym `icy-name` pozostaje pod
  nazwą hosta. To jest informacja o braku danych ze źródła, nie błąd parsera.
- Metadane tytułu zależą od stacji i formatu. XHE-AAC, MP2 oraz część starszych
  odpowiedzi fragmentowanych pozostają na dotychczasowej ścieżce zgodności i
  mogą nie przekazywać tytułu.
- Ręczny odbiór NVDA pozostaje: import, początkowy fokus po imporcie, komunikat
  liczbowy, odtwarzanie stacji, `NVDA+T`, zatrzymanie i ponowne otwarcie.
- Nie powstała paczka, instalator, lokalna instalacja ani wydanie GitHub.

## Zmienione pliki

- importer i odtwarzanie: `RadioPlaylistImporter.cs`,
  `IcyFrameRadioWaveProvider.cs`, `LegacyIcyAudioStream.cs`,
  `RadioMediaOutput.cs` i projekt LiteHost;
- Biblioteka i protokół: `LiteRadioLibraryMutation.cs`,
  `LiteEngineHandlers.cs`;
- interfejs i tłumaczenia: `wxlite/amc_wx_lite/gui.py` oraz katalogi językowe;
- testy: `Program.cs`, `RadioLibraryMutationTests.cs`,
  `test_current_radio_broadcast.py` i `test_i18n.py`;
- blokada kompilacji: `FacebookPublicPageClient.cs`.

## Wersja i commit

- PR #2: commity źródłowe `239c7e82`, `32fb6c04`, `f1c09348` po przeniesieniu
  na bieżącą gałąź.
- Korekta po rzeczywistej playliście i niezależnych testach: `5428b278`.
- Build: wyłącznie celowane projekty Release; nie powstał pakiet wydaniowy.
- Instalacja i publikacja: nie wykonano.

## Projekt wpisu do listy zmian

- Import list M3U zawierających same adresy uzupełnia nazwy stacji z nagłówków
  ICY i nie nadpisuje nazw nadanych przez użytkownika.
- Radio MP3, AAC i AAC+ może pokazywać bieżący utwór lub audycję również w
  tytule okna odczytywanym przez `NVDA+T`.
- Import nie porzuca już poprawnej nazwy tylko dlatego, że serwer odpowiada
  nieco wolniej albo lista zawiera kilka kanałów tego samego dostawcy.
