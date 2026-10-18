# REC-001 — harmonogram, Alt+R i bezpieczne zamykanie

Status: **Zrobione**

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

- Implementacja: commit lokalny
  `de8d10ed1bd0eb1f22e54df3f464170331f8fb55`.
- Testy ukierunkowane: `58 passed`.
- Pełne testy wxPython: `1717 passed, 110 skipped, 11 subtests passed`.
- Zainstalowana kompilacja:
  `2026.10.18-de8d10ed1bd0eb1f22e54df3f464170331f8fb55-02e9b980`.
- Instalację wykonano początkowo z `-NoLaunch`, aby stary termin 20:42
  zdążył wyjść poza piętnastominutowe okno wykonania i nie rozpoczął
  drugiego nagrania przed pierwszym uruchomieniem poprawionej wersji.
- Po pierwszym uruchomieniu poprawionej wersji oba zaległe jednorazowe plany
  „Katedra” zostały trwale zapisane jako wyłączone. W logu nie pojawiło się
  nowe nagranie.
- Próba interfejsu: `Alt+R` pokazał pustą listę i „0 elementów”; `Alt+F4`
  zamknął AMC bez komunikatu o trwającym nagrywaniu.
- Po próbie zamknięcia AMC uruchomiono ponownie z
  `D:\Projekty Codex\AMC Python\AMC.exe`. Potwierdzono proces prywatnego
  runtime'u i tytuł okna kompilacji z 18.10.2026, 20:54.

## Wniosek dotyczący pierwotnego zgłoszenia

Blokada zamknięcia nie była fałszywa: nagranie zaczęło się tuż po uruchomieniu
interfejsu z zaległego harmonogramu. Pusta lista `Alt+R` pochodziła z krótkiego
okna czasowego przed startem nagrania albo z odczytu wykonanego zanim zdarzenie
startu dotarło do interfejsu. Usunięto przyczynę ponownego odtwarzania tej
sytuacji przy kolejnych uruchomieniach: wykonany termin nie wróci już jako
aktywny.
