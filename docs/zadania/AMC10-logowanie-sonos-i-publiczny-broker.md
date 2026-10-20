# AMC10 — proste logowanie Sonos i publiczny broker

## Status

**W trakcie — niezależny broker ma gotowy i sprawdzony pakiet wdrożeniowy
Docker Compose z własnym HTTPS, ale nie został jeszcze uruchomiony na publicznym
serwerze. Bieżące źródła AMC Test są odłączone od Hermesa i pozostają w
bezpiecznym stanie „publiczny broker nieskonfigurowany”. Publiczny serwer,
dane integracji Sonos, instalacja klienta oraz odbiór z zewnętrznym kontem
pozostają bramą.**

Sterowanie Sonosem i WiiM było już przeszczepione i użytkownik ocenił je jako
prawie gotowe. Ten etap nie zmienia adapterów, list, transportu ani WiiM.

## Korekty użytkownika

- 2026-10-18: ustalenie, że Sonos i WiiM już działają; zastępuje wcześniejsze
  szerokie rozumienie AMC10. Zakres to wyłącznie proste logowanie Sonos i
  publiczny broker.
- 2026-10-19: użytkownik polecił kontynuować broker podczas ręcznego testowania
  AMC. Nie zezwala to na otwieranie przeglądarki, logowanie konta ani wysyłanie
  poleceń do głośników.
- 2026-10-20: użytkownik wskazał Sonosa jako wcześniejszą bramę do publicznego
  instalatora. Zastępuje to późniejszą kolejność AMC10, ale nie znosi bramy
  prawdziwej domeny, danych integracji, odbioru na zewnętrznym koncie ani
  osobnej zgody na publikację w GitHubie.
- 2026-10-20: użytkownik potwierdził, że bieżący publiczny kandydat ma pozostać
  czysty, bez Spotify i TIDAL-a, a logowanie Sonos oraz `Ctrl+F5` należy najpierw
  dopracować w AMC Test i dopiero po odbiorze podpiąć do profilu publicznego.
  Zastępuje to ewentualne bezpośrednie odsłonięcie Sonosa w obecnym instalatorze.
- 2026-10-20: późniejsza kontrola dziennika zastępuje roboczą diagnozę, według
  której zakończony harmonogram pozostawił fałszywy stan nagrywania. Harmonogram
  z 12:30 zakończył plik o 12:35, ale równolegle trwały cztery prawdziwe
  nagrania rozpoczęte około 10:25–10:33. Zakończyły się dopiero około 12:51,
  dlatego odmowa zamknięcia była prawidłowa.
- 2026-10-20: użytkownik polecił dalej dopracowywać Sonosa w AMC Test, ale nie
  budować teraz następnego publicznego instalatora. Nowy publiczny kandydat ma
  powstać dopiero po domknięciu kolejnych funkcji. Zastępuje to przebudowywanie
  profilu publicznego po każdej małej korekcie.
- 2026-10-20: po potwierdzeniu działania Spotify i poprawki wyszukiwania
  użytkownik polecił wrócić do Sonosa. Odczyt Hermesa wykazał działający host
  HTTPS, ale brak usługi brokera. AMC rozróżnia teraz ten stan od uszkodzonej
  odpowiedzi i nie ujawnia użytkownikowi adresu ani treści odpowiedzi serwera.
- 2026-10-20: użytkownik doprecyzował, że obecna architektura Sonosa **nie
  bazuje na Hermesie i nie ma z nim związku**. To ustalenie zastępuje wcześniejszy
  roboczy plan uruchomienia brokera na Hermesie. Wykonany odczyt hosta i lokalny
  ZIP pozostają wyłącznie historycznym śladem eksperymentu; nie są celem
  wdrożenia. Docelowym elementem jest niezależny, wspólny publiczny broker HTTPS.
- 2026-10-20: kontrola źródeł po tej korekcie wykazała pozostały stały origin
  Hermesa w konfiguracji klienta. Został usunięty z aktywnej ścieżki AMC Test.
  Zastępuje go nierutowalny znacznik konfiguracyjny oraz jawna bramka
  dostępności. Nie jest to nowy adres usługi ani próba połączenia.
- 2026-10-20: użytkownik polecił wdrażać niezależny broker i wskazał Lyd jako
  przykład innej aplikacji Sonos, zaznaczając, że prawdopodobnie nie jest ona
  open source. Lyd jest wyłącznie porównaniem użytkowym; nie kopiujemy jego
  kodu ani nie opieramy architektury AMC na przypuszczeniach o zamkniętej
  implementacji. Obowiązującym kontraktem są oficjalne wymagania Control API.
- 2026-10-20: użytkownik potwierdził, że wcześniej logował się do portalu Sonos
  prawdopodobnie kontem Google i tworzył integrację, oraz zezwolił sprawdzić
  historyczny AMC. Audyt tylko do odczytu potwierdził prawdziwy zapis konta
  Sonos z 19 października. Nie oznacza to zgody na ujawnienie lub przesłanie
  sekretu w rozmowie; należy go odnaleźć i przenieść wyłącznie chronionym
  kanałem wdrożeniowym.

