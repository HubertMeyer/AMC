# AM-007 — wyszukiwanie i nawigacja Apple Music

- Data: 15 listopada 2026.
- Produkt: AMC Test, aplikacja wxPython. AMC Public nie udostępnia Apple Music.
- Stan: źródła i testy celowane gotowe; kompilacja, instalacja, wydanie GitHub
  i próba z NVDA w działającym oknie wymagają osobnego potwierdzenia wynikiem.

## Materiał do dokumentacji użytkownika

- `Ctrl+F` przeszukuje osobistą Bibliotekę i katalog regionu konta. Wyniki
  obejmują utwory, albumy, wykonawców i playlisty. Każdy rodzaj i źródło
  pokazuje do 25 trafień na zapytanie; przy szerokim zapytaniu trzeba
  doprecyzować tekst. `Ctrl+K` filtruje tylko bieżącą, wczytaną listę.
- Enter na wykonawcy otwiera cztery nazwane poziomy: Albumy, Single i EP,
  Popularne utwory, Playlisty z wykonawcą. Enter na albumie lub playliście
  otwiera utwory. Enter na utworze nadal używa istniejącego mechanizmu
  odtwarzania AMC; to zadanie nie potwierdza poprawności odtwarzacza.
- Prawa strzałka w wynikach wyszukiwania i na głównej liście Apple Music
  pokazuje dostępne przejścia. Dla utworu są to album i wykonawca, gdy Apple
  zwraca te powiązania. W oknie wyboru Enter otwiera cel, a lewa strzałka
  lub Escape wraca z fokusem do listy. Backspace w widokach Apple Music wraca
  do poprzedniej listy i odtwarza zaznaczenie.
- Lewa strzałka odczytuje czas trwania utworu oraz dostępne warianty audio,
  jeżeli katalog je podaje. Komunikat mówi wprost, że format bieżącego
  odtwarzania jest nieznany. Nie utożsamiamy dostępnego wariantu z jakością
  strumienia, który faktycznie gra w osadzonym Chromium.
- Biblioteczne Utwory, Albumy, Wykonawcy, Playlisty oraz zawartość albumów,
  playlist i widoków wykonawcy wczytują do 150 pozycji na porcję. „Załaduj
  więcej” pobiera następne do 150 pozycji i zachowuje poprzednie.
- Opisy `Ctrl+F1`, pełnej pomocy i palety komend korzystają ze wspólnego
  modelu poleceń; menu kontekstowe ma nazwane Powiązania Apple Music.

## Uzasadnienie i decyzje

Wcześniejszy kod pytał tylko o Bibliotekę, więc nie widział pozycji
katalogowych. W pierwszej wersji AM-007 z 15 listopada 2026 wyszukiwanie
katalogowe ograniczono do pojedynczych utworów, a opis sugerował, że Enter
jedynie wybiera wynik. Użytkownik tego samego dnia wskazał, że wyniki dla
wykonawcy są przemieszane z utworami i nie pozwalają wejść do albumów,
utworów ani playlist. Ta korekta zastępuje wcześniejszą decyzję: katalog
zwraca cztery rodzaje, a wyniki można otwierać hierarchicznie.

Odczytowa próba na zalogowanym koncie wykazała: zapytanie o „Bryan Adams”
zwróciło wykonawców, albumy, playlisty i utwory. Widoki wykonawcy zwróciły
21 albumów, 31 singli i EP, 150 popularnych utworów z dalszym kursorem oraz
8 playlist. Odczyt utworu zwrócił album i wykonawcę. Próba nie uruchamiała
odtwarzania ani nie przejmowała fokusu komputera.

Apple nazywa jedną z list `top-songs`, więc etykieta „Popularne utwory” jest
celowa: nie obiecujemy kompletnej dyskografii. Wyszukiwanie biblioteczne
przyjmuje limit 25; limit 26 i 50 zwracał HTTP 400. Przy szerokich hasłach
nie można zapewnić wszystkich wyników bez doprecyzowania zapytania.

Zmiana koryguje też decyzję z 13 listopada 2026 opisaną w
`A11Y-COLLECTIONS-20261113-fokus-mowa-sortowanie.md`: `Ctrl+F` obejmuje
Bibliotekę i katalog, a porcje list wynoszą do 150. Nadal nie ma dowodu,
że oficjalne Apple Music uruchamia dokładnie wskazany utwór ani że
osadzony odtwarzacz AMC gra w maksymalnej jakości.

## Testy i wynik

- Testy celowane adaptera, nawigatora, GUI, etykiet i skrótów oraz kontrola
  menu TIDAL: 254 zaliczone, 3 podtesty.
- Pełny przebieg źródeł: 2786 zaliczonych, 117 pominiętych, 20 niezaliczonych.
  Niepowodzenia obejmowały wcześniejsze testy kopii zapasowej, ustawień,
  startu, Radio Archiwisty, Sonosa, TIDAL oraz istniejące braki tłumaczeń.
  Jedną regresję nowego menu Apple Music w teście TIDAL naprawiono i
  potwierdzono w zestawie celowanym. Różnicowy audyt tekstów potwierdził,
  że wszystkie nowe statyczne etykiety Apple Music mają tłumaczenia.
- Odczytowa próba katalogu i relacji na koncie: powodzenie; bez sterowania
  aplikacją i dźwiękiem.

## Znane ograniczenia

- Próba NVDA w działającym AMC pozostaje do wykonania przy wolnym komputerze:
  początkowy fokus Ctrl+F, przejścia Enter i prawą strzałką, odczyt lewą,
  powrót Escape i Backspace, ponowne otwarcie oraz mowa pierwszej pozycji.
- Nadal nie zweryfikowano, czy wybrany utwór uruchamia się i daje sterować
  dokładnie w AMC. Na tym etapie nie ogłaszamy rozwiązania odtwarzania.

## Wersja i commit

- Kandydat instalatora alpha.508 z wcześniejszej wersji źródeł jest
  nieaktualny i nie może być publikowany jako wynik tej korekty.
- Nowe źródła otrzymują numer alpha.509, aby nie pomylić ich z kandydatem
  alpha.508. Numer w źródłach nie dowodzi jeszcze powstania instalatora.
- Wersja zainstalowana na początku zadania: alpha.507. Nowe źródła, build,
  instalacja i opublikowane wydanie mają odrębne statusy.
- Commit zmiany hierarchii: do uzupełnienia po zapisaniu źródeł.

## Projekt instrukcji i listy zmian — do korekty użytkownika

W sesji Apple Music naciśnij `Ctrl+F` i wpisz nazwę wykonawcy, albumu,
playlisty albo utworu. Enter na wykonawcy pokazuje Albumy, Single i EP,
Popularne utwory oraz Playlisty z wykonawcą. Prawa strzałka pokazuje
powiązania zaznaczonej pozycji, a Backspace wraca do poprzedniej listy.
Lewa strzałka odczytuje czas trwania i znane warianty audio; faktyczna
jakość odtwarzania pozostaje nieznana. Listy wczytują do 150 pozycji naraz,
a dalsze pozycje otwiera „Załaduj więcej”. Przy zbyt szerokim zapytaniu
doprecyzuj nazwę, ponieważ Apple ogranicza wyniki wyszukiwania.
