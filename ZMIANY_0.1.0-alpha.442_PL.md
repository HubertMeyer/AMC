# AMC Test 0.1.0-alpha.442 — szkic zmian i odbioru

To jest roboczy opis wydania testowego do sprawdzenia przez użytkownika.

## Najważniejsze zmiany

- Opcja **Zgodny z systemem** prawidłowo rozpoznaje polski język Windows także
  wtedy, gdy system zwraca nazwę regionalną `Polish_Poland`.
- Wybranie języka polskiego, angielskiego albo zgodnego z systemem i zapisanie
  Ustawień od razu zmienia język otwartego interfejsu. Restart AMC nie jest
  wymagany.
- Menu, karty Ustawień, przyciski, pomoc, paleta poleceń, nazwy dostępności,
  nagłówki i komunikaty są ponownie tłumaczone z jednego wspólnego katalogu.
- Naprawiono mieszany odczyt, w którym NVDA mógł mówić po polsku
  **Ulubione, lista**, gdy menu i pozostały interfejs były angielskie.
- Własne teksty użytkownika pozostają przypisane do polskiego, a osobne
  domyślne szablony polskie i angielskie oraz szablon przyszłych tłumaczeń są
  zachowane.

## Sposób odbioru

1. W zainstalowanym AMC Test wybierz **Pomoc** i **Sprawdź aktualizację AMC…**.
2. Otwórz **Ustawienia programu**, karta **Ogólne**.
3. W polu **Język** wybierz **Polski** i naciśnij Enter na przycisku zapisu.
   Otwarte menu i okna powinny od razu przejść na język polski.
4. Ponownie otwórz Ustawienia, wybierz **English** i zapisz. Menu, przyciski,
   pomoc i paleta poleceń powinny od razu przejść na język angielski.
5. W angielskim interfejsie przejdź do widoku Favorites. NVDA powinien mówić
   **Favorites, list**, bez polskiego słowa **Ulubione**.
6. Ustaw **Zgodny z systemem**. Na polskim Windows interfejs powinien od razu
   wrócić do języka polskiego.

## Ważne ograniczenia

- To wydanie kanału Test. Nie jest stabilnym wydaniem AMC Public.
- Automatyczne testy sprawdzają kompletność katalogów i zgodność menu, pomocy
  oraz palety, ale nie zastępują ręcznego odsłuchu całego interfejsu z NVDA.
- Duży angielski katalog zgodności może jeszcze wymagać korekty stylistycznej
  w mniej używanych miejscach interfejsu.
- Codex nie instaluje tej aktualizacji lokalnie. Ręczne uruchomienie
  aktualizacji pozostaje po stronie użytkownika.
