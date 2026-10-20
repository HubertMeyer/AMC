# REC-001 — harmonogram, Alt+R i bezpieczne zamykanie

Status: **Pierwotna poprawka zrobiona; korekta zachowania pliku po zerwaniu
strumienia gotowa w źródłach, teście i kompilacji, czeka na instalację**

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
- 20.10.2026 ręczne nagrywanie stacji „Poznań” rozpoczęło się prawidłowo o
  11:22:15. O 12:04:44 serwer zakończył strumień; dwie próby ponownego
  połączenia odrzuciły dekodery. AMC bezpiecznie domknął plik o 12:04:46:
  istnieje, ma 40 637 231 bajtów i około 42 minuty materiału. Gdy użytkownik
  później zatrzymał zadanie, nieaktywny już potok zwrócił pustą ścieżkę, więc
  koordynator błędnie zgłosił brak pliku i zapisał zero plików w historii.

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

## Materiał do dokumentacji użytkownika

- Zerwanie odbioru stacji nie usuwa dźwięku zapisanego przed awarią. Jeżeli
  AMC zdążyło utworzyć i domknąć niepusty plik, zatrzymanie nagrania zachowuje
  go jako ukończony plik i umieszcza w Historii nagrywania.
- Pusty plik roboczy nie jest przedstawiany jako poprawne nagranie.
- Sam odbiór stacji nadal może się zakończyć, gdy serwer odrzuci wszystkie
  próby ponownego połączenia; poprawka dotyczy zachowania już nagranego
  materiału i prawdziwego wyniku w historii.

## Uzasadnienie i decyzje

- Docelowa ścieżka nagrania jest unikatowa i zostaje ustalona przed startem
  kodera. Gdy backend po awarii nie ma już aktywnego potoku i zwraca brak
  ścieżki, koordynator może bezpiecznie uznać dokładnie ten oczekiwany plik,
  ale tylko jeśli plik rzeczywiście istnieje i ma co najmniej jeden bajt.
- Korekta użytkownika z 20.10.2026 uzupełnia wcześniejszą realizację REC-001:
  udane zapisanie pliku ma pierwszeństwo przed późniejszym technicznym brakiem
  ścieżki z już zwolnionego potoku.

## Testy i wynik

- Test regresji odtwarza backend, który po awarii zwraca brak ścieżki mimo
  istniejącego, niepustego pliku. Potwierdzono zwrot właściwej ścieżki,
  dokładnie jeden wpis ukończonego pliku i wyczyszczenie bieżącej ścieżki.
- Ten sam test potwierdza, że plik zerowej długości nie trafia do historii.
- Kompilacja Release projektu Windows SmokeTests: zaliczona, 0 ostrzeżeń i 0
  błędów. Ukierunkowany przebieg zakończył się komunikatem „OK: plik zapisany
  przed awarią strumienia pozostaje w historii”.
- Odczyt dziennika i pliku Poznania był diagnostyką istniejących danych;
  pliku użytkownika nie zmieniano ani nie przenoszono.

## Znane ograniczenia

- Istniejący błędny wpis Poznania nie został zmieniony podczas działania AMC.
  Sam plik jest dostępny na dysku, ale automatyczna naprawa historycznego wpisu
  wymaga osobnej, bezpiecznej migracji danych albo ręcznego odbioru.
- Poprawka nie zwiększa liczby prób ponownego połączenia i nie gwarantuje, że
  zewnętrzny serwer radia wznowi transmisję.

## Wersja i commit

- Zachowanie opublikowanego pliku po zerwaniu strumienia: commit `4d87189e`
  (`fix(amc): ujednolic klawisze i zachowaj nagranie po awarii`). Kod, test i
  kompilacja są potwierdzone. Instalacja i uruchomienie tej korekty jeszcze nie
  zostały wykonane.
