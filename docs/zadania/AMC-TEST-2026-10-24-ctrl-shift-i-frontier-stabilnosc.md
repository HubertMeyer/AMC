# AMC Test — zbiorcze transmisje YouTube i stabilność Frontier Smart

- Data: 24 października 2026
- Status: źródła i pełna regresja zaliczone; trwa kontrolowana budowa i
  instalacja AMC Test
- Gałąź: `integration/amc-test-20261023-late`
- Baza przed zmianą: `044c9a5ce5146145c9429eb9755ccaf7bed6dd5f`
- AMC Public i GitHub: bez zmian

## Zachowanie użytkowe

`Ctrl+Shift+I` otwiera zbiorczą listę transmisji trwających i zaplanowanych z
wybranych kanałów YouTube. Pierwsze użycie bez wyboru otwiera dostępne okno
`Kanały zbiorczej listy transmisji`. Użytkownik może wybrać do 20 kanałów.
Polecenie występuje w tym samym modelu wykonania, menu Widok, menu
kontekstowym, palecie `Ctrl+Shift+K`, pomocy `Ctrl+F1` i pełnej pomocy.

Na liście działają Enter, `Ctrl+Shift+C`, `F5`, `Ctrl+R`, `Shift+R`,
Backspace i Escape. Nagranie bieżącej transmisji używa jej adresu, a
harmonogram stabilnego adresu kanału `/live`. Lista nie działa w tle i nie
skanuje wszystkich subskrypcji.

Frontier Smart scala szybką serię regulacji głośności. Wysyła bieżącą wartość
i najwyżej jedną, najnowszą wartość oczekującą. Timer odczytu stanu nie nakłada
się na trwające polecenie. Zmiana powstała po rzeczywistym odbiorze, w którym
radio wykonywało dwuminutową kolejkę starych żądań i stało się chwilowo
niesterowalne.

## Komunikaty i dostępność

- `Najpierw wybierz kanały zbiorczej listy transmisji` prowadzi do selektora.
- Okno wyboru mówi wyłącznie nazwy kanałów, liczbę wybranych i limit 20.
- Wynik podaje liczbę transmisji na żywo, zaplanowanych oraz ewentualnych
  kanałów, których nie udało się sprawdzić.
- Próba `Ctrl+R` na transmisji przyszłej mówi, że nie jest jeszcze na żywo.
- Nakładające się polecenie Frontier Smart mówi:
  `Poprzednie polecenie Frontier Smart jeszcze trwa`.
- Po błędzie głośności suwak wraca do ostatniej potwierdzonej wartości.

## Różnice trybów i ograniczenia

- Zbiorcza lista wymaga skonfigurowanego konta YouTube w profilu AMC Test.
- Wybrane kanały są prywatnym ustawieniem AMC Test i częścią pełnej kopii
  danych; token Google pozostaje w hoście C#.
- Limit 20 i jawne uruchomienie chronią dzienny limit oficjalnego API.
- Trwałe cotygodniowe nagranie nadal najlepiej planować na dynamicznej stacji
  Radia; `Shift+R` z listy służy także pojedynczym zaplanowanym wydarzeniom.
- Stabilność Frontier wymaga ponownego testu na prawdziwym Teufelu; test
  automatyczny potwierdza algorytm, ale nie zachowanie firmware.

## Testy i rzeczywiste wyniki

- celowany zestaw po synchronizacji: **273 zaliczone testy i 2 podtesty**;
- pełna regresja `wxlite`: **2032 zaliczone, 111 pominiętych, 13 podtestów
  zaliczonych**, zero błędów, 153,04 s;
- `git diff --check`: bez błędów;
- test Frontier potwierdza, że seria `25, 30, 35` wysyła tylko `25` i `35`;
- testy parytetu potwierdzają wspólne nazwy, skróty i widoczność w menu,
  kontekście, palecie i pomocy;
- ręczny odbiór NVDA, prawdziwego konta YouTube, nagrywania i Teufela:
  oczekuje po instalacji.

## Zmienione miejsca

- `wxlite/amc_wx_lite/gui.py` — selektor, zbiorczy widok, nagrywanie,
  harmonogram i scalanie poleceń Frontier;
- `shortcuts.py`, `menu_model.py`, `navigation.py` — jeden kontrakt poleceń;
- `youtube_live.py`, `list_model.py`, `state_store.py`, `full_backup.py` —
  dane, sortowanie, trwałość i kopia;
- `radio_schedule_dialogs.py`, `transient_preview_policy.py` — termin
  początkowy i bezpieczny powrót;
- sześć modułów testowych — widok, trwałość, parytet i Frontier.

## Wersja, commit i instalacja

Dokładny commit, wersja, identyfikator paczki, wynik kontroli procesów i ścieżka
instalacji zostaną dopisane po zakończeniu kontrolowanej promocji. Samo
przejście testów nie jest przedstawiane jako dowód zbudowania ani instalacji.

## Materiał do instrukcji i listy zmian — projekt

> `Ctrl+Shift+I` pokazuje transmisje na żywo i zaplanowane z wybranych kanałów
> YouTube. Przy pierwszym użyciu wybierz kanały. Enter odtwarza, F5 odświeża,
> Ctrl+R nagrywa trwającą transmisję, a Shift+R otwiera harmonogram.

> Regulacja głośności Frontier Smart nie wysyła już długiej kolejki zmian do
> radia. AMC zachowuje tylko ostatnią wartość wybraną podczas oczekiwania na
> odpowiedź urządzenia.
