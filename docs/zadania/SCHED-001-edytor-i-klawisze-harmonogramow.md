# SCHED-001 — edytor i klawisze harmonogramów

## Status

Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA.

## Cel

Uprościć obsługę harmonogramów wyłącznie klawiaturą i zapewnić jednoznaczne,
krótkie komunikaty NVDA. To zadanie nie dotyczy naprawionej już trwałości
wykonanych planów z `REC-001`; obejmuje listę harmonogramów oraz pola edytora.

## Ustalony zakres listy

- `Spacja` — włącza lub wyłącza zaznaczony harmonogram i mówi nowy stan.
- `Enter` — otwiera edycję zaznaczonego harmonogramu.
- `Ctrl+D` — tworzy kopię zaznaczonego harmonogramu i otwiera ją do edycji,
  bez ryzyka uruchomienia dwóch identycznych aktywnych planów przed zapisem.
- `Strzałka w lewo` — czyta krótki stan: włączony lub wyłączony oraz najbliższy
  termin wykonania. Nie zmienia zaznaczenia ani ustawień.
- `Strzałka w prawo` — czyta pełne szczegóły zaznaczonego planu bez otwierania
  edytora: nazwa, źródło, data lub powtarzanie, godzina, czas trwania lub czas
  zakończenia, format i folder docelowy. Pomija pola, które nie mają znaczenia
  dla danego rodzaju harmonogramu i nie powtarza nazwy listy.
- `Ctrl+Enter` pozostaje bez zmiany do osobnej decyzji. Otwieranie folderu
  nagrania zostanie zaprojektowane razem z integracją powłoki Windows.

## Ustalony zakres edytora daty i czasu

1. Data ma być kontrolką segmentową dostępną dla NVDA, a nie zwykłym polem
   tekstowym wymagającym ręcznego wpisania `YYYY-MM-DD`.
2. `Strzałka w lewo` i `Strzałka w prawo` przechodzą między segmentami dnia,
   miesiąca i roku. `Strzałka w górę` i `Strzałka w dół` zwiększają lub
   zmniejszają aktywny segment, zawsze pozostawiając prawidłową datę.
3. Czas rozpoczęcia działa analogicznie dla godzin i minut.
4. Wpisanie cyfr zastępuje aktywny segment. Po wpisaniu kompletnej wartości
   fokus przechodzi do następnego segmentu; nie wolno przeskakiwać po jednej
   cyfrze, jeśli wartość może mieć jeszcze drugą cyfrę.
5. NVDA przy wejściu i każdej zmianie mówi nazwę segmentu oraz jego wartość,
   na przykład „dzień 18”, „miesiąc październik”, „godzina 9”, „minuty 25”.
   Nie ujawnia nazw klas, właściwości ani surowych wartości modelu.
6. Przy tworzeniu harmonogramu zaznaczony dzień tygodnia wynika z wybranej
   daty nagrania, a nie z dnia, w którym zapisano harmonogram. Zmiana daty ma
   aktualizować tę wartość, dopóki użytkownik sam nie zmieni dni powtarzania.
7. Czas rozpoczęcia musi być pełny i prawidłowy. Inaczej działa czas trwania:
   puste godziny oznaczają zero godzin, więc wpisanie samych `25` w polu minut
   oznacza 25 minut. Pusta cała długość nie może zostać po cichu odczytana jako
   niezamierzone zero — edytor ma podać zrozumiały komunikat albo zastosować
   jawnie opisany tryb zakończenia.
8. Po `Zapisz` i `Anuluj` fokus wraca na ten sam element listy. Wielokrotne
   otwieranie edytora ma zachować poprawne nazwy dostępności i wybór segmentu.

## Kryteria akceptacji

- Wszystkie opisane gesty działają w harmonogramach Radia i w kolejnych
  sesjach korzystających ze wspólnego modelu harmonogramu.
- Testy obejmują końce miesięcy, lata przestępne, przejście 23:59/00:00,
  wartości wpisywane cyframi, puste godziny czasu trwania i zmianę daty po
  ręcznej zmianie dni powtarzania.
- Test NVDA obejmuje pierwsze otwarcie, wszystkie strzałki, wpisywanie cyfr,
  `Zapisz`, `Anuluj` i ponowne otwarcie.
