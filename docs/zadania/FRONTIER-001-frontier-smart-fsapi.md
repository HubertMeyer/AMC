# FRONTIER-001 — Frontier Smart przez FSAPI

Status: **W trakcie — rzeczywisty Teufel RADIO 3SIXTY łączy się i pokazuje
bieżące odtwarzanie. Stabilizacja kolejki głośności jest zainstalowana.
24.10.2026 odbiór ujawnił brak skrótu do wyboru trybu i blokadę presetów,
ponieważ AMC nie włączał nawigacji FSAPI przed pobraniem listy. Korekta
źródłowa jest przygotowywana i wymaga nowej instalacji oraz odbioru NVDA.**

**Korekta nadrzędna z 23.10.2026, późny odbiór:** AMC znalazł Teufel RADIO
3SIXTY, pokazał listę wyboru i po Enterze prawidłowo skupił pole PIN. To
zastępuje wcześniejsze przypuszczenie, że wykrywanie sprzętu nadal nie działa.
Użytkownik zatrzymał próbę, ponieważ nie wiedział, jaki kod wpisać. Oficjalna
instrukcja Teufela wyjaśnia, że jest to czterocyfrowy PIN NetRemote, nie hasło
Wi-Fi; wartość fabryczna to `1234`, a ustawienie znajduje się w radiu pod
`Ustawienia systemowe → Sieć → Ustawienia NetRemote PIN`:
<https://cdn.teufelaudio.com/products/Radio_3sixty/ECN/Teufel-Radio_3sixty_UM_V5.0_PL_web>.
Kod AMC Test zawiera teraz tę informację w komunikacie po wykryciu Teufela i w
nazwie dostępnościowej pola. Zmiana ma testy źródłowe, została zainstalowana w
pakiecie `53e3d987` i czeka na ręczne połączenie PIN-em `1234`.

**Korekta użytkownika z 23.10.2026 po odbiorze instalacji 11:24:** podczas
wyszukiwania urządzeń fokus przechodził na przycisk „Zamknij” albo „Wstecz”,
przez co interfejs sprawiał wrażenie niezmienionego. Przyczyną było wyłączenie
wszystkich kontrolek poza zamknięciem na czas skanowania; Windows przenosił
fokus na jedyny aktywny przycisk. Nowa korekta utrzymuje fokus na nazwanym
przycisku „Wyszukiwanie urządzeń, czekaj”, a ponowne naciśnięcie tylko oznajmia,
że wyszukiwanie już trwa. Początkowy przepływ również zaczyna się na tym
przycisku, a nie na pustej liście. Kod, pełna regresja, budowa i instalacja są
gotowe w AMC Test `23.10.2026, 12:56`; uruchomiona paczka ma rewizję
`65b11661` i identyfikator `94b08d59`. Szczegóły:
[AMC-TEST-2026-10-23-1256-korekta-spotify-youtube-frontier.md](AMC-TEST-2026-10-23-1256-korekta-spotify-youtube-frontier.md).
AMC Public pozostaje bez zmian.

Wejście do pola PIN po wybraniu rzeczywiście rozpoznanego urządzenia jest
zamierzonym następnym krokiem. W bieżącej próbie sieciowej urządzenie nie było
dostępne: host zwrócił 0 urządzeń w 5,04 s. Nie jest to dowód działania ani
awarii ścieżki sprzętowej, dlatego nadal wymaga ona ręcznego odbioru z Teufelem.

Data rozpoczęcia: 2026-10-21

## Polecenie użytkownika i źródła

Użytkownik chce w istniejącym Menedżerze sesji pod `Ctrl+Shift+S` włączyć nową
sesję „Frontier Smart”, skonfigurować lub wykryć własne urządzenie, a następnie
sprawdzić rzeczywiste możliwości sterowania. Presety i pozostałe funkcje mają
korzystać ze wspólnych wzorców AMC i WiiM tam, gdzie FSAPI rzeczywiście je
udostępnia.

Materiały wskazane przez użytkownika:

- dokumentacja FSAPI: <https://github.com/flammy/fsapi/blob/master/FSAPI.md>;
- znane obrazy firmware: <https://github.com/cweiske/frontier-silicon-firmwares/>;
- narzędzia i analiza firmware:
  <https://github.com/MatrixEditor/fsapi-tools> oraz
  <https://matrixeditor.github.io/fsapi-tools/firmware-analysis.html>.

## Zakres bieżącego etapu

- nowa sesja dostępna początkowo tylko w profilu AMC Test;
- włączenie, wyłączenie, kolejność i konfiguracja przez istniejący Menedżer
  sesji, bez drugiego konkurencyjnego kreatora;
- wykrywanie SSDP oraz ręczne podanie lokalnego adresu IP;
- weryfikacja PIN-u przez rzeczywisty odczyt urządzenia; PIN poza `state.json`,
  osobno dla profilu wydania w Menedżerze poświadczeń Windows;
- zapis nazwy, adresu, wersji firmware i wybranego urządzenia;
- odczyt stanu, odtwarzanie/pauza, poprzedni/następny, głośność i wyciszenie;
- dostępne tryby i presety pobierane z urządzenia, bez założenia stałej listy;
- wspólny model nazw, menu, pomocy, palety i wykonania poleceń;
- automatyczne testy protokołu, zapisu i powierzchni poleceń oraz ręczny odbiór
  klawiaturą i NVDA na urządzeniu użytkownika.

## Zachowanie użytkowe i komunikaty czytnika

- Menedżer sesji pokazuje celową nazwę „Frontier Smart”, stan włączenia i
  lokalnie znaną gotowość. Pierwsze włączenie sesji Spacją zamyka Menedżer
  sesji, przechodzi do konfiguracji i od razu rozpoczyna wykrywanie urządzeń.
- „Konfiguruj…” oraz `Ctrl+F5` otwierają okno „Urządzenia Frontier Smart”. Gdy
  lista jest pusta, pierwsze otwarcie automatycznie rozpoczyna wykrywanie. Po
  zapisaniu urządzenia kolejne otwarcia od razu pokazują listę i nie skanują
  sieci; nowe wyszukiwanie uruchamia osobny przycisk „Szukaj nowych urządzeń”.
  Lista, pola i przyciski mają jawne nazwy użytkowe; obiekty, enumy i
  identyfikatory nie są tekstem dostępnościowym.
