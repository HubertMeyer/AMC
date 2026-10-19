# Rejestr zadań AMC

Ten katalog jest kanonicznym miejscem zapisywania osobnych zadań, które mają
przetrwać między rozmowami i być czytelne zarówno dla Codexa, jak i Hermesa.
Rejestr nie uruchamia pracy samodzielnie. Zadanie rozpoczyna się dopiero po
jawnym poleceniu użytkownika albo przez osobno uzgodniony harmonogram.

## Zasady prowadzenia

- Każde większe zadanie ma stały identyfikator i osobny plik o nazwie
  `<OBSZAR>-<NUMER>-<krotka-nazwa>.md`.
- Dozwolone statusy: `Oczekuje`, `W trakcie`, `Zablokowane`, `Zrobione`.
- Przed pracą przeczytaj ten rejestr, właściwy plik zadania, `AGENTS.md` oraz
  dokumenty wskazane przez zadanie.
- Nie rozpoczynaj pozostałych wpisów tylko dlatego, że znajdują się w rejestrze.
- Przy rozpoczęciu zmień status w pliku zadania i tutaj na `W trakcie`.
- Po zakończeniu zapisz w pliku zadania datę, wynik, zmienione pliki, commit,
  uruchomione testy z rezultatami i dokładną wersję instalacji, jeśli powstała.
  Dopiero po zweryfikowaniu kryteriów akceptacji ustaw status `Zrobione`.
- W każdym rozpoczętym zadaniu prowadź również sekcje `Materiał do dokumentacji
  użytkownika`, `Uzasadnienie i decyzje`, `Testy i wynik`, `Znane ograniczenia`
  oraz `Wersja i commit`. Tekst użytkowy ma być gotowy do automatycznego
  złożenia instrukcji i opisu wydania, ale pozostaje projektem do korekty i
  zatwierdzenia użytkownika.
- Korekty użytkownika zapisuj z datą i oznaczaj, które wcześniejsze ustalenie
  zastępują. Nie utrzymuj dwóch sprzecznych wariantów jako równoważnych.
- Jeżeli praca utknęła, ustaw `Zablokowane` i opisz konkretną przeszkodę oraz
  najkrótszy sposób wznowienia.
- Nie zapisuj tu haseł, tokenów, danych kont ani prywatnych logów użytkownika.

## Zadania

- `REC-001` — **Zrobione** — trwałość wykonanego harmonogramu nagrywania
  Radia i zgodność listy `Alt+R` z blokadą zamknięcia. Szczegóły:
  [REC-001-harmonogram-alt-r-zamykanie.md](REC-001-harmonogram-alt-r-zamykanie.md).
