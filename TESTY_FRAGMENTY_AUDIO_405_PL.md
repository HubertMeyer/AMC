# Fragmenty audio — jak sprawdzić alfa405

Do próby wybierz własne kopie dwóch plików dźwiękowych.

## Zapis do osobnego pliku

1. Otwórz plik lokalny w odtwarzaczu AMC. Klawiszem I oznacz początek, przejdź dalej i klawiszem O oznacz koniec.
2. Naciśnij Ctrl+S. Otworzy się „Zapisz fragment audio”. Dotychczasowy klawisz X już go nie otwiera.
3. Wybierz format i miejsce zapisu, zatwierdź. Sprawdź odtworzony wynik, jego początek, koniec oraz czas. Źródło powinno pozostać niezmienione.
4. Escape przed zapisem zamyka okno i wraca do odtwarzacza.

## Dopisanie na końcu istniejącego pliku

1. Przy tym samym zaznaczeniu naciśnij Ctrl+D. Czytnik ma odczytać okno „Dopisz fragment na końcu pliku” i pole „Istniejący plik docelowy”.
2. Wpisz ścieżkę innego istniejącego pliku albo wybierz go przyciskiem „Wybierz plik”. W oknie powinno istnieć tylko jedno pole edycyjne: „Istniejący plik docelowy”. Zasady są tekstem pomocy przycisku „Dopisz”, nie drugim polem edycyjnym.
3. Dopisz zachowuje dawny dźwięk na początku, a zaznaczenie umieszcza po nim. Źródło nie jest zmieniane. O zachowaniu kopii poprzedniej wersji decyduje ustawienie „Zachowuj kopie po edycji”; przy ustawieniu wyłączonym kopia znika dopiero po sprawdzeniu wyniku.
4. W trakcie pracy czytnik ma podawać kolejne etapy: przygotowanie fragmentu, łączenie plików i sprawdzanie gotowego pliku. Postęp nie powinien zatrzymać się pozornie na 70%. Po zakończeniu czytnik powinien odczytać wynik i rzeczywisty los kopii. Sprawdź dźwięk oraz sumę czasów; po zapisie fokus wraca do odtwarzacza.
5. Przy MP3, M4A, AAC, Ogg lub Opus program pyta o zgodę na ponowną kompresję całego celu. Może ona obniżyć jakość. Anulowanie pytania nie zapisuje zmian.
6. Po rozpoczęciu przycisk Anuluj zmienia się w „Przerwij”. Przerwanie przed podmianą nie może zmienić źródła ani celu i nie może pozostawić połowy dopisanego pliku.
7. Ten sam plik jako źródło i cel, uszkodzony plik, brak pliku, zapis tylko do odczytu albo zmiana celu w czasie operacji mają dać komunikat odmowy, nie sukces.

## Podcasty i słuchanie

W pobranym podcaście pełny fragment zaznaczony w widoku odtwarzacza uruchamia eksport przez Ctrl+S. Poza tym kontekstem Ctrl+S zachowuje dotychczasowy zapis odcinka. Otwieranie i zamykanie okien fragmentu nie powinno zmieniać odsłuchu, pozycji, głośności ani kolejki.

Menu i paleta poleceń zawierają także „Dopisz zaznaczony fragment na końcu pliku”. To skróty wewnątrz AMC, nie nowe systemowe skróty globalne.

## Usunięcie fragmentu z oryginalnego pliku

1. Na kopii lokalnego pliku zaznacz fragment klawiszami I oraz O i naciśnij Ctrl+X.
2. Powinno otworzyć się osobne okno „Usuń fragment z oryginalnego pliku”. Opis zakresu i skutków nie może być zgłaszany przez NVDA jako pole edycyjne.
3. Początkowy fokus ma znajdować się na „Anuluj”. Tab przechodzi do „Usuń fragment”, którego tekst pomocy podaje zakres, zatrzymanie odtwarzania, zasady jakości i kopii.
4. Po rozpoczęciu w tym samym oknie widać i słychać postęp, a „Anuluj” zmienia się w „Przerwij”. Fokus nie może wrócić w trakcie pracy do pola czasu ani przycisku „Wstrzymaj” odtwarzacza.
5. „Przerwij” ma zatrzymać operację i pozostawić oryginał bitowo niezmieniony. Udane cięcie ma usunąć wyłącznie zaznaczony przedział, zaktualizować czas oraz wrócić fokusem do odtwarzacza.