## Materiał do dokumentacji użytkownika

W AMC Test polecenie „Konfiguruj…” w Menedżerze sesji otwiera okno „Konto
Sonos”. Pokazuje ono wyłącznie informacje potrzebne użytkownikowi i przyciski
właściwe dla bieżącego stanu: rozpoczęcie i sprawdzenie logowania, anulowanie,
odświeżenie dostępu, ponowienie zapisu, wylogowanie oraz przejście do listy
głośników i grup. Hasło podaje się tylko na oficjalnej stronie Sonosa.

„Rozpocznij logowanie” przygotowuje adres. AMC nie otwiera wtedy przeglądarki
samoczynnie: adres można skopiować albo jawnie wybrać „Otwórz stronę
logowania”. Po ukończeniu logowania użytkownik wraca do okna i wybiera
„Sprawdź logowanie”. `Ctrl+F5` nadal oznacza „Głośniki i grupy Sonos”. Gdy konto
jest połączone, otwiera wybór domu i grupy; gdy konto nie jest gotowe, prowadzi
do okna konta zamiast kończyć się niejasnym błędem.

Po otwarciu okna konta AMC jawnie wypowiada aktualny stan Sonosa, mimo że fokus
trafia na przycisk. Gdy `Ctrl+F5` wykryje już połączone konto, mówi „Konto
Sonos jest połączone. Wczytuję głośniki i grupy”, a następnie otwiera listę.
Nie uruchamia ponownie logowania i nie wysyła polecenia do głośnika.

Jeżeli skonfigurowany host odpowiada, ale nie ma pod nim uruchomionej usługi
logowania AMC, po wybraniu „Rozpocznij logowanie” program mówi: „Usługa
logowania Sonos nie jest uruchomiona pod skonfigurowanym adresem”. Ten stan
nie jest mylony z odmową Sonosa ani z oczekiwaniem na przeglądarkę.

W bieżących źródłach, dopóki niezależny publiczny broker nie zostanie naprawdę
skonfigurowany, okno „Konto Sonos” mówi: „Publiczna usługa logowania Sonos nie
jest jeszcze skonfigurowana w tej wersji AMC”. Przycisk rozpoczęcia logowania
nie jest wtedy pokazywany, a początkowy fokus trafia na „Zamknij”. Program nie
otwiera przeglądarki i nie wykonuje żądania sieciowego. To zachowanie nie jest
jeszcze zainstalowane w użytkowym AMC Test.

Wydanie publiczne nie będzie wymagało od zwykłego użytkownika własnego klucza,
sekretu ani serwera. Użytkownik wybierze logowanie, otrzyma adres oficjalnej
strony Sonosa, zaloguje się tam i wróci do AMC, aby sprawdzić wynik. Sekret
integracji pozostaje tylko na wspólnym serwerze AMC.

Istniejące konto autora było wcześniej prawidłowo połączone z Sonosem, ale jego
zaszyfrowany rekord jest przypisany do historycznego originu. Po uruchomieniu
nowego publicznego brokera AMC poprosi autora o świeże, świadome logowanie.
Nie będzie po cichu przepisywać starego tokenu ani udawać, że należy on do
nowego serwera.

AMC nie zna i nie przechowuje sekretu integracji Sonos. Tokeny użytkownika
pozostają wyłącznie w procesie C# i w istniejącym lokalnym magazynie chronionym
systemem Windows; interfejs wxPython otrzymuje tylko stan, komunikaty i zaufany
adres autoryzacji.

Publiczny Sonos nie jest jeszcze widoczny. Pozostanie ukryty, dopóki broker nie
będzie działał pod stałym adresem HTTPS i nie przejdzie świadomego odbioru na
zewnętrznym koncie. Broker nie będzie usługą Hermesa. WiiM nie zależy od tego
brokera.

## Uzasadnienie i decyzje

- Zachowano istniejący kontrakt klienta AMC:
  `POST /login/start`, `GET /login/callback`, `POST /login/result` i
  `POST /login/refresh`.
- Sekret Sonosa jest wyłącznie zmienną środowiskową serwera. Nie trafia do
  źródeł, instalatora, adresu przeglądarki ani aplikacji użytkownika.
- Każdy start używa osobnego losowego `state` oraz wyzwania PKCE. Callback może
  rozpocząć wymianę kodu tylko raz, a tokeny można odebrać tylko raz po
  przedstawieniu właściwego verifiera.
- Sesje żyją dziesięć minut i są trzymane tylko w pamięci. Restart unieważnia
  rozpoczęte logowanie zamiast zapisywać tokeny na serwerowym dysku.
- Broker ma ograniczenie tempa per adres i ścisły limit aktywnych sesji.
- Wyłączono informacyjne logi HTTP zawierające query string callbacku, ponieważ
  znalazłyby się tam krótkotrwały kod Sonosa i `state`.
