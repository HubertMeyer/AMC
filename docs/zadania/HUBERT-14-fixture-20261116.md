# HUBERT-14-fixture-20261116 — stabilny aparat testu strażnika procesu

Status: Zrobione — wyłącznie etap aparatury, odebrany i zintegrowany przez prowadzącego. Odbiór aktualizatora #14 jako funkcji produktu, instalacja, wydanie i zamykanie zgłoszenia pozostają otwarte.

## Cel i zakres

Ten etap diagnozuje pojedynczy padający test `UpdaterFindsRunningInstalledProcess` w `AccessibleMediaController.PythonLauncher.Tests`. Zmienione są wyłącznie:

- `tests/AccessibleMediaController.PythonLauncher.Tests/Program.cs`;
- ten rekord zadania.

`src/AccessibleMediaController.PythonUpdater/InstalledProcessGuard.cs` odczytano, ale nie zmieniono. Nie wykonano instalacji AMC, GUI, NVDA, dostępu do kont, API write, push ani wydania.

## Dowód przyczyny

Punkt bazowy: `c8c0c7f3992462ed9a86898c87f3f182cbc2ff34` w osobnym worktree `hubert14-fixture`. Własny staging NTFS:

`C:\Users\Michal\AppData\Local\AMC-Hermes-Build\hubert14-fixture`

Materializacja miała 2984 pliki po obu stronach; SHA-256 `Program.cs` przed zmianą był identyczny w worktree i stagingu:

`aa5f4c787c4bf4fa647dd15fe02c1086f026f865f8f1325a13f2f5a89f86cfa9`.

Rzeczywisty Windowsowy runner .NET 8.0.423 z katalogu NTFS dał RED: 45/46, z jednym błędem `aktualizator wykrywa żywy proces z instalacji` (kod procesu 1). Niezależna sonda fixture powtórzyła problem: kopia `cmd.exe` uruchamiająca `ping -n 300 127.0.0.1 > nul` albo `ping.exe -n 300 127.0.0.1 > nul` kończyła się przed skanem, kodem 1 i stderr `Serwer DNS nieautorytatywny dla strefy.`; guard zwracał 0.

Kontrola pojedynczej zmiennej z bezwzględnym `C:\WINDOWS\system32\ping.exe` utrzymała proces i dała guardowi 1 proces. `System32` było w `PATH`, `PATHEXT` zawierało `.EXE`, a wcześniejsza kontrola `where.exe ping` wskazywała systemowy plik. Przyczyna różnicy między nazwą a ścieżką bezwzględną nie została ustalona; nie przypisano jej braku `PATH` ani uprawnieniom.

Wniosek: defekt dotyczył niestabilnego fixture zależnego od `ping`/DNS, nie jest dowodem defektu produkcyjnego guarda.

## Zmiana aparatu

Test kopiuje teraz własny skompilowany runner testów wraz z wymaganymi plikami .NET do `runtime/amc-test-process.exe`, uruchamia go z wewnętrznym argumentem `--fixture-process`, odbiera jawne `READY` przez stdout i utrzymuje dziecko na `stdin` do zakończenia testu. Dziecko jest więc rzeczywiście żywe przed skanem, a test nadal wymaga:

1. wykrycia procesu przez niezmieniony `InstalledProcessGuard`;
2. dokładnie jednego blokera;
3. zgodności PID;
4. ścieżki wykonywalnej wewnątrz katalogu instalacji.

Asercje guarda nie zostały osłabione. `finally` kończy proces przez stdin, a dopiero przy przekroczeniu 5 sekund zabija całe drzewo.

## Testy i wynik

Windows PowerShell uruchamiał `C:\Users\Michal\AppData\Local\AMC-BuildTools\dotnet\dotnet.exe` 8.0.423 z cwd stagingu NTFS, `TEMP` i `TMP` w jego `headless-checks`, względną ścieżką projektu i bez uruchamiania z UNC.

- RED, przed zmianą: pełny `AccessibleMediaController.PythonLauncher.Tests`, **45/46**, kod **1**.
- GREEN po zmianie: pełny runner, **46/46**, `Wszystkie testy launchera przeszły (46).`, kod **0**.
- Stabilność: trzy kolejne pełne przebiegi, każdy **46/46**, kody **0**; po nich `LEFTOVER_AMC_TEST_PROCESS_COUNT=0`.

Końcowy SHA-256 `Program.cs` w worktree i stagingu:

`f25faf5e16118f3eae39e6186586a4bade8236b81a5501f414ba02f7fab96070`.

## Znane ograniczenia

Przebieg dowodzi tylko stabilności aparatu testowego i aktualnego kontraktu strażnika dla rzeczywiście żywego procesu w katalogu instalacji. Nie potwierdza pełnego zachowania aktualizatora na rzeczywistej instalacji, nie rozstrzyga źródła różnicy wyszukiwania `ping`, nie zastępuje instalacji ani odbioru NVDA.

## Wersja i commit

Baza worktree: `c8c0c7f3992462ed9a86898c87f3f182cbc2ff34`. Kandydat lokalny: `dbfa07e38123b43a2989ec58e232ea3f3a183ac6`; integracja w `codex/amc-test-public-20261109`: `d52fa980c0db6d8cf9bd876c14d6d8da1351fe3d`. Nie jest to ukończenie Issue #14.

## Niezależny odbiór prowadzącego

Przejrzano pełny diff i potwierdzono brak jakiejkolwiek zmiany drzewa `src` w kandydacie względem jego bazy. SHA-256 obu zmienionych plików odpowiadają raportowi wykonawcy. Worktree wykonawcy jest czysty.

Prowadzący wyeksportował dokładny commit kandydata do osobnego NTFS `C:\Users\Michal\AppData\Local\AMC-Hermes-Build\hubert14-parent-dbfa07e38123`: **2985 plików, 0 brakujących, 0 niezgodnych SHA-256**. Wymuszony rebuild Release: **0 ostrzeżeń, 0 błędów**, kod 0, 4.23 s. Ponowiony rzeczywisty runner Windows: **46/46**, kod 0, `LEFTOVER_AMC_TEST_PROCESS_COUNT=0`.

Po integracji porównano z kandydatem wszystkie pliki projektu testowego i linkowane drzewa `Shared`, `PythonLauncher`, `PythonUpdater` oraz `Core/ShellIntegration`: brak różnic. Log prowadzącego jest w scratch profilu AMC jako `amc-hubert14-parent-acceptance.log` i towarzyszący JSON. Nie uruchamiano GUI, instalatora ani programu na głównym komputerze.

## Materiał do dokumentacji użytkownika

Ten etap nie zmienia poleceń, skrótów, menu ani zachowania aktualizacji dostępnego użytkownikowi. Naprawia wyłącznie sposób sprawdzania blokady procesu w automatycznych testach. Nie oznacza jeszcze, że zgłoszony problem aktualizacji został odtworzony i odebrany na rzeczywistej instalacji.

## Następny krok

W zadaniu zbiorczym #14 wykonać na Hermesie uzgodniony odbiór cichej aktualizacji i blokady startu podczas instalacji, z uprzednim odczytowym sprawdzeniem nagrywania. Nie aktualizować ani nie zamykać AMC na głównym komputerze użytkownika.
