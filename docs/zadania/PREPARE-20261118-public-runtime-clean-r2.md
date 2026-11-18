# PREPARE-R2 — czysty runtime Public z wejścia AMC Test

## Stan

Przygotowano wyłącznie źródła i jednorazowy workflow dla gałęzi
`codex/amc-protected-public-test-20261118-issue21-r2`. Nie wykonano pushu,
GitHub Actions, lokalnego buildu .NET/instalatora, pobrania artefaktów,
instalacji, uruchomienia GUI ani zmiany ochrony.

## Przyczyna i decyzja

`copy_runtime` kopiował fizycznie cały runtime rozpakowany z przypiętego
instalatora AMC Test. Dla Public późniejsze `copy_apple_music_dependencies`
zwracało pustą listę, ale nie usuwało już skopiowanych `applemusic` i
`playwright`; kanoniczne `validate_profile_files` słusznie blokowało taki
kandydat. Walidacji nie zmieniono.

Przy kopiowaniu do nowego katalogu Public filtr używa istniejącego
`is_apple_music_dependency` i pomija tylko unikalne katalogi `applemusic*` i
`playwright*`. Współdzielone `httpx` i `greenlet` pozostają. Domyślne wywołania
`copy_runtime` zachowują poprzednie zachowanie. Dla runtime będącego już
katalogiem docelowym kod niczego nie usuwa ani nie filtruje w miejscu, a
niezmieniona walidacja nadal odrzuca prywatne pozostałości.

## Testy i wynik

- RED: syntetyczny pełny łańcuch Public `main → copy_runtime →
  validate_profile_files → manifest/fileHashes` zakończył się oczekiwanym
  błędem wskazującym `applemusic` i `playwright` w runtime.
- GREEN: trzy jawne kontrakty przeszły: czysty Public bez prywatnych plików,
  zachowany input i zgodność filesystemu z manifestem/hashami; kompletność
  Test wraz z `httpx`/`greenlet`; in-place Public bez mutacji i z odrzuceniem
  przez guard.
- Pięć statycznych kontraktów workflow przeszło. R2 zachowuje wszystkie bramki
  i zmienia wyłącznie dokładną gałąź triggera oraz warunku joba; nadal wymaga
  `before` równego zerom i `run_attempt == '1'`.
- Parser Windows PowerShell 5.1 przez `Parser.ParseInput` zaliczył 8 bloków
  workflow i 3 kanoniczne skrypty, bez ich wykonania.

## Ograniczenia i następny krok

Nie jest to zbudowany instalator ani wynik Defendera. Lokalnie nie ma PyYAML,
więc nie instalowano parsera; pięć istniejących kontraktów tekstowych workflow
pozostaje dowodem statycznym YAML. Rodzic ma najpierw niezależnie przejrzeć
commit, a potem może wykonać dokładnie jeden push nowej gałęzi; ręczne retry,
dispatch i ponowienie poprzedniego runu są poza zakresem.
