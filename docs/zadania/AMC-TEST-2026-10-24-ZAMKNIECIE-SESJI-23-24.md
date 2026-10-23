# AMC Test — zamknięcie sesji 23–24.10.2026

- Status: **bezpieczny punkt wznowienia; bieżąca wersja AMC Test jest
  zainstalowana i uruchomiona, dalszy odbiór wykona użytkownik 24.10.2026**.
- Gałąź: `integration/amc-test-20261023-late`.
- Punkt źródłowy przed tym zapisem: `225669da982abb740b17f9a47812fc6007d64931`.
- Stała instalacja testowa: `D:\Projekty Codex\AMC Python`.
- Profil: wyłącznie AMC Test. AMC Public, instalator publiczny i GitHub nie
  zostały dziś promowane ani opublikowane.
- Decyzja użytkownika z 24.10.2026: zakończyć tę sesję, zachować cały stan i
  przeprowadzić ręczny odbiór przygotowanych pozycji następnego dnia. Sonos i
  Apple Music będą kontynuowane w osobnych zadaniach.

## Bieżąca zainstalowana wersja

Najnowsza promocja zawiera źródła z commitu
`05621539cba449a06986e3544557d7d039b0e2d9`, pakiet `0ca58fd4`, etykietę
`2026.10.24-05621539cba449a06986e3544557d7d039b0e2d9-0ca58fd4` i 1674 pliki.
Potwierdzony tytuł okna to `AMC Test — 24.10.2026, 00:21`. Kandydat i stała
instalacja przeszły kontrolę manifestu, sum, izolowany start interfejsu i
hosta oraz kontrolowany start po atomowej podmianie.

Późniejsze commity do punktu `225669da` zmieniają wyłącznie dokumentację.
Nie ma nowszego kodu oczekującego na instalację. W chwili zamknięcia zapisu
działają procesy `AMC.exe`, `runtime\python.exe` i `host\amc_lite_host.exe`
z katalogu stałej instalacji. Nie należy ich teraz zamykać ani ponownie
promować tylko z powodu tego dokumentu.

## Co zostało wdrożone i co rzeczywiście potwierdzono

### Konto i Biblioteka YouTube

- Oficjalne logowanie Google do zakresu tylko do odczytu działa. Użytkownik
  zakończył przepływ zgody i zobaczył swoje kanały w AMC Test.
- Okno `Konto YouTube, subskrypcje i playlisty…` jest dostępne w menu Plik,
  palecie i pomocy. Sam start programu nie otwiera przeglądarki ani nie
  synchronizuje konta.
- Oddzielono podgląd od zapisu. Synchronizacja działa tylko YouTube → AMC i
  nie modyfikuje konta Google.
- Dodano synchronizację zwykłych playlist konta, opisy playlist i materiałów
  oraz chronione, trwałe respektowanie kanałów i filmów usuniętych lokalnie.
- Sam restart lub ponowne logowanie nie przywraca usunięć. Przywrócenie
  wymaga jawnego pola w oknie konta.
- Naprawiono kolejkę automatycznego odświeżania: wadliwe albo puste kanały nie
  blokują w nieskończoność następnych źródeł. Kanały bez standardowej karty
  `Filmy` dostają bezpieczną próbę publicznej strony głównej.
- Na rzeczywistej bazie po migracji do schematu 3 kolejka przeszła od pięciu
  pierwszych prób do 13 różnych źródeł, a liczba nigdy nieodświeżonych kanałów
  w Bibliotece spadła z 96 do 86. Wszystkie 123 kanały wcześniej usunięte
  lokalnie pozostały poza Biblioteką.
- `Alt+D` dla kanału, playlisty i materiału YouTube działa; użytkownik
  potwierdził odczyt opisów.
- `Ctrl+N` z szybkim wklejeniem linku, fokusem i ukrywaniem procesów
  pomocniczych został wcześniej przyjęty przez użytkownika.

### Transmisje YouTube i dynamiczne Radio

- Na zaznaczonym kanale YouTube działa wspólne polecenie
  `Transmisje na żywo i zaplanowane kanału…` pod `Ctrl+T`.
- Lista jednego kanału obsługuje: Enter — odtworzenie w AMC,
  `Ctrl+Shift+C` — kopiowanie publicznego adresu, `F5` — ponowne sprawdzenie
  tego kanału, Backspace — powrót do dokładnie tego kanału.
