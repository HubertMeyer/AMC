# AMC Test 0.1.0-alpha.436 — szkic zmian i odbioru

## SoundCloud jako podcast w AMC

W Podcastach `Ctrl+F` może znaleźć publiczny podcast SoundCloud dostępny w
katalogu Apple Podcasts, a `Ctrl+Shift+L` zapisuje go jako lokalną
subskrypcję. `Ctrl+N` przyjmuje również publiczny adres profilu SoundCloud albo
bezpośredni adres jego RSS.

Odcinki SoundCloud są zwykłymi plikami audio z RSS. Można je odtwarzać w AMC,
dodawać do kolejki, pobierać przez `Ctrl+D` i zapisywać przez `Ctrl+S`. Funkcja
nie wymaga konta SoundCloud, logowania Google ani klucza API.

Mixcloud nie został dodany. Dostępne mechanizmy tej usługi nie przekazują AMC
plików ani adresów strumieni audio, a osadzony odtwarzacz internetowy nie
spełniałby kontraktu pobierania i zwykłego sterowania podcastem.

## YouTube i skrzynka nowych materiałów

Pierwsze `Ctrl+I` otwiera skrzynkę nowych odcinków i materiałów. Kolejne
naciśnięcia w otwartej skrzynce wczytują po 150 następnych pozycji i ustawiają
fokus na pierwszej nowej pozycji.

Kolekcje YouTube żądają polskich tytułów przy zachowaniu dat przybliżonych.
Starsze tytuły mogą zostać poprawione przy zwykłym odświeżeniu źródła.

## Stan przed wydaniem

Zmiany SoundCloud przeszły kompilację bez ostrzeżeń i błędów, pełną regresję
wxPython: 2101 zaliczonych, 113 pominiętych i 13 podtestów zaliczonych, pełne
testy Core, 42 końcowe testy Pythona oraz próby publicznego wyszukiwania, RSS i
pliku `audio/mpeg`. Zmiany YouTube przeszły 141 testów Pythona, dwie regresje
C# oraz odczytowe próby biblioteki i yt-dlp.

Zbudowanie instalatora, publikacja GitHub i ręczny test aktualizacji są
oddzielnymi etapami. Zgodnie z decyzją użytkownika instalator tej wersji ma
zostać opublikowany, lecz nie zostanie automatycznie zainstalowany ani
uruchomiony na komputerze użytkownika.
