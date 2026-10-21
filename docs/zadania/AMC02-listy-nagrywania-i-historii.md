# AMC02 — krótkie listy nagrywania i historia plików

Status: **Uogólniona korekta pojedynczego wiersza i zapisu `Ctrl+H` jest
zbudowana, zainstalowana i uruchomiona także w najnowszym publicznym AMC
`0.1.0-alpha.431`. Integralność i kontrolowany start są zaliczone; działający
AMC Test nie został podmieniony, a oba profile czekają na ręczny odbiór NVDA**.

### Korekta użytkownika z 21.10.2026 — pojedynczy wiersz i `Ctrl+H`

Ta korekta zastępuje wcześniejszy opis, według którego `Alt+Shift+R` kończył
komunikat na „Nagrane, 1 z 1”. Przy jednym wpisie ma podać także użytkową nazwę
pliku, dokładnie jak poprawione `Alt+R`. Wspólna reguła obejmuje również
pojedynczy wpis `Ctrl+H` oraz `Ctrl+I`; nie obejmuje list wieloelementowych,
które nadal korzystają ze zwykłej mowy fokusu kontrolki.

Przyczyną pustego `Ctrl+H` w publicznym `alpha.429` nie była pusta prezentacja,
lecz brak zapisu potwierdzonego startu odtwarzania w warstwie wxPython.
Naprawa zapisuje Radio, lokalne pliki i podcasty ze zdarzenia rzeczywistego
startu silnika. Nie rekonstruuje wstecz odtworzeń, których wcześniejsza wersja
nie zachowała.

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

`Alt+R` otwiera listę aktualnych nagrań. Po zaktualizowaniu listy podaje jeden
pełny komunikat wejścia, na przykład „Nagrywane, 1 z 1, TVP Info - data i
godzina.mp3”. Pierwsza liczba jest zapamiętaną pozycją, druga liczbą widocznych
plików, a końcówka nazwą rzeczywiście wybranego pliku. Dzięki temu także
jedyny wiersz jest nazwany, nawet gdy Windows nie wyśle nowego zdarzenia
fokusu. Kolejne strzałki zaczynają się od samej nazwy pliku; słowo
„Nagrywane” nie jest powtarzane przy każdym ruchu. Podczas uruchamiania
nagrania, zanim silnik zna jeszcze ścieżkę pliku, zamiast pustej nazwy może
zostać podana nazwa stacji. Lista nie powtarza czasu trwania, liczby zapisanych
części, folderu ani nazwy harmonogramu.

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
- **Korekta odbiorcza użytkownika z 21.10.2026 zastępuje dla `Alt+R`
  założenie, że natywna lista zawsze sama odczyta pierwszy wiersz po komunikacie
  „Nagrywane, X z X”.** Przy pojedynczym aktywnym nagraniu nazwa nie została
  odczytana. Program synchronizuje teraz listę przed komunikatem i jawnie
  dołącza użytkową nazwę wybranego pliku. Techniczny identyfikator nagrania
  nadal nie trafia do mowy ani tekstu kontrolki.
- **Korekta użytkownika z 21.10.2026 zastępuje każde wyjaśnienie wiążące
  pustą Historię odtwarzania z pustym profilem albo eksportem i importem.**
  Publiczny AMC prowadzi własną lokalną historię bieżącego profilu. Po
  potwierdzonym rozpoczęciu stacji wpis ma być od razu dostępny pod `Ctrl+H`;
  eksport, import i zawartość profilu AMC Test nie mają na to wpływu.

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

19.10.2026, promocja korekty do AMC Test:

- użytkownik potwierdził brak nagrywania; niezależna bramka wykazała brak
  procesu poprzedniej instalacji, brak rosnących plików `.amc-partial` w dwóch
  pomiarach oraz brak harmonogramu przypadającego na bieżące okno;
- pełna regresja wxPython: **1842 zaliczone, 110 pominiętych i 11 podtestów
  zaliczonych** w 86,72 s;
- kompilacje Release hosta, uruchamiacza i aktualizatora: zaliczone bez
  ostrzeżeń i błędów;
- paczka 1666 plików przeszła kontrolę manifestu i SHA-256, została
  zainstalowana, a integralność instalacji zwróciła kod 0;
