# AMC02 — krótkie listy nagrywania i historia plików

Status: **W trakcie; kod i testy źródłowe gotowe, czeka na bezpieczną
kompilację, instalację i odbiór NVDA**.

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

`Alt+R` otwiera listę „Nagrywane”. Każdy zwykły wiersz ma krótki format
„Nagrywane, nazwa pliku”. Podczas uruchamiania nagrania, zanim silnik zna
jeszcze ścieżkę pliku, zamiast pustej nazwy może zostać podana nazwa stacji.
Lista nie powtarza czasu trwania, liczby zapisanych części, folderu ani nazwy
harmonogramu.

`Alt+Shift+R` otwiera „Historię nagrywania”. Zwykły ukończony plik jest czytany
jako „Nagrane, nazwa pliku”. Inne stany zaczynają się od krótkiego,
jednoznacznego określenia: „Zatrzymane”, „Przerwane”, „Nieudane”, „Brak pliku
nagrania” albo „Plik nagrania niedostępny”. Przy nieudanej próbie, dla której
nie powstał plik, lista może podać nazwę stacji i przyczynę. Normalny wiersz nie
powtarza stacji, harmonogramu, daty ani folderu.

Po wejściu do Historii nagrywania AMC mówi jej nazwę, ale nie dodaje osobnego
komunikatu „X elementów”. Pozycję „1 z 1”, „2 z 5” i podobną przekazuje
natywna lista razem z aktualnym wierszem. Lista „Nagrywane” i Historia
nagrywania pamiętają zaznaczenie oddzielnie.

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

Testy potwierdzają krótkie etykiety bez nazw stacji i harmonogramów, brak
osobnego licznika w niepustej Historii nagrywania, oddzielną pamięć zaznaczeń,
odrzucenie folderu dla wpisu internetowego, brak powtórzenia tytułu oraz
zgodność nazw i skrótów wykonania, pomocy i palety.

## Znane ograniczenia

- Zmiana nie została jeszcze skompilowana ani zainstalowana. Nie przeprowadzono
  jeszcze odsłuchu rzeczywistego NVDA; nagrywanie użytkownika ma pierwszeństwo.
- Wczesny stan „uruchamianie nagrania” może chwilowo użyć nazwy stacji, dopóki
  host nie poda nazwy tworzonego pliku.
- Bitrate i rozmiar zależą od dostępności pliku i odpowiedzi hosta. Folder
  pochodzi z lokalnej ścieżki i nie jest zgadywany dla elementu sieciowego.
- Zadanie nie dodaje podglądu pliku podczas nagrywania ani nowych działań na
  pliku. Ten zakres pozostaje osobnym, późniejszym zadaniem.

## Wersja i commit

- Zmiana źródłowa: commit `de9814b6` — „Skróć listy nagrywania i uzupełnij
  informacje o folderze”.
- Kompilacja: jeszcze niewykonana.
- Instalacja: jeszcze niewykonana.
- Publikacja: niewykonana i niedozwolona w tym etapie.

