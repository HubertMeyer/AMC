# AMC10 — proste logowanie Sonos i publiczny broker

## Status

**W trakcie — niezależny broker działa publicznie pod
`https://sonos.stareaudycje.pl/`. Operator zaliczył 17/17 kontroli publicznych
bez logowania oraz potwierdził 20/20 testów pakietu, bez sekretów w źródłach i
logach. Źródła AMC są lokalnie przygotowane do użycia nowego originu, ale nie
zostały zainstalowane ani opublikowane. Autor musi jeszcze dodać nowy callback
w istniejącej integracji Sonos, nie usuwając Hermesa i nie rotując sekretu,
a następnie wykonać z użytkownikiem prawdziwe logowanie, odmowę, odnowienie,
odbiór sprzętu i NVDA. Pakiet zwrotny operatora nie został jeszcze odnaleziony
na tym komputerze, więc jego treść i suma pozostają do lokalnej weryfikacji.**

Sterowanie Sonosem i WiiM było już przeszczepione i użytkownik ocenił je jako
prawie gotowe. Ten etap nie zmienia adapterów, list, transportu ani WiiM.

## Korekty użytkownika

- 2026-10-25: podczas ręcznego odbioru zainstalowanego AMC Test użytkownik
  otworzył sesję Sonos i nacisnął `Ctrl+F5`. W oknie dostępny klawiaturą był
  tylko przycisk „Zamknij”, a instrukcję dało się odczytać dopiero kursorem
  myszy. Jest to dowód działania starszej instalacji z `canLogin=false`, ale
  także rzeczywista wada dostępności: instrukcja i stan były statycznymi
  napisami poza kolejnością Tab. Zastępuje to wcześniejsze założenie, że samo
  wypowiedzenie stanu przy otwarciu wystarcza. Użytkownik polecił poprawić
  interfejs wyłącznie AMC Test i zgodził się dodać nowy callback Sonosa.

- 2026-10-25: użytkownik przekazał raport operatora z działającego publicznego
  brokera. Zastępuje on stan „broker nie został wdrożony”. Operator podał
  17/17 kontroli publicznych, 20/20 testów źródeł, prawidłowy limit per klient,
  bezpieczne logi, start usług po restarcie i pamięć 37–62 MB przy limicie
  300 MB. Prawdziwe logowanie pozostaje zablokowane do dodania callbacku
  `https://sonos.stareaudycje.pl/login/callback`. Podana suma pakietu zwrotnego
  to `c435a3ee6315a226463f86828d087e4a845203834e1914bc95398cc9b6928a01`,
  ale samego pliku nie ma w dotychczas wskazanym folderze, dlatego nie jest to
  jeszcze lokalnie potwierdzony wynik. Commit `bc56ce5` pozostaje tylko lokalny.

- 2026-10-24: użytkownik przekazał odpowiedź operatora serwera. Zastępuje ona
  wcześniejsze ograniczenia o braku hostingu, domeny i znanego reverse proxy.
  Gotowe są Ubuntu 24.04, ASP.NET Core Runtime 8.0.32, systemd, Cloudflare
  Tunnel do `127.0.0.1:5080`, origin `https://sonos.stareaudycje.pl/`,
  chroniony plik sekretu oraz zaufane proxy `127.0.0.1`. Blokadą był brak
  dostępnego kodu brokera; przygotowano wariant B, bez publikacji repozytorium.

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
- 2026-10-20: użytkownik przypomniał, że w historycznym AMC działało pełne
  sterowanie i grupowanie Sonosa, a po przeniesieniu działa ono również w
  zainstalowanym AMC Test. To zastępuje zbyt szerokie wcześniejsze sformułowanie,
  że bieżąca architektura „nie ma związku” z Hermesem. Dokładnie: gotowa
  obsługa Sonosa nie zależy od Hermesa przy zwykłym sterowaniu, ale zainstalowany
  wariant używa go jako brokera logowania i odnowienia tokenu. Docelowe wydanie
  publiczne nadal ma otrzymać broker niezależny od Hermesa.
