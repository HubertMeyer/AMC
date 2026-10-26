# AMC15 — opcjonalne wideo pełnoekranowe po wydaniu instalatora

Data decyzji: 18 października 2026 r.

Status: zadanie długoterminowe, odroczone co najmniej do czasu ukończenia AMC12, wydania niezależnego instalatora i ustabilizowania podstawowego odtwarzania audio. Nie jest częścią najbliższej wersji ani najbliższych bramek kompilacji. Nie zmieniono kodu produkcyjnego ani testów i nie uruchomiono AMC.

## Decyzja

Obsługa obrazu może być wartościowym dodatkiem dla lokalnych plików wideo oraz zwykłych, skończonych materiałów YouTube, ale nie jest funkcją podstawową AMC i nie może zagrozić niezawodnemu odtwarzaniu dźwięku. Dlatego nie wdrażamy jej teraz w głównym odtwarzaczu.

Jeżeli prace zostaną kiedyś wznowione, obraz powstanie jako opcjonalny, domyślnie wyłączony moduł pełnoekranowy lub osobna powierzchnia wizualna. Bieżący tor audio pozostanie rozwiązaniem podstawowym i będzie działał identycznie także wtedy, gdy modułu wideo nie ma, nie uruchomił się albo uległ awarii.

To zadanie zastępuje wcześniejsze AMC07. Numer AMC07 pozostaje wyłącznie odsyłaczem historycznym, a AMC06 nie czeka już na obraz wideo.

## Dlaczego odkładamy wdrożenie

1. Lokalne kontenery wideo są obecnie celowo odtwarzane jako dźwięk. `FfmpegLocalAudioWaveStream` dekoduje tylko audio, natomiast `WindowsMediaOutput` odpowiada za urządzenie wyjściowe, głośność, tempo, pozycję, normalizację i przejścia.
2. Materiały YouTube są obecnie rozwiązywane przez `yt-dlp` jako `bestaudio`. Dodanie obrazu oznacza nowy wariant źródła, nową synchronizację oraz większe zużycie sieci i procesora.
3. Drugi niezależny odtwarzacz audio-wideo mógłby uruchomić podwójny dźwięk, przesunąć pozycję, przejąć urządzenie audio albo inaczej obsłużyć tempo i przewijanie.
4. Osadzenie strony lub WebView w głównym odtwarzaczu mogłoby wprowadzić do fokusa i drzewa NVDA kontrolki HTML, adresy albo elementy techniczne.
5. Dodatkowy silnik multimedialny zwiększa rozmiar pakietu, zakres aktualizacji, licencji, kontroli integralności oraz testów instalatora. Najpierw musi istnieć stabilny mechanizm instalowania i aktualizowania takich komponentów.
6. Obraz nie jest potrzebny do podstawowej pracy użytkownika korzystającego z NVDA, dlatego nie uzasadnia ryzyka przed wydaniem stabilnego instalatora.

## Źródła objęte ewentualnym przyszłym wdrożeniem

### Etap pierwszy — wyłącznie lokalne, skończone pliki

- MP4, MKV, WebM, MOV i pozostałe lokalne kontenery dopiero po potwierdzeniu rzeczywistej, obsługiwanej ścieżki wideo;
- plik z samym dźwiękiem w kontenerze wideo pozostaje źródłem audio;
- istniejące zakładki, rozdziały, tempo, przewijanie, fragmenty i urządzenie wyjściowe nie mogą zmienić działania.

### Etap drugi — zwykłe, skończone materiały YouTube

- dopiero po pełnym przejściu etapu lokalnego;
- bez zapisywania podpisanych adresów strumieni do konfiguracji, historii, schowka albo zwykłego logu;
- wyszukiwanie, kanał i playlista mają nadal używać tej samej tożsamości materiału oraz tych samych zakładek i pozycji;
- brak zgodnego obrazu pozostawia działający dźwięk.

### Wyłączenia

- Transmisje YouTube na żywo używane jako radio pozostają dźwiękowe. Nie wchodzą do pierwszej ani drugiej fazy. Obraz transmisji na żywo może kiedyś otrzymać osobny prototyp, ale dopiero po wykazaniu, że nie narusza bufora, Time Shiftu, skoku `End` na żywo, nagrywania ani stabilności radia.
- TIDAL Video jest wyłączony z zadania. AMC nie będzie próbował wyświetlać teledysków przez ukryty oficjalny odtwarzacz ani obchodzić ograniczeń usługi lub DRM.
- Spotify, TIDAL Audio, Sonos i WiiM pozostają poza zakresem. Sam fakt, że katalog ma element nazwany wideo, nie oznacza możliwości pokazania go w AMC.
- Radiowe HLS zawierające przypadkową ścieżkę obrazu nadal jest traktowane jako źródło audio.

## Przyszły model interfejsu

- Obraz nie jest na stałe osadzony między kontrolkami głównego `PlayerPanel`.
- Po świadomym włączeniu otwiera się osobna, lekka powierzchnia wideo, docelowo pełnoekranowa. Natywny odtwarzacz AMC nadal steruje dźwiękiem i czasem.
- `Alt+V` pokazuje albo ukrywa obraz tylko dla bieżącego, zgodnego materiału. Nie zapisuje ustawienia.
- `Alt+Shift+V` włącza albo wyłącza zapamiętane automatyczne pokazywanie obrazu dla przyszłych zgodnych materiałów. Skrót podaje `Automatyczne pokazywanie obrazu włączone` albo `Automatyczne pokazywanie obrazu wyłączone`.
- Ustawienie `Automatycznie pokazuj obraz dla materiałów wideo` jest domyślnie wyłączone zarówno dla nowych instalacji, jak i przy migracji istniejącej konfiguracji.
- `Alt+Shift+V` zapisuje ustawienie i od razu stosuje je do bieżącego zgodnego materiału, aby rezultat polecenia był jednoznaczny. Nie restartuje dźwięku.
- Escape zamyka powierzchnię obrazu i wraca do natywnego odtwarzacza, pozostawiając dźwięk zgodnie z dotychczasową regułą odtwarzania. Nie zamyka AMC.
- Powierzchnia wideo nie dodaje kontrolek HTML do Tab ani trybu przeglądania NVDA. Jeśli występuje w drzewie automatyzacji, ma jedną użytkową nazwę `Obraz wideo, bez elementów sterujących`.
- Dla źródła nieobsługiwanego `Alt+V` mówi `Obraz niedostępny dla tego materiału`. Nie próbuje otwierać strony ani zewnętrznej aplikacji.

## Polecenia i dokumentacja

Jeżeli funkcja przejdzie kiedyś do produkcji, oba polecenia muszą zostać dodane jednocześnie do wspólnego katalogu poleceń:

- `Włącz lub wyłącz obraz bieżącego materiału`, `Alt+V`;
- `Włącz lub wyłącz automatyczne pokazywanie obrazu`, `Alt+Shift+V`.

Te same nazwy i skróty trafiają do:

- pomocy `Ctrl+F1`;
- palety `Ctrl+Shift+K`;
- menu kontekstowego odtwarzacza;
- Ustawień;
- instrukcji użytkownika.

`Alt+V` i `Alt+Shift+V` nie są przechwytywane w polu tekstowym, oknie dialogowym ani podczas pracy menu.

## Prototyp przed wyborem silnika

Nie wybieramy teraz biblioteki ani odtwarzacza. Po instalatorze powstanie osobny prototyp porównujący co najmniej:

- lekki silnik oparty na mpv lub libmpv;
- VLC albo LibVLCSharp;
- bezpośrednie dekodowanie klatek przez FFmpeg przy zachowaniu obecnego toru audio.

Nazwa wspomniana w rozmowie nie została rozstrzygnięta; nie zapisujemy przypadkowej nazwy jako zależności. Wybór nastąpi na podstawie pomiaru, nie popularności.

Każdy kandydat musi przejść te same warunki:

1. Windows i pełny ekran bez osadzania strony internetowej.
2. Możliwość całkowitego wyłączenia własnego audio albo przejęcia całej osi czasu bez uruchamiania dwóch torów.
3. Synchronizacja po przewinięciu, pauzie, zmianie tempa i wznowieniu.
4. Sprzętowe dekodowanie z bezpiecznym powrotem do programowego albo jasnym błędem.
5. Brak elementów technicznych w fokusie NVDA.
6. Kontrolowany rozmiar pakietu, znana licencja, sposób aktualizacji, weryfikacja sumy i możliwość odinstalowania opcjonalnego komponentu.
7. Awaria procesu lub dekodera wideo nie zamyka AMC i nie zatrzymuje audio.
8. Brak logowania prywatnych albo tymczasowych adresów multimediów.

