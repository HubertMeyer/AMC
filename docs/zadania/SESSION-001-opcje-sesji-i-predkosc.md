# SESSION-001 — pełne opcje sesji i domyślna prędkość

## Status

W trakcie — korekta po odbiorze NVDA jest zbudowana, zainstalowana i
uruchomiona w zbiorczym AMC Test 2026-10-23; czeka na ponowny ręczny odbiór
NVDA. `Ctrl+Alt+Enter` edytuje teraz tylko aktywną sesję, a dziedziczona
prędkość ma krótką etykietę „Jak ustawienie ogólne”.

## Zakres

Przenieść do bieżącego AMC Python wszystkie rzeczywiście działające opcje sesji
z historycznego AMC, dodać trwałą domyślną prędkość osobno dla Plików lokalnych
i Podcastów i YouTube oraz zachować wspólny kontrakt menu, skrótu
`Ctrl+Alt+Enter`, pomocy i palety poleceń.

## Materiał do dokumentacji użytkownika

Projekt roboczy. Okno **Opcje sesji** otwiera się skrótem `Ctrl+Alt+Enter`
i zawsze dotyczy sesji aktywnej w chwili otwarcia. Nie zawiera dodatkowego
pola wyboru innej sesji. Aby zmienić opcje innej sesji, najpierw przejdź do
niej w głównym oknie AMC, a następnie użyj `Ctrl+Alt+Enter`.
Pliki lokalne oraz Podcasty i YouTube mają osobne ustawienia pozycji
odtwarzania, domyślnej prędkości, normalizacji głośności, łagodnych przejść,
ciszy między utworami i zachowania po wyjściu z odtwarzacza. Wartość `1,00`
jest nazwana normalną prędkością, mniejsze wartości są opisane jako wolniejsze,
a większe jako szybsze. Wariant dziedziczący prędkość jest czytany wyłącznie
jako „Jak ustawienie ogólne”; nie dokleja wartości bieżącego ustawienia
ogólnego. Radio i sesje zewnętrzne pokazują wyłącznie opcje, które ich
wykonawca rzeczywiście obsługuje. Urządzenie audio pozostaje osobnym wyborem
pod `Shift+A`.

## Uzasadnienie i decyzje

- 2026-10-22: pole urządzenia audio z historycznego edytora nie jest
  przenoszone, ponieważ było nieaktywne, a bieżący AMC ma działający osobny
  wybór urządzenia dla sesji pod `Shift+A`.
- 2026-10-22: decyzja z wcześniejszej mapy portu o pominięciu prędkości sesji
  zostaje zastąpiona poleceniem użytkownika. Prędkość ma być zapisywana i
  rzeczywiście stosowana od następnego uruchomienia materiału.
- 2026-10-23: korekta użytkownika zastępuje wcześniejszy projekt zbiorczego
  wyboru „Konfigurowana sesja”. `Ctrl+Alt+Enter` jest selektywne i zawsze
  edytuje tylko aktywną sesję. Zapis nie może zmienić ustawień innej sesji.
- 2026-10-23: wariant dziedziczonej prędkości ma etykietę wyłącznie
  „Jak ustawienie ogólne”. Tekst typu „Jak ustawienie ogólne — 2,00 razy —
  szybciej” był poprawny obliczeniowo, lecz mylący jako nazwa wyboru i zostaje
  zastąpiony krótką etykietą stanu dziedziczenia.
- Ustawienie odcinka lub podcastu zachowuje pierwszeństwo przed ustawieniem
  sesji. Brak jawnej wartości w polu sesji oznacza dziedziczenie ustawienia
  ogólnego.
- Zapis opcji nie przestawia w locie materiału grającego we współdzielonym
  silniku Plików i Podcastów.

## Testy i wynik

- Korekta z 2026-10-23: `76 passed` w trzech zestawach dialogu, skutku i
  podłączenia. Obejmuje brak zbiorczego pola sesji, zapis tylko sesji aktywnej,
  dokładną etykietę dziedziczenia prędkości, początkowy fokus, Anuluj, zapis,
  odmowę silnika, trwałość profilu, menu, pomoc i skrót.
- Pełna regresja Pythona po korekcie:
  `1983 passed, 111 skipped, 11 subtests passed`.
  Pominięcia są oznaczonymi zależnościami opcjonalnymi, nie błędami.
- Poniższe testy C# i build były zaliczone przed korektą wyłącznie w Pythonie;
  sama korekta nie zmienia hosta ani protokołu.
- Wszystkie 27 zestawów protokołu LiteHost: zaliczone.
- Testy launchera i aktualizatora: `30/30` zaliczone.
- Krzyżowy test parsera: 378 payloadów wygenerowanych przez Python przyjętych
  przez rzeczywisty parser C#.
- Pełna kompilacja `AccessibleMediaController.sln` w konfiguracji Debug:
  powodzenie, 0 ostrzeżeń, 0 błędów.
- `compileall` dla kodu i testów Pythona: powodzenie.
- Pełny `Core.SmokeTests` doszedł przez testy modelu Podcastów i wznowienia,
  lecz cały proces zakończył się istniejącą, niezwiązaną z tym zadaniem odmową
  polityki instalatora: `ShellApplicationName "Accessible Multimedia
  Controller"`. W tym zadaniu nie zmieniano instalatora.
- `ruff` nie był dostępny w przypiętym środowisku testowym; nie instalowano
  nowych narzędzi z sieci.
