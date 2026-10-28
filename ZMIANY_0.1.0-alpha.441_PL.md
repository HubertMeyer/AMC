# AMC Test 0.1.0-alpha.441 — szkic zmian i odbioru

To jest roboczy opis wydania testowego do sprawdzenia przez użytkownika.

## Najważniejsze zmiany

- Menedżer sesji `Ctrl+Shift+S` ma osobną czynność **Ustawienia sesji…** dla
  zaznaczonej, włączonej sesji. Konfiguracja sesji jest oddzielona od folderów,
  kont i urządzeń.
- Każda obsługiwana sesja może zdecydować, co dzieje się po uruchomieniu
  materiału Enterem: użyć ustawienia ogólnego, otworzyć odtwarzacz albo
  pozostać na liście.
- Ustawienie działa dla plików lokalnych, Radia, Podcastów i YouTube, Spotify,
  Sonosa i strumieni WiiM oraz dla obsługiwanych kolejek, zakładek i wyników
  wyszukiwania.
- Pliki lokalne i Radio mają również osobne ustawienie zachowania po
  uruchomieniu presetu.
- Dotychczasowe ustawienia ogólne pozostają wartościami domyślnymi. Istniejące
  profile zachowują więc wcześniejsze działanie, dopóki użytkownik nie wybierze
  ustawienia dla konkretnej sesji.
- `Ctrl+Alt+Enter` nadal otwiera ustawienia aktywnej sesji. Menu, pomoc
  kontekstowa, pełna pomoc i paleta poleceń używają tej samej nazwy
  **Ustawienia sesji**.

## Sposób odbioru

1. W zainstalowanym AMC Test wybierz **Pomoc** i **Sprawdź aktualizację AMC…**.
2. Po aktualizacji otwórz Menedżer sesji skrótem `Ctrl+Shift+S`.
3. Wybierz włączoną sesję, przejdź do przycisku **Ustawienia sesji…** i ustaw
   **Po uruchomieniu materiału Enterem** na **Pozostań na liście**.
4. Zapisz ustawienie i sprawdź, czy fokus wrócił do listy sesji.
5. Uruchom materiał Enterem w tej sesji. Dźwięk powinien się rozpocząć, ale
   lista i fokus powinny pozostać dostępne.
6. Ponownie otwórz ustawienia i sprawdź z NVDA wartości wyboru, anulowanie,
   zapis oraz powrót fokusu. Dla aktywnej sesji sprawdź także `Ctrl+Alt+Enter`.

## Ważne ograniczenia

- To wydanie kanału Test. Nie jest stabilnym wydaniem AMC Public.
- TIDAL i Frontier Smart nie pokazują martwego ustawienia zachowania Entera,
  ponieważ te sesje nie wykonują tej samej drogi wewnętrznego odtwarzania.
- `Ctrl+O` i otwieranie pliku przez powłokę Windows zachowują dotychczasową
  nawigację; nowe ustawienie dotyczy uruchamiania materiału Enterem.
- Automatyczne testy nie zastępują ręcznego odsłuchu kontrolek i powrotu
  fokusu z NVDA.
- Codex nie instaluje tej aktualizacji lokalnie. Ręczne uruchomienie
  aktualizacji pozostaje po stronie użytkownika.
