# AMC08 — natywne playlisty Spotify

Status: **Korekta po próbie na prawdziwym koncie wdrożona, przetestowana na
atrapach, zainstalowana i uruchomiona; wymaga ponownego logowania oraz odbioru
na prawdziwym koncie**.

Źródło decyzji: zatwierdzona analiza historyczna tylko do odczytu
`D:\Projekty Codex\Accessible Multimedia Controller\AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

- W sesji Spotify `Ctrl+P` otwiera listę natywnych playlist konta Spotify.
  Samo wejście na listę nie obiecuje odtwarzania całej playlisty.
- Na zaznaczonym utworze albo odcinku `Ctrl+Shift+P` otwiera okno „Dodaj do
  playlist Spotify”. Strzałki wybierają playlistę, a Spacja zaznacza lub
  odznacza wiele playlist. Enter wykonuje operację, Escape ją anuluje.
- Przycisk „Nowa playlista…” pyta o nazwę i widoczność: domyślnie prywatną
  albo jawnie publiczną w jednym oknie. Pole ma jednoznaczną nazwę „Nazwa
  playlisty Spotify”. Nowa playlista jest od razu zaznaczona jako cel, a AMC
  mówi, że kolejny Enter utworzy ją i doda wybrane elementy.
- Przy pierwszym `Ctrl+Shift+P` w danym uruchomieniu AMC mówi „Pobieram
  playlisty Spotify”. Kolejne otwarcia korzystają z pamięci podręcznej i nie
  pobierają tej samej listy ponownie. Po zapisie AMC mówi, ile pozycji dodano,
  które były już obecne oraz czy wynik jest częściowy.
- Playlista utworzona w oknie od razu trafia do listy bieżącego uruchomienia.
  Przy następnym `Ctrl+Shift+P` jest widoczna, a ostatnio użyte playlisty są
  zaznaczone. Ich wybór jest zapisany w prywatnych ustawieniach AMC Test.
- Starsze logowanie Spotify nie zawiera zgód na zmianę playlist. AMC nie
  otwiera wtedy przeglądarki samoczynnie, tylko kieruje do `Ctrl+F5`, aby
  użytkownik świadomie zalogował konto ponownie.
- Lista odczytywana przez NVDA zawiera tylko nazwę, widoczność, informację o
  współdzieleniu i właścicielu oraz stan zaznaczenia. Identyfikatory playlist,
  adresy i `snapshot_id` pozostają niewidocznymi danymi modelu.
- `Ctrl+F1`, pełna pomoc, menu i paleta `Ctrl+Shift+K` używają tego samego
  polecenia. W Spotify brzmi ono „Dodaj do playlist Spotify lub utwórz
  playlistę”; w Plikach, Radiu i Podcastach zachowuje lokalne znaczenie
  „Przynależność do playlist”.
- To samo zachowanie ma obowiązywać w następnych usługach, które udostępnią
  zdalne playlisty albo inne cele: pierwsze otwarcie pobiera listę, kolejne
  korzysta z pamięci bieżącego uruchomienia, potwierdzony nowy cel pojawia się
  od razu, a ostatni wybór wraca z właściwego profilu. Mechanizm ma osobne
  partycje usług i kont, aby adapter z dostępną tożsamością konta nie pomieszał
  celów nawet przy takich samych nazwach lub identyfikatorach.

## Uzasadnienie i decyzje

- **Korekta użytkownika z 19 października 2026 zastępuje wcześniejszy odbiór
  cache'u oparty tylko na atrapach.** W prawdziwym użyciu pole nazwy było
  niejednoznaczne, nie było wiadomo, który Enter jedynie przygotowuje cel, a
  nowa playlista nie wracała na następną listę. Nazwa i widoczność są teraz w
  jednym dostępnym formularzu, przygotowanie i rozpoczęcie zapisu mają osobne
  komunikaty, a pusta nazwa dostępna z odpowiedzi hosta jest uzupełniana
  świadomą etykietą użytkową.
- Potwierdzenie HTTP 201 po utworzeniu jest autorytatywne dla bieżącego konta.
  Jeżeli późniejszy odczyt `/me/playlists` jest chwilowo niespójny, host
  zachowuje potwierdzony cel i pozwala natychmiast dodać element. Gdy katalog
  zacznie już zwracać playlistę, wpis przejściowy jest usuwany; nie staje się
  trwałym źródłem uprawnień.

- **Korekta użytkownika z 18 października 2026:** `Ctrl+Shift+P` zastępuje
  wcześniejszy pomysł osobnego `Alt+Shift+P`.
- **Korekta użytkownika z 18 października 2026:** tworzone są prawdziwe
  playlisty Spotify, które można udostępnić. Funkcja nie obiecuje odtwarzania
  całych playlist przez Librespot.
- Używane są ścieżki `/me/playlists` i `/playlists/{id}/items`. Odczyt
  zawartości przyjmuje pole `item`, a `track` wyłącznie jako kontrolowany
  fallback zgodności.
- Wejściowe utwory i odcinki są odduplikowane. Przed zapisem klient odczytuje
  istniejącą zawartość każdej playlisty, więc ponowienie nie dopisuje drugiego
  wystąpienia tej samej pozycji.
- Jedno żądanie zawiera najwyżej 100 pozycji. Każda przyjęta partia zapisuje
  zwrócony `snapshot_id`; awaria późniejszej partii zachowuje i raportuje
  wcześniejszy sukces.
- Identyfikatory playlist z wxPython są ponownie rozwiązywane na świeżej liście
  edytowalnych playlist wewnątrz C#. Interfejs nie może nadać sobie prawa do
  cudzej playlisty przez podmianę danych żądania.
- OAuth prosi jawnie o `playlist-modify-private` oraz
  `playlist-modify-public`. Bez obecności użytkownika nie jest rozpoczynane
  ponowne logowanie i żaden test nie zapisuje danych na prawdziwym koncie.
- **Korekta użytkownika z 19 października 2026 zastępuje wcześniejsze
  pobieranie listy przy każdym `Ctrl+Shift+P`.** Lista jest pobierana raz na
  proces, ale samo dodanie nadal przechodzi przez świeżą weryfikację hosta.
  Potwierdzona nowa playlista jest dopisywana do pamięci, zamiast czekać na
  późniejsze odświeżenie katalogu Spotify.
- **Korekta użytkownika z 19 października 2026 rozszerza tę zasadę na kolejne
  wdrażane usługi.** Powstał neutralny mechanizm list celów przygotowany do
  rozdzielenia usługi i konta. Nie narzuca on innym dostawcom endpointów ani możliwości
  Spotify. Pamięć przyspiesza interfejs, natomiast zapis zawsze przechodzi
  przez świeżą walidację adaptera konkretnej usługi.

## Testy i wynik

- Po korekcie prawdziwego przepływu: **136/136** testów ukierunkowanych oraz
  pełna regresja wxPython **1845 zaliczonych, 110 pominiętych, 11 podtestów**.
- Osobny test hosta kompiluje rzeczywisty `SpotifyIntegrationService` i
  symuluje opóźnione `/me/playlists`: nowa playlista pozostaje widoczna i
  przyjmuje utwór. Kompilacja i ten test zakończyły się kodem 0.

- 19 października 2026, przed 02:00: `py_compile` zmienionych modułów —
  zaliczony.
- 19 października 2026, odizolowane testy Pythona: parser etykiet, przepływ
  tworzenia i dodawania, fokus po dialogu, klient hosta, skróty, menu,
  `Ctrl+F1` i paleta `Ctrl+Shift+K` — **101 zaliczonych**.
- Po wzmocnieniu obsługi niepotwierdzonego utworzenia playlisty ponowiono
  ukierunkowany zestaw — **63 zaliczone**.
- Pełna odizolowana regresja wxPython po ostatecznej zmianie — **1754
  zaliczone, 110 pominiętych, 11 podtestów zaliczonych** w 91,86 s.
- Testy atrap C# obejmują zakresy OAuth, listę edytowalnych playlist,
  prywatne i publiczne tworzenie, partie 100, idempotencję, `snapshot_id`,
  endpoint `/items` i wynik częściowy. Ukierunkowane zestawy playlist i
  istniejącej zmiany Biblioteki Spotify zaliczone; pełne Core SmokeTests
  zakończone kodem 0.
- Ukierunkowany kontrakt protokołu playlist zaliczony **1/1**, a pełna regresja
  LiteHost ProtocolTests — **20/20 zestawów**.
- Kompilacja Release Core SmokeTests, LiteHost ProtocolTests i właściwego
  LiteHost zakończona powodzeniem, bez ostrzeżeń i błędów.
- Bramkę bezpieczeństwa po 02:00 zaliczono: żaden harmonogram nie pozostawał
  w aktywnym oknie, przez 10 sekund nie rósł żaden plik `.amc-partial`, a żaden
  z zachowanych plików odzyskiwania nie był zablokowany przez proces.
- Nie wykonano odbioru sieciowego ani zapisu na koncie Spotify.
- Procedura promocji ponownie zaliczyła pełne **1754** testy wxPython,
  zbudowała paczkę 1659 plików, sprawdziła jej manifest i sumy SHA-256,
  zainstalowała ją oraz potwierdziła uruchomienie właściwego procesu i tytułu.
- 19 października 2026 po zgłoszeniu z prawdziwego użycia: bramka obejmująca
  cache, nową playlistę, zapamiętanie celów, magazyn ustawień, menu,
  nagrywanie i harmonogramy — **204 zaliczone**. Atrapa potwierdza, że dwa
  kolejne wywołania pobierają katalog tylko raz, nowa publiczna playlista jest
  widoczna za drugim razem, oba ostatnie cele są zaznaczone, a wybór przeżywa
  zapis ustawień. Korekta nie została jeszcze zainstalowana ani odebrana w
  sieci na prawdziwym koncie.
- Szeroki audyt menu, skrótów i sesji: **403 zaliczone i 5 podtestów**.
  Pełna regresja wxPython po połączeniu korekt: **1837 zaliczonych, 110
  pominiętych i 11 podtestów zaliczonych**.
- Po uogólnieniu mechanizmu: **61 zaliczonych** testów Spotify, wspólnego
  cache'u, migracji i magazynu oraz **121 zaliczonych** testów menu, skrótów,
  pomocy i palety. Testy potwierdzają izolację Spotify/TIDAL i dwóch kont,
  selektywne unieważnianie, natychmiastowe dopisanie potwierdzonego celu oraz
  migrację wcześniejszego pola ustawień Spotify.
- Pełna regresja wxPython po uogólnieniu: **1842 zaliczone, 110 pominiętych i
  11 podtestów zaliczonych** w 78,80 s. Cztery testy hosta podcastów, które w
  pierwszym przebiegu zatrzymała blokada lokalnego `127.0.0.1`, zaliczyły się
  po udzieleniu dostępu do testowego serwera lokalnego; drugi pełny przebieg
  zakończył się bez błędów.
- 19 października 2026 przy promocji do AMC Test pełna regresja została
  powtórzona: **1842 zaliczone, 110 pominiętych i 11 podtestów zaliczonych** w
  86,72 s. Kompilacje Release zakończyły się bez ostrzeżeń i błędów. Paczka
  1666 plików przeszła kontrolę manifestu i SHA-256, instalację, osobną
  kontrolę integralności z kodem 0 oraz weryfikację uruchomionego procesu.
- Nie wykonano automatycznego OAuth ani zapisu na prawdziwym koncie Spotify.

## Znane ograniczenia

- Korekta `4b85e0c8` została zainstalowana. Nie wykonano po niej kolejnego
  zapisu na prawdziwym koncie Spotify; odbiór sieciowy wymaga świadomej próby
  użytkownika.
- Token zapisany przed tą korektą nie zawiera zakresów
  `playlist-modify-private` i `playlist-modify-public`. Przed próbą tworzenia
  i dodawania trzeba wykonać `Ctrl+F5` w sesji Spotify i ponownie zatwierdzić
  logowanie. Bez tego Spotify prawidłowo odmówi zapisu niezależnie od działania
  interfejsu AMC.

- Odtwarzanie całej playlisty Spotify przez AMC nadal nie jest obiecywane.
- Zewnętrzny odbiór na prawdziwym koncie, w tym ponowne OAuth z nowymi
  zakresami, pozostaje zadaniem ręcznym.
- Ręczny test NVDA i prawdziwego konta Spotify nie został wykonany. Sama
  poprawna instalacja nie potwierdza jeszcze odbioru mowy ani operacji
  sieciowej na koncie.
- Pamięć katalogu obowiązuje do zamknięcia AMC Test. Playlista utworzona w
  AMC trafia do niej natychmiast; zmiana wykonana równolegle w innej aplikacji
  Spotify będzie widoczna po ponownym uruchomieniu AMC Test. Dodawanie nie
  ufa cache — host ponownie sprawdza uprawnienia i istnienie wskazanego celu.
- TIDAL i przyszłe usługi mają teraz wspólny fundament i trwały kontrakt, ale
  ich adapter musi jawnie podłączyć własną zdalną listę. Nie przypisujemy im
  automatycznie tworzenia playlist publicznych ani innych możliwości Spotify.
- Bieżący kontrakt hosta Spotify nie przekazuje interfejsowi stabilnego
  identyfikatora konta. W jednym procesie używane jest bieżące konto; po jego
  zmianie wymagane jest ponowne uruchomienie albo przyszłe jawne unieważnienie
  cache'u przez przepływ logowania. Sam zapis nadal sprawdza konto i prawa w
  hoście, więc pamięć interfejsu nie może nadać uprawnień do obcej playlisty.

## Wersja i commit

- Korekta po odbiorze: `4b85e0c8` — kod, testy wxPython i test hosta C#;
  pełny pakiet AMC Test zbudowano, zainstalowano i uruchomiono.
- Instalacja zawierająca korektę:
  `2026.10.19-0c098eb5dde2b039f5d6f86c415559d63c84adcc-9e2be1b9`;
  publikacji nie wykonano.

- Profil docelowy: bieżący AMC Test.
- Kod źródłowy: commit `697d1a73fd66c12bfa061f4d5f55a93ddaa36e85`.
- Kompilacja: Release, zaliczona 19 października 2026 po bezpiecznej bramce
  nagrywania.
- Instalacja: `2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonywać w tym etapie.
- Korekta cache i ostatniego celu: commit `fdc26b83` — `fix(amc): uporzadkuj
  nagrania menu i playlisty Spotify`.
- Uogólnienie dla kolejnych usług: commit `e317cbbc` — `refactor(amc):
  ujednolic listy uslug i kontrakt menu`.
- Instalacja zawierająca obie korekty:
  `2026.10.19-8093e22adfa9b6abfc72c35c5c7029eaaade88c8-718893c9`;
  manifest, sumy, integralność i uruchomienie zweryfikowane 19 października
  2026. Publikacji nie wykonano.
