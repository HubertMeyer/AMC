# POD-003 — niezawodność odświeżania i duże kanały podcastów

## Status

Zrobione w źródłach i testach automatycznych, zainstalowane i uruchomione w
zbiorczym AMC Test `23.10.2026, 11:24`; ręczny odbiór NVDA pozostaje do
wykonania. Ten zapis zastępuje niższe historyczne informacje o braku instalacji.
Szczegóły:
[AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md](AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md).

## Zgłoszenie użytkownika

23 października 2026 użytkownik zgłosił, że TyfloPodcast nie wczytał się, a
część innych podcastów nie pokazała wszystkich pozycji. Należało rozdzielić
awarię całego źródła od niepełnego kanału i od celowego stronicowania listy,
bez zapisu do prawdziwej biblioteki użytkownika.

## Diagnoza

- Publiczny kanał `https://new.tyflopodcast.pl/feed/podcast/` miał podczas
  odczytowej próby 2 904 wpisy, z czego 2 883 zawierały materiał. Plik miał
  2 466 218 bajtów, więc nie przekraczał limitu odpowiedzi 5 MiB, i został
  pobrany w około sekundę.
- Parser RSS przyjmował najwyżej 1 000 poprawnych odcinków i ucinał resztę bez
  informacji dla hosta ani użytkownika. To potwierdzony defekt źródłowy.
- Odczyt prawdziwej bazy wyłącznie w trybie SQLite `mode=ro` wykazał 1 023
  zapisane odcinki TyfloPodcast i ostatnie udane odświeżenie 23.10.2026 o
  00:01:18. Sieć, parser i zapis nie zawiodły wtedy całkowicie; wynik był
  ograniczony przez dawny limit i wcześniejsze zachowane rekordy.
- 89 źródeł należących do Biblioteki miało ponad 150 odcinków, a siedem ponad
  1 000. Interfejs wczytywał celowo porcje po 150, ale mówił tylko liczbę
  widocznej porcji. Nie podawał `150 z N`, więc poprawne stronicowanie mogło
  wyglądać jak brak reszty.
- Pięć kolejnych otwarć TyfloPodcast przez produkcyjny moduł odczytu, nadal
  `mode=ro`, zwróciło 150 wierszy i użytkowy wiersz doładowania. Pierwsze
  trwało 165,6 ms, kolejne 21,9–24,6 ms. Nie potwierdzono awarii SQLite ani
  braku całego źródła.
- Dziennik `amc.log` potwierdzał wcześniejsze odtwarzanie TyfloPodcast, ale nie
  zawierał przyczyny nieudanego odświeżenia. Host zapisywał tylko nazwę klasy
  wyjątku do standardowego błędu, a odpowiedź dla interfejsu niosła wyłącznie
  liczniki. Interfejs nie rozróżniał pełnego, częściowego i nieudanego wyniku.

## Materiał do dokumentacji użytkownika

W sesji **Podcasty i YouTube** klawisz `F5` odświeża wybrane źródło, a
`Ctrl+F5` wszystkie źródła. AMC od razu mówi, że operacja trwa. Po zakończeniu
podaje osobno liczbę źródeł odświeżonych w całości, częściowo i nieodświeżonych.
Przy błędzie podaje nazwę źródła oraz zrozumiałą przyczynę, na przykład brak
połączenia, przekroczenie czasu lub nieprawidłowy dokument RSS. Widok zostaje
ponownie otwarty na tym samym odcinku, jeśli nadal istnieje.

Duży kanał jest wyświetlany porcjami po 150 odcinków. Po otwarciu AMC mówi na
przykład **TyfloPodcast, wczytano 150 z 1023 odcinków**. Ostatni wiersz
**Załaduj więcej odcinków** podaje ten sam postęp; Enter doładowuje następną
porcję. Jest to stronicowanie interfejsu, a nie brak odcinków w bibliotece.

Parser przyjmuje obecnie do 5 000 poprawnych odcinków z jednego dokumentu RSS
lub Atom. Jeśli kanał przekracza także ten bezpieczny limit, AMC zapisuje
dostępną część, ale wyraźnie nazywa wynik częściowym zamiast pełnym sukcesem.

## Uzasadnienie i decyzje

- Prawdziwy profil był wyłącznie czytany. Próby sieciowe użyły publicznego RSS,
  a testy zapisu korzystają wyłącznie z tymczasowych ustawień i baz.
