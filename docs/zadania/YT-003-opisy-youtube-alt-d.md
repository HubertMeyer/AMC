# YT-003 — opisy YouTube pod Alt+D

- Status: **kod, testy i kompilacje zaliczone; przygotowywana scalona paczka
  AMC Test do ręcznego odbioru NVDA**.
- Utworzono: 23 października 2026.
- Ostatnia aktualizacja: 23 października 2026.
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

## Testy i rzeczywiste wyniki przed scaleniem

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
- Szeroki Core SmokeTests przeszedł nowe testy YouTube, lecz później zatrzymał
  się na zastanym, niezwiązanym z YT-003 teście nazwy powłoki instalatora:
  `ShellApplicationName "Accessible Multimedia Controller"`. Ten przebieg nie
  jest przedstawiany jako pełna zaliczona regresja Core.

## Znane ograniczenia i ręczny odbiór

- Nie wykonano automatycznego testu na żywej stronie YouTube. Na komputerze nie
  ma obecnie składnika `yt-dlp` w zarządzanym katalogu AMC, dlatego przed próbą
  starszego publicznego wpisu może być potrzebne polecenie `Pomoc → Sprawdź
  składniki: FFmpeg i yt-dlp`. Nowe opisy playlist konta przychodzą z
  oficjalnego API i nie zależą od tego składnika.
- Opis może być pusty, jeżeli autor go nie podał, film został usunięty albo
  YouTube ogranicza jego widoczność. AMC nie zgaduje i nie pokazuje identyfikatora
  jako zastępczej treści.
- Trzeba ręcznie sprawdzić z NVDA: kanał, playlistę i film z opisem; starszy
  film bez zapisanego opisu; brak opisu; brak składnika; anulowanie, powrót
  fokusu i ponowne otwarcie.
- Opisy nie są tłumaczone i nie są pobierane w tle dla całej Biblioteki.

## Wersja, commit, instalacja i publikacja

Źródła są przygotowane w gałęzi zadania `task/youtube-descriptions`. Dokładny
commit, tożsamość pakietu, liczba plików, wynik kontroli nagrywania i stała
instalacja zostaną dopisane po scaleniu oraz promocji. Sam kod i testy nie są
jeszcze dowodem instalacji. AMC Public, instalator publiczny i GitHub nie
zostały zmienione.
