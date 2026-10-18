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
- Jeżeli praca utknęła, ustaw `Zablokowane` i opisz konkretną przeszkodę oraz
  najkrótszy sposób wznowienia.
- Nie zapisuj tu haseł, tokenów, danych kont ani prywatnych logów użytkownika.

## Zadania

- `REC-001` — **Zrobione** — trwałość wykonanego harmonogramu nagrywania
  Radia i zgodność listy `Alt+R` z blokadą zamknięcia. Szczegóły:
  [REC-001-harmonogram-alt-r-zamykanie.md](REC-001-harmonogram-alt-r-zamykanie.md).
- `SCHED-001` — **Oczekuje** — dostępna przebudowa listy i edytora
  harmonogramów: informacje pod strzałkami, segmentowa data i czas oraz
  jednoznaczne wpisywanie czasu trwania. Szczegóły:
  [SCHED-001-edytor-i-klawisze-harmonogramow.md](SCHED-001-edytor-i-klawisze-harmonogramow.md).
- `NVDA-001` — **Oczekuje** — usunięcie opóźnienia `Ctrl+C` powodowanego przez
  NVDAExtensionGlobalPlugin. Szczegóły:
  [NVDA-001-opoznienie-ctrl-c.md](NVDA-001-opoznienie-ctrl-c.md).
- `SEARCH-001` — **W trakcie** — wyszukiwanie YouTube i Spotify: naprawa
  `Ctrl+Shift+L` oraz usunięcie komunikatu „AMC Python” przesłaniającego wynik
  prawej strzałki i potwierdzenie Biblioteki. Szczegóły:
  [SEARCH-001-youtube-biblioteka-komunikaty.md](SEARCH-001-youtube-biblioteka-komunikaty.md).
- `POD-001` — **Oczekuje** — sortowanie zbiorczej Biblioteki podcastów,
  kanałów YouTube i kolekcji „Media internetowe”. Szczegóły:
  [POD-001-sortowanie-biblioteki-zrodel.md](POD-001-sortowanie-biblioteki-zrodel.md).
- `AMC04` — **W trakcie** — przeniesienie do bieżącego AMC Test zatwierdzonego
  modelu skrótów zakładek, nazwanych zakładek, rozdziałów i historii. Nie jest
  to nowe zadanie: źródłowy audyt i rozpoczęta realizacja są zapisane w
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC03_AUDYT_SKROTOW_2026-10-18.md`
  oraz `AMC04_REALIZACJA_ETAP_A_2026-10-18.md`. Stare źródła WPF służą tylko
  jako wzorzec; właściwe wdrożenie wykonujemy w tym repozytorium.
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
- `REL-001` — **Oczekuje** — GitHub Releases, kanały aktualizacji oraz
  dostępny formularz Sygnalisty tworzący GitHub Issues. Szczegóły:
  [REL-001-github-aktualizacje-sygnalista.md](REL-001-github-aktualizacje-sygnalista.md).
- `STR-001` — **Oczekuje** — osobne laboratorium TIDAL i Apple Music, najpierw
  badanie oficjalnych API i warunków, później ewentualny profil testowy.
  Szczegóły:
  [STR-001-tidal-apple-music-laboratorium.md](STR-001-tidal-apple-music-laboratorium.md).

## Krótkie polecenia użytkownika

Wystarczy powiedzieć na przykład: `Uruchom zadanie NVDA-001`. Agent ma wtedy
odczytać rejestr oraz właściwy plik i wykonać wyłącznie wskazane zadanie.
