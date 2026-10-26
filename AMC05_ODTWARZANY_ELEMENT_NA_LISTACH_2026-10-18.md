# AMC05 — odtwarzany element na listach

Data przygotowania i zatwierdzenia zakresu: 18 października 2026 r.

Status: specyfikacja poziomu A zatwierdzona do późniejszego wdrożenia produkcyjnego. Kod produkcyjny AMC05 nie został jeszcze zmieniony. Nie wykonano kompilacji ani uruchomienia programu.

## Zgłoszone zachowanie

Radio poprawnie pozwala rozpoznać na liście aktualnie odtwarzaną stację. Na innych listach NVDA nie zawsze podaje stan odtwarzanego elementu. Stan może też zniknąć po odświeżeniu widoku albo po ponownym wejściu na listę.

## Wynik audytu źródłowego

1. Główna lista ma prawidłowe jawne powiązanie `AutomationProperties.Name` z użytkową właściwością `Label`. Nie jest to błąd wynikający z domyślnej reprezentacji obiektu.
2. `FormatListItem` umie obecnie dodać stan bieżącego elementu, ale robi to równocześnie z budowaniem całej etykiety treści.
3. Część widoków tworzy własne, bogatsze etykiety bez użycia tego formatera. Dotyczy to między innymi szczegółowych list odcinków podcastów, historii nagrywania i listy nagranych plików.
4. `RefreshPlaybackIndicators` ponownie wywołuje ogólny formatter. Może więc dodać stan po zdarzeniu odtwarzania, ale przy tym zgubić szczegóły etykiety właściwe dla danego widoku. Ponowne zbudowanie specjalizowanego widoku może z kolei usunąć stan.
5. Obecny mechanizm porównuje identyfikator wiersza z bieżącym elementem aktualnej sesji. To nie wystarcza dla list łączących dane z różnych sesji ani dla wierszy pośrednich.
6. Ustawienie `FollowPlaybackOnPlayerExit` już osobno steruje przeniesieniem zaznaczenia po powrocie z odtwarzacza. AMC05 nie może zastąpić tego ustawienia automatycznym przestawianiem fokusa.

Wniosek: trzeba rozdzielić stałą treść wiersza od dynamicznego stanu odtwarzania. Doraźne dopisywanie tekstu w kolejnych fabrykach list tylko powieliłoby błąd.

## Zatwierdzone zachowanie

- Każdy wiersz reprezentujący dokładnie odtwarzany materiał otrzymuje w jawnej nazwie dostępności stan `Odtwarzane`.
- Po pauzie ten sam wiersz otrzymuje stan `Wstrzymane`.
- Stan nie zastępuje tytułu, autora, daty, czasu, postępu ani innych informacji właściwych dla danego widoku.
- Stan jest obliczany z pary: sesja i stabilny identyfikator materiału. Taki sam identyfikator w innej sesji nie może oznaczyć niewłaściwego wiersza.
- Zmiana elementu, automatyczne przejście do następnego, pauza, wznowienie, zakończenie i błąd odtwarzania aktualizują stary oraz nowy wiersz bez przebudowy całej listy, jeśli nie jest ona konieczna z innego powodu.
- Odświeżenie, filtrowanie, powrót z odtwarzacza, zmiana widoku i ponowne otwarcie listy zachowują prawidłowy stan.
- Stan nie przesuwa fokusa i nie zmienia zaznaczenia. Jeżeli użytkownik chce, aby po wyjściu z odtwarzacza fokus przeszedł na grający element, nadal służy do tego istniejące ustawienie `Po wyjściu z odtwarzacza ustaw fokus na aktualnie odtwarzanym elemencie`.
- Nie dodajemy osobnego komunikatu live region. NVDA ma odczytać stan razem z wierszem podczas zwykłej nawigacji, bez nakładającej się drugiej wypowiedzi.
- Dobrze działające zachowanie Radia zostaje zachowane i objęte testem regresji.

## Właściwe listy objęte zadaniem

### Wewnętrzne sesje AMC

- Pliki lokalne: Biblioteka, Wszystkie pliki, Foldery, zawartość albumu, Kolejka, Historia odtwarzania, Ulubione i zawartość playlist.
- Podcasty i YouTube: listy odcinków i materiałów, Nowe odcinki i materiały, W trakcie słuchania, Pobrane, Kolejka, Historia odtwarzania, Ulubione i zawartość playlist.
- Spotify i TIDAL odtwarzane wewnątrz AMC: listy utworów albumu, wykonawcy i playlisty, Biblioteka, Kolejka, Historia odtwarzania i Ulubione.
- Radio: Biblioteka stacji, Ulubione, Historia oraz zawartość playlist stacji.
- Historia nagrywania i lista nagranych plików: tylko wtedy, gdy wiersz wskazuje rzeczywisty, odtwarzany plik. Wpis nieudanego nagrania nie jest materiałem i nie otrzymuje stanu.
- Wyniki wyszukiwania: po zakończeniu zmian AMC01 mają używać tej samej reguły, bez utraty nazwy usługi i stanu Biblioteki.

