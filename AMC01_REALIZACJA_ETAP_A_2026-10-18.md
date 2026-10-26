# AMC01 — realizacja etapu A bez uruchamiania

Data: 18 października 2026 r.

## Co zmieniono

### Okno wyszukiwania

Plik: `src/AccessibleMediaController.Windows/SearchWindow.xaml.cs`

- Końcowy komunikat działania nie jest już poprzednikiem bezwarunkowego ponownego ustawienia fokusa.
- Fokus wraca na wynik tylko wtedy, gdy lista naprawdę go utraciła.
- Po `Ctrl+C` i `Ctrl+Shift+C` komunikat końcowy jest odkładany do czasu obsłużenia bieżącego wejścia i stabilizacji fokusa.
- Prawa strzałka zachowuje menu relacji TIDAL, a dla pozostałych wyników podaje krótką informację użytkową albo jawną etykietę wiersza. Zdarzenie nie trafia już do przypadkowej domyślnej obsługi WPF.
- Komunikaty odmowy oraz błędu zaznaczenia korzystają z tej samej kolejności: najpierw właściwy fokus, na końcu celowy komunikat.
- Dodano aktualizację stanu wiersza kanału lub podcastu po zmianie członkostwa w Bibliotece.
- Awaryjna nazwa usługi brzmi „Nieznana usługa”; identyfikator sesji nie jest ujawniany NVDA.

### Kanały YouTube z wyszukiwania

Plik: `src/AccessibleMediaController.Windows/MainWindow.xaml.cs`

- Asynchroniczny wynik dodawania kanału YouTube trafia do nadal aktywnego okna wyszukiwania, nie do ukrytego pod nim statusu głównego okna.
- Komunikaty rozróżniają kanał YouTube i zwykły podcast.
- Po sukcesie wiersz wyniku dostaje aktualny stan Biblioteki bez zamykania wyszukiwania.
- Po błędzie nie jest przywracany fokus głównej listy, jeżeli użytkownik nadal pracuje w oknie wyszukiwania.
- Dla nowego kanału komunikat początkowy podaje „Dodawanie kanału YouTube…”, a komunikat końcowy podaje rzeczywisty sukces albo przyczynę niepowodzenia.
- Dla kanału już znanego ponowne `Ctrl+Shift+L` korzysta z istniejącego przełącznika członkostwa, a stan wiersza jest odświeżany.

### Test regresji

Plik: `tests/AccessibleMediaController.Windows.SmokeTests/Program.cs`

- Rozszerzono istniejący test dostępności wyniku katalogu.
- Test sprawdza, że po zmianie członkostwa w Bibliotece etykieta UI Automation przechodzi na użytkowe „w Bibliotece”.
- Test nadal odrzuca ujawnienie technicznej nazwy typu `SearchResultRow`.

## Dlaczego tak

Dodatek NVDA nie rejestruje zwykłego `Ctrl+C`, prawej strzałki ani `Ctrl+Shift+L`. Źródłem zagłuszania był interfejs WPF: po właściwym komunikacie zlecał jeszcze zdarzenie fokusa. Poprawka zmienia kolejność i eliminuje zbędne zdarzenie, zamiast dodawać kolejne sztuczne komunikaty w dodatku NVDA.

Kanał YouTube jest dodawany asynchronicznie. Wcześniej rozpoczęcie operacji było widoczne w oknie wyszukiwania, ale wynik końcowy trafiał do głównego okna, a etykieta wiersza pozostawała stara. Teraz rozpoczęcie, wynik i stan wiersza należą do jednego kontekstu.

## Czego nie wykonano

- Nie kompilowano rozwiązania.
- Nie uruchamiano AMC.
- Nie instalowano ani nie restartowano dodatku NVDA.
- Nie wykonywano zapytania do YouTube na żywo.
- Nie zmieniano pomocy `Ctrl+F1` ani palety `Ctrl+Shift+K`, ponieważ AMC01 nie dodaje nowego polecenia ani skrótu; zmienia zachowanie już istniejących poleceń.

## Co sprawdzić na bramce AMC01 + AMC02

1. `Ctrl+C` na jednym i wielu wynikach: schowek oraz jeden końcowy komunikat.
2. Prawa strzałka na kanale YouTube, filmie YouTube, podcaście, radiu, Spotify i TIDAL.
3. `Ctrl+Shift+L` na nowym kanale YouTube, kanale już zapisanym i kanale usuwanym z Biblioteki.
4. Szybkie powtórzenia `Ctrl+C` i `Ctrl+Shift+L` bez technicznego „AMC Python”.
5. Początkowy fokus, strzałki, menu kontekstowe, powrót fokusa oraz ponowne otwarcie wyszukiwania.

## Uwaga o stanie repozytorium

Przed AMC01 repozytorium zawierało inne niezapisane zmiany, w tym w `MainWindow.xaml.cs` i programie testowym. Poprawkę zastosowano punktowo do bieżącej zawartości; istniejących zmian nie cofano ani nie zastępowano.