- Produkcja wymaga HTTPS. Reverse proxy może zakończyć TLS tylko wtedy, gdy
  jego konkretny adres IP znajduje się w `SONOS_TRUSTED_PROXIES`. Bez tej
  wartości broker ignoruje `X-Forwarded-For` i `X-Forwarded-Proto`; nie ufa
  nagłówkom przesłanym bezpośrednio przez publicznego klienta.
- Przyjęto najwyżej jeden krok przekazania i najwyżej 16 dokładnych adresów IP.
  Nazwy hostów, zakresy CIDR, adresy ogólne oraz puste elementy zatrzymują start
  zamiast przypadkowo poszerzać zaufanie.
- Publiczny profil AMC nadal nie udostępnia Sonosa. W czasie rozwoju adres
  klienta pozostaje konfigurowalny, lecz wydanie ma używać jednego zaufanego,
  publicznego brokera. Zwykły użytkownik nie podaje identyfikatora klienta,
  sekretu ani własnego serwera. Przełączenie originu nastąpi dopiero po
  rzeczywistym publicznym wdrożeniu i odbiorze.
- Nie zmieniono znaczenia `Ctrl+F5` ani istniejącego transportu Sonosa. Dodano
  jedynie świadomą bramkę konta przed odczytem grup. Nazwa, skrót, opis, menu,
  pomoc `Ctrl+F1`, pełna pomoc i paleta `Ctrl+Shift+K` nadal pochodzą ze
  wspólnego katalogu poleceń.
- Host udostępnia wxPythonowi siedem wąskich operacji konta bez argumentów
  poświadczeń: stan, rozpoczęcie, sprawdzenie i anulowanie logowania,
  odświeżenie, ponowienie samego zapisu oraz wylogowanie. Odpowiedzi nie
  zawierają tokenów, sekretu, adresu brokera, nazw klas ani wartości enumów.
- `404` z punktu rozpoczęcia logowania nie jest prawidłową odpowiedzią
  brokera. Oznacza, że pod zaufanym hostem nie działa usługa AMC, dlatego ma
  osobny stały komunikat. Treść HTML lub JSON odpowiedzi nie jest cytowana.
- Sama wartość adresu w modelu nie może włączać logowania. Program przekazuje
  do hosta osobną informację o dostępności publicznego brokera. Gdy jest
  wyłączona, stan konta, próba logowania oraz odczyt celów kończą się lokalnym,
  użytkowym komunikatem przed wykonaniem jakiegokolwiek żądania HTTP.
- Nierutowalna domena `.invalid` jest wyłącznie bezpiecznym znacznikiem
  konfiguracji. Zostanie zastąpiona prawdziwym publicznym originem dopiero razem
  z wdrożeniem, konfiguracją Sonosa i odbiorem. Historyczne poświadczenia
  powiązane z innym originem nie są automatycznie używane ani migrowane.
- Wybrano przenośny wariant jednej stale działającej instancji Linux:
  Docker Compose uruchamia broker w prywatnej sieci, a Caddy wystawia wyłącznie
  porty 80 i 443 oraz automatycznie obsługuje certyfikat. Stałe adresy prywatne
  pozwalają brokerowi ufać dokładnie jednemu reverse proxy, a nie całej sieci.
- Obecny pamięciowy magazyn dziesięciominutowych prób logowania wyklucza hosting
  zasypiający lub skalujący usługę do zera. Restart bezpiecznie unieważnia próbę,
  ale nie może następować między rozpoczęciem logowania i callbackiem.
- Sekret może być podany z chronionego pliku `SONOS_CLIENT_SECRET_FILE`.
  Jednoczesna wartość i plik, względna ścieżka, brak pliku, nadmierny rozmiar
  albo wielowierszowa zawartość zatrzymują start bez ujawnienia sekretu.
- Historyczny AMC i bieżący AMC Test używają tego samego publicznego
  identyfikatora integracji
  `b051a8f0-499c-4deb-9f66-843a752c36e4`. Identyfikator nie jest sekretem.
  Historyczna dokumentacja wskazuje źródła dawnego brokera pod
  `/home/michal/projekty/amc-sonos-auth` oraz konfigurację produkcyjną pod
  `/etc/amc-sonos-auth/sonos.env`; tych danych nie znaleziono lokalnie na
  komputerze Windows.
- Token użytkownika i sekret integracji są różnymi danymi. Zaszyfrowany plik
  Windows potwierdza udane logowanie użytkownika, ale nie zawiera i nie może
  zastąpić serwerowego `SONOS_CLIENT_SECRET`.

Kontrakt sprawdzono 2026-10-19 z aktualną oficjalną dokumentacją Sonosa:

- `https://docs.sonos.com/docs/authorize`;
- `https://docs.sonos.com/reference/create-authorization-code`;
- `https://docs.sonos.com/reference/refreshtoken`.

## Zmienione pliki

