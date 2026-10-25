# Roboczy indeks materiału do instrukcji i opisu zmian — stan na 25 października 2026

## Status dokumentu

To jest indeks roboczy wygenerowany z zapisów zadań. Nie jest gotową
instrukcją ani opublikowanym opisem wydania. Wymaga korekty i zatwierdzenia
użytkownika. Nie zmienia statusu ręcznego odbioru NVDA poszczególnych funkcji.

## Punkt odniesienia wersji

- Najnowsza potwierdzona zainstalowana i uruchomiona paczka AMC Test:
  `2026.10.25-8f42e319453164779a0ff2c3ab574998f4694a76-0423232e`.
- Zawiera dostępne okna kont Spotify i TIDAL, kontekstowy `Ctrl+F5`, poprawki
  wyszukiwania i Biblioteki, playlist Spotify oraz lokalny formularz
  Sygnalisty. Użytkownik potwierdził szybkie `Ctrl+C`, działające ponowne
  logowanie Spotify, zapis do playlisty na prawdziwym koncie oraz brak
  powtarzania komunikatu AMC na prawej strzałce wyszukiwarki. Pozostały odbiór
  NVDA innych funkcji i internetowa wysyłka Sygnalisty są nadal otwarte.
- Fundament profili AMC12 został skompilowany i sprawdzony; zbudowano czystą
  paczkę publiczną oraz lokalny instalator z kontrolą integralności. Nie
  zainstalowano ich i nie opublikowano.
- Nie wykonano publikacji na GitHubie ani publicznego wydania.

## Materiał do przyszłej instrukcji użytkownika

1. Kopiowanie nazwy i NVDA — `Ctrl+C`, jeden komunikat „Skopiowano nazwę”,
   zgodność z NVDAExtensionGlobalPlugin. Ręczny odbiór mowy i schowka nadal
   otwarty. Źródło:
   [NVDA-001-opoznienie-ctrl-c.md](NVDA-001-opoznienie-ctrl-c.md), sekcja
   „Materiał do dokumentacji użytkownika”.
2. Wyszukiwanie i Biblioteka — `Ctrl+Shift+L` w modalnych wynikach YouTube,
   Spotify i TIDAL; różnica między kanałem, podcastem, filmem i odcinkiem;
   pozostanie w wyszukiwarce oraz powrót do odświeżonej Biblioteki po
   `Escape`. W Radiu polecenie nie poprzedza potwierdzonego wyniku zbędnym
   komunikatem „Przygotowywanie stacji”. Na świeżym profilu wyszukiwarki nie
   mogą zależeć od nieprzekazanej ścieżki starego magazynu. Źródło:
   [SEARCH-001-youtube-biblioteka-komunikaty.md](SEARCH-001-youtube-biblioteka-komunikaty.md).
3. Nagrywane pliki i historia — krótkie widoki `Alt+R`, `Alt+Shift+R`;
   ukończony plik zaczyna się od razu nazwą bez powtarzanego „Nagrane”;
   oddzielna pamięć zaznaczenia oraz szczegóły bitrate, wielkości i folderu pod
   lewą strzałką, również w `Ctrl+H`. Źródło:
   [AMC02-listy-nagrywania-i-historii.md](AMC02-listy-nagrywania-i-historii.md).
4. Harmonogramy — zwięzły wiersz nazwa–stan–data–czas, lewa strzałka
   powtarzająca stan i termin oraz prawa z niepowtarzanymi szczegółami;
   Spacja, Enter i `Ctrl+D`; menu pod `Shift+F10`; segmentowe wpisywanie daty, czasu i czasu
   trwania; powrót fokusu i komunikaty NVDA. Źródło:
   [SCHED-001-edytor-i-klawisze-harmonogramow.md](SCHED-001-edytor-i-klawisze-harmonogramow.md).
