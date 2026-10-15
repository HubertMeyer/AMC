# Stan zależności deweloperskich AMC

Stan na 15 października 2026 r. dla commita bazowego
`17d7993cb26a3202e9c750f6d688dda8c10f183b`. Wspólny katalog ma trwałą
lokalizację `D:\Projekty Codex\AMC - zależności`; repozytorium ani cache nie
zostały umieszczone w katalogu synchronizowanym.

## Przygotowane środowisko

- .NET SDK `8.0.423`; współdzielony cache NuGet zawiera 28 paczek, a płaskie
  źródło lokalne pozwoliło wykonać restore bez sieci i kompilację Release z
  `--no-restore` (0 błędów, 0 ostrzeżeń).
- Rust `1.98.1` (`rustc 48a229cea`, Cargo `797e8a9bc`) i target
  `x86_64-pc-windows-msvc` w katalogach `rustup` i `cargo` na dysku D.
- Visual Studio Build Tools 2022 `17.14.37806.7`, MSVC v143
  `14.44.35207` i Windows SDK `10.0.26100.0`. Build Tools są jedynym
  składnikiem zainstalowanym poza dyskiem D, w wymaganej przez instalator
  lokalizacji `C:\BuildTools`; nie instalowano pełnego Visual Studio.
- Node.js `22.23.2` z oficjalnego archiwum oraz pnpm `11.25.0`, ze wspólnym
  store i cache na dysku D. `pnpm install --offline --frozen-lockfile`, 15
  testów modułu TIDAL i jego build zakończyły się powodzeniem.
- Prywatny runtime istniejącej instalacji: Python `3.14.7`, wxPython `4.3.1`,
  wxWidgets `3.3.3`. Oddzielne środowisko próbne używa Python `3.14.2` z tej
  samej zgodnej ABI `cp314`, dokładnego wheel wxPython i pytest `9.0.2`.
  Instalacja obu pakietów z cache offline i import `wx` przeszły.
- WebView2 Runtime `155.0.4283.45` jest obecny.

## Pobrane pliki i sumy

| Plik | Oficjalne źródło | SHA-256 |
| --- | --- | --- |
| `rustup-init-x86_64-pc-windows-msvc.exe` | `https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe` | `6f4bef66261261fcb43131be8720bab817d403a09edec7455c371974b90bdb7e` |
| `node-v22.23.2-win-x64.zip` | `https://nodejs.org/dist/v22.23.2/node-v22.23.2-win-x64.zip` | `1177b4137ba5adaa56354ae40f1080c7450e8ae09cecb47da459d1c52ac99f97` |
| `vs_BuildTools_17_bootstrapper.exe` | `https://aka.ms/vs/17/release/vs_BuildTools.exe` | `2a6aa7d94e38d457a4eb3930fc60056ecab06865b2eb925e5275b8473a017583` |
| `wxpython-4.3.1-cp314-cp314-win_amd64.whl` | PyPI, wersja i hash z `requirements-win64.txt` | `bbb4cefea441cba77f81b0ac2f7445f0ad01f18fee3b72a78ed48298b3f8f0ab` |
| `pytest-9.0.2-py3-none-any.whl` | PyPI | `711ffd45bf766d5264d487b917733b453d917afd2b0ad65223959f59089f875b` |

Instalator Build Tools ma prawidłowy podpis Microsoft Corporation, suma
rustup została porównana z oficjalnym plikiem `.sha256`, a suma Node.js z
oficjalnym `SHASUMS256.txt`. Pełny wykaz wheel testowych i ich sum znajduje
się poza repozytorium w
`D:\Projekty Codex\AMC - zależności\metadata\python-test-wheels.json`.

## Próby kontrolne i offline

- Cargo: wykonano pełne `cargo fetch --locked`, potem build Release z
  `--locked --offline` i statycznym CRT. Testy: 30 jednostkowych i 13 E2E,
  wszystkie zaliczone.
- Lokalna binarka kontrolna hosta Spotify ma 6 555 648 bajtów i SHA-256
  `bdf4484e6224ba46a459104addfeebdfe9b67ace4d55479f2bf496d57d3c64f7`.
  Importy PE nie zawierają `vcruntime`, `msvcp` ani `api-ms-win-crt`.
  Wszystkie 372 paczki Cargo mają deklarację licencji, a paczki rejestru są
  objęte istniejącym indeksem licencji repozytorium.
- .NET: restore z lokalnego źródła/cache i pełna kompilacja Release bez
  restore przeszły.
- pnpm: fetch/cache, instalacja offline z zamrożonym lockfile, testy i build
  przeszły.
- Python: końcowy zestaw używany przez promocję wykonał `1554 passed`,
  `110 skipped` oraz `11 subtests passed` w 72,47 s. Zmienna `DOTNET` wskazywała
  bieżące SDK, dzięki czemu testy protokołu rzeczywiście użyły zbudowanego
  hosta zamiast linuksowej ścieżki domyślnej.
- `Prepare-AMCDevelopmentDependencies.ps1 -CheckOnly` po przygotowaniu
  zakończył się powodzeniem i potwierdził wersje, cache, MSVC, SDK, prywatny
  runtime i WebView2 bez pobierania ani instalowania.

Pierwsza pełna próba skryptu ujawniła dwie rzeczy, które zostały poprawione:
ogólna zmienna `Platform=x64` z `vcvars64.bat` kolidowała z rozwiązaniem
`Any CPU`, a nowy test używał pytest, którego nie było w czystym środowisku.
Końcowe kontrole odpowiadają już poprawionym skryptom. Ze względu na czas nie
powtarzano po tych poprawkach całego wielominutowego skryptu od początku;
każdy jego etap został jednak uruchomiony po poprawce, a finalny `-CheckOnly`
jest zielony.

## Granice zadania

- Nie zmieniono `Cargo.lock`, `pnpm-lock.yaml`, plików `.csproj` ani
  `requirements-win64.txt`.
- Nie podmieniono niczego w `third_party`. Lokalna binarka kontrolna różni się
  sumą od przypiętego wydania i pozostała wyłącznie w `cargo-target`; jej
  proweniencja jest w `metadata\amc-spotify-librespot-host-local-provenance.json`.
- Nie instalowano ani nie uruchamiano AMC, nie publikowano wydania i nie
  wykonywano testu z kontem lub dźwiękiem Spotify.
- FFmpeg i `yt-dlp` pozostają opcjonalnymi składnikami zarządzanymi przez AMC.
  Nie instalowano ich globalnie. Inno Setup nie jest potrzebny do bieżącego
  buildu. Zdalny Spotify Web Playback SDK nie był aktualizowany ani dołączany.

Do powtarzalnej pracy służą `scripts\Prepare-AMCDevelopmentDependencies.ps1`
oraz `scripts\Use-AMCDevelopmentEnvironment.ps1`. Drugi skrypt ustawia cache,
narzędzia, MSVC, statyczny CRT i ścieżkę do `dotnet` wyłącznie dla bieżącego
procesu PowerShell.