- 2026-10-20: użytkownik dostarczył odczytowy raport Hermesa. Zastępuje on
  wcześniejszy wniosek, że odpowiedź `404` z `/health/*` oznacza brak dawnej
  usługi. Historyczny broker i proxy nadal działają, lecz nie udostępniają
  nowych endpointów zdrowia. Raport potwierdził zgodny identyfikator klienta,
  obecność niepustego sekretu i obsługę odnowienia bez ujawnienia wartości.

## Materiał do dokumentacji użytkownika

Etap z 24.10.2026 przygotował sprawdzony pakiet serwerowy do zewnętrznego
wdrożenia. Raport z 25.10.2026 potwierdza działanie serwera i pozwala wpisać
`sonos.stareaudycje.pl` do źródeł AMC Test. Nie zmieniono jeszcze zainstalowanej
aplikacji, jej menu, skrótów ani komunikatów NVDA. Instalacja pozostaje za bramą
callbacku Sonosa, lokalnej weryfikacji pakietu zwrotnego oraz testów.

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

Instrukcja logowania oraz bieżący stan konta są także polami tylko do odczytu
w kolejności Tab. Można wejść do nich klawiaturą i czytać je strzałkami. Gdy
logowanie jest dostępne, początkowy fokus trafia na „Rozpocznij logowanie”. Gdy
usługa jest niedostępna, fokus trafia na pole stanu z wyjaśnieniem zamiast na
sam przycisk „Zamknij”. Błąd operacji również przenosi fokus na czytelny stan.

Jeżeli skonfigurowany host odpowiada, ale nie ma pod nim uruchomionej usługi
logowania AMC, po wybraniu „Rozpocznij logowanie” program mówi: „Usługa
logowania Sonos nie jest uruchomiona pod skonfigurowanym adresem”. Ten stan
nie jest mylony z odmową Sonosa ani z oczekiwaniem na przeglądarkę.

W przygotowanych źródłach publiczny broker jest dostępny, więc okno „Konto
Sonos” pokazuje przycisk rozpoczęcia logowania. Zainstalowany AMC Test nie został
jeszcze zmieniony. Do czasu dodania callbacku w Sonos Integration Manager nie
należy w nim uruchamiać prawdziwej próby na nowym brokerze.

Jeżeli użytkownik wybierze „Sprawdź logowanie” przed powrotem z Sonosa, broker
odpowiada technicznym kodem `unknown_session`, ale AMC nie wypowiada tego kodu.
Program mówi, że logowanie jeszcze trwa, zachowuje rozpoczętą próbę i pozwala
sprawdzić ponownie. Istniejące testy obejmują kolejno oczekiwanie oraz udany
drugi odczyt tej samej próby.

Wydanie publiczne nie będzie wymagało od zwykłego użytkownika własnego klucza,
sekretu ani serwera. Użytkownik wybierze logowanie, otrzyma adres oficjalnej
strony Sonosa, zaloguje się tam i wróci do AMC, aby sprawdzić wynik. Sekret
integracji pozostaje tylko na wspólnym serwerze AMC.

Podczas przejścia na niezależny serwer nowy adres powrotu zostanie dodany do
tej samej integracji Sonos obok działającego adresu Hermesa. Stary broker
pozostanie czynny do czasu sprawdzenia nowego HTTPS, świeżego logowania,
odnowienia tokenu oraz AMC Test z NVDA. Zwykły użytkownik nie zobaczy tego
etapu migracji.

Istniejące konto autora jest prawidłowo połączone z Sonosem i obsługuje
sterowanie oraz grupowanie w zainstalowanym AMC Test. Zaszyfrowany rekord jest
jednak przypisany do historycznego originu. Przed instalacją wariantu z nowym
brokerem AMC albo poprosi autora o świeże, świadome logowanie, albo zastosuje
osobno sprawdzoną migrację tego samego konta i integracji. Nie będzie po cichu
przepisywać starego tokenu ani udawać, że należy on do innego serwera.

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
  `/home/test/projekty/amc-sonos-auth` oraz konfigurację produkcyjną pod
  `/etc/amc-sonos-auth/sonos.env`; tych danych nie znaleziono lokalnie na
  komputerze Windows.
