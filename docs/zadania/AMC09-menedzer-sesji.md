# AMC09 — Menedżer sesji i zwarta numeracja

Status: **Menedżer oraz pierwsze rozszerzenie Konfiguruj są zainstalowane w
AMC Test. Ujednolicone `Ctrl+F5`, Foldery Biblioteki i naprawa obsługi
klawiszy na natywnych listach są gotowe w źródłach i testach; czekają na
bezpieczną instalację oraz ręczny odbiór NVDA i usług**

Data realizacji: 2026-10-19

Specyfikacja zatwierdzona przez użytkownika:
`D:\Projekty Codex\Accessible Multimedia Controller\AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.
Historyczny projekt został użyty tylko jako materiał do odczytu.

## Materiał do dokumentacji użytkownika

- `Ctrl+Shift+S` otwiera jedną listę „Menedżer sesji”. Lista pokazuje najpierw
  sesje włączone z ich aktualnymi numerami `Ctrl+1–9`, a następnie sesje
  wyłączone. Każdy wiersz zawiera zwykłą nazwę, stan włączenia oraz znany
  aplikacji stan gotowości. W mowie nie pojawiają się identyfikatory ani nazwy
  klas.
- `Enter` przełącza do zaznaczonej włączonej sesji. Na sesji wyłączonej lista
  pozostaje otwarta i podaje, że należy użyć Spacji.
- `Spacja` włącza lub wyłącza zaznaczoną sesję. Wyłączenie zagęszcza numery.
  Ponowne włączenie dopisuje sesję na końcu. Nie usuwa konta, biblioteki,
  historii ani ustawień usługi.
- `Alt+strzałka w górę` i `Alt+strzałka w dół` zmieniają położenie włączonej
  sesji oraz jej numer. Fokus pozostaje na tej samej sesji.
- Przycisk „Konfiguruj…” oraz kontekstowe `Ctrl+F5` prowadzą do właściwego
  konta albo urządzenia. Spotify i TIDAL otwierają okno statusu konta z
  przyciskiem „Zaloguj w przeglądarce”, a WiiM odświeża zapisane urządzenia.
  Samo otwarcie Menedżera ani okna konta nie uruchamia OAuth, nie skanuje sieci
  i nie steruje głośnikami.
- W Plikach lokalnych `Ctrl+F5` otwiera okno „Foldery Biblioteki”. Można w nim
  dodać folder, odświeżyć zaznaczony folder albo wszystkie foldery oraz
  bezpiecznie odłączyć folder. Odłączenie wyłącza dalsze skanowanie, ale nie
  usuwa plików z dysku ani zapisanych w AMC pozycji, historii, Ulubionych,
  kolejki, playlist, zakładek i pozycji odtwarzania. Po zapisie fokus wraca na
  listę folderów albo — gdy lista jest pusta — na „Dodaj folder”.
- W tej samej sesji `F5` wykonuje pełne odświeżenie Folderów Biblioteki bez
  otwierania okna. Menu „Plik” zawiera osobno „Odśwież Foldery Biblioteki,
  F5” oraz „Foldery Biblioteki, Ctrl+F5”.
- `Ctrl+F5` zachowuje odrębne, utrwalone znaczenie sesji i ma teraz wszędzie
  jednoznaczną nazwę:

  - Pliki lokalne — „Foldery Biblioteki”; można dodać, odświeżyć albo
    bezpiecznie odłączyć folder;
  - Radio — „Odśwież stacje Radia”; ponownie wczytuje stacje i aktualnie
    otwarty widok, zachowując zaznaczenie tego samego elementu, jeżeli nadal
    istnieje;
  - Podcasty i YouTube — „Odśwież wszystkie podcasty, kanały YouTube i
    playlisty”;
  - Spotify — „Konto Spotify”; pomoc dopowiada, że jest tu również ponowne
    logowanie;
  - TIDAL — „Konto i synchronizacja TIDAL”;
  - WiiM — „Urządzenia WiiM”; polecenie odświeża listę zapisanych urządzeń;
  - Sonos — „Głośniki i grupy Sonos”; polecenie pozwala wybrać dom i grupę
    sterowania.
- Polecenia konfiguracyjne i „Foldery Biblioteki” są w menu „Plik”, tak jak w
  historycznym AMC. `Ctrl+F1`, pełna pomoc oraz paleta `Ctrl+Shift+K` pokazują
  tylko wariant właściwy dla bieżącej sesji.
- Nie można wyłączyć ostatniej sesji. Nie można również wyłączyć sesji, w
  której trwa wewnętrzne odtwarzanie, oczekiwanie na rozpoczęcie odtwarzania
  albo nagrywanie. Wyłączenie Sonosa lub WiiM zmienia tylko widoczność sesji;
  nie wysyła do urządzenia polecenia Stop.
- `Ctrl+1–9`, `Ctrl+Page Up`, `Ctrl+Page Down`, menu Widok, pełna pomoc,
  `Ctrl+F1`, dodatek NVDA i paleta `Ctrl+Shift+K` korzystają z tej samej
  aktywnej kolejności. Wyłączona sesja nie jest reklamowana w menu ani palecie.
- Świeży profil ma: `Ctrl+1` Pliki lokalne, `Ctrl+2` Radio oraz `Ctrl+3`
  Podcasty i YouTube. Domyślnie otwiera Pliki lokalne. Istniejący profil po
  aktualizacji zachowuje wszystkie dotychczasowe sesje i ich kolejność.
- Nazwa sesji radiowej brzmi wszędzie „Radio”. Wartości techniczne zapisu nie
  zostały zmienione, więc dotychczasowe stacje, harmonogramy i historia nie
  wymagają migracji nazw.
- W Ustawieniach pozostała informacja kierująca do Menedżera sesji. Nie ma już
  drugiego, konkurencyjnego edytora kolejności.

## Uzasadnienie i decyzje

- Jedna zwarta lista jest źródłem kolejności i stanu włączenia. Dzięki temu
  wyłączenie sesji nie zostawia dziury w numerach i nie rozjeżdża skrótów z
  menu, pomocą ani paletą.
- Zapis otrzymał wersjonowany znacznik migracji. Stary zapis oznaczał tylko
  kolejność, dlatego pierwsza migracja zachowuje wszystkie znane sesje zamiast
  uznać brakującą usługę za wyłączoną. Dopiero nowy zapis rozróżnia sesje
  aktywne i wyłączone.
- Stan gotowości pochodzi wyłącznie z już znanych danych lokalnych i pamięci
  bieżącego procesu. Menedżer nie wykonuje sieciowego „sprawdzania” konta w
  tle, bo samo przeglądanie listy nie jest zgodą na logowanie.
- Blokada wyłączania obejmuje wewnętrzne tory programu i Radio podczas
  nagrywania. Stan odtwarzania na urządzeniach zewnętrznych nie blokuje
  ukrycia Sonosa ani WiiM, ponieważ ukrycie sesji nie może sterować
  urządzeniem.
- Korekta z 2026-10-18 zastępuje wcześniejsze założenie stałych numerów usług:
  numer wynika z bieżącej, ręcznie ustawionej kolejności aktywnych sesji.
- Korekta z 2026-10-18 zastępuje nazwę „Radio internetowe” krótką nazwą
  „Radio” we wszystkich powierzchniach użytkowych. Wewnętrzny identyfikator
  `radio` i dane profilu pozostają bez zmian.
- Automatyczne pierwsze otwarcie Menedżera w publicznym AMC nie zostało
  włączone. To zachowanie należy do odbioru czystego profilu w AMC12 i nie
  zmienia obecnego profilu AMC Test.
- **Korekta użytkownika z 19 października 2026:** przywrócono kontekstowe
  znaczenie `Ctrl+F5` ze starego AMC. Spotify i TIDAL otwierają konto, WiiM
  odświeża urządzenia, Podcasty odświeżają Bibliotekę, a Sonos zachowuje wybór
  celu. Zwykłe `F5` nadal jest odświeżaniem bieżącego widoku.
- **Korekta użytkownika z 19 października 2026, późniejsza:** powyższe
  ustalenie rozszerzono o Pliki lokalne. `Ctrl+F5` otwiera „Foldery
  Biblioteki” z dodawaniem, odświeżaniem i niedestrukcyjnym odłączaniem.
  Polecenia przeniesiono z ogólnego menu „Widok” do kontekstowego menu „Plik”.
- **Korekta użytkownika z 19 października 2026, najnowsza:** ogólne określenie
  „Konfiguruj konto lub urządzenie bieżącej sesji” nie jest już używane jako
  opis działającego `Ctrl+F5`. Zastąpiły je powyższe nazwy właściwe dla
  Spotify, TIDAL-a, WiiM, Sonosa, Podcastów i YouTube oraz Plików lokalnych.
  Nazwa, opis, skrót, widoczność i wykonywana akcja pochodzą z jednego modelu
  używanego przez menu, pełną pomoc, `Ctrl+F1` i paletę `Ctrl+Shift+K`.
- **Korekta użytkownika z 20 października 2026:** zgłoszenie „Ctrl+F5 dalej
  nie działa” ujawniło, że poprzednia decyzja o pozostawieniu skrótu bez
  funkcji w Radiu była błędna. Ta korekta zastępuje zdanie, że Radio nie
  reklamuje `Ctrl+F5`. W Radiu skrót ma teraz nazwę „Odśwież stacje Radia”,
  przeładowuje bieżący widok bez zmiany zaznaczenia i jest dostępny również
  w otwartym odtwarzaczu. Ta sama nazwa, akcja i dostępność obowiązują w menu,
  pełnej pomocy, `Ctrl+F1` i palecie `Ctrl+Shift+K`.
- Natywny widok listy Windows przejmował wcześniej `F5` i `Ctrl+F5` przed
  routerem AMC. Oba gesty przechodzą teraz przez tę samą wczesną bramkę co
  pozostałe polecenia listy, więc menu, skrót, pomoc, paleta i wykonanie nie
  rozchodzą się.
- **Doprecyzowanie diagnozy z 20 października 2026:** działająca instalacja
  `f96149f7-904ceb8c` zawiera już wczesną bramkę listy oraz poprawne funkcje
  `Ctrl+F5` dla Plików lokalnych, Podcastów i YouTube, Spotify, TIDAL-a, WiiM-a
  i Sonosa. Nie zawiera jednak późniejszego commitu `a6614d11`; właśnie dlatego
  w Radiu nie ma ani rozstrzygniętej akcji skrótu, ani prezentacji, ani pozycji
  menu. Zgłoszenie nie wynika z NVDA ani z awarii klawiatury.

## Zmienione miejsca

- Model aktywnych sesji i migracji: `wxlite/amc_wx_lite/session_order.py`,
  `state_store.py`.
- Wykonanie, fokus, gotowość, ochrona odtwarzania i nagrywania:
  `wxlite/amc_wx_lite/gui.py`.
- Wspólne menu, skróty, pomoc, paleta i dodatek NVDA:
  `menu_model.py`, `shortcuts.py`, `nvda_bridge.py`.
- Obsługa Folderów Biblioteki: `LocalFolderLibraryManager.cs`, operacje
  LiteHost, `host_client.py` i dostępne okno `LibraryFoldersDialog` w `gui.py`.
- Ujednolicona nazwa „Radio”: `navigation.py`, `search_catalog.py`,
  `search_sources.py`, `transient_preview_policy.py` oraz powiązane testy.
- Nowe testy Menedżera: `wxlite/tests/test_session_manager.py`, rozszerzone
  testy kolejności, migracji, menu, pomocy, palety i sesji usługowych.

## Testy i wynik

- Rozszerzenie kont i WiiM: **105/105** ukierunkowanych testów wxPython oraz
  **3/3** zestawy protokołu .NET zaliczone. Kompilacje Release testów protokołu
  i LiteHost zakończyły się bez ostrzeżeń i błędów. Testy nie otwierały
  przeglądarki, nie logowały kont i nie wysyłały poleceń do urządzeń.
- Poszerzona regresja poleceń i sesji: **191/191 zaliczonych**. Promocja
  zbudowała 1667 plików, potwierdziła manifest i sumy SHA-256 kandydata oraz
  instalacji, a następnie uruchomiła właściwy profil AMC Test. Niezależna
  kontrola po promocji potwierdziła działający uruchamiacz, LiteHost i okno.
- Korekta `Ctrl+F5` i Folderów Biblioteki: **160/160** ukierunkowanych testów
  skrótów, menu, pomocy, palety, fokusu i wczesnego routingu listy zaliczonych.
  Pełny zestaw Core zakończył się kodem 0; nowy test potwierdził dodanie,
  odświeżenie i odłączenie folderu przy zachowaniu rzeczywistego pliku.
- Doprecyzowanie nazw `Ctrl+F5`: **131/131** testów katalogu poleceń, skrótów,
  menu, palety, kolejności sesji i Sonosa oraz dodatkowe **73/73** testy
  profili wydania, GUI, wczesnego routingu listy, dodatku NVDA i Menedżera
  sesji zaliczone. Test kontraktowy sprawdza dla każdej właściwej sesji nazwę,
  opis, skrót, widoczność, rozwiązaną akcję, menu, paletę, pełną pomoc i
  komunikat `Ctrl+F1`; ówczesne założenie o braku polecenia w Radiu zostało
  zastąpione korektą z 20 października 2026.
- Radiowe `Ctrl+F5`: **5/5** bezpośrednich testów kontraktu zaliczonych.
  Sprawdzono rozstrzygnięcie skrótu na liście i w odtwarzaczu, wykonanie,
  zachowanie zaznaczenia, kolejność komunikatów, pojedynczą pozycję menu,
  paletę, pełną pomoc i `Ctrl+F1`. Szerszy lokalny przebieg zaliczył 154 testy,
  w tym wszystkie zmienione, ale jako całość nie był zieloną bramką: dwa
  niezależne testy nie mogły pisać do systemowego katalogu tymczasowego, a
  cztery moduły wymagały nieobecnego w tym interpreterze pakietu `pytest`.
  Dlatego wyniku 154 nie przedstawia się jako pełnego zaliczonego zestawu.
- Ponowna diagnoza z działającej instalacji potwierdziła kontrakt sześciu
  pozostałych sesji i dokładny brak trzech elementów wyłącznie w Radiu:
  prezentacji, wykonywanej akcji i pozycji menu. Aktualne źródła zaliczyły
  **135/135** ukierunkowanych testów skrótów, wczesnego routingu listy, menu,
  palety, pełnej pomocy, `Ctrl+F1` i wykonania. Zbudowany kandydat został
  dodatkowo zaimportowany z własnego runtime: każda z siedmiu sesji ma
  dokładnie jedną właściwą akcję i jedną pozycję `Ctrl+F5`.
- Końcowa regresja wxPython bez czterech istniejących prób wymagających
  lokalnego gniazda sieciowego: **1851 zaliczonych, 110 pominiętych i 11
  podtestów zaliczonych**. Cztery wyłączone próby RSS doszły w osobnym
  przebiegu do połączenia z `127.0.0.1`, lecz sandbox zabronił tego połączenia;
  nie dotyczyły zmienionego kodu Folderów Biblioteki.
- LiteHost oraz projekt testów Core zbudowały się w konfiguracji Release bez
  ostrzeżeń i błędów. Następnie utworzono i sprawdzono integralność paczki 1667
  plików. Aktualizator dwukrotnie odmówił podmiany, ponieważ widział działające
  składniki bieżącej instalacji AMC Test. Nie zatrzymano ich i nie zmieniono
  zainstalowanej wersji.

- Testy ukierunkowane modelu, magazynu, skrótów, palety, GUI i dostępnych
  etykiet: **94 zaliczone**.
- Testy regresji menu, Sonosa, TIDAL-a, WiiM, kolejności i izolacji wx:
  **152 zaliczone**.
- Pierwszy pełny przebieg wykrył pięć regresji testów: trzy testy zakładały
  dawną domyślną obecność wszystkich usług, jeden dawną nazwę polecenia, a
  jeden kolizję klawiszy dostępu. Założenia testów i klawisze menu poprawiono;
  ukierunkowana regresja po poprawce jest zielona.
- Pełny końcowy przebieg `wxlite/tests`: **1788 zaliczonych, 110 świadomie
  pominiętych, 11 podtestów zaliczonych**, czas 82,14 s. Pominięcia dotyczą
  istniejących bramek wymagających zbudowanych składników lub środowiska i nie
  zostały policzone jako zaliczone.
- Przed kompilacją bramka bezpieczeństwa o 02:54 UTC sprawdziła 15 jawnych
  katalogów nagrań: 0 aktywnych okien harmonogramów, 0 plików
  `.amc-partial`, 0 plików rosnących i 0 plików zablokowanych. Działające AMC
  zostało podmienione dopiero po tym wyniku.
- Skrypt odbiorczy zbudował trzy składniki .NET, utworzył pakiet liczący 1660
  plików, sprawdził manifest i sumy SHA-256, zastosował aktualizację,
  zweryfikował zainstalowany pakiet i uruchomił nowe AMC Test.
- Kwit instalacji potwierdza zgodność oczekiwanej i zainstalowanej wersji oraz
  trzy procesy uruchomione z jednego katalogu instalacji. Okno miało tytuł
  „AMC Test — 19.10.2026, 04:54”.
- 20.10.2026 przed promocją ponownie sprawdzono procesy według pełnych ścieżek
  i wierszy poleceń, rozpoznano 17 skonfigurowanych lokalizacji nagrań,
  sprawdzono dziennik hosta, dziesięciosekundowy przyrost dostępnych plików
  `.amc-partial` oraz najbliższe terminy harmonogramów. Sześć folderów na
  dysku `H:` nie było dostępnych dla izolowanego procesu kontrolnego; w
  pozostałych nie znaleziono pliku częściowego ani terminu przypadającego w
  ciągu 10 minut, a ostatnie wpisy nagrywania w dzienniku były zakończone.
  Rozstrzygającą bramką było przyjęcie zwykłego zamknięcia przez działający
  interfejs i jego żywy host: ta sama ścieżka odmawia zamknięcia przy aktywnym
  nagraniu albo niepewnym stanie. Nie wymuszono zakończenia żadnego procesu.
- Promocja bieżącego `HEAD` zbudowała trzy składniki .NET i paczkę 1667 plików.
  Skrypt sprawdził pełny manifest i wszystkie 1667 sum SHA-256 przed i po
  atomowej podmianie. Zainstalowany manifest ma SHA-256
  `CA4FAF3711E018728A2493D1F866F502F756A6A8904E0BD439B9F5554391D16F`.
- Uruchomienie zostało potwierdzone niezależnie: dokładnie jeden uruchamiacz,
  jeden frontend i jeden LiteHost działają z `D:\Projekty Codex\AMC Python`.
  Okno ma tytuł „AMC Test — 20.10.2026, 00:10”. W tym przebiegu nie powtarzano
  testów, ponieważ niezmieniony kod `e1ea7f3d` miał wiarygodny wynik
  **131 + 73 = 204 zaliczone**; kwit uczciwie zapisuje testy promocji jako
  „pominięte”.

## Znane ograniczenia

- Prawdziwe logowanie Spotify, TIDAL i Sonos oraz odświeżenie rzeczywistego WiiM
  wymagają świadomej próby użytkownika. Automaty tej nocy nie otwierały
  przeglądarki, nie logowały kont i nie wysyłały poleceń do urządzeń.
- Trwającego OAuth nie można jeszcze anulować z okna AMC; okno pozostaje
  otwarte do wyniku albo limitu czasu.
- Stan Spotify jest „Połączona” dopiero po odczycie konta w bieżącym procesie;
  przed nim Menedżer uczciwie pokazuje „Wymaga zalogowania”. TIDAL może użyć
  istniejącej lokalnej migawki Biblioteki, ale nie pobiera jej w tle.
- Publiczne filtrowanie sesji przez manifest możliwości, osobne magazyny AMC i
  AMC Test oraz jednorazowe otwarcie na czystej publicznej instalacji należą
  do AMC12.
- Ręczny odbiór NVDA powinien sprawdzić pierwsze otwarcie, ruch po wierszach,
  Spację, Enter, Alt+strzałki, Konfiguruj, anulowanie, powrót fokusu i ponowne
  otwarcie. Testy automatyczne nie są dowodem rzeczywistej mowy NVDA.
- Ręczny odbiór Folderów Biblioteki powinien sprawdzić początkowy fokus,
  dodanie małego folderu, ponowne odświeżenie, anulowanie odłączenia,
  potwierdzone odłączenie i powrót fokusu. Odłączenie jest celowo
  niedestrukcyjne; osobne ręczne zapominanie wpisów nie należy do tego okna.
- Ręczny odbiór NVDA nadal powinien sprawdzić sesyjne nazwy i działanie
  `Ctrl+F5` na prawdziwych kontach i urządzeniach. Kompilacja i instalacja
  potwierdzają dostarczenie kodu, ale nie zastępują tego odbioru.
- Radiowe i sesyjne `Ctrl+F5` jest zainstalowane w AMC Test w pakiecie
  `fd5f4231-b7475d46`. Nadal wymaga ręcznego odbioru NVDA na prawdziwych
  kontach i urządzeniach; instalacja nie jest dowodem działania zewnętrznej
  usługi.

## Porządek dysku

- Po testach doprecyzowania nazw usunięto pusty, utworzony wyłącznie dla tego
  przebiegu katalog
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\.amc-temp-ctrl-f5-labels`.
  Nie zawierał plików ani podkatalogów, więc odzyskane miejsce wyniosło 0 B;
  usunięcie nie objęło danych użytkownika ani zastanych artefaktów projektu.
