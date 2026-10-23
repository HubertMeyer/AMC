# AMC08 — natywne playlisty Spotify

Status: **Użytkownik potwierdził prawdziwe OAuth i skuteczne dodawanie do
playlist Spotify. Korekta jawnej mowy stanu konta oraz widoczności pod
`Ctrl+P` playlist istniejących i właśnie utworzonych jest zainstalowana w AMC
Test; czeka na ręczny odbiór NVDA. Dodatkowa korekta unieważnienia migawki po
ponownym logowaniu także jest zbudowana, zainstalowana i uruchomiona; czeka na
ręczny odbiór NVDA na prawdziwym koncie. Korekta z 23.10.2026 naprawiająca
odświeżanie zapisanych podcastów i odcinków oraz opisująca granice pełnego
ładowania została zainstalowana i uruchomiona w zbiorczym AMC Test
`23.10.2026, 11:24`; zastępuje to niższe historyczne informacje o braku
instalacji. Zapis:
[AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md](AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md).**

**Korekta użytkownika z 23.10.2026, po instalacji 11:24:** otwarcie programu
„TyfloPodcast” nadal kończyło się bez listy i bez odtwarzania. Ten wynik
zastępuje wcześniejsze założenie, że odświeżenie kolekcji rozwiązało również
otwieranie dużego programu. Log AMC potwierdził wykonanie właściwego polecenia
`spotify.containerItems`, więc problem nie dotyczył klawisza Enter ani starej
instalacji. Rzeczywiste Web API zwróciło 2873 rekordy, w tym 10 wartości
`null`; parser próbował czytać je jak odcinki i przerywał całe żądanie.

Nowa korekta pomija wyłącznie puste rekordy i odsłania odcinki programu
narastająco po 150 przez pozycję „Załaduj więcej”, zamiast blokować interfejs
pełnym odczytem kilku tysięcy pozycji. Rzeczywisty odczyt z konta, bez zmiany
danych użytkownika, zwrócił pierwsze 150 odcinków, `hasMore=true`, w 3,38 s.
Kod i testy celowane są gotowe; poniższy status instalacji zostanie uzupełniony
po zbudowaniu i promocji nowego AMC Test. AMC Public pozostaje bez zmian.