- `AMC02` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór
  NVDA** — krótkie wiersze `Alt+R` i `Alt+Shift+R`, brak
  osobnego „X elementów”, pamięć zaznaczenia oraz bitrate, wielkość i folder
  pod lewą strzałką także w `Ctrl+H`. Bieżący zapis realizacji:
  [AMC02-listy-nagrywania-i-historii.md](AMC02-listy-nagrywania-i-historii.md).
  Zatwierdzona analiza historyczna:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC02_ANALIZA_2026-10-18.md`
  oraz `AMC02_REALIZACJA_ETAP_A_2026-10-18.md`. Właściwe wdrożenie wykonujemy
  w bieżącym AMC Test, a stary kod służy tylko jako wzorzec.
- `SCHED-001` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór
  NVDA** — dostępna przebudowa listy i edytora
  harmonogramów: informacje pod strzałkami, segmentowa data i czas oraz
  jednoznaczne wpisywanie czasu trwania. Szczegóły:
  [SCHED-001-edytor-i-klawisze-harmonogramow.md](SCHED-001-edytor-i-klawisze-harmonogramow.md).
- `NVDA-001` — **W trakcie; poprawka zastosowana i NVDA zrestartowane, czeka
  na ręczny odbiór mowy oraz schowka** — usunięcie opóźnienia `Ctrl+C` powodowanego przez
  NVDAExtensionGlobalPlugin bez zmiany zwykłego schowka w innych programach.
  Szczegóły:
  [NVDA-001-opoznienie-ctrl-c.md](NVDA-001-opoznienie-ctrl-c.md).
- `SEARCH-001` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór
  NVDA** — wyszukiwanie YouTube, Spotify i TIDAL:
  `Ctrl+Shift+L` pozostaje w oknie także dla zapisanego wyniku, wykonuje jedną
  właściwą operację i nie oddaje mowy głównemu oknu. Szczegóły:
  [SEARCH-001-youtube-biblioteka-komunikaty.md](SEARCH-001-youtube-biblioteka-komunikaty.md).
- `POD-001` — **Oczekuje** — sortowanie zbiorczej Biblioteki podcastów,
  kanałów YouTube i kolekcji „Media internetowe”. Szczegóły:
  [POD-001-sortowanie-biblioteki-zrodel.md](POD-001-sortowanie-biblioteki-zrodel.md).
- `AMC04` — **Kod i testy zakończone; czeka na instalację i ręczny odbiór
  NVDA** — przeniesiony do bieżącego AMC Test zatwierdzony model skrótów
  zakładek, nazwanych zakładek, rozdziałów, historii widoków i historii
  odtwarzanych elementów. Bieżący zapis realizacji:
  [AMC04-nawigacja-zakladki-rozdzialy-historia.md](AMC04-nawigacja-zakladki-rozdzialy-historia.md).
  Źródłowy audyt i rozpoczęta realizacja są zapisane w
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC03_AUDYT_SKROTOW_2026-10-18.md`
  oraz `AMC04_REALIZACJA_ETAP_A_2026-10-18.md`. Stare źródła WPF służą tylko
  jako wzorzec; właściwe wdrożenie wykonujemy w tym repozytorium.