- Po testach tej korekty usunięto wyłącznie utworzony przez nią katalog
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\.amc-temp-ctrl-f5`:
  283 odtwarzalne pliki testowe, około 0,39 MB. Usunięcie jest lokalnie
  nieodwracalne, lecz nie obejmowało źródeł ani danych użytkownika.
- Zachowano sprawdzoną paczkę kandydującą w projektowym `.test-output`, bo
  instalacja nie została ukończona. Nie usuwano zastanych `.test-output` ani
  `.test-tmp` i nie traktowano ich jako śmieci bez potwierdzenia pochodzenia.
- Po potwierdzonej instalacji usunięto wyłącznie katalog roboczy etapu
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\work\amc09` (27 plików,
  około 1,6 MB) oraz odtwarzalne katalogi `bin\Release` trzech budowanych
  projektów pod
  `D:\Projekty Codex\AMC - integracja wxPython\src` (157 plików, około
  133,3 MB).
- Łącznie odzyskano około 128,7 MiB. Usunięcie jest lokalnie nieodwracalne,
  ale te pliki są odtwarzalne z zatwierdzonych źródeł przez kompilację.
- Skrypt promowania sam usunął bieżący staging w `.test-tmp`. Nie usuwano
  zastanych, niepewnych katalogów `.test-tmp`, pamięci testów ani danych
  użytkownika.
