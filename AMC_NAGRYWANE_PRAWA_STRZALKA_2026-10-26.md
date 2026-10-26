# AMC — prawa strzałka w Nagrywanych i Harmonogramie

Data: 26 października 2026 r.

## Zachowanie użytkowe

- W widoku `Nagrywane`, otwieranym przez `Alt+R`, `Strzałka w lewo` nadal
  podaje parametry odbieranego strumienia radiowego.
- W tym samym widoku `Strzałka w prawo` podaje ustawienia pliku wynikowego:
  bitrate albo rodzaj zapisu, nazwę bieżącego pliku oraz miejsce zapisu.
- Folder ogólny jest mówiony jako `folder domyślny`. Inny folder jest mówiony
  samą pełną ścieżką, bez etykiety `folder:`.
- Przed utworzeniem pierwszego pliku komunikat używa tekstu
  `plik przygotowywany` zamiast nazwy typu, pustej wartości albo ścieżki
  technicznej.
- W Harmonogramie `Strzałka w prawo` podaje ten sam krótki zestaw danych dla
  wybranego planu. Nie zaczyna od słowa `Źródło`, nazwy stacji ani adresu URL.
- Przykładowe komunikaty:
  - `192 kb/s, plik audycja.mp3, folder domyślny`;
  - `FLAC, plik przygotowywany, D:\Nagrania radia`.

## Lokalizacje i wspólny kontrakt

- `src/AccessibleMediaController.Core/Presentation/RadioRecordingOutputDescription.cs`
  jest jednym formatterem użytkowego komunikatu dla aktywnego nagrania i
  harmonogramu.
- `src/AccessibleMediaController.Windows/MainWindow.xaml.cs` rozdziela gesty
  listy `Nagrywane`, zachowuje rzeczywisty folder uruchomionego nagrania i
  aktualizuje pomoc kontekstową `Ctrl+F1`.
- `src/AccessibleMediaController.Windows/RadioSchedulesWindow.xaml.cs` kieruje
  prawą strzałkę do wspólnego formattera. Używa efektywnego formatu i bitrate,
  rozszerza przykładową nazwę pliku i rozróżnia folder domyślny, folder stacji
  oraz folder wpisany w planie.
- `src/AccessibleMediaController.Windows/RadioSchedulesWindow.xaml` uzupełnia
  widoczną instrukcję i tekst pomocy UI Automation.
- `src/AccessibleMediaController.Core/Presentation/ShortcutHelpCatalog.cs`
  dodaje oba konteksty do pełnej pomocy. Nie dodano pozycji do palety poleceń,
  ponieważ gest tylko odczytuje zaznaczony wiersz i nie jest samodzielnym
  poleceniem aplikacji.

## Korekta wcześniejszej decyzji

Korekta użytkownika z 26 października 2026 r. zastępuje zapis z 18 października
w `AMC06_HARMONOGRAMY_DATA_CZAS_DZIEN_2026-10-18.md`, który przypisywał prawej
strzałce rozbudowaną część czasową. Bieżącym znaczeniem prawej strzałki w
Harmonogramie jest krótki opis pliku wynikowego bez wstępu `Źródło`.
Rozbudowane informacje czasowe pozostają niewdrożonym zakresem AMC06.

## Testy i rzeczywiste wyniki

- Kompilacja projektu
  `tests/AccessibleMediaController.Windows.SmokeTests/AccessibleMediaController.Windows.SmokeTests.csproj`
  w konfiguracji Debug: zaliczona, 0 ostrzeżeń i 0 błędów.
- `--active-recording-output`: zaliczony. Test rzeczywistego handlera WPF
  potwierdził, że lewa strzałka mówi `AAC` i bitrate strumienia `128`, a prawa
  mówi bitrate zapisu `192`, nazwę pliku i folder domyślny. Oba zdarzenia były
  obsłużone i fokus pozostał w kontrolce listy. Po usunięciu niestabilności
  aparatury startowej test zaliczono trzy razy z rzędu.
- `--schedule-copy`: 9 z 9 testów zaliczonych. Nowy przypadek potwierdził
  prawą strzałkę, brak `Źródło` i URL-a, `folder domyślny`, samą ścieżkę
  niestandardową oraz brak etykiety `folder:`.
- Pierwsza próba kompilacji ujawniła wcześniejszy, niezwiązany błąd w
  `RadioRecognitionHistoryWindow.xaml.cs`: użycie `HttpRequestException` bez
  `using System.Net.Http`. Dodano wyłącznie brakujący import. Ponowna
  kompilacja zakończyła się powodzeniem.
- Pierwsza końcowa powtórka testu strzałek ujawniła, że zdarzenie
  `ContentRendered` mogło po przygotowaniu sztucznego wiersza przywrócić widok
  startowy. Aparatura ustawia teraz sesję i widok dopiero po opróżnieniu kolejki
  startowej. Nie zmieniono z tego powodu kodu produkcyjnego.

## Stan weryfikacji

- Zmiany źródłowe: wykonane.
- Testy automatyczne: wskazane wyżej testy wąskie zaliczone.
- Kompilacja: zaliczona.
- Ręczny test z NVDA: niewykonany.

## Znane ograniczenia i migracja

- Nie zmienia się format ustawień ani danych użytkownika; migracja nie jest
  potrzebna.
- Dla MP3 i M4A/AAC komunikat zaczyna się od bitrate. Dla FLAC, WAV i zapisu
  oryginalnego strumienia zaczyna się odpowiednio od rodzaju zapisu, ponieważ
  ustawienie bitrate nie ma tam tego samego znaczenia.
- Ręczny test powinien objąć pierwszą chwilę przed utworzeniem pliku, podział
  na nową część, folder ogólny, folder stacji i folder planu oraz ponowne
  otwarcie Harmonogramu.

## Szkic instrukcji użytkownika

1. Otwórz `Nagrywane` przez `Alt+R`.
2. Ustaw fokus na nagrywanym pliku.
3. Naciśnij lewą strzałkę, aby usłyszeć parametry transmisji.
4. Naciśnij prawą strzałkę, aby usłyszeć bitrate lub rodzaj pliku, jego nazwę
   i folder zapisu.
5. W Harmonogramie użyj prawej strzałki na planie, aby usłyszeć taki sam krótki
   opis planowanego pliku bez powtarzania źródła.

## Szkic changelogu

- Rozdzielono informacje o odbieranym strumieniu i zapisywanym pliku w widoku
  `Nagrywane`: lewa strzałka opisuje strumień, prawa ustawienia zapisu.
- Skrócono prawą strzałkę w Harmonogramie: komunikat zaczyna się od bitrate lub
  rodzaju zapisu i nie powtarza źródła.
- Dodano jawne opisy gestów do pomocy kontekstowej, pełnej pomocy i tekstu
  pomocy UI Automation.

Tekst instrukcji i changelogu jest szkicem do korekty i zatwierdzenia przez
użytkownika; nie został opublikowany.
