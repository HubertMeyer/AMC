# AMC02 — realizacja etapu A bez uruchamiania

Data: 18 października 2026 r.

## Co zmieniono

### Krótkie etykiety nagrań

Pliki:

- `src/AccessibleMediaController.Core/Presentation/RadioRecordingRowLabels.cs`
- `src/AccessibleMediaController.Windows/MainWindow.RecordingFiles.cs`
- `src/AccessibleMediaController.Windows/MainWindow.xaml.cs`

Zmiany:

- `Alt+R` buduje wiersze z bieżącej ścieżki kontrolera nagrania: `Nagrywane, nazwa pliku`.
- Zwykły plik w historii ma etykietę `Nagrane, nazwa pliku`.
- Wpisy przerwane, zatrzymane, nieudane, brakujące i chwilowo niedostępne zachowują swój rzeczywisty stan.
- Z etykiet zwykłej listy usunięto stację, harmonogram, datę, godzinę i folder.
- Nieudana próba bez pliku zachowuje nazwę stacji i powód, ponieważ nie ma nazwy pliku, która pozwoliłaby ją rozpoznać.
- Pełna informacja o brakującym pliku i folderze nadal jest używana po świadomej próbie otwarcia niedostępnego wpisu.

### Fokus NVDA

Pliki:

- `src/AccessibleMediaController.Windows/MainWindow.TransientPreviews.cs`
- `src/AccessibleMediaController.Windows/MainWindow.xaml.cs`

Zmiany:

- `Alt+R` i `Alt+Shift+R` używają procedury, która fokusuje konkretny zaznaczony wiersz.
- Procedura nie ustawia przejściowo fokusa na całej liście, więc usuwa źródło osobnego komunikatu „X elementów”.
- Gdy lista jest pusta, jej jawna nazwa brzmi odpowiednio `Nagrywane, lista pusta` albo `Historia nagrywania, lista pusta`.
- Opóźnione ponowienie sprawdza bieżący widok i identyfikator elementu, dlatego nie powinno przenosić fokusa po opuszczeniu podglądu.
- Istniejąca, osobna pamięć zaznaczenia według sesji i widoku została zachowana.

### Szczegóły nagrania pod strzałką w lewo

Pliki:

- `src/AccessibleMediaController.Core/Presentation/QuickMediaInformationFormatter.cs`
- `src/AccessibleMediaController.Windows/MainWindow.xaml.cs`

Zmiany:

- Na liście `Historia nagrywania` oraz na lokalnym wpisie Historii odtwarzania otwieranej przez `Ctrl+H` `strzałka w lewo` podaje istniejące informacje o bitrate i wielkości oraz dopisuje użytkową nazwę folderu, na przykład `folder Nagrania próby`.
- Folder jest dodatkiem do komunikatu wywołanego świadomie; zwykły wiersz pozostaje krótki: `Nagrane, nazwa pliku`.
- Wpisy internetowe w `Ctrl+H` nie dostają folderu: przed utworzeniem etykiety kod potwierdza, że źródło jest lokalną ścieżką.
- Pozostałe listy zachowują dotychczasowy komunikat lewej strzałki.
- `Ctrl+F1` opisuje w obu widokach bitrate, wielkość i folder lokalnego pliku. Nie dodano osobnej pozycji do palety `Ctrl+Shift+K`, ponieważ nie jest to nowe polecenie, tylko kontekstowe zachowanie istniejącej strzałki.

### Pomoc, paleta i menu

Pliki:

- `src/AccessibleMediaController.Core/Commands/CommandCatalog.cs`
- `src/AccessibleMediaController.Core/Presentation/ShortcutHelpCatalog.cs`
- `src/AccessibleMediaController.Core/Presentation/TransientPreviewNavigation.cs`
- `src/AccessibleMediaController.Windows/MainWindow.xaml`
- `src/AccessibleMediaController.Windows/MainWindow.TransientPreviews.cs`

Zmiany:

- Paleta `Ctrl+Shift+K` nazywa polecenie `Pokaż aktualnie nagrywane pliki`.
- Pomoc `Ctrl+F1` wyjaśnia, że każdy wiersz podaje stan i nazwę pliku.
- Menu i komunikaty dostępności używają określenia `nagrywane pliki`, nie `nagrywane stacje`.
- `Alt+Shift+R` pozostaje poleceniem `Pokaż historię nagrywania`.