- Pole PIN jest chronione. Zwykłe listy i komunikaty nie pokazują PIN-u ani
  pełnych adresów żądań FSAPI.
- Ręczny adres jest schowany pod osobnym przyciskiem „Wpisz adres ręcznie…” i
  pozostaje opcją awaryjną, gdy SSDP jest blokowane przez sieć.
- Po wykryciu jednego urządzenia fokus przechodzi do chronionego pola PIN.
  Brak urządzeń lub błąd jest odczytywany przez NVDA i prowadzi do ponownego
  wyszukania albo jawnego ręcznego adresu, a nie do nieopisanej pętli pól.
- Po potwierdzonym połączeniu okno konfiguracji zamyka się i wraca do listy
  urządzeń. Anulowanie, błąd i ponowne otwarcie zachowują przewidywalny fokus.

## Korekta po pierwszym odbiorze — 21.10.2026

Ta decyzja zastąpiła pierwszą wersję zadania, według której każde skanowanie
miało rozpoczynać się dopiero po osobnym poleceniu. Pierwsze włączenie pustej
sesji ma od razu szukać urządzeń, a ręczny adres ma być dopiero opcją awaryjną.
Późniejsza korekta dotycząca ponownego otwarcia `Ctrl+F5` jest zapisana poniżej
i ma pierwszeństwo przed wcześniejszym, zbyt szerokim opisem automatycznego
skanowania.

Rzeczywisty pomiar sieci wykazał, że Teufel RADIO 3SIXTY reklamuje usługę
`urn:schemas-frontier-silicon-com:undok:fsapi:1`, podczas gdy pierwsza wersja
AMC pytała wyłącznie o starsze `fs_reference:fsapi:1`. AMC wysyła teraz dwie
krótkie serie zapytań dla obu wariantów i czeka pięć sekund. Nie skanuje całej
podsieci i nadal odrzuca niezwiązane renderery UPnP.

Drugą przyczyną pozornej pętli był firmware radia, który odrzuca duże
`GET_MULTIPLE` kodem HTTP 400 i może zamknąć połączenie przy zbyt szybkiej
serii pojedynczych odczytów. Klient przechodzi teraz na pojedyncze `GET`, robi
krótkie przerwy i jednokrotnie ponawia przejściowy błąd połączenia. Błędny PIN
i brak radia mają osobne komunikaty i odmienny powrót fokusu.

## Korekta ponownego otwarcia listy — 21.10.2026

Ta decyzja zastępuje wcześniejsze ustalenie z tego samego dnia, że `Ctrl+F5`
ma automatycznie skanować sieć przy każdym otwarciu. Wzorzec jest teraz zgodny
z WiiM, Sonosem i Folderami Biblioteki:

- pierwsze włączenie sesji bez zapisanego urządzenia automatycznie skanuje;
- `Ctrl+F5` przy pustej liście również pomaga znaleźć pierwsze urządzenie;
- po zapisaniu co najmniej jednego urządzenia `Ctrl+F5` natychmiast pokazuje
  listę zapisanych urządzeń, skupia ją i nie wykonuje skanowania sieci;
- późniejsze dodanie urządzenia jest jawną czynnością pod przyciskiem „Szukaj
  nowych urządzeń”; ręczny adres pozostaje osobną opcją awaryjną;
- po usunięciu wszystkich urządzeń sesja znów jest nieskonfigurowana, więc jej
  następne otwarcie może automatycznie wyszukać pierwsze urządzenie.

Opis `Ctrl+F5` w menu, pomocy kontekstowej, pełnej pomocy i palecie brzmi:
„Pokaż zapisane urządzenia Frontier Smart i opcjonalnie wyszukaj nowe”.

## Drugi odbiór NVDA i punkt wznowienia — 21.10.2026

Użytkownik sprawdził świeżą, nadal pustą sesję w zainstalowanym AMC Test:

- wejście bezpośrednim skrótem sesji nie otworzyło konfiguracji; dopiero
  `Ctrl+F5` otworzył okno urządzeń. Nie jest to obecnie priorytet, ale
  obserwacja pozostaje zapisana do porównania z pierwszym włączeniem przez
  Menedżer sesji;
- podczas automatycznego skanowania fokus trafił na „Anuluj”/„Zamknij”. Jest to
  błąd dostępności: użytkownik powinien otrzymać jednoznaczny stan wykrywania,
  a fokus nie może sugerować, że jedyną dostępną czynnością jest anulowanie;
- po krótkiej chwili fokus przeszedł do pola PIN, natomiast lista zapisanych
  urządzeń nadal była pusta. W obecnej implementacji taki przebieg następuje
  tylko po otrzymaniu co najmniej jednego wyniku wykrywania; przy zerowym
  wyniku fokus trafia na „Wpisz adres ręcznie”. Jest to więc silna przesłanka,
  że Teufel RADIO 3SIXTY został wykryty, lecz nie był jeszcze uwierzytelniony
  PIN-em i zapisany w AMC;
- rozdzielenie listy zapisanych urządzeń od chwilowego wyniku wykrywania jest
  technicznie poprawne, ale użytkowo niejasne. Następna korekta ma wyraźnie
  ogłosić nazwę wykrytego urządzenia, wyjaśnić, że wpisanie PIN-u kończy jego
  dodawanie, oraz zachować przewidywalny fokus;
- różne pasma Wi-Fi 2,4 GHz i 5 GHz przy tym samym SSID mogą wymagać kontroli
  izolacji klientów i multicastu w routerze, ale opisane przejście do PIN-u nie
  wygląda jak całkowity brak wykrycia. Nie należy przedwcześnie przypisywać
  problemu pasmom sieci bez ponownego pomiaru.

Nie wprowadzono kolejnej poprawki kodu podczas tego odbioru. Prace mają zostać
wznowione w tygodniu rozpoczynającym się 28.10.2026 od odtworzenia dokładnego
przebiegu, korekty fokusu w czasie skanowania i jednoznacznego komunikatu po
wykryciu urządzenia.

