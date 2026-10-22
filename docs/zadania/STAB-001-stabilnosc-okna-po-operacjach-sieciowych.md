# STAB-001 — stabilność okna po operacjach sieciowych

## Status

Zrobione 2026-10-23. Incydent z chwilowym brakiem reakcji, zniknięciem okna
i jego ponownym pojawieniem się nie był awarią Pythona ani samoczynnym
restartem po błędzie. W tym samym przedziale trwała kontrolowana promocja
nowszej kompilacji AMC Test: poprzednia instancja przyjęła zwykłe zamknięcie,
instalacja została podmieniona i uruchomiono nowy łańcuch procesów.

Nie potwierdzono ogólnego defektu stabilności wymagającego zmiany źródeł.
Operacje ładowania oraz odświeżania źródeł są wykonywane poza wątkiem GUI,
a długie zadania hosta nie blokują jego kolejki transportowej. Nie zmieniano
logiki Podcastów, YouTube ani Frontier należącej do innych zadań.

## Zachowanie widoczne dla użytkownika

- Nie dodano funkcji, polecenia, skrótu ani nowego komunikatu czytnika ekranu.
- Ponowne uruchomienie launchera tej samej kompilacji aktywuje istniejące okno.
  Instalacja nowszej kompilacji prosi bieżącą instancję o zwykłe zamknięcie,
  podmienia paczkę, sprawdza ją i dopiero wtedy uruchamia nowe okno.
- Diagnoza dotyczy wyłącznie profilu AMC Test. AMC Public zachował osobne
  procesy i stan; nie był instalowany, uruchamiany ani zmieniany.
- Nie wykonano ręcznego odbioru NVDA. Brak nowych komunikatów oznacza, że karta
  nie przypisuje czytnikowi ekranu żadnego niezmierzonego tekstu ani zachowania.

## Zdarzenie i korelacja

- Użytkownik zgłosił, że podczas ładowania źródeł i podcastów AMC na chwilę
  przestał reagować, po czym okno zniknęło i wróciło jak po restarcie.
- O `00:23:29` zapisano manifest nowej instalacji AMC Test. Kontrolowane
  uruchomienia sprawdzające hosta zakończyły się prawidłowo, a o `00:24:09`
  wystartował nowy frontend; sekundę później miał już własny proces hosta.
- Rewizja i identyfikator paczki z manifestu zgadzają się z dokumentacją
  wykonanej tej nocy promocji. Dokumentacja promocji podaje także, że
  poprzednie okno przyjęło normalne zamknięcie i nie było potrzebne wymuszenie.
- Lokalny dziennik AMC Test pokazuje zwykłe starty i zakończenia hosta w tym
  przedziale. Nie zawiera śladu wyjątku ani nieoczekiwanego zakończenia.
- Dziennik aplikacji Windows, historia niezawodności i archiwum raportów WER
  nie zawierają awarii `AMC.exe`, `python.exe` ani hosta w badanym przedziale.
  Dziennik audytu tworzenia i kończenia procesów nie miał pasujących wpisów,
  więc nie stanowi dodatkowego dowodu.
- Po incydencie działał nowy komplet trzech procesów z kanonicznej instalacji
  AMC Test. To wyklucza samo ukrycie i ponowne pokazanie tego samego okna.

## Klasyfikacja hipotez

1. **Awaria Pythona — niepotwierdzona.** Brak wyjątku, WER, wpisu awarii
   aplikacji i śladu niezerowego wyjścia launchera.
2. **Restart launchera/aktualizatora — potwierdzona przyczyna zniknięcia i
   powrotu okna.** Była to zaplanowana promocja AMC Test, a nie automatyczne
   odzyskanie po błędzie.
3. **Zamknięcie i ponowne pokazanie tego samego okna — wykluczone.** Zmieniły
   się manifest instalacji i procesy. Dla tej samej kompilacji launcher tylko
   aktywuje istniejące okno; nie tworzy nowego procesu.
4. **Modalne okno potomne — brak dowodu.** Logi nie rejestrują takiego okna,
   a zmiana procesów wystarcza do wyjaśnienia obserwowanego zachowania.
5. **Blokada wątku GUI przez operację sieciową — niepotwierdzona w kodzie i
   testach izolowanych.** Frontend uruchamia pracę w tle, a wynik dostarcza do
   wx przez `CallAfter`. Odświeżanie i dodawanie źródeł są jawnie wpisane jako
   operacje współbieżne hosta, więc nie stają przed pauzą, statusem ani
   nagrywaniem.
6. **Wyłącznie odebranie fokusu przez inny program — wykluczone jako pełne
   wyjaśnienie.** Zewnętrzna promocja rzeczywiście zamknęła starą i uruchomiła
   nową instancję. Samo przejęcie fokusu nie zmieniłoby procesów ani manifestu.

Ustalenie z 2026-10-23 zastępuje roboczą hipotezę, że operacja sieciowa
spowodowała awarię albo samoczynny restart AMC.

## Zachowanie operacji długich

- `BackgroundRunner` wykonuje pracę poza wątkiem GUI. `StaleResultGate`
  przydziela osobne generacje strumieniom i nie dostarcza wyniku starej
  generacji ani wyniku do zamkniętego okna.