- Token użytkownika i sekret integracji są różnymi danymi. Zaszyfrowany plik
  Windows potwierdza udane logowanie użytkownika, ale nie zawiera i nie może
  zastąpić serwerowego `SONOS_CLIENT_SECRET`.
- Zainstalowany pakiet ma `sourceRevision`
  `1df89b186803cd6c4b1b4163a2a4ebd41e54f118`. W tej rewizji
  `SonosIntegrationDefaults.BrokerOrigin` wskazuje Hermesa. Broker jest używany
  do rozpoczęcia, sprawdzenia i odnowienia logowania. Wszystkie operacje
  urządzeń, grup, ulubionych, playlist i strumieni używają bezpośrednio
  `SonosControlApiClient` z tokenem konta i publicznym kluczem integracji.
- Źródła przygotowane 25.10.2026 mają publiczny origin
  `https://sonos.stareaudycje.pl/` i `BrokerAvailable=true`. Zainstalowany AMC
  Test pozostaje niezmieniony. Instalację wolno rozpocząć dopiero po dodaniu
  nowego callbacku, sprawdzeniu pakietu zwrotnego i kontroli aktywnych nagrań;
  historyczny rekord poświadczeń związany ze starym originem nie jest po cichu
  przepisywany.
- Oficjalny kontrakt Sonosa wymaga, aby `redirect_uri` odpowiadał jednemu z
  adresów zapisanych dla klucza integracji. Pozwala to najpierw dodać callback
  niezależnego brokera i zachować callback Hermesa jako punkt powrotu, zamiast
  wykonywać ryzykowne przełączenie jednoczesne.
- Nowy pakiet zawiera `MIGRATION_FROM_LEGACY.md`: kolejność bezprzerwowego
  wdrożenia, zakaz kopiowania tokenów, świeże logowanie po zmianie originu,
  odbiór i wycofanie nieudanej próby.

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
- `deploy/sonos-broker/MIGRATION_FROM_LEGACY.md`
- `scripts/Build-SonosBrokerDeploymentBundle.ps1`
- `docs/zadania/AMC10-HERMES-AUDYT-SONOS-2026-10-20.md`
- `AccessibleMediaController.sln`
- `docs/zadania/README.md`

## Testy i wynik

- 2026-10-24: bazowy broker zaliczył 18/18 testów. Dodano kontrolę, że
  zaufany `X-Forwarded-For` rozdziela limity dwóch klientów, oraz kontrolę
  filtrów logowania przy globalnym Debug/Trace. Rozszerzony zestaw zaliczył
  **20/20** testów zarówno w repozytorium, jak i ponownie ze źródeł
  rozpakowanych z finalnego ZIP-a. Testy używały atrap Sonosa i lokalnego
  portu; nie otwierały przeglądarki, nie logowały konta i nie sterowały
  głośnikami.
- Skrypt pakowania odtworzył zależności, wykonał testy, opublikował
  framework-dependent `net8.0` dla `linux-x64` bez apphosta oraz dołączył
  minimalny snapshot źródeł i testów. Manifest finalnego ZIP-a obejmuje 22
  pliki; wszystkie rozmiary i SHA-256 sprawdzono ponownie bez rozbieżności.
  Manifest ma `workingTreeClean=true`, `runtimeIdentifier=linux-x64`,
  `includesSecrets=false` i `includesSource=true`.
- Finalny ZIP ma 63 404 bajty i SHA-256
  `fdf9cb33560d80403ecdaa3991244a44567417a0f7f82d14ed7ef7f37e9a1e18`.
  Skan nie znalazł kluczy prywatnych, `.p8`, JWT, tokenów GitHub/AWS,
  `sonos_client_secret.txt`, symboli PDB ani wykonywalnego apphosta.
- Kontrolny proces Release na Windows odpowiedział `200` z `/health/ready`.
  Pięć próbek wskazało 48,59–50,26 MiB working set i 40,39–40,96 MiB private
  memory. Jest to pomiar orientacyjny; operator ma zwrócić `MemoryCurrent` i
  `MemoryPeak` z docelowego Ubuntu.