## Trzeci odbiór NVDA i korekta nadrzędna — 22.10.2026

Użytkownik sprawdził zainstalowane `AMC Test — 22.10.2026, 22:48` z rewizji
`6ce22410`. Wejście skrótem `Ctrl+8` nadal tylko pokazywało pustą sesję. Trzeba
było użyć `Ctrl+F5`, a następnie przejść do wykrywania. Podczas pracy fokus
znajdował się w okolicy przycisku „Zamknij”, a dopiero dalsza nawigacja
prowadziła do pola PIN. Ta obserwacja zastępuje wcześniejsze przypuszczenie,
że sam istniejący kod automatycznego wykrywania zapewnia poprawny przebieg.

Przyczyna została potwierdzona w kodzie wxPython:

- `Ctrl+8` wczytywał pustą listę urządzeń, ale nie przechodził do pierwszej
  konfiguracji;
- dialog pustej sesji ustawiał początkowy fokus na „Zamknij”, po czym osobno
  planował automatyczne wykrywanie;
- pole PIN było widoczne jeszcze przed wyborem wykrytego urządzenia, a jego
  nazwa dostępnościowa nie wskazywała, którego radia dotyczy.

Poprawka źródłowa z 22.10.2026 wprowadza następujący kontrakt:

- `Ctrl+8` przy pustej sesji otwiera pierwszą konfigurację i samoczynnie
  rozpoczyna wykrywanie; użytkownik nie musi wcześniej naciskać `Ctrl+F5` ani
  przycisku wyszukiwania;
- podczas wykrywania fokus pozostaje na jednoznacznie nazwanej liście
  „Zapisane urządzenia Frontier Smart”, a NVDA ogłasza „Wykrywanie urządzeń w
  sieci lokalnej”; fokus nie trafia na „Zamknij”;
- po wykryciu jednego radia AMC ogłasza „Wykryto urządzenie [nazwa]. Wpisz jego
  PIN, a następnie wybierz Połącz i zapisz”, pokazuje dopiero wtedy pole PIN i
  ustawia na nim fokus;
- nazwa dostępnościowa pola zawiera użytkową nazwę radia, na przykład „PIN
  urządzenia Teufel RADIO 3SIXTY, pole chronione”, ale nie adres IP ani
  identyfikator techniczny;
- `Tab` z pola PIN prowadzi do „Połącz i zapisz”;
- ponowne wejście do sesji z zapisanym urządzeniem skupia listę i nie uruchamia
  wykrywania. `Ctrl+F5` zachowuje rolę zarządzania istniejącą konfiguracją.

### Testy i wynik korekty z 22.10.2026

- przed zmianą: `wxlite/tests/test_frontier_smart_session.py` — **8/8
  zaliczonych**, co potwierdziło, że dotychczasowe testy nie odtwarzały błędu
  zgłoszonego przez użytkownika;
- po zmianie: ten sam moduł — **12/12 zaliczonych**; nowe testy obejmują
  wejście do pustej sesji, automatyczne wykrywanie bez fokusu na zamknięciu,
  nazwę i fokus pola PIN oraz ponowne otwarcie zapisanej listy bez skanowania;
- regresja powierzchni poleceń, Menedżera sesji, skrótów, menu, pomocy i palety
  — **116/116 zaliczonych**;
- sprawdzono w przypiętym środowisku wxPython 4.3.1, że użyte zdarzenie
  inicjalizacji dialogu i sterowanie kolejnością `Tab` są dostępne;
- dodatkowy, szerszy przebieg zatrzymał się na zastanym teście zapisu opcji
  sesji (`test_zapisz_wykonuje_pelny_pion_az_do_profilu`): 11 wcześniejszych
  testów w tym module przeszło, a awaria dotyczyła braku wywołania klienta
  opcji sesji i nie przecina zmienionych miejsc Frontier Smart. Nie jest to
  dowód pełnej regresji.

### Wersja, instalacja i publikacja korekty z 22.10.2026

Zmiana jest zapisana w repozytorium
`D:\Projekty Codex\AMC - integracja wxPython` w commicie `3ce574a6` —
`fix(frontier): popraw pierwsze wykrywanie urządzenia`. Historycznie po tym
commicie nie było jeszcze nowej paczki. Zbiorcza promocja 2026-10-23 z czystej
rewizji `c4a4c214e7e5bdc05fddc02c1dc644806d94490e` zainstalowała poprawkę w
`D:\Projekty Codex\AMC Python`. Nie zbudowano ani nie zainstalowano AMC Public.

### Materiał do dokumentacji użytkownika — projekt

Przy pierwszym wejściu do włączonej sesji Frontier Smart skrótem `Ctrl+8` AMC
sam wyszukuje radio w sieci lokalnej. W czasie wyszukiwania można czekać bez
przechodzenia po przyciskach. Po znalezieniu radia NVDA podaje jego nazwę i
ustawia fokus w chronionym polu PIN. Po wpisaniu PIN-u należy nacisnąć `Tab`,
wybrać „Połącz i zapisz” i zatwierdzić. Późniejsze `Ctrl+F5` pokazuje zapisane
urządzenia; nowego skanowania używa się tylko przez osobny przycisk „Szukaj
nowych urządzeń”.

### Projekt listy zmian

- Pusta sesja Frontier Smart rozpoczyna pierwszą konfigurację już po `Ctrl+8`.
- Fokus podczas wykrywania nie trafia na przycisk zamknięcia.
- Po znalezieniu radia AMC podaje jego nazwę, wyjaśnia czynność z PIN-em i
  ustawia fokus na właściwym polu.
- Zapisane urządzenia otwierają się ponownie bez automatycznego skanowania.

## Czwarte zgłoszenie użytkownika i korekta nadrzędna — 23.10.2026

Użytkownik jednoznacznie odrzucił przebieg, w którym `Ctrl+8` i `Ctrl+F5`
prowadziły różnymi drogami, a pole PIN pojawiało się po samym odebraniu pakietu
SSDP. Ta decyzja zastępuje wcześniejsze założenie, że obecność adresu
`LOCATION` oznacza już wykrycie konkretnego radia. Zainstalowana korekta z
22.10.2026 nie została uznana za zakończoną.