- Zamknięcie frontendu unieważnia oczekujące dostawy przez `cancel_all`, dzięki
  czemu spóźniona odpowiedź nie może odtworzyć starego widoku po zamknięciu.
- Odświeżanie Podcastów i YouTube oraz dodawanie źródła działa poza szeregową
  kolejką hosta. Limit trzech równoległych zadań zapobiega nieograniczonemu
  mnożeniu pracy.
- Klient RSS ogranicza jedną odpowiedź do 20 sekund i 5 MiB. Pobranie jednej
  kolekcji YouTube ma limit 60 sekund i najwyżej 100 elementów. Python ma
  nadrzędny limit oczekiwania na całe odświeżenie biblioteki.
- Po odświeżeniu frontend stosuje wynik tylko do nadal aktywnego widoku i
  odtwarza zaznaczenie przez stabilny identyfikator, nie przez chwilowy indeks.

## Uzasadnienie i decyzje

- Nie wprowadzono poprawki źródłowej, ponieważ jedyna potwierdzona zmiana
  procesu była oczekiwanym skutkiem równoległej promocji AMC Test, a wszystkie
  sprawdzone zabezpieczenia asynchroniczne były już obecne w kompilacji z
  incydentu.
- Nie odtwarzano zdarzenia na działającym AMC Test. Zadanie zabraniało
  zamykania, restartowania i instalowania tej instancji; reprodukcję
  ograniczono do izolowanych testów bez profilu użytkownika.
- Nie kopiowano do repo surowych logów, prywatnych ścieżek profilu, adresów
  źródeł ani danych użytkownika. Karta zawiera wyłącznie zanonimizowaną oś
  czasu i identyfikatory kompilacji.

## Testy i wynik

- Izolowane testy Pythona: `test_async_gate.py`, `test_host_client.py`,
  `test_startup.py`, `test_startup_messages.py`, `test_podcast_refresh.py`
  i `test_podcast_add.py`: **72 zaliczone, 0 nieudanych**.
- Testy launchera i aktualizatora Release: **30 zaliczonych, 0 nieudanych**.
  Obejmują aktywację istniejącego okna dla tej samej kompilacji, bezpieczną
  podmianę dla nowej kompilacji i rozdzielenie instancji profili.
- Izolowany zestaw protokołu `--dispatch`: **1 zestaw zaliczony**. Obejmuje
  barierowy test, że długie zadanie współbieżne nie blokuje statusu ani pauzy,
  ograniczenie liczby takich zadań oraz dalsze działanie po błędzie handlera.
- Sprawdzenie drzewa roboczego po testach: brak zmian w śledzonych plikach.
- Nie wykonano pełnej regresji, pełnego builda aplikacji, instalacji ani
  publikacji. Wyniki testów nie są przedstawiane jako ich odpowiednik.

## Znane ograniczenia

- Brak systemowego zapisu zmian fokusu i okien modalnych oznacza, że nie da się
  odtworzyć każdej krótkiej zmiany fokusu z samej telemetrii po fakcie. Nie
  wpływa to na potwierdzoną zmianę procesu i instalacji.
- Odświeżanie całej biblioteki nie ma osobnego polecenia **Anuluj** w GUI.
  Zamknięcie unieważnia dostarczenie wyniku, a pojedyncze pobrania mają limity,
  lecz sekwencyjny przebieg po wielu źródłach może trwać długo. To ograniczenie
  szczegółowej funkcji Podcastów/YouTube, a nie przyczyna restartu; nie było
  zmieniane w tym zadaniu.
- Nie wykonano ręcznego odbioru NVDA ani rzeczywistego pobierania sieciowego.
  Testy potwierdzają kontrakt kodu i kolejki, nie zachowanie każdej usługi
  zewnętrznej ani wszystkich warunków sieciowych.

## Wersja i commit

- Bazowy `HEAD` diagnozy: `609aa64447c6eb2c8775341157ef243952b61942`.
- Kompilacja działająca po incydencie:
  `2026.10.23-1badabbeeacde3d8853457683ef750d558b3f1fd-7353e273`.
- Zmiany źródeł: brak. Zmieniono wyłącznie tę kartę i rejestr zadań.
- Commit dokumentacji diagnozy zostanie zapisany w końcowym raporcie zadania.
- AMC Test, AMC Public, instalator i publikacja: bez zmian.

## Materiał do dokumentacji użytkownika

Podczas instalowania nowszej kompilacji AMC Test bieżące okno może na krótko
zniknąć. Aktualizator prosi działającą instancję o zwykłe zamknięcie, sprawdza
podmienioną paczkę i uruchamia nowe okno. Taki przebieg jest kontrolowaną
aktualizacją, a nie automatycznym restartem po awarii. Zwykłe ponowne
uruchomienie launchera tej samej kompilacji tylko pokazuje istniejące okno.

Projekt tekstu wymaga korekty i zatwierdzenia użytkownika przed publikacją.

## Roboczy wpis do changelogu

- Diagnostyka incydentu z 23.10.2026 potwierdziła kontrolowaną podmianę AMC
  Test zamiast awarii. Nie wprowadzono zmian funkcjonalnych; testy zachowania
  asynchronicznego, launchera, aktualizatora i kolejki hosta pozostały zielone.
