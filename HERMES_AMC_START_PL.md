# AMC Python — start pracy dla Hermesa na drugim komputerze

Stan przekazania: 16 listopada 2026 r. Użytkownik chce prowadzić dalsze,
większe prace nad AMC przez Hermesa. Ten plik i pozostałe pliki repozytorium
zastępują niedostępną na drugim komputerze historię rozmów Codex.

## Pierwsze pięć czynności

1. Otwórz repozytorium `https://github.com/michalkasperczak/AMC` i gałąź
   `codex/amc-test-public-20261109`. Na komputerze użytkownika właściwy
   folder to `D:\Projekty Codex\AMC - integracja wxPython`; na drugim
   komputerze ustal rzeczywistą ścieżkę checkoutu.
2. Przeczytaj w całości `HERMES_AMC_PRZEKAZANIE_2026-11-16_PL.md` oraz
   `AGENTS.md`. Następnie przeczytaj `docs/zadania/README.md` i
   `docs/zadania/HERMES_AMC_KATALOG_ZADAN_2026-11-16_PL.md`.
3. Sprawdź `git status --short --branch`, `git log -n 12 --oneline`,
   `git remote -v` oraz HEAD gałęzi GitHub. Odczyt 16.11: czyste drzewo,
   commit `f55892435c5795cad48b7eb5f178f30f9985b158` lokalnie i na
   GitHub. To punkt odniesienia, nie gwarancja, że stan nie zmienił się później.
4. Wybierz tylko zadanie wskazane przez użytkownika. Przeczytaj cały jego
   rekord z późniejszymi korektami, kod i testy. Nie uznawaj starego
   nagłówka „Bieżący punkt wznowienia” w rejestrze za nowszy niż wydania
   z 15 listopada.
5. Po pracy zapisz w rekordzie zadania pliki, commit, wyniki testów, build,
   instalację, publikację i odbiór NVDA jako osobne fakty. Zaktualizuj rejestr.

## Krótka orientacja

- Bieżący produkt to AMC Python z interfejsem wxPython w `wxlite/` i
  hostem C# w `src/`. Historycznego AMC WPF nie rozwijaj.
- Test i Public są profilami tej samej bazy kodu. Bieżący Public nie ma
  Apple Music, a ma lokalnego Sonosa i Spotify. Możliwości sprawdzaj w
  `wxlite/amc_wx_lite/release_profile.py` i w manifeście konkretnej paczki.
- Ostatnie wydania sprawdzone na GitHub 16.11 to
  `test-2026.11.15.2036` i `public-2026.11.15.2040` z poprawką pobierania.
  Folder instalacji Test na D ma manifest źródeł alpha.510. Użytkownik 16.11
  mówi, że prawdopodobnie ma najnowszą wersję i odczuwa poprawę szybkości
  Podcastów oraz Radio Archiwisty; pobierania jeszcze nie sprawdzał.
  Proces `AMC.exe` został odczytowo potwierdzony w tym folderze, ze startem
  16.11 po zapisaniu paczki. Odbioru pobierania i NVDA nie wykonano.
- Przed zamknięciem lub aktualizacją AMC sprawdź stan nagrywania i
  harmonogramów. Nie przerywaj nagrania. Sam proces `yt-dlp` nie dowodzi
  nagrywania, bo może sprawdzać źródło YouTube.
- Wspólny model poleceń musi zgadzać się z klawiaturą, menu, paletą,
  pomocą i dostępnością NVDA. Szczegóły i datowane zgody są w `AGENTS.md`.

## Gdzie czytać dalej

- Pełny kontekst, architektura, interfejs, decyzje, aktualne wydania i
  otwarte tematy: `HERMES_AMC_PRZEKAZANIE_2026-11-16_PL.md`.
- Wszystkie 173 zastane pliki zadań i materiałów pomocniczych:
  `docs/zadania/HERMES_AMC_KATALOG_ZADAN_2026-11-16_PL.md`.
- Rejestr zadań: `docs/zadania/README.md`.
- Zależności i testy: `ZALEZNOSCI_AMC_STAN_PL.md`, `wxlite/JAK_TESTOWAC.md`.

Nie zakładaj, że Hermes automatycznie widzi czaty Codex lub lokalne pliki
drugiego komputera. GitHub przenosi zatwierdzone źródła i dokumentację;
lokalne instalacje, konta, nagrania i poświadczenia pozostają osobne.