### Przyczyna i decyzje

- LiteHost uznawał dowolną odpowiedź SSDP z nagłówkiem `LOCATION` za urządzenie
  i sam tworzył etykietę z adresem IP, bez pobrania opisu `/device` i bez
  potwierdzenia użytkowej nazwy radia.
- Parser akceptował odpowiedź bez nagłówka `ST`, więc niezwiązana usługa mogła
  zostać potraktowana jak Frontier Smart.
- Interfejs przechodził z chwilowego wyniku prosto do pola PIN. Ręczny adres
  również pokazywał PIN przed identyfikacją urządzenia.
- `Ctrl+F5` mógł najpierw uruchomić automatyczną konfigurację z przełączenia
  sesji, a następnie otworzyć zarządzanie jeszcze raz. Powstawały dwie
  konkurujące ścieżki zamiast jednego modelu stanu.

Nowy kontrakt jest wspólny dla `Ctrl+8`, `Ctrl+F5` i ręcznego adresu:

- skanowanie wysyła zapytania dla obu używanych usług,
  `fs_reference:fsapi:1` oraz `undok:fsapi:1`, na wszystkich aktywnych
  interfejsach IPv4;
- wynik SSDP musi mieć zgodny nagłówek `ST`, a wskazany opis XML musi zawierać
  `netRemote`, użytkową `friendlyName` i lokalny adres `webfsapi` na tym samym
  hoście; dopiero taki wynik jest konkretnym urządzeniem;
- adres IP pozostaje wartością modelu. NVDA otrzymuje wyłącznie nazwę radia;
- stany `pusto`, `zapisane urządzenia`, `wykrywanie`, `wyniki`, `brak wyników`,
  `błąd`, `ręczny adres`, `identyfikowanie` i `oczekiwanie na PIN` są jawne i
  przechodzą przez jeden model konfiguracji;
- pole PIN istnieje w przebiegu dopiero po potwierdzeniu konkretnego urządzenia
  i jego użytkowej nazwy. Ręczny adres najpierw wykonuje bezpinową identyfikację
  `/device`;
- brak wyniku lub błąd nie pokazuje PIN-u. Komunikat prowadzi do ponownego
  wyszukania albo ręcznego adresu, a fokus trafia na działającą czynność;
- błąd jednego interfejsu sieciowego nie przekreśla wyników z pozostałych.
  Wspólny limit czasu, anulowanie użytkownika i ponowne otwarcie są rozróżnione;
- `Ctrl+8` przy pustej sesji otwiera jeden przebieg pierwszej konfiguracji.
  `Ctrl+F5` otwiera jeden przebieg zarządzania: przy pustej liście może szukać,
  a przy zapisanym urządzeniu pokazuje listę bez automatycznego skanowania.

### Testy i rzeczywiste wyniki korekty z 23.10.2026

- `wxlite/tests/test_frontier_smart_session.py` oraz testy klienta hosta:
  **16/16 zaliczonych**. Fikcyjne odpowiedzi obejmują osobne stany, pusty
  wynik, błąd i fokus, ręczną identyfikację przed PIN-em, `Ctrl+8`, pojedynczy
  przebieg `Ctrl+F5`, zapisane urządzenie i odrzucenie starej etykiety z IP.
- Izolowany `wxlite/tests/test_gui_logic.py`: **36/36 zaliczonych**.
- Izolowana regresja sesji, palety, menu, kolejności, skrótów, profili i haka
  klawiatury odtwarzacza: **156/156 zaliczonych**.
- Łączny przebieg dwóch grup wxPython w jednym procesie dał **178 zaliczonych
  i 14 błędów**. Błędy wynikały z kolejności importu: prawdziwy moduł `wx`
  został załadowany przed atrapą używaną przez `test_gui_logic.py`. Obie grupy
  uruchomione we właściwej izolacji przeszły; wynik 178/14 nie jest
  przedstawiany jako zaliczona pełna regresja.
- Ukierunkowany zestaw kontraktu Frontier Smart LiteHost: **1/1 zaliczony**.
  Pełny projekt testów protokołu LiteHost: **27/27 zestawów zaliczonych**.
  Obejmuje dwa warianty `ST`, brak `ST`, bezpieczny opis urządzenia, odrzucenie
  DTD i obcego hosta `webfsapi`, kilka interfejsów, częściowy błąd, limit czasu
  oraz zewnętrzne anulowanie.
- Kompilacja Release `AccessibleMediaController.LiteHost` z lokalnego źródła
  NuGet zakończyła się z **0 ostrzeżeń i 0 błędów**. Pierwsza próba
  `--no-restore` nie była testem kodu: zatrzymała się na braku
  `obj\project.assets.json`; po odtworzeniu zależności offline kompilacja
  przeszła.

Nie wykonywano skanowania żywej sieci, nie używano prawdziwego PIN-u, nie
uruchamiano AMC, nie instalowano ani nie pakowano AMC Test lub AMC Public i nie
publikowano niczego w GitHubie. Testy sieciowe korzystały wyłącznie z atrap.

### Materiał do dokumentacji użytkownika — projekt

Przy pierwszym wejściu do pustej sesji skrótem `Ctrl+8` AMC wyszukuje radio.
Pole PIN pojawia się dopiero wtedy, gdy AMC potwierdzi opis urządzenia i poda
jego zwykłą nazwę, na przykład „Teufel RADIO 3SIXTY”. Sam adres sieciowy nie
jest urządzeniem i nie jest czytany jako jego nazwa. Jeśli nic nie znaleziono
albo wystąpił błąd, AMC nie pyta o PIN: pozwala ponowić wyszukiwanie lub
sprawdzić ręcznie wpisany adres. `Ctrl+F5` używa tego samego przebiegu, a po
zapisaniu radia otwiera jego listę bez nowego skanowania.

### Projekt listy zmian

- Weryfikacja opisu radia przed pokazaniem pola PIN.
- Obsługa obu wariantów SSDP Frontier Smart/UNDOK na wielu interfejsach.
- Jeden jawny model stanów dla `Ctrl+8`, `Ctrl+F5` i ręcznego adresu.
- Jednoznaczne komunikaty i fokus dla wykrywania, braku wyniku i błędu.
- Adres IP pozostaje poza zwykłą nazwą czytaną przez NVDA.

