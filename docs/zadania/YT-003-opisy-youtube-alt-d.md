# YT-003 — opisy YouTube pod Alt+D

- Status: **Podstawowy zakres opisów jest zainstalowany i wcześniej odebrany;
  korekta pełnego automatycznego odczytu z 27 października 2026 r. jest
  zapisana w źródłach i testach, lecz czeka na następną paczkę AMC Test,
  instalację oraz ręczny odsłuch NVDA**.
- Utworzono: 23 października 2026.
- Ostatnia aktualizacja: 27 października 2026.
- Obszar: Podcasty i YouTube, opisy kanałów, playlist i materiałów, NVDA.
- Profil: wyłącznie AMC Test. AMC Public i GitHub pozostają bez zmian.

## Polecenie użytkownika i korekta wcześniejszego stanu

23 października 2026 użytkownik zaakceptował `Ctrl+N` w sesji Podcasty i
YouTube, a następnie wskazał, że pod `Alt+D` nie ma opisów YouTube, również dla
wcześniej importowanych pozycji. Ta decyzja uzupełnia YT-001 i YT-002:
`Alt+D` ma pokazywać właściwy opis kanału, playlisty albo filmu bez wymagania
ponownego logowania do Google.

Regulacja prędkości podcastów Spotify pozostaje oddzielnym zadaniem SPOT-001.
Nie zmieniano jej w YT-003.

## Materiał do dokumentacji użytkownika — wersja robocza

- W sesji Podcasty i YouTube wybierz kanał, playlistę albo materiał i naciśnij
  `Alt+D`.
- Jeśli opis jest już zapisany w Bibliotece AMC, okno otwiera się od razu.
- Jeśli starsza publiczna pozycja YouTube nie ma zapisanego opisu, AMC pobiera
  go na żądanie z jej publicznego adresu. Nie uruchamia przy tym logowania
  Google i nie korzysta z tokenu konta ani ciasteczek przeglądarki.
- Nowy import publicznego kanału lub playlisty zapisuje opis kolekcji oraz te
  opisy materiałów, które zwróci YouTube. Synchronizacja playlist zalogowanego
  konta również zapisuje opis playlisty i opis każdego materiału zwrócony przez
  oficjalne API.
- Okno rozpoczyna fokus na początku opisu. Dalej zawiera tylko czytelne dane,
  między innymi tytuł, kanał, czas i publiczną stronę. Techniczny identyfikator,
  nazwa klasy ani nazwa operacji hosta nie są czytane przez NVDA.
- Jeśli YouTube nie opublikował opisu, AMC mówi to wprost i nadal pokazuje
  zapisane dane pozycji.
- Odczyt starszych publicznych wpisów wymaga składnika `yt-dlp`. Gdy go brakuje,
  okno wyjaśnia: `Wybierz Pomoc, Sprawdź składniki: FFmpeg i yt-dlp`.
- Samo otwieranie opisów nie wymaga ponownego logowania. Dla playlist konta AMC
  używa lokalnie chronionego tokenu odświeżania; ponowne logowanie jest potrzebne
  dopiero po wylogowaniu, cofnięciu zgody, unieważnieniu dostępu albo wygaśnięciu
  testowej autoryzacji Google.

## Powierzchnie poleceń i dostępność

Nie dodano drugiego skrótu ani osobnej czynności. Istniejące wspólne polecenie
`Opis` z `Alt+D` nadal jest jedynym źródłem prawdy dla routingu klawiatury,
menu, pomocy kontekstowej `Ctrl+F1`, pełnej pomocy i palety
`Ctrl+Shift+K`. Zmieniła się jego rzeczywista dostępność danych w sesji
Podcasty i YouTube.

Tytuły użytkowe zależą od rodzaju elementu: `Opis kanału YouTube`, `Opis
playlisty YouTube` i `Opis materiału YouTube`. Dostępna nazwa okna i pola
tekstu zaczyna się od prawdziwego opisu albo jednoznacznej informacji o jego
braku. Punkt wstawiania jest ustawiany na początku. Zamknięcie oddaje fokus do
tego samego wiersza listy; ponowne otwarcie wykonuje ten sam kontrakt.

## Implementacja i uzasadnienie

- `YouTubePlaylistClient` odczytuje pola `snippet.description` playlisty i
  elementów playlisty z oficjalnego YouTube Data API. Synchronizacja zapisuje
  je w istniejącym modelu Podcastów i YouTube.
- `YouTubeCollectionClient` zachowuje opisy zwracane przy publicznym imporcie
  przez `yt-dlp` zamiast zastępować je pustym tekstem.
- Starsze rekordy pozostają zgodne bez migracji bazy. Gdy nie mają opisu,
  `YouTubeDescriptionClient` odczytuje pojedynczy publiczny opis z zapisanego
  adresu. Dla kolekcji pobiera płaskie metadane i najwyżej pierwszy element,
  więc `Alt+D` nie rozwija całego dużego kanału.