- `Ctrl+Y` otwiera formularz dodania kanału jako dynamicznej stacji Radia.
  Stacja przechowuje stały publiczny adres `/live`, a nie wygasający adres
  konkretnego filmu.
- `Ctrl+T` i `Ctrl+Y` pochodzą ze wspólnego modelu poleceń i mają parytet
  klawiatury, menu, menu kontekstowego, palety `Ctrl+Shift+K`, pomocy
  `Ctrl+F1` i pełnej pomocy.
- Lista transmisji wymaga aktywnego konta YouTube w AMC Test. Dynamiczne radio
  używa publicznego adresu i nie wymaga logowania.

### Spotify

- Duży podcast Tyflo jest wczytywany porcjami po 150 odcinków i odtwarza się
  wewnętrznym silnikiem. Użytkownik potwierdził ten wynik.
- Dodano prawdziwe tempo `0,50–2,00x` w Librespot z zachowaniem wysokości.
  Użytkownik potwierdził, że przyspieszanie działa.
- Skróty: `Shift+,` wolniej, `Shift+.` szybciej, `Ctrl+.` tempo normalne.
  Pole wartości mówi jednoznacznie, że `1,00x` oznacza tempo normalne.
- Po Enter AMC natychmiast mówi `Przygotowywanie odtwarzania Spotify`, ale
  nie ogłasza sukcesu przed rzeczywistym zdarzeniem startu.
- Fallback brakującego zapamiętanego urządzenia, na przykład odłączonego
  Denona USB, jest zaimplementowany przed pierwszym Play i ma testy. Ręczny
  zimny odbiór nadal pozostaje.
- Natywne rozdziały Spotify nie są wdrożone. Obecny kod może stworzyć
  rozdziały tylko z co najmniej dwóch znaczników czasu w opisie. Oficjalny
  obiekt odcinka używany przez bieżący katalog nie dostarcza takiej listy.

### Frontier Smart

- Teufel RADIO 3SIXTY jest wykrywany jako urządzenie FSAPI/UNDOK. Użytkownik
  potwierdził listę świadomego wyboru oraz przejście Enterem do chronionego
  pola PIN.
- PIN jest PIN-em NetRemote, a nie hasłem Wi-Fi. Dla tego modelu wartość
  fabryczna to `1234`; w radiu można ją sprawdzić w `Ustawienia systemowe →
  Sieć → Ustawienia NetRemote PIN`.
- Także jeden wykryty wynik wymaga świadomego wybrania z listy. Escape wraca
  bez ujawniania pola PIN.
- Sam PIN jest zapisywany w Menedżerze poświadczeń Windows, osobno dla AMC
  Test i urządzenia. Nie trafia do zwykłych etykiet NVDA ani profilu.
- Naprawiono usuwanie urządzenia: AMC nie usuwa wpisu z profilu i nie mówi o
  sukcesie, jeżeli Windows nie usunął poświadczenia. Tolerowany jest tylko
  stan, w którym poświadczenia już nie ma.
- Pełne połączenie kodem `1234`, zamknięcie konfiguracji, powrót fokusu,
  ponowne otwarcie, tryby, presety i sterowanie pozostają do ręcznego odbioru.

### Inne dzisiejsze elementy

- `Odtwarzaj losowo (R)` dla Plików, Podcastów i Spotify jest w kodzie,
  wspólnych powierzchniach poleceń i zainstalowanym AMC Test; pozostaje
  ręczny odbiór NVDA.
- Audyt TIDAL-a nie zmienił źródeł. Obecny model — katalog w AMC i
  przekazanie odtwarzania do oryginalnego TIDAL-a — pozostaje najbardziej
  praktyczny. Ewentualne późniejsze utwardzenie ma ograniczyć się do wyboru
  wiersza po stabilnym identyfikatorze, potwierdzenia właściwego utworu przed
  komunikatem sukcesu i sondowania wyłącznie faktycznie obsługiwanych poleceń
  sesji systemowej.
- Nie pobierano, nie wydobywano ani nie zapisywano chronionych strumieni z
  YouTube, Spotify lub TIDAL-a.

## Testy i wyniki bieżącej promocji

- Pełna regresja wxPython: **2029 zaliczonych, 111 kontrolowanie pominiętych,
  13 podtestów zaliczonych**; wykonana dwukrotnie po końcowej poprawce.
- Celowane testy menu, skrótów, konta i transmisji: **104 zaliczone i 2
  podtesty zaliczone**.