- Kod, testy i pakiet zostały przygotowane. Nie wykonano publikacji GitHub,
  instalacji na serwerze, wpisu w portalu Sonos, prawdziwego logowania ani
  zmiany i instalacji AMC Test.

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
  `%LOCALAPPDATA%\AccessibleMediaController\credentials\sonos.bin`
  o rozmiarze 518 bajtów, zmieniony 19 października 2026 o 18:27 czasu
  lokalnego. Kontrolowany odczyt przez DPAPI bieżącego użytkownika nie wypisał
  żadnego poświadczenia. Potwierdził format 1, typ Bearer, zakres
  `playback-control-all`, obecność access tokenu i refresh tokenu oraz
  przypisanie do historycznego originu. Token dostępu wygasł 20 października,
  ale sam rekord nadal zawiera refresh token. Bufory jawnego tekstu wyzerowano
  po sprawdzeniu.
- Manifest zainstalowanego AMC Test wskazuje rewizję
  `1df89b186803cd6c4b1b4163a2a4ebd41e54f118`. Odczyt tej rewizji potwierdził
  broker `https://hermes.tail6caad7.ts.net/`, a odczyt bieżącego HEAD —
  nieroutowalny placeholder. To wyjaśnia jednocześnie działanie obecnej
  instalacji oraz brak gotowości nowszych źródeł do instalacji. W czasie audytu
  proces AMC nie był uruchomiony; nie wykonywano polecenia do głośników,
  odnowienia tokenu, kompilacji ani instalacji.
- Odczytowy raport Hermesa potwierdził działające usługi
  `amc-sonos-auth.service` i `amc-sonos-proxy.service`, nginx, zgodny publiczny
  identyfikator oraz niepusty sekret w chronionej konfiguracji pod nazwami
  `AMC_SONOS_*`. Nie ujawniono wartości, nie wykonano odnowienia, restartu ani
  zmiany konfiguracji. Źródła dawnego brokera są czyste na commicie
  `b27ed4b2e31fcc232677f9fe2f36aa36f237d1d3`.
- Próba pakowania po dodaniu instrukcji migracji zakończyła się sukcesem.
  Brudny pakiet kontrolny miał 37 148 bajtów i SHA-256
  `ff213bb24755b5e2f7cf8609aa11b34a68d1eb9dee31246c1633399dbbf067b5`.
  Manifest obejmował 11 kontrolowanych plików, zawierał
  `MIGRATION_FROM_LEGACY.md`, miał `includesSecrets=false` i nie zawierał
  `secrets/sonos_client_secret.txt`. Pakiet służy wyłącznie weryfikacji i nie
  jest kandydatem wdrożeniowym, ponieważ powstał przed commitem zmian.
- Ukierunkowane testy brokera: pierwsze 15 testów logiki przeszło w
  piaskownicy, a trzy próby HTTP zostały przez nią zablokowane na localhost.
  Identyczny zestaw uruchomiony z dostępem wyłącznie do `127.0.0.1` zaliczył
  wszystkie **18/18** przypadków. Nie użyto sieci Sonosa, konta ani głośników.
- Po commicie zbudowano czysty pakiet
  `AMC-Sonos-Deployment-0.1.0-alpha.422-b762c9b59b58.zip`: 37 153 bajty,
  SHA-256 `6b799ec360f62c1008494b44fd556ee8e11a616154825efd885cdd1de96d4643`.
  Manifest wskazuje pełny commit
  `b762c9b59b585fe3571a1fb0aaaf8fc83c3439fc`,
  `workingTreeClean=true`, `includesSecrets=false` i 11 kontrolowanych plików.
  Ponowne obliczenie wszystkich sum dało zero rozbieżności. Instrukcja migracji
  jest obecna w manifeście i ZIP-ie; `sonos_client_secret.txt` nie występuje.

## Wynik przygotowania klienta 25.10.2026

