# AMC 0.1.0-alpha.430 — szkic zmian do odbioru

## Naprawiona Historia odtwarzania

Potwierdzony przez silnik start Radia, lokalnego pliku albo podcastu zapisuje
teraz element w `Ctrl+H`. Ponowne odtworzenie przenosi wpis na początek bez
duplikatu, każda sesja zachowuje własną historię, a najstarszy ogon jest
ograniczony do 500 pozycji. Zapis następuje także po automatycznym przejściu
żywej kolejki, ponieważ źródłem jest rzeczywiste zdarzenie startu dźwięku.

Awaria samego zapisu Historii nie zatrzymuje już grającego materiału. NVDA
podaje wtedy krótki komunikat użytkowy, a techniczna przyczyna pozostaje tylko
w prywatnym logu programu.

## Pełny komunikat jednego elementu

Wspólna poprawka pojedynczego wiersza obejmuje teraz `Alt+R`, `Alt+Shift+R`,
`Ctrl+H` we wszystkich obsługiwanych sesjach oraz globalny podgląd `Ctrl+I`.
Po zsynchronizowaniu listy AMC podaje jej kontekst i użytkową nazwę wybranego
elementu, nie polegając na przypadkowym zdarzeniu fokusu Windows. Listy z
wieloma pozycjami zachowują zwykłą nawigację i mowę kontrolki.

## Stan profilu publicznego

Publiczny AMC pozostaje kopią wspólnego kodu AMC Test z wyłączonymi i fizycznie
pominiętymi niedopracowanymi modułami TIDAL, Spotify oraz Frontier Smart. WiiM,
Sonos i pełny eksport/import pozostają dostępne. Dokument jest szkicem do
ręcznego odbioru; nie jest automatycznie publikowany.

## Stan sprawdzenia

Pełna regresja wxPython: 1952 zaliczone, 110 świadomie pominiętych i 11
podtestów zaliczonych. Wszystkie 26 zestawów protokołu C# przeszło. Kompilacja
Release całego rozwiązania zakończyła się bez ostrzeżeń i błędów. Publiczna
paczka oraz zainstalowana kopia przeszły pełną integralność i kontrolowany
start; publiczny program jest uruchomiony do ręcznego odbioru NVDA. Instalacji
AMC Test nie podmieniono, ponieważ działający program nie potwierdził
bezpiecznego zamknięcia. Niczego nie opublikowano zdalnie.
