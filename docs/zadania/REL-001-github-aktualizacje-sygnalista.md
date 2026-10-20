# REL-001 — GitHub Releases, aktualizacje i Sygnalista

- Status: `W trakcie — transport i Worker gotowe lokalnie; czekają na infrastrukturę i odbiór`
- Utworzono: 18 października 2026
- Obszar: wydania, aktualizator i dostępne zgłoszenia
- Polecenie uruchamiające: `Uruchom zadanie REL-001`
- Roboczy opis pierwszego wydania:
  [REL-001-opis-pierwszego-wydania-publicznego-roboczy.md](REL-001-opis-pierwszego-wydania-publicznego-roboczy.md).

## Cel

Po przygotowaniu pierwszego publicznego instalatora połączyć jeden kontrolowany
proces: oznaczony kod w GitHubie, wydanie GitHub Releases, manifest aktualizacji
oraz dostępne zgłaszanie błędów bez wymagania konta GitHub od użytkownika.

## Zatwierdzony kierunek

- GitHub jest źródłem kodu, tagów, opisów zmian i gotowych wydań.
- `AMC-Python-Updater.exe` pozostaje wykonawcą transakcyjnej podmiany. Moduł
  internetowy jedynie sprawdza podpisany lub jednoznacznie zweryfikowany
  manifest, pobiera właściwy pakiet i przekazuje go aktualizatorowi.
- Kanał testowy i publiczny mają osobne manifesty. Aktualizacja nigdy nie
  zamyka AMC podczas nagrywania i nie instaluje niesprawdzonego pliku.
- Formularz `Zgłoś błąd lub sugestię` korzysta z idei Sygnalisty Michała
  Dziwisza: aplikacja wysyła zatwierdzony raport do Cloudflare Workera, a
  Worker tworzy issue w repozytorium AMC. Użytkownik nie potrzebuje konta
  GitHub.

## Wynik porównania zewnętrznego projektu

Sprawdzono projekt `michaldziwisz/sygnalista` z 18 października 2026:

- licencja MIT pozwala użyć i zmodyfikować kod z zachowaniem informacji
  licencyjnej;
- endpoint `POST /v1/report` przyjmuje rodzaj, tytuł, opis, wersję, kanał,
  diagnostykę oraz opcjonalny skompresowany log;
- pełny raport i log mogą trafić do prywatnego repozytorium `support-intake`,
  a publiczne issue dostaje etykietę `bug` lub `enhancement` oraz `from-app`;
- mapowanie aplikacji, token aplikacji, limity rozmiaru i tempo żądań są
  konfigurowane w Workerze;
- rozwiązanie jest wzorcem i możliwym składnikiem, ale AMC potrzebuje własnej
  polityki prywatności, filtrowania danych i testów nadużyć.

## Zakres formularza AMC

- Typ: błąd albo sugestia.
- Krótki tytuł, opis i opcjonalne kroki odtworzenia.
- Automatycznie: wersja AMC, commit, kanał wydania, wersja Windows, rodzaj
  aktywnej sesji i wersje składników — bez nazw prywatnych plików i bez danych
  kont.
- Log jest domyślnie wyłączony. Przed wysłaniem użytkownik może zobaczyć
  dokładny raport, usunąć log i zatwierdzić operację.
- Po powodzeniu aplikacja podaje numer zgłoszenia i umożliwia skopiowanie
  adresu. Nie otwiera wbudowanej przeglądarki.

## Przejście zgłoszeń do pracy

Sygnalista już tworzy zwykłe GitHub Issues, więc dalszy proces może być
automatyzowany bez przepisywania danych:

1. etykiety `bug`, `enhancement` i `from-app` rozdzielają kolejkę;
2. dodatkowe etykiety AMC określają sesję i wydanie testowe lub publiczne;
3. po weryfikacji zgłoszenia tworzymy albo wskazujemy zadanie w
   `docs/zadania`, zachowując numer issue;
