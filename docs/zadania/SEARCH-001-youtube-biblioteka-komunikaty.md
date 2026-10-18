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
   materiał. Potwierdzenie ma wymienić kolekcję `Media internetowe`, aby było
   wiadomo, gdzie znaleźć zapisany film.
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

### Korekta po odbiorze Spotify — 18 października 2026

Użytkownik potwierdził, że w wyszukiwarce Spotify `Ctrl+Shift+L` nie daje
czytelnego skutku, a ogłoszenie nazwy głównego okna nadal może przesłonić
operację. Przyczyna jest analogiczna do pierwotnego błędu YouTube: bezpośrednie
wykonanie bez zamykania wyszukiwarki ograniczono wcześniej tylko do Podcastów
i YouTube. Rozszerzamy ten sam kontrakt fokusu i komunikatów na katalog
Spotify oraz TIDAL. Dla utworu lub odcinka polecenie podaje wprost właściwy
skrót `Ctrl+Shift+U`, zgodnie ze wspólnym kontraktem TIDAL/Spotify; nie może
pozostać bez komunikatu.

- Data rozpoczęcia i wdrożenia: 18 października 2026
- Przyczyna: `SearchDialog` zamykał okno modalne przed wykonaniem
  asynchronicznego zapisu i przed wyborem pojedynczej relacji. Fokus wracał
  wtedy do głównego okna, dlatego NVDA ogłaszał „AMC Python” i przesłaniał
  wynik operacji.
- Rozwiązanie: `Ctrl+Shift+L` dla publicznego wyniku Podcastów i YouTube
  wykonuje zapis bez zamykania wyszukiwarki. Komunikaty przygotowania, sukcesu
  i błędu są kierowane do aktywnego regionu wyszukiwarki. Sukces wymaga flagi
  `added` albo `restored` z hosta. Prawa strzałka zawsze pokazuje relacje w
  drugiej liście tego samego okna, również gdy istnieje tylko jedna relacja.
- Zmienione pliki: `wxlite/amc_wx_lite/gui.py`,
  `wxlite/tests/test_search_gui_navigation.py` oraz niniejszy rejestr.
- Commit implementacji: `e57cfc2480467939c751280fa2d6d64ac7ceaa81`.
- Testy ukierunkowane: `38 passed`.
- Testy regresji pomocy, palety, skrótów i zapisu profilu: `85 passed`.
- Pełny odbiór: `1714 passed, 110 skipped, 11 subtests passed`.
  Dodatkowo wszystkie trzy projekty wykonywalne zostały opublikowane, a
  manifest i sumy SHA-256 paczki oraz instalacji przeszły kontrolę.
- Pomoc i paleta: istniejące polecenie `Ctrl+Shift+L` w `Ctrl+F1`, menu i
  `Ctrl+Shift+K` zostało zachowane i objęte testem regresji. Szczegółowa pomoc
  listy wyników opisuje teraz prawą strzałkę i `Ctrl+Shift+L`.
- Wersja instalacji:
  `2026.10.18-e57cfc2480467939c751280fa2d6d64ac7ceaa81-3dc84e49`.
  Uruchomiona ze stałej instalacji `D:\Projekty Codex\AMC Python\AMC.exe`.
- Do odbioru z NVDA: wyszukać kanał YouTube, nacisnąć prawą strzałkę,
  wrócić lewą, następnie nacisnąć `Ctrl+Shift+L`. Potwierdzić brak
  wtórnego „AMC Python”, pozostanie fokusu na wyniku i obecność kanału po
  ponownym otwarciu Biblioteki.

### Korekta widoczności zapisu YouTube — 18 października 2026

Odczyt implementacji i bieżącej bazy potwierdził dwa niezależne źródła
niejasności:

- zbiorcza Biblioteka podcastów i kanałów jest obecnie czytana według pola
  `ordinal`, czyli w kolejności własnej, a nie alfabetycznie ani według
  ostatniego dodania;
- pojedynczy film YouTube jest prawidłowo zapisywany jako odcinek we wspólnej
  pozycji `Media internetowe`, natomiast wcześniejszy komunikat podawał tylko
  tytuł filmu i nie wskazywał tej pozycji;
- po zapisie z modalnej wyszukiwarki lista Biblioteki pod spodem nie była
  odświeżana ani ustawiana na zwróconym `subscriptionId`.

W bieżącej bibliotece kontrola tylko do odczytu wykazała 302 źródła, a
`Media internetowe` znajdowały się na pozycji 287. To wyjaśnia, dlaczego
poprawnie zapisany film był praktycznie niewidoczny bez filtrowania.

Poprawka:

1. Film otrzymuje komunikat „Dodano do Biblioteki, Media internetowe: nazwa”
   albo „Materiał jest już w Bibliotece, Media internetowe: nazwa”.
2. Po zapisie kanału, podcastu lub filmu widoczna Biblioteka jest odświeżana
   bez dodatkowej mowy i bez odbierania fokusu wyszukiwarce.
3. Zwrócony przez host identyfikator źródła staje się zaznaczeniem listy, więc
   po zamknięciu wyszukiwania użytkownik trafia na dodany kanał albo na
   `Media internetowe`, niezależnie od ich pozycji w kolejności własnej.
4. Osobne sortowanie listy źródeł zapisano jako zadanie `POD-001`.

- Testy ukierunkowane po korekcie: `84 passed`.
- Commit korekty widoczności: `74cab87ec05e2f25e45e253f0fceae93efdcaff3`.
- Pełny odbiór po obu korektach: `1723 passed, 110 skipped, 11 subtests
  passed`; kompilacja projektów .NET zakończona bez ostrzeżeń i błędów.
- Zainstalowana kompilacja:
  `2026.10.18-74cab87ec05e2f25e45e253f0fceae93efdcaff3-a3214a5e`.
  Uruchomiona 18 października 2026 ze stałej instalacji
  `D:\Projekty Codex\AMC Python\AMC.exe`.
- Odbiór ręczny z NVDA pozostaje otwarty: sprawdzić osobno kanał YouTube,
  pojedynczy film kierowany do `Media internetowe` i wynik Spotify.