- potwierdzono działający proces
  `D:\Projekty Codex\AMC Python\runtime\python.exe` i okno „AMC Test”.

21.10.2026, korekta po ręcznym odbiorze pojedynczego wiersza:

- ukierunkowane testy widoków aktywności, nagrywania, skrótów, palety i
  publicznych regresji: **121 zaliczonych**;
- pełna regresja wxPython w przypiętym środowisku projektu: **1948
  zaliczonych, 110 pominiętych i 11 podtestów zaliczonych** w 155,69 s;
- test sprawdza kolejność „synchronizacja listy, potem komunikat”, pełny tekst
  „Nagrywane, 1 z 1, nazwa pliku”, brak technicznego ID oraz niezmienione
  „zero elementów” dla pustej listy;
- źródła, testy i dokumentacja nie są jeszcze dowodem buildu, instalacji ani
  rzeczywistej mowy NVDA. Budowę odłożono, ponieważ żywy AMC Test nadal
  nagrywał stację i plik roboczy faktycznie zwiększał rozmiar.

21.10.2026, budowa i instalacja po bezpiecznym zakończeniu nagrania:

- publiczna paczka `cf01ffda` powstała z czystej rewizji `ed5db367`, ma 1075
  kontrolowanych plików i numer `0.1.0-alpha.429`;
- instalator zakończył aktualizację `D:\Projekty Codex\AMC Public` kodem 0;
  zainstalowana kopia przeszła pełną integralność oraz kontrolowany start;
- w zainstalowanym profilu są WiiM, Sonos i pełny eksport/import, a nie ma
  modułów TIDAL, Spotify ani Frontier Smart;
- program uruchomiono z właściwej stałej ścieżki. Rzeczywista wypowiedź NVDA
  dla jednego aktywnego nagrania nadal wymaga ręcznego odsłuchu użytkownika.

21.10.2026, `alpha.430` po zgłoszeniu pustego `Ctrl+H` i `Alt+Shift+R`:

- pełna regresja wxPython: **1952 zaliczone, 110 pominiętych i 11 podtestów
  zaliczonych**; wszystkie **26 zestawów** protokołu C# przeszło;
- kompilacja Release całego rozwiązania: **0 ostrzeżeń, 0 błędów**;
- publiczna paczka `d8eb2766` ma 1075 kontrolowanych plików i pochodzi z
  czystej rewizji `462783c56383757819b9aa5df02f6d6ccbbbc826`;
- instalacja publiczna zakończyła się kodem 0, pełna integralność zwróciła 0,
  kontrolowany start przeszedł, a widoczne okno uruchomiono ze stałej ścieżki;
- przed podmianą sprawdzono 15 skonfigurowanych folderów i 47 włączonych
  harmonogramów: brak aktywnego okna, terminu w ciągu 5 minut i rosnących
  plików. AMC Public zamknął się prawidłowo;
- AMC Test dwukrotnie odrzucił zwykłe `WM_CLOSE`. W lokalnym magazynie
  odzyskiwania były 23 zachowane pliki `.amc-partial`; żaden nie rósł w
  pomiarze, lecz procesu nie wymuszono i instalacji Test nie podmieniono.

21.10.2026, diagnostyka zainstalowanego `alpha.430` po korekcie użytkownika:

- rzeczywista publiczna baza profilu miała poprawną integralność, lecz nadal
  zero wpisów `playback_history`; jej ostatni zapis danych pochodził sprzed
  instalacji `alpha.430`, więc nie jest to dowód niepowodzenia bieżącego kodu;
- zainstalowany host z `D:\Projekty Codex\AMC Public` uruchomiono na
  izolowanej kopii profilu i wyciszonym lokalnym strumieniu HTTP. Potwierdzony
  start dopisał jeden wpis sesji `radio` z pozycją 0, bez `historyError`;
- ten sam czytnik danych, którego używa `Ctrl+H`, odczytał dokładnie ten wpis,
  dopasował go do właściwej stacji i nie zgłosił ograniczenia widoku;
- próba nie zmieniła prawdziwego profilu użytkownika. Kopię diagnostyczną
  usunięto z katalogu Temp po zamknięciu hosta; odzyskano 410 166 bajtów.