5. Playlisty Spotify — przed pierwszą próbą zapisu po aktualizacji `Ctrl+F5`
   otwiera konto, a dopiero „Zaloguj w przeglądarce” rozpoczyna oficjalne OAuth
   i odnawia zgodę na prywatne i publiczne playlisty; dalej `Ctrl+P`,
   `Ctrl+Shift+P`, jedna lub wiele playlist,
   jednoznacznie nazwane pole nowej playlisty, tworzenie playlisty prywatnej
   lub publicznej, jasne rozróżnienie przygotowania od zapisu oraz uczciwe
   wyniki częściowe. Udane ponowne logowanie unieważnia migawkę playlist, więc
   następne `Ctrl+P` lub `Ctrl+Shift+P` pobiera aktualną listę dokładnie raz.
   Użytkownik potwierdził zapis do istniejącej playlisty na prawdziwym koncie;
   pełny odbiór tworzenia i ponownego otwierania nowej playlisty pozostaje
   otwarty. Źródło:
   [AMC08-playlisty-spotify.md](AMC08-playlisty-spotify.md).
6. Zakładki, nazwane zakładki, rozdziały i historia — rozróżnienie danych oraz
   skróty `B`, `Ctrl+Shift+B`, `Shift+Page Up/Down`,
   `Ctrl+Shift+Page Up/Down`, `Ctrl+Shift+lewo/prawo`, `Alt+lewo/prawo` i
   `Alt+góra/dół`. Źródło:
   [AMC04-nawigacja-zakladki-rozdzialy-historia.md](AMC04-nawigacja-zakladki-rozdzialy-historia.md).
7. Odtwarzany element na listach — znaczenie etykiet „Odtwarzane” i
   „Wstrzymane”, zachowanie szczegółów wiersza i ograniczenia stanu urządzeń
   Sonos/WiiM. Źródło:
   [AMC05-odtwarzany-element-na-listach.md](AMC05-odtwarzany-element-na-listach.md).
8. Time Shift Radia — `Home` przechodzi na początek, `End` wraca do transmisji
   na żywo i tempa normalnego, a cyfry `0`–`9` przechodzą do 0–90% bieżącego
   bufora; `NVDA+End` pozostaje skrótem NVDA. Źródło:
   [AMC13-timeshift-end-na-zywo.md](AMC13-timeshift-end-na-zywo.md).
9. Sortowanie Biblioteki Podcastów i YouTube — trzy tryby, trwałość wyboru,
   zachowanie zaznaczenia oraz wspólne powierzchnie poleceń. Źródło:
   [POD-001-sortowanie-biblioteki-zrodel.md](POD-001-sortowanie-biblioteki-zrodel.md).
10. Menedżer sesji — `Ctrl+Shift+S`, Enter, Spacja,
    `Alt+strzałka w górę/dół`, „Konfiguruj…”, zwarta numeracja `Ctrl+1–9` i
    zabezpieczenia przed wyłączeniem aktywnej lub ostatniej sesji. Kontekstowe
    `Ctrl+F5` otwiera konto Spotify lub TIDAL, odświeża urządzenia WiiM,
    odświeża Podcasty albo wybiera cel Sonos; przy braku połączenia Sonos
    prowadzi do okna konta. Zwykłe `F5` nadal odświeża widok.
    Źródło:
    [AMC09-menedzer-sesji.md](AMC09-menedzer-sesji.md).
11. AMC Test i przyszły publiczny AMC — osobne dane i możliwości, publiczne
    sesje Pliki lokalne, Radio, Podcasty i YouTube oraz WiiM, bez reklamowania
    ukrytych usług w menu, pomocy i palecie. Wariant ochronny przeszedł
    odizolowaną instalację i odinstalowanie; końcowy kandydat z dobrowolnymi
    skrótami jest lokalnie zbudowany, sprawdzony i nie zawiera prywatnych
    modułów interfejsu Spotify/TIDAL ani Librespot, ale nie był ponownie
    instalowany ani publikowany. Źródło:
    [AMC12-profile-wydania-publicznego-i-testowego.md](AMC12-profile-wydania-publicznego-i-testowego.md).
12. Foldery i powłoka Windows — „Otwórz folder zawierający”, argument pliku,
    przekazanie do właściwej działającej instancji oraz dobrowolne „Otwórz za
    pomocą AMC” i „Dodaj do kolejki AMC”. Rejestracja systemowa nie została
    jeszcze zastosowana. Źródło:
    [AMC14-foldery-i-integracja-powloki.md](AMC14-foldery-i-integracja-powloki.md).