- Core `--youtube-subscription-sync-apply`: **5/5 scenariuszy**.
- Windows `--youtube-collection-normalization`: zaliczony.
- Testy launchera i aktualizatora podczas promocji: **30/30 zaliczonych**.
- Buildy .NET użyte przez promocję: **0 ostrzeżeń i 0 błędów**.
- Publiczna próba kanału `0dB.pl` zwróciła 100 materiałów bez logowania i bez
  zapisu do bazy.
- Przed promocją dwie kontrole wykazały 0 plików `.amc-partial`.
- Dwa szersze przebiegi nie są przedstawiane jako pełny sukces: Core
  zatrzymał się później na zastanym teście nazwy powłoki instalatora, a
  Windows SmokeTests na chwilowej odmowie `OpenClipboard`. Zmienione obszary
  oraz pełna regresja interfejsu przeszły.

## Plan ręcznego odbioru 24.10.2026

Nie trzeba wykonywać wszystkiego naraz. Najbardziej wartościowa kolejność:

1. Na prawdziwym kanale YouTube sprawdzić `Ctrl+T`, mowę wierszy live i
   upcoming, Enter, `Ctrl+Shift+C`, `F5` i Backspace.
2. Na kanale nacisnąć `Ctrl+Y`, sprawdzić fokus formularza, zapis i anulowanie.
   W Radiu sprawdzić Enter przy trwającej transmisji oraz czy brak transmisji
   daje uczciwy komunikat zamiast uruchomienia starego filmu.
3. Dla przygotowanych dynamicznych stacji sprawdzić nagrywanie teraz przez
   `Ctrl+R` oraz harmonogram przez `Shift+R`. Po odbiorze odnotować, czy
   transmisja zaczęła się o czasie, później lub zmieniła adres.
4. W oknie konta YouTube sprawdzić playlisty, zapis, strzałki po liście,
   ponowne otwarcie i powrót fokusu. Sprawdzić, czy usunięty kanał lub film
   nie wraca bez jawnego pola przywracania.
5. Przy odłączonym Denonie uruchomić AMC Test na zimno i rozpocząć krótkie
   odtwarzanie Spotify. Oczekiwany wynik: jeden komunikat o niedostępnym
   urządzeniu i dźwięk na domyślnym urządzeniu systemowym.
6. W Frontier Smart wpisać `1234`, wybrać `Połącz i zapisz`, sprawdzić
   komunikaty, zamknięcie okna, powrót fokusu, ponowne otwarcie oraz podstawowe
   sterowanie Teufelem.
7. Osobno sprawdzić `R` i pozycję `Odtwarzaj losowo` w menu kontekstowym dla
   Plików, Podcastów i Spotify.

## Ustalenia dotyczące dynamicznej stacji i nagrywania

Dynamiczne radio nie jest kopią nazwy z podmienianym ręcznie adresem. Jego
stały adres kanału `/live` jest rozwiązywany dopiero przy próbie odtworzenia
albo nagrania:

- jeżeli kanał właśnie nadaje publicznie, resolver znajduje aktualny film i
  odtwarzanie może się rozpocząć;
- jeżeli kanał nie nadaje, stacja jest chwilowo „martwa” i nie uruchamia
  archiwalnego filmu;
- przy następnym Enterze albo wystąpieniu harmonogramu resolver pyta ponownie,
  więc zmiana konkretnego adresu filmu nie wymaga edycji stacji;
- materiał prywatny, tylko dla członków, ograniczony regionalnie albo usunięty
  może pozostać niedostępny.

W Radiu `Ctrl+R` oznacza rozpoczęcie lub zakończenie nagrywania teraz, natomiast
`Shift+R` otwiera harmonogram dla wybranej stacji. Harmonogram przechowuje
stały adres `/live` i rozwiązuje go w chwili wystąpienia. Kod ponawia próbę
połączenia w czasie aktywnego okna harmonogramu, dlatego warto rozpocząć okno
kilka minut przed spodziewaną transmisją i zostawić zapas czasu. AMC musi
pozostać uruchomiony; wybudzenie może pomóc przy uśpieniu komputera, ale nie
uruchamia zamkniętego AMC ani wyłączonego komputera.

Poszczególne mechanizmy są zaimplementowane i testowane, lecz nie wykonano
jeszcze jednego pełnego testu rzeczywistego: brak live na początku okna,
późniejsze rozpoczęcie transmisji i automatyczne złapanie jej przez
harmonogram dynamicznej stacji. To jest najważniejszy odbiór przygotowany na
24.10.2026.