4. Codex lub Hermes może później analizować wybrane issue wyłącznie na jawne
   polecenie użytkownika; samo nadejście raportu nie uruchamia zmian kodu.

## Kolejność wdrożenia

1. Repozytorium i model wersji.
2. Powtarzalne wydanie GitHub Releases z manifestem i sumą SHA-256.
3. Internetowe sprawdzanie aktualizacji oraz bezpieczne przekazanie paczki do
   istniejącego aktualizatora.
4. Własna instancja Workera Sygnalisty i prywatne repo raportów.
5. Dostępny formularz AMC, filtrowanie danych, testy NVDA, brak sieci,
   ponowienie, limit i odrzucenie zbyt dużego logu.

## Podział umożliwiający wcześniejszą pracę

Po przygotowaniu lokalnego instalatora wolno wdrożyć bez połączenia z usługą:

- dostępny formularz błędu lub sugestii;
- jawny podgląd całego raportu i domyślnie wyłączony log;
- filtrowanie ścieżek, nazw prywatnych plików, adresów, tokenów i danych kont;
- wspólny kontrakt transportu z atrapą sukcesu, błędu, braku sieci, limitu i
  zbyt dużego raportu;
- możliwość skopiowania albo zapisania zatwierdzonego raportu lokalnie, gdy
  prawdziwy serwer nie jest jeszcze skonfigurowany;
- testy NVDA fokusa, ponownego otwarcia, podglądu, Anuluj i Wyślij.

Nie wolno przed etapem GitHub uznawać wysyłania za działające, osadzać tokenu,
stawiać publicznego Workera ani tworzyć prawdziwych Issues. Wdrożenie Workera,
prywatnego repozytorium raportów, mapowania etykiet i końcowego endpointu
pozostaje częścią tego samego REL-001, wykonywaną razem z zatwierdzonym
repozytorium, kanałami wydań i polityką prywatności.

## Korekty użytkownika

- 19 października 2026: użytkownik polecił kontynuować lokalny fundament
  Sygnalisty, a integrację GitHub wykonać później. To doprecyzowuje wcześniejszą
  kolejność: bieżący etap nie wdraża Workera, tokenu, GitHub Issues ani
  publikacji, lecz przygotowuje bezpieczny formularz, redakcję i kontrakt
  transportu.
- 20 października 2026: użytkownik polecił dokończyć internetową część
  Sygnalisty przed pierwszym publicznym wydaniem. To zastępuje wcześniejsze
  odłożenie kodu Workera, ale nie jest zgodą na publikację AMC bez odbioru ani
  na pozorowane wdrożenie bez konta Cloudflare, prywatnego repozytorium i
  końcowego HTTPS. Kod klienta i Workera wolno przygotować oraz testować na
  atrapach; prawdziwy endpoint musi przejść osobny odbiór.

## Materiał do dokumentacji użytkownika

- Polecenie `Zgłoś błąd lub sugestię…` znajduje się w menu `Pomoc` i w
  palecie `Ctrl+Shift+K`. Pełna pomoc F1 pokazuje je jako polecenie bez
  przypisanego skrótu.
- Formularz pozwala wybrać `Błąd` albo `Sugestia`, wpisać tytuł, opis i
  opcjonalne kroki odtworzenia. Początkowy fokus trafia do pola tytułu, a
  wszystkie pola i wybory mają jawne etykiety dla czytnika ekranu.
- Cały raport jest widoczny w polu `Pełny podgląd zredagowanego raportu`.
  Dokładnie ten tekst jest kopiowany do schowka, zapisywany lokalnie albo —
  po skonfigurowaniu serwera — wysyłany.
- Log jest domyślnie wyłączony. Po świadomym włączeniu dołączany jest tylko
  ograniczony ogon dziennika po redakcji danych prywatnych.
- Raport może zostać skopiowany albo zapisany atomowo w osobnym folderze
  zgłoszeń bieżącego profilu. AMC Test i publiczny AMC nie współdzielą żywego
  folderu raportów.
