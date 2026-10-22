# Rejestr zadań AMC

Ten katalog jest kanonicznym miejscem zapisywania osobnych zadań, które mają
przetrwać między rozmowami i być czytelne zarówno dla Codexa, jak i Hermesa.
Rejestr nie uruchamia pracy samodzielnie. Zadanie rozpoczyna się dopiero po
jawnym poleceniu użytkownika albo przez osobno uzgodniony harmonogram.

## Zasady prowadzenia

- Każde większe zadanie ma stały identyfikator i osobny plik o nazwie
  `<OBSZAR>-<NUMER>-<krotka-nazwa>.md`.
- Dozwolone statusy: `Oczekuje`, `W trakcie`, `Zablokowane`, `Zrobione`.
- Przed pracą przeczytaj ten rejestr, właściwy plik zadania, `AGENTS.md` oraz
  dokumenty wskazane przez zadanie.
- Nie rozpoczynaj pozostałych wpisów tylko dlatego, że znajdują się w rejestrze.
- Przy rozpoczęciu zmień status w pliku zadania i tutaj na `W trakcie`.
- Po zakończeniu zapisz w pliku zadania datę, wynik, zmienione pliki, commit,
  uruchomione testy z rezultatami i dokładną wersję instalacji, jeśli powstała.
  Dopiero po zweryfikowaniu kryteriów akceptacji ustaw status `Zrobione`.
- W każdym rozpoczętym zadaniu prowadź również sekcje `Materiał do dokumentacji
  użytkownika`, `Uzasadnienie i decyzje`, `Testy i wynik`, `Znane ograniczenia`
  oraz `Wersja i commit`. Tekst użytkowy ma być gotowy do automatycznego
  złożenia instrukcji i opisu wydania, ale pozostaje projektem do korekty i
  zatwierdzenia użytkownika.
- Korekty użytkownika zapisuj z datą i oznaczaj, które wcześniejsze ustalenie
  zastępują. Nie utrzymuj dwóch sprzecznych wariantów jako równoważnych.
- Jeżeli praca utknęła, ustaw `Zablokowane` i opisz konkretną przeszkodę oraz
  najkrótszy sposób wznowienia.
- Nie zapisuj tu haseł, tokenów, danych kont ani prywatnych logów użytkownika.

## Zadania

- `SESSION-001` — **W trakcie; korekta po odbiorze NVDA ma 76/76 testów
  celowanych, pełną regresję Pythona 1983/1983 i została zainstalowana w
  zbiorczym AMC Test; czeka na ponowny odbiór NVDA** —
  pełne, wykonywalne opcje sesji z historycznego AMC oraz nowa domyślna
  prędkość osobno dla Plików i Podcastów. Szczegóły:
  [SESSION-001-opcje-sesji-i-predkosc.md](SESSION-001-opcje-sesji-i-predkosc.md).

Roboczy indeks materiału z nocnych etapów do przyszłej instrukcji i opisu
zmian, wymagający korekty użytkownika:
[INDEKS-MATERIALU-INSTRUKCJA-I-ZMIANY-2026-10-19.md](INDEKS-MATERIALU-INSTRUKCJA-I-ZMIANY-2026-10-19.md).

- `BACKUP-001` — **Wdrożone i zweryfikowane w źródłach; czeka na instalację
  kandydata oraz ręczny odbiór NVDA** — bezpieczna pełna kopia bieżącego
  profilu oraz osobny eksport i import ustawień, Biblioteki, playlist AMC,
  Radia, harmonogramów, Podcastów i YouTube oraz urządzeń i usług. Szczegóły:
  [BACKUP-001-eksport-import-danych.md](BACKUP-001-eksport-import-danych.md).

- `REC-001` — **Zrobione; korekta zachowania istniejącego pliku po zerwaniu
  strumienia jest zainstalowana w AMC Test** — trwałość wykonanego
  harmonogramu nagrywania, zgodność listy `Alt+R` z blokadą zamknięcia oraz
  zachowanie niepustego pliku domkniętego przed awarią odbioru. Szczegóły:
  [REC-001-harmonogram-alt-r-zamykanie.md](REC-001-harmonogram-alt-r-zamykanie.md).
