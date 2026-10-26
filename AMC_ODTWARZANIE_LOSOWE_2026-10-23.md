# AMC Test — Odtwarzaj losowo, zapis prac 23.10.2026

## Zachowanie użytkowe

- Klawisz R w odtwarzaczu przełącza odtwarzanie losowe.
- To samo polecenie jest dostępne jako przycisk odtwarzacza, pozycja menu
  Odtwarzanie i pozycja menu kontekstowego odtwarzacza.
- Etykieta mówi o następnym skutku: „Włącz odtwarzanie losowe” albo
  „Wyłącz odtwarzanie losowe”. Stan zaznaczenia jest zgodny na obu menu.
- Funkcja działa w Plikach lokalnych, Podcastach i YouTube oraz Spotify.
- Nie przejmuje R w Radiu, WiiM, TIDAL ani Apple Music, gdzie klawisz ma inne
  znaczenie albo funkcja nie jest dostępna.
- „Odtwarzaj jako następne” i jawna Kolejka mają pierwszeństwo przed losowaniem.
- Stan jest zapisywany osobno dla każdej obsługiwanej sesji.

## Dostępność i wspólny model poleceń

- Polecenie ma jeden identyfikator i jedną nazwę w katalogu poleceń.
- Przycisk, menu, menu kontekstowe, paleta poleceń, pomoc kontekstowa i pełna
  pomoc korzystają z tej samej informacji o dostępności.
- UI Automation przekazuje nazwę działania i skrót R bez technicznych nazw
  klas, właściwości lub identyfikatorów.
- Po przełączeniu fokus pozostaje w odtwarzaczu.

## Różnice między sesjami

| Sesja | Odtwarzanie losowe | Znaczenie R |
|---|---|---|
| Pliki lokalne | tak | przełącz losowanie |
| Podcasty i YouTube | tak | przełącz losowanie |
| Spotify | tak | przełącz losowanie |
| Radio internetowe | nie | nagrywanie |
| WiiM | nie | tryb powtarzania |
| TIDAL | nie | brak tego polecenia |
| Apple Music | nie | brak tego polecenia |

## Testy i wyniki

- Core, selektor `--playback-shuffle`: kod 0; kolejka ma pierwszeństwo,
  obsługiwane sesje i pomoc są zgodne.
- Windows, selektor `--playback-shuffle-ui`: kod 0; R, przycisk, oba menu,
  etykiety NVDA i stan zaznaczenia są zgodne.
- Kompilacja Core i Windows Debug: kod 0, 0 ostrzeżeń, 0 błędów.

## Ograniczenia i migracja

- Losowanie nie jest jeszcze rozszerzone na Apple Music ani TIDAL.
- Nie wymaga migracji danych; brak wcześniejszego wpisu oznacza stan wyłączony.
- AMC Test `0.1.0-alpha.425` został zainstalowany. Ręczny test NVDA pozostaje
  do wykonania przez użytkownika.

## Wersja i commit

- Wersja źródeł podczas implementacji: `0.1.0-alpha.424`.
- Wspólny zainstalowany pakiet testowy: `0.1.0-alpha.425`.
- Commit nie został jeszcze utworzony.
