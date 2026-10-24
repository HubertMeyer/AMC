# YT-002 — transmisje YouTube na żywo i dynamiczne radio

- Status: `Zrobione w AMC Test — import i parsowanie kanałów, Ctrl+I,
  Ctrl+T, Ctrl+Shift+I, dynamiczne radio /live, odtwarzanie oraz nagrywanie
  ręczne i z harmonogramu zostały sprawdzone; korekta zakończonych transmisji
  czeka na instalację paczki z 24.10.2026`
- Utworzono: 23 października 2026
- Ostatnia aktualizacja: 24 października 2026
- Obszar: YouTube, Podcasty i YouTube, Radio, nawigacja, NVDA
- Polecenie użytkownika: śledzenie trwających i zaplanowanych transmisji
  zapisanych kanałów oraz radio automatycznie odnajdujące zmienny link live

## Cel

Kanał zapisany w Bibliotece AMC ma oferować osobną listę transmisji trwających
i zaplanowanych. Publiczny adres wskazanej transmisji można skopiować albo
uruchomić Enterem w wewnętrznym silniku AMC. Ten sam kanał można także zapisać
jako dynamiczną stację radiową; stacja przechowuje stabilny adres kanału
`/live`, a silnik przy każdym uruchomieniu odnajduje bieżący film, więc nie
trzeba ręcznie podmieniać wygasającego adresu `watch`.

## Zachowanie użytkowe i dokładne polecenia

1. W sesji `Podcasty i YouTube` ustaw fokus na źródle typu `kanał YouTube`.
2. Menu Plik, menu kontekstowe `Shift+F10` i paleta `Ctrl+Shift+K` udostępniają:
   - `Transmisje na żywo i zaplanowane kanału…` — `Ctrl+T`;
   - `Dodaj kanał jako dynamiczne radio YouTube na żywo…` — `Ctrl+Y`.
   Skróty działają wyłącznie wtedy, gdy na liście jest zaznaczony kanał
   YouTube. `Ctrl+T` wymaga dostępnego konta YouTube, natomiast `Ctrl+Y`
   korzysta z publicznego adresu kanału i nie wymaga logowania.
3. Pierwsze polecenie otwiera listę `Transmisje YouTube na żywo i
   zaplanowane`. Wiersz mówi nazwę i jeden świadomie przygotowany stan:
   `na żywo`, `na żywo dzisiaj o GG:MM`, `zaplanowana` albo
   `zaplanowana DD.MM.RRRR o GG:MM`.
4. `F5` w tej liście oznacza `Odśwież transmisje kanału YouTube`. `F5` w
   zwykłym kanale nadal odświeża materiały kanału, a `Ctrl+F5` zachowuje
   dotychczasowe odświeżenie wszystkich źródeł.
5. `Enter` na transmisji używa istniejącego wewnętrznego odtwarzacza AMC.
   `Ctrl+Shift+C` kopiuje jej publiczny adres. `Backspace` wraca na dokładnie
   ten kanał w Bibliotece.
6. Drugie polecenie otwiera natywny formularz `Dodaj dynamiczną stację
   YouTube` z fokusem na polu `Nazwa stacji`. Nazwa oraz stabilny adres
   kanału są już uzupełnione i można je zmienić. `Anuluj` oddaje fokus bez
   przełączania sesji; `OK` przechodzi do Radia i zapisuje stację zwykłą,
   istniejącą drogą profilu.

## Uzasadnienie i decyzje

- Oficjalne YouTube Data API pozwala filtrować `search.list` według
  `channelId` oraz `eventType=live` albo `eventType=upcoming`. Szczegóły czasu
  pochodzą z `videos.list` i `liveStreamingDetails`.
- `liveBroadcasts.list` nie jest właściwą drogą do cudzych subskrybowanych
  kanałów: ten kontrakt służy przede wszystkim transmisjom należącym do
  zalogowanego użytkownika.
- Jedno pełne odświeżenie kanału wykonuje dwa kosztowne wyszukania, dlatego
  nie skanujemy w tle wszystkich subskrypcji. Wynik jednego kanału jest
  przechowywany przez pięć minut; jawne `F5` omija pamięć podręczną.
