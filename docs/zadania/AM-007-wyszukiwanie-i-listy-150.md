# AM-007 — wyszukiwanie Apple Music i listy po 150

- Data: 15 listopada 2026.
- Produkt: AMC Test, aplikacja wxPython. AMC Public nie udostępnia Apple Music.
- Stan: źródła i testy celowane gotowe; brak nowej kompilacji, instalacji,
  wydania GitHub i próby Ctrl+F z NVDA na żywym oknie.

## Zachowanie użytkowe

- W sesji Apple Music `Ctrl+F` szuka w osobistej Bibliotece oraz wśród utworów
  katalogu regionu konta. Wyniki katalogowe mają rodzaj „Utwór z katalogu”.
  Enter w oknie wyszukiwania przenosi na przejściową listę AMC; samo wybranie
  wyniku nie uruchamia odtwarzania.
- `Ctrl+K` filtruje bieżącą wczytaną listę. Opis polecenia w `Ctrl+F1` i
  pełnej pomocy wskazuje zakres Apple Music. Menu i paleta korzystają z
  istniejącego polecenia „Szukaj w bieżącej usłudze”.
- Listy Utwory, Albumy, Wykonawcy, Playlisty oraz zawartość albumów i playlist
  pokazują do 150 pozycji na porcję. AMC pobiera dwie strony Apple po 100 i 50,
  zachowuje dalszy kursor i po „Załaduj więcej” pokazuje kolejne do 150.
- Wskazówki okna wyszukiwania mówią, że Apple zwraca najwyżej 25 dopasowań
  każdego rodzaju w każdym źródle i zalecają doprecyzowanie tekstu.

## Przyczyna i decyzje

Poprzedni kod pytał tylko o Bibliotekę. Zawartość katalogu Apple Music, która
nie została dodana do osobistej Biblioteki, nie mogła się pojawić. Katalogowe
utwory mają istniejącą ścieżkę wyboru i dostępne akcje. Albumy, artyści i
playlisty z katalogu wymagają osobnych widoków szczegółowych, dlatego na razie
nie są reklamowane jako otwieralne wyniki. Katalog i Biblioteka są odczytywane
niezależnie: błąd jednego źródła nie usuwa poprawnych wyników drugiego.

Odczytowa próba na zalogowanym koncie potwierdziła, że `/v1/me/library/search`
przyjmuje limit 25, a limit 26 i 50 odrzuca jako HTTP 400. Dla terminu
„Whitney” zwróciła 30 wyników Biblioteki. W odczycie dla „a” oraz „Whitney”
grupy z 25 wynikami nie podały dalszego kursora. Odczyt katalogu dla
„Whitney” zwrócił 25 utworów. Nie deklarujemy pełnych wyników przy szerokim
zapytaniu; użytkownik może doprecyzować tekst. Lista biblioteczna z limitem
100 i druga strona z limitem 50 dały łącznie 150 utworów i 150 albumów.

Korekta decyzji z 13 listopada 2026 w
`A11Y-COLLECTIONS-20261113-fokus-mowa-sortowanie.md`: zakres `Ctrl+F`
obejmujący wyłącznie Bibliotekę zostaje rozszerzony o utwory katalogowe,
a porcja 100 pozycji zmienia się na 150. Nadal nie ma odtwarzacza AMC ani
potwierdzenia, że oficjalne Apple Music odtworzy dokładnie wskazany utwór.

## Weryfikacja i ograniczenia

- Testy adaptera, GUI, wyszukiwarki i poleceń: 168 zaliczonych, 3 podtesty.
- Próba odczytowa na koncie: wyszukiwanie Biblioteki i katalogu oraz pobranie
  150 elementów działały. Nie otwierano okna ani nie sterowano dźwiękiem.
- Potrzebna próba z NVDA: otwarcie Ctrl+F, fokus początkowy, wyniki,
  strzałki, Enter, Escape, powrót fokusu i ponowne otwarcie. Warto użyć
  dokładnego zapytania, dla którego użytkownik wcześniej słyszał brak wyników.
- Wersja wydana: nadal alpha.507; zmiana nie jest w niej zainstalowana.
- Commit źródeł: `dc166908`. Wydanie: jeszcze nie przygotowano.

## Projekt instrukcji i listy zmian — do korekty użytkownika

W AMC Test przejdź do sesji Apple Music i naciśnij `Ctrl+F`. Wpisz nazwę utworu,
albumu, wykonawcy lub playlisty. AMC pokaże wyniki Twojej Biblioteki oraz
pasujące utwory z katalogu Apple Music. Przy bardzo ogólnym haśle doprecyzuj
tekst, ponieważ każde źródło pokazuje do 25 wyników danego rodzaju. Enter
wybiera wynik na liście AMC; nie rozpoczyna muzyki. `Ctrl+K` filtruje tylko
aktualnie wczytaną listę. Listy Apple Music pokazują do 150 pozycji; na końcu
można wybrać „Załaduj więcej”.
