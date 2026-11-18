# PREPARE — chroniona jednorazowa budowa Public i Test z #21

## Stan

Przygotowano lokalnie na gałęzi
`codex/amc-protected-public-test-20261118-issue21`, od commitu
`86add1c14e146d321cb9042403c1ec0122ca5a8d`. Ten commit zawiera zintegrowane
źródła #21. Nie wykonano pushu, uruchomienia Actions, lokalnej budowy,
pobrania artefaktów, instalacji, publikacji Release ani zmiany ochrony lokalnej.

Workflow buduje najpierw `public`, następnie `test`, zawsze z jednego SHA.
Public nie dostaje `-AppleMusicSitePackages`; Test dostaje je jawnie. Profile
mają osobne raporty `public-*` i `test-*`, a binaria są przesyłane jako artifact
wyłącznie gdy cały job wraz z końcowym audytem Defendera zakończy się sukcesem.
Małe raporty pozostają przez `if: always()`.

## Bramki

- Branch/ref, all-zero `before` i `run_attempt == '1'` ograniczają job do
  pierwszego utworzenia jednej dokładnej gałęzi.
- Jest tylko GitHub-hosted `windows-2025`, `contents: read`, brak dispatch,
  cache, self-hosted, sekretów, publikacji release i uprawnień zapisu.
- Zachowano kontrolę ochrony i podpisu/hasza Inno z potwierdzonej gałęzi
  diagnostycznej; `Pyrsys B.V.` jest wymaganym dokładnym wydawcą.
- Skanowane są źródła, zamknięte wejścia, helper przed wykonaniem, runtime,
  dodatki NVDA, bundle przed i po każdym profilu, instalator po każdym profilu
  oraz detekcje 1116/1117 od początku joba.
- Brak wyniku skanu, ostrzeżenie, detekcja lub nieaktywna ochrona zatrzymują
  build; workflow nie publikuje Release i nie uruchamia instalatora.

## Weryfikacja lokalna

- Test statyczny Public/Test: 4/4 PASS (uruchomiony bez pytest, którego lokalne
  środowisko nie ma).
- Parser PowerShell: 8 bloków workflow i 3 skrypty PASS przez
  `System.Management.Automation.Language.Parser::ParseInput`; nic nie zostało
  wykonane.
- Parser YAML `ruamel.yaml`: PASS, 12 kroków workflow.
- `git diff --check`: PASS.
- `actionlint` ani `yamllint` nie są zainstalowane; nie pobierano narzędzi ani
  nie uruchamiano lokalnego buildu.

## Jedyny komendostart dla rodzica po przeglądzie

```bash
git -C /home/michal/.hermes/profiles/amc/cache/scratch/amc-protected-public-test-20261118-issue21 push --set-upstream origin codex/amc-protected-public-test-20261118-issue21
```

Ten push jest celowym, jednorazowym startem. Nie powtarzać go, nie uruchamiać
ręcznie workflow i nie publikować Release z workflow.