- Dynamiczne radio nie korzysta z tego limitu API. Stabilny publiczny adres
  `/channel/…/live` albo `/@nazwa/live` jest rozwiązywany dopiero przy Enterze
  przez istniejący `YouTubeSourceResolver`. Gdy pod zapisanym adresem nie ma
  aktywnej transmisji, silnik zgłasza zwykły brak dostępnego strumienia.
- Token OAuth i techniczny identyfikator kanału pozostają w hoście C#.
  Python dostaje tylko tytuł, publiczny adres filmu, stan oraz czas
  przeznaczone do wyświetlenia. Techniczne ID filmu nie trafia do protokołu.
- Ręcznie dodany kanał `@nazwa` korzysta z identyfikatora zapisanego wcześniej
  wewnątrz stabilnego ID subskrypcji. Awaryjny lokalny hash nie jest wysyłany
  do API jako rzekomy identyfikator kanału.

## Testy i wynik

Stan z 23 października 2026 przed pełną promocją:

- `YouTubeBroadcastClientTests`: 3/3 scenariusze zaliczone — live, upcoming,
  czasy, Bearer, limit API bez wycieku odpowiedzi i odmowa niebezpiecznego ID.
- `AccessibleMediaController.LiteHost.ProtocolTests`: 27/27 zestawów
  zaliczonych; kontrakt YouTube ma 8 scenariuszy i nie ujawnia ID filmu.
- Celowane testy wxlite: 178 zaliczonych i 2 podtesty — transmisje, Podcasty,
  skróty, menu, paleta, źródła i klient hosta.
- Pełna regresja wxlite po korekcie klasyfikacji widoku: 2024 zaliczone, 111
  kontrolowanie pominiętych i 13 zaliczonych podtestów.
- Własny test YT-002: 5/5 scenariuszy — stały adres, jawne etykiety,
  Enter/Backspace/F5 oraz parytet menu–kontekst–paleta–pomoc.
- `dotnet build AccessibleMediaController.LiteHost.csproj --no-restore`:
  sukces, 0 ostrzeżeń, 0 błędów.
- Procedura promocji powtórzyła pełną regresję: 2024 zaliczone, 111 pominiętych,
  13 podtestów; launcher i aktualizator 30/30, buildy .NET po 0 ostrzeżeń i 0
  błędów.
- Kandydat miał 1674 pliki. Integralność, kontrolowany start kandydata,
  atomowa instalacja, integralność zainstalowanej kopii i jej kontrolowany
  start: zaliczone.
- Ręczny odbiór NVDA i prawdziwy odczyt transmisji z konta: jeszcze nie
  wykonane w chwili tego zapisu.

## Znane ograniczenia

- YouTube tworzy niektóre zaplanowane linki dopiero krótko przed transmisją.
  AMC nie pokaże czegoś, czego nie ma jeszcze w publicznym API; wtedy należy
  nacisnąć F5 później.
- Kanał może usunąć zapis albo nie pozostawić przewijalnego archiwum. AMC nie
  może zachować filmu, którego właściciel już nie udostępnia.
- Pierwsza wersja pokazuje najwyżej 25 transmisji live i 25 upcoming jednego
  kanału. Nie wykonuje kosztownego, stałego monitoringu całej Biblioteki.
- Lista transmisji wymaga zalogowanego konta YouTube w AMC Test. Dynamiczne
  radio działa także bez konta, jeżeli publiczna transmisja jest dostępna.
- AMC Public pozostaje bez listy konta i transmisji do osobnej decyzji po
  odbiorze. Dynamiczne radio używa ogólnego, publicznego resolvera, ale w tej
  realizacji nie przygotowano ani nie opublikowano nowej wersji publicznej.

## Materiał do dokumentacji użytkownika

Projekt instrukcji:

> Aby sprawdzić transmisje kanału, ustaw na nim fokus w Bibliotece `Podcasty i
> YouTube`, otwórz menu kontekstowe i wybierz `Transmisje na żywo i
> zaplanowane kanału`. Enter odtwarza, Ctrl+Shift+C kopiuje adres, F5 sprawdza
> kanał ponownie, a Backspace wraca do Biblioteki. Jeśli chcesz mieć pozycję w
> Radiu, użyj `Dodaj kanał jako dynamiczne radio YouTube na żywo`. Taka stacja
> sama odnajduje aktualną transmisję kanału i nie wymaga ręcznej zmiany adresu
> po każdej mszy, koncercie lub audycji.