- `AMC02` — **Publiczny `alpha.431` zainstalowany i uruchomiony do odbioru
  NVDA; AMC Test czeka na bezpieczne zamknięcie** — `Alt+R`
  i `Alt+Shift+R` przy jednym wpisie podają widok, pozycję oraz nazwę pliku.
  `Ctrl+H` zapisuje od teraz potwierdzony start Radia, pliku i podcastu, a
  pojedynczy wpis Historii jest nazwany niezależnie od zdarzenia fokusu;
  wcześniejszych niezapisanych odtworzeń nie da się odtworzyć wstecz.
  Zachowano osobną pamięć zaznaczenia oraz bitrate, wielkość i folder pod lewą
  strzałką także w `Ctrl+H`. Bieżący zapis realizacji:
  [AMC02-listy-nagrywania-i-historii.md](AMC02-listy-nagrywania-i-historii.md).
  Zatwierdzona analiza historyczna:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC02_ANALIZA_2026-10-18.md`
  oraz `AMC02_REALIZACJA_ETAP_A_2026-10-18.md`. Właściwe wdrożenie wykonujemy
  w bieżącym AMC Test, a stary kod służy tylko jako wzorzec.
- `SCHED-001` — **Druga korekta po ręcznym odbiorze zainstalowana w AMC Test;
  czeka na ponowny odbiór NVDA** — dostępna przebudowa listy i edytora
  harmonogramów: informacje pod strzałkami, segmentowa data i czas oraz
  jednoznaczne wpisywanie czasu trwania. Szczegóły:
  [SCHED-001-edytor-i-klawisze-harmonogramow.md](SCHED-001-edytor-i-klawisze-harmonogramow.md).
- `NVDA-001` — **W trakcie; użytkownik potwierdził bardzo szybką reakcję
  `Ctrl+C` w AMC, pozostaje kontrola zwykłej aplikacji** — usunięcie opóźnienia `Ctrl+C` powodowanego przez
  NVDAExtensionGlobalPlugin bez zmiany zwykłego schowka w innych programach.
  Szczegóły:
  [NVDA-001-opoznienie-ctrl-c.md](NVDA-001-opoznienie-ctrl-c.md).
- `SEARCH-001` — **Wspólny kontrakt wyszukiwania dla wszystkich sesji oraz
  pustego profilu jest zainstalowany w obu profilach po pełnej regresji 1910
  testów; czeka na ręczny odbiór NVDA** — wyszukiwanie Plików lokalnych,
  YouTube, Radia,
  Spotify, TIDAL, WiiM i Sonosa:
  `Ctrl+Shift+L` pozostaje w oknie także dla zapisanego wyniku, wykonuje jedną
  właściwą operację i nie oddaje mowy głównemu oknu. `Ctrl+L` zamyka modal i
  przechodzi wspólnym poleceniem do Biblioteki. Szczegóły:
  [SEARCH-001-youtube-biblioteka-komunikaty.md](SEARCH-001-youtube-biblioteka-komunikaty.md).
- `POD-001` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór
  NVDA** — trzy tryby sortowania
  zbiorczej Biblioteki podcastów, kanałów YouTube i „Media internetowe”,
  prywatna trwałość wyboru i zachowanie zaznaczenia po stabilnym ID. Szczegóły:
  [POD-001-sortowanie-biblioteki-zrodel.md](POD-001-sortowanie-biblioteki-zrodel.md).
- `POD-002` — **Poprawka importu kanałów z uchwytem `@` jest zweryfikowana na
  prawdziwym kanale i zainstalowana w zbiorczym AMC Test; czeka na ponowny
  odbiór NVDA** — wcześniejsza wersja odrzucała stabilny adres z `%40` przed
  uruchomieniem `yt-dlp`. Normalizacja jest teraz idempotentna, a Enter nadal
  wykonuje sprawdzenie i zapis bez drugiego przycisku. Szczegóły:
  [POD-002-import-youtube-ctrl-n.md](POD-002-import-youtube-ctrl-n.md).
- `AMC04` — **Rozdziały podcastów oraz zakładki i rozdziały Spotify
  zweryfikowane automatycznie, zainstalowane i uruchomione w AMC Test; czekają
  na ręczny odbiór NVDA; korekta źródeł z 23.10.2026 uczciwie ogranicza
  automatyczne rozdziały Spotify do znaczników czasu z opisu odcinka i nie
  była instalowana** — przeniesiony do głównego AMC
  Test/Python zatwierdzony model skrótów
  zakładek, nazwanych zakładek, rozdziałów, historii widoków i historii
  odtwarzanych elementów. Bieżący zapis realizacji:
  [AMC04-nawigacja-zakladki-rozdzialy-historia.md](AMC04-nawigacja-zakladki-rozdzialy-historia.md).
  Źródłowy audyt i rozpoczęta realizacja są zapisane w
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC03_AUDYT_SKROTOW_2026-10-18.md`
  oraz `AMC04_REALIZACJA_ETAP_A_2026-10-18.md`. Stare źródła WPF służą tylko
  jako wzorzec; właściwe wdrożenie wykonujemy w tym repozytorium.