Źródło decyzji: zatwierdzona analiza historyczna tylko do odczytu
`D:\Projekty Codex\Accessible Multimedia Controller\AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

- W sesji Spotify `Ctrl+P` otwiera listę natywnych playlist konta Spotify.
  Przy pierwszym otwarciu w danym uruchomieniu AMC pobiera wąską, aktualną
  listę playlist konta. Następne otwarcia korzystają z tej pamięci i nie
  uruchamiają pełnej synchronizacji kolekcji. Samo wejście na listę nie
  obiecuje odtwarzania całej playlisty.
- Po utworzeniu playlisty w AMC potwierdzony wpis pojawia się od razu zarówno
  przy następnym `Ctrl+Shift+P`, jak i na liście otwieranej przez `Ctrl+P`.
  Nie trzeba wykonywać pełnej synchronizacji całej kolekcji Spotify.
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
- Starsze logowanie Spotify nie zawiera zgód na zmianę playlist. AMC nie może
  wtedy utworzyć playlisty ani dodać do niej elementów. W sesji Spotify
  `Ctrl+F5` oraz „Konto Spotify” otwierają dostępne okno konta. Dopiero
  przycisk „Zaloguj w przeglądarce” rozpoczyna oficjalne OAuth i prosi między
  innymi o zgodę na prywatne i publiczne playlisty. Hasło podaje się wyłącznie
  na stronie Spotify; AMC nie prosi o przepisywanie kodu.
- Samo otwarcie konta przez `Ctrl+F5` nie rozpoczyna ponownego logowania. AMC
  odczytuje bieżący stan i jawnie mówi między innymi, że katalog Spotify jest
  połączony oraz czy konto odtwarzania jest gotowe. OAuth zaczyna dopiero
  przycisk „Zaloguj w przeglądarce”.
- Po udanym ponownym logowaniu następne `Ctrl+P` pobiera playlisty bieżącego
  konta od nowa dokładnie raz. AMC nie pokazuje wtedy migawki sprzed logowania
  ani playlist poprzedniego konta.
- Pierwsze wejście w „Podcasty Spotify” albo „Zapisane odcinki Spotify” w
  danym uruchomieniu pobiera oba zbiory z konta. Następne otwarcia korzystają
  z jednej migawki. Prawidłowy pusty wynik usuwa stare wpisy; przy częściowej
  awarii AMC zachowuje ostatni zapis brakującej części i czyta ostrzeżenie.
- Kolekcje są pobierane z Web API po stronach po 50 pozycji aż do braku adresu
  `next`, a interfejs odsłania migawkę narastająco po 150 pozycji przez
  „Załaduj więcej”. Otwarcie programu pobiera tylko tyle stron jego odcinków,
  ile potrzeba do bieżącej porcji 150 pozycji. Bezpiecznik klienta kończy
  pojedynczy pełny odczyt po 400 stronach;
  nie wolno opisywać tego jako listy bez technicznej granicy.
- Wyszukiwanie Spotify pozostaje podglądem: jedno zapytanie pokazuje najwyżej
  10 wyników każdego rodzaju. Interfejs mówi o tym w ostrzeżeniu; AMC nie
  przedstawia tego podglądu jako kompletnego wyniku wyszukiwania.
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

### Audyt podcastów, odcinków i pełnego ładowania — 23.10.2026

Odpowiedzialności są rozdzielone. Oficjalne Web API zasila katalog przez
`/me/shows`, `/me/episodes` i `/shows/{id}/episodes`; przypięty Librespot służy
wyłącznie do odtwarzania utworu lub odcinka i transportu. Brak podcastu na
liście nie jest zatem ograniczeniem Librespota.

Audyt znalazł błąd AMC: koordynator używał niepustej trwałej migawki od razu.
Jeżeli zawierała na przykład utwór albo album, wejście w podcasty nie
uruchamiało synchronizacji i mogło do końca procesu pokazywać niepełną starą
listę. Naprawa wykonuje jeden wąski odczyt programów i zapisanych odcinków przy
pierwszym wejściu w jeden z tych widoków, nawet gdy inne kategorie są już w
cache. Ponowne otwarcie nie dubluje sieci, a udane logowanie unieważnia tę
migawkę.

Zachowanie błędów jest jawne:

- pełny sukces zastępuje oba zbiory, również prawidłowym pustym wynikiem;
- częściowy sukces scala nowe dane z ostatnim zapisem i oznajmia, że jednej
  części nie udało się odświeżyć;
- pełna awaria zostawia ostatni zapis i podaje bezpieczny komunikat bez tokenu,
  adresu ani szczegółów wyjątku.

Klient API wysyła `limit=50` i podąża za dokładnym adresem `next`. Dotyczy to
zapisanych programów, zapisanych odcinków oraz odcinków otwartego programu.
Wewnętrzny limit bezpieczeństwa wynosi 400 stron. Widoki głównych kolekcji
wykonują następnie lokalne, narastające porcje po 150. Wyszukiwanie nie jest
pełną kolekcją: po zmianie Spotify z lutego 2026 limit jednego żądania wynosi
10 na rodzaj, a AMC obecnie nie stronicuje wyszukiwania; dlatego wynik dostał
jawne ostrzeżenie.

Oficjalne źródła sprawdzone 23.10.2026:
[zapisane programy](https://developer.spotify.com/documentation/web-api/reference/get-users-saved-shows),
[zapisane odcinki](https://developer.spotify.com/documentation/web-api/reference/get-users-saved-episodes),
[odcinki programu](https://developer.spotify.com/documentation/web-api/reference/get-a-shows-episodes)
oraz [zmiana limitu wyszukiwania z lutego 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).

- **Korekta użytkownika z 21 października 2026 uzupełnia wcześniejszy odbiór
  logowania i `Ctrl+P`.** Sukces OAuth unieważnia teraz migawkę kolekcji oraz
  znaczniki jednorazowego odświeżenia playlist i albumów. Nie kasuje danych
  Biblioteki ani trwałych ustawień; następne wejście do kategorii wykonuje
  jeden właściwy odczyt dla aktualnego konta.

- **Korekta użytkownika z 20 października 2026 zastępuje wcześniejsze
  ograniczenie „odbiór na prawdziwym koncie niewykonany”.** Użytkownik
  zalogował się ponownie, potwierdził skuteczne dodanie utworu do utworzonej
  playlisty na urządzeniu oraz działanie `F5`. Pozostały dwa konkretne braki:
  stan zalogowania nie był wypowiadany po `Ctrl+F5`, a potwierdzona nowa
  playlista nie pojawiała się w osobnym widoku `Ctrl+P`.
- Lista celów dodawania i widok kolekcji są różnymi powierzchniami. Po
  potwierdzonym utworzeniu host dopisuje teraz tę samą playlistę do bieżącej
  migawki kolekcji. Nie ufa temu wpisowi jako uprawnieniu do zapisu; właściwe
  dodawanie nadal ponownie weryfikuje playlistę po stronie dostawcy.
- **Korekta użytkownika z 20 października 2026 uzupełnia poprzednią poprawkę
  widoczności.** Dodawanie do nowej playlisty zostało potwierdzone na
  urządzeniu, ale osobny widok `Ctrl+P` nie pokazywał playlisty utworzonej
  przed bieżącym uruchomieniem AMC. Pierwsze `Ctrl+P` w procesie korzysta
  teraz z wąskiego odczytu `/me/playlists`, scala wynik z bieżącą kolekcją i
  zachowuje pozostałe pozycje. Ten odczyt nie uruchamia kosztownej pełnej
  synchronizacji katalogu Spotify.

- **Korekta użytkownika z 19 października 2026 zastępuje wcześniejsze
  ustalenie, że `Ctrl+F5` ma być wyłącznie odświeżaniem źródeł.** Historyczny
  kontrakt AMC został przywrócony kontekstowo: w Spotify i TIDAL otwiera konto,
  w WiiM odświeża urządzenia, w Podcastach odświeża Bibliotekę, a w Sonos
  zachowuje wybór celu. Rzeczywisty profil Spotify ma
  zakresy odczytu playlist, ale nie ma `playlist-modify-private` ani
  `playlist-modify-public`. Dlatego lista istniejących playlist może się
  otworzyć, lecz Spotify odrzuca utworzenie i dodanie. Potwierdzonej nowej
  playlisty nie ma potem w pamięci ani na kolejnym otwarciu. Nowe okno konta
  daje świadome wejście OAuth; dopiero po jego ręcznym odbiorze należy ponowić
  odbiór tworzenia, dodawania, cache'u i zapamiętania celu.

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

- 23 października 2026 ukierunkowany kontrakt Spotify przeszedł **1/1**.
  Nowe scenariusze obejmują niepusty cache innej kategorii, wspólny odczyt
  programów i odcinków dokładnie raz, ponowne otwarcie, prawidłowy pusty
  wynik, częściową odpowiedź z zachowaniem cache oraz unieważnienie po
  logowaniu.
- Test atrap rzeczywistego `SpotifyApiClient` i adaptera Librespot zaliczony:
  oba zapisane zbiory i odcinki programu podążają za `next`, a odcinek dochodzi
  do hosta jako `spotify:episode:…`. Test nie używa konta ani prawdziwego
  tokenu i nie dowodzi obecności natywnych rozdziałów.
- Sześć modułów wxPython: **93 zaliczone**; moduł dialogu playlist uruchomiony
  oddzielnie z przewidzianą atrapą wx: **6 zaliczonych**. Wspólny przebieg z
  prawdziwym wxPython nie jest liczony jako regresja, ponieważ jedna próba
  dialogu celowo wymaga atrapy i kolidowała ze wcześniej załadowanym wx.
- LiteHost Release: kompilacja zaliczona, **0 ostrzeżeń i 0 błędów**.
- Nie wykonano prawdziwego OAuth, odczytu konta, instalacji, uruchomienia AMC,
  budowy instalatora ani publikacji.

- 21 października 2026 ukierunkowane zestawy protokołu Spotify oraz YouTube
  przeszły 2 z 2. Nowy scenariusz otworzył `Ctrl+P` przed logowaniem, zmienił
  konto atrapą OAuth i potwierdził jeden świeży odczyt oraz brak starej
  playlisty po logowaniu. Kod nie wykonywał prawdziwego OAuth ani mutacji konta.

- 21 października 2026 potwierdzono, że commity `39386e90` i `640afc65` są
  przodkami zainstalowanej rewizji `a947f79d`. Dokładnie ta rewizja przeszła
  pełną regresję: **1910 zaliczonych, 110 pominiętych i 11 podtestów**, została
  zbudowana, atomowo zainstalowana i uruchomiona jako AMC Test.
- Nie wykonano kolejnej mutacji prawdziwego konta Spotify. Jutrzejszy odbiór
  ma sprawdzić istniejącą playlistę pod `Ctrl+P`, utworzenie nowej przez
  `Ctrl+Shift+P`, ponowne otwarcie obu list i przywrócenie fokusu.

- 19 października 2026, etap konta: **105/105** ukierunkowanych testów wxPython
  sprawdza wspólne polecenie `Ctrl+F5`, menu, etykiety dostępności, fokus,
  klienta hosta oraz to, że interfejs nie przesyła haseł ani tokenów.
  Ukierunkowane testy protokołu .NET dla Spotify, TIDAL i atomowego magazynu
  ustawień: **3/3 zestawy zaliczone**. Kompilacje Release testów protokołu i
  LiteHost zakończyły się bez ostrzeżeń i błędów. Nie otwierano przeglądarki,
  nie wykonywano OAuth ani operacji na prawdziwym koncie.
- Poszerzona regresja wspólnego katalogu poleceń, palety, Menedżera sesji,
  Spotify, TIDAL i WiiM: **191/191 zaliczonych**. Skrypt promocji zbudował
  1667 plików, zweryfikował manifest oraz SHA-256 kandydata i instalacji,
  zastosował aktualizację, a niezależne uruchomienie potwierdziło uruchamiacz,
  LiteHost i okno właściwej wersji. Pierwsze wywołanie przez Windows
  PowerShell 5 zatrzymało się przed budową z powodu kodowania skryptu; właściwa
  promocja w PowerShell 7 zakończyła się powodzeniem.

- 19 października 2026, diagnoza bez mutacji konta: odczytano wyłącznie nazwy
  przyznanych zakresów z lokalnego profilu. Obecne są zakresy odczytu playlist,
  nieobecne są oba zakresy zapisu. Nie uruchamiano OAuth, nie otwierano
  przeglądarki i nie wykonywano kolejnej próby zapisu na Spotify.

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
- 20 października 2026 po ręcznym odbiorze użytkownika: **124 testy**
  interfejsu Spotify, Sonosa, skrótów, pomocy i palety zaliczone. Obejmują
  jawne oznajmienie aktualnego stanu konta bez uruchamiania logowania.
- Kompilacja Release testów protokołu LiteHost: zaliczona, 0 ostrzeżeń i 0
  błędów. Ukierunkowane zestawy `--spotify-catalog --sonos`: **2/2 zaliczone**.
  Nowe testy potwierdzają, że playlista potwierdzona przez Spotify jest od
  razu widoczna pod `Ctrl+P`, playlista istniejąca wcześniej jest pobierana
  tylko raz na proces i pozostaje widoczna przy ponownym otwarciu, pełna
  synchronizacja kolekcji nie jest przy tym wywoływana, a identyfikator
  playlisty nie trafia do etykiety NVDA.
- Próba pełnego ProtocolTests w piaskownicy uruchomiła pozostałe zestawy, ale
  cztery niezwiązane testy zapisu plików zostały zatrzymane przez odmowę
  dostępu do katalogu tymczasowego. Nie przedstawiono tego wyniku ani jako
  regresji kodu, ani jako zaliczonej pełnej regresji. Nie wykonywano nowego
  OAuth ani kolejnej mutacji prawdziwego konta.

## Znane ograniczenia

- Wyszukiwanie Spotify pokazuje obecnie najwyżej 10 wyników każdego rodzaju
  dla jednego zapytania i nie ma „Załaduj więcej”. Jest to jawnie opisany
  podgląd, nie pełny wynik.
- Odczyt kolekcji i zawartości programu podąża za `next`, lecz ma bezpiecznik
  400 stron. Gdyby konto lub program przekroczyły tę granicę, wynik nie byłby
  kompletny; obecny kontrakt nie ma osobnego komunikatu o osiągnięciu tego
  bezpiecznika.
- Korekta podcastów i odcinków z 23.10.2026 jest zweryfikowanym kodem
  źródłowym, nie zainstalowanym AMC Test. Ręczny odbiór NVDA pustej i
  częściowej listy, fokusu oraz ponownego otwarcia pozostaje do wykonania po
  przyszłej instalacji.

- Ponowne logowanie i rzeczywiste dodawanie do playlisty zostały odebrane
  przez użytkownika. Jawna mowa aktualnego stanu konta po `Ctrl+F5` oraz
  odświeżony widok `Ctrl+P` są już zainstalowane, ale wymagają ręcznego odbioru
  NVDA na prawdziwym koncie.
- Korekta czyszczenia migawki po sukcesie OAuth ma zaliczone testy źródła,
  kompilację Release, instalację i uruchomienie w AMC Test. Pozostaje ręczny
  odbiór: po zalogowaniu pierwsze `Ctrl+P` ma pobrać bieżące playlisty dokładnie
  raz i nie pokazać pozycji poprzedniego konta.
- Trwającego OAuth nie można jeszcze anulować przyciskiem okna AMC; do wyniku
  albo limitu czasu okno pozostaje otwarte. Hasła i tokeny nadal nie trafiają
  do interfejsu Python.

- Odtwarzanie całej playlisty Spotify przez AMC nadal nie jest obiecywane.
- Pamięć katalogu obowiązuje do zamknięcia AMC Test. Playlista utworzona w
  AMC trafia do niej natychmiast; zmiana wykonana równolegle w innej aplikacji
  Spotify po pierwszym odczycie będzie widoczna po ponownym uruchomieniu AMC
  Test. Dodawanie nie ufa cache — host ponownie sprawdza uprawnienia i
  istnienie wskazanego celu.
- TIDAL i przyszłe usługi mają teraz wspólny fundament i trwały kontrakt, ale
  ich adapter musi jawnie podłączyć własną zdalną listę. Nie przypisujemy im
  automatycznie tworzenia playlist publicznych ani innych możliwości Spotify.
- Bieżący kontrakt hosta Spotify nie przekazuje interfejsowi stabilnego
  identyfikatora konta. W jednym procesie używane jest bieżące konto; po jego
  zmianie wymagane jest ponowne uruchomienie albo przyszłe jawne unieważnienie
  cache'u przez przepływ logowania. Sam zapis nadal sprawdza konto i prawa w
  hoście, więc pamięć interfejsu nie może nadać uprawnień do obcej playlisty.
- Korekta z 20 października jest potwierdzona w kodzie, testach, kompilacji,
  instalacji i uruchomieniu. Ręczny odbiór mowy `Ctrl+F5` i widoku `Ctrl+P`
  pozostaje do wykonania przez użytkownika.

## Wersja i commit

- Bieżąca instalacja zawierająca `39386e90` i `640afc65`:
  `2026.10.21-a947f79d83f11888e2d1ea353909a1ee50b3ccaa-1dfc80e8` w
  `D:\Projekty Codex\AMC Python`. Pełna regresja, manifest, integralność,
  instalacja i uruchomienie są zaliczone; publikacji nie wykonywano.

- Dostępne konta Spotify i TIDAL oraz kontekstowy `Ctrl+F5`: commit `c3ffea7`
  (`feat(amc): dodaj konta Spotify i TIDAL pod Ctrl+F5`).
- Instalacja i uruchomienie: potwierdzone dla
  `2026.10.19-c3ffea70d9f002d936bbabd43421b03393c9702d-a329942c` w
  `D:\Projekty Codex\AMC Python`. Publikacji nie wykonano.

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
- Jawna mowa stanu kont Spotify/Sonos i zgodność nowej playlisty z widokiem
  `Ctrl+P`: commit `39386e90` — `fix(amc): oznajmiaj konta i synchronizuj
  playlisty Spotify`. Kod, testy interfejsu i ukierunkowane testy protokołu są
  zaliczone; instalacji ani publikacji nie wykonano.
- Jednorazowe odświeżenie istniejących playlist pod `Ctrl+P`: commit
  `640afc65` — `fix(amc08): odswiez playlisty Spotify pod Ctrl+P`. Kod,
  kompilacja Release i ukierunkowane testy protokołu są zaliczone; instalacji
  ani publikacji nie wykonano.
- Unieważnienie migawki playlist po udanym logowaniu: commit `b493ae07` —
  `fix(spotify): refresh playlist view after login`. Ukierunkowane testy
  Spotify i YouTube zaliczone: 2/2 zestawy protokołu. Wspólna bramka
  wyszukiwania i świeżego profilu: 88/88. Właściwy host skompilowano w Release.
- Jednorazowe pełne odświeżenie podcastów i zapisanych odcinków, zachowanie
  częściowego cache oraz jawne granice rozdziałów i wyszukiwania: commit
  `d646bdf20c0b5f050620637bdf4ae73529bcc6a4` —
  `fix(spotify): odswiez podcasty i opisz rozdzialy`. Kod, testy i build
  Release zaliczone; instalacji, uruchomienia i publikacji nie wykonano.
- Zainstalowany i uruchomiony AMC Test: rewizja `b258fb69fef580f7899c30abd0d48e6b877119be`,
  paczka `726f0791`, 1668 plików, etykieta
  `2026.10.21-b258fb69fef580f7899c30abd0d48e6b877119be-726f0791`.
  Integralność i kontrolowany start kandydata oraz zainstalowanej kopii są
  zaliczone. Pełnego zestawu wxPython nie powtarzano: wcześniejszy wspólny
  stan miał 1910 zaliczonych testów, a bieżący przyrost sprawdzono testami
  ukierunkowanymi. Publikacji nie wykonywano.