Projekt opisu zmian:

> AMC Test potrafi wyświetlić trwające i zaplanowane transmisje zapisanego
> kanału YouTube oraz dodać kanał jako dynamiczną stację Radia. Lista ma
> spójne polecenia menu, kontekstu, palety i pomocy; Enter korzysta z
> wewnętrznego odtwarzacza, F5 odświeża, a Backspace wraca do kanału.

## Wersja i commit

- Gałąź: `integration/amc-test-20261023-late`.
- Commit źródłowy: `4119476314529741741639de6ee662951e656092`.
- Zainstalowano i uruchomiono `AMC Test — 23.10.2026, 21:25` w
  `D:\Projekty Codex\AMC Python`.
- Identyfikator paczki: `dd5f80fc`; uruchomiony PID w chwili weryfikacji:
  `41544`, dokładny plik:
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.
- GitHub i AMC Public: bez zmian.

### Korekta skrótów i bieżąca instalacja — 24.10.2026

Korekta użytkownika dodaje kontekstowe `Ctrl+T` i `Ctrl+Y`. Oba skróty są
zdefiniowane w tym samym modelu, z którego korzystają wykonanie, menu, menu
kontekstowe, paleta `Ctrl+Shift+K`, pomoc `Ctrl+F1` i pełna pomoc. Nie działają
na odcinku, playliście, kanale RSS ani w odtwarzaczu. Testy sprawdzają również
brak technicznych nazw obiektów w etykietach oraz ukrycie `Ctrl+T`, gdy konto
YouTube jest niedostępne.

Zainstalowana wersja to `AMC Test — 24.10.2026, 00:21`, commit
`05621539cba449a06986e3544557d7d039b0e2d9`, pakiet `0ca58fd4`. Pełna
regresja wxPython: 2029 zaliczonych, 111 kontrolowanie pominiętych i 13
podtestów zaliczonych. Szczegóły promocji:
[AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md](AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md).

## Decyzja o widoku zbiorczym i nagrywaniu — 24.10.2026

Użytkownik zaakceptował `Ctrl+Shift+I` jako skrót przyszłej zbiorczej listy
transmisji trwających i zaplanowanych. Zastępuje to wcześniejsze luźne
rozważania o nieustalonym skrócie. `Ctrl+I` pozostaje skrzynką nowych
materiałów. Nowa funkcja nie jest częścią bieżącej instalacji 00:21.

Widok ma obejmować tylko kanały świadomie wybrane przez użytkownika, a nie
automatycznie wszystkie subskrypcje. Powodem jest koszt oficjalnych zapytań
API. Pierwsze uruchomienie bez wyboru powinno otworzyć dostępny selektor
kanałów. Menu kontekstowe kanału ma udostępnić jawne polecenie włączenia lub
wyłączenia go w widoku zbiorczym. Lista ma pokazywać najpierw transmisje
trwające, następnie zaplanowane chronologicznie, a każdy wiersz ma zawierać
wyłącznie użytkowe dane: kanał, tytuł, stan i czas.

Enter, `Ctrl+Shift+C`, `F5` i Backspace mają zachować kontrakt istniejącej
listy jednego kanału. `Ctrl+R` na trwającej transmisji może rozpocząć
nagrywanie teraz. `Shift+R` na trwającej albo zaplanowanej pozycji powinien
otworzyć wstępnie uzupełniony jednorazowy harmonogram, który przechowuje
stabilny adres `/live` kanału, a nie wygasający adres filmu. Cotygodniowe
audycje lepiej zapisywać jako dynamiczną stację z harmonogramem cyklicznym;
pojedyncze wydarzenia można planować bezpośrednio z przyszłej listy.

Bieżące Radio już rozróżnia `Ctrl+R` — nagranie teraz — od `Shift+R` —
harmonogram. Dynamiczna stacja jest chwilowo niedostępna, gdy kanał nie
nadaje, i rozwiązuje nowy adres przy kolejnej próbie. Kod harmonogramu ponawia
połączenie w aktywnym oknie, lecz pełny rzeczywisty scenariusz „brak live na
początku, późniejszy start, automatyczne złapanie nagrania” pozostaje do
ręcznego odbioru 24.10.2026.