- Zachowano zainstalowany program w `D:\Projekty Codex\AMC Python`, bieżący
  kwit oraz jedyną zweryfikowaną paczkę odbiorczą w `.test-output`. Nie
  usunięto źródeł, `.git`, ustawień, poświadczeń, nagrań ani pobrań.
- Pomocniczy katalog zapisu tego kwitu
  `C:\Users\micha\Documents\Codex\2026-10-18\ma\work\amc09-docs`
  zawierał jeden plik Markdown (około 8,7 KB) i również został usunięty.
- Po zweryfikowaniu nowej instalacji usunięto dokładnie zastąpionego kandydata
  `AMC-Python-next-2026.10.19-8f1dad15c1af78d25ebc074f0f571fac8bb18cdd-0cfb4e32`
  z projektowego `.test-output` oraz odtwarzalne `bin\Release` projektów
  uruchamiacza, aktualizatora, LiteHost i Core. Było to łącznie 1828 plików i
  275 600 358 bajtów, czyli około 262,8 MiB. Usunięcie jest lokalnie
  nieodwracalne, lecz zawartość można odtworzyć z zatwierdzonych źródeł.
- Zachowano nowego zweryfikowanego kandydata `f96149f7-904ceb8c`, kwit
  instalacji oraz wszystkie zastane, niepewne katalogi `.test-output` i
  `.test-tmp`. Nie usunięto danych użytkownika, nagrań, ustawień ani źródeł.