13. Sonos — okno konta w AMC Test udostępnia rozpoczęcie, jawne sprawdzenie i
    anulowanie logowania, odświeżenie dostępu, ponowienie zapisu, wylogowanie
    oraz przejście do głośników i grup. Rozpoczęcie otwiera oficjalną stronę i
    zwalnia okno AMC. Po powrocie można sprawdzić wynik, otworzyć tę samą stronę
    ponownie albo skopiować pierwotny adres, również do okna prywatnego. Adres
    istnieje tylko w pamięci bieżącej próby; tokeny pozostają w C#, a broker nie
    ujawnia sekretu integracji. Publiczny broker HTTPS działa, lecz Sonos w AMC
    Public pozostaje ukryty do czasu pełnego odbioru prawdziwego konta. Źródło:
    [AMC10-logowanie-sonos-i-publiczny-broker.md](AMC10-logowanie-sonos-i-publiczny-broker.md).
14. Sygnalista — polecenie `Zgłoś błąd lub sugestię…` w menu Pomoc i palecie,
    pełny podgląd zredagowanego raportu, domyślnie wyłączony log oraz lokalne
    kopiowanie lub zapis w magazynie bieżącego profilu. Po dostarczeniu
    zweryfikowanego endpointu ten sam formularz pokaże `Wyślij zgłoszenie`,
    poda wynik i pozwoli skopiować adres issue; bez endpointu uczciwie pozostaje
    lokalny. Worker, klient i samodzielna bramka wdrożenia są gotowe w kodzie:
    lokalny przebieg wykonuje testy i pakowanie `--dry-run`, a jawne wdrożenie
    potrafi automatycznie przygotować KV i odczytać standardowy adres
    `workers.dev`. Internet pozostaje wyłączony do świadomego logowania
    Cloudflare, ustawienia ograniczonego sekretu GitHub i odbioru prawdziwego
    zgłoszenia.
    Źródło:
    [REL-001-github-aktualizacje-sygnalista.md](REL-001-github-aktualizacje-sygnalista.md).

## Materiał do przyszłego opisu zmian

- Poprawiono kolejność i jednoznaczność komunikatów NVDA po kopiowaniu i po
  zmianach Biblioteki z wyszukiwarki.
- Uporządkowano listy nagrywania, historię nagrań i szczegóły plików bez
  powtarzania stacji, harmonogramu i folderu w zwykłym wierszu.
- Przebudowano dostępny edytor harmonogramów oraz nawigację daty i czasu.
- Dodano rzeczywiste menu kontekstowe harmonogramów i region aktywny, dzięki
  któremu informacje pod strzałkami mogą zostać wypowiedziane przez NVDA.
- Naprawiono bezpośrednie otwieranie tego menu przez `Shift+F10`, skrócono
  zwykły wiersz harmonogramu i rozdzielono zakres lewej oraz prawej strzałki.
- Nazwę radiowego `Alt+D` zmieniono na „Informacje o bieżącym odtwarzaniu”,
  ponieważ polecenie tylko odczytuje stan i nie przechodzi do innego widoku.
- Dodano zarządzanie natywnymi playlistami Spotify, bez obiecywania
  nieobsługiwanego odtwarzania całych playlist.
- Uporządkowano tworzenie playlisty Spotify i zachowano potwierdzony nowy cel
  również podczas krótkiej niespójności katalogu Spotify.
- Uproszczono nazwę „Odtwarzaj jako następne” oraz zmieniono opis
  `Ctrl+Shift+C` na „Skopiuj ścieżkę do pliku” dla lokalnych plików.
- Ujednolicono zakładki, nazwane zakładki, rozdziały i historię we wspólnym
  katalogu poleceń.
- Dodano wiarygodne oznaczenie odtwarzanego elementu oraz przywrócono `End` na
  żywo w Time Shifcie.
- Dodano trwałe sortowanie zbiorczej Biblioteki Podcastów i YouTube.
- Dodano Menedżer sesji i dynamiczne, zwarte skróty `Ctrl+1–9`.
- Przywrócono kontekstowe `Ctrl+F5` oraz dostępne okna kont Spotify i TIDAL;
  samo otwarcie okna nie rozpoczyna logowania.
