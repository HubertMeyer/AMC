# AMC Test — projekt instrukcji odbioru zmian z 26 października 2026 r.

Ten dokument jest projektem do korekty i zatwierdzenia. Nie oznacza publikacji
ani zainstalowania wersji.

## Rozpoznane utwory

1. W Radiu naciśnij `Ctrl+Alt+S` zarówno na głównej liście, jak i w
   odtwarzaczu. Za każdym razem powinno otworzyć się okno **Rozpoznane utwory**.
2. Strzałkami sprawdź krótkie wiersze. Prawa strzałka otwiera najważniejsze
   działania, a menu kontekstowe — pełny zestaw usług i łączy.
3. `Enter` pokazuje utwór w usłudze domyślnej, `Ctrl+Enter` pokazuje album i
   ustawia fokus na rozpoznanym utworze. `Ctrl+C` kopiuje pełny opis, a
   `Ctrl+Shift+C` dokładne publiczne łącze.

## Nagrywane i Harmonogram

1. Otwórz `Nagrywane` przez `Alt+R`.
2. Lewa strzałka podaje parametry odbieranego strumienia, a prawa — bitrate lub
   format pliku, nazwę pliku i folder zapisu.
3. W Harmonogramie prawa strzałka podaje ten sam krótki opis pliku, bez adresu
   stacji.

## Pobieranie i zapisywanie wideo

1. W sesji **Podcasty i YouTube** zaznacz materiał YouTube.
2. `Ctrl+Shift+D` pobiera wideo do skonfigurowanego folderu. `Ctrl+S` otwiera
   **Zapisz wideo jako** i pozwala jednorazowo wybrać MP4 albo najlepszy
   dostępny format.
3. `Ctrl+D` nadal pobiera audio. Zwykły odcinek pod `Ctrl+S` nadal otwiera
   zapis audio.

## Import nazw stacji

1. Otwórz sesję **Radio internetowe**.
2. Wybierz `Ctrl+O` albo **Plik > Importuj stacje z playlisty…**.
3. Wskaż M3U, M3U8, PLS, XSPF albo obsługiwany JSON.
4. Jeśli część wpisów nie ma nazw, NVDA powinien powiedzieć:
   `Odczytuję nazwy stacji z serwerów`.
5. Po zakończeniu NVDA poda liczbę dodanych stacji, nazw odczytanych z serwerów
   i nazw zastępczych.
6. Strzałkami sprawdź wynikową Bibliotekę. Pozycje powinny mówić nazwę z pliku,
   nazwę serwera albo — gdy serwer jej nie podał — krótki host. Pełny URL nie
   powinien być zwykłą nazwą pozycji.

Nazwa z playlisty jest nadrzędna. Import nie odtwarza stacji i nie używa tytułu
bieżącego utworu jako nazwy stacji.

Dokument jest projektem do ręcznego odbioru z NVDA. Testy automatyczne i
instalacja zakończyły się powodzeniem, ale rzeczywiste pobranie wideo i pełny
odsłuch wszystkich komunikatów NVDA nie zostały wykonane automatycznie.