- `AMC05` — **Kod i testy zakończone; czeka na instalację i ręczny odbiór
  NVDA** — stan `Odtwarzane` lub `Wstrzymane` na właściwych listach bez utraty
  etykiety i bez przestawiania fokusa. Bieżący zapis realizacji:
  [AMC05-odtwarzany-element-na-listach.md](AMC05-odtwarzany-element-na-listach.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC05_ODTWARZANY_ELEMENT_NA_LISTACH_2026-10-18.md`.
- `AMC13` — **Kod i testy zakończone; czeka na instalację i ręczny odbiór
  NVDA** — `End` w otwartym odtwarzaczu Time Shiftu wraca na żywo i do tempa
  normalnego, a `NVDA+End` pozostaje poleceniem czytnika. Bieżący zapis
  realizacji:
  [AMC13-timeshift-end-na-zywo.md](AMC13-timeshift-end-na-zywo.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC13_TIMESHIFT_RADIA_2026-10-18.md`.
  Eksport fragmentów Time Shiftu pozostaje późniejszym rozszerzeniem.
- `AMC08` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA
  i świadomą próbę na koncie** — natywne playlisty Spotify w AMC
  Test: `Ctrl+P`, `Ctrl+Shift+P`, tworzenie playlist i dodawanie utworów lub
  odcinków. Przebieg: `AMC08-playlisty-spotify.md`. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.
  Historyczne źródła są tylko wzorcem; kod powstaje w tym repozytorium.
- `AMC09` — **Oczekuje, zlecone do nocnej realizacji przed AMC12** — dostępny
  Menedżer sesji pod `Ctrl+Shift+S`, włączanie Spacją, zwarta kolejność
  `Ctrl+1–9`, zmiana kolejności `Alt+strzałkami`, stan gotowości i stała nazwa
  `Radio`. Ma działać już w AMC Test; profil publiczny będzie później filtrował
  tę samą listę przez manifest możliwości. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.
  Automatyczne otwarcie na czystej instalacji pozostaje do odbioru AMC12 i nie
  może zmienić obecnego profilu testowego.
- `AMC12` — **Oczekuje, etap późniejszy tej samej nocy** — jeden kod, osobne
  profile AMC Test i publicznego AMC, izolowane magazyny oraz bezpieczny
  instalator. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`.
- `AMC10` — **Oczekuje, opcjonalnie tej samej nocy tylko logowanie Sonos** —
  działające sterowanie Sonosem i WiiM jest już przeszczepione i nie wymaga
  ponownego wdrażania. Pozostaje proste logowanie Sonos i brama publicznego
  brokera. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC10_SONOS_WIIM_URUCHOMIENIE_I_UJEDNOLICENIE_2026-10-18.md`.
  Bez obecności użytkownika nie logować konta i nie sterować głośnikami.
- `AMC14` — **Oczekuje, po fundamencie AMC12** — aplikacyjna integracja z
  powłoką Windows, przekazywanie plików do właściwej instancji i późniejsza
  rejestracja przez instalator. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC14_FOLDERY_I_INTEGRACJA_POWLOKI_2026-10-18.md`.
- `YT-001` — **Odłożone — po instalatorze i pierwszych stabilnych wydaniach** —
  oficjalne logowanie do konta YouTube, synchronizacja subskrypcji i zwykłych
  playlist oraz bezpieczny zakres czynności konta. Rozpocząć wyłącznie na nowe,
  jawne polecenie użytkownika. Szczegóły:
  [YT-001-konto-youtube-i-synchronizacja.md](YT-001-konto-youtube-i-synchronizacja.md).
- `NAME-001` — **Zrobione** — zmiana widocznej nazwy prywatnej wersji z
  „AMC Python” na „AMC Test”, bez zmiany technicznej tożsamości instalacji.
  Szczegóły: [NAME-001-amc-test.md](NAME-001-amc-test.md).
- `ARC-001` — **Oczekuje** — wspólny rdzeń poleceń dla GUI, palety, NVDA,
  przyszłego CLI i lokalnego sterowania AI. Szczegóły:
  [ARC-001-wspolny-rdzen-polecen-cli-ai.md](ARC-001-wspolny-rdzen-polecen-cli-ai.md).
- `MAC-001` — **Oczekuje, odłożone bez terminu** — ewentualna ocena portu AMC
  na macOS dopiero po wydaniu Windows i wyłącznie na nowe jawne polecenie.
  Szczegóły:
  [MAC-001-port-macos-wxpython-litehost.md](MAC-001-port-macos-wxpython-litehost.md).
- `LIC-001` — **Oczekuje** — Radio Browser, licencja BASS i bezpieczna decyzja
  o dobrowolnych wpłatach. Szczegóły:
  [LIC-001-radio-browser-bass-darowizny.md](LIC-001-radio-browser-bass-darowizny.md).
- `REL-001` — **Oczekuje; lokalny formularz Sygnalisty dopuszczony po
  instalatorze** — GitHub Releases, kanały aktualizacji oraz dostępny formularz
  Sygnalisty. Nocą można przygotować formularz, podgląd, filtrowanie danych i
  transport na atrapach. Własny Worker, tokeny i prawdziwe GitHub Issues
  dopiero razem z zatwierdzoną integracją GitHub. Szczegóły:
  [REL-001-github-aktualizacje-sygnalista.md](REL-001-github-aktualizacje-sygnalista.md).
- `STR-001` — **Oczekuje** — osobne laboratorium TIDAL i Apple Music, najpierw
  badanie oficjalnych API i warunków, później ewentualny profil testowy.
  Szczegóły:
  [STR-001-tidal-apple-music-laboratorium.md](STR-001-tidal-apple-music-laboratorium.md).

## Krótkie polecenia użytkownika

Wystarczy powiedzieć na przykład: `Uruchom zadanie NVDA-001`. Agent ma wtedy
odczytać rejestr oraz właściwy plik i wykonać wyłącznie wskazane zadanie.