- Próba z prawdziwym NVDA 2026-10-23: niezaliczona dla zainstalowanego
  kandydata. Użytkownik potwierdził mylące zbiorcze pole sesji i etykietę
  „Jak ustawienie ogólne — 2,00 razy — szybciej”. Oba problemy poprawiono
  w źródłach.
- Zbiorcza promocja poprawki 2026-10-23: **30/30** testów launchera i
  aktualizatora, pełna regresja Pythona **1983 zaliczone, 111 pominiętych i
  11 podtestów zaliczonych**, kompilacje Release bez ostrzeżeń i błędów,
  kontrolowany start kandydata oraz stałej instalacji: OK.

## Znane ograniczenia

- Ponowny ręczny odbiór z NVDA pozostaje osobnym etapem. Bieżąca instalacja
  zawiera korektę, ale wynik automatyczny nie zastępuje odsłuchu początkowej
  wartości, przejścia po polach, Zapisz, Anuluj, powrotu fokusu i ponownego
  otwarcia.
- Wznowienie Spotify z historycznego WPF nie jest pokazane w bieżącym
  adapterze, ponieważ nowy wykonawca Spotify nie ma jeszcze bezpiecznej drogi
  sesyjnego wznowienia. Nie dodano martwej kontrolki.
- TIDAL, Spotify, Sonos i Frontier Smart mają obecnie wykonywalne zachowanie
  po wyjściu z odtwarzacza; WiiM nie ma opcji sesji, zgodnie z historycznym
  kontraktem urządzenia zewnętrznego.

## Zmienione pliki

- Model, okno i wykonanie po stronie Python:
  `wxlite/amc_wx_lite/session_options.py`, `gui.py`, `host_client.py` oraz
  `shortcuts.py`.
- Obsługa wznowienia po stronie C#:
  `src/AccessibleMediaController.LiteHost/Protocol/LiteQueueCoordinator.cs`,
  `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`,
  `src/AccessibleMediaController.Core/Configuration/PodcastLibraryDatabase.cs`
  oraz `PodcastLibraryMutationStore.cs`.
- Testy C#: `QueuePersistenceTests.cs` i `PodcastProgressStoreTests.cs`.
- Testy Python: `test_session_options.py`, `test_session_options_dialog.py`,
  `test_session_options_effect.py`, `test_session_options_wiring.py`,
  `test_transport_parity_gui_wiring.py`, `test_radio_jump_live.py`,
  `test_startup.py`, `test_host_client.py`, `test_general_settings_dialog.py`,
  `test_live_queue_activation.py`, `test_queue_persistence_wiring.py`,
  `test_command_palette.py` oraz `test_menu_exposes_existing_actions.py`.
- Dokumentacja: `wxlite/MAPA_1_1.md`, `wxlite/JAK_TESTOWAC.md`,
  `MAPA_KODU_PL.md`, `docs/zadania/README.md` i niniejszy rekord.

## Wersja i commit

- Pierwszy wspólny commit wdrożeniowy:
  `6ce22410bb80ac867504d15d17d890e9774d929e`.
- Korekta z 2026-10-23: commit źródeł i testów
  `d941c5212126c6d3ab5f8ed7a36e261ca05d9bd4`, przygotowany na bazie
  `b57ade090f3807f53dca9686a90f6e623e189ea6` wraz z poprawką YouTube.
- Build: pełne rozwiązanie Release zbudowane pomyślnie, 0 ostrzeżeń i
  0 błędów.
- Instalacja AMC Test:
  `2026.10.22-6ce22410bb80ac867504d15d17d890e9774d929e-f3e80d2d`,
  1670 plików. Aktualizator i kontrola integralności zakończyły się kodem 0;
  kontrolowany start przeszedł, a uruchomione okno ma tytuł
  `AMC Test — 22.10.2026, 22:48`. Ta instalacja nie zawiera korekty
  kontekstowego okna z 2026-10-23.
- Zbiorcza instalacja zawierająca korektę:
  `2026.10.23-c4a4c214e7e5bdc05fddc02c1dc644806d94490e-7353e273`,
  1670 plików, czyste źródło `c4a4c214e7e5bdc05fddc02c1dc644806d94490e`.
  Manifest, wszystkie sumy, kontrolowany start przed i po instalacji oraz
  uruchomione okno `AMC Test — 23.10.2026, 00:16` zostały potwierdzone.
- Instalator AMC Public i publikacja: nie wykonano.

## Projekt wpisu do listy zmian

- Rozszerzono `Ctrl+Alt+Enter` o pamiętanie pozycji i domyślną prędkość osobno
  dla Plików lokalnych oraz Podcastów i YouTube.
- Ustawienie podcastu lub odcinka nadal ma pierwszeństwo przed ustawieniem
  całej sesji.
- Bieżąca zmiana tempa nie przecieka już do domyślnego tempa innej sesji.
- `Ctrl+Alt+Enter` edytuje wyłącznie aktywną sesję, bez dodatkowego pola
  „Konfigurowana sesja”.
- Wariant dziedziczonej prędkości brzmi tylko „Jak ustawienie ogólne”, a jawna
  wartość `1,00 razy` pozostaje nazwana normalną prędkością.
- Urządzenie audio pozostaje osobnym wyborem `Shift+A`; nie przywrócono dawnej
  nieaktywnej kontrolki.

## Porządek dysku

Po krzyżowym teście usunięto wyłącznie odtwarzalny plik
`session-options-payloads.json` z
`C:\Users\micha\Documents\Codex\2026-10-22\am\work` (96 807 bajtów).
Usunięcie nie jest odzyskiwalne z Kosza, ale plik można ponownie wygenerować.
Buildów `bin/obj` nie usuwano przed odbiorem zadania.