- `src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj`
- `src/AccessibleMediaController.SonosBroker/Program.cs`
- `src/AccessibleMediaController.SonosBroker/SonosBrokerApplication.cs`
- `src/AccessibleMediaController.SonosBroker/SonosBrokerOptions.cs`
- `src/AccessibleMediaController.SonosBroker/SonosBrokerModels.cs`
- `src/AccessibleMediaController.SonosBroker/SonosLoginSessionStore.cs`
- `src/AccessibleMediaController.SonosBroker/SonosOAuthGateway.cs`
- `src/AccessibleMediaController.SonosBroker/README.md`
- `src/AccessibleMediaController.Core/Sonos/SonosLoginContract.cs`
- `src/AccessibleMediaController.Core/Sonos/SonosLoginClient.cs`
- `scripts/Build-SonosBrokerBundle.ps1`
- `tests/AccessibleMediaController.SonosBroker.SmokeTests/*`
- `tests/AccessibleMediaController.Core.SmokeTests/SonosLoginClientTests.cs`
- `src/AccessibleMediaController.LiteHost/LiteSonosAccountOwner.cs`
- `src/AccessibleMediaController.LiteHost/LiteSonosCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `src/AccessibleMediaController.LiteHost/Protocol/LiteSonosContract.cs`
- `src/AccessibleMediaController.LiteHost/Program.cs`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/tests/test_sonos_account_dialog.py`
- `wxlite/tests/test_sonos_session.py`
- `wxlite/tests/test_command_palette.py`
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/SonosContractTests.cs`
- `tests/AccessibleMediaController.Windows.SmokeTests/SonosAccountWiringTests.cs`
- `src/AccessibleMediaController.Core/Sonos/SonosIntegrationDefaults.cs`
- `src/AccessibleMediaController.Windows/Services/SonosAccountOwner.cs`
- `.dockerignore`
- `deploy/sonos-broker/Dockerfile`
- `deploy/sonos-broker/Dockerfile.runtime`
- `deploy/sonos-broker/compose.yaml`
- `deploy/sonos-broker/Caddyfile`
- `deploy/sonos-broker/.env.example`
- `deploy/sonos-broker/README.md`
- `scripts/Build-SonosBrokerDeploymentBundle.ps1`
- `AccessibleMediaController.sln`
- `docs/zadania/README.md`

## Testy i wynik

- `dotnet build src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj -c Release --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet run --project tests/AccessibleMediaController.SonosBroker.SmokeTests/AccessibleMediaController.SonosBroker.SmokeTests.csproj -c Release`
  — 16/16 testów przeszło 2026-10-20.
- `dotnet build AccessibleMediaController.sln -c Release --no-restore` — sukces;
  nowy broker i jego testy kompilują się razem z całym rozwiązaniem.
- Testy obejmują: brak i częściową konfigurację, zgodność originu i callbacku,
  PKCE, jednorazową sesję, zły verifier bez utraty wyniku, ochronę przed drugim
  callbackiem, wygaśnięcie, równoległy limit pojemności, dokładny adres Sonosa,
  serwerową wymianę kodu, odnowienie z rotacją i bez rotacji oraz zgodność
  endpointów start/odmowa/wynik z klientem AMC, ścisłą listę proxy, odrzucenie
  fałszywego `X-Forwarded-Proto` od niezaufanego klienta oraz poprawne
  zakończenie TLS przez jawnie zaufane lokalne proxy.
- Integracyjny test HTTP działał wyłącznie na lokalnym porcie w środowisku
  `Development` i `Production`; nie otworzył przeglądarki, nie użył sieci
  Sonosa, konta ani głośnika. Pierwsza próba w piaskownicy nie mogła połączyć
  się z lokalnym gniazdem; identyczny test uruchomiony z dostępem do localhost
  zaliczył komplet 16 przypadków.
- Historyczny eksperyment z 20 października 2026 obejmował wyłącznie bezpieczne odczyty
  `https://hermes.tail6caad7.ts.net/health/live` i `/health/ready`. Host
  odpowiada przez HTTPS, ale oba adresy zwracają `404`. Pod originem wpisanym
  wtedy w AMC nie był więc uruchomiony przygotowany broker Sonos. Po późniejszej
  korekcie użytkownika Hermes nie jest już kandydatem do wdrożenia. Nie
  rozpoczynano logowania, nie otwierano przeglądarki i nie wysyłano poleceń do
  głośników.
- Skrypt `Build-SonosBrokerBundle.ps1` zbudował próbny pakiet framework-dependent
  bez symboli i sekretów. Manifest objął 4 pliki opublikowanego brokera, a
  kontrola ponownie obliczonych rozmiarów i SHA-256 nie wykazała rozbieżności.
  Próbny ZIP miał 30 025 bajtów i SHA-256
  `30e691e3726e09c689bd4df8896ef4b4fcd8c61c900feb215d6615d11f7cb2ae`.
  Ponieważ źródła były w trakcie pracy, manifest uczciwie oznaczył go jako
  `dirty`; nie jest to paczka do wdrożenia ani publikacji.
