# Zadanie na niedzielę — trwałe przygotowanie zależności AMC Python

To zadanie należy wykonać jako pierwsze, przed równoległymi pracami nad
Spotify. Jego celem nie jest bezmyślne podniesienie wszystkich bibliotek do
najnowszych wersji, lecz przygotowanie kompletnego, trwałego i powtarzalnego
środowiska zgodnego z plikami blokady projektu.

Punktem startowym jest najnowszy lokalny commit gałęzi
`integracja/wxpython-sonos-tidal-20261008`, a nie sam commit zainstalowanej
kompilacji. Pracować wyłącznie w
`D:\Projekty Codex\AMC - integracja wxPython`; nie modyfikować starego AMC WPF.

## Wynik wstępnego audytu z 14 października

Już dostępne:

- .NET SDK `8.0.423` i istniejący cache NuGet;
- Python `3.14.7` oraz użytkowy prywatny runtime z wxPython `4.3.1` i
  wxWidgets `3.3.3`;
- Node.js `22.23.2` oraz pnpm `11.25.0`;
- Microsoft Edge WebView2 Runtime `155.0.4283.45`;
- przypięta binarka hosta Librespot w `third_party\LibrespotHost\win-x64`,
  ze sprawdzaną przez projekt sumą SHA-256;
- `Cargo.lock`, `pnpm-lock.yaml` i dokładnie przypięty wheel wxPython.

Brakuje w zwykłej ścieżce systemowej:

- `rustup`, `rustc` i `cargo`;
- kompilatora MSVC oraz linkera z Visual Studio Build Tools.

Globalny `yt-dlp` również nie jest zainstalowany, ale to nie jest błąd
środowiska programistycznego. FFmpeg i `yt-dlp` są opcjonalnymi składnikami
zarządzanymi przez AMC i nie należy zastępować ich przypadkowymi instalacjami
globalnymi. Brak Inno Setup nie blokuje budowania ani aktualizowania nowego
AMC Python.

## Zasady przygotowania

1. Wszystkie wspólne cache i narzędzia, które nie muszą należeć do Windows,
   umieścić poza repozytorium w trwałym katalogu
   `D:\Projekty Codex\AMC - zależności`.
2. Nie przechowywać cache, środowisk, `target`, `node_modules` ani paczek w
   iCloud, OneDrive lub innym katalogu synchronizowanym.
3. Nie zmieniać wersji w `Cargo.lock`, `pnpm-lock.yaml`, plikach `.csproj` ani
   `requirements-win64.txt` tylko dlatego, że pojawiła się nowsza wersja.
   Najpierw odtworzyć obecny, działający zestaw.
4. Każdy plik pobrany bezpośrednio ma mieć zapisane źródło, wersję i SHA-256.
   Korzystać wyłącznie z oficjalnych źródeł producenta lub rejestru wskazanego
   w pliku blokady.
5. Nie podmieniać przypiętej binarki Librespot ani działającej instalacji AMC
   wynikiem lokalnej kompilacji bez porównania proweniencji i pełnych testów.
6. Nie zamykać ani nie aktualizować uruchomionego AMC podczas nagrywania.

## Zakres wykonania

### 1. Stały katalog i skrypty środowiska

Utworzyć w projekcie dwa idempotentne skrypty PowerShell:

- `scripts\Prepare-AMCDevelopmentDependencies.ps1` — audytuje, pobiera brakujące
  składniki do wspólnego katalogu i kończy się niezerowym kodem przy braku;
- `scripts\Use-AMCDevelopmentEnvironment.ps1` — ustawia dla bieżącego procesu
  ścieżki do wspólnych cache i narzędzi, bez polegania na katalogach
  tymczasowych Codex lub Hermes.

Skrypty mają przyjmować jawny parametr katalogu zależności, domyślnie
`D:\Projekty Codex\AMC - zależności`, oraz tryb `-CheckOnly`, który niczego nie
pobiera ani nie instaluje.

### 2. Rust i natywny host Spotify

- Zainstalować oficjalnym `rustup` trwały toolchain `1.98.1` z minimalnym
  profilem oraz targetem `x86_64-pc-windows-msvc`. Jest to wersja zapisana w
  proweniencji aktualnej binarki; `Cargo.toml` wymaga co najmniej Rust `1.85`.