### Testy źródłowe

Pliki:

- `tests/AccessibleMediaController.Core.SmokeTests/RecordingMoveAndFolderRowTests.cs`
- `tests/AccessibleMediaController.Core.SmokeTests/Program.cs`
- `tests/AccessibleMediaController.Windows.SmokeTests/RecordingFilesAcceptanceTests.cs`

Przygotowane kontrole obejmują:

- dokładny format `Nagrywane, nazwa` i `Nagrane, nazwa`;
- brak stacji, harmonogramu, daty i folderu w zwykłym wierszu;
- zachowanie stanów błędu, przerwania, braku pliku i niedostępnego folderu;
- zmianę nazwy i przeniesienie pliku bez utraty powiązania;
- deduplikację pliku bibliotecznego i wpisu historii;
- czytelną nazwę zastępczą przed przygotowaniem ścieżki aktywnego nagrania;
- nazwę polecenia używaną przez paletę.
- format komunikatu szczegółów nagrania zawierający bitrate, wielkość i jawną etykietę folderu.

## Kontrole wykonane bez uruchamiania

- Punktowy przegląd wszystkich nowych symboli i odwołań.
- Wyszukanie martwych nazw starych metod oraz starych tekstów „nagrywane stacje”: brak wyników w kodzie użytkowym i testach objętych zmianą.
- `git diff --check` dla plików AMC02: bez błędów.

Nie wykonano kompilacji ani testów binarnych, więc przygotowanych testów nie oznaczono jako zaliczone.

## Czego nie wykonano

- Nie kompilowano rozwiązania ani dodatku NVDA.
- Nie uruchamiano AMC i nie restartowano NVDA.
- Nie rozpoczynano ani nie zatrzymywano żadnego nagrania.
- Nie zmieniano formatu danych ani ustawień; migracja nie jest potrzebna.
- Nie zmieniano skrótów `Alt+R` i `Alt+Shift+R`.

## Bramka 1 — lista prób AMC01 + AMC02

Po potwierdzeniu, że nic nie jest nagrywane:

1. Sprawdzić stan uruchomionej instancji i dopiero wtedy wykonać jedną kompilację aplikacji oraz dodatku NVDA.
2. Uruchomić automatyczne testy Core i Windows dotyczące AMC01 i AMC02.
3. NVDA: `Alt+R` przy jednym i kilku aktywnych nagraniach, przed i po utworzeniu pliku oraz po podziale nagrania.
4. NVDA: `Alt+Shift+R` dla nagrania ukończonego, zatrzymanego, przerwanego, nieudanego, brakującego i na chwilowo niedostępnym dysku.
5. Potwierdzić kolejność: nagłówek lub stan, nazwa pliku, standardowa pozycja `1 z N`; bez osobnego `X elementów`.
6. Zmienić zaznaczenie, opuścić każdy widok, wejść ponownie i potwierdzić osobną pamięć ostatniego elementu.
7. Sprawdzić `Ctrl+F1`, `Ctrl+Shift+K` i menu dla obu poleceń.
8. Na kilku nagranych plikach nacisnąć `strzałkę w lewo` i potwierdzić bitrate, wielkość oraz właściwy folder, bez powtórzenia nazwy pliku; sprawdzić również opis tego gestu w `Ctrl+F1`.
9. Otworzyć `Ctrl+H`, sprawdzić lewą strzałkę na lokalnym pliku oraz na wpisie internetowym: lokalny ma podać folder, internetowy nie może udawać ścieżki na dysku.
10. W tej samej sesji wykonać scenariusze AMC01: `Ctrl+C`, prawa strzałka i `Ctrl+Shift+L` w wyszukiwaniu, w tym kanał YouTube.

## Uwaga o stanie repozytorium

Repozytorium zawierało wcześniej liczne niezapisane zmiany, także w `MainWindow.xaml.cs`, `MainWindow.xaml`, katalogach poleceń i testach. AMC02 zastosowano punktowo do bieżącej zawartości. Nie cofano ani nie zastępowano pozostałej pracy.