- Limit pozostaje skończony jako druga bramka po limicie 5 MiB, ale wzrasta do
  5 000. Przekroczenie nie jest już udawane jako pełny sukces.
- Poszerzenie okna parsera nie może oznaczyć całego historycznego archiwum jako
  nowych odcinków. Za nowe uznawane są wpisy przed pierwszym znanym odcinkiem;
  późniejszy, wcześniej niewidoczny archiwalny ogon jest zachowywany bez
  zalewania Skrzynki.
- Teksty błędów są składane wyłącznie z jawnej nazwy źródła i kontrolowanego
  opisu użytkowego. Identyfikator, adres, typ wyjątku i reprezentacja obiektu
  nie trafiają do etykiety NVDA.

## Testy i wynik

- Publiczny RSS TyfloPodcast, zapisany wyłącznie jako materiał diagnostyczny:
  produkcyjny parser zwrócił 2 883 odcinki z materiałem, bez obcięcia. Sam
  dokument miał 2 904 wpisy i 2 466 218 bajtów.
- Prawdziwa baza użytkownika, otwarta produkcyjnym modułem wyłącznie w trybie
  SQLite `mode=ro`: `loaded=150`, `total=1023`, `has_more=True`; użytkowy opis
  wiersza doładowania zawierał `wczytano 150 z 1023`.
- Wybrana regresja wxPython: 177 testów zaliczonych, 0 niezaliczonych, w tym
  odświeżanie, źródło i nawigacja podcastów, brama zadań asynchronicznych,
  klient hosta, menu oraz spis skrótów.
- Sprawdzenie składni trzech zmienionych modułów Pythona: zaliczone.
- Nowe testy Core zaliczyły kanał z 2 904 odcinkami, jawne przekroczenie limitu
  oraz dołączenie archiwum bez zalania Skrzynki. Pełny przebieg SmokeTests
  przeszedł wszystkie sekcje podcastowe, po czym zatrzymał się na istniejącym,
  niezwiązanym kontrakcie instalatora dotyczącym `ShellApplicationName`.
  Plików instalatora ani tego testu w zadaniu nie zmieniano; pełnej regresji
  Core nie przedstawia się więc jako całkowicie zaliczonej.
- Kompilacja Release projektu Core SmokeTests: 0 ostrzeżeń, 0 błędów.
- Kompilacja Release `AccessibleMediaController.LiteHost`: 0 ostrzeżeń,
  0 błędów.
- Kontrola `git diff --check`: zaliczona.
- Testów manualnych NVDA nie wykonywano, zgodnie z zakazem uruchamiania żywej
  aplikacji w tym zadaniu.

## Znane ograniczenia

- Ręczny odsłuch NVDA nie jest wykonywany w tym izolowanym worktree.
- Kanał zawierający ponad 5 000 poprawnych odcinków nadal jest ograniczany,
  ale użytkownik otrzymuje teraz jawny wynik częściowy wraz z liczbą wczytanych
  pozycji.
- Fizyczne żądanie sieciowe rozpoczęte przez odświeżenie nie ma osobnego
  przycisku przerwania. Interfejs pozostaje responsywny, a wspólna brama
  generacji odrzuca spóźniony wynik po nowszym otwarciu lub zamknięciu okna.

## Wersja i commit

- Bazowy commit gałęzi roboczej: `609aa644`.
- Gałąź: `task/podcasty-tyflo`.
- Commit kodu, testów i pierwszego zapisu dokumentacji: `405267f7`.
- Build źródeł: wykonany pomyślnie dla Core SmokeTests i LiteHost, bez
  ostrzeżeń i błędów.
- Instalacja AMC Test/Public: niewykonana i niedozwolona w tym zadaniu.
- Instalator i publikacja: bez zmian.

## Roboczy wpis do changelogu

- Duże kanały podcastów nie są już po cichu ucinane do 1 000 odcinków.
  TyfloPodcast został odczytany jako 2 883 odcinki z materiałem.
- Odświeżanie podaje oddzielnie wynik pełny, częściowy i nieudany oraz
  zrozumiałą przyczynę dla konkretnego źródła.
- Lista dużego podcastu mówi `wczytano N z całości`, a Enter na wierszu
  **Załaduj więcej odcinków** doładowuje następną porcję bez utraty kontekstu.
- Poszerzenie zakresu kanału zachowuje historyczne odcinki bez oznaczania
  całego odzyskanego archiwum jako nowych pozycji w Skrzynce.

