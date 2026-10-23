# AMC Test 24.10.2026, 00:21 — trwałe usunięcia i kolejka YouTube

- Status: **zbudowane, atomowo zainstalowane i uruchomione; automatyczne
  bramki zaliczone, czeka na ręczny odbiór NVDA transmisji i radia YouTube**.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Profil: wyłącznie AMC Test. AMC Public, instalator publiczny i GitHub nie
  zostały zmienione.

## Zachowanie widoczne dla użytkownika

- Samo ponowne uruchomienie AMC ani zalogowanie do Google nie pobiera ponownie
  wszystkich subskrypcji i nie przywraca elementów usuniętych z Biblioteki.
- Usunięty kanał pozostaje wyłączony po restarcie i następnej synchronizacji.
  Przywrócenie wymaga jawnego pola `Przywróć kanały i playlisty wcześniej
  usunięte z Biblioteki AMC`.
- Pojedynczy usunięty film również nie wraca po odświeżeniu kanału, ponieważ
  ma osobny trwały zapis usunięcia.
- Automatyczne odświeżanie nie zatrzymuje już całej Biblioteki na tych samych
  pięciu kanałach. Każda próba ma własny czas odroczenia; niepowodzenie nie
  udaje poprawnego odświeżenia, a następna porcja dostaje kolejkę.
- Kanał bez standardowej karty `Filmy` jest sprawdzany przez publiczną stronę
  główną. Playlista i zwykły błąd sieci nie uruchamiają tego obejścia.
- Na zaznaczonym kanale YouTube `Ctrl+T` otwiera transmisje na żywo i
  zaplanowane, a `Ctrl+Y` tworzy dynamiczną stację Radia z publicznego adresu
  kanału `/live`.

## Dostępność i powierzchnie poleceń

`Ctrl+T` i `Ctrl+Y` pochodzą z jednego współdzielonego modelu używanego przez
routing klawiatury, menu, menu kontekstowe, paletę `Ctrl+Shift+K`, pomoc
`Ctrl+F1` i pełną pomoc. Działają tylko na zaznaczonym kanale YouTube; nie
przejmują tych klawiszy na odcinku, playliście, kanale RSS ani w odtwarzaczu.
`Ctrl+T` jest dostępne tylko z działającym kontem YouTube, a `Ctrl+Y` działa
publicznie bez konta. Etykiety mówią pełnymi nazwami użytkowymi i nie ujawniają
identyfikatora kanału, nazwy klasy ani nazwy operacji hosta.

Okno konta wyjaśnia, że start i logowanie nie przywracają usuniętych kanałów
lub filmów. Tekst rozdziela zwykłą synchronizację od jawnego przywracania.

## Testy i rzeczywiste wyniki

- Celowane testy menu, skrótów, konta i transmisji: **104 zaliczone oraz 2
  podtesty zaliczone**.
- Pełna regresja wxPython, wykonana dwukrotnie po końcowej poprawce:
  **2029 zaliczonych, 111 kontrolowanie pominiętych i 13 podtestów
  zaliczonych**.
- Core `--youtube-subscription-sync-apply`: **5/5 scenariuszy**. Obejmuje
  ponowne otwarcie bazy, brak samoczynnego powrotu kanału, pięć nieudanych
  prób, kolejkę szóstego źródła, ręczne F5 i ponowienie po 60 minutach.
- Windows `--youtube-collection-normalization`: zaliczony. Izolowane testy
  obejścia `/videos`: kanał korzysta z publicznej strony głównej wyłącznie po
  dokładnym błędzie braku karty; playlista i błąd sieci nie korzystają z
  obejścia.
- Publiczna próba na żywym kanale `0dB.pl`, bez logowania i bez zapisu bazy:
  klient zwrócił **100 materiałów**.
- Testy launchera i aktualizatora podczas promocji: **30/30 zaliczonych**.
  Buildy .NET użyte przez promocję: **0 ostrzeżeń i 0 błędów**.
- Pakiet zawiera **1674 pliki**. Kandydat i stała instalacja przeszły kontrolę
  manifestu, sum, izolowany start interfejsu i hosta oraz kontrolowany start po
  atomowej podmianie.