- Gdy wydanie nie ma zweryfikowanego endpointu, formularz uczciwie pozostaje
  w trybie lokalnym i nie pokazuje martwego przycisku. Po wpisaniu końcowego
  endpointu HTTPS pojawia się `Wyślij zgłoszenie`; w trakcie pracy przycisk
  jest wyłączony, NVDA słyszy `Wysyłanie zgłoszenia`, a po sukcesie numer issue
  i przycisk `Skopiuj adres zgłoszenia`. AMC nie otwiera przeglądarki.

## Uzasadnienie i decyzje

- Jedna funkcja przygotowuje zredagowaną treść używaną przez podgląd,
  schowek, zapis i przyszły transport. Dzięki temu późniejsza wysyłka nie może
  dostać innego raportu niż tekst zatwierdzony przez użytkownika.
- Redakcja usuwa między innymi ścieżki lokalne i sieciowe, nazwy plików
  multimedialnych i diagnostycznych, adresy WWW i e-mail, adresy IP i MAC,
  identyfikatory, nagłówki autoryzacji, tokeny, hasła oraz nazwy kont.
- Odczyt logu jest ograniczony do ostatnich 512 KiB, najwyżej 200 wierszy i
  64 KiB zredagowanej treści. Cały raport ma bramkę 256 KiB przed przyszłą
  wysyłką.
- Kontrakt transportu rozróżnia sukces, brak konfiguracji, brak sieci,
  ograniczenie tempa, zbyt duży raport i pozostały błąd. Bieżący transport
  lokalny zawsze zwraca uczciwy stan `nieskonfigurowane` i nie używa sieci.
- Internetowy klient przyjmuje tylko prosty adres HTTPS bez danych logowania,
  parametrów i fragmentu. Wysyła widoczny raport w wątku roboczym, nie zawiera
  tokenu GitHuba i nie ponawia automatycznie niepewnego żądania.
- Każda wersja treści ma losowy identyfikator raportu. Ponowienie niezmienionej
  treści zachowuje identyfikator, a edycja przydziela nowy. Worker przechowuje
  etap realizacji w Cloudflare KV: ten sam raport zwraca istniejące issue,
  inna treść z tym samym identyfikatorem jest odrzucana.
- Worker ponownie redaguje dane, ogranicza wielkość i tempo żądań, zapisuje
  pełną treść w prywatnym repozytorium intake, a w publicznym AMC tworzy tylko
  krótki wpis. Sekret GitHuba występuje wyłącznie jako sekret Workera.
- Własna domena nie jest wymagana: zatwierdzona konfiguracja używa HTTPS pod
  `workers.dev`, wymaga sekretu `GITHUB_TOKEN`, KV i limitera. Logowanie
  urządzeniem może wypisać adres i kod bez otwierania przeglądarki, a dane OAuth
  na Windows mają być przechowywane w systemowym magazynie poświadczeń.
- Publikacja instalatora ma osobną bramkę PowerShell. Domyślny przebieg tylko
  sprawdza profil `public`, wersję, nazwę, rozmiar, SHA-256 i pełną rewizję
  źródeł oraz przygotowuje opis i manifest gotowości. Dopiero jawne `-Publish`
  może utworzyć wydanie; wymaga czystych śledzonych źródeł i obecności rewizji
  instalatora na GitHubie, nie zastępuje istniejącego tagu i odczytowo
  potwierdza oba przesłane pliki oraz sumę w opisie.
- Polecenie korzysta ze wspólnego modelu akcji dla menu, F1, palety i
  wykonania oraz jest jawnie dostępne we wszystkich sesjach i obu profilach.
- Możliwość lokalnego formularza jest częścią zamkniętego manifestu zarówno
  Python, jak i uruchamiacza .NET. Rozbieżność tych list zatrzymuje testy przed
  instalacją zamiast tworzyć paczkę, której uruchamiacz później odmówi.