Implementacja `Ctrl+Shift+I` musi w jednym zadaniu uzupełnić wspólny model
poleceń, klawiaturę, menu, menu kontekstowe, paletę `Ctrl+Shift+K`, pomoc
`Ctrl+F1`, pełną pomoc, dokumentację i testy parytetu oraz NVDA. Nie należy
zaczynać stałego monitoringu wszystkich kanałów w tle.

## Implementacja zbiorczej listy — 24.10.2026

Powyższy projekt został wdrożony w źródłach AMC Test. `Ctrl+Shift+I` jest
globalnym poleceniem `Transmisje wybranych kanałów YouTube` i jest dostępne
również w menu Widok, menu kontekstowym, palecie `Ctrl+Shift+K`, pomocy
`Ctrl+F1` i pełnej pomocy. Gdy nie wybrano jeszcze kanałów, pierwsze użycie
otwiera natywne okno `Kanały zbiorczej listy transmisji` z listą pól wyboru.
Okno zapamiętuje zaznaczenia, przy ponownym otwarciu ustawia fokus na pierwszym
zaznaczonym kanale i pozwala wybrać najwyżej 20 kanałów. Lista i komunikaty
podają wyłącznie nazwy użytkowe; identyfikatory pozostają w modelu.

Ten sam wybór można zmienić na zaznaczonym kanale przez polecenie
`Uwzględniaj kanał na zbiorczej liście transmisji`. Właściwy skan wykonuje
oficjalne zapytania kolejno, a nie równolegle. Wynik pokazuje najpierw pozycje
`na żywo`, a potem transmisje zaplanowane chronologicznie. Każdy wiersz zawiera
nazwę kanału, tytuł, stan i czas. Częściowy błąd jednego kanału nie usuwa
wyników pozostałych, lecz jest jawnie podany w komunikacie.

Polecenia widoku:

- `Enter` — odtwarzanie istniejącą drogą AMC;
- `Ctrl+Shift+C` — skopiowanie publicznego adresu;
- `F5` — wymuszone ponowne sprawdzenie wybranych kanałów;
- `Ctrl+R` — rozpoczęcie albo zatrzymanie nagrywania pozycji już trwającej;
- `Shift+R` — otwarcie edytora harmonogramu dla pozycji trwającej lub
  zaplanowanej; przyszły termin jest wstępnie uzupełniany, a użytkownik nadal
  wybiera czas trwania;
- `Backspace` albo `Escape` — powrót do dokładnego wcześniejszego widoku i
  fokusu. Spóźniony wynik po wyjściu nie otwiera listy ponownie.

Nagranie uruchamiane teraz używa dokładnego adresu bieżącego filmu. Harmonogram
przechowuje stabilny adres kanału `/live`, aby nie przywiązywać się do
wygasającego linku `watch`. Wybór kanałów jest prywatny dla profilu AMC Test i
wchodzi do pełnej kopii danych w sekcji Podcasty. Host C# pozostaje jedynym
właścicielem tokenu Google.

### Testy i stan instalacji

- celowana bramka po zsynchronizowaniu z repozytorium: **273 zaliczone testy i
  2 zaliczone podtesty**;
- pełna regresja wxPython: **2032 zaliczone, 111 kontrolowanie pominiętych i
  13 zaliczonych podtestów**, zero błędów, czas 153,04 s;
- `git diff --check`: bez błędów; ostrzeżenia dotyczyły wyłącznie normalizacji
  końców linii w trzech istniejących plikach;
- ręczny odbiór okna wyboru, mowy NVDA, prawdziwych transmisji oraz nagrywania
  pozostaje do wykonania po instalacji nowego AMC Test;
- stały monitoring w tle nie został dodany. Skan odbywa się tylko na jawne
  polecenie użytkownika i obejmuje najwyżej 20 świadomie wybranych kanałów.

### Wersja i commit

