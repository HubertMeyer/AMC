# AMC17 — podgląd trwającego nagrania

Data przygotowania zakresu: 18 października 2026 r.

Status: funkcja zatwierdzona użytkowo i odłożona do późniejszej wersji po ukończeniu AMC12, wydaniu stabilnego instalatora i ponownym świadomym rozpoczęciu prac. Wykonano audyt źródłowy poziomu A. Nie zmieniono kodu produkcyjnego, nie kompilowano i nie uruchamiano AMC.

## Cel

Trwające nagranie ma zachowywać się dla użytkownika jak zwykły plik możliwy do odsłuchania, ale jego podgląd nie może otwierać, zamykać, przenosić, usuwać ani modyfikować pliku należącego do rejestratora.

Podstawowa droga:

1. `Alt+R` otwiera listę `Nagrywane`.
2. `Enter` na wybranym nagraniu otwiera zwykły widok odtwarzacza i rozpoczyna odsłuch od początku tego nagrywanego pliku.
3. `Home` przechodzi do początku dostępnego nagrania, a `End` do bieżącego końca i dalej podąża za dopisywanym dźwiękiem.
4. `Escape` zamyka odtwarzacz i wraca do tego samego wiersza listy `Nagrywane`.
5. Nagrywanie działa niezależnie od otwierania, przewijania, pauzowania i zamykania podglądu.

## Wynik audytu źródłowego

1. Wiersz obecnego widoku `Nagrywane` przechowuje stację radiową, nie nagrywany plik ani stabilny identyfikator konkretnego nagrania. `Enter` uruchomiłby więc transmisję stacji na żywo.
2. Widok grupuje nagrania według stacji. Dwa jednoczesne nagrania tej samej stacji mogą zostać pokazane jako jeden wiersz, co nie pozwala bezpiecznie wskazać pliku ani zatrzymać tylko wybranego nagrania.
3. Ręczny i harmonogramowy rejestrator tworzą prywatny `RadioMediaOutput` z buforem tylko jednej minuty. Istniejące `TryGetRecentAudio` nadaje się do rozpoznawania utworów i krótkich próbek, lecz nie do odsłuchu pliku od początku.
4. Koder zapisuje najpierw do prywatnego pliku roboczego, a gotowy plik publikuje w folderze użytkownika dopiero po poprawnym zamknięciu. Dla MP3, AAC i WAV zapis dopuszcza równoczesny odczyt, lecz FLAC oraz zapis oryginalnego strumienia przechodzą przez FFmpeg.
5. Bezpośrednie otwieranie rosnącego pliku nie jest rozwiązaniem wspólnym dla formatów: część kontenerów uzupełnia nagłówek, indeks albo długość dopiero podczas zamykania, a zwykły odtwarzacz może zapamiętać początkową długość.
6. `Delete`, `Shift+Delete` i `Ctrl+X` są dziś na liście `Nagrywane` odrzucane pośrednio, ponieważ wiersz nie jest lokalnym plikiem i widok nie dopuszcza usuwania. Po dodaniu prawdziwego źródła podglądu ta przypadkowa ochrona mogłaby zniknąć, dlatego musi stać się jawną regułą.
7. W otwartym odtwarzaczu `Ctrl+X` oznacza destrukcyjne usunięcie zaznaczonego fragmentu z oryginalnego pliku, a nie systemowe wycięcie. To polecenie musi być bezwzględnie niedostępne dla trwającego nagrania.

## Model danych listy `Nagrywane`

- jeden wiersz oznacza jeden aktualnie zapisywany fizyczny plik, nie tylko stację;
- wiersz ma stabilny, nietechniczny dla interfejsu identyfikator wiążący go z dokładnym `RadioRecordingControl` i bieżącą częścią nagrania;
- zwykła etykieta pozostaje krótka zgodnie z AMC02: stan, nazwa pliku oraz pozycja na liście;
- nazwy klas, identyfikatory zadań, ścieżka robocza i rozszerzenie `.amc-partial` nigdy nie trafiają do nazwy dostępności;
- dwa nagrania tej samej stacji są dwoma osobnymi wierszami;
- po podziale klawiszem `T` ukończona część staje się zwykłym nagranym plikiem, a nowa część pojawia się jako nowy aktywny plik. Odtwarzacz już otwartej części nie przeskakuje sam do kolejnego pliku.

## Bezpieczne źródło podglądu

