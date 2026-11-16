# HUBERT-SPOTIFY-20261116

Status: **w trakcie**. Zakres tego checkoutu obejmuje przegląd Spotify #9, #10
i #11. Nie wykonywano logowania, parowania ani odtwarzania na żywym koncie.
Nie zmieniono README, AGENTS, wersji, ustawień użytkownika ani danych
uwierzytelniających.

## Stan architektury

- Katalog i logowanie używają `LiteSpotifyWindowsCatalogBackend` oraz wspólnego
  konta Spotify. UI przekazuje zapisany Client ID i redirect URI do
  `ServiceAccountDialog`; nie wystawia już parowania LibreSpot.
- Odtwarzanie działa przez `LiteSpotifyChromeOutput` (Web Playback SDK w
  ukrytym Chrome) albo przez `LiteSpotifySoloistOutput`. Soloist jest
  alternatywnym adapterem, nie zamiennikiem lokalnej kolejki AMC.
- `LiteSpotifySoloistOutput` odpytuje `soloist ctl now --json`; nie tworzy
  połączenia WebSocket, nie odbiera `queue_changed` ani `context_changed` i nie
  wywołuje `get_queue`. Lokalna kolejka AMC pozostaje odrębna od kolejki
  Soloist.

## Uzasadnienie i decyzje

### #11 — EOS odrzucone i cofnięte

Niezależny przegląd odrzucił heurystykę EOS z commita
`c48081fe9ca51a01832bb332ca205877e53a94dd`. Stan poprzednio grającego utworu
`178/180`, po którym zewnętrzne źródło wykona seek do `0` i pauzę, jest dla tej
heurystyki nieodróżnialny od naturalnego końca. Także krótki, około
2-sekundowy utwór mógłby fałszywie wyemitować koniec. Test ręcznej pauzy
obejmował wyłącznie pauzę wywołaną przez AMC, nie ten zewnętrzny przypadek.

Nie ma śladu protokołu potwierdzającego provider EOS. Dlatego nie dodano nowej
heurystyki, timera ani obejścia. Do bazy `26950509629a2092b0cc4e7987e5a370d740db31`
przywrócono wyłącznie własne zmiany EOS w:

- `src/AccessibleMediaController.LiteHost/LiteSpotifyChromeOutput.cs`;
- `src/AccessibleMediaController.LiteHost/LiteSpotifySoloistOutput.cs`.

Usunięto własne pliki `LiteSpotifyPlaybackEndDetector.cs` i
`SpotifyPlaybackEndTests.cs` oraz ich wpisy `Compile` i rejestrację
`--spotify-playback-end` w ProtocolTests. #11 pozostaje otwarte do czasu
rzeczywistego dowodu protokołowego lub równoważnego, rozstrzygającego pomiaru.

### #10 — kandydat zachowany, bez odbioru C#

Zachowano `SpotifyCollectionCompletion` i testy kompletności kolekcji:
pełność zależy od obecności wymaganych `Track`, `Album`, `Artist` i `Playlist`,
a nie od równości liczby zwróconych kategorii do czterech. Wynik zawierający
również podcasty i odcinki nie jest więc fałszywie oznaczany jako częściowy.

Przegląd wykrył brak rzeczywistego wpięcia helpera do hosta: pełny
`AccessibleMediaController.LiteHost.csproj` linkował
`SpotifyIntegrationService.cs`, ale nie `SpotifyCollectionCompletion.cs`,
którego ta usługa używa. ProtocolTests miały osobny link, co nie dowodziło
kompilacji hosta.

Dodano minimalny link w pełnym projekcie hosta:

```xml
<Compile Include="..\AccessibleMediaController.Windows\Services\SpotifyCollectionCompletion.cs"
         Link="Engine\SpotifyCollectionCompletion.cs" />
```

`wxlite/tests/test_spotify_collection_completion_litehost_wiring.py` jest
wyraźnie statycznym testem XML wpięcia: czyta rzeczywisty pełny plik `.csproj`
i sprawdza, że host linkuje zarówno `SpotifyIntegrationService.cs`, jak i jego
helper. Nie jest testem kompilacji ani zachowania Spotify.

## Testy i wynik

- RED: `python3 wxlite/tests/test_spotify_collection_completion_litehost_wiring.py`
  zakończył się kodem `1`, ponieważ w pełnym projekcie hosta brakowało linku do
  `SpotifyCollectionCompletion.cs`.
- GREEN: po minimalnym linku ten sam test zakończył się `OK` (1 test).
- Porównanie obu plików wyjść Spotify z bazą `2695050` jest puste; nie pozostało
  odwołanie do detektora EOS ani do jego testu.
- C# ProtocolTests i build LiteHosta **nie zostały uruchomione**. W tym WSL
  `dotnet` nie jest w PATH. Oczekiwany prywatny plik
  `/mnt/c/Users/Michal/AppData/Local/AMC-BuildTools/dotnet/dotnet.exe` jest już
  wykonywalny, lecz niekompletny: `--info` kończy się kodem `131` z błędem braku
  `dotnet/host/fxr`. Nie instalowano SDK i nie symulowano wyniku.

## Dokładne polecenia do wznowienia C# na Hermesie

Po pojawieniu się prywatnego SDK uruchomić wyłącznie z osobnego stagingu NTFS,
nie z worktree WSL ani przez UNC. W powłoce WSL:

```bash
set -euo pipefail
DOTNET=/mnt/c/Users/Michal/AppData/Local/AMC-BuildTools/dotnet/dotnet.exe
STAGE=/mnt/c/Users/Michal/AppData/Local/AMC-BuildStaging/hubert-spotify-$(git rev-parse --short HEAD)
test -x "$DOTNET"
"$DOTNET" --info
test ! -e "$STAGE"
mkdir -p "$STAGE"
git archive HEAD | tar -x -C "$STAGE"
"$DOTNET" run --project "$STAGE/tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj" -c Release -- --spotify-collection-completion
"$DOTNET" build "$STAGE/src/AccessibleMediaController.LiteHost/AccessibleMediaController.LiteHost.csproj" -c Release
```

Te polecenia najpierw kompilują i uruchamiają wyłącznie test #10, następnie
budują host. Zaliczenie ich nie zastępuje ręcznej próby synchronizacji cache po
restarcie ani odbioru na koncie.

## Znane ograniczenia

- #10 nie jest odebrane: brak rzeczywistego uruchomienia C# oraz brak ręcznej
  synchronizacji pełnej kolekcji, restartu i odczytu cache.
- #11 nie ma bezpiecznej implementacji; nie uznawać go za rozwiązany.
- #9 pozostaje do odbioru OAuth/NVDA na świeżym profilu; nie zamykać go na
  podstawie inspekcji kodu.

## Materiał do dokumentacji użytkownika

Brak nowej funkcji użytkowej. Korekta #10 ma po przyszłym odbiorze zapobiec
fałszywemu komunikatowi o częściowym odświeżeniu, gdy Spotify zwraca komplet
wymaganych kategorii razem z podcastami i odcinkami. Nie obiecuje rozwiązania
końca utworu #11.

## Wersja i commit

Punkt wyjścia: `c48081fe9ca51a01832bb332ca205877e53a94dd`; baza porównania EOS:
`26950509629a2092b0cc4e7987e5a370d740db31`. Końcowy commit tego etapu należy
dopisać po lokalnym commicie; nie wykonano instalacji, publikacji ani push.