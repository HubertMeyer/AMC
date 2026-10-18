# SCHED-001 — edytor i klawisze harmonogramów

## Status

Oczekuje.

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

- Data rozpoczęcia:
- Data zakończenia:
- Zmienione pliki:
- Testy:
- Commit:
- Zainstalowana kompilacja:
