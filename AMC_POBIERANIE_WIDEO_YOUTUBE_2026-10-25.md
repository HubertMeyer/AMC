# AMC — pobieranie wideo z YouTube — zapis prac z 25 października 2026

## Stan zadania

- Stan źródła: funkcja zaimplementowana i skompilowana.
- Wersja źródła: `0.1.0-alpha.425`; zmiana przygotowana po tej wersji, bez zmiany numeru.
- Punkt wyjścia Git: `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`.
- Commit tej zmiany: brak; praca pozostaje w istniejącym katalogu roboczym użytkownika.
- Instalacja i publikacja: niewykonane. Udana kompilacja nie oznacza zainstalowanego ani wydanego programu.
- `git diff` i `git status` nie były dostępne: Git zwracał `fatal: this operation must be run in a work tree`, mimo że repozytorium i `HEAD` były czytelne. Nie wykonywano naprawy Git, żeby nie naruszyć istniejącej pracy użytkownika.
- Limit Codex po zakończeniu: wykorzystano `19%`, pozostało `81%`; reset `1 listopada 2026 o 07:15` czasu polskiego.

## Korekta użytkownika z 25 października 2026

Ta korekta zastępuje wcześniejszą decyzję zapisaną niżej jako „`Ctrl+S` nadal
otwiera Zapisz jako dla jednego odcinka”, jeżeli zdanie było rozumiane jako
zapis wyłącznie audio. `Ctrl+S` nadal jest jednorazowym **Zapisz jako**, lecz
rodzaj pliku wynika teraz z jednego zaznaczonego materiału:

- zwykły odcinek: dotychczasowe **Zapisz odcinek audio jako**;
- materiał YouTube: **Zapisz wideo jako**, z jednorazowym wyborem MP4 albo
  oryginalnego/najlepszego dostępnego formatu;
- `Ctrl+Shift+D`: szybkie pobieranie jednego lub wielu wideo do folderu
  domyślnego, w formacie zapisanym w Ustawieniach Podcastów.

Uzasadnienie: `Ctrl+S` zachowuje znany model jednorazowego **Zapisz jako** i nie
zmienia trwałych preferencji użytkownika. `Ctrl+Shift+D` pozostaje szybką akcją
bez dodatkowych pytań, dlatego korzysta z formatu zapisanego w Ustawieniach.

## Zachowanie widoczne dla użytkownika

- W sesji **Podcasty i YouTube** `Ctrl+Shift+D` pobiera wideo z jednego albo wielu zaznaczonych materiałów YouTube.
- Ten sam command ID obsługuje listę, odtwarzacz, wyniki wyszukiwania, oba menu kontekstowe, paletę poleceń i Pomoc klawiatury.
- Pozycja jest widoczna tylko wtedy, gdy cały wybór składa się z rozpoznanych materiałów YouTube. Mieszany wybór zostaje odrzucony w całości.
- Plik trafia do skonfigurowanego folderu pobierania Podcastów, z uwzględnieniem folderu ustawionego dla konkretnego kanału.
- Wideo nie ustawia pola `DownloadPath` i nie pojawia się w widoku **Pobrane**, ponieważ ten rekord nadal oznacza lokalne audio używane do odtwarzania odcinka.
- `Ctrl+D` nadal pobiera audio. `Ctrl+S` otwiera **Zapisz audio jako** albo **Zapisz wideo jako** zależnie od jednego zaznaczonego odcinka. `Ctrl+Shift+S` nadal otwiera listę sesji.

## Format i zapis pliku

- **MP4 — domyślny i najbardziej zgodny**: yt-dlp wybiera najlepszy obraz i dźwięk, preferuje H.264 oraz AAC, a FFmpeg scala lub przepakowuje wynik do MP4 bez wymuszania ponownego kodowania.
- **Oryginalny lub najlepszy dostępny — bez wymuszania MP4**: yt-dlp wybiera najlepszy dostępny obraz i dźwięk; wynik może mieć kontener WebM, MKV lub inny dostępny dla danego materiału.
- Oba tryby wyłączają playlistę, nie używają konta, OAuth ani ciasteczek przeglądarki.
- Pobieranie odbywa się w osobnym lokalnym katalogu roboczym. Dopiero ukończony, niepusty plik jest publikowany w folderze docelowym.
- Nazwa jest oczyszczana tą samą przenośną regułą co nazwy podcastów; kolizja tworzy sufiks `(2)`, `(3)` i tak dalej.
- Argumenty MP4 odpowiadają opisanemu przez yt-dlp presetowi: `--merge-output-format mp4`, `--remux-video mp4` i preferencja `vcodec:h264,...,acodec:aac`.
- Wideo zapisywane przez `Ctrl+S` trafia najpierw do odrębnego katalogu roboczego, a następnie jest atomowo publikowane pod nazwą wskazaną w systemowym oknie. Rozszerzenie jest dopasowywane do MP4 albo do rzeczywistego kontenera wyniku; dodatkowa kolizja po zmianie rozszerzenia wymaga jawnego potwierdzenia.

Źródło decyzji o argumentach: [oficjalna dokumentacja yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/README.md?plain=1).

## Polecenia i miejsca interfejsu

- Skróty: `Ctrl+Shift+D` dla szybkiego pobrania i `Ctrl+S` dla jednorazowego **Zapisz jako**.
- Menu Plik oraz menu kontekstowe listy, odtwarzacza i wyników wyszukiwania zmieniają etykietę `Ctrl+S` na **Zapisz wideo jako** albo **Zapisz odcinek audio jako** zależnie od elementu.
- Paleta `Ctrl+Shift+K`: **Pobierz wideo z YouTube**, skrót lokalny **Ctrl+Shift+D (materiały YouTube)**, oraz **Zapisz odcinek audio lub wideo jako**, skrót **Ctrl+S (jeden odcinek audio lub materiał YouTube)**.
- Pomoc `Ctrl+F1`: polecenie w sekcji Podcastów i YouTube; niedostępność mówi, że wybrany element nie jest materiałem YouTube.
- Ustawienia: **Podcasty > Pobieranie wideo z YouTube > Domyślny format wideo**.

## Komunikaty czytnika ekranu

- Start jednego pliku: **Rozpoczęto pobieranie wideo w formacie MP4** albo komunikat o formacie oryginalnym/najlepszym.
- Start wielu plików: liczba plików i wybrany format.
- Sukces jednego pliku: **Pobrano wideo: nazwa_pliku.rozszerzenie**.
- Sukces `Ctrl+S`: **Zapisano wideo jako: nazwa_pliku.rozszerzenie**.
- Sukces częściowy wielu plików: liczba pobranych i liczba niepowodzeń.
- Zły kontekst: **Pobieranie wideo jest dostępne tylko dla materiałów YouTube**.
- Błąd pojedynczego pliku: **Nie można pobrać wideo: przyczyna**.
- Anulowanie systemowego okna zapisu nie rozpoczyna pobierania; po anulowaniu, sukcesie i błędzie fokus wraca do listy albo pozostaje w odtwarzaczu zgodnie z miejscem wywołania.

Kontrolka wyboru formatu i każda jej pozycja mają jawne nazwy UI Automation. Model zachowuje wartości `Mp4` i `Original`, ale NVDA otrzymuje wyłącznie etykiety użytkowe:

- **MP4, domyślny i najbardziej zgodny**;
- **Oryginalny lub najlepszy dostępny format, bez wymuszania MP4**.

## Różnice między trybami i sesjami

- Polecenie istnieje tylko w sesji Podcasty i YouTube oraz tylko dla wiersza odcinka, którego trwała strona albo źródło prowadzi do YouTube.
- Działa także po wcześniejszym pobraniu audio: wspólna reguła najpierw sprawdza trwałą stronę YouTube, a nie lokalną ścieżkę MP3.
- Radio, Pliki lokalne, Spotify, TIDAL, Apple Music, Sonos, WiiM i Frontier Smart nie przejmują skrótu.
- Tryb MP4 zapewnia zgodniejszy kontener, ale może się nie udać, jeżeli udostępnione kodeki nie dają się legalnie przepakować do MP4. Tryb oryginalny/najlepszy nie obiecuje konkretnego rozszerzenia.

## Zmiany źródłowe

- Model i migracja ustawień: `AppSettings.cs`, `ConfigurationStore.cs`, `PodcastLibraryDatabase.cs`, `SettingsTarget.cs`; numer schematu stanu podniesiony do `55`.
- Wspólny kontrakt polecenia: `CommandIds.cs`, `CommandCatalog.cs`, `CommandRouter.cs`, `CommandPaletteSearch.cs`.
- Ustawienia i dostępność: `SettingsWindow.xaml`, `SettingsWindow.xaml.cs`.
- Pobieranie i publikacja pliku: `YouTubeMediaDownloader.cs`, `PodcastDownloadNaming.cs`.
- Jedna reguła dostępności i wspólna etykieta zapisu: `YouTubeVideoDownloadPolicy.cs`.
- Listy, odtwarzacz, fokus, komunikaty i Pomoc: `MainWindow.xaml`, `MainWindow.xaml.cs`, `MainWindowShortcutRouter.cs`.
- Wyniki wyszukiwania: `SearchWindow.xaml`, `SearchWindow.xaml.cs`.
- Dokumentacja użytkownika: `README_PL.md`, `README_EN.md`, `MEDIA_CONTROLLER_PL.md`, `MEDIA_CONTROLLER_EN.md`.

## Testy i rzeczywiste wyniki

1. `dotnet build AccessibleMediaController.sln --configuration Release --no-restore --disable-build-servers -m:1`
   - wynik końcowy: sukces;
   - błędy: `0`;
   - ostrzeżenia: `0`.
   - po korekcie `Ctrl+S` kompilację powtórzono 25 października 2026; wynik pozostał taki sam.
