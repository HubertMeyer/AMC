# PLAY-001 — odtwarzanie losowe klawiszem R

## Status

**W trakcie.** Kod i automatyczna regresja są gotowe. Zadanie czeka na
zbudowanie i kontrolowaną instalację zbiorczego AMC Test oraz ręczny odbiór z
NVDA.

## Zakres i zachowanie użytkowe

- W odtwarzaczu Plików, Podcastów i Spotify klawisz `R` przełącza
  `Odtwarzaj losowo`.
- To samo polecenie jest dostępne w menu Odtwarzanie, menu kontekstowym
  odtwarzacza, palecie poleceń i obu wariantach pomocy klawiaturowej.
- Włączenie i wyłączenie jest wypowiadane odpowiednio jako
  `Odtwarzanie losowe włączone` i `Odtwarzanie losowe wyłączone`.
- Bieżący element pozostaje pierwszy. Losowane są dopiero pozostałe elementy
  źródła, bez duplikatów. Po naturalnym końcu AMC uruchamia następny element
  losowej sekwencji.
- Wyłączenie przywraca pierwotną kolejność bieżącego katalogu, listy odcinków
  albo wyników Spotify.
- Stan jest zapamiętywany osobno dla Plików, Podcastów i Spotify, a ustawienie
  może być objęte eksportem i importem konfiguracji.
- Jawna zapisana lub żywa kolejka, także blok `Odtwórz następne`, ma
  pierwszeństwo i nie jest przestawiana przez losowanie.
- Losowanie działające w tle nie przenosi fokusu z aktualnie oglądanej sesji.

## Różnice między sesjami

- Pliki, Podcasty i Spotify: `R` oznacza `Odtwarzaj losowo` wyłącznie w widoku
  odtwarzacza.
- Radio: istniejące `R` nadal rozpoczyna lub kończy nagrywanie.
- WiiM: istniejące `R` nadal wybiera tryb powtarzania urządzenia.
- TIDAL, Sonos i Frontier Smart: AMC nie przejmuje `R` i nie pokazuje
  niedziałającego polecenia losowania.
- Na listach pojedyncza litera nie jest przechwytywana, dzięki czemu nie psuje
  nawigacji znakowej kontrolki.

## Uzasadnienie i decyzje

- Polecenie zostało dodane do wspólnego modelu akcji. Ten sam identyfikator
  zasila routing klawiatury, menu główne, menu kontekstowe, paletę i pomoc.
- Losowanie dotyczy źródła zwykłego odtwarzania. Nie zmienia świadomie ułożonej
  kolejki użytkownika.
- Zapis przechowuje tylko jawne wartości `true` dla trzech wspieranych sesji;
  nieznane sesje i wartości techniczne są odrzucane.
- W menu zmieniono wyłącznie klawisz dostępu pozycji `Prędkość normalna` z
  `r` na `ć`, aby dwa widoczne polecenia nie miały tego samego klawisza
  dostępu. Skrót `Ctrl+.` pozostał bez zmian.

## Materiał do dokumentacji użytkownika — projekt

W odtwarzaczu Plików, Podcastów lub Spotify naciśnij `R`, aby włączyć albo
wyłączyć odtwarzanie losowe. AMC potwierdzi zmianę głosem. Możesz też użyć
pozycji `Odtwarzaj losowo` w menu Odtwarzanie lub w menu kontekstowym
odtwarzacza. Bieżący utwór lub odcinek nie zmieni się natychmiast; losowa
kolejność obowiązuje od następnego elementu. Zapisane i żywe kolejki zachowują
własną kolejność.

## Projekt wpisu do opisu zmian

- Dodano trwałe `Odtwarzaj losowo (R)` w odtwarzaczach Plików, Podcastów i
  Spotify, ze wspólną obsługą menu, menu kontekstowego, palety poleceń i pomocy
  klawiaturowej.
- Losowanie zachowuje bieżący element, nie przestawia jawnych kolejek i może
  kontynuować odtwarzanie w tle bez przenoszenia fokusu.

## Zmienione miejsca

- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/navigation.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/state_store.py`
- `wxlite/amc_wx_lite/full_backup.py`
- `wxlite/tests/test_playback_shuffle.py`
- testy wspólnego menu, GUI, Radia i stanu

## Testy i wynik

- Testy celowane nowej funkcji: **6 zaliczonych**.
- Rozszerzona regresja nawigacji, menu, palety, GUI, zapisu stanu i transportu:
  **205 zaliczonych**.
- Regresja menu kontekstowego i GUI po jej dodaniu: **86 zaliczonych**.
- Po wykryciu niezgodności formatu pełnej kopii, starszych atrap GUI i starego
  oczekiwania testu Radia poprawiono kod oraz kontrakt; ponowienie:
  **8 zaliczonych**.
- Pełna regresja wxPython 23.10.2026: **2010 zaliczonych, 111 pominiętych,
  11 podtestów zaliczonych** w 133,63 s.

## Znane ograniczenia i odbiór ręczny

- Losowanie kończy się po jednokrotnym przejściu dostępnego źródła; nie tworzy
  automatycznie nowej rundy.
- Zakładka lub pojedynczy wynik bez listy źródłowej nie ma kolejnego elementu
  do wylosowania.
- Przed oznaczeniem zadania jako `Zrobione` trzeba sprawdzić z NVDA: stan
  początkowy pola wyboru, przełączanie `R`, menu i menu kontekstowe, powrót
  fokusu, ponowne otwarcie oraz zachowanie po restarcie programu.

## Migracja

Nie jest wymagana ręczna migracja. Brak nowego pola w starszym pliku ustawień
oznacza wyłączone losowanie. Pełna kopia konfiguracji rozpoznaje nowe pole.

## Wersja i commit

- Commit funkcji: do uzupełnienia po zatwierdzeniu spójnego przyrostu.
- Zainstalowany AMC Test: do uzupełnienia po kontrolowanej promocji.
- AMC Public i publiczny instalator: bez zmian.