### Świadome wyłączenia

- Foldery, albumy jako kontenery, podcasty jako kanały, playlisty jako kontenery, nagłówki, kategorie wykonawcy, `Wczytaj więcej` i inne wiersze techniczne.
- Zakładki nie otrzymują stanu tylko dlatego, że wskazują pozycję w aktualnym materiale. Wiele zakładek tego samego pliku nie może równocześnie udawać wielu odtwarzanych elementów.
- Zewnętrzne listy Sonos i WiiM otrzymają stan dopiero wtedy, gdy adapter ma świeżą i jednoznaczną informację o rzeczywiście odtwarzanym materiale. Nie wolno go wywnioskować z samego ostatniego polecenia. To pozostaje powiązane z AMC10.
- AMC05 nie zmienia działania Enter, Escape, F6, ustawienia śledzenia odtwarzania ani kolejności list.

## Projekt implementacji

1. Wiersz listy przechowuje osobno bazową etykietę użytkową i opcjonalną tożsamość materiału, którego stan może przedstawiać.
2. Wspólny prezenter nakłada na bazową etykietę jeden dynamiczny stan: odtwarzane, wstrzymane, ostatnio odtwarzane albo brak stanu.
3. Fabryki widoków nadal odpowiadają za własną treść, na przykład datę i postęp podcastu albo krótką nazwę nagranego pliku. Nie składają samodzielnie tekstu stanu odtwarzania.
4. `AutomationProperties.Name`, tekst wizualny wiersza i `ToString()` korzystają z tej samej końcowej etykiety użytkowej. Żaden identyfikator sesji, nazwa typu, rekord ani enum nie trafia do NVDA.
5. Zdarzenia transportu odświeżają dekorację stanu dla widocznych wierszy. Pełna przebudowa widoku pozostaje tylko tam, gdzie zmienia się jego zawartość.
6. Globalny wynik wyszukiwania może oznaczyć więcej niż jeden faktycznie grający materiał, jeśli różne sesje równolegle odtwarzają dźwięk. Każdy wynik musi wtedy być rozstrzygnięty przez właściwą sesję.

## Testy źródłowe do przygotowania przy wdrożeniu

1. Lokalny plik uruchomiony z Kolejki ma stan również w Bibliotece, Folderach, Historii i playliście zawierającej ten plik.
2. Odcinek uruchomiony z `Nowe odcinki i materiały` zachowuje stan na liście kanału po odświeżeniu i ponownym wejściu.
3. Utwór Spotify lub TIDAL uruchomiony z albumu ma stan w innych właściwych widokach tej samej sesji, bez oznaczenia kontenera albumu.
4. Zmiana z elementu A na B usuwa stan z A i dodaje go do B. Pauza i wznowienie zmieniają wyłącznie słowo stanu.
5. Identyczne tekstowo tytuły oraz identyczne identyfikatory należące do dwóch różnych sesji nie powodują fałszywego oznaczenia.
6. Filtr i ponowne otwarcie listy nie dublują prefiksu i nie usuwają szczegółów wiersza.
7. Folder, playlista, album, kategoria, zakładka, nieudane nagranie i `Wczytaj więcej` nigdy nie otrzymują stanu.
8. `AutomationProperties.Name` każdego zmienionego wiersza zawiera wyłącznie docelowy tekst użytkowy. Test obejmuje pierwszy fokus, strzałki, odświeżenie, powrót z odtwarzacza i ponowne otwarcie.
9. Przy wyłączonym śledzeniu odtwarzania zaznaczenie pozostaje na przeglądanym wierszu. Przy włączonym istniejące ustawienie przenosi fokus tylko wtedy, gdy bieżący materiał występuje w danym widoku.
10. Radio zachowuje dotychczas poprawne oznaczenie i nie otrzymuje podwójnego komunikatu.

## Dokumentacja i bramka

- AMC05 nie wprowadza nowego polecenia ani skrótu, więc nie dodaje osobnej pozycji do palety `Ctrl+Shift+K` ani pomocy `Ctrl+F1`.
- Opis znaczenia stanów listy należy uzupełnić w głównej instrukcji użytkownika przy wdrożeniu.
- Implementację, testy automatyczne i próbę NVDA należy połączyć w Bramce 2 z AMC04 oraz naprawą `End` z AMC13.
- Przed Bramką 2 trzeba ponownie potwierdzić, że AMC nie nagrywa.

## Poza zakresem tej decyzji

- Nie kompilowano i nie uruchamiano AMC.
- Nie zmieniano kodu produkcyjnego ani testów.
- Nie rozstrzygano jeszcze prezentacji zewnętrznego stanu Sonos i WiiM bez wiarygodnych danych adaptera.