2. Wyodrębnione testy Windows:
   `dotnet run --project tests/AccessibleMediaController.Windows.SmokeTests --configuration Release --no-build --disable-build-servers -- --youtube-video-download`
   - skróty pobierania Podcastów: zaliczone;
   - argumenty i wspólna reguła pobierania wideo: zaliczone;
   - kontekstowe etykiety **Zapisz wideo jako** / **Zapisz odcinek audio jako**: zaliczone;
   - reguły rozszerzeń MP4, WebM i MKV w oknie **Zapisz jako**: zaliczone;
   - dostępne ustawienia pobierania i etykiety NVDA: zaliczone;
   - kod zakończenia po korekcie: `0`.
3. Wyodrębnione testy Core:
   `dotnet run --project tests/AccessibleMediaController.Core.SmokeTests --configuration Release --no-build --disable-build-servers -- --youtube-video-download`
   - katalog poleceń, paleta i Pomoc dla `Ctrl+S` oraz `Ctrl+Shift+D`: zaliczone;
   - kod zakończenia: `0`.
4. Pełne testy Core:
   - testy nazwy pliku, trwałości ustawienia, katalogu poleceń, palety i Pomocy dotyczące tej zmiany: zaliczone;
   - cały przebieg nie jest zielony: niezależny test **Transport osobnego procesu hosta Librespot** zakończył się komunikatem „Awaria procesu musi być zgłoszona jako awaria sesji”.
5. Pełne testy Windows:
   - przebieg zatrzymał się przed końcem na istniejącym teście schowka z wyłączonym `BinaryFormatter`, a następnie na awarii WPF podczas obsługi zasobu wyjątku;
   - dlatego nie jest przedstawiany jako zaliczona pełna regresja;
   - wyodrębniony przebieg wszystkich nowych testów jest zielony.
6. Rzeczywiste pobranie z publicznego YouTube i ręczny odbiór NVDA: niewykonane. Nie pobierano obcego materiału tylko w celu testowym i nie uruchamiano zwykłej aplikacji AMC.

## Ograniczenia i dalszy odbiór

- Funkcja wymaga dostępnych składników yt-dlp i FFmpeg; korzysta z istniejącego sprawdzania składników AMC.
- Dostępność formatów zależy od konkretnego materiału i bieżącej obsługi YouTube przez yt-dlp.
- Przed wydaniem należy wykonać ręczny test z własnym albo dozwolonym krótkim materiałem: lista, odtwarzacz i wyszukiwanie; MP4 i tryb oryginalny; anulowanie; kolizja nazwy; fokus po sukcesie i błędzie.
- Z NVDA należy sprawdzić początkowo wybrane MP4, rozwinięte oba wybory, strzałki, zapis, anulowanie, powrót fokusa i ponowne otwarcie Ustawień.
- Nie utworzono instalatora, nie instalowano programu, nie publikowano wydania i nie sprzątano istniejących artefaktów kompilacji przed akceptacją użytkownika.

## Migracja

- Starsza baza Podcastów otrzymuje kolumnę `youtube_video_download_format` z wartością domyślną `Mp4`.
- Starszy plik stanu bez pola używa `Mp4`.
- Nieznana lub uszkodzona wartość enuma jest normalizowana do `Mp4`.
- Istniejące pobrane audio, ścieżki `DownloadPath` i foldery pozostają bez zmian.

## Szkic instrukcji użytkownika — do korekty i akceptacji

1. Otwórz sesję **Podcasty i YouTube** i zaznacz materiał albo kilka materiałów YouTube.
2. Naciśnij `Ctrl+Shift+D` albo wybierz **Pobierz wideo z YouTube** z menu kontekstowego.
3. AMC zapisze ukończony plik w domyślnym folderze pobierania Podcastów i poda jego nazwę.
4. Aby jednorazowo wybrać nazwę, miejsce i format jednego materiału, naciśnij `Ctrl+S`. Zwykły odcinek otworzy zapis audio; materiał YouTube otworzy zapis wideo z wyborem MP4 albo formatu oryginalnego/najlepszego.
5. Aby zmienić domyślny format szybkiego pobierania `Ctrl+Shift+D`, otwórz **Ustawienia > Podcasty**. MP4 jest ustawieniem domyślnym; drugi wybór nie wymusza MP4 i może dać WebM lub MKV.
6. `Ctrl+D` pozostaje pobieraniem audio.

## Szkic changelogu — do korekty i akceptacji

- Dodano pobieranie wideo z publicznych materiałów YouTube przez `Ctrl+Shift+D`.
- Dodano format MP4 jako domyślny oraz tryb najlepszego dostępnego kontenera bez wymuszania MP4.
- Dodano funkcję do menu kontekstowych listy, odtwarzacza i wyszukiwania, palety poleceń oraz Pomocy.
- Rozszerzono `Ctrl+S` o kontekstowe **Zapisz wideo jako** dla materiałów YouTube, z jednorazowym wyborem MP4 albo oryginalnego/najlepszego formatu.
- Dodano jawne etykiety NVDA, bezpieczne nazwy, atomową publikację gotowego pliku i trwałe ustawienie formatu.
- Zachowano znaczenie `Ctrl+D`, jednorazowy charakter `Ctrl+S`, widok **Pobrane** i lokalną kopię audio; `Ctrl+S` rozróżnia teraz audio i wideo.
