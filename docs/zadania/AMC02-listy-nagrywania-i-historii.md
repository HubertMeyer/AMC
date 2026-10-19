# AMC02 — krótkie listy nagrywania i historia plików

Status: **Kolejna korekta wdrożona w źródłach i testach; czeka na pełną
regresję, instalację po bezpiecznej bramce nagrywania i odbiór NVDA**.

## Zakres

Zadanie porządkuje dwa równorzędne podglądy:

- `Alt+R` — aktualnie nagrywane pliki;
- `Alt+Shift+R` — historia nagrywania, łącznie z plikami ukończonymi,
  zatrzymanymi, przerwanymi, niedostępnymi i próbami nieudanymi.

Uzupełnia także lewą strzałkę na lokalnym pliku historii nagrywania i na
lokalnym wpisie `Ctrl+H` o nazwę folderu, obok parametrów przygotowanych przez
wspólny formatter hosta.

Źródłem zatwierdzonego kontraktu były tylko do odczytu:

- `D:\Projekty Codex\Accessible Multimedia Controller\AMC02_ANALIZA_2026-10-18.md`;
- `D:\Projekty Codex\Accessible Multimedia Controller\AMC02_REALIZACJA_ETAP_A_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

`Alt+R` otwiera listę aktualnych nagrań i mówi raz „Nagrywane, X z X”, gdzie
pierwsza liczba jest zapamiętaną pozycją, a druga liczbą widocznych plików.
Zwykły wiersz zaczyna się od razu nazwą pliku; słowo „Nagrywane” nie jest
powtarzane przy każdej strzałce. Podczas uruchamiania nagrania, zanim silnik
zna jeszcze ścieżkę pliku, zamiast pustej nazwy może zostać podana nazwa
stacji. Lista nie powtarza czasu trwania, liczby zapisanych części, folderu
ani nazwy harmonogramu.

`Alt+Shift+R` otwiera Historię nagrywania i mówi raz „Nagrane, X z X”. Zwykły
ukończony plik jest czytany
od razu jako sama nazwa pliku, bez powtarzanego przedrostka „Nagrane”. Inne
stany zaczynają się od krótkiego,
jednoznacznego określenia: „Zatrzymane”, „Przerwane”, „Nieudane”, „Brak pliku
nagrania” albo „Plik nagrania niedostępny”. Przy nieudanej próbie, dla której
nie powstał plik, lista może podać nazwę stacji i przyczynę. Normalny wiersz nie
powtarza stacji, harmonogramu, daty ani folderu.

Lista „Nagrywane” i Historia nagrywania pamiętają zaznaczenie oddzielnie.
Komunikat wejścia podaje pozycję, a kolejne strzałki pozostają krótkie i
zaczynają się od nazwy bieżącego pliku.

Na lokalnym nagraniu w Historii nagrywania lewa strzałka podaje dostępne
parametry, między innymi bitrate i rozmiar, a na końcu nazwę folderu bez
ponownego czytania tytułu. Ta sama zasada dotyczy lokalnego pliku w historii
odtwarzania `Ctrl+H`. Wpis internetowy nie otrzymuje wymyślonej informacji o
folderze.

Polecenie `Alt+R` ma w menu, pomocy klawiatury `Ctrl+F1` i palecie
`Ctrl+Shift+K` nazwę „Pokaż aktualnie nagrywane pliki”. `Alt+Shift+R` ma nazwę
„Historia nagrywania”.

## Uzasadnienie i decyzje

- Zwykły wiersz jest identyfikatorem pliku, nie raportem o stacji lub
  harmonogramie. Szczegóły, które spowalniały nawigację NVDA, usunięto z jego
  dostępnej etykiety.
- Folder przeniesiono do jawnej informacji pod lewą strzałką. Dzięki temu jest
  dostępny na żądanie i nie powtarza się przy każdym ruchu po liście.
- Format bitrate, rozmiaru, kodeka i czasu nadal tworzy wspólny formatter C#.
  Python dopisuje jedynie sprawdzoną nazwę folderu lokalnej ścieżki.
- Informacja o folderze jest dozwolona tylko w sesji Pliki lokalne i tylko w
  Historii odtwarzania lub Historii nagrywania. Adres URL nie jest traktowany
  jak ścieżka.
- Pamięć zaznaczenia Historii nagrywania jest niezależna od pamięci widoku
  „Nagrywane” i od zwykłego powrotu do Biblioteki.
- Korekta użytkownika z 18.10.2026 zastępuje wcześniejszy wariant, w którym
  normalny wiersz Historii zawierał stację, datę, harmonogram i folder, a
  ukończony wpis nie zaczynał się od „Nagrane”.
- Korekta użytkownika z 18.10.2026 zastępuje wcześniejszy wariant, w którym
  `Alt+Shift+R` ogłaszał osobny licznik elementów przed pierwszym wierszem.
- Korekta użytkownika z 19.10.2026 zastępuje ustalenie z 18.10.2026, według
  którego każdy poprawnie ukończony wiersz zaczynał się od „Nagrane”. W
  zwykłej historii ta informacja nie rozróżnia plików i niepotrzebnie wydłuża
  każdy ruch NVDA, dlatego wiersz zaczyna się teraz bezpośrednio nazwą pliku.
  Określenia „Zatrzymane”, „Przerwane”, „Nieudane” i informacje o braku albo
  niedostępności pliku pozostają, ponieważ opisują stan wyjątkowy.
- **Korekta użytkownika z 19.10.2026 zastępuje wcześniejsze ustalenie o samym
  nagłówku bez pozycji.** `Alt+R` ma ogłaszać raz „Nagrywane, X z X”, a
  `Alt+Shift+R` — „Nagrane, X z X”. Nie przywraca to przedrostka do każdego
  wiersza; strzałki nadal zaczynają od nazwy pliku.

## Zmienione miejsca

- `wxlite/amc_wx_lite/radio_recording.py` — etykiety aktywnych i zakończonych
  nagrań;
- `wxlite/amc_wx_lite/navigation.py` — opcjonalne pominięcie licznika i osobna
  pamięć zaznaczenia Historii nagrywania;
- `wxlite/amc_wx_lite/quick_info.py` i `gui.py` — folder lokalnego pliku w
  szybkiej informacji oraz nagłówek „Historia nagrywania”;
- `wxlite/amc_wx_lite/menu_model.py` i `shortcuts.py` — wspólne nazwy menu,
  pomocy i palety;
- testy nagrywania, szybkiej informacji i katalogu poleceń.

## Testy i wynik

19.10.2026 przed 02:00 wykonano wyłącznie testy źródłowe, bez zamykania,
kompilowania, instalowania ani uruchamiania AMC:

- testy ukierunkowane nagrywania, szybkiej informacji, menu i palety:
  **129 zaliczonych**;
- poszerzona regresja obejmująca dodatkowo nawigację Biblioteki, `Ctrl+L`,
  podglądy przejściowe, fokus i komunikaty zmiany widoku:
  **207 zaliczonych**;
- kontrola składni zmienionych modułów: zaliczona;
- `git diff --check`: zaliczony; ostrzeżenia o planowanej normalizacji końców
  wierszy nie są błędem diffu.
- Po 02:00 potwierdzono brak aktywnego harmonogramu, brak wzrostu
  `.amc-partial` i brak blokady tych plików. Pełna regresja wxPython po
  połączeniu etapów: **1754 zaliczone, 110 pominiętych, 11 podtestów**.
- Paczka instalacyjna przeszła kontrolę manifestu i SHA-256, została
  zainstalowana, a AMC Test uruchomiono z potwierdzoną tożsamością kompilacji.

Testy potwierdzają krótkie etykiety bez nazw stacji i harmonogramów, brak
osobnego licznika w niepustej Historii nagrywania, oddzielną pamięć zaznaczeń,
odrzucenie folderu dla wpisu internetowego, brak powtórzenia tytułu oraz
zgodność nazw i skrótów wykonania, pomocy i palety.

19.10.2026, korekta po ręcznym odsłuchu użytkownika:

- `39 passed` — cały `test_radio_recording.py`, w tym jawne sprawdzenie, że
  poprawnie ukończony i dostępny plik zaczyna się od nazwy, a nie od słowa
  „Nagrane”;
- `96 passed` — regresje palety poleceń, informacji pod lewą strzałką,
  nawigacji i widoków Biblioteki;
- `py_compile` zmienionego formattera i testu: zaliczony;
- osobny przebieg zawierający test zależny od wx nie został zebrany przez
  systemowy Python bez wxPython. Nie przedstawia się go jako zaliczonego;
  dotychczasowe testy tego widoku oraz pełny odbiór wymagają następnej paczki.
- W tym źródłowym przebiegu korekty nie wykonywano kompilacji ani instalacji.

19.10.2026, instalacja zbiorcza korekty:

- pełna regresja wxPython: **1831 zaliczonych, 110 pominiętych i 11
  podtestów zaliczonych**;
- paczka: 1665 plików, manifest i SHA-256 zweryfikowane;
- instalacja i uruchomienie AMC Test ze stałej ścieżki: zaliczone.

19.10.2026, kolejna korekta pozycji i nazw wierszy:

- wspólna bramka nagrywania, menu, Spotify, ustawień i harmonogramów:
  **204 zaliczone**;
- pełna regresja wxPython po połączeniu korekt: **1837 zaliczonych, 110
  pominiętych i 11 podtestów zaliczonych**;
- test sprawdza zapamiętaną pozycję „2 z 2” oraz brak słowa „Nagrywane” w
  tytułach obu zwykłych wierszy;
- na tym etapie wykonano wyłącznie zmianę źródeł i odizolowane testy. Pełna
  kompilacja, instalacja i uruchomienie pozostają osobnymi krokami po 18:30 i
  ponownej kontroli nagrywania.

## Znane ograniczenia

- Ostatnia korekta „Nagrywane/Nagrane, X z X” nie jest jeszcze zainstalowana.
  Po instalacji wymaga odsłuchu wejścia, ruchu strzałkami i powrotu do obu
  widoków ze wcześniej zapamiętanym zaznaczeniem.
- Wczesny stan „uruchamianie nagrania” może chwilowo użyć nazwy stacji, dopóki
  host nie poda nazwy tworzonego pliku.
- Bitrate i rozmiar zależą od dostępności pliku i odpowiedzi hosta. Folder
  pochodzi z lokalnej ścieżki i nie jest zgadywany dla elementu sieciowego.
- Zadanie nie dodaje podglądu pliku podczas nagrywania ani nowych działań na
  pliku. Ten zakres pozostaje osobnym, późniejszym zadaniem.

## Wersja i commit

- Zmiana źródłowa: commit `de9814b6` — „Skróć listy nagrywania i uzupełnij
  informacje o folderze”.
- Korekta usuwająca „Nagrane” z poprawnych wierszy: `5e6a15eb` —
  `fix(amc02): zacznij historie nagran od nazwy pliku`.
- Kompilacja: Release, zaliczona bez ostrzeżeń i błędów.
- Instalacja: `2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026; ta
  instalacja nie zawiera jeszcze korekty usuwającej „Nagrane”.
- Instalacja korekty: `2026.10.19-fb9ba25fe0680cf7bf5435d53eb5b073de091cca-0debb6aa`;
  manifest 1665 plików, sumy, stała ścieżka i uruchomione AMC Test
  zweryfikowane 19 października 2026.
- Publikacja: niewykonana i niedozwolona w tym etapie.
- Kolejna korekta źródłowa: commit `fdc26b83` — `fix(amc): uporzadkuj
  nagrania menu i playlisty Spotify`; kompilacja i instalacja jeszcze
  niewykonane.

## Porządek dysku po korekcie

- Usunięto trzy odtwarzalne pliki `.pyc` utworzone przez test i kontrolę
  składni w katalogach nadrzędnych
  `D:\Projekty Codex\AMC - integracja wxPython\wxlite\amc_wx_lite\__pycache__`
  oraz `D:\Projekty Codex\AMC - integracja wxPython\wxlite\tests\__pycache__`.
  Odzyskano 237 379 bajtów. Python może utworzyć te pliki ponownie; ich
  odzyskiwanie nie jest potrzebne.
- Nie usunięto `.test-output`, `.test-tmp`, paczek, instalatorów, źródeł,
  dokumentacji, ustawień ani danych użytkownika.

