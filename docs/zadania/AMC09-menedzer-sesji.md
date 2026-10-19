# AMC09 — Menedżer sesji i zwarta numeracja

Status: **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA**

Data realizacji: 2026-10-19

Specyfikacja zatwierdzona przez użytkownika:
`D:\Projekty Codex\Accessible Multimedia Controller\AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.
Historyczny projekt został użyty tylko jako materiał do odczytu.

## Materiał do dokumentacji użytkownika

- `Ctrl+Shift+S` otwiera jedną listę „Menedżer sesji”. Lista pokazuje najpierw
  sesje włączone z ich aktualnymi numerami `Ctrl+1–9`, a następnie sesje
  wyłączone. Każdy wiersz zawiera zwykłą nazwę, stan włączenia oraz znany
  aplikacji stan gotowości. W mowie nie pojawiają się identyfikatory ani nazwy
  klas.
- `Enter` przełącza do zaznaczonej włączonej sesji. Na sesji wyłączonej lista
  pozostaje otwarta i podaje, że należy użyć Spacji.
- `Spacja` włącza lub wyłącza zaznaczoną sesję. Wyłączenie zagęszcza numery.
  Ponowne włączenie dopisuje sesję na końcu. Nie usuwa konta, biblioteki,
  historii ani ustawień usługi.
- `Alt+strzałka w górę` i `Alt+strzałka w dół` zmieniają położenie włączonej
  sesji oraz jej numer. Fokus pozostaje na tej samej sesji.
- Przycisk „Konfiguruj…” przechodzi do ustawień sesji podstawowej albo do
  właściwej sesji konta lub urządzenia. Samo otwarcie Menedżera nie otwiera
  przeglądarki, nie rozpoczyna logowania, nie skanuje sieci i nie steruje
  głośnikami.
- Nie można wyłączyć ostatniej sesji. Nie można również wyłączyć sesji, w
  której trwa wewnętrzne odtwarzanie, oczekiwanie na rozpoczęcie odtwarzania
  albo nagrywanie. Wyłączenie Sonosa lub WiiM zmienia tylko widoczność sesji;
  nie wysyła do urządzenia polecenia Stop.
- `Ctrl+1–9`, `Ctrl+Page Up`, `Ctrl+Page Down`, menu Widok, pełna pomoc,
  `Ctrl+F1`, dodatek NVDA i paleta `Ctrl+Shift+K` korzystają z tej samej
  aktywnej kolejności. Wyłączona sesja nie jest reklamowana w menu ani palecie.
- Świeży profil ma: `Ctrl+1` Pliki lokalne, `Ctrl+2` Radio oraz `Ctrl+3`
  Podcasty i YouTube. Domyślnie otwiera Pliki lokalne. Istniejący profil po
  aktualizacji zachowuje wszystkie dotychczasowe sesje i ich kolejność.
- Nazwa sesji radiowej brzmi wszędzie „Radio”. Wartości techniczne zapisu nie
  zostały zmienione, więc dotychczasowe stacje, harmonogramy i historia nie
  wymagają migracji nazw.
- W Ustawieniach pozostała informacja kierująca do Menedżera sesji. Nie ma już
  drugiego, konkurencyjnego edytora kolejności.

## Uzasadnienie i decyzje

- Jedna zwarta lista jest źródłem kolejności i stanu włączenia. Dzięki temu
  wyłączenie sesji nie zostawia dziury w numerach i nie rozjeżdża skrótów z
  menu, pomocą ani paletą.
- Zapis otrzymał wersjonowany znacznik migracji. Stary zapis oznaczał tylko
  kolejność, dlatego pierwsza migracja zachowuje wszystkie znane sesje zamiast
  uznać brakującą usługę za wyłączoną. Dopiero nowy zapis rozróżnia sesje
  aktywne i wyłączone.
- Stan gotowości pochodzi wyłącznie z już znanych danych lokalnych i pamięci
  bieżącego procesu. Menedżer nie wykonuje sieciowego „sprawdzania” konta w
  tle, bo samo przeglądanie listy nie jest zgodą na logowanie.
- Blokada wyłączania obejmuje wewnętrzne tory programu i Radio podczas
  nagrywania. Stan odtwarzania na urządzeniach zewnętrznych nie blokuje
  ukrycia Sonosa ani WiiM, ponieważ ukrycie sesji nie może sterować
  urządzeniem.
- Korekta z 2026-10-18 zastępuje wcześniejsze założenie stałych numerów usług:
  numer wynika z bieżącej, ręcznie ustawionej kolejności aktywnych sesji.
- Korekta z 2026-10-18 zastępuje nazwę „Radio internetowe” krótką nazwą
  „Radio” we wszystkich powierzchniach użytkowych. Wewnętrzny identyfikator
  `radio` i dane profilu pozostają bez zmian.
- Automatyczne pierwsze otwarcie Menedżera w publicznym AMC nie zostało
  włączone. To zachowanie należy do odbioru czystego profilu w AMC12 i nie
  zmienia obecnego profilu AMC Test.

## Zmienione miejsca

- Model aktywnych sesji i migracji: `wxlite/amc_wx_lite/session_order.py`,
  `state_store.py`.
- Wykonanie, fokus, gotowość, ochrona odtwarzania i nagrywania:
  `wxlite/amc_wx_lite/gui.py`.
- Wspólne menu, skróty, pomoc, paleta i dodatek NVDA:
  `menu_model.py`, `shortcuts.py`, `nvda_bridge.py`.
- Ujednolicona nazwa „Radio”: `navigation.py`, `search_catalog.py`,
  `search_sources.py`, `transient_preview_policy.py` oraz powiązane testy.
- Nowe testy Menedżera: `wxlite/tests/test_session_manager.py`, rozszerzone
  testy kolejności, migracji, menu, pomocy, palety i sesji usługowych.

## Testy i wynik

- Testy ukierunkowane modelu, magazynu, skrótów, palety, GUI i dostępnych
  etykiet: **94 zaliczone**.
- Testy regresji menu, Sonosa, TIDAL-a, WiiM, kolejności i izolacji wx:
  **152 zaliczone**.
- Pierwszy pełny przebieg wykrył pięć regresji testów: trzy testy zakładały
  dawną domyślną obecność wszystkich usług, jeden dawną nazwę polecenia, a
  jeden kolizję klawiszy dostępu. Założenia testów i klawisze menu poprawiono;
  ukierunkowana regresja po poprawce jest zielona.
- Pełny końcowy przebieg `wxlite/tests`: **1788 zaliczonych, 110 świadomie
  pominiętych, 11 podtestów zaliczonych**, czas 82,14 s. Pominięcia dotyczą
  istniejących bramek wymagających zbudowanych składników lub środowiska i nie
  zostały policzone jako zaliczone.
- Przed kompilacją bramka bezpieczeństwa o 02:54 UTC sprawdziła 15 jawnych
  katalogów nagrań: 0 aktywnych okien harmonogramów, 0 plików
  `.amc-partial`, 0 plików rosnących i 0 plików zablokowanych. Działające AMC
  zostało podmienione dopiero po tym wyniku.
- Skrypt odbiorczy zbudował trzy składniki .NET, utworzył pakiet liczący 1660
  plików, sprawdził manifest i sumy SHA-256, zastosował aktualizację,
  zweryfikował zainstalowany pakiet i uruchomił nowe AMC Test.
- Kwit instalacji potwierdza zgodność oczekiwanej i zainstalowanej wersji oraz
  trzy procesy uruchomione z jednego katalogu instalacji. Okno miało tytuł
  „AMC Test — 19.10.2026, 04:54”.

## Znane ograniczenia

- Prawdziwe logowanie Spotify, TIDAL i Sonos oraz wybór rzeczywistego WiiM
  wymagają świadomej próby użytkownika. Automaty tej nocy nie otwierały
  przeglądarki, nie logowały kont i nie wysyłały poleceń do urządzeń.
- Stan Spotify jest „Połączona” dopiero po odczycie konta w bieżącym procesie;
  przed nim Menedżer uczciwie pokazuje „Wymaga zalogowania”. TIDAL może użyć
  istniejącej lokalnej migawki Biblioteki, ale nie pobiera jej w tle.
- Publiczne filtrowanie sesji przez manifest możliwości, osobne magazyny AMC i
  AMC Test oraz jednorazowe otwarcie na czystej publicznej instalacji należą
  do AMC12.
- Ręczny odbiór NVDA powinien sprawdzić pierwsze otwarcie, ruch po wierszach,
  Spację, Enter, Alt+strzałki, Konfiguruj, anulowanie, powrót fokusu i ponowne
  otwarcie. Testy automatyczne nie są dowodem rzeczywistej mowy NVDA.

## Porządek dysku

- Po potwierdzonej instalacji usunięto wyłącznie katalog roboczy etapu
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\work\amc09` (27 plików,
  około 1,6 MB) oraz odtwarzalne katalogi `bin\Release` trzech budowanych
  projektów pod
  `D:\Projekty Codex\AMC - integracja wxPython\src` (157 plików, około
  133,3 MB).