## Granica architektoniczna

- Moduł obrazu jest dodatkiem do stabilnego odtwarzania, nie nowym obowiązkowym fundamentem wszystkich sesji.
- Podstawowy model i wyjścia audio nie zależą od obecności biblioteki wideo.
- Uruchomienie materiału zawsze najpierw zapewnia działający dźwięk. Obraz dołącza dopiero po powodzeniu własnego przygotowania.
- Wyłączenie ustawienia oznacza brak uruchamiania, pobierania i dekodowania obrazu w tle.
- Każde żądanie obrazu ma token anulowania. Zmiana materiału, sesji albo zatrzymanie unieważniają wszystkie opóźnione klatki i procesy poprzedniego elementu.
- Funkcja pozostaje za domyślnie wyłączonym przełącznikiem do czasu osobnego wydania testowego i pełnych testów regresji audio.
- Nie zmieniamy wspólnego toru audio tylko po to, aby ułatwić obraz. Jeżeli prototyp nie potrafi zachować obecnych właściwości odtwarzania, funkcja nie trafia do produkcji.

## Warunki rozpoczęcia prac

Prace nad AMC15 można rozpocząć dopiero wtedy, gdy wszystkie poniższe warunki są spełnione:

1. AMC12 i niezależny instalator są ukończone oraz sprawdzone na czystej instalacji i aktualizacji.
2. Podstawowe odtwarzanie lokalne, YouTube audio, Radio, Time Shift i nagrywanie mają zamknięte najważniejsze regresje.
3. Istnieje sposób bezpiecznego dostarczania, aktualizowania i usuwania opcjonalnego silnika wideo.
4. Powstaje osobna gałąź albo wydanie eksperymentalne; funkcja nie trafia bezpośrednio do stabilnego wydania.
5. Użytkownik ponownie świadomie zatwierdza rozpoczęcie tego zadania.

## Testy wymagane przed produkcją

1. Te same pliki audio odtwarzają się identycznie z nieobecnym modułem, z zainstalowanym modułem i z wyłączonym ustawieniem.
2. Lokalny plik wideo odtwarza dokładnie jeden dźwięk i zachowuje pozycję po wielokrotnym `Alt+V`.
3. Awaria, zabicie albo brak opcjonalnego silnika usuwa tylko obraz; dźwięk i AMC działają dalej.
4. Page Up, Page Down, Home, End, strzałki, cyfry, zakładki, rozdziały, tempo i fragmenty zachowują obecne działanie.
5. `Alt+Shift+V` zapisuje ustawienie, a migracja ustawia je na wyłączone. Zapisz, Anuluj i ponowne otwarcie Ustawień przywracają fokus prawidłowo.
6. NVDA nie odczytuje nazw klas, adresów, kontrolek silnika, DOM ani reprezentacji obiektów.
7. Zwykły materiał YouTube nie zapisuje tymczasowego adresu i po wygaśnięciu źródła potrafi uzyskać nowy bez utraty użytkowej tożsamości materiału.
8. Transmisja YouTube traktowana jako radio, TIDAL Video, Spotify, Sonos i WiiM nie uruchamiają modułu i nie zmieniają dotychczasowego zachowania.
9. Instalacja, aktualizacja, naprawa i odinstalowanie opcjonalnego komponentu przechodzą kontrolę integralności oraz nie usuwają Biblioteki ani ustawień AMC.
10. Długa próba lokalnego wideo obejmuje przewijanie, zmianę tempa, uśpienie, wznowienie, zmianę monitora i wielokrotne otwieranie pełnego ekranu bez narastania procesów lub pamięci.

## Dokumentacja i bramka

- AMC15 ma własną przyszłą bramkę A/B/C/D i nie jest łączony z AMC06 ani żadną obecną bramką.
- Najpierw powstaje wyłącznie prototyp techniczny i raport porównawczy. Kod produkcyjny zaczyna się dopiero po zatwierdzeniu wyniku.
- Każda kompilacja, instalacja i próba na żywo nadal wymaga potwierdzenia, że AMC nie nagrywa.
- Nie ustalono terminu. Zadanie znajduje się po instalatorze i po pierwszym stabilnym wydaniu, nie w planie na najbliższy tydzień.

## Stan prac

- Zmieniono wyłącznie dokumentację planu.
- Nie zmieniono kodu produkcyjnego ani testów.
- Nie kompilowano i nie uruchamiano AMC.