Gałąź: `integration/amc-test-20261023-late`. Commit źródłowy:
`fe281d31af2c5328f1ada1c3668a587feefbcf80` —
`feat: dodaj zbiorcze transmisje i ustabilizuj Frontier`. Zbudowano i
zainstalowano paczkę `8bce7f95` o etykiecie
`2026.10.24-fe281d31af2c5328f1ada1c3668a587feefbcf80-8bce7f95` w
`D:\Projekty Codex\AMC Python`. Potwierdzone okno:
`AMC Test — 24.10.2026, 13:33`. AMC Public i GitHub pozostają bez zmian.

## Odbiór i los zakończonych transmisji — 24.10.2026

Użytkownik potwierdził, że wybór kanałów i `Ctrl+Shift+I` działają, choć przy
pierwszym użyciu spodziewał się automatycznego przejścia z zapisu wyboru do
wyniku skanowania. Wynik pojawił się po ponownym użyciu skrótu. Do osobnego
sprawdzenia pozostaje, czy po zapisie wyboru należy od razu rozpocząć skan,
bez ponownego skrótu. Nie należy w tym celu wykonywać dwóch równoległych
odświeżeń ani zużywać ponownie limitu API.

`Ctrl+Shift+I` jest bieżącym widokiem transmisji **trwających i
zaplanowanych**, a nie archiwum. Host pyta YouTube osobno o stany `live` oraz
`upcoming`, a wynik przechowuje tylko w krótkim, pięciominutowym cache. Po
zakończeniu Teleexpressu albo programu `19:30` pozycja przestaje spełniać te
warunki i przy następnym odświeżeniu znika z widoku transmisji.

Zwykła lista materiałów kanału jest niezależna i pochodzi z publicznego kanału
Atom YouTube. Zakończona transmisja pojawi się tam tylko wtedy, gdy właściciel
kanału pozostawi ją jako publiczne archiwalne nagranie i YouTube umieści je w
tym kanale. Materiał usunięty, prywatny, niepubliczny albo niewystawiony w
kanale nie może zostać pokazany przez AMC. Bieżąca implementacja celowo nie
dopisuje wcześniej zauważonych transmisji do zwykłej listy kanału.

Nagranie zaplanowane lub wykonane przez AMC jest osobnym bytem: jego plik i
historia nagrań pozostają dostępne niezależnie od późniejszego zniknięcia
pozycji z YouTube. Harmonogram przechowuje stabilny adres `/live` kanału i przy
starcie rozwiązuje aktualną transmisję, więc nie zależy od wygasającego adresu
konkretnego filmu.

### Decyzja: bez osobnej historii transmisji — 24.10.2026

Użytkownik zdecydował, że nie należy wdrażać osobnej funkcji `Historia
zauważonych transmisji`. Ta decyzja zastępuje powyższą możliwość pozostawioną
do rozważenia. Jeśli zakończony materiał nadal istnieje publicznie, można go
odnaleźć przez wyszukiwanie albo zwykłą listę kanału udostępnianą przez
YouTube. Jeśli AMC wykonało nagranie, pozostaje ono w historii nagrań.
`Ctrl+Shift+I` nadal ma być małym, bieżącym widokiem transmisji trwających i
zaplanowanych, bez lokalnego archiwizowania znalezionych pozycji i bez nowego
polecenia, skrótu, menu ani widoku.

## Korekta: zakończone transmisje na zwykłej liście kanału — 24.10.2026

Użytkownik wskazał kanał Dominikanie Poznań, na którym codzienna Msza o 17:00
po zakończeniu pozostaje publicznym nagraniem, lecz nie była widoczna po
otwarciu kanału z Biblioteki AMC. Rzeczywista próba wykazała, że YouTube
utrzymuje osobne karty `Filmy` (`/videos`) i `Transmisje` (`/streams`). Każda
Msza ma inny adres `watch?v=…`; po zakończeniu ten sam adres konkretnej Mszy
pozostaje nagraniem ze stanem `was_live`. Stały adres kanału `/live` nadal
służy wyłącznie do odnajdywania transmisji bieżącej.

Ta korekta zastępuje wcześniejsze uproszczenie, że zwykła lista kanału pochodzi
z Atom i zakończony stream pojawi się tam automatycznie. W rzeczywistości AMC
pobierało wyłącznie kartę `/videos` przez yt-dlp, a Atom tylko poprawiał tytuły
i daty pozycji już znalezionych. Dlatego publiczne archiwa z `/streams` mogły
pozostawać niewidoczne.