### Plan odbioru sprzętowego — 24.10.2026

Na rzeczywistym Teufel RADIO 3SIXTY z NVDA trzeba sprawdzić:

1. `Ctrl+8` w pustej sesji rozpoczyna wykrywanie, a fokus pozostaje na
   sensownej kontrolce.
2. Brak wyniku pokazuje komunikat i fokus na ponowieniu lub ręcznym adresie,
   bez pola PIN.
3. Wykrycie Teufela ogłasza dokładną nazwę użytkową i dopiero potem pokazuje
   chronione pole PIN.
4. `Ctrl+F5` przy pustej konfiguracji korzysta z tego samego modelu, a przy
   zapisanym urządzeniu skupia listę bez skanowania.
5. Anulowanie, zamknięcie, powrót fokusu i ponowne otwarcie są przewidywalne.

Do czasu tego odbioru nie ma potwierdzenia, że nowy przebieg działa z
rzeczywistym radiem i bieżącą konfiguracją sieciową użytkownika.

### Wersja i commit korekty z 23.10.2026

Zmiana źródłowa i testy są w commicie
`b11fd8bbc2de6a8f23746e5f2ec437b021f86762` —
`fix(frontier): potwierdzaj radio przed pytaniem o PIN`. Commit nie został
zainstalowany, uruchomiony, spakowany ani opublikowany.

## Różnice względem WiiM

- Frontier Smart używa lokalnego XML FSAPI i PIN-u, a WiiM własnego protokołu
  HTTP bez PIN-u.
- Lista trybów oraz lista presetów pochodzą z urządzenia i mogą różnić się
  pomiędzy firmware. AMC nie reklamuje trybu albo presetu, którego urządzenie
  nie zwróciło.
- Nie jest tworzona sesja powiadomień FSAPI (`CREATE_SESSION`), aby nie
  unieważniać połączenia aplikacji UNDOK/SmartRadio. Stan jest odczytywany
  krótkimi żądaniami z PIN-em.

## Uzasadnienie i bezpieczeństwo

- `GET_MULTIPLE` jest używane dla migawki, z bezpiecznym powrotem do
  pojedynczych `GET` w starszym firmware.
- Klient przyjmuje wyłącznie lokalne adresy IP, nie podąża za przekierowaniami,
  ogranicza czas i rozmiar odpowiedzi oraz bezpiecznie parsuje XML bez DTD.
- Wydanie publiczne pozostaje bez tej sesji do czasu odbioru na prawdziwym
  urządzeniu i osobnej decyzji o publikacji.

## Zmienione miejsca

- `src/AccessibleMediaController.Core/Devices/FrontierSmart/` — ograniczony do
  sieci lokalnej klient FSAPI, bezpieczny parser XML, wykrywanie SSDP oraz
  modele migawki, trybów i presetów;
- `src/AccessibleMediaController.Core/Configuration/` — opcjonalny, zgodny
  wstecz zapis urządzeń Frontier i bieżącego wyboru;
- `src/AccessibleMediaController.LiteHost/` — koordynator urządzeń, magazyn
  PIN-u w Menedżerze poświadczeń Windows oraz wąskie operacje hosta;
- `src/Shared/ReleaseProfileContract.cs` i
  `wxlite/amc_wx_lite/release_profile.py` — możliwość dostępna wyłącznie w
  profilu AMC Test;
- `wxlite/amc_wx_lite/frontier_smart_source.py`, `host_client.py`, `gui.py`,
  `navigation.py`, `session_order.py` — sesja, konfiguracja, lista urządzeń,
  odtwarzacz, tryby i presety;