- Przed instalacją dwukrotny odczyt katalogu nagrań wykazał **0 plików
  `.amc-partial`**.
- Rzeczywista baza użytkownika została bez błędu podniesiona do schematu 3.
  Pierwsza porcja automatu zapisała pięć prób: trzy źródła zakończyły się
  sukcesem, dwa zachowały brak czasu sukcesu. Kolejne minuty przeszły do
  następnych źródeł: licznik wzrósł do 13 różnych prób, a liczba kanałów w
  Bibliotece bez pierwszego poprawnego odświeżenia spadła z 96 do 86.
  Wszystkie 123 kanały usunięte lokalnie pozostały poza Biblioteką.

Szerszy Core SmokeTests przeszedł nowe testy YouTube, lecz później zatrzymał
się na zastanym, niezwiązanym teście nazwy powłoki instalatora. Wcześniejszy
szeroki Windows SmokeTests przeszedł zmienione testy i zatrzymał się później
na chwilowej odmowie systemowego schowka `OpenClipboard`. Żadnego z tych dwóch
przebiegów nie przedstawiamy jako pełnej zaliczonej regresji; pełna regresja
interfejsu i wszystkie celowane bramki tej zmiany są zaliczone.

## Zawartość bieżącej wersji zbiorczej

Ta instalacja zawiera również wcześniejsze, już scalone zmiany: poprawione
usuwanie PIN-u urządzenia Frontier Smart, komunikat przygotowania Spotify,
rzeczywistą regulację prędkości Spotify, opisy YouTube pod `Alt+D`, konto i
playlisty YouTube oraz listę transmisji i dynamiczne radio. Użytkownik
potwierdził działanie prędkości Spotify i opisów YouTube. Odbiór Smart Frontier
na fizycznym urządzeniu oraz nowe skróty transmisji pozostają ręczne.

## Znane ograniczenia i ręczny odbiór

- Puste kanały nie muszą oznaczać błędu: autor może nie mieć publicznych
  materiałów albo YouTube może niczego nie zwrócić. Po tej poprawce kanał nie
  blokuje jednak całej kolejki.
- `Ctrl+T` używa oficjalnego API i wymaga aktywnego konta YouTube w AMC Test.
  `Ctrl+Y` zapisuje publiczny adres dynamiczny i nie wymaga konta.
- Tryb testowy zgody Google może nadal wymagać ponownego logowania po
  wygaśnięciu autoryzacji testowej, cofnięciu zgody, unieważnieniu tokenu lub
  wylogowaniu. Zwykły restart AMC nie jest powodem ponownego logowania.
- Użytkownik ma sprawdzić z NVDA: `Ctrl+T`, powrót `Backspace`, `Ctrl+Y`, fokus
  formularza Radia, zapis/anulowanie oraz czy liczba pustych kanałów maleje w
  kolejnych porcjach.

## Projekt instrukcji użytkownika

> Usunięty kanał lub film YouTube nie wraca po restarcie ani następnym
> logowaniu. Aby świadomie przywrócić usunięty kanał, otwórz konto YouTube i
> zaznacz pole przywracania przed ponownym sprawdzeniem i zapisem. Na kanale
> naciśnij Ctrl+T, aby otworzyć transmisje na żywo i zaplanowane, albo Ctrl+Y,
> aby dodać kanał jako dynamiczną stację Radia.

## Projekt opisu zmian

> AMC Test zachowuje lokalne usunięcia YouTube, sprawiedliwie odracza błędne
> kanały i obsługuje kanały bez standardowej karty Filmy. Dodano kontekstowe
> Ctrl+T dla transmisji oraz Ctrl+Y dla dynamicznego radia YouTube.

## Wersja i commit

- Commit źródłowy: `05621539cba449a06986e3544557d7d039b0e2d9` —
  `fix(youtube): preserve removals and unblock refresh`.
- Pakiet: `0ca58fd4`.
- Etykieta: `2026.10.24-05621539cba449a06986e3544557d7d039b0e2d9-0ca58fd4`.
- Okno: `AMC Test — 24.10.2026, 00:21`.
- Potwierdzony proces interfejsu w chwili promocji: PID 58992,
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.
- Promocja zakończona 24.10.2026 o 00:23:45 czasu lokalnego.
