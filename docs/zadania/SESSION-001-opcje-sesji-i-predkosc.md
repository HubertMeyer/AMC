# SESSION-001 — pełne opcje sesji i domyślna prędkość

## Status

W trakcie — źródła i testy automatyczne ukończone 2026-10-22; zgodnie z
decyzją użytkownika zadanie czeka na zbiorczą instalację AMC Test i ręczny
odbiór NVDA razem z pozostałymi nocnymi zmianami.

## Zakres

Przenieść do bieżącego AMC Python wszystkie rzeczywiście działające opcje sesji
z historycznego AMC, dodać trwałą domyślną prędkość osobno dla Plików lokalnych
i Podcastów i YouTube oraz zachować wspólny kontrakt menu, skrótu
`Ctrl+Alt+Enter`, pomocy i palety poleceń.

## Materiał do dokumentacji użytkownika

Projekt roboczy. Okno **Opcje sesji** otwiera się skrótem `Ctrl+Alt+Enter`.
Pliki lokalne oraz Podcasty i YouTube mają osobne ustawienia pozycji
odtwarzania, domyślnej prędkości, normalizacji głośności, łagodnych przejść,
ciszy między utworami i zachowania po wyjściu z odtwarzacza. Wartość `1,00`
jest nazwana normalną prędkością, mniejsze wartości są opisane jako wolniejsze,
a większe jako szybsze. Radio i sesje zewnętrzne pokazują wyłącznie opcje,
które ich wykonawca rzeczywiście obsługuje. Urządzenie audio pozostaje osobnym
wyborem pod `Shift+A`.

## Uzasadnienie i decyzje

- 2026-10-22: pole urządzenia audio z historycznego edytora nie jest
  przenoszone, ponieważ było nieaktywne, a bieżący AMC ma działający osobny
  wybór urządzenia dla sesji pod `Shift+A`.
- 2026-10-22: decyzja z wcześniejszej mapy portu o pominięciu prędkości sesji
  zostaje zastąpiona poleceniem użytkownika. Prędkość ma być zapisywana i
  rzeczywiście stosowana od następnego uruchomienia materiału.
- Ustawienie odcinka lub podcastu zachowuje pierwszeństwo przed ustawieniem
  sesji. Brak jawnego wyboru sesji oznacza dziedziczenie ustawienia ogólnego.
- Zapis opcji nie przestawia w locie materiału grającego we współdzielonym
  silniku Plików i Podcastów.

## Testy i wynik

- Pełna regresja Pythona po połączeniu z rozdziałami Spotify:
  `1978 passed, 110 skipped, 11 subtests passed`.
  Pominięcia są oznaczonymi zależnościami opcjonalnymi, nie błędami.
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
- Próba z prawdziwym NVDA: odłożona do zbiorczej instalacji kandydata.

## Znane ograniczenia

- Ręczny odbiór z NVDA zostanie wykonany dopiero po zbiorczej instalacji
  kandydata AMC Test, zgodnie z decyzją użytkownika.
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

- Źródła: praca rozpoczęta na `b9cedf76`.
- Commit: zmiany lokalne, bez commitu i bez publikacji.
- Build: pełne rozwiązanie Debug zbudowane pomyślnie; nie jest to pakiet
  wydaniowy.
- Instalacja AMC Test: nie wykonano — świadomie odłożona do zbiorczej
  aktualizacji.
- Instalator i publikacja: nie wykonano.

## Projekt wpisu do listy zmian

- Rozszerzono `Ctrl+Alt+Enter` o pamiętanie pozycji i domyślną prędkość osobno
  dla Plików lokalnych oraz Podcastów i YouTube.
- Ustawienie podcastu lub odcinka nadal ma pierwszeństwo przed ustawieniem
  całej sesji.
- Bieżąca zmiana tempa nie przecieka już do domyślnego tempa innej sesji.
- Lista sesji i wszystkie wartości mają jawne etykiety użytkowe dla NVDA;
  `1,00 razy` jest nazwane normalną prędkością.
- Urządzenie audio pozostaje osobnym wyborem `Shift+A`; nie przywrócono dawnej
  nieaktywnej kontrolki.

## Porządek dysku

Po krzyżowym teście usunięto wyłącznie odtwarzalny plik
`session-options-payloads.json` z
`C:\Users\micha\Documents\Codex\2026-10-22\am\work` (96 807 bajtów).
Usunięcie nie jest odzyskiwalne z Kosza, ale plik można ponownie wygenerować.
Buildów `bin/obj` nie usuwano przed odbiorem zadania.