- Ustawić wspólne `RUSTUP_HOME` i `CARGO_HOME` w katalogu zależności na dysku D.
- Jeżeli ich nie ma, doinstalować oficjalne Visual Studio Build Tools z MSVC
  v143 i właściwym Windows SDK. Nie instalować całego Visual Studio, jeżeli
  wystarczą narzędzia kompilacyjne.
- W `native\AmcSpotifyLibrespotHost` wykonać `cargo fetch --locked`, a następnie
  kontrolną kompilację `cargo build --release --locked`.
- Nie kopiować automatycznie wyniku do `third_party`. Najpierw uruchomić testy
  protokołu, sprawdzić importy PE, licencje i przygotować nową proweniencję.

### 3. .NET i NuGet

- Zachować .NET SDK 8 jako podstawę obecnego projektu; nie migrować frameworka
  w tym zadaniu.
- Przywrócić rozwiązanie dla `win-x64` do wspólnego cache NuGet na dysku D.
- Wykonać kompilację z `--no-restore`, aby potwierdzić, że pobrany zestaw jest
  kompletny. Nie aktualizować wersji pakietów NuGet w trakcie przygotowania.

### 4. Python i wxPython

- Zweryfikować prywatny runtime bieżącej instalacji: Python `3.14.7`, wxPython
  `4.3.1`, wxWidgets `3.3.3`.
- Pobrać do wspólnego cache dokładny wheel zapisany w
  `wxlite\requirements-win64.txt` z wymaganym SHA-256. Nie instalować wxPython
  globalnie i nie zastępować działającego runtime'u nieprzetestowaną wersją.
- Uruchomić test importu `wx` zarówno z runtime'u użytkowego, jak i ze
  środowiska używanego do testów GUI.

### 5. Node, pnpm i WebView2

- Utrwalić używany Node.js i pnpm w raporcie środowiska; skrypty nie mogą
  zależeć wyłącznie od ścieżki tymczasowego runtime'u Codex.
- Dla `src\AccessibleMediaController.Windows\TidalPlayerHost` wykonać
  `pnpm fetch --frozen-lockfile` do wspólnego store na dysku D, a następnie
  kontrolne `pnpm install --offline --frozen-lockfile` i test/budowę modułu.
- Potwierdzić obecność WebView2 Runtime. Nie dołączać ani nie aktualizować po
  cichu zdalnego Spotify Web Playback SDK; jego zachowanie sieciowe i warunki
  użycia są osobnym elementem odbioru Spotify.

### 6. Próba bez sieci i raport

Po pobraniu zależności odłączyć pobieranie w skryptach i potwierdzić, że z
cache da się wykonać co najmniej:

- `cargo build --release --locked` natywnego hosta;
- `dotnet restore` z lokalnego źródła/cache oraz pełną kompilację;
- instalację pnpm z `--offline --frozen-lockfile`;
- instalację dokładnego wheel wxPython do pustego środowiska próbnego;
- pełny zestaw testów AMC Python wykorzystywany przez promocję wydania.

Zapisać wersjonowany raport `ZALEZNOSCI_AMC_STAN_PL.md` z wersjami, ścieżkami,
sumami, wynikiem próby bez sieci i listą składników opcjonalnych. Nie umieszczać
w nim tokenów, danych kont Spotify/TIDAL/Sonos ani prywatnych ścieżek nagrań.

## Kryterium zakończenia

Zadanie jest zakończone dopiero wtedy, gdy nowy worktree utworzony od
kanonicznego commita potrafi skorzystać ze wspólnego katalogu zależności bez
ponownego pobierania wszystkiego, wszystkie kontrole przechodzą, a skrypty są
idempotentne. Samo zainstalowanie `cargo` albo jednorazowy udany build nie jest
wystarczające.

## Gotowe polecenie do uruchomienia zadania w niedzielę

> Pracuj w nowym AMC Python od najnowszego lokalnego commita gałęzi
> `integracja/wxpython-sonos-tidal-20261008`.
> Najpierw przeczytaj `ZADANIE_NIEDZIELA_PRZYGOTOWANIE_ZALEZNOSCI_PL.md` i
> wykonaj je w całości. Przygotuj trwały wspólny katalog zależności na dysku D,
> idempotentne skrypty audytu i przygotowania, cache do pracy bez ponownego
> pobierania oraz raport wersji i sum. Nie zmieniaj przypiętych wersji bez
> osobnego uzasadnienia, nie dotykaj starego WPF, nie instaluj wydania AMC i
> nie publikuj. Zakończ lokalnym commitem oraz podaj wyniki kontroli offline.