- Łącznie odzyskano około 128,7 MiB. Usunięcie jest lokalnie nieodwracalne,
  ale te pliki są odtwarzalne z zatwierdzonych źródeł przez kompilację.
- Skrypt promowania sam usunął bieżący staging w `.test-tmp`. Nie usuwano
  zastanych, niepewnych katalogów `.test-tmp`, pamięci testów ani danych
  użytkownika.
- Zachowano zainstalowany program w `D:\Projekty Codex\AMC Python`, bieżący
  kwit oraz jedyną zweryfikowaną paczkę odbiorczą w `.test-output`. Nie
  usunięto źródeł, `.git`, ustawień, poświadczeń, nagrań ani pobrań.
- Pomocniczy katalog zapisu tego kwitu
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\work\amc09-docs`
  zawierał jeden plik Markdown (około 8,7 KB) i również został usunięty.

## Wersja i commit

- Kod i testy źródłowe: commit `dece7646` (`feat(amc09): dodaj menedzer sesji`).
- Dokumentacja wyniku i wersja użyta do instalacji: commit `6c79bdd3`
  (`docs(amc09): zapisz realizacje menedzera sesji`).
- Kompilacja, instalacja i uruchomienie: potwierdzone dla
  `2026.10.19-6c79bdd32904b9468b07489e79da715de512d3e0-972b46e1` w
  `D:\Projekty Codex\AMC Python`.
- Pełne testy Python wykonano przed kompilacją. Skrypt promowania otrzymał
  `-SkipTests`, aby nie powtarzać bez zmian tego samego przebiegu; kwit
  prawidłowo zapisuje testy etapu promowania jako „pominięte”, a nie jako
  zaliczone.
- Publikacja: nie wykonana i nie jest częścią nocnego zadania.
