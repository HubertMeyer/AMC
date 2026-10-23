# AMC Test — korekta Spotify, YouTube i Frontier 23.10.2026, 12:56

## Wynik

Nowy AMC Test został zbudowany, atomowo zainstalowany i uruchomiony z
`D:\Projekty Codex\AMC Python`. AMC Public, instalator publiczny i GitHub nie
zostały zmienione.

- rewizja źródeł: `65b1166181e8cc3952584a7b22f85a8e77b747b2`;
- identyfikator zawartości paczki: `94b08d59`;
- etykieta kompilacji:
  `2026.10.23-65b1166181e8cc3952584a7b22f85a8e77b747b2-94b08d59`;
- tytuł uruchomionego okna: `AMC Test — 23.10.2026, 12:56`;
- uruchomiony interfejs:
  `D:\Projekty Codex\AMC Python\runtime\python.exe`;
- stały plik uruchamiający: `D:\Projekty Codex\AMC Python\AMC.exe`;
- paczka: 1671 plików, z kompletnymi sumami SHA-256 w manifeście.

## Zachowanie widoczne dla użytkownika

### Spotify — TyfloPodcast i inne duże programy

Enter na programie otwiera pierwsze 150 prawidłowych odcinków. Puste rekordy
zwrócone przez Spotify są pomijane, a pozycja „Załaduj więcej” pobiera kolejną
porcję i ustawia fokus na pierwszym nowym odcinku. Cofnięcie wraca do programu,
bez dopisywania osobnego kroku historii dla każdej porcji.

Log poprzednio zainstalowanej wersji potwierdził wykonanie właściwego
`spotify.containerItems`; instalacja nie była stara. Rzeczywiste Web API dla
zapisanego programu zwróciło 2873 rekordy, w tym 10 wartości `null`, na których
stary parser przerywał cały wynik. Odczyt aktualnego kodu z prawdziwego konta,
bez zmiany jego danych, zwrócił 150 pozycji, `hasMore=true`, w 3,38 s.

### YouTube — szybkie Ctrl+N, Ctrl+V

Okno dodawania źródła przechwytuje `Ctrl+V` we własnym polu adresu albo nazwy
i wykonuje natywne wklejenie w następnym obrocie kolejki interfejsu. Globalne
polecenie listy nie powinno już uruchamiać się przed ustabilizowaniem fokusu.
Nie powstał nowy skrót aplikacji, więc katalog poleceń, menu, pomoc i paleta nie
wymagały nowej pozycji.

### Frontier Smart — fokus podczas wykrywania

Podczas aktywnego skanowania fokus pozostaje na dostępnym przycisku
„Wyszukiwanie urządzeń w sieci lokalnej, czekaj”. Ponowne naciśnięcie podaje
„Wyszukiwanie urządzeń już trwa” i nie uruchamia drugiego skanu. Windows nie ma
już powodu przenosić fokusu na jedyny aktywny przycisk „Zamknij”.

Próba sieciowa przed instalacją zwróciła 0 urządzeń w 5,04 s. Nie dowodzi ona
działania ani awarii sprzętowej ścieżki Teufela. Po rzeczywistym rozpoznaniu
urządzenia przejście do nazwanego pola PIN jest zamierzonym kolejnym krokiem.

## Testy i bramki

- testy celowane Spotify, YouTube i Frontier: 85 zaliczonych;
- protokół LiteHost: 27 zestawów zaliczonych;
- celowany test podcastów Spotify w hoście Windows: zaliczony;
- kompilacja LiteHost Release: 0 ostrzeżeń, 0 błędów;
- pełna regresja promocji: 2014 zaliczonych, 111 świadomie pominiętych oraz
  11 podtestów zaliczonych;
- launcher i aktualizator: 30/30 testów;
- kontrolowany start kandydata przed instalacją: zaliczony;
- manifest i sumy SHA-256 kandydata: zaliczone;
- atomowa instalacja do stałego katalogu D: zaliczona;
- ponowna kontrola manifestu, sum i odizolowanego startu plików już
  zainstalowanych: zaliczona;
- widoczne uruchomienie właściwej wersji i ścieżki: potwierdzone.

Nie wykonano publikacji, budowy instalatora publicznego, zmiany konta Spotify
ani sprzętowego sterowania Frontier. Ręczny odbiór NVDA pozostaje potrzebny dla
trzech opisanych przepływów.

