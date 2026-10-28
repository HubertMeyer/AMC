# AMC Test 0.1.0-alpha.438 — szkic zmian i odbioru

To jest roboczy opis wydania testowego do sprawdzenia przez użytkownika.

## Najważniejsze zmiany

- Wielojęzyczny interfejs: dodano wspólną warstwę językową z pełnym polskim
  i angielskim katalogiem oraz wyborem języka zgodnego z systemem.
- Ustawienia: na karcie **Ogólne** można wybrać **Zgodny z systemem**,
  **Polski** albo **Angielski**. Zmiana zaczyna obowiązywać po zapisaniu i
  ponownym uruchomieniu AMC.
- Dostępność: menu, pomoc klawiatury, pełna pomoc, paleta poleceń, ustawienia,
  nazwy kontrolek i komunikaty korzystają z tej samej warstwy językowej.
  Techniczne identyfikatory poleceń nie są używane jako etykiety dla NVDA.
- Własne komunikaty: polskie i angielskie szablony są przechowywane osobno.
  Dotychczasowe własne teksty pozostają przypisane do języka polskiego.
- Prędkość odtwarzania: wartość neutralna jest jednoznacznie opisana jako
  normalna prędkość, a pozostałe wartości jako wolniejsze albo szybsze.
- Przygotowanie następnych języków: do źródeł dołączono deterministyczny
  szablon i kontrolę kompletności katalogów tłumaczeń.

## Sposób odbioru

1. W zainstalowanym AMC Test wybierz **Pomoc** i **Sprawdź aktualizację AMC…**.
2. Sprawdź opis wersji i uruchom aktualizację ręcznie.
3. Po ponownym uruchomieniu otwórz **Ustawienia programu**, kartę **Ogólne**,
   wybierz język i zapisz ustawienia.
4. Uruchom AMC ponownie i sprawdź z NVDA menu, ustawienia, `Ctrl+F1`, pełną
   pomoc oraz paletę poleceń `Ctrl+Shift+K`.
5. Na karcie **Dostępność i komunikaty** sprawdź, czy własne teksty są
   niezależne dla polskiego i angielskiego.

## Ważne ograniczenia

- To wydanie kanału Test. Nie jest stabilnym wydaniem AMC Public.
- Angielski katalog jest kompletny technicznie, ale nie przeszedł jeszcze
  pełnego ręcznego odsłuchu całego interfejsu z NVDA. Dalsze korekty językowe
  mogą zostać wydane w następnych aktualizacjach.
- Codex nie instaluje tej aktualizacji lokalnie. Ręczne uruchomienie
  aktualizacji pozostaje po stronie użytkownika.