- Zmieniono wyłącznie źródła kandydata **AMC Test**: domyślny origin to
  `https://sonos.stareaudycje.pl/`, a publiczna możliwość logowania jest
  włączona. Stary AMC, jego instalacja, poświadczenia i broker nie zostały
  zmienione.
- Potwierdzono w kodzie i testach, że `404 {"error":"unknown_session"}` przed
  callbackiem jest stanem `Pending`: próba pozostaje aktywna, komunikat dla
  użytkownika nie ujawnia kodu technicznego, a kolejne sprawdzenie może
  zakończyć tę samą sesję sukcesem.
- Zaliczone ukierunkowane testy Sonosa: klient pierwszego logowania 36/36,
  odnowienie 58/58, koordynator konta 37/37 oraz parytet routera, katalogu i
  palety 6/6. Kompilacja Release projektu testów okien Windows zakończyła się
  bez ostrzeżeń i błędów.
- Kompilacja Release projektu testów okien Windows oraz późniejsza kompilacja
  LiteHosta zakończyły się bez ostrzeżeń i błędów. Pierwsza równoległa próba
  testów spowodowała kolizję pliku kompilacji, dlatego nie jest zaliczana;
  kolejne kompilacje wykonano pojedynczo.
- Nie wykonano instalacji, uruchomienia AMC Test, prawdziwego logowania,
  polecenia do głośnika ani publikacji GitHub.
- Po ręcznym zgłoszeniu poprawiono źródła okna konta AMC Test: instrukcja i
  stan są klawiaturowymi polami tylko do odczytu, a stan bez dostępnego
  logowania przejmuje początkowy fokus. Ukierunkowane testy okna, sesji i
  palety zaliczyły 48/48 przypadków. Pełna regresja wxPython po skierowaniu
  katalogu tymczasowego do worktree zaliczyła 1996 przypadków, 147 pominęła
  zgodnie z warunkami i zatrzymała dwa testy wymagające wcześniej zbudowanego
  LiteHosta; po jego poprawnej kompilacji oba pozostałe testy zaliczyły 2/2.
  Zmiana czeka na bezpieczną instalację i ręczny odbiór NVDA; zainstalowany
  program nie jest jeszcze jej dowodem.

## Znane ograniczenia

- Serwer, domena i TLS przez Cloudflare Tunnel są przygotowane, ale broker nie
  został jeszcze wdrożony. Brakuje wpisu callbacku w portalu Sonos, publicznych
  testów operatora oraz pakietu zwrotnego z raportem i wycofaniem.
- Docelowy wariant to pojedyncza usługa systemd na Mikrusie srv28 z Ubuntu
  24.04 i ASP.NET Core Runtime 8.0.32. Docker i Caddy pozostają wariantem
  referencyjnym, a nie sposobem tego wdrożenia.
- Magazyn sesji jest pamięciowy i przeznaczony dla jednej instancji. Skalowanie
  na wiele replik wymaga wspólnego atomowego magazynu.
- Znanym i jedynym zaufanym peerem jest lokalny `cloudflared` pod
  `127.0.0.1`. Operator musi potwierdzić na docelowym Ubuntu, że przekazuje
  symetryczne `X-Forwarded-For` i `X-Forwarded-Proto: https`.
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
- Produkcyjna integracja Sonos istnieje i może zostać ponownie wykorzystana,
  ale do uruchomienia następcy i wpisania callbacku logowanie w nowych
  źródłach pozostaje celowo niedostępne.
- Nie znaleziono na komputerze Docker Engine, Azure CLI, narzędzi Fly.io,
  Cloudflare, Google Cloud ani zmiennych `SONOS_*`. Nie ma więc lokalnego dowodu
  dostępu do zewnętrznego hostingu lub sekretu integracji. Publicznego
  wdrożenia nie wolno pozorować samym ZIP-em.
- Lokalny magazyn użytkownika nie zawiera sekretu integracji. Audyt potwierdził
  go w chronionej konfiguracji dawnego brokera; jego wartość nadal nie może
  trafić do odpowiedzi, historii terminala, repozytorium ani pliku zadania.