## Znane ograniczenia

- Ostatnia korekta pełnego komunikatu `Alt+R` jest zainstalowana w publicznym
  AMC. Wymaga jeszcze odsłuchu wejścia, ruchu strzałkami i powrotu ze wcześniej
  zapamiętanym zaznaczeniem w rzeczywistym NVDA.
- Wczesny stan „uruchamianie nagrania” może chwilowo użyć nazwy stacji, dopóki
  host nie poda nazwy tworzonego pliku.
- Bitrate i rozmiar zależą od dostępności pliku i odpowiedzi hosta. Folder
  pochodzi z lokalnej ścieżki i nie jest zgadywany dla elementu sieciowego.
- Zadanie nie dodaje podglądu pliku podczas nagrywania ani nowych działań na
  pliku. Ten zakres pozostaje osobnym, późniejszym zadaniem.
- Odtworzeń wykonanych przed zainstalowaniem `alpha.430`, których wcześniejsza
  wersja nie zapisała, nie da się wiarygodnie odtworzyć wstecz. Nie jest to
  zamierzone czyszczenie historii: każde nowe, potwierdzone odtworzenie w
  `alpha.430` ma być zapisane lokalnie i widoczne pod `Ctrl+H`.

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
  nagrania menu i playlisty Spotify`.
- Korekta odczytu pojedynczego aktywnego nagrania z 21.10.2026: commit
  `d94ccecf` — `fix(amc02): odczytaj pojedyncze aktywne nagranie`. Jest to
  stan źródeł i testów; nie jest jeszcze dowodem nowej kompilacji ani
  instalacji.
- Uogólnienie na `Alt+Shift+R`, `Ctrl+H` i `Ctrl+I` oraz rzeczywisty zapis
  Historii ze zdarzenia startu silnika: commit `d94b4303` — `fix(amc): zapisz
  historie i nazwij pojedyncze podglady`. Nowy kod i testy są wspólne dla AMC
  Test i Public; instalacja następcy pozostaje osobnym krokiem.
- Kandydat instalacyjny tej korekty otrzymuje numer `0.1.0-alpha.429`, aby nie
  nadpisywać nieodróżnialnym plikiem odebranego wcześniej `alpha.428`.
- Zainstalowana paczka `alpha.429`: rewizja `ed5db3679d046a6861283a7a98952396deef2663`,
  identyfikator `cf01ffda`, 1075 plików. Instalator ma 124 094 692 bajty i
  SHA-256 `09df938029ee66722785ad27a3c3b3f1aadc2bedd21e35f2323bc25d0b01c81b`.
  Instalacja, pełna integralność i kontrolowany start są zaliczone.
- Zainstalowana publiczna paczka `alpha.430`: rewizja
  `462783c56383757819b9aa5df02f6d6ccbbbc826`, identyfikator `d8eb2766`, 1075
  plików. Instalator `AMC-0.1.0-alpha.430-win-x64.exe` ma 124 077 804 bajty i
  SHA-256 `848f3d7ca9e397bb0e10d8ec006a2fcc1faca777d6531031b36215c3e2d45f1b`.
  Instalacja, pełna integralność, kontrolowany start i widoczny start są
  zaliczone; publikacji nie wykonano.
- Instalacja zawierająca kolejną korektę:
  `2026.10.19-8093e22adfa9b6abfc72c35c5c7029eaaade88c8-718893c9`;
  pełna regresja, manifest, sumy, integralność, stała ścieżka procesu i
  uruchomienie zweryfikowane 19 października 2026.

## Porządek dysku po korekcie

- Usunięto trzy odtwarzalne pliki `.pyc` utworzone przez test i kontrolę
  składni w katalogach nadrzędnych
  `D:\Projekty Codex\AMC - integracja wxPython\wxlite\amc_wx_lite\__pycache__`
  oraz `D:\Projekty Codex\AMC - integracja wxPython\wxlite\tests\__pycache__`.
  Odzyskano 237 379 bajtów. Python może utworzyć te pliki ponownie; ich
  odzyskiwanie nie jest potrzebne.
- Nie usunięto `.test-output`, `.test-tmp`, paczek, instalatorów, źródeł,
  dokumentacji, ustawień ani danych użytkownika.

