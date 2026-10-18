# SEARCH-001 — YouTube, Biblioteka i komunikaty wyszukiwania

- Status: `W trakcie`
- Utworzono: 18 października 2026
- Obszar: wyszukiwanie Podcastów i YouTube, Biblioteka, NVDA i fokus
- Polecenie uruchamiające: `Uruchom zadanie SEARCH-001`

## Zgłoszenie użytkownika

W wynikach wyszukiwania co najmniej dla YouTube nie można dodać kanału do
Biblioteki skrótem `Ctrl+Shift+L`. Dodatkowo po prawej strzałce w wynikach oraz
po `Ctrl+Shift+L` pojawia się ogólny komunikat „AMC Python”, który przesłania
właściwą informację, w szczególności „Dodano do Biblioteki”.

Te dwa objawy należy badać razem, ponieważ mogą wynikać z błędnego routingu
tożsamości wyniku, niepotrzebnego odświeżenia głównego okna albo ponownego
ogłoszenia jego tytułu po zmianie fokusu.

## Oczekiwane zachowanie

1. Na wyniku będącym kanałem YouTube `Ctrl+Shift+L` dodaje lub usuwa właśnie
   ten kanał jako źródło Biblioteki.
2. Na pojedynczym filmie obowiązuje istniejący kontrakt `Media internetowe`;
   nie wolno przypadkiem zamienić filmu w cały kanał ani kanału w pojedynczy
   materiał.
3. Sukces jest ogłaszany dopiero po potwierdzeniu zapisu: „Dodano do
   Biblioteki: <nazwa>” albo „Usunięto z Biblioteki: <nazwa>”.
4. Po potwierdzeniu nie może pojawić się wtórny komunikat „AMC Python”, który
   zagłusza wynik operacji.
5. Prawa strzałka podaje wyłącznie właściwą relację, akcję lub informację dla
   zaznaczonego wyniku. Sam tytuł aplikacji nie jest komunikatem funkcji.
6. Fokus pozostaje na logicznie tym samym wyniku, a Escape wraca do właściwego
   miejsca wyszukiwania.
7. Błąd API, brak obsługiwanej tożsamości albo samo przeładowanie listy nie
   mogą zostać ogłoszone jako dodanie do Biblioteki.

## Zakres sprawdzenia

- wyniki: kanał YouTube, film YouTube, podcast i odcinek podcastu;
- wyszukiwanie globalne i każdy widok korzystający z tego samego modelu wyniku;
- routing po `session_id`, typie i identyfikatorze dostawcy;
- prawa strzałka, `Ctrl+Shift+L`, Enter, Escape i powrót fokusu;
- kolejność komunikatów własnych AMC, zdarzeń fokusu i odczytu NVDA;
- trwałość zapisu po ponownym otwarciu Biblioteki oraz po odświeżeniu źródeł.

## Pomoc i paleta poleceń

Jeżeli naprawa zmieni dostępność albo opis polecenia, ten sam warunek ma zostać
odzwierciedlony w pomocy `Ctrl+F1`, menu kontekstowym i palecie `Ctrl+Shift+K`.
Nie dodajemy drugiego skrótu do tej samej operacji.

## Kryteria akceptacji

1. Test automatyczny wykazuje rzeczywistą zmianę Biblioteki dla kanału, a nie
   tylko obecność tekstu sukcesu.
2. Test rozróżnia kanał od filmu i sprawdza właściwy zapis po przeładowaniu.
3. Test kolejności ogłoszeń nie dopuszcza wtórnego „AMC Python” po właściwym
   komunikacie prawej strzałki lub `Ctrl+Shift+L`.
4. Test z NVDA obejmuje początkowe zaznaczenie, ruch po wynikach, wykonanie
   operacji, zachowanie fokusu i ponowne otwarcie wyszukiwarki.
5. Kontrola regresji obejmuje Podcasty oraz inne usługi używające
   `Ctrl+Shift+L`.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data rozpoczęcia i zakończenia:
- Przyczyna:
- Zmienione pliki:
- Testy i ich wyniki:
- Pomoc i paleta:
- Wersja instalacji:
