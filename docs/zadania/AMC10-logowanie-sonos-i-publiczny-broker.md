# AMC10 — proste logowanie Sonos i publiczny broker

## Status

**W trakcie — broker gotowy w źródłach, kompilacji i testach lokalnych;
publiczne wdrożenie oraz odbiór z zewnętrznym kontem pozostają bramą.**

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

AMC nie zna i nie przechowuje sekretu integracji Sonos. Tokeny użytkownika
pozostają wyłącznie w procesie C# i w istniejącym lokalnym magazynie chronionym
systemem Windows; interfejs wxPython otrzymuje tylko stan, komunikaty i zaufany
adres autoryzacji.

Publiczny Sonos nie jest jeszcze widoczny. Pozostanie ukryty, dopóki broker nie
będzie działał pod stałym adresem HTTPS i nie przejdzie świadomego odbioru na
zewnętrznym koncie. WiiM nie zależy od tego brokera.

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
- Publiczny profil AMC nadal nie udostępnia Sonosa. Bieżący prywatny AMC Test
  nadal używa dotychczasowego brokera; przełączenie originu nastąpi dopiero po
  rzeczywistym wdrożeniu i odbiorze.
- Nie zmieniono znaczenia `Ctrl+F5` ani istniejącego transportu Sonosa. Dodano
  jedynie świadomą bramkę konta przed odczytem grup. Nazwa, skrót, opis, menu,
  pomoc `Ctrl+F1`, pełna pomoc i paleta `Ctrl+Shift+K` nadal pochodzą ze
  wspólnego katalogu poleceń.
- Host udostępnia wxPythonowi siedem wąskich operacji konta bez argumentów
  poświadczeń: stan, rozpoczęcie, sprawdzenie i anulowanie logowania,
  odświeżenie, ponowienie samego zapisu oraz wylogowanie. Odpowiedzi nie
  zawierają tokenów, sekretu, adresu brokera, nazw klas ani wartości enumów.

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
- `tests/AccessibleMediaController.SonosBroker.SmokeTests/*`
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
- Nie wykonano instalacji, publikacji, logowania ani wdrożenia publicznego.
- `python -m compileall -q wxlite/amc_wx_lite` — sukces.
- `dotnet build src/AccessibleMediaController.LiteHost/AccessibleMediaController.LiteHost.csproj --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet build tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet run --project tests/AccessibleMediaController.LiteHost.ProtocolTests/AccessibleMediaController.LiteHost.ProtocolTests.csproj --no-build -- --sonos`
  — jeden ukierunkowany zestaw Sonos zaliczony. Test potwierdza jawne etykiety
  i brak tokenu, adresu brokera oraz technicznych nazw stanów w odpowiedzi.
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

## Znane ograniczenia

- Brak publicznej domeny, certyfikatu, produkcyjnych danych integracji i wpisu
  callbacku w portalu Sonos. Tych danych nie wolno wymyślać ani zapisywać w Git.
- Magazyn sesji jest pamięciowy i przeznaczony dla jednej instancji. Skalowanie
  na wiele replik wymaga wspólnego atomowego magazynu.
- Nadal trzeba znać dokładne adresy reverse proxy wybranego hostingu. Jeżeli
  hosting zmienia je dynamicznie i nie gwarantuje stałej listy, należy użyć
  bezpośredniego HTTPS w Kestrel albo wybrać inny sposób wdrożenia; nie wolno
  omijać tej ochrony przez zaufanie wszystkim klientom.
- Nie wykonano ręcznego odbioru NVDA istniejącego okna konta ani prawdziwego
  odnowienia tokenu. Potrzebna jest obecność użytkownika.
- Nowe okno konta jest gotowe w źródłach, testach i zweryfikowanym kandydacie,
  ale nie jest jeszcze zainstalowane w użytkowym AMC Test. Dopiero bezpieczna
  bramka nagrywania pozwala podmienić działającą instalację.
- Prawdziwe rozpoczęcie logowania, otwarcie przeglądarki, sprawdzenie konta i
  odczyt grup nie były automatyzowane. Wymagają świadomego odbioru użytkownika;
  żadne polecenie nie zostało wysłane do głośnika.

## Brama publicznego udostępnienia

1. Wybrać stałą domenę i hosting obsługujący prawdziwy HTTPS.
2. Utworzyć albo zatwierdzić produkcyjną integrację Sonos i dokładny callback
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
- Kandydat AMC Test: `2026.10.20-fd5f423117f87c34aff6e9c4def22a985aa307a6-b7475d46`.
- Zainstalowany AMC Test pozostaje w wersji
  `2026.10.20-f96149f75e83eea064899db78c762596e56d2504-904ceb8c`;
  instalacja nowego kandydata została bezpiecznie odłożona przez aktywne
  nagrywanie harmonogramowe.
- Publikacja: brak.