- Rozpoczęto fundament dwóch izolowanych profili wydania; ta ostatnia zmiana
  nie jest jeszcze częścią zainstalowanej paczki.
- Dodano aplikacyjne otwieranie folderu, bezpieczne przekazywanie plików do
  właściwego profilu i opcjonalną, odwracalną integrację z powłoką Windows.
- Dodano lokalnie testowalny broker logowania Sonos z jednorazowym PKCE,
  odnowieniem i ochroną danych; nie został jeszcze wdrożony publicznie.
- Dodano dostępne okno konta Sonos w AMC Test i bezpieczną bramkę `Ctrl+F5`:
  połączone konto prowadzi do grup, a brak połączenia do logowania. Zmiana
  została zainstalowana w AMC Test. Poprawiono też powrót do oczekującej próby:
  pierwotny adres można ponownie otworzyć lub skopiować bez przepisywania adresu
  pośredniego z przeglądarki. Odbiór prawdziwego logowania i NVDA pozostaje otwarty.
- Rozszerzono Sygnalistę o bezsekretowy klient HTTPS i własnego Workera z drugą
  redakcją, limitem, prywatnym intake oraz idempotencją. Kod przeszedł testy na
  atrapach oraz rzeczywiste pakowanie Wranglera bez publikacji. Uproszczono
  przyszłe wdrożenie przez automatyczne przygotowanie KV i odczyt adresu
  `workers.dev`; wysyłanie pozostaje wyłączone do autoryzacji i odbioru.
- Usunięto zbędne „Przygotowywanie stacji” przed wynikiem `Ctrl+Shift+L` w
  Radiu i rozszerzono regresje pustego profilu na wyszukiwarki oraz Bibliotekę.
- Po udanym OAuth Spotify pamięć playlist jest unieważniana, aby kolejna lista
  pokazała aktualne cele bez wielokrotnego pobierania przy każdym otwarciu.

## Odbiory i ograniczenia do zachowania w instrukcji

- Nie oznaczać ręcznych testów NVDA jako zaliczonych, dopóki użytkownik ich nie
  potwierdzi.
- Nie przedstawiać testów atrap Spotify/TIDAL jako próby prawdziwego konta.
- Okna kont są zainstalowane, ale nie przedstawiać ich jako odebranych, dopóki
  nie przejdą ręcznej próby NVDA i OAuth.
- Korekta `4b85e0c8` jest zainstalowana; nadal nie przedstawiać jej jako
  odebranej z NVDA ani sprawdzonej zapisem na prawdziwym koncie Spotify.
- Druga korekta harmonogramów i nazwy `Alt+D` jest zainstalowana w AMC Test w
  kompilacji
  `2026.10.19-2930a9498f7abc4e64a10362ab67631d6423b407-67d8b325`;
  nie przedstawiać jej jako odebranej z NVDA przed testem użytkownika.
- Nie przedstawiać zbudowanej paczki i instalatora AMC12 jako instalacji albo
  wydania publicznego.
- Nie obiecywać publicznego Sonosa przed działającym brokerem HTTPS i odbiorem
  z zewnętrznym kontem.
- Nie opisywać gotowego kodu Sygnalisty jako działającego internetowego
  zgłoszenia ani GitHub Issue, dopóki Worker i endpoint nie zostaną świadomie
  wdrożone i odebrane. Prywatne repozytorium intake i etykiety już istnieją;
  brakującą granicą jest Cloudflare, sekret o minimalnym zakresie i raport
  próbny.
- Nie opisywać logowania YouTube; `YT-001` jest odłożone do czasu po
  instalatorze i pierwszych stabilnych wydaniach.
- Pomoc `Ctrl+F1`, pełna pomoc klawiatury, menu i paleta `Ctrl+Shift+K` mają
  być opisywane jako różne powierzchnie jednego katalogu poleceń, a nie jako
  niezależne listy funkcji.

## Następny krok redakcyjny

Po ręcznym odbiorze użytkownika złożyć z powyższych źródeł dwa osobne teksty:

1. instrukcję funkcji według codziennych czynności użytkownika;
2. opis zmian według wersji faktycznie zbudowanej i zainstalowanej.

Żadnego z tych tekstów nie publikować automatycznie.