### Uzasadnienie i decyzje

- istniejąca lista kanału łączy teraz zwykłe filmy i publiczne, zakończone
  transmisje; nie powstaje osobna historia ani nowy widok;
- lekki publiczny feed Atom najpierw sprawdza, czy zawiera identyfikatory
  nieobecne na karcie `Filmy`; dopiero wtedy AMC uruchamia dodatkowy odczyt
  `/streams`, więc kanały bez rozdzielonej zawartości nie płacą kosztu drugiego
  skanu;
- z karty transmisji do zwykłej listy trafiają tylko pozycje zakończone ze
  stanem `was_live`; trwające i zaplanowane nadal należą do `Ctrl+Shift+I`;
- wyniki są łączone według identyfikatora filmu, bez duplikatów, porządkowane
  po dokładnych datach z Atom i ograniczone do 100 najnowszych pozycji;
- brak albo chwilowy błąd karty `Transmisje` nie usuwa zwykłych filmów i nie
  powoduje niepowodzenia całego odświeżenia kanału.

### Materiał do dokumentacji użytkownika

Po odświeżeniu kanału YouTube w Bibliotece jego zwykła lista może zawierać
zarówno filmy, jak i dostępne publicznie nagrania wcześniejszych transmisji.
Nie trzeba otwierać dodatkowej historii. Enter, wyszukiwanie, kopiowanie,
usuwanie pojedynczego materiału i pozostałe polecenia listy działają tak samo
jak wcześniej. `Ctrl+Shift+I` nadal pokazuje tylko transmisje trwające i
zaplanowane, a dynamiczna stacja `/live` służy do odtwarzania lub nagrywania
tego, co kanał nadaje w danej chwili.

### Testy i wynik

- izolowany test `--youtube-collection-normalization`: zaliczony; obejmuje
  budowę `/streams`, odrzucanie transmisji trwających i zaplanowanych,
  wykrywanie potrzeby drugiego skanu, usuwanie duplikatów oraz ponowne
  sortowanie po uzupełnieniu dokładnych dat;
- celowane testy interfejsu wxPython dla YouTube, konta Google i komunikacji z
  hostem: 52 zaliczone; nie uruchamiano ponownie niezwiązanych testów Sonosa;
- build `AccessibleMediaController.LiteHost` w konfiguracji `Release`:
  zaliczony, 0 ostrzeżeń i 0 błędów; wszystkie 27 testów protokołu LiteHost:
  zaliczone;
- rzeczywisty kanał Dominikanie Poznań: 100 połączonych materiałów, pierwsze
  trzy pozycje to Msze z 23, 22 i 21 października 2026;
- rzeczywiste kanały Dominikanie we Wrocławiu, Dominikanie Freta i Dominikanie
  Szczecin: każdy zwrócił 100 materiałów, a zakończone Msze znalazły się na
  początku listy;
- testy były wykonane na źródłach AMC Test; na tym etapie nie zbudowano ani
  nie zainstalowano nowej paczki i nie opublikowano wydania.

### Znane ograniczenia

AMC może pokazać tylko transmisję pozostawioną przez właściciela jako
publiczne nagranie. Materiał usunięty, prywatny albo niepubliczny nie trafi do
listy. Kanał z bardzo częstymi publikacjami jest ograniczony do 100 najnowszych
pozycji po połączeniu obu kart.

### Wersja i commit

Gałąź `integration/amc-test-20261023-late`. Kod i testy: commit `921b784e`
(`fix(youtube): pokaz zakonczone transmisje w kanale`). Paczka i instalacja nie
zostały jeszcze wykonane; nie opublikowano wydania.

## Zbiorcze podsumowanie i odbiór użytkownika — 24.10.2026

Poniższy zapis scala prace z 23 i 24 października 2026. Zastępuje wcześniejsze
oznaczenie, że ręczny odbiór prawdziwych transmisji nie został wykonany.

### Zakres użytkowy

- `Ctrl+N` przyjmuje publiczny adres filmu, playlisty albo kanału, w tym
  uchwyty `@nazwa`; formularz nie gubi fokusu przy szybkim wklejeniu i nie
  uruchamia dwóch równoległych importów;
