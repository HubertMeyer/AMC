# AMC 0.1.0-alpha.430 — szkic krótkiego odbioru NVDA

Programy po instalacji uruchamiają się z:

- `D:\Projekty Codex\AMC Public\AMC.exe` — publiczny AMC;
- `D:\Projekty Codex\AMC Python\AMC.exe` — AMC Test.

## Historia odtwarzania `Ctrl+H`

1. W Radiu uruchom stację i poczekaj, aż rzeczywiście zacznie grać.
2. Naciśnij `Ctrl+H`.
3. Historia powinna zawierać uruchomioną stację. Jeśli jest to jedyna pozycja,
   NVDA powinien podać nazwę widoku, pozycję oraz nazwę stacji w jednym pełnym
   komunikacie.
4. Naciśnij `Escape`; program powinien wrócić dokładnie do wcześniejszej sesji,
   widoku i zaznaczenia.

Historia publicznego `alpha.429` była naprawdę pusta, ponieważ wersja wxPython
nie zapisywała potwierdzonego startu Radia, pliku ani podcastu. `alpha.430`
zapisuje nowe odtworzenia; nie odtwarza wstecz wpisów, których poprzednia
wersja nigdy nie zachowała.

## Pojedynczy element podglądu

- `Alt+R`: „Nagrywane, 1 z 1, nazwa pliku”.
- `Alt+Shift+R`: „Nagrane, 1 z 1, nazwa pliku”.
- `Ctrl+H`: nazwa Historii, pozycja lub liczba oraz nazwa jedynego elementu.
- `Ctrl+I`: przy jednym nowym materiale komunikat zawiera także jego nazwę.

Identyfikatory techniczne, nazwy klas i treści błędów bazy nie powinny być
czytane przez NVDA. Jeśli zapis Historii nie powiedzie się, odtwarzanie ma
działać dalej, a użytkownik otrzymuje tylko krótki komunikat bez szczegółów
technicznych.

## Profile wydania

Publiczny AMC i AMC Test powstają z tego samego commitu. Publiczna paczka ma
Pliki, Radio, Podcasty/YouTube, WiiM, Sonos oraz pełny eksport i import danych.
Nie zawiera jeszcze TIDAL-a, Spotify ani Frontier Smart. Ten tekst jest
szkicem do ręcznego odbioru i korekty użytkownika.