- Po ponownej diagnozie usunięto wyłącznie odtwarzalny katalog testowy
  `.test-tmp\ctrl-f5-diagnoza-20261020`. Zachowano nowego kandydata
  `18f48ef0-86421c1d`, ponieważ jest jedynym gotowym pakietem z radiowym
  `Ctrl+F5` i nie został jeszcze bezpiecznie zainstalowany.

## Wersja i commit

- Radiowe `Ctrl+F5`, wspólny katalog poleceń i testy kontraktu: commit
  `a6614d11` (`fix(amc09): dodaj Ctrl+F5 w Radiu`). Zmiana jest potwierdzona
  w źródłach, testach i kandydacie
  `2026.10.20-fd5f423117f87c34aff6e9c4def22a985aa307a6-b7475d46`
  (1667 plików). Instalację, integralność i uruchomienie potwierdzono
  20 października 2026 o 12:55. Publikacji nie wykonano.
- Instalacja i uruchomienie doprecyzowanych nazw `Ctrl+F5`: potwierdzone dla
  `2026.10.20-f96149f75e83eea064899db78c762596e56d2504-904ceb8c` w
  `D:\Projekty Codex\AMC Python`. Paczka zawiera 1667 plików; źródłem jest
  `f96149f7`, czyli commit dokumentacyjny oparty na zmianie `e1ea7f3d`.
  Publikacji nie wykonano.
