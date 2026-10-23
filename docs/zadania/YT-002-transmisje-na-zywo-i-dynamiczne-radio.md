# YT-002 — transmisje YouTube na żywo i dynamiczne radio

- Status: `W trakcie — źródła, kontrakt, pełna regresja wxPython 2024/2024,
  testy .NET i build LiteHosta są zaliczone; przed zmianą na Zrobione pozostają
  instalacja AMC Test i ręczny odbiór NVDA`
- Utworzono: 23 października 2026
- Ostatnia aktualizacja: 23 października 2026
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
   - `Transmisje na żywo i zaplanowane kanału…`;
   - `Dodaj kanał jako dynamiczne radio YouTube na żywo…`.
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
- Commit źródłowy: do wpisania po bezpiecznym commicie.
- Instalacja AMC Test: jeszcze nie wykonana dla YT-002.
- GitHub i AMC Public: bez zmian.
