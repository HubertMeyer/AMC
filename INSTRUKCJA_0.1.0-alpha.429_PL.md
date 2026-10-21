# AMC 0.1.0-alpha.429 — szkic krótkiego odbioru NVDA

Program jest zainstalowany w `D:\Projekty Codex\AMC Public` i uruchamia się
plikiem `AMC.exe`.

## Najważniejszy test tej wersji

1. W Radiu rozpocznij krótkie nagranie skrótem `Ctrl+R` na liście stacji albo
   klawiszem `R` w odtwarzaczu Radia.
2. Naciśnij `Alt+R`.
3. Przy jednym nagraniu NVDA powinien podać jeden pełny komunikat: „Nagrywane,
   1 z 1, nazwa pliku”. Nie powinien czytać identyfikatora technicznego.
4. Naciśnij `Escape`, ponownie `Alt+R` i sprawdź, czy komunikat znów zawiera
   nazwę zaznaczonego pliku.
5. Zatrzymaj nagranie ponownie skrótem `Ctrl+R` albo `R`, a historię nagrań
   otwórz przez `Alt+Shift+R`.

## Historia i informacja pod lewą strzałką

- `Ctrl+H` otwiera historię odtwarzania.
- `Ctrl+0` nie ma przypisanej funkcji.
- Lewa strzałka na nowym, jeszcze niemierzonym pliku może potrzebować chwili na
  pierwszy pomiar parametrów. Powtórzenie na tym samym pliku powinno skorzystać
  z pamięci podręcznej i odpowiedzieć wyraźnie szybciej.

## Funkcje profilu publicznego

WiiM, Sonos oraz pełny eksport/import powinny być dostępne. TIDAL, Spotify i
Frontier Smart nie powinny pojawiać się w sesjach, menu, pomocy ani palecie
poleceń. Ten dokument jest szkicem do ręcznego odbioru i korekty użytkownika.
