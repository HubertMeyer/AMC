# YT-005 — skrzynka Ctrl+I i polskie tytuły YouTube

## Status

W trakcie. Kod, 141 testów Pythona, dwie regresje C# oraz odczytowe próby
prawdziwej biblioteki i publicznego YouTube są zweryfikowane. Nie zbudowano
paczki użytkowej, nie zainstalowano jej i nie wykonano jeszcze ręcznego odbioru
NVDA.

## Zgłoszenie użytkownika

27 października 2026 użytkownik potwierdził, że porcje po 150 pozycji są
potrzebne, ale pierwsza porcja skrzynki obejmuje jedynie około pół dnia przy
dużej liczbie obserwowanych podcastów i kanałów YouTube. Poprosił, aby kolejne
naciśnięcia `Ctrl+I` doładowywały dalsze porcje po 150. Zgłosił też, że część
tytułów filmów YouTube ponownie jest wyświetlana po angielsku.

Ta korekta zastępuje wcześniejsze założenie z POD-003, że sam końcowy wiersz
**Załaduj więcej** wystarcza jako jedyna droga szybkiego doładowania skrzynki.

Późniejsza korekta użytkownika z 27 października 2026 zastępuje zbyt wąskie
uzasadnienie, według którego porcje po 150 służą tylko ochronie interfejsu.
Porcja 150 dotyczy prezentacji, natomiast właściwym celem jest także pełny,
ciągły obieg odświeżania wszystkich obserwowanych źródeł, tak aby materiały z
całego dnia były zapisane i dostępne do przejrzenia.

## Diagnoza

- Odczytowa kontrola prawdziwej bazy wykazała 27 862 pozycje w skrzynce, a
  pierwsze 150 obejmowało około 14 godzin. Dane użytkownika nie zostały
  zmienione.
- `Ctrl+I` ponownie otwierało ten sam widok, ale żądało poprzedniej liczby
  pozycji zamiast następnej porcji. Enter na wierszu doładowania działał.
- Argument kolekcji yt-dlp łączył `youtubetab:approximate_date` z pozbawionym
  nazwy ekstraktora `lang=pl`. Ustawienie języka nie trafiało więc do
  ekstraktora `youtube`. Kanałowy Atom poprawiał tytuły tylko dla niewielkiej
  liczby najnowszych materiałów, a starsze pozycje mogły zachować automatyczne
  tłumaczenie angielskie.
- Korekta z 27 października 2026 zastępuje wcześniejszy komentarz źródłowy z
  11 września 2026, według którego dwie opcje `--extractor-args` nie mogły
  działać razem. Oficjalny kontrakt yt-dlp pozwala powtórzyć opcję dla różnych
  ekstraktorów; średnik rozdziela argumenty tylko w obrębie jednego ekstraktora.
- Odczytowa kontrola bieżącej biblioteki wykazała 523 obserwowane źródła.
  Odświeżanie było włączone dla 521 z nich, rozmiar partii wynosił 5, a każde z
  521 aktywnych źródeł miało próbę odświeżenia w ostatnich 3 godzinach. To
  potwierdza, że automat przechodzi przez kolejne partie zamiast zatrzymywać się
  na pierwszej.

## Materiał do dokumentacji użytkownika

Pierwsze `Ctrl+I` otwiera **Nowe odcinki i materiały** i wczytuje 150 pozycji.
Kolejne `Ctrl+I`, gdy ta skrzynka jest otwarta, doładowuje następne 150 i
ustawia fokus na pierwszej nowej pozycji. Nadal można użyć Enter na końcowym
wierszu **Załaduj więcej**. `Ctrl+I` nie pobiera danych z sieci; pokazuje dane
już zapisane. Odświeżanie sieciowe uruchamia `F5` lub `Ctrl+F5` zgodnie z
kontekstem.

Po odświeżeniu kanału lub playlisty YouTube AMC prosi yt-dlp o polskie
metadane. Zapisane wcześniej tytuły zostaną zaktualizowane przy następnym
odświeżeniu źródła.

## Uzasadnienie i decyzje

- Rozmiar porcji pozostaje równy 150, aby bardzo duża skrzynka nie blokowała
  interfejsu ani czytnika ekranu. Nie ogranicza liczby materiałów zapisanych
  przez synchronizację.
- Automatyczne odświeżanie co minutę zleca następną partię należnych źródeł.
  Źródła są uporządkowane od najdawniej sprawdzanych, więc kolejne przebiegi
  domykają całą kolejkę bez głodzenia dalszych źródeł.
- Powtórne `Ctrl+I` jest drugim wejściem do istniejącej operacji doładowania;
  nie tworzy osobnej listy i nie zmienia zachowania Escape.
- Nazwa, skrót i opis polecenia pochodzą ze wspólnego modelu używanego przez
  menu, paletę, pełną pomoc i Pomoc klawiatury.
- yt-dlp otrzymuje dwa jawne argumenty ekstraktorów: `youtubetab` dla dat
  oraz `youtube` dla języka metadanych. Jest to składnia udokumentowana przez
  dostawcę i sprawdzona z zainstalowanym komponentem.

## Testy i wynik