## Zapisane decyzje na następny etap YouTube

Użytkownik zaakceptował `Ctrl+Shift+I` jako skrót przyszłej zbiorczej listy
transmisji na żywo i zaplanowanych. Ta funkcja **nie została jeszcze
zaimplementowana**. Uzgodniony kierunek:

- widok systemowy Biblioteki, a nie sztuczny zapisany kanał;
- skanowanie tylko kanałów świadomie wybranych przez użytkownika, aby nie
  zużywać kosztownego limitu API na wszystkie subskrypcje;
- polecenie kontekstowe kanału `Uwzględniaj na zbiorczej liście transmisji`;
- przy pierwszym `Ctrl+Shift+I` i pustym wyborze — dostępny selektor kanałów;
- najpierw transmisje trwające, potem zaplanowane chronologicznie;
- użytkowa etykieta wiersza: kanał, tytuł, stan i czas, bez ID;
- Enter, `Ctrl+Shift+C`, `F5` i Backspace zgodne z obecną listą jednego kanału;
- `Ctrl+R` na transmisji trwającej może rozpocząć nagrywanie teraz;
- `Shift+R` na transmisji trwającej lub zaplanowanej może otworzyć wstępnie
  uzupełniony jednorazowy harmonogram oparty na stabilnym `/live` kanału;
- cotygodniowe nabożeństwa lepiej obsłużyć dynamiczną stacją i harmonogramem
  cyklicznym, a pojedyncze wydarzenie — `Shift+R` z przyszłej listy zbiorczej;
- pełny parytet klawiatury, menu, kontekstu, palety, obu pomocy,
  dokumentacji i testów NVDA jest obowiązkowy w tym samym zadaniu.

`Ctrl+I` pozostaje skrzynką nowych materiałów. `Ctrl+Shift+I` było wolne w
obecnym modelu skrótów i nie zmienia znaczenia importu ani Biblioteki.

## Otwarte tematy przekazane do osobnych zadań

- **Sonos:** kontynuować w osobnej instancji na podstawie `AMC10`; nie logować
  konta ani nie sterować głośnikami bez obecności użytkownika.
- **Apple Music:** wykonać osobną aktualną diagnozę oficjalnych możliwości
  logowania, biblioteki, playlist i osadzonego odtwarzania, a dopiero potem
  prototyp dla AMC Test. Dziś nie dodano Apple Music i nie potrzeba jeszcze
  przekazywać hasła, tokenu ani pliku od osoby z Apple ID.
- **Spotify — rozdziały:** pozostają ograniczone do znaczników czasu z opisu.
  Można osobno dodać uczciwszą diagnostykę różnicy między brakiem znaczników a
  błędem API, ale nie odzyska to natywnych danych, których kontrakt nie daje.
- **TIDAL:** bez przebudowy. Ewentualne utwardzenie identyfikatora i
  potwierdzenia startu powinno być osobnym, małym zadaniem.

## Dokumenty źródłowe do wznowienia

- [Bieżąca instalacja 00:21](AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md)
- [Konto YouTube i synchronizacja](YT-001-konto-youtube-i-synchronizacja.md)
- [Transmisje i dynamiczne radio](YT-002-transmisje-na-zywo-i-dynamiczne-radio.md)
- [Opisy YouTube](YT-003-opisy-youtube-alt-d.md)
- [Prędkość Spotify](SPOT-001-predkosc-odtwarzania.md)
- [Frontier Smart](FRONTIER-001-frontier-smart-fsapi.md)
- [Losowe odtwarzanie](PLAY-001-odtwarzanie-losowe-r.md)
- [Sonos](AMC10-logowanie-sonos-i-publiczny-broker.md)
- [Laboratorium TIDAL i Apple Music](STR-001-tidal-apple-music-laboratorium.md)

## Stan publikacji i bezpieczeństwa

- Nie utworzono wydania publicznego, instalatora publicznego ani zmiany na
  GitHubie.
- Nie zapisano w dokumentacji tokenów Google, sekretu klienta, PIN-u
  użytkownika, ciasteczek ani danych konta.
- Katalogi `.test-output/` i `.test-tmp/` są zachowane jako wyniki robocze;
  nie usuwano ich przed ręcznym odbiorem.
- Dalsze poprawki po odbiorze mają uzupełnić właściwe pliki zadaniowe z datą
  24.10.2026 zamiast nadpisywać dzisiejszy wynik.