## Wynik bezpiecznego sprawdzenia na Hermesie

Pełny odczytowy raport znajduje się w
`AMC10-HERMES-AUDYT-SONOS-2026-10-20.md`. Nie zawiera sekretów ani tokenów.
Potwierdza następcę repozytorium, czysty commit, działające usługi, nginx,
zgodny identyfikator, obecność sekretu oraz możliwość bezpiecznego przeniesienia
go bez czatu. Historyczny callback to `/sonos/callback`; niezależny broker używa
`/login/callback`. Oba adresy należy utrzymać w integracji do zakończenia
migracji.

## Brama publicznego udostępnienia

1. Wybrać stałą domenę i hosting obsługujący prawdziwy HTTPS.
2. Dodać do istniejącej integracji Sonos dokładny callback nowego brokera
   `/login/callback`, pozostawiając dotychczasowy callback Hermesa.
3. Wprowadzić sekrety poza repozytorium i sprawdzić `/health/ready`.
4. Z użytkownikiem wykonać logowanie, odmowę, odnowienie oraz ponowne
   uruchomienie brokera.
5. Dopiero wtedy dodać publiczny origin do profilu wydania, wykonać testy
   parytetu możliwości/pomocy/palety i rozważyć odsłonięcie Sonosa w AMC.

## Wersja i commit

- Przekazanie systemd/Cloudflare, pakowanie `linux-x64`, ochrona logów i testy
  20/20: commit `bc56ce577bfac4d86c68ecc4f6f90a56a6c22e7a` —
  `build(amc10): przygotuj przekazanie brokera dla systemd`.
- Finalny pakiet:
  `AMC-Sonos-Deployment-0.1.0-alpha.433-bc56ce577bfa.zip`, 63 404 bajty,
  SHA-256 `fdf9cb33560d80403ecdaa3991244a44567417a0f7f82d14ed7ef7f37e9a1e18`.
  Lokalizacja przekazania:
  `D:\Projekty Codex\AMC - pakiety do weryfikacji\Sonos\2026-10-24\do-operatora`.
- Gałąź `integration/sonos-broker-20261024` pozostaje lokalna. Publikacji
  GitHub nie wykonano, ponieważ wymaga osobnej zgody na konkretny stan.
- Wersja finalnego pakietu brokera: `0.1.0-alpha.433`. Wcześniejsze wpisy
  `alpha.422` poniżej opisują historyczne pakiety z etapu 20.10.2026.
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
- Korekta stanu działającego konta, dokładne rozdzielenie bezpośredniego
  sterowania od brokera logowania oraz bramka przed instalacją źródeł z
  wyłączonym brokerem: commit `2759b508` —
  `docs(amc10): doprecyzuj dzialajace konto Sonos`.
- Raport Hermesa, bezprzerwowa instrukcja przejścia i dołączenie jej do pakietu
  wdrożeniowego: commit `b762c9b5` —
  `docs(amc10): przygotuj migracje dzialajacej integracji`.

## Porządek dysku

- 2026-10-24: po pozytywnej kontroli usunięto wyłącznie brudny pakiet próbny,
  rozpakowaną kopię finalnego ZIP-a i drugi katalog weryfikacyjny. Ostatnie dwa
  katalogi zajmowały łącznie 1 627 287 bajtów, około 1,55 MiB; wcześniejszy
  brudny pakiet zajmował 223 381 bajtów. Są odtwarzalne i nie podlegają
  odzyskaniu. Zachowano finalny ZIP, plik jego sumy, odpowiedź dla operatora,
  źródła, commit oraz pliki kompilacji do czasu odbioru etapu.
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
- Po kontroli nowego pakietu usunięto dokładnie katalog brudnej próby
  `.test-output\sonos-deployment-migration-check` oraz rozpakowany katalog
  czystego kandydata pod `.test-output\sonos-deployment-migration-final`.
  Odzyskano około 189 KiB. Pliki są odtwarzalne i nie podlegają odzyskaniu;
  zachowano jedyny zweryfikowany ZIP nowego kandydata o rozmiarze 37 153 bajtów.