- `python -m pytest` dla polityki podglądu, palety poleceń, menu, skrótów i
  nawigacji Podcastów: **126 zaliczonych w 6,64 s**.
- `dotnet run --project tests/AccessibleMediaController.Windows.SmokeTests
  -c Release --no-restore --disable-build-servers --
  --youtube-collection-normalization`: **zaliczony**, komunikat
  „OK: ograniczone kanały i playlisty publicznego YouTube”. Polecenie
  skompilowało cel testowy i jego zależności; nie jest to build paczki AMC.
- Zainstalowany, zweryfikowany yt-dlp 2026.08.19 otrzymał dwa osobne
  `--extractor-args` zgodne z kodem i dla trzech pozycji publicznego kanału
  zwrócił polskie tytuły. Nie pobierano filmów.
- `git -c core.whitespace=cr-at-eol diff --check`: **bez błędów** przed
  commitem. Opcja uwzględnia kanoniczne końce CRLF pliku testów C#.
- Próba systemowym Pythonem nie uruchomiła testów, ponieważ nie miał modułu
  pytest. Powtórzenie przypiętym środowiskiem projektu dało wynik powyżej.
- Szerszy plik `test_podcast_source.py` został przerwany po braku postępu w
  piaskownicy; nie jest liczony jako zaliczenie ani jako regresja produktu.
- Dodano regresję pięciu należnych źródeł przy partii równej 2. Oczekiwane
  przebiegi mają rozmiary 2, 2 i 1, każde źródło występuje dokładnie raz, a po
  pełnym obiegu żadne nie jest od razu ponownie należne.
- `pytest tests/test_general_settings_dialog.py`: **15 zaliczonych w 0,38 s**;
  kontroluje też zgodny podpis „Liczba źródeł sprawdzanych w jednym przebiegu”.
- `dotnet run --project
  tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj
  -c Release --no-restore --disable-build-servers -- --podcast-progress`:
  **zaliczony**, komunikat „Wszystkie zestawy przeszły (1)”.
- Pierwsza kompilacja nowej regresji ujawniła użycie wewnętrznej klasy bazy,
  niedostępnej dla projektu testowego. Test poprawiono tak, aby przygotowywał
  własną izolowaną bazę przez publiczną bramę i SQLite; końcowy wynik jest
  zaliczony i tylko ten wynik stanowi dowód funkcji.

## Testy NVDA i klawiatury

Automatyczne testy sprawdzają pierwsze i ponowne `Ctrl+I`, niezmieniony punkt
powrotu Escape oraz zgodność menu, palety i obu rodzajów pomocy. Ręczny odbiór
NVDA nowej kompilacji pozostaje do wykonania po zbudowaniu i instalacji.

Przy doładowaniu fokus logiczny trafia na pierwszą nową pozycję. Pomoc i Pomoc
klawiatury podają: „Otwórz nowe odcinki i materiały; w otwartej skrzynce wczytaj
kolejne 150 pozycji”. Menu i paleta używają nazwy „Nowe odcinki i materiały”,
bez identyfikatora technicznego.

## Różnice trybów i migracja

- Pierwsze `Ctrl+I` działa jako dotychczasowy globalny podgląd; Escape wraca
  do zapamiętanej sesji i pozycji. Doładowanie następuje tylko wtedy, gdy
  skrzynka jest już otwarta.
- Pozycja menu i palety pozostaje kontekstowa dla sesji Podcasty i YouTube.
- Nie ma migracji schematu ani jednorazowej zmiany bazy. Stare tytuły zostaną
  poprawione przy zwykłym odświeżeniu źródła.

## Zmienione pliki

- Zachowanie i wspólny kontrakt polecenia: `gui.py`, `shortcuts.py`,
  `menu_model.py`.
- Czytelny podpis ustawienia partii: `gui.py`; regresja etykiety:
  `test_general_settings_dialog.py`.
- YouTube: `YouTubeCollectionClient.cs`.
- Regresje: `test_transient_preview_policy.py`, `test_command_palette.py`
  `AccessibleMediaController.Windows.SmokeTests/Program.cs` oraz
  `PodcastProgressStoreTests.cs`.
- Dokumentacja: `MEDIA_CONTROLLER_PL.md`, rejestr i ten zapis zadania.

## Znane ograniczenia

- Poprawa już zapisanych tytułów wymaga odświeżenia odpowiedniego źródła.
- Źródło publiczne YouTube nadal ma bezpieczny limit 100 pozycji na jedno
  odświeżenie; limit 150 dotyczy wyłącznie liczby pozycji pokazanych naraz w
  zbiorczym widoku skrzynki.
- Pełny obieg działa, gdy AMC pozostaje uruchomione. Po zamknięciu programu
  automat wznawia wybór najdawniej sprawdzanych źródeł przy następnym
  uruchomieniu.

## Wersja i commit

Zmiana źródłowa: commit `054240cb` na gałęzi
`codex/konfigurowalne-skroty-20261026`.
Korekta opisu ustawienia i regresja pełnego obiegu automatycznego odświeżania:
commit `eefb1d71` na tej samej gałęzi.

Wersja użytkowa nie została zbudowana, zainstalowana ani opublikowana. Stan
zainstalowanego AMC Test nie jest dowodem tej poprawki i nie został zmieniony.