- Po zapisaniu zmian zbudowano czysty następca, który pierwotnie miał służyć
  próbie na Hermesie:
  `.test-output/sonos-broker/AMC-Sonos-Broker-0.1.0-alpha.422-9431fd8d2619.zip`.
  Archiwum ma 30 029 bajtów i SHA-256
  `388f5e7a1dd31f8cd8b2c609c2096a641571a528ca6c8fe20569e2f3359c8660`.
  Manifest wskazuje czysty commit
  `9431fd8d2619a1c267299e91b70f89637980ba40`, .NET 8, cztery pliki
  kontrolowane i pięć plików razem z manifestem. Sumę archiwum obliczono
  ponownie niezależnie. Pakiet nie został wdrożony ani uruchomiony i po korekcie
  z 20 października jest wyłącznie artefaktem historycznym, nie kandydatem do
  uruchomienia.
- Nie wykonano instalacji, publikacji, logowania ani wdrożenia publicznego.
- `python -m compileall -q wxlite/amc_wx_lite` — sukces.
- `dotnet build src/AccessibleMediaController.LiteHost/AccessibleMediaController.LiteHost.csproj --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet build tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet run --project tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj --no-build -- --sonos`
  — jeden ukierunkowany zestaw Sonos zaliczony. Test potwierdza jawne etykiety
  i brak tokenu, adresu brokera oraz technicznych nazw stanów w odpowiedzi.
- Po rozdzieleniu odpowiedzi `404` historycznego hosta kompilacje Release testów Core i
  protokołu LiteHost zakończyły się z 0 ostrzeżeń i 0 błędów. Ukierunkowane
  testy klienta pierwszego logowania: **36 zaliczonych**. Ukierunkowany
  kontrakt Sonos LiteHost: **1/1 zaliczony**. Test potwierdza stały komunikat
  bez adresu brokera i rozróżnienie `404` od niezgodnej odpowiedzi innego
  rodzaju.
- 136 ukierunkowanych testów wxPython — zaliczone. Obejmują `Ctrl+F5`, menu,
  pomoc, paletę, Menedżer sesji, jawne etykiety, rozdzielenie stanu konta od
  tokenów, drogę konto–grupy oraz zachowanie innych kont i sesji.
- Pierwszy niepoprawny równoległy przebieg dwóch kompilacji został odrzucony:
  oba procesy próbowały pisać ten sam plik `obj`. Powtórzenie sekwencyjne
  przeszło bez błędów. Nie jest to wada kodu.
- Próba pełnego `wxlite/tests` w piaskownicy została zatrzymana po potwierdzeniu,
  że `tempfile` nie może pisać SQLite w wirtualnym katalogu `%TEMP%`. Wynik ten
  nie jest przedstawiany jako regresja ani jako zaliczenie.
- Pełny `wxlite/tests` poza piaskownicą: **1861 zaliczonych, 116 świadomie
  pominiętych, 11 podtestów zaliczonych**. Jedyny początkowy brak dotyczył
  wymaganego wcześniejszego pliku LiteHost Release, a nie zachowania kodu.