- Pomoc `Ctrl+F1` i paleta `Ctrl+Shift+K` opisują te same skróty i komunikaty.

## Prace i weryfikacja

- Data rozpoczęcia: 19.10.2026.
- Data zakończenia kodu i testów źródłowych: 19.10.2026.
- Zmienione pliki: `radio_schedule_dialogs.py`, `schedule_segments.py`,
  `shortcuts.py`, testy segmentów, klawiatury harmonogramów i palety poleceń.
- Testy ukierunkowane: 63 zaliczone.
- Pełna regresja `wxlite/tests`: 1748 zaliczonych, 110 pominiętych,
  11 podtestów zaliczonych.
- Commit źródłowy: `689a8c77` — „Przebuduj dostępny edytor harmonogramów”.
- Zainstalowana kompilacja: jeszcze nie powstała; przed 02:00 trwało nagranie.

## Materiał do dokumentacji użytkownika

Listę harmonogramów otwiera `Ctrl+Shift+H`. Góra i dół wybierają plan.
`Spacja` włącza albo wyłącza wybrany plan i po udanym zapisie mówi jego nowy
stan. `Enter` otwiera edycję. `Ctrl+D` przygotowuje osobną, domyślnie wyłączoną
kopię i najpierw otwiera ją w edytorze; kopia trafia do harmonogramu dopiero po
wybraniu „Zapisz”. `Ctrl+Enter` nie został zmieniony. `Insert` nadal tworzy
nowy plan, a `Delete` usuwa go po potwierdzeniu.

Na liście lewa strzałka podaje tylko stan „włączony” albo „wyłączony” oraz
najbliższy termin. Prawa strzałka podaje pełny opis: nazwę planu, stację,
jednorazową datę albo regułę powtarzania, godzinę, długość, format i folder.
Oba klawisze są informacyjne — nie zmieniają zaznaczenia ani planu.

Data rozpoczęcia składa się z segmentów dnia, miesiąca i roku. Czas rozpoczęcia
ma segmenty godziny i minut. Lewa i prawa strzałka przechodzą między segmentami,
a góra i dół zmieniają bieżący segment, zawsze pozostawiając prawidłową datę
lub czas. Można wpisywać cyfry: kontrolka czeka na drugą cyfrę tylko wtedy, gdy
z wpisanego początku może jeszcze powstać prawidłowa wartość. Po kompletnej
wartości przechodzi do następnego segmentu.

Nazwy dostępnościowe są użytkowe, na przykład „dzień 18”, „miesiąc
październik”, „rok 2026”, „godzina 9” i „minuty 25”. Nie zawierają nazw klas,
pól modelu ani technicznych identyfikatorów.

W nowym planie zaznaczony dzień tygodnia podąża za wybraną datą. Po ręcznej
zmianie listy dni AMC zachowuje wybór użytkownika i kolejne zmiany daty już go
nie nadpisują. W planie już istniejącym zapisane dni także nie są automatycznie
zmieniane.

Godziny długości nagrania wolno pozostawić puste — oznacza to zero godzin.
Jeżeli w minutach zostanie wpisane `25`, długość wynosi 25 minut. Całkowicie
pusta lub zerowa długość nie jest przyjmowana; edytor mówi „Podaj długość
nagrania; puste godziny oznaczają zero”. Po „Zapisz” i po „Anuluj” fokus wraca
na ten sam plan listy.

Menu i paleta `Ctrl+Shift+K` nazywają wejście „Harmonogram nagrywania” i podają
skrót `Ctrl+Shift+H`. Takiej samej nazwy używa pomoc klawiatury `Ctrl+F1`.
Wewnątrz okna widoczny i dostępny opis wymienia klawisze listy.

## Uzasadnienie i decyzje

- Segmenty opierają się na osobnym modelu kalendarza i czasu. Dzięki temu
  końce miesięcy, luty w roku przestępnym oraz granice 23:59/00:00 nie zależą
  od swobodnego tekstu.
- Zmiana miesiąca lub roku ścina dzień wyłącznie do ostatniego prawidłowego
  dnia, na przykład 31 stycznia przechodzi na 28 albo 29 lutego.