## Testy i wynik

- `8 passed` — ukierunkowane testy `test_problem_report.py`: redakcja danych,
  log domyślnie wyłączony, ograniczony ogon logu, atomowy zapis dokładnego
  podglądu, wszystkie stany kontraktu transportu, zgodność menu/palety/F1/
  wykonania, oba profile i kontrakt dostępnego dialogu.
- `119 passed, 1 failed` — regresje katalogu poleceń, profili, skrótów i menu.
  Jedyny błąd to zastana kolizja litery dostępu `Z` w menu `Pliki`; nowy wpis
  znajduje się w menu `Pomoc` i tej kolizji nie tworzy ani nie zmienia.
- `py_compile` zmienionych modułów i testu: zaliczony.
- Nie wykonano pełnej kompilacji, instalacji ani uruchomienia AMC, ponieważ
  użytkownik w tym czasie testuje bieżącą instalację.
- Ręczny odbiór NVDA — pierwszy fokus, poruszanie się, Anuluj, ponowne
  otwarcie, schowek i zapis — pozostaje do wykonania po instalacji przyszłej
  paczki.
- Pierwsza zbiorcza paczka zawierająca Sygnalistę została poprawnie odrzucona
  przed instalacją, ponieważ uruchamiacz .NET nie znał jeszcze możliwości
  `problem-report-local`. Wszystkie sumy plików startowych były zgodne.
  Kontrakt .NET uzupełniono, a test profili porównuje odtąd pełne listy
  możliwości obu implementacji. Wtedy wymagane było ponowne zielone pakowanie.
- Powtórzona pełna bramka: **1831 zaliczonych, 110 pominiętych i 11
  podtestów**. Paczka 1665 plików przeszła kontrolę profilu, manifest i
  SHA-256; AMC Test z lokalnym formularzem zostało zainstalowane i uruchomione.
  Ręczny odbiór NVDA formularza nadal pozostaje otwarty.
- Internetowy etap z 20 października: **20 zaliczonych testów Python**
  (`test_problem_report.py` i `test_async_gate.py`) oraz **8 zaliczonych testów
  Node Workera**. Sprawdzono dokładną treść żądania bez sekretu, wyłącznie
  HTTPS, brak sieci, limit, rozmiar, uszkodzoną odpowiedź, drugą redakcję,
  prywatne i publiczne issue na atrapach, idempotencję, konflikt treści,
  częściową awarię i brak wycieku błędu GitHuba.
- Kod Workera nie został wdrożony, nie połączono prawdziwego tokenu i nie
  utworzono próbnego GitHub Issue. To są testy kodu i atrap, nie odbiór sieci.
- Utworzono prywatne repozytorium `michalkasperczak/amc-support-intake`.
  Odczyt zwrotny GitHuba potwierdził `PRIVATE`, włączone Issues i etykiety
  `bug`, `enhancement`, `from-app`. Publiczne repozytorium AMC również ma
  `from-app`. Nie utworzono żadnego issue.
- Zmiana internetowa nie została zbudowana ani zainstalowana, ponieważ bramka
  bezpieczeństwa wykazała aktywne nagrywanie w AMC Test. Nie przerwano go.
- Testy skryptu pierwszego publicznego wydania: **3 zaliczone** — poprawne
  przygotowanie bez publikacji oraz odmowa profilu testowego i zmienionej sumy.
  Istniejący instalator `alpha.424` przeszedł dodatkowo rzeczywistą kontrolę
  rozmiaru i SHA-256; powstał lokalny opis oraz manifest gotowości z polem
  `published: false`. Niczego nie wysłano na GitHub.

## Znane ograniczenia

- Jest gotowy kod internetowego transportu i Workera, ale nie ma jeszcze
  wdrożonego Workera, prawdziwego endpointu, Cloudflare KV, limitera ani
  prywatnego repozytorium raportów. Dlatego zbudowane obecnie wydanie nadal
  pozostaje w trybie lokalnym i nie tworzy GitHub Issues.