- `MENU-001` — **W trakcie; naprawa `Shift+F10` harmonogramów i nazwa `Alt+D`
  oraz korekta pełnych ścieżek profilu hosta są zainstalowane w AMC Test i
  czekają na odbiór NVDA** —
  wspólne menu kontekstowe bez odczytu technicznych cyfr i przypadkowych
  liter dostępu, nazwy zależne od rodzaju elementu, rzeczywiste skróty oraz
  audyt dostępności poleceń i nawigacji między sesjami. Szczegóły:
  [MENU-001-menu-kontekstowe-i-skroty.md](MENU-001-menu-kontekstowe-i-skroty.md).
- `AMC05` — **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór
  NVDA** — stan `Odtwarzane` lub `Wstrzymane` na właściwych listach bez utraty
  etykiety i bez przestawiania fokusa. Bieżący zapis realizacji:
  [AMC05-odtwarzany-element-na-listach.md](AMC05-odtwarzany-element-na-listach.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC05_ODTWARZANY_ELEMENT_NA_LISTACH_2026-10-18.md`.
- `AMC13` — **Rozszerzenie skoków procentowych zainstalowane w AMC Test;
  czeka na odbiór NVDA** — `End` w otwartym
  odtwarzaczu Time Shiftu wraca na żywo i do tempa normalnego, `NVDA+End`
  pozostaje poleceniem czytnika, a cyfry `0`–`9` przechodzą do 0–90%
  aktualnego bufora. Bieżący zapis realizacji:
  [AMC13-timeshift-end-na-zywo.md](AMC13-timeshift-end-na-zywo.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC13_TIMESHIFT_RADIA_2026-10-18.md`.
  Eksport fragmentów Time Shiftu pozostaje późniejszym rozszerzeniem.
- `AMC08` — **Prawdziwe OAuth i dodawanie do playlist zostały potwierdzone
  przez użytkownika; korekta mowy `Ctrl+F5` i widoczności pod `Ctrl+P`
  playlist istniejących oraz nowych jest zainstalowana w AMC Test; również
  czyszczenie migawki po ponownym logowaniu jest zbudowane i zainstalowane,
  całość czeka na ręczny odbiór NVDA; źródłowa korekta z 23.10.2026 naprawia
  jednorazowe pełne odświeżenie zapisanych podcastów i odcinków, lecz nie była
  instalowana ani uruchamiana**
  — natywne playlisty
  Spotify w AMC Test: `Ctrl+P`, `Ctrl+Shift+P`, pobranie katalogu raz na
  uruchomienie, natychmiastowa widoczność nowej playlisty i zapamiętanie
  ostatnich celów. Mechanizm ma partycje usług i kont, aby kolejne integracje
  używały tego samego kontraktu bez kopiowania kodu Spotify. Przebieg:
  `AMC08-playlisty-spotify.md`. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.
  Historyczne źródła są tylko wzorcem; kod powstaje w tym repozytorium.
- `AMC09` — **Menedżer, pierwsze rozszerzenie Konfiguruj, ujednolicone
  `Ctrl+F5`, precyzyjne nazwy dla każdej sesji oraz Foldery Biblioteki są
  zbudowane; po ręcznym wykryciu brakującego mapowania poprawiono całą rodzinę
  `F1`–`F24` i nawigację bloku numerycznego; najnowsza korekta jest
  zainstalowana i czeka na ponowny odbiór NVDA** — dostępny
  Menedżer sesji pod `Ctrl+Shift+S`, włączanie Spacją, zwarta kolejność
  `Ctrl+1–9`, zmiana kolejności `Alt+strzałkami`, stan gotowości i stała nazwa
  `Radio`. Ma działać już w AMC Test; profil publiczny będzie później filtrował
  tę samą listę przez manifest możliwości. Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.
  Automatyczne otwarcie na czystej instalacji pozostaje do odbioru AMC12 i nie
  może zmienić obecnego profilu testowego. W Plikach lokalnych `Ctrl+F5`
  otwiera teraz niedestrukcyjny menedżer dodawania, odświeżania i odłączania
  Folderów Biblioteki; pozostałe sesje zachowują własne znaczenie tego skrótu.
  Korekta z 20.10.2026 dodaje w Radiu rzeczywiste „Odśwież stacje Radia” pod
  `Ctrl+F5`, również z odtwarzacza, przy wspólnym opisie menu, pomocy i palety.
  Kod i testy kontraktu są potwierdzone. Ręczny odbiór ujawnił jednak wspólną
  przyczynę ciszy `F5` i `Ctrl+F5`: brak mapowania rzeczywistego kodu klawisza
  wxPython. Poprawka obejmuje już wszystkie klawisze funkcyjne, a nie tylko
  `F5`; testy zaczynają się od surowych zdarzeń klawiatury. Najnowsza wersja
  została zainstalowana 20.10.2026. Korekta z 21.10.2026 utrwala zasadę, że
  `Ctrl+F5` po skonfigurowaniu pokazuje stan i zapisane cele bez ponownego
  logowania lub skanowania. Audyt wykazał, że Spotify i TIDAL nadal wymagają
  domknięcia jawnego wylogowania oraz stanowych przycisków konta.
  Bieżący zapis realizacji:
  [AMC09-menedzer-sesji.md](AMC09-menedzer-sesji.md).
- `AMC12` — **Lokalny kandydat `alpha.433` przeszedł pełną regresję źródeł,
  został zbudowany i zainstalowany w `D:\Projekty Codex\AMC Public`, lecz
  decyzją użytkownika z 21.10.2026 jest wstrzymany do odbioru Smart Frontier.
  Nie uruchomiono go do odbioru, nie opublikowano i nie należy go jeszcze
  przekazywać. Dodaje ręczną kolejność Biblioteki i Ulubionych Radia:
  `Alt+strzałka góra/dół` oraz `Ctrl+X`, `Ctrl+V`, z nazwaniem stacji nad albo
  pod którą przeniesiono wybór.
  Publiczny AMC jest budowany z tego samego kodu co AMC Test; zgodnie z korektą
  użytkownika z 21.10.2026 wyłącza
  wyłącznie niedopracowane funkcje streamingowe, a wszystkie ukończone funkcje,
  w tym Sonosa, zachowuje. Obecnie TIDAL, Spotify i nieodebrana jeszcze
  integracja Frontier Smart pozostają tylko w AMC Test. Końcowa paczka
  `e6d4269d` ma 1075 plików; integralność i kontrolowany start paczki oraz
  integralność zainstalowanej kopii są zaliczone. Instalator usuwa także stare moduły niedostępnych usług
  pozostałe po wcześniejszej wersji. Najnowsza poprawka rozpoznaje ten sam plik
  w `Ctrl+O` i Bibliotece podczas `Ctrl+Shift+U`, nie przełącza folderu na pustą
  Bibliotekę oraz jasno wskazuje `Ctrl+F5`, gdy folder nie jest źródłem.
  Wcześniejsza poprawka zachowuje
  kolejność importowanej playlisty Radia, uruchamia `Alt+1–3` w Bibliotece i
  Ulubionych, wiąże `Ctrl+Shift+U` z Ulubionymi oraz `Ctrl+Shift+L` z
  członkostwem w Bibliotece. Ręczny odbiór w NVDA i decyzja o dołączeniu
  Frontier Smart pozostają do wykonania; niczego nie opublikowano** — jeden kod, jawny manifest możliwości, osobne
  katalogi, blokady, logi i kanały AMC Test oraz publicznego AMC. Bieżący zapis
  realizacji:
  [AMC12-profile-wydania-publicznego-i-testowego.md](AMC12-profile-wydania-publicznego-i-testowego.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`.
- `AMC10` — **W trakcie; zainstalowany AMC Test ma prawidłowo zapisane konto i
  działające sterowanie, grupowanie oraz treści Sonos. Polecenia idą bezpośrednio
  do Sonos Control API, natomiast broker na Hermesie obsługuje w tej instalacji
  wyłącznie logowanie i odnowienie tokenu. Niezależny broker ma czysty,
  sprawdzony pakiet Docker Compose z Caddy i własnym HTTPS, ale nie został
  jeszcze uruchomiony publicznie. Odczytowy audyt potwierdził zgodny identyfikator
  istniejącej integracji, obecność chronionego sekretu oraz działające dawne
  usługi; nie trzeba tworzyć nowej integracji ani przepisywać sterowania.
  Pakiet zawiera teraz bezprzerwową instrukcję przejścia z zachowaniem starego
  callbacku do czasu odbioru następcy. Bieżących źródeł z wyłączonym brokerem nie
  należy instalować przed zapewnieniem następcy albo bezpiecznej ciągłości
  konta autora** — działające sterowanie Sonosem i WiiM jest już przepisane i
  nie wymaga ponownej implementacji. `Ctrl+F5` wybiera dom i grupę, a przy braku
  połączenia prowadzi do konta zamiast kończyć się błędem. Okno udostępnia
  rozpoczęcie, jawne
  sprawdzenie, anulowanie i odświeżenie logowania bez przekazywania tokenów do
  Pythona i bez samoczynnego otwierania przeglądarki. Dodano wcześniej serwerowy
  kontrakt logowania, PKCE, jednorazowe sesje, odnowienie, ograniczenie tempa,
  bezpieczne logowanie oraz ścisłą obsługę zakończenia TLS przez jawnie zaufane
  reverse proxy. Do czasu prawdziwego publicznego wdrożenia przycisk logowania
  jest ukryty, stan ma jawną etykietę i nie wykonuje żądania sieciowego.
  Publiczny Sonos nadal jest ukryty.
  Bieżący zapis realizacji:
  [AMC10-logowanie-sonos-i-publiczny-broker.md](AMC10-logowanie-sonos-i-publiczny-broker.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC10_SONOS_WIIM_URUCHOMIENIE_I_UJEDNOLICENIE_2026-10-18.md`.
  Bez obecności użytkownika nie logować konta i nie sterować głośnikami.
- `AMC14` — **W trakcie; folder zawierający, argument pliku, osobny kanał
  działającej instancji i idempotentne `/kolejka` są zainstalowane w AMC Test;
  opcjonalna i odwracalna rejestracja instalatora jest rozdzielona dla AMC
  oraz AMC Test, ma
  potwierdzoną składnię, lecz nie została zastosowana w systemie** —
  aplikacyjna integracja z powłoką Windows,
  przekazywanie plików do właściwej instancji i późniejsza rejestracja przez
  instalator. Bieżący zapis realizacji:
  [AMC14-foldery-i-integracja-powloki.md](AMC14-foldery-i-integracja-powloki.md).
  Zatwierdzona specyfikacja:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC14_FOLDERY_I_INTEGRACJA_POWLOKI_2026-10-18.md`.
- `YT-001` — **W trakcie — bezpieczny fundament OAuth, lokalny odbiornik,
  transport tokenów, koordynator, odczyt, niedestrukcyjny plan oraz atomowy
  zapis subskrypcji, chroniony protokół hosta i osobne magazyny poświadczeń
  AMC Test/AMC są zbudowane i obecne niewidocznie w AMC Test; brak
  identyfikatora aplikacji Google i interfejsu wx** — oficjalne logowanie do
  konta YouTube, synchronizacja subskrypcji i zwykłych playlist oraz bezpieczny
  zakres czynności konta. Etap rozpoczęto 21 października 2026 na nowe jawne
  polecenie użytkownika; nic nie loguje konta ani nie otwiera przeglądarki.
  Szczegóły:
  [YT-001-konto-youtube-i-synchronizacja.md](YT-001-konto-youtube-i-synchronizacja.md).
- `NAME-001` — **Kod, testy, paczka, instalacja i uruchomienie AMC Test gotowe;
  bez nowego instalatora AMC Public** —
  krótkie nazwy `AMC Test — data, godzina` i `AMC Public — data, godzina`,
  z technicznymi identyfikatorami pozostawionymi poza zwykłą nazwą.
  Szczegóły: [NAME-001-amc-test.md](NAME-001-amc-test.md).
- `FRONTIER-001` — **Poprawka po trzecim odbiorze NVDA została zbudowana,
  zainstalowana i uruchomiona w zbiorczym AMC Test; czeka na ponowny odbiór
  `Ctrl+8`, automatycznego wykrywania, fokusu i komunikatu przed PIN-em** — pusta sesja automatycznie szuka pierwszego urządzenia
  FSAPI/UNDOK. Po zapisaniu urządzenia `Ctrl+F5` pokazuje listę bez ponownego
  skanowania, a osobny przycisk pozwala szukać nowych urządzeń; ręczny adres
  jest opcją awaryjną. Bezpieczny PIN, transport, tryby i presety pozostają
  dostępne wyłącznie w AMC Test.
  Szczegóły:
  [FRONTIER-001-frontier-smart-fsapi.md](FRONTIER-001-frontier-smart-fsapi.md).
- `ARC-001` — **Oczekuje** — wspólny rdzeń poleceń dla GUI, palety, NVDA,
  przyszłego CLI i lokalnego sterowania AI. Szczegóły:
  [ARC-001-wspolny-rdzen-polecen-cli-ai.md](ARC-001-wspolny-rdzen-polecen-cli-ai.md).
- `MAC-001` — **Oczekuje, odłożone bez terminu** — ewentualna ocena portu AMC
  na macOS dopiero po wydaniu Windows i wyłącznie na nowe jawne polecenie.
  Szczegóły:
  [MAC-001-port-macos-wxpython-litehost.md](MAC-001-port-macos-wxpython-litehost.md).
- `LIC-001` — **Oczekuje** — Radio Browser, licencja BASS i bezpieczna decyzja
  o dobrowolnych wpłatach. Szczegóły:
  [LIC-001-radio-browser-bass-darowizny.md](LIC-001-radio-browser-bass-darowizny.md).
- `REL-001` — **W trakcie; lokalny formularz, klient HTTPS, Worker i samodzielna
  bramka wdrożenia są gotowe; nieaktywny bootstrap istnieje, a aktywacja czeka
  na subdomenę `workers.dev`, osobny token GitHuba i odbiór** — menu, F1 i
  paleta prowadzą do dostępnego formularza z pełnym
  podglądem, domyślnie wyłączonym logiem, redakcją danych oraz kopiowaniem lub
  atomowym zapisem w magazynie profilu. Po zweryfikowanym endpointcie ten sam
  formularz wysyła dokładnie widoczny raport w tle. Worker ma drugą redakcję,
  limit, idempotencję i rozdziela prywatną treść od publicznego issue; nie
  został wdrożony wyłącznie jako bootstrap bez sekretu i nie utworzył
  prawdziwego zgłoszenia. Zależności
  Workera są przypięte, a skrypt wdrożenia wykonuje testy oraz dwa pakowania
  `--dry-run`. Jawny bootstrap przygotowuje migrację Durable Object bez sekretu,
  ustawienie tokenu i właściwe wdrożenie są osobnymi etapami, a skrypt nigdy sam
  nie rozpoczyna logowania. Sesja Cloudflare jest potwierdzona. Prywatne
  repozytorium intake i wymagane etykiety są już utworzone. Lokalna bramka
  publikacji instalatora sprawdza profil, rewizję, rozmiar, SHA-256 i wynik
  odczytany z GitHuba, ale bez jawnego `-Publish` niczego nie wysyła. Czysta
  publiczna linia źródeł powstaje jako lokalny snapshot identycznego drzewa,
  bez publikowania roboczej historii i bez przełączania bieżącej gałęzi.
  Szczegóły:
  [REL-001-github-aktualizacje-sygnalista.md](REL-001-github-aktualizacje-sygnalista.md).
- `STR-001` — **Oczekuje** — osobne laboratorium TIDAL i Apple Music, najpierw
  badanie oficjalnych API i warunków, później ewentualny profil testowy.
  Szczegóły:
  [STR-001-tidal-apple-music-laboratorium.md](STR-001-tidal-apple-music-laboratorium.md).

## Krótkie polecenia użytkownika

Wystarczy powiedzieć na przykład: `Uruchom zadanie NVDA-001`. Agent ma wtedy
odczytać rejestr oraz właściwy plik i wykonać wyłącznie wskazane zadanie.
