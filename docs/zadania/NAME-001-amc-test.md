# NAME-001 — widoczne nazwy AMC Test i AMC Public

## Status

Kod, testy, paczka AMC Test, instalacja i uruchomienie gotowe 22 października
2026. Potwierdzono tytuł `AMC Test — 22.10.2026, 22:48`. Nie zbudowano nowego
instalatora AMC Public i niczego nie opublikowano.

## Cel

Obie bieżące odmiany mają mieć krótką, rozpoznawalną nazwę użytkową:

- `AMC Test — dd.mm.rrrr, gg:mm` dla głównej wersji roboczej właściciela;
- `AMC Public — dd.mm.rrrr, gg:mm` dla paczki gotowej do niezależnego
  przekazania innej osobie.

Commit, identyfikator zawartości, numer techniczny i kanał aktualizacji nadal
są przechowywane do diagnostyki i kontroli integralności, lecz nie są zwykłą
nazwą czytaną przez NVDA.

## Nadrzędna korekta użytkownika z 22.10.2026

Ta decyzja zastępuje wcześniejszy zapis, według którego publiczny profil miał
być widoczny jako samo `AMC`, oraz wcześniejsze propozycje nazw zawierających
`alpha`, numer kompilacji albo długi identyfikator BUILD.

`AMC Test` jest główną rozwijaną wersją produktu, a nie bocznym repozytorium.
`AMC Public` oznacza wersję, którą można już samodzielnie wysłać innej osobie.
Nie zależy to od tego, czy ta sama paczka została już umieszczona na GitHubie;
lokalna gotowość do przekazania i publikacja zdalna są osobnymi stanami.

## Zachowanie widoczne dla użytkownika

- Tytuł głównego okna oraz polecenie `Pomoc > Wersja programu` używają tej
  samej nazwy z datą i godziną utworzenia paczki.
- Manifest zapisuje stałą etykietę czasu powstałą na komputerze budującym.
  Po przekazaniu paczki do innej strefy czasowej jej nazwa nie zmienia się.
- Przyszłe pliki instalatorów otrzymają nazwy w rodzaju
  `AMC-Test-2026-10-22-2125.exe` i `AMC-Public-2026-10-22-2125.exe`.
- Kreator instalacji, skróty, lista aplikacji i integracja z Eksploratorem
  używają odpowiednio nazw `AMC Test` i `AMC Public`.
- Starsze okno `AMC Python` jest nadal rozpoznawane jako poprzednik AMC Test,
  a starsze okno `AMC` jako poprzednik AMC Public. Aktualizacja nie traci więc
  możliwości odnalezienia bezpiecznie działającej starszej wersji.

## Komunikaty i etykiety dla NVDA

Zwykła informacja o wersji ma być krótka, na przykład:

- `AMC Test — 22.10.2026, 21:25`;
- `AMC Public — 22.10.2026, 21:25`.

Pełny hash źródeł i identyfikator paczki są dozwolone w raporcie technicznym
otwieranym świadomie przez użytkownika, ale nie w tytule okna, nazwie skrótu,
menu systemowym ani zwykłym komunikacie czytnika ekranu.

## Uzasadnienie i decyzje

- Data i godzina odpowiadają sposobowi, w jaki użytkownik zapamiętuje kolejne
  próby i łatwiej odróżniają paczki niż numer `alpha.4xx` związany historycznie
  także ze starym AMC WPF.
- Techniczny `AppVersion`, commit, `bundleId` i podpis integralności pozostają
  niezmienione w swojej roli, dlatego krótka nazwa nie osłabia identyfikacji
  pliku ani możliwości przeprowadzenia aktualizacji.
- Tag GitHuba może nadal używać technicznego numeru, ale tytuł przyszłego
  wydania i nazwa załącznika mają używać `AMC Public` oraz daty i godziny.

## Zmienione miejsca

- wspólny model profilu Python i .NET;
- tytuł okna i okno `Wersja programu`;
- zgodność launchera oraz aktualizatora ze starszymi nazwami;
- manifest paczki i skrypty budowy przyszłych instalatorów;
- nazwy kreatora, skrótów i integracji z Eksploratorem;
- przygotowanie i publikacja przyszłego AMC Public;
- testy Pythona, PowerShell i .NET oraz dokumentacja projektu.

## Testy i wynik

- Testy Pythona dotyczące wersji, profili, układu paczki, instalatora i
  publikacji: **63 zaliczone**. Z tego 62 wykonano w interpreterze systemowym,
  a test importu GUI wykonano osobno w prywatnym runtime AMC zawierającym
  wxPython. Pierwszy przebieg w sandboxie zatrzymał część przypadków na braku
  prawa zapisu do systemowego katalogu tymczasowego; powtórzenie poza tym
  ograniczeniem wykazało jeden brak zależności `wx`, po czym ten sam test
  przeszedł w właściwym runtime.
- Testy launchera i aktualizatora .NET: **30 z 30 zaliczonych**.
- Analiza składni skryptów `Build-AMCInstaller.ps1` i
  `Publish-AMCPublicRelease.ps1`: oba bez błędów parsera.
- Nie kompilowano Inno Setup, ponieważ użytkownik wyraźnie poprosił, by na tym
  etapie nie budować nowego instalatora.

## Znane ograniczenia

- AMC Test ma już nową nazwę. Zainstalowany wcześniej AMC Public zachowuje
  dotychczasową nazwę do czasu osobnej, świadomej promocji publicznej.
- Zachowane historyczne instalatory `alpha.4xx` nie są przemianowywane; ich
  dotychczasowe nazwy pozostają dowodem tego, co rzeczywiście zbudowano.
- Nie wykonano jeszcze ręcznego odbioru polecenia `Wersja programu` z NVDA ani
  odbioru przyszłego kreatora AMC Public. Tytuł głównego okna AMC Test został
  potwierdzony automatycznie po uruchomieniu.

## Wersja i commit

- Stan bazowy repozytorium podczas zmiany: `b9cedf7641c2`.
- Wspólny commit wdrożeniowy:
  `6ce22410bb80ac867504d15d17d890e9774d929e`.
- Paczka AMC Test:
  `2026.10.22-6ce22410bb80ac867504d15d17d890e9774d929e-f3e80d2d`,
  1670 plików.
- Instalacja: `D:\Projekty Codex\AMC Python`; integralność i kontrolowany
  start zaliczone, uruchomiony tytuł `AMC Test — 22.10.2026, 22:48`.
- AMC Public i publikacja: bez zmian; nie budowano instalatora.

## Materiał do dokumentacji użytkownika

### Projekt instrukcji

W tytule okna i w poleceniu `Pomoc > Wersja programu` AMC podaje nazwę
odmiany oraz datę i godzinę przygotowania paczki. `AMC Test` jest główną,
pełną wersją używaną do codziennej pracy i prób. `AMC Public` jest wersją
przygotowaną do przekazania innym osobom. Obecność albo brak tej paczki na
GitHubie nie zmienia jej nazwy.

### Projekt listy zmian

- Uproszczono widoczną nazwę wersji do `AMC Test — data, godzina` albo
  `AMC Public — data, godzina`.
- Usunięto z przyszłych nazw użytkowych numery `alpha` i długie identyfikatory
  BUILD, pozostawiając je w bezpiecznych danych technicznych.
- Zachowano zgodność aktualizacji ze starszymi nazwami `AMC Python` i `AMC`.