- Prawdziwe uruchomienie wymaga świadomego logowania do właściwego konta
  Cloudflare, utworzenia prywatnego `amc-support-intake`, etykiet, ograniczonego
  tokenu GitHuba w sekrecie Workera i kontrolowanego raportu próbnego.
- Zapisany raport pozostaje plikiem lokalnym; AMC nie otwiera przeglądarki.
- Filtry prywatności mają charakter ostrożny i mogą usunąć z logu więcej
  tekstu niż bezwzględnie konieczne.
- Bieżąca zmiana jest zainstalowana w AMC Test, lecz nie ma jeszcze odbioru
  formularza z NVDA ani internetowego transportu.

## Porządek dysku

- Po testach usunięto osiem odtwarzalnych plików `.pyc` utworzonych w
  `D:\Projekty Codex\AMC - integracja wxPython\wxlite\amc_wx_lite\__pycache__`
  oraz `D:\Projekty Codex\AMC - integracja wxPython\wxlite\tests\__pycache__`.
  Odzyskano 1 600 458 bajtów, około 1,53 MiB. Pliki nie wymagają odzyskania,
  ponieważ Python utworzy je ponownie przy następnym uruchomieniu.
- Zachowano jedyną zweryfikowaną paczkę publiczną, instalator, całe zastane
  `.test-output` i `.test-tmp`, źródła, dokumentację, ustawienia oraz dane
  użytkownika.

## Wersja i commit

- Wersja źródeł: `0.1.0`, profile `AMC Test` i `AMC`.
- Commit implementacji: `f2e310fc` (`feat(rel): dodaj lokalny fundament
  sygnalisty`).
- Ujednolicenie możliwości profili Python–.NET: `fb9ba25f` —
  `fix(rel): ujednolić możliwości profili launchera`.
- Internetowy klient i lokalnie testowalny Worker: `d9426684` —
  `feat(rel): przygotuj internetowego Sygnaliste`.
- Bezpieczna bramka publikacji publicznego instalatora: `61837b26` —
  `feat(rel): dodaj bezpieczna publikacje instalatora`.
- Druga redakcja serwerowa ścieżek, przypisań tokenów i kont,
  identyfikatorów oraz nazw plików: `8149d076` —
  `fix(rel): wzmocnij redakcje Workera`.
- Wymagany sekret, `workers.dev`, systemowy magazyn logowania i ochrona plików
  lokalnych: `94d6a0f7` — `fix(rel): utwardz wdrozenie Workera`; 8/8 testów
  Workera zaliczone.
- Instalacja: `2026.10.19-fb9ba25fe0680cf7bf5435d53eb5b073de091cca-0debb6aa`;
  manifest 1665 plików, pełna integralność i uruchomienie zweryfikowane.
- Publikacja: nie wykonano.

## Poza zakresem

- Publikacja obecnego stanu bez osobnej decyzji użytkownika.
- Wysyłanie logów, adresów stacji, historii lub danych kont bez podglądu i
  zgody.
- Automatyczne wdrażanie poprawek na podstawie samego zgłoszenia.
- Instalowanie lub utrzymywanie zewnętrznej aplikacji Michała Dziwisza.

## Wynik wykonania

- Data lokalnego etapu: 19–20 października 2026.
- Repozytorium i kanały: profile i kanały są rozdzielone przez AMC12. GitHub
  został użyty wyłącznie do utworzenia i zweryfikowania prywatnego repozytorium
  intake oraz etykiet; nie wysłano kodu, instalatora, wydania ani zgłoszenia.
- Kontrakt Workera: `POST /v1/report`, schemat 1; adres końcowy nadal brak,
  ponieważ infrastruktura nie została wdrożona.
- Testy aktualizacji: poza zakresem tego etapu.
- Testy prywatności: zaliczone na poziomie kodu; ręczny NVDA po instalacji.
- Wydanie: nie utworzono i nie opublikowano.