- `wxlite/amc_wx_lite/shortcuts.py`, `menu_model.py`, `search_catalog.py`,
  `search_sources.py`, `session_options.py` — wspólna powierzchnia poleceń,
  pomocy, palety i nazw;
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/` oraz
  `wxlite/tests/test_frontier_smart_session.py` — kontrakt protokołu,
  bezpieczeństwa, profilu, nazw dostępnościowych i klawiatury.

## Testy i rzeczywiste wyniki

- 21.10.2026: kompilacja `AccessibleMediaController.LiteHost` w konfiguracji
  Release przeszła z **0 ostrzeżeń i 0 błędów**.
- 21.10.2026: pełne **25/25 zestawów testów protokołu LiteHost** przeszło,
  w tym walidacja lokalnych adresów, odrzucanie XML z DTD, jawne etykiety
  trybów/presetów oraz brak adresu i technicznych reprezentacji w danych
  czytanych przez NVDA.
- 21.10.2026: ukierunkowana bramka Python przeszła **72/72 testy**.
- 21.10.2026: pierwsza pełna bramka Python przeszła **1926 testów**, **110 testów
  środowiskowych celowo pominięto**, a **11 podtestów** również przeszło.
- Pierwsza promocja kandydata z rewizji `c3258214` ponownie zaliczyła pełną
  bramkę Python i odizolowany start paczki `1debd5a9`, po czym zatrzymała się
  bez podmiany stałej instalacji: starszy manifest AMC Test nie znał jeszcze
  sesji Frontier Smart, a updater wymagał identycznej listy sesji.
- Walidator migracji nadal wymaga dokładnie tej samej tożsamości, kanału,
  katalogów i przestrzeni poświadczeń, lecz przyjmuje starszy podzbiór znanych
  sesji i możliwości niezależnie od ich dawnej kolejności. Nieznana sesja lub
  możliwość nadal powoduje odmowę. Nowy kontrakt przeszedł **29/29 testów
  launchera i updatera** oraz **52/52 ukierunkowane testy profili i pakowania**.
  Testy launchera/updatera są od tej pory obowiązkową bramką skryptu promocji.
- Końcowa bramka przed instalacją przeszła **29/29 testów
  launchera/updatera**, **1927 testów Python**, **110 celowo pominiętych
  testów środowiskowych** i **11 podtestów**; kompilacje .NET ponownie miały
  0 ostrzeżeń i 0 błędów.
- Kandydat `82d28f84` przeszedł pełną kontrolę 1669 plików i odizolowany start.
  Updater zakończył się kodem 0, pełna kontrola stałej instalacji kodem 0, a
  kontrolowany start interfejsu i hosta z `D:\Projekty Codex\AMC Python`
  również wynikiem OK.
- Uruchomiono widoczne okno `AMC Test — 21.10.2026, 14:35`; potwierdzony proces
  interfejsu to `D:\Projekty Codex\AMC Python\runtime\python.exe`.
- 21.10.2026 po pierwszym odbiorze ręczna sonda SSDP na dwóch aktywnych
  interfejsach wykryła radio pod wariantem `undok:fsapi`. Poprawiony,
  rzeczywisty LiteHost AMC wykrył jedno urządzenie, a pełny odczyt FSAPI z
  właściwym PIN-em zwrócił nazwę „Teufel RADIO 3SIXTY”, wersję firmware i
  bieżący stan. Próba zapisu odbyła się w odizolowanym profilu diagnostycznym;
  po teście urządzenie i tymczasowe poświadczenie zostały usunięte, co
  potwierdzono osobnym odczytem.
- Ukierunkowana regresja po korekcie: **13/13 testów Python** oraz **1/1 zestaw
  kontraktu Frontier Smart**. Kompilacja LiteHost przeszła z **0 ostrzeżeń i
  0 błędów**.
- Pełna promocja z czystego worktree commitu `19ae6089` przeszła **29/29
  testów launchera i aktualizatora**, **1956 testów Python**, **110 celowo
  pominiętych testów środowiskowych** i **11 podtestów**. Kandydat obejmuje
  1670 plików; integralność i kontrolowany start interfejsu oraz hosta przeszły
  przed i po atomowej instalacji.
- Zainstalowano i uruchomiono AMC Test z kompilacji
  `2026.10.21-19ae6089b6cb24ea102273d37cb00f8eb86b1c38-e894430c`.
  Dodatkowy odczyt przez dokładnie zainstalowany runtime i LiteHost wykrył w
  bieżącej sieci jedno urządzenie Frontier Smart pod prawidłowym adresem.
- Ukierunkowana regresja korekty ponownego otwarcia listy zaliczyła **99/99
  testów**. Obejmuje pustą i niepustą listę, celową nazwę przycisku, wykonanie
  `Ctrl+F5`, menu, pomoc kontekstową, pełną pomoc oraz paletę poleceń.
- Pełna promocja z czystego worktree commitu `86727573` przeszła **29/29
  testów launchera i aktualizatora**, **1963 testy Python**, **110 celowo
  pominiętych testów środowiskowych** i **11 podtestów**. Kompilacje .NET
  zakończyły się z 0 ostrzeżeń i 0 błędów. Kandydat oraz stała instalacja po
  atomowej podmianie zaliczyły integralność i kontrolowany start interfejsu
  oraz hosta.
- Zainstalowano AMC Test z kompilacji
  `2026.10.21-8672757327c7bc5ae1995e47753f3976f2399600-e97b3868`.
  Manifest stałej instalacji potwierdza commit `86727573`, pakiet `e97b3868`
  i 1670 plików. Kontrola instalatora potwierdziła okno „AMC Test —
  21.10.2026, 21:29” oraz właściwy runtime ze stałego katalogu instalacji.
- Zbiorcza promocja korekty z commitu `3ce574a6` 2026-10-23 przeszła
  **30/30 testów launchera i aktualizatora**, pełną regresję Pythona
  **1983 zaliczone, 111 pominiętych i 11 podtestów zaliczonych** oraz
  kompilacje Release bez ostrzeżeń i błędów. Kandydat i stała instalacja
  zaliczyły pełną integralność i kontrolowany start. Zainstalowano kompilację
  `2026.10.23-c4a4c214e7e5bdc05fddc02c1dc644806d94490e-7353e273`,
  1670 plików; uruchomione okno ma tytuł „AMC Test — 23.10.2026, 00:16”.
- Późniejszy `HEAD` `1badabbe` zmieniał wyłącznie dokumentację. Ponowna
  promocja zbudowała trzy składniki Release, zachowała identyczne sumy plików
  wykonywalnych i ponownie zaliczyła pełną integralność oraz kontrolowany start
  przed i po instalacji. Niezmienionych testów nie uruchamiano drugi raz.

## Znane ograniczenia i dalszy odbiór

- Połączenie, nazwa, firmware i bieżący stan zostały potwierdzone na prawdziwym
  Teufel RADIO 3SIXTY. Nawigacja całej sesji, tryby, presety oraz mowa i fokus
  nadal wymagają ręcznego odbioru użytkownika z NVDA w zainstalowanym AMC Test.
- Wykrywanie SSDP zależy od multicastu w lokalnej sieci; ręczny adres jest
  obowiązkowym obejściem.
- Dokładne węzły wspierane przez konkretny firmware zostaną potwierdzone dopiero
  po pierwszym połączeniu.
- Bieżący etap nie dodaje nagrywania, historii odtwarzania ani przewijania
  urządzenia. Polecenia, których sesja nie obsługuje, są ukryte w jej menu i
  pomocy albo odmawiane z komunikatem zamiast wysyłania przypadkowego żądania.
- Ręczny odbiór obejmie `Ctrl+Shift+S`, pierwsze włączenie i konfigurację,
  automatyczne wykrywanie pustej sesji, `Ctrl+F5` bez ponownego skanowania po
  zapisaniu urządzenia, przycisk „Szukaj nowych urządzeń”, ręczny adres, błędny
  i prawidłowy PIN, Enter oraz dwuklik na liście urządzeń, powrót fokusu po
  Zamknij, ponowne otwarcie, odtwarzanie, głośność, wyciszenie, tryby i presety
  z NVDA.
- Drugi i trzeci odbiór ujawniły, że podczas skanowania pustej sesji fokus
  trafiał na przycisk zamknięcia, a wykryty, lecz jeszcze niezapisany wynik
  nie był dostatecznie odróżniony od pustej listy zapisanych urządzeń.
  Zainstalowana wtedy poprawka nie wystarczyła. Zastępuje ją nieinstalowana
  korekta źródłowa `b11fd8bb`, wymagająca odbioru sprzętowego 24.10.2026.

## Piąty odbiór i korekta wyboru urządzenia — 23.10.2026

Użytkownik potwierdził, że automatyczne i ręczne wyszukiwanie rzeczywiście
znajduje urządzenie, lecz po zakończeniu oba warianty nadal przenoszą fokus do
pola PIN. Przyczyną nie jest teraz SSDP ani fałszywy wynik. Metoda
`use_discovered` miała celową gałąź: przy dokładnie jednym potwierdzonym
urządzeniu pomijała okno wyboru i od razu wywoływała etap PIN; listę wyboru
pokazywała dopiero dla co najmniej dwóch urządzeń.

Decyzja użytkowa zastępująca wcześniejszy kontrakt: każde udane wyszukiwanie,
także z jednym wynikiem, pokazuje listę `Wykryte urządzenia Frontier Smart`.
Pierwszy wynik jest zaznaczony. Enter lub OK świadomie wybiera radio i dopiero
wtedy ujawnia oraz skupia pole PIN. Escape anuluje wybór, pozostawia PIN ukryty
i zwraca fokus do `Szukaj nowych urządzeń`.

Poprawka jest w commicie
`3e57b68656ee06c1742a3775bac3d810f792646f`. Dwa nowe testy wykonują oba
warianty dla pojedynczego wyniku: anulowanie bez PIN-u oraz zatwierdzenie
przechodzące do następnego kroku. Łącznie z testami nazw, komunikatów i pustego
wyniku ukierunkowana bramka Python przeszła. Zestaw protokołu Frontier Smart
również przeszedł podczas kompilacji LiteHosta. Rzeczywisty odbiór NVDA i
Teufela wymaga nowej instalacji AMC Test; AMC Public pozostaje bez tej sesji.

## Szósty audyt bezpieczeństwa PIN-u — 23.10.2026

PIN wymagany przez AMC jest PIN-em NetRemote do lokalnych poleceń FSAPI/UNDOK,
a nie hasłem Wi-Fi ani kodem konta. Dla Teufel RADIO 3SIXTY wartość fabryczna
to `1234`; można ją sprawdzić lub zmienić w radiu w `Ustawienia systemowe →
Sieć → Ustawienia NetRemote PIN`. Po poprawnym sprawdzeniu AMC przechowuje PIN
wyłącznie w Menedżerze poświadczeń Windows, w przestrzeni oddzielonej dla AMC
Test. Zwykła lista urządzeń ani komunikaty NVDA nie ujawniają PIN-u i adresu.

Audyt wykrył jedną usterkę usuwania urządzenia: wynik `CredDelete` był
ignorowany, więc przy odmowie Windows interfejs mógł niesłusznie ogłosić
usunięcie, pozostawiając poświadczenie. Commit `9e8d3eab` usuwa najpierw PIN,
toleruje wyłącznie stan „poświadczenia już nie ma”, a każdy inny błąd Windows
przerywa operację bez usunięcia urządzenia z profilu i bez komunikatu sukcesu.

Ukierunkowany zestaw kontraktu Frontier Smart przeszedł **1/1**. Kompilacja
LiteHost Release przeszła z **0 ostrzeżeń i 0 błędów**. Jest to na razie
zweryfikowana zmiana źródłowa. Późniejsza promocja tego samego dnia zbudowała
i atomowo zainstalowała dokładny commit `9e8d3eab` jako AMC Test 22:41;
kontrolowany start został zaliczony. Ręczny odbiór usuwania nadal pozostaje do
wykonania.

## Migracja, wersja i commit

**Korekta nadrzędna z 23.10.2026, instalacja 22:20:** piąta poprawka oraz
wyjaśnienie PIN-u NetRemote zostały zbudowane, atomowo zainstalowane i
uruchomione w AMC Test z rewizji
`591322e2f85c0a07634733c6164fa4cc6a336595`, pakiet `53e3d987`. Kontrola
potwierdziła odpowiadające okno „AMC Test — 23.10.2026, 22:20” z właściwego
katalogu `D:\Projekty Codex\AMC Python`. Wcześniejsze wzmianki, że poprawka
`3e57b686` albo informacja o PIN-ie nie są zainstalowane, są historyczne i
zastąpione przez ten zapis. Odbiór samego połączenia z radiem nadal pozostaje
do wykonania przez użytkownika.

Nowa sekcja konfiguracji jest opcjonalna i nie wymaga migracji istniejących
profili. Profil publiczny nie otrzymuje możliwości `session.frontier-smart`.
Commit źródłowy implementacji i testów: `412adf67` —
`feat(amc): dodaj Frontier Smart i domknij poprawki Radia`. Identyfikator
poprawki zgodnej migracji profilu: `63b30444` —
`fix(amc): pozwol updaterowi rozszerzyc profil wydania`. Korekta po pierwszym
odbiorze urządzenia: `19ae6089` —
`fix(frontier): wykryj radio UNDOK i uprosc konfiguracje`. Poprawka zachowania
pustej i zapisanej listy: `86727573` —
`fix(frontier): skanuj automatycznie tylko pusta sesje`. Korekta po trzecim
odbiorze: `3ce574a6` — `fix(frontier): popraw pierwsze wykrywanie urządzenia`.
Korekta po czwartym zgłoszeniu: `b11fd8bbc2de6a8f23746e5f2ec437b021f86762`
— `fix(frontier): potwierdzaj radio przed pytaniem o PIN`. Piąta korekta
wyboru także dla jednego wyniku: `3e57b68656ee06c1742a3775bac3d810f792646f`
— `fix(amc): domknij OAuth YouTube i wybor Frontier`.
Korekta obsługi błędu usuwania PIN-u: `9e8d3eab643b579215719bc52ac77b215f0c6fea`
— `fix(amc-test): dopracuj PIN Frontier i start Spotify`.
Najnowsza zainstalowana kompilacja AMC Test:
`2026.10.23-9e8d3eab643b579215719bc52ac77b215f0c6fea-ce7898a4`.
Nie publikować ani nie promować do profilu publicznego bez nowej zgody
użytkownika.

## Siódmy odbiór: kolejka głośności i zawieszenie radia — 24.10.2026

Użytkownik potwierdził, że połączenie z Teufel RADIO 3SIXTY działa, AMC pokazał
bieżące `Radio Poznań`, a zmiany głośności ostatecznie docierały do urządzenia.
Szybka seria poleceń była jednak wykonywana z bardzo dużym opóźnieniem. Po
około dwóch minutach radio nadal realizowało wcześniejsze zmiany, interfejs
AMC przestał odpowiadać przewidywalnie, a chwilowo nie dało się ściszyć radia
również sprzętowo. Anulowanie i ponowne wejście nie przywróciły od razu
odtwarzacza. Ta obserwacja zastępuje wcześniejsze założenie, że sama
serializacja hosta wystarcza do bezpiecznej regulacji.

Przyczyną była różnica między odrzuceniem spóźnionego wyniku a anulowaniem
pracy. Bramka `BackgroundRunner` nie pokazywała starych odpowiedzi, lecz każde
naciśnięcie nadal uruchamiało rzeczywiste żądanie FSAPI. Koordynator C#
wykonywał je kolejno, więc szybkie klawisze tworzyły długą kolejkę po stronie
radia.

Poprawiony kontrakt:

- AMC wysyła najwyżej jedno polecenie głośności naraz;
- podczas jego wykonywania zapamiętuje tylko najnowszą wartość docelową;
- seria `25, 30, 35` wysyła `25`, a następnie `35`, bez pośredniego `30`;
- inne polecenie transportu nie nakłada się na trwające; NVDA mówi
  `Poprzednie polecenie Frontier Smart jeszcze trwa`;
- cichy timer stanu nie odpytuje radia w czasie aktywnego polecenia;
- po błędzie suwak wraca do ostatniej potwierdzonej wartości i AMC prosi o
  odczekanie przed ponowieniem;
- zmiana aktywnego urządzenia usuwa oczekującą wartość głośności.

Automatyczny test odtwarza szybką serię trzech zmian i potwierdza dokładnie dwa
wywołania transportu: pierwszą oraz ostatnią wartość. Zmiana przeszła także
pełną regresję wxPython: **2032 zaliczone, 111 kontrolowanie pominiętych i 13
zaliczonych podtestów**, zero błędów. Rzeczywisty odbiór na Teufelu pozostaje
obowiązkowy, ponieważ testy nie mogą zasymulować opóźnień konkretnego firmware
ani jego interakcji z przyciskami sprzętowymi.

Zmiana jest w commicie `fe281d31af2c5328f1ada1c3668a587feefbcf80` —
`feat: dodaj zbiorcze transmisje i ustabilizuj Frontier`. Została zbudowana,
atomowo zainstalowana i uruchomiona jako paczka `8bce7f95` w
`D:\Projekty Codex\AMC Python`; potwierdzone okno ma tytuł
`AMC Test — 24.10.2026, 13:33`. AMC Public pozostaje bez zmian. Po instalacji
pozostaje ręczny test szybkiej serii głośności na Teufelu.

## Ósmy odbiór: skrót trybu i przygotowanie presetów — 24.10.2026

Użytkownik ocenił zachowanie Frontier Smart jako stabilniejsze i nie zgłosił
nowego wyniku regulacji głośności. Potwierdził natomiast dwa niezależne błędy:

- pozycja `Odtwarzanie → Wybierz tryb Frontier Smart…` nie miała skrótu;
- `Ctrl+Alt+P` kończył się komunikatem
  `Nie udało się odczytać presetów Frontier Smart: Urządzenie nie udostępniło presetów w bieżącym trybie.`

Log z 13:43:44 potwierdził, że drugi błąd pochodził z operacji
`frontierSmart.presets`, a nie z listy lub fokusu wxPython. AMC wysyłał od razu
`LIST_GET_NEXT netRemote.nav.presets`. Protokół FSAPI po zmianie trybu wyłącza
jednak `netRemote.nav.state`; urządzenie może wtedy zwrócić blokadę węzła mimo
istniejących presetów. Poprawiony klient najpierw odczytuje stan nawigacji,
w razie potrzeby ustawia go na `1`, czeka aż `netRemote.nav.status` zgłosi
gotowość i dopiero pobiera listę. Ten sam warunek poprzedza uruchomienie
wybranego presetu. Starsze urządzenie bez węzła stanu zachowuje zgodny,
bezpośredni wariant odczytu.

Polecenie wyboru trybu otrzymuje kontekstowy skrót `Ctrl+Alt+M` w sesji
Frontier Smart. Ta sama kombinacja ma być widoczna i wykonywać tę samą akcję w
menu Odtwarzanie, pełnej i kontekstowej pomocy oraz palecie poleceń. Nie jest
rejestrowana jako niezależny akcelerator menu, dzięki czemu wykonanie nadal
przechodzi przez wspólny router i jego warunki dostępności.

Automatyczna bramka obejmuje kolejność żądań FSAPI: stan nawigacji, włączenie,
przejściową odpowiedź `FS_NODE_BLOCKED`, oczekiwanie na gotowość i dopiero
listę presetów. Test powierzchni poleceń sprawdza wykonanie `Ctrl+Alt+M`, skrót
w menu, opis w pomocy oraz nazwę i skrót w palecie.

Rzeczywiste wyniki fazy źródłowej:

- ukierunkowane testy wxPython: **106 zaliczonych**;
- ukierunkowany kontrakt Frontier Smart: **1/1 zestaw zaliczony**;
- komplet kontraktów LiteHost: **27/27 zestawów zaliczonych**;
- pełna regresja wxPython: **2032 zaliczone, 111 kontrolowanie pominiętych i
  13 zaliczonych podtestów**;
- kompilacja LiteHost Release: **0 ostrzeżeń i 0 błędów**.

Powyższe wyniki dowodzą zmiany źródłowej i budowalności, nie działania na
prawdziwym Teufelu. Numer commitu, paczki i wynik instalacji należy dopisać po
ich rzeczywistym wykonaniu. Po instalacji konieczny jest odbiór `Ctrl+Alt+M`,
`Ctrl+Alt+P`, początkowego fokusu, Escape i uruchomienia presetu z NVDA.