- `dotnet build src/AccessibleMediaController.LiteHost/AccessibleMediaController.LiteHost.csproj -c Release --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów; po nim brakujący
  `test_profile_edits_go_through_the_real_host` przeszedł: **1 zaliczony**.
- Zbudowano pełnego kandydata AMC Test
  `2026.10.20-fd5f423117f87c34aff6e9c4def22a985aa307a6-b7475d46`:
  manifest obejmuje 1667 plików, a cały katalog 1668 plików i około 133,59 MiB.
  SHA-256 manifestu:
  `C60D5072408CFC936160531CF627B8F35432EF4A2F14CEA064F4D08C098C1F66`.
- Pierwsza próba instalacji została prawidłowo zatrzymana przed podmianą.
  Między wcześniejszą kontrolą a etapem zamykania programu harmonogram o 12:30
  rozpoczął nagrywanie `3 - 2026-10-20 12-30.mp3`. AMC Test odmówił zwykłego
  zamknięcia, aktualizator zakończył się kodem 3 i nie zmienił zainstalowanych
  plików. To potwierdza działanie ochrony nagrywania, nie błąd instalatora.
- Po zakończeniu harmonogramu z 12:30 o 12:35 wykonano drugą bramkę: 15/15
  folderów było dostępnych, nie znaleziono plików `.amc-partial`, a następny
  harmonogram był dopiero o 13:00. Aktualizator ponownie nie podmienił plików,
  ponieważ działający frontend nie zakończył się po bezpiecznym `WM_CLOSE`.
  Dwa dodatkowe zwykłe polecenia zamknięcia skierowane do potwierdzonego
  głównego okna również zostały odrzucone. Okno było widoczne, włączone i bez
  okna modalnego. Tekst kontrolki stanu brzmiał: „Nie zamykam AMC Test,
  ponieważ trwa nagrywanie”. Późniejsza analiza pełnego dziennika wykazała, że
  wciąż działały cztery inne nagrania: Gdańsk Regiony, Meteor, RDC i PIK.
  Wszystkie zakończyły pliki oraz wpisy stanu około 12:50:51–12:50:56.
  Odmowa zamknięcia była więc prawidłową ochroną rzeczywistych nagrań, a nie
  pozostawionym wpisem po harmonogramie. Procesów nie zakończono wymuszenie.
- O 12:53 ponowna bramka wykazała 15/15 dostępnych folderów, 0 plików
  `.amc-partial`, 0 plików rosnących i następny sześciominutowy harmonogram
  o 13:00. Cztery równoległe nagrania zakończyły się około 12:51, więc zwykłe
  zamknięcie zostało przyjęte. Pierwsze wywołanie aktualizatora zwróciło kod 2 wyłącznie
  przez nieprawidłowe ujęcie ścieżek ze spacjami i nie rozpoczęło podmiany.
  Powtórzenie z poprawnymi argumentami zakończyło się kodem 0.
- Zainstalowana paczka przeszła pełne `--sprawdz-pakiet-cicho` z kodem 0.
  Manifest ma 1667 plików i SHA-256
  `C60D5072408CFC936160531CF627B8F35432EF4A2F14CEA064F4D08C098C1F66`.
  O 12:55 działały dokładnie trzy nowe procesy z katalogu instalacji: jeden
  uruchamiacz, jeden frontend i jeden LiteHost.
- Po odłączeniu aktywnych źródeł od Hermesa wyszukiwanie w `src` nie znalazło
  originu `hermes.tail6caad7.ts.net`; jedyny pozostały tekst znajduje się w
  asercji testowej chroniącej przed jego ponownym wprowadzeniem.
- `python -m compileall -q wxlite/amc_wx_lite` — sukces. Cztery bezpośrednie
  testy okna konta Sonos — **4/4 zaliczone**; potwierdzają ukrycie rozpoczęcia
  logowania, jawny komunikat, fokus „Zamknij” i brak technicznego adresu.
- Kompilacje Release LiteHost i jego testów protokołu — sukces, 0 ostrzeżeń,
  0 błędów. Ukierunkowany zestaw `--sonos` — **1/1 zaliczony**.
- Kompilacja Release `AccessibleMediaController.Windows.SmokeTests` — sukces,
  0 ostrzeżeń, 0 błędów. Pierwszy przebieg w piaskownicy zatrzymał resolver
  workloadów MSBuild bez diagnostyki źródłowej; identyczny przebieg poza tą
  izolacją przeszedł. `--sonos-account-wiring` zaliczył **24 sprawdzenia** bez
  pokazywania GUI.
- Przed testami nie znaleziono uruchomionego procesu AMC, LiteHost ani Pythona
  należącego do aplikacji oraz plików `.amc-partial` w jawnych katalogach
  projektu. Nie zamykano, nie instalowano i nie uruchamiano użytkowego AMC Test.
- Po dodaniu plikowego sekretu i pakietu wdrożeniowego kompilacja Release
  testów brokera zakończyła się z 0 ostrzeżeń i 0 błędów. Wszystkie
  **18/18** testów przeszło; nowe przypadki obejmują poprawny plik sekretu,
  konflikt dwóch źródeł, brak pliku i ścieżkę względną.
- Publikacja framework-dependent utworzyła 5 plików aplikacji o łącznym
  rozmiarze 97 504 bajtów. Na tym komputerze nie ma Docker Engine ani innego
  runtime'u kontenerowego, więc nie przedstawia się statycznej kontroli plików
  Compose jako rzeczywistego uruchomienia kontenerów.
- Skrypt pakowania z czystego commitu `2bac12d0` utworzył samodzielny ZIP
  `AMC-Sonos-Deployment-0.1.0-alpha.422-2bac12d03241.zip`: 34 856 bajtów,
  SHA-256 `defd288ec942bb22706ffe8e05d3a5c73454df3cec651e1f1a1abceffc3ce9cd`.
  Manifest obejmuje 10 plików, ma `workingTreeClean=true` i
  `includesSecrets=false`; niezależne ponowne obliczenie rozmiarów i sum nie
  wykazało rozbieżności. ZIP rozpakowano próbnie i ponownie zweryfikowano.
- Audyt historycznego magazynu wykazał plik
  `C:\Users\micha\AppData\Local\AccessibleMediaController\credentials\sonos.bin`
  o rozmiarze 518 bajtów, zmieniony 19 października 2026 o 18:27 czasu
  lokalnego. Kontrolowany odczyt przez DPAPI bieżącego użytkownika nie wypisał
  żadnego poświadczenia. Potwierdził format 1, typ Bearer, zakres
  `playback-control-all`, obecność access tokenu i refresh tokenu oraz
  przypisanie do historycznego originu. Token dostępu wygasł 20 października,
  ale sam rekord nadal zawiera refresh token. Bufory jawnego tekstu wyzerowano
  po sprawdzeniu.

## Znane ograniczenia

- Brak publicznej domeny, certyfikatu, produkcyjnych danych integracji i wpisu
  callbacku w portalu Sonos. Tych danych nie wolno wymyślać ani zapisywać w Git.
- Przygotowano techniczny wariant pojedynczego serwera Linux, ale nie ma jeszcze
  konkretnego publicznego serwera, nazwy DNS ani sposobu opłacenia i utrzymania
  hostingu. Hermes nie jest rozwiązaniem tego ograniczenia ani częścią obecnej
  architektury.
- Magazyn sesji jest pamięciowy i przeznaczony dla jednej instancji. Skalowanie
  na wiele replik wymaga wspólnego atomowego magazynu.
- Nadal trzeba znać dokładne adresy reverse proxy wybranego hostingu. Jeżeli
  hosting zmienia je dynamicznie i nie gwarantuje stałej listy, należy użyć
  bezpośredniego HTTPS w Kestrel albo wybrać inny sposób wdrożenia; nie wolno
  omijać tej ochrony przez zaufanie wszystkim klientom.
- Nie wykonano ręcznego odbioru NVDA istniejącego okna konta ani prawdziwego
  odnowienia tokenu. Potrzebna jest obecność użytkownika.
- Nowe okno konta jest zainstalowane w użytkowym AMC Test. Nadal wymaga
  ręcznego odbioru NVDA i świadomej próby prawdziwego logowania.
- Prawdziwe rozpoczęcie logowania, otwarcie przeglądarki, sprawdzenie konta i
  odczyt grup nie były automatyzowane. Wymagają świadomego odbioru użytkownika;
  żadne polecenie nie zostało wysłane do głośnika.
- Nie potwierdzono regresji pozostawiającej fałszywe aktywne nagranie. Bramka
  instalacji widziała równoległe, rzeczywiste nagrania, których nie obejmowała
  początkowa kontrola samych plików harmonogramowych. Kolejne bramki muszą więc
  nadal łączyć stan hosta z kontrolą wszystkich jawnych folderów nagrań.
- Jawne oznajmienie stanu konta z 20 października jest potwierdzone w kodzie i
  testach, ale nie zostało jeszcze zainstalowane ani odebrane z NVDA.
- Rozpoznanie nieuruchomionej usługi brokera jest potwierdzone w kodzie,
  kompilacji i testach, lecz nie zostało jeszcze zainstalowane w AMC Test.
- Bezpieczny stan „publiczny broker nieskonfigurowany” jest potwierdzony w
  źródłach i testach, ale nie został jeszcze zainstalowany. Zainstalowany AMC
  Test nadal zawiera wcześniejszą wersję i nie jest dowodem tej korekty.
- Nie ma jeszcze niezależnego hostingu, domeny, certyfikatu ani produkcyjnej
  integracji Sonos. Do czasu ich powstania logowanie w nowych źródłach jest
  celowo niedostępne, a nie częściowo emulowane.
- Nie znaleziono na komputerze Docker Engine, Azure CLI, narzędzi Fly.io,
  Cloudflare, Google Cloud ani zmiennych `SONOS_*`. Nie ma więc lokalnego dowodu
  dostępu do zewnętrznego hostingu lub sekretu integracji. Publicznego
  wdrożenia nie wolno pozorować samym ZIP-em.
- Lokalny magazyn użytkownika nie zawiera sekretu integracji. Trzeba potwierdzić
  na dawnym hoście, czy istnieją źródła brokera i chroniona konfiguracja oraz
  czy publiczny identyfikator odpowiada temu w AMC. Sekretu nie wolno zwracać
  w odpowiedzi Hermesa, historii terminala ani w pliku zadania.

## Bezpieczne sprawdzenie na Hermesie

Hermes ma wykonać wyłącznie odczyt metadanych i odpowiedzieć bez wartości
sekretów oraz tokenów:

1. Czy istnieje repozytorium `/home/michal/projekty/amc-sonos-auth` albo jego
   następca oraz jaki jest jego bieżący commit i stan zmian.
2. Czy istnieje konfiguracja `/etc/amc-sonos-auth/sonos.env` albo równoważny
   magazyn sekretów. Wystarczy odpowiedź tak/nie dla nazw
   `SONOS_CLIENT_ID`, `SONOS_CLIENT_SECRET`, `SONOS_REDIRECT_URI` i
   `SONOS_BROKER_PUBLIC_ORIGIN`; nie wolno wypisywać wartości.
3. Czy zapisany `SONOS_CLIENT_ID` jest równy publicznemu identyfikatorowi
   `b051a8f0-499c-4deb-9f66-843a752c36e4` — wyłącznie tak/nie.
4. Czy działała lub nadal istnieje usługa systemowa, kontener, reverse proxy
   albo certyfikat dawnego brokera; podać nazwy usług i ścieżki konfiguracji,
   bez treści sekretów.
5. Czy sekret można później umieścić bezpośrednio w chronionym pliku na nowym
   serwerze, bez przesyłania go przez czat. Na tym etapie nie należy go jeszcze
   kopiować ani uruchamiać starej usługi.

## Brama publicznego udostępnienia

1. Wybrać stałą domenę i hosting obsługujący prawdziwy HTTPS.
2. Odzyskać metadane istniejącej integracji z Hermesa albo zatwierdzić nową
   produkcyjną integrację Sonos i dokładny callback
   `/login/callback`.
3. Wprowadzić sekrety poza repozytorium i sprawdzić `/health/ready`.
4. Z użytkownikiem wykonać logowanie, odmowę, odnowienie oraz ponowne
   uruchomienie brokera.
5. Dopiero wtedy dodać publiczny origin do profilu wydania, wykonać testy
   parytetu możliwości/pomocy/palety i rozważyć odsłonięcie Sonosa w AMC.

## Wersja i commit

- Wersja kodu AMC: `0.1.0-alpha.422`.
- Commit źródeł, testów i pierwszego zapisu dokumentacji: `97a29c09`.
- Commit bezpiecznego reverse proxy i testów 16/16: `1db05e74`.
- Commit okna konta Sonos, bramki `Ctrl+F5`, testów i zapisu realizacji:
  `6b967a29`.
- Powtarzalny skrypt tworzenia lokalnego pakietu brokera i jego manifestu:
  przygotowany oraz sprawdzony 20 października 2026; commit `2bac12d0`.
- Kandydat AMC Test: `2026.10.20-fd5f423117f87c34aff6e9c4def22a985aa307a6-b7475d46`.
- Instalacja i uruchomienie AMC Test są potwierdzone dla
  `2026.10.20-fd5f423117f87c34aff6e9c4def22a985aa307a6-b7475d46`
  w `D:\Projekty Codex\AMC Python` 20 października 2026 o 12:55.
- Publikacja: brak.
- Jawna mowa bieżącego stanu kont Spotify i Sonos: commit `39386e90`.
  **124** testy reprezentatywnych powierzchni interfejsu oraz ukierunkowane
  zestawy protokołu Spotify i Sonos **2/2** zaliczone; kompilacja Release bez
  ostrzeżeń i błędów. Instalacji i publikacji nie wykonywano.
- Historyczny lokalny pakiet brokera, pierwotnie przygotowany do próby na Hermesie:
  źródło `9431fd8d`, ZIP 30 029 bajtów, SHA-256
  `388f5e7a1dd31f8cd8b2c609c2096a641571a528ca6c8fe20569e2f3359c8660`.
  Budowa i integralność są potwierdzone; wdrożenia, konfiguracji sekretów,
  logowania i publikacji nie wykonywano. Pakiet nie jest obecnym celem
  wdrożenia i nie należy go uruchamiać na Hermesie.
- Osobny użytkowy stan braku endpointu brokera: commit `c6eaeee9` —
  `fix(amc10): rozpoznaj brak uslugi logowania Sonos`. Kompilacja Release oraz
  testy 36 i 1/1 są zaliczone; instalacji ani publikacji nie wykonywano.
- Usunięcie Hermesa z aktywnych źródeł klienta, jawna bramka dostępności,
  użytkowy stan niedostępności i testy: commit `3ab4c079` —
  `fix(amc10): oddziel logowanie Sonos od Hermesa`. Kod i testy są
  zweryfikowane; paczki, instalacji, uruchomienia i publikacji nie wykonywano.
- Kontenerowy wariant niezależnego serwera, Caddy, plikowy sekret i testy
  18/18: commit `5cfb60bb` — `feat(amc10): przygotuj niezalezne wdrozenie
  brokera`.
- Powtarzalny samodzielny ZIP bez źródeł i sekretów: commit `2bac12d0` —
  `build(amc10): pakuj broker do wdrozenia`. Pakiet został zbudowany i
  zweryfikowany lokalnie; nie został wysłany ani uruchomiony na serwerze.
- Dowód historycznego logowania użytkownika, rozdzielenie tokenu od sekretu
  integracji i bezpieczna lista kontroli dla Hermesa: commit `8ac9b2be` —
  `docs(amc10): zapisz dowod historycznego logowania`.

## Porządek dysku

- Po pomyślnej weryfikacji usunięto wyłącznie odtwarzalny dziennik diagnostyczny
  `D:\Projekty Codex\AMC - integracja wxPython\.test-output\sonos-windows-build.log`
  o rozmiarze 1 402 075 bajtów, czyli około 1,34 MiB. Plik nie jest możliwy do
  odzyskania, ale można go ponownie wytworzyć kompilacją diagnostyczną.
- Nie usunięto zastanych katalogów `.test-output` ani `.test-tmp`, ponieważ ich
  pozostała zawartość nie powstała wyłącznie w tym etapie i wymaga osobnej oceny.
- Po weryfikacji usunięto należące wyłącznie do tego etapu brudny pakiet próbny,
  osobny katalog publikacji oraz rozpakowany czysty pakiet i katalog kontroli:
  razem około 346 KiB z
  `D:\Projekty Codex\AMC - integracja wxPython\.test-output`. Są odtwarzalne i
  nie podlegają odzyskaniu. Zachowano jedyny czysty ZIP wdrożeniowy o rozmiarze
  34 856 bajtów oraz nie dotknięto zastanych `.test-output` i `.test-tmp`.
