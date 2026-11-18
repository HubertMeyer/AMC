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

Nie jest to zbudowany instalator ani wynik Defendera. Worker nie miał PyYAML i nie instalował parsera. Rodzic niezależnie
przeprowadził rzeczywisty odczyt YAML przez dostępne `ruamel.yaml`; struktura,
ściśle wskazana gałąź r2 i uprawnienia `contents: read` zostały potwierdzone.
Rodzic może wykonać dokładnie jeden push nowej gałęzi; ręczne retry,
dispatch i ponowienie poprzedniego runu są poza zakresem.

## Niezależny przegląd rodzica przed uruchomieniem

- Powtórzono tylko krytyczną granicę, nie cały zestaw 47 kontraktów:
  nowy test produkcyjnego `main` na oryginalnym builderze odrzucił prywatne
  pliki (RED), a na poprawionym przeszedł (GREEN). Dwa sąsiednie kontrakty
  Test/in-place również przeszły. To małe jawnie syntetyczne fixture, nie
  prawdziwe EXE, instalator ani pomiar AV.
- Zweryfikowano pięć odebranych blobów produkcyjnych #21 wobec
  `ca9d1b23b804abdada8ffa833b1dc139705a95f9`: `gui.py`, `library_db.py`,
  `locales/en_legacy.json`, `locales/template.json` i
  `LocalFolderLibraryManager.cs` pozostają identyczne.
- Przegląd wykrył pominięty ref w `Enable-AMCDiagnosticProtection.ps1`:
  workflow wskazywał r2, lecz skrypt nadal wyłącznie starą gałąź. Nowy
  kontrakt najpierw rzeczywiście upadł; poprawiono tylko dokładny ref na r2,
  bez rozszerzania zgody na inny host lub gałąź.
- Sześć kontraktów workflow przeszło. Parser PowerShell 5.1 poprawionego
  skryptu przeszedł. Wyizolowany sam początkowy guard, bez cmdletów Defendera
  i bez I/O, przyjął kontekst r2 i odrzucił starą gałąź, self-hosted, Linux
  oraz brak GitHub Actions — pięć scenariuszy PASS. To test warunków, nie
  zmiana lokalnej ochrony ani dowód skanu.
- Dołączono aktualny plan z kanonicznej gałęzi (`0bce7df`), w tym rzeczywisty
  wynik pierwszego runu. Końcowy audyt, wejścia, hash/podpis Inno i hooki
  kanonicznych builderów pozostały niezmienione.
