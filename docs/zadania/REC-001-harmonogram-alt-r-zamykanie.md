# REC-001 — harmonogram, Alt+R i bezpieczne zamykanie

Status: **W trakcie**

## Zgłoszenie

18.10.2026 użytkownik widział pustą listę `Alt+R`, ale `Alt+F4` prawidłowo
odmówił zamknięcia z komunikatem o trwającym nagrywaniu. Użytkownik zezwolił
na zatrzymanie nagrania, zamknięcie, kompilację, instalację i ponowne
uruchomienie AMC.

## Ustalenia diagnostyczne

- Host rzeczywiście nagrywał stację „Katedra”; nie był to fałszywy alarm
  blokady zamknięcia.
- Jednorazowy plan ustawiony na 20:42 wystartował po uruchomieniu AMC o 20:43.
- Po zatrzymaniu host wyłączył wykonany plan tylko w pamięci procesu.
- Interfejs zapisał historię nagrania, ale nie pobrał i nie utrwalił
  efektywnego stanu harmonogramu. Przy kolejnym uruchomieniu mógł więc
  ponownie wysłać stary aktywny termin.
- `Alt+R` i blokada zamknięcia pytają ten sam host o pełną migawkę. Pusta
  lista mogła wystąpić w krótkim oknie pomiędzy startem interfejsu a
  uruchomieniem zaległego planu; wymaga to testu po wdrożeniu poprawki.

## Zakres poprawki

1. Po zakończeniu, zatrzymaniu lub błędzie zaplanowanego nagrania pobrać
   pełny stan harmonogramów z hosta.
2. Utrwalić w prywatnym stanie wxPython wyłączenie planu jednorazowego albo
   następny termin planu cyklicznego.
3. Utrwalać także normalizację zaległego planu otrzymaną podczas startowej
   synchronizacji.
4. Nie tworzyć prywatnej kopii niezmienionych harmonogramów z profilu.
5. Zachować bezpieczną blokadę `Alt+F4`, gdy host potwierdza aktywne
   nagrywanie albo nie pozwala wiarygodnie odczytać jego stanu.

## Kryteria akceptacji

- wykonany plan jednorazowy zostaje zapisany jako wyłączony;
- plan cykliczny zachowuje termin przesunięty przez host;
- ponowne uruchomienie nie uruchamia ponownie zużytego terminu;
- ręczne nagranie nie powoduje zbędnej synchronizacji harmonogramów;
- `Alt+R` pokazuje aktywne nagranie po zdarzeniu startu;
- kompilacja, testy automatyczne i próba uruchomienia przechodzą poprawnie.

## Wynik

Do uzupełnienia po testach i instalacji.