- Żądanie publicznego opisu zawiera tylko adres i rodzaj `video` albo
  `collection`. Nie zawiera pola logowania, tokenu, sekretu klienta ani danych
  przeglądarki.
- Tekst zachowuje akapity, usuwa przypadkowe odstępy i znaki zerowe oraz ma
  jawne limity rozmiaru. Długi odczyt działa jako operacja współbieżna hosta,
  więc nie blokuje transportu odtwarzania.
- Oficjalne źródła pól opisów sprawdzone 23 października 2026:
  [playlistItems](https://developers.google.com/youtube/data/reference/rest/v3/playlistItems),
  [playlists](https://developers.google.com/youtube/v3/docs/playlists) i
  [videos](https://developers.google.com/youtube/data/reference/rest/v3/videos).

## Testy i rzeczywiste wyniki

- Ukierunkowane testy wxPython: **115/115 zaliczonych**. Obejmują opis zapisany,
  pobranie starego publicznego opisu bez argumentów logowania, komunikat przy
  niedostępnym hoście bez technicznej nazwy operacji, teksty dostępnościowe,
  menu i wspólne skróty.
- Pełna regresja wxPython: **2029 zaliczonych, 111 kontrolowanie pominiętych,
  13 podtestów zaliczonych**.
- Core: klient playlist **3/3**, synchronizacja playlist **4/4**.
- LiteHost ProtocolTests: kontrakt konta YouTube **9/9**; pełny zestaw
  **27/27 grup zaliczonych**.
- Windows SmokeTests `--youtube-collection-normalization`: zaliczony. Sprawdza
  opis kolekcji, opis materiału, zachowanie akapitów i usuwanie przypadkowych
  odstępów.
- Kompilacje Release Core, LiteHost, ProtocolTests i Windows SmokeTests:
  **0 ostrzeżeń, 0 błędów**.
- Końcowa promocja ponownie zaliczyła **30/30 testów launchera i
  aktualizatora**, pełne **2029 testów wxPython**, 111 kontrolowanie
  pominiętych i 13 podtestów oraz kompilacje wymaganych składników.
- Próba zainstalowanego hosta bez argumentów konta Google odczytała przez
  zarządzany `yt-dlp 2026.08.19` prawdziwy publiczny opis filmu, **2362 znaki**,
  oraz opis kanału, **79 znaków**. Filmów ani kolekcji nie pobierano.
- Szeroki Core SmokeTests przeszedł nowe testy YouTube, lecz później zatrzymał
  się na zastanym, niezwiązanym z YT-003 teście nazwy powłoki instalatora:
  `ShellApplicationName "Accessible Multimedia Controller"`. Ten przebieg nie
  jest przedstawiany jako pełna zaliczona regresja Core.

## Znane ograniczenia i ręczny odbiór

Korekta z 24.10.2026 zastępuje wcześniejszy zapis o braku ręcznego odbioru:
użytkownik potwierdził, że opisy YouTube pod `Alt+D` działają. To potwierdzenie
nie oznacza, że każdy film ma opis — pusty wynik nadal może być prawidłową
treścią zwróconą przez autora lub YouTube.

- Na tym komputerze zarządzany składnik `yt-dlp 2026.08.19` jest obecny i
  zaliczył próbę filmu oraz kanału. Na innym profilu, gdy składnika zabraknie,
  przed próbą starszego publicznego wpisu trzeba użyć `Pomoc → Sprawdź
  składniki: FFmpeg i yt-dlp`. Nowe opisy playlist konta przychodzą z
  oficjalnego API i nie zależą od tego składnika.
- Opis może być pusty, jeżeli autor go nie podał, film został usunięty albo
  YouTube ogranicza jego widoczność. AMC nie zgaduje i nie pokazuje identyfikatora
  jako zastępczej treści.
- Podstawowy odczyt `Alt+D` został przyjęty przez użytkownika. Nietypowe
  przypadki braku opisu, braku składnika i starszego wpisu pozostają pokryte
  automatycznymi testami, ale nie były osobno odtwarzane ręcznie.
- Opisy nie są tłumaczone i nie są pobierane w tle dla całej Biblioteki.

## Wersja, commit, instalacja i publikacja

Implementacja i testy mają commit
`f8668937659a518770fa598934082c11a3f7cf47` —
`feat(youtube): dodaj opisy pod Alt+D`. Zainstalowany pakiet AMC Test ma
identyfikator `3c2a9986`, etykietę
`2026.10.23-f8668937659a518770fa598934082c11a3f7cf47-3c2a9986` i **1674
pliki**. Przed promocją pięciosekundowa bramka sprawdziła skonfigurowany katalog
nagrań: 0 plików `.amc-partial` przed i po pomiarze oraz 0 plików rosnących.
Aktualizator zachował dodatkową żywą blokadę zamknięcia podczas nagrywania.

Kandydat i stała instalacja przeszły kontrolę manifestu, sum, odizolowany start
oraz kontrolowany start po podmianie. Potwierdzone okno to `AMC Test —
23.10.2026, 23:13`, proces interfejsu pochodzi z
`D:\Projekty Codex\AMC Python\runtime\python.exe`, a stała instalacja znajduje
się w `D:\Projekty Codex\AMC Python`. Promocję ukończono 23.10.2026 o 23:15
czasu lokalnego.

Ten późniejszy zapis dokumentacyjny nie zmienia rewizji zainstalowanego źródła.
AMC Public, instalator publiczny i GitHub nie zostały zmienione.

## Korekta pełnego automatycznego odczytu — 27 października 2026

Użytkownik stwierdził na rzeczywistych opisach odcinków i materiałów YouTube,
że po otwarciu `Alt+D` NVDA automatycznie czyta tylko początek, odbierany jak
pierwszy akapit, mimo że dalsza treść pozostaje widoczna w polu tekstowym.
Poprosił o automatyczny odczyt całego opisu. Ta decyzja zastępuje wcześniejszą
decyzję prezentacyjną, która ograniczała dostępną nazwę okna do około 500
znaków w obawie przed zbyt długą wypowiedzią.

### Materiał do dokumentacji użytkownika

- `Alt+D` w Podcastach i YouTube oraz przy podcastach Spotify ma automatycznie
  odczytać wszystkie akapity opisu, nie tylko jego początek.
- Pole nadal rozpoczyna się na początku treści. Można poruszać się po nim
  klawiaturą, przerwać długą mowę zwykłym poleceniem NVDA, użyć przycisku
  `Kopiuj wszystko` albo zamknąć okno klawiszem `Escape`.
- Nie zmieniły się nazwa polecenia, skrót, menu, `Ctrl+F1`, pełna pomoc ani
  paleta `Ctrl+Shift+K`; wszystkie te powierzchnie nadal prowadzą do jednego
  polecenia `Opis`.
- Radio już przekazywało do dostępnego regionu całą odpowiedź hosta bez limitu
  500 znaków. Dodany test chroni również wieloakapitowy tekst Radia.

### Uzasadnienie i decyzje

- Pełny opis był obecny w natywnym polu tekstowym, ale dostępna nazwa okna i
  pola powstawała z osobnej, skróconej reprezentacji. NVDA automatycznie
  wypowiadał właśnie tę reprezentację i kończył przed dalszymi akapitami.
- Usunięto tylko wtórny limit 500 znaków w warstwie prezentacji dla RSS,
  YouTube i Spotify. Nadal obowiązują limity rozmiaru, czyszczenie znaków
  sterujących i filtrowanie danych na wejściu, więc modelowe identyfikatory,
  reprezentacje obiektów ani nieograniczony surowy tekst nie trafiają do mowy.
- Nie zmieniano pobierania danych, logowania Google, odtwarzania, fokusu po
  zamknięciu ani mechanizmu Radia.

### Testy i wynik

- Sześć dokładnie wybranych testów pełnego odczytu RSS, YouTube, Spotify,
  wspólnego okna `Alt+D` i Radia: **6/6 zaliczonych**.
- Wszystkie samowystarczalne testy w pięciu zmienionych obszarach:
  **88/88 zaliczonych**. Jeden zastany test Spotify wymagający fixture
  `monkeypatch` nie był częścią tego przebiegu.
- Projektowy runner wykonał dodatkowo **89 testów poprawnie**, ale cały przebieg
  nie jest raportowany jako zaliczony: lokalny Python nie zawiera `pytest`, więc
  osiem niezwiązanych modułów nie dało się zaimportować, a zastany runner nie
  obsługuje fixture `monkeypatch` w dziewiątym przypadku.
- Kontrola składni zmienionych modułów i testów: zaliczona. `git diff --check`:
  bez błędów; pozostało jedynie informacyjne ostrzeżenie o przyszłej
  normalizacji końców linii jednego pliku testowego.
- Nie budowano paczki, nie instalowano programu i nie wykonywano ręcznej próby
  z NVDA. Te etapy pozostają osobne od zaliczonych testów źródłowych.

### Znane ograniczenia

- Bardzo długi opis da teraz odpowiednio długą automatyczną wypowiedź. Użytkownik
  może ją przerwać i czytać pole ręcznie; nie wprowadzono dzielenia treści na
  osobne, potencjalnie gubione komunikaty.
- Rzeczywisty odsłuch musi po instalacji sprawdzić opis RSS, materiał YouTube i
  podcast Spotify z co najmniej dwoma akapitami, a także `Escape`, powrót fokusu
  i ponowne otwarcie.

### Wersja i commit

- Źródła i testy: commit `a4471493` —
  `fix(accessibility): czytaj pelne opisy pod Alt+D`.
- Nowa paczka, build, instalacja, ręczny odbiór NVDA i publikacja GitHub: **nie
  wykonano**. Poprawka ma wejść do następnej zbiorczej wersji AMC Test.