- Precyzyjne, sesyjne nazwy `Ctrl+F5` we wspólnym katalogu poleceń: commit
  `e1ea7f3d` (`fix(amc09): doprecyzuj Ctrl+F5 wedlug sesji`). Kod, testy,
  kompilacja, instalacja i uruchomienie są potwierdzone lokalnie.
- Ujednolicenie `F5`, `Ctrl+F5` i Folderów Biblioteki: commit `8f1dad15`
  (`feat(amc): przywroc Ctrl+F5 i Foldery Biblioteki`).
- Sprawdzony kandydat:
  `2026.10.19-8f1dad15c1af78d25ebc074f0f571fac8bb18cdd-0cfb4e32`,
  1667 plików. Instalacja została bezpiecznie wstrzymana przez aktualizator;
  zainstalowany AMC Test pozostał na
  `2026.10.19-c3ffea70d9f002d936bbabd43421b03393c9702d-a329942c`.
  Publikacji nie wykonano.

- Rozszerzenie `Ctrl+F5` oraz kont Spotify i TIDAL: commit `c3ffea7`
  (`feat(amc): dodaj konta Spotify i TIDAL pod Ctrl+F5`).
- Instalacja i uruchomienie: potwierdzone dla
  `2026.10.19-c3ffea70d9f002d936bbabd43421b03393c9702d-a329942c` w
  `D:\Projekty Codex\AMC Python`. Publikacji nie wykonano.

- Kod i testy źródłowe: commit `dece7646` (`feat(amc09): dodaj menedzer sesji`).
- Dokumentacja wyniku i wersja użyta do instalacji: commit `6c79bdd3`
  (`docs(amc09): zapisz realizacje menedzera sesji`).
- Kompilacja, instalacja i uruchomienie: potwierdzone dla
  `2026.10.19-6c79bdd32904b9468b07489e79da715de512d3e0-972b46e1` w
  `D:\Projekty Codex\AMC Python`.
- Pełne testy Python wykonano przed kompilacją. Skrypt promowania otrzymał
  `-SkipTests`, aby nie powtarzać bez zmian tego samego przebiegu; kwit
  prawidłowo zapisuje testy etapu promowania jako „pominięte”, a nie jako
  zaliczone.
- Publikacja: nie wykonana i nie jest częścią nocnego zadania.