- Model wartości jest oddzielony od tekstu dla NVDA. Do dostępnej nazwy trafia
  wyłącznie polska nazwa segmentu i jego wartość.
- `Ctrl+D` nie zapisuje drugiego aktywnego planu przed pokazaniem edytora.
  Pierwszy stan kopii jest wyłączony, a anulowanie nie zmienia harmonogramu.
- Lewa i prawa strzałka korzystają z aktualnego, bezpiecznie oczyszczonego
  modelu planu; etykieta hosta nie jest parsowana z powrotem na dane.
- Korekta użytkownika z 18.10.2026 zastępuje wcześniejszy wariant ręcznego
  wpisywania daty `RRRR-MM-DD` i czasu `GG:MM`.
- Korekta użytkownika z 18.10.2026 potwierdza, że `Ctrl+Enter` pozostaje bez
  zmian, a otwieranie folderu będzie osobnym zadaniem integracji z powłoką.

## Testy i wynik

Testy modelu obejmują:

- koniec lutego w roku przestępnym i zwykłym;
- przejście 31. dnia do krótszego miesiąca;
- zmianę dnia na końcu miesiąca;
- granice godziny i minut 23:59/00:00;
- cyfry, prefiksy jedno- i dwucyfrowe oraz odrzucenie wartości spoza zakresu;
- puste godziny długości, same minuty i całkowicie pustą długość;
- krótką informację pod lewą i pełną pod prawą strzałką;
- otwarcie wyłączonej kopii przez `Ctrl+D` przed zapisem;
- brak przypisania `Ctrl+Enter`;
- dostępne nazwy segmentów bez reprezentacji obiektów;
- wspólną nazwę i skrót w palecie oraz pomocy;
- trwałość harmonogramów i ochronę `REC-001` w pełnej regresji.

Wynik 19.10.2026: 63/63 testy ukierunkowane oraz 1748 zaliczonych,
110 pominiętych i 11 zaliczonych podtestów w ówczesnym pełnym
`wxlite/tests`. Po połączeniu nocnych etapów pełna regresja dała **1754
zaliczone, 110 pominiętych, 11 podtestów**. Kompilacja Release, kontrola paczki,
instalacja i uruchomienie również zakończyły się powodzeniem.

Ponowna bramka przed zaplanowanym restartem 19.10.2026 objęła model daty i
czasu, klawiaturę listy, zapis planów oraz integrację z menu: razem z bieżącymi
regresjami **204 testy zaliczone**. Nie wprowadzano drugiej implementacji —
harmonogramy są już w aktualnym źródle i mają wejść do kolejnej instalacji
zbiorczej po kontroli aktywnego nagrywania.
Pełna regresja wxPython po połączeniu bieżących korekt: **1837 zaliczonych,
110 pominiętych i 11 podtestów zaliczonych**.

## Znane ograniczenia

- Nie wykonano jeszcze rzeczywistego odsłuchu NVDA. Należy sprawdzić pierwsze
  wejście, każdą strzałkę, cyfry, zapis, anulowanie i ponowne otwarcie.
- Segmenty używają natywnych pól liczbowych wxPython. Ostateczny odbiór musi
  potwierdzić, że dana wersja NVDA nie powtarza wartości po dostępnej nazwie.
- Pełny opis prawej strzałki podaje długość, nie osobny czas zakończenia.
- Zmiany dotyczą harmonogramów Radia, bo tylko ta sesja ma obecnie działający
  wspólny model harmonogramu. Kolejna sesja ma go użyć zamiast kopiować dialog.
- `Ctrl+Enter` i otwieranie folderów nie należą do tego etapu.
- Kod został zainstalowany, ale ręczny odbiór wszystkich segmentów z NVDA
  nadal pozostaje do wykonania; automatyczne etykiety nie zastępują odsłuchu.

## Wersja i commit

- Źródła i testy: commit `689a8c77`.
- Kompilacja: Release, zaliczona bez ostrzeżeń i błędów; pełna regresja po
  połączeniu etapów: **1754 zaliczone, 110 pominiętych, 11 podtestów**.
- Instalacja: `2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`,
  manifest, sumy SHA-256 i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: niewykonana i niedozwolona w tej pracy nocnej.