- odświeżanie zapisanych kanałów rozpoznaje różne postacie adresu i łączy
  zwykłe filmy z publicznymi, zakończonymi transmisjami z karty `/streams`;
  identyczny film nie jest powielany;
- `Ctrl+I` pozostaje skrzynką nowych materiałów z Podcastów i YouTube. Nie jest
  osobnym skanerem transmisji, ale korzysta z poprawionych danych odświeżonych
  kanałów, więc nowe publiczne archiwa mogą trafić do niej tak jak inne nowe
  materiały;
- `Ctrl+T` na jednym kanale pokazuje jego transmisje trwające i zaplanowane;
- `Ctrl+Shift+I` pokazuje wspólną listę transmisji trwających i zaplanowanych
  z maksymalnie 20 świadomie wybranych kanałów. Wybór można zmienić w menu
  Plik albo w menu kontekstowym kanału. Ponowne użycie skrótu lub `F5` podczas
  trwającego skanu nie rozpoczyna drugiego odpytywania i nie zużywa ponownie
  limitu API;
- Enter odtwarza znalezioną transmisję wewnętrznym silnikiem AMC,
  `Ctrl+Shift+C` kopiuje jej publiczny adres, `Ctrl+R` nagrywa transmisję
  trwającą, a `Shift+R` otwiera harmonogram;
- dynamiczna stacja Radia zapamiętuje stały adres kanału `/live`. Przy każdym
  odtworzeniu albo rozpoczęciu nagrania AMC rozwiązuje aktualny, zmienny adres
  filmu. Gdy kanał niczego nie nadaje, stacja jest chwilowo niedostępna bez
  utraty konfiguracji;
- zakończona transmisja znika z bieżącej listy `Ctrl+Shift+I`, lecz może
  pozostać na zwykłej liście kanału jako publiczne archiwum. Plik nagrany przez
  AMC pozostaje niezależnie w Historii nagrywania.

### Potwierdzony odbiór

Użytkownik potwierdził, że harmonogram prawidłowo rozpoznał i nagrał transmisje
`Dominikanie Poznań` oraz `Teleexpress`. Następne transmisje na 25 października
zostały odnalezione i przygotowane do nagrania. Oznacza to zaliczony ręczny
odbiór rzeczywistego wyszukiwania, stabilnego adresu `/live`, harmonogramu i
utworzenia plików nagrań. Po zainstalowaniu najnowszej paczki pozostaje ręcznie
sprawdzić wyłącznie nową korektę widoczności zakończonych transmisji na zwykłej
liście kanału.

### Kandydat do wersji publicznej

Mechanizm publicznych adresów kanału, dynamicznego radia i parsowania
zakończonych transmisji nie wymaga prywatnych danych użytkownika. Lista
transmisji z konta i wybranych kanałów wymaga natomiast poprawnie przygotowanej
konfiguracji Google OAuth. Cały zakres jest kandydatem do przyszłego
aktualizatora publicznego po domknięciu konfiguracji Google, osobnym odbiorze
profilu publicznego i jawnej decyzji o publikacji. W tym zadaniu nie zbudowano
ani nie opublikowano wersji publicznej.

### Kandydat AMC Test i wstrzymana podmiana — 24.10.2026

Z dokumentacyjnego commita
`ae843a499b5a94c63dc41d43bbe97bba5544c01b` zbudowano paczkę AMC Test
`5b3ac88c` o etykiecie
`2026.10.24-ae843a499b5a94c63dc41d43bbe97bba5544c01b-5b3ac88c`.
Paczka ma 1674 kontrolowane pliki; pełny manifest, sumy SHA-256 i kontrolowany
start interfejsu oraz hosta na odizolowanym profilu są zaliczone.

Aktualizator prawidłowo odmówił podmiany, ponieważ poprzedni AMC Test nadal
działał z `D:\Projekty Codex\AMC Python`. Zwykłe polecenie zamknięcia okna
zostało przyjęte, lecz odpowiadający proces nie zakończył się w ciągu 30
sekund. Nie użyto wymuszonego zatrzymania. Kandydat pozostaje zachowany w
`.test-output`; instalacja czeka na ręczne, czyste zamknięcie starego okna.