Nie należy używać docelowego pliku ani prywatnego pliku kodera jako podstawowego źródła odtwarzania. Docelowy mechanizm ma być formatowo neutralny:

1. dekoder przekazuje te same ramki PCM niezależnie do kodera nagrania i do źródła podglądu;
2. źródło podglądu jest tylko do odczytu dla odtwarzacza i ma własny kursor; przewijanie podglądu nie zmienia kursora rejestratora ani jego bufora;
3. dane od początku bieżącego pliku są przechowywane w lokalnym, niesynchronizowanym magazynie tymczasowym rosnącym razem z rzeczywistą zawartością, bez rezerwowania z góry wielogigabajtowego pliku;
4. writer nagrania i reader podglądu mają osobne blokady, anulowanie i czas życia. Błąd, zamknięcie albo zatrzymanie podglądu może zatrzymać tylko podgląd;
5. chwilowy brak nowych ramek oznacza oczekiwanie na dalszy dźwięk, nie koniec pliku;
6. `End` ustawia osobny kursor podglądu przy ostatniej kompletnej ramce i włącza podążanie za końcem. Komunikat użytkowy: `Na końcu nagrania`;
7. po zakończeniu i opublikowaniu nagrania otwarty podgląd może przejść na gotowy plik bez utraty pozycji. Magazyn podglądu wolno usunąć dopiero wtedy, gdy gotowy plik jest poprawnie opublikowany i żaden podgląd już z niego nie korzysta;
8. przed produkcją trzeba zmierzyć koszt miejsca dla jednej i kilku równoczesnych sesji. Brak miejsca na magazyn podglądu wyłącza podgląd z jasnym komunikatem, ale nigdy nie przerywa właściwego nagrywania.

## Sterowanie w odtwarzaczu

- `Spacja`: pauza i wznowienie samego odsłuchu;
- strzałki i zwykłe polecenia przewijania: poruszanie wyłącznie po już zapisanej części;
- `Home`: początek bieżącego pliku;
- `End`: bieżący koniec, z dalszym podążaniem za dopisywanym materiałem;
- `Escape`: powrót do `Nagrywane`, a gdy plik w międzyczasie zakończył się — do `Historii nagrywania` z zaznaczonym gotowym plikiem;
- `Ctrl+R`: kończy dokładnie to nagranie, z którego otwarto podgląd. AMC mówi najpierw `Kończenie nagrania`, czeka na bezpieczne zamknięcie i publikację, a potem `Nagrano, nazwa pliku`;
- po `Ctrl+R` dźwięk już nagrany pozostaje możliwy do odtwarzania, a pozycja nie wraca samoczynnie do zera;
- jeżeli plik został już zakończony przez harmonogram, podział albo inne polecenie, ponowne `Ctrl+R` niczego nie zatrzymuje i mówi `Ten plik jest już nagrany`;
- `F6` nie jest potrzebne do wejścia w ten odtwarzacz, ponieważ `Enter` otwiera go bezpośrednio. Zwykłe znaczenie `F6` w pozostałych widokach nie zmienia się.

## Ochrona trwającego nagrania

Poniższe działania są jawnie zablokowane zarówno na liście `Nagrywane`, jak i w jego odtwarzaczu:

- `Ctrl+X` jako systemowe wycięcie albo destrukcyjne usunięcie fragmentu z oryginału;
- `Delete` oraz usunięcie z Biblioteki;
- `Shift+Delete` i przeniesienie do Kosza;
- zmiana nazwy pliku, przeniesienie, podmiana rozszerzenia i edycja metadanych;
- otwarcie technicznego pliku roboczego w innej aplikacji;
- każda operacja, która wymaga zamknięcia uchwytu kodera.

Komunikat powinien nazywać przyczynę, na przykład: `Nie można przenieść ani usunąć pliku podczas nagrywania`. Nie wolno polegać na ogólnym komunikacie, że polecenie jest dostępne tylko w innej sesji.

Bezpieczne pozostają kopiowanie nazwy, informacje, zakładki nagrania oraz późniejszy eksport kopii fragmentu, jeżeli otrzyma osobne zadanie. Pierwsza wersja AMC17 nie usuwa fragmentu z trwającego nagrania i nie edytuje go w miejscu.

## Rozdzielenie od sterowania nagrywaniem

- rozpoczęcie i zatrzymanie podglądu nie wywołuje `StartRecording`, `StopRecording`, `RequestStop`, `SplitRecording`, `PauseRecording` ani `ResumeRecording`;
- `Ctrl+R` jest jedynym poleceniem podglądu, które świadomie żąda zakończenia wybranego nagrania;
- pauza odsłuchu nie jest pauzą nagrywania. Wstrzymanie nagrywania nadal ma osobne, istniejące polecenie i komunikat;
- zamknięcie głównego odtwarzacza, zmiana sesji, błąd urządzenia audio lub utrata fokusa nie zatrzymują nagrania;
- awaria źródła podglądu jest raportowana oddzielnie i nie może trafić do `RecordingFailed` właściwego kodera.

## Pomoc, paleta i menu

- `Ctrl+F1` w widoku `Nagrywane` opisuje `Enter`, `End`, `Escape`, `Ctrl+R` oraz blokadę usuwania i przenoszenia;
- `Ctrl+Shift+K` zawiera polecenie `Odtwórz podgląd trwającego nagrania`, dostępne tylko dla aktywnego wiersza;
- menu kontekstowe zawiera `Odtwórz podgląd`, `Zakończ nagrywanie`, pauzę nagrywania, podział i informacje. Nie pokazuje czynności niszczących plik;
- NVDA ma mówić nazwę gotowego pliku, bieżącą pozycję i rosnący czas bez nazw technicznych źródła podglądu.

## Testy i kryteria odbioru

1. `Enter` na aktywnym nagraniu nie uruchamia nowego połączenia ze stacją i nie zmienia liczby aktywnych nagrań.
2. Odsłuch od początku, przewijanie, `Home`, `End`, pauza odsłuchu i `Escape` nie zmieniają rozmiaru ani stanu właściwego nagrania inaczej niż przez naturalne dopisywanie.
3. Nagranie rośnie i kończy się poprawnie przy podglądzie w początku, środku, na końcu, w pauzie i po zamknięciu odtwarzacza.
4. `Ctrl+R` kończy tylko wybrany ręczny albo harmonogramowy plik, publikuje go i pozwala dalej odtworzyć dotychczasową zawartość.
5. Dwa równoczesne nagrania tej samej stacji są osobnymi wierszami i zatrzymanie jednego nie zatrzymuje drugiego.
6. MP3, M4A/AAC, WAV, FLAC i zapis oryginalnego strumienia mają to samo zachowanie użytkowe; podgląd nie zależy od tego, czy niedokończony kontener jest samodzielnie odtwarzalny.
7. `Ctrl+X`, `Delete`, `Shift+Delete`, zmiana nazwy, przeniesienie i destrukcyjna edycja fragmentu są zablokowane przed dotknięciem systemu plików.
8. Brak miejsca, błąd urządzenia wyjściowego i awaria podglądu nie przerywają nagrywania; zapisany plik nadal przechodzi zwykłą finalizację.
9. Podział ręczny i automatyczny kończy oglądaną część bez uszkodzenia, a nowa część pojawia się jako osobny aktywny plik.
10. Test NVDA obejmuje wejście z `Alt+R`, pierwszy wiersz, dwa pliki o tej samej nazwie stacji, komunikat `Na końcu nagrania`, zakończenie `Ctrl+R`, powrót `Escape` oraz ponowne otwarcie gotowego pliku z historii.

## Zasoby i bramka

- poziom A: audyt i niniejsza specyfikacja — wykonane;
- poziomy B i C: odłożone do osobnej przyszłej sekwencji po AMC12; nie dołączać AMC17 do bieżącej Bramy 2 ani do najbliższego wydania;
- po ponownym rozpoczęciu: formatowo neutralne źródło podglądu, osobny kursor, routing odtwarzacza i testy bez prawdziwej stacji, a następnie kontrolowana próba ręcznego i harmonogramowego nagrania z NVDA, osobno dla formatów oraz dwóch nagrań równoczesnych;
- nie kompilować ani nie uruchamiać AMC tylko dla tej notatki. AMC17 otrzyma własną bramkę bezpieczeństwa po stabilnym instalatorze, zawsze po potwierdzeniu, że ważne nagranie użytkownika nie trwa.

## Poza pierwszą wersją

- destrukcyjne wycinanie z trwającego pliku;
- montaż i podmiana oryginału podczas nagrywania;
- otwieranie technicznego pliku roboczego w zewnętrznym odtwarzaczu;
- automatyczne łączenie części podzielonego nagrania w jeden fizyczny plik;
- zachowywanie magazynu podglądu po awarii jako drugiej kopii nagrania.
