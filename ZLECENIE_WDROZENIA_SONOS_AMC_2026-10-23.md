# Zlecenie: dokończenie Sonosa oraz przekazanie Apple Music do lokalnego wdrożenia w AMC

Data przygotowania: 23 października 2026 r.

Ten plik jest gotowym poleceniem dla osoby, która ma dostęp do mojego serwera i może posłużyć się Codexem albo innym agentem programistycznym. Proszę wykonać zadanie od początku do końca, ale nie ujawniać żadnych sekretów w czacie, repozytorium, logach ani raporcie.

## 1. Oczekiwany rezultat

Chcę mieć stabilne logowanie do konta Sonos i sterowanie moim systemem Sonos z aplikacji Accessible Multimedia Controller (AMC) dla Windows.

Po zakończeniu:

- AMC ma otwierać oficjalną stronę logowania Sonos w zwykłej przeglądarce;
- hasło do Sonosa ma być wpisywane wyłącznie na stronie Sonosa;
- sekret integracji Sonos ma pozostać wyłącznie na serwerze;
- AMC ma otrzymywać token dostępu i token odświeżania przez broker HTTPS, zapisywać je lokalnie za pomocą DPAPI i po restarcie nadal móc odnowić dostęp;
- w AMC mają działać odczyt domów, grup i urządzeń, wybór celu, odtwarzanie, pauza, następny/poprzedni, przewijanie, głośność, wyciszenie, ulubione, playlisty, własne strumienie i presety w zakresie już obsługiwanym przez kod;
- rozwiązanie ma mieć testowalne endpointy stanu, bezpieczne logi, plan wycofania i opis utrzymania;
- wykonawca ma przekazać mi kompletne pakiety zwrotne, które zostaną niezależnie sprawdzone, zbudowane i przetestowane na moim komputerze przed instalacją AMC;
- nie wolno wyłączać obecnego działającego wariantu, dopóki nowy nie przejdzie pełnego odbioru.

To nie jest prośba o napisanie przypadkowego proxy od zera. W AMC istnieje gotowy kontrakt klienta, a lokalnie istnieje także przygotowany broker .NET 8 i zestaw Docker Compose. Najpierw trzeba odzyskać i zweryfikować właściwe źródła, potem je wdrożyć.

## 2. Stan, który został już ustalony

Repozytorium AMC:

- GitHub: `https://github.com/michalkasperczak/AMC`
- kanoniczny katalog autora: `D:\Projekty Codex\Accessible Multimedia Controller`
- aplikacja: .NET/WPF dla Windows;
- profil testowy z bieżącymi funkcjami: AMC Test 0.1.0-alpha.425;
- publiczny identyfikator istniejącej integracji Sonos zapisany w kliencie AMC: `b051a8f0-499c-4deb-9f66-843a752c36e4`;
- obecnie wbudowany adres brokera w `src/AccessibleMediaController.Windows/Services/SonosAccountOwner.cs`:
  `https://hermes.tail6caad7.ts.net/`.

Identyfikator klienta Sonos nie jest sekretem. Sekret klienta Sonos jest sekretem i nie może trafić do tego pliku, GitHuba, wiadomości ani aplikacji Windows.

Klient AMC oczekuje pod zaufanym adresem głównym brokera:

- `POST /login/start`;
- `POST /login/result`;
- `POST /login/refresh`.

Nowy broker dodatkowo wystawia:

- `GET /login/callback`;
- `GET /health/live`;
- `GET /health/ready`.

Stan publicznego adresu sprawdzony 23 października 2026 r. bez uruchamiania logowania:

- serwer odpowiada przez HTTPS i nginx;
- `GET /sonos/callback` zwraca 400, czyli istnieje stary callback;
- `GET /login/callback` zwraca 404;
- `/health/live` i `/health/ready` zwracają 404;
- żądania GET do tras POST `/login/start`, `/login/result` i `/login/refresh` są odrzucane kodem 403.

To jest zgodne z zachowaną dokumentacją starego brokera, a nie dowód awarii. Zachowana dokumentacja podaje:

- dawne źródła na serwerze: `/home/test/projekty/amc-sonos-auth-refresh1`;
- commit starego brokera: `b27ed4b2e31fcc232677f9fe2f36aa36f237d1d3`;
- usługi: `amc-sonos-auth.service` oraz `amc-sonos-proxy.service`;
- reverse proxy: nginx;
- stary redirect URI: `https://hermes.tail6caad7.ts.net/sonos/callback`.

Nie należy przyjmować, że adres `.ts.net` jest dostępny dla Sonosa tylko dlatego, że działa z komputera należącego do tej samej sieci Tailscale. Trzeba potwierdzić dostępność callbacku z publicznego Internetu, spoza tailnetu, oraz prawidłowy publiczny certyfikat.

## 3. Ważna sprawa z kodem nowego brokera

Nowy broker jest przygotowany w lokalnym drzewie:

`D:\Projekty Codex\AMC - integracja wxPython`

Znany punkt tego drzewa w chwili przygotowania zlecenia:

- gałąź lokalna: `integration/amc-test-20261023-late`;
- commit: `42e8f91ca70c95cae4adce263b19ba7c88fd5abf`;
- historia brokera obejmuje m.in. commity `97a29c09`, `1db05e74`, `c6231e59`, `5cfb60bb`, `2bac12d0` i `b762c9b5`;
- projekt: `src/AccessibleMediaController.SonosBroker`;
- testy: `tests/AccessibleMediaController.SonosBroker.SmokeTests`;
- wdrożenie: `deploy/sonos-broker`;
- pakowanie: `scripts/Build-SonosBrokerDeploymentBundle.ps1`.

W chwili sprawdzania plików brokera nie było na domyślnej gałęzi GitHub repozytorium `michalkasperczak/AMC`, a wyszukiwanie gałęzi GitHub nie pokazało gałęzi integracyjnej. Lokalna ścieżka i lokalny commit nie są dla zewnętrznego wykonawcy źródłem do pobrania.

Dlatego przed właściwym wdrożeniem należy wykonać jedno z dwóch działań:

1. opublikować zweryfikowaną gałąź lub commit z brokerem do repozytorium i dać wykonawcy dostęp tylko w potrzebnym zakresie; albo
2. przekazać wykonawcy zbudowany, bezsekretowy ZIP `AMC-Sonos-Deployment-...zip` wraz z `deployment-manifest.json` i sumą SHA-256.

Nie należy odtwarzać brokera na podstawie samego opisu, jeżeli można uzyskać istniejący, przetestowany kod. Nie wolno wdrażać pakietu oznaczonego `dirty`, bez dokładnego commitu i manifestu.

## 4. Dostępy i dane, które wykonawca musi mieć

Przed pracą proszę ustalić i zapisać w raporcie, bez ujawniania sekretów:

- dokładny serwer docelowy, system, architekturę procesora i sposób administracji;
- czy serwer to obecny `hermes.tail6caad7.ts.net`, czy inna maszyna;
- czy są zainstalowane Docker Engine i Docker Compose v2;
- jakie usługi już zajmują porty 80 i 443;
- jaka publiczna nazwa DNS ma wskazywać na nowy broker;
- czy rekordy A/AAAA są poprawne, a przy rekordzie AAAA ruch IPv6 faktycznie dochodzi do serwera;
- czy firewall i operator hostingu dopuszczają ruch przychodzący TCP 80 i 443;
- kto ma dostęp do Sonos Integration Manager dla istniejącej integracji Control;
- czy publiczny Client ID w portalu jest zgodny z `b051a8f0-499c-4deb-9f66-843a752c36e4`;
- gdzie jest przechowywany Client Secret Sonosa i jak zostanie bezpiecznie umieszczony w magazynie sekretów na serwerze.

Jeżeli wykonawca potrzebuje dostępu do GitHuba, należy zaprosić jego konto GitHub do repozytorium. Nie wysyłać mu osobistego tokenu właściciela. Do samego odczytu wystarczy dostęp Read; do przygotowania gałęzi i Pull Requestu wystarczy Write. Dostęp Admin nie jest potrzebny.

Dostęp do serwera powinien być imiennym kluczem SSH, najlepiej dla osobnego użytkownika z kontrolowanym `sudo`. Nie należy wysyłać wspólnego hasła roota ani prywatnego klucza SSH w Telegramie, Hermesie lub promptach Codexa. Po zakończeniu można odwołać tymczasowy klucz.

## 5. Bezwzględne zasady bezpieczeństwa

- Nie umieszczać Sonos Client Secret w repozytorium, `.env`, ZIP-ie, obrazie kontenera, argumentach procesu, zgłoszeniu, czacie ani raporcie.
- Sekret ma być pojedynczą wartością w chronionym pliku `secrets/sonos_client_secret.txt` albo w równoważnym magazynie sekretów. Dostęp tylko dla administratora i usługi.
- Nie kopiować zapisanych tokenów użytkownika ze starego brokera. Po zmianie originu wykonać świeże, świadome logowanie.
- Nie kopiować ani nie usuwać lokalnego pliku poświadczeń Sonosa na komputerze autora. Stary zapis ma pozostać punktem powrotu do czasu odbioru nowego rozwiązania.
- Nie zapisywać pełnego query stringu callbacku. Zawiera krótkotrwały kod i `state`.
- Nie włączać publicznego dziennika dostępu Caddy/nginx dla callbacku bez pewnego filtrowania query stringu.
- Nie publikować zawartości odpowiedzi tokenowej ani nagłówków `Authorization`.
- Nie wyłączać starego brokera, usług systemd, starego callbacku ani starego klucza przed odbiorem nowej instalacji.
- Nie rotować istniejącego sekretu bez oceny wpływu na działający broker. Bezpieczniejsza jest migracja równoległa albo nowy klucz w tej samej integracji, jeżeli portal Sonos na to pozwala.

## 6. Zalecana architektura

Zalecany wariant to jedna stale działająca instancja brokera .NET 8 za prawdziwym HTTPS:

`AMC Windows -> broker HTTPS -> OAuth Sonos / Sonos Control API`

Broker przechowuje tylko krótkie, dziesięciominutowe sesje logowania w pamięci. Nie zapisuje tokenów użytkowników na dysku. Z tego powodu:

- ma działać dokładnie jedna replika;
- usługa nie może zasypiać ani skalować się do zera;
- restart podczas rozpoczętego logowania bezpiecznie unieważnia tę próbę;
- wdrożenie wieloreplikowe wymagałoby osobnego, wspólnego i atomowego magazynu sesji i nie należy go improwizować w tym zadaniu.

Na czystym serwerze można użyć dostarczonego Docker Compose z Caddy. Jeżeli porty 80/443 zajmuje już nginx lub inny ważny serwis, nie wolno go zastępować ani uruchamiać drugiego procesu na tych portach. W takim przypadku trzeba świadomie dostosować wdrożenie do istniejącego reverse proxy, wystawić broker wyłącznie na lokalnym/prywatnym porcie i podać brokerowi dokładny adres IP zaufanego proxy. Po takiej zmianie należy ponownie wykonać testy nagłówków przekazywanych i HTTPS.

Dla obecnego Hermesa bezpieczniejsza jest migracja równoległa na nowym publicznym hoście lub nowej nazwie DNS. Nowy i stary broker używają innych callbacków, a ich trasy logowania częściowo się pokrywają, więc nie należy podmieniać ich w miejscu bez planu wycofania.

## 7. Konfiguracja w Sonos Integration Manager

Należy użyć integracji typu Control. Oficjalny zakres Sonosa to obecnie `playback-control-all`.

Dla nowego hosta, przykładowo `sonos.example.org`, dokładne wartości muszą być następujące:

- publiczny origin brokera: `https://sonos.example.org/`;
- redirect URI w Sonos: `https://sonos.example.org/login/callback`.

Redirect URI musi być publicznie routowalny, używać HTTPS i dokładnie odpowiadać wartości zapisanej w portalu Sonosa. Podczas migracji należy dodać nowy redirect URI obok starego `https://hermes.tail6caad7.ts.net/sonos/callback`. Starego adresu nie usuwać przed końcowym odbiorem.

Jeżeli używana jest istniejąca integracja i ten sam publiczny Client ID, nowy broker musi otrzymać odpowiadający mu sekret. Jeżeli powstanie nowy Client ID, trzeba zaktualizować razem konfigurację brokera i publiczną stałą `IntegrationApiKey` w AMC oraz ponownie zbudować i przetestować aplikację. Nie wolno mieszać identyfikatora jednej integracji z sekretem drugiej.

## 8. Konfiguracja nowego brokera

W dostarczonym wdrożeniu znajdują się `.env.example`, `compose.yaml`, `Caddyfile`, Dockerfile i instrukcja migracji.

W `.env` mają znaleźć się wyłącznie dane niesekretne:

```text
SONOS_BROKER_HOST=sonos.example.org
SONOS_CLIENT_ID=b051a8f0-499c-4deb-9f66-843a752c36e4
```

Sekret ma zostać utworzony bezpośrednio na serwerze jako:

```text
secrets/sonos_client_secret.txt
```

Plik ma zawierać tylko sekret, bez nazwy zmiennej i bez dodatkowych wierszy. Należy użyć chronionego edytora lub magazynu sekretów tak, aby wartość nie trafiła do historii powłoki. Po utworzeniu sprawdzić prawa i rozmiar pliku, ale nie wyświetlać zawartości.

Broker otrzymuje następującą konfigurację:

- `SONOS_BROKER_PUBLIC_ORIGIN=https://NAZWA-DNS/`;
- `SONOS_CLIENT_ID`;
- `SONOS_CLIENT_SECRET_FILE=/run/secrets/sonos_client_secret`;
- `SONOS_REDIRECT_URI=https://NAZWA-DNS/login/callback`;
- `SONOS_TRUSTED_PROXIES` z dokładnymi adresami IP proxy kończącego TLS.

Nie używać szerokiej podsieci, publicznych adresów klientów ani wartości `0.0.0.0` jako zaufanego proxy.

## 9. Uruchomienie

Z katalogu wdrożenia wykonać po kolei:

```text
docker compose config
docker compose build --pull
docker compose up -d
docker compose ps
```

Jeżeli używany jest gotowy ZIP, przed uruchomieniem porównać jego SHA-256 oraz pliki z `deployment-manifest.json`. Jeżeli używane są źródła, przejść na dokładny, zweryfikowany commit, nie na ruchomy HEAD i nie na katalog z niezapisanymi zmianami.

Po uruchomieniu sprawdzić:

```text
curl -i https://NAZWA-DNS/health/live
curl -i https://NAZWA-DNS/health/ready
curl -i https://NAZWA-DNS/login/callback
docker compose ps
```

Oczekiwane wyniki:

- `/health/live`: HTTP 200;
- `/health/ready`: HTTP 200 i stan gotowy;
- `/login/callback` bez parametrów: krótka, bezpieczna strona błędu; bez stack trace, ścieżek i danych technicznych;
- broker nie publikuje własnego portu bezpośrednio do Internetu;
- certyfikat jest ważny, zaufany i odpowiada nazwie DNS;
- po restarcie kontenerów usługi wracają automatycznie;
- w logach nie ma sekretu, tokenu, kodu callbacku ani pełnego query stringu.

Zapisać dokładne digesty użytych obrazów brokera i Caddy oraz commit źródeł. Wykonać kopię wolumenu Caddy zawierającego stan certyfikatu albo opisać, dlaczego certyfikat może zostać bezpiecznie odtworzony.

## 10. Podłączenie AMC

Dopiero po odebraniu serwera zmienić w AMC Test zaufany adres główny w:

`src/AccessibleMediaController.Windows/Services/SonosAccountOwner.cs`

Stała `DefaultBrokerOrigin` ma zawierać wyłącznie root HTTPS zakończony ukośnikiem, na przykład:

```text
https://sonos.example.org/
```

Nie wpisywać tam `/login/callback`, `/login/start` ani starego `/sonos/callback`.

Jeżeli używany jest dotychczasowy Client ID, pozostawić `IntegrationApiKey` bez zmiany. Jeżeli Client ID jest nowy, zaktualizować go razem z konfiguracją serwera.

Zmiana adresu lub dostępności Sonosa musi w tym samym zadaniu objąć:

- rzeczywistą drogę wykonania;
- menu Plik i Konto Sonos;
- skrót kontekstowy Ctrl+F5;
- pełną pomoc;
- pomoc kontekstową Ctrl+F1;
- paletę poleceń Ctrl+Shift+K;
- dokumentację użytkownika;
- testy widoczności, dostępności i działania dla profilu AMC Test oraz publicznego.

Nie dodawać pól Client ID, Client Secret ani adresu brokera do zwykłego okna użytkownika. To stała konfiguracja integracji, nie ustawienie końcowego użytkownika.

## 11. Odbiór rzeczywisty

Testy automatyczne są wymagane, ale nie wystarczają. Należy rozdzielić w raporcie: zmianę źródeł, zaliczone testy, udany build, instalację, uruchomienie i prawdziwe działanie na sprzęcie.

### Serwer

- sprawdzić gotowość i żywotność;
- sprawdzić limitowanie prób logowania i bezpieczne odpowiedzi błędów;
- sprawdzić restart brokera podczas niezakończonej próby;
- potwierdzić jednorazowy odbiór wyniku oraz brak ponownego wydania tokenu;
- potwierdzić, że zły verifier PKCE nie zużywa prawidłowego wyniku;
- potwierdzić odnowienie tokenu;
- sprawdzić, że logi i monitoring nie zapisują sekretów ani callback query.

### AMC Test i konto Sonos

Z użytkownikiem wykonać:

1. pierwsze otwarcie okna Konto Sonos;
2. rozpoczęcie logowania i oficjalną zgodę w przeglądarce;
3. świadomą odmowę, a następnie nową udaną próbę;
4. zamknięcie i ponowne otwarcie okna konta;
5. restart AMC i odtworzenie zaszyfrowanego konta;
6. ręczne „Odnów dostęp”;
7. odczyt domów, grup i urządzeń;
8. wybór domu i grupy, ponowne otwarcie oraz zachowanie wyboru;
9. pauzę/wznowienie spacją, poprzedni/następny, przewijanie, zmianę głośności i wyciszenie;
10. ulubione, playlisty, własne strumienie i presety, w tym presety 10–12;
11. utratę sieci, błąd serwera i powrót po błędzie bez utraty zapisanych danych;
12. wylogowanie z domyślną odpowiedzią „Nie” i ponowne zalogowanie po świadomym potwierdzeniu.

### Klawiatura i NVDA

Sprawdzić żywym NVDA:

- początkowy fokus;
- Tab, Shift+Tab, strzałki, Enter, Spacja i Escape;
- powrót fokusu po Zapisz, Anuluj, zamknięciu i powrocie z przeglądarki;
- ponowne otwieranie okien i zapamiętane wybory;
- menu, pomoc Ctrl+F1, pełną pomoc i paletę Ctrl+Shift+K;
- czy listy domów, grup, urządzeń, ulubionych i playlist czytają wyłącznie nazwy użytkowe;
- czy NVDA nigdzie nie odczytuje nazwy klasy, rekordu, enuma, identyfikatora, adresu URL ani technicznego `ToString()`;
- czy niedostępne funkcje są ukryte albo uczciwie opisane, a nie reklamowane jako działające.

## 12. Zdarzenia Sonosa — poza tym etapem

Bieżący broker służy do logowania i odnawiania tokenów. Wdrożenie webhooków zdarzeń Sonosa jest osobnym zadaniem.

Sonos wymaga dla zdarzeń osobnego publicznego callbacku HTTPS, innego niż redirect URI OAuth, oraz weryfikacji podpisu `X-Sonos-Event-Signature`. Nie należy wpisywać przypadkowego callbacku zdarzeń ani obiecywać powiadomień czasu rzeczywistego w tym wdrożeniu. Do czasu osobnego projektu AMC może odczytywać stan na wejściu, po poleceniu i przez ostrożne odświeżanie.

## 13. Plan wycofania

Jeżeli nowy broker albo nowy build AMC nie przejdzie odbioru:

- nie instalować publicznego wydania ze zmienionym originem;
- pozostawić dotychczasowy AMC Test, jego zaszyfrowany zapis i usługi Hermesa bez zmian;
- przywrócić poprzedni `DefaultBrokerOrigin` w kandydacie;
- zatrzymać tylko nową, nieodebraną usługę po zachowaniu zanonimizowanej diagnostyki;
- usunąć tylko nowy callback Sonosa, jeżeli nie jest już używany;
- nie usuwać starego callbacku, starego brokera, starego klucza ani jedynego działającego pakietu.

Stary broker wolno wyłączyć dopiero po ustaleniu, że wszystkie wspierane instalacje korzystają z nowego originu i potrafią odnowić konto.

## 14. Pakiet zwrotny Sonos, który wykonawca ma mi oddać

Samo wdrożenie na serwerze i opis w wiadomości nie wystarczą. Wykonawca ma przygotować jeden bezsekretowy plik:

`AMC-SONOS-HANDOFF-RRRRMMDD.zip`

W archiwum mają znaleźć się co najmniej:

- `HANDOFF.md` — krótka instrukcja, co dokładnie wykonano i co pozostaje do zrobienia na komputerze z AMC;
- `MANIFEST.json` — maszynowo czytelny manifest opisany niżej;
- `SHA256SUMS.txt` — sumy SHA-256 wszystkich przekazanych plików;
- `SOURCE.md` — adres repozytorium, dokładna gałąź, pełny commit, ewentualny Pull Request i informacja, czy drzewo podczas budowy było czyste;
- `source.patch` albo pełne źródła zmienionych elementów, jeżeli commit nie jest dostępny w repozytorium, do którego mam dostęp;
- katalog `deploy/sonos-broker` albo gotowy bezsekretowy pakiet wdrożeniowy brokera z jego własnym manifestem;
- zmienione testy i dokładne polecenia ich uruchomienia;
- `SERVER_REPORT_REDACTED.md` — raport serwerowy bez sekretów;
- `TEST_RESULTS.md` — polecenia, kody wyjścia, liczba testów oraz uczciwy opis testów prawdziwych i syntetycznych;
- `ROLLBACK.md` — dokładny sposób powrotu do poprzedniego brokera i poprzedniego buildu AMC;
- `.env.example` zawierający wyłącznie nazwy zmiennych i wartości przykładowe.

`MANIFEST.json` ma zawierać co najmniej:

```text
schema_version
artifact_type
created_utc
source_repository
source_commit
source_branch
working_tree_clean
build_command
tests
files: path, size, sha256
secrets_included: false
```

Jeżeli wykonawca zmieni kod Windows AMC, nie może oddać wyłącznie gotowego instalatora. Musi przekazać źródła lub patch, dokładny commit i testy. Może dołączyć zbudowany instalator albo ZIP testowy, ale na moim komputerze będzie on traktowany jako materiał porównawczy. Docelowy AMC Test ma zostać zbudowany lokalnie ze sprawdzonych źródeł.

Pakiet zwrotny nie może zawierać:

- Sonos Client Secret;
- `.env` z rzeczywistymi wartościami;
- katalogu `secrets` z prawdziwym plikiem sekretu;
- access tokenu ani refresh tokenu Sonosa;
- kodu lub pełnego adresu callbacku z query stringiem;
- prywatnego klucza SSH;
- pliku Apple `.p8` ani Apple developer tokenu;
- surowych logów mogących zawierać poświadczenia;
- cache, `bin`, `obj`, zrzutów pamięci i innych niepotrzebnych plików roboczych.

`SERVER_REPORT_REDACTED.md` ma zawierać:

- nazwę i rolę serwera;
- publiczny origin oraz callback OAuth;
- informację, czy publiczną dostępność sprawdzono spoza Tailscale;
- system, architekturę, wersje Docker Engine i Compose;
- dokładny commit, wersję brokera i SHA-256 pakietu;
- digesty obrazów kontenerów;
- nazwy usług/kontenerów i sposób automatycznego startu;
- wynik `/health/live` i `/health/ready` bez nagłówków poufnych;
- wynik testów brokera;
- wynik prawdziwego logowania, odmowy, ponownego logowania i odnowienia;
- wersję i commit AMC Test, jeżeli zmieniano klienta;
- wynik testów funkcji Sonosa na prawdziwym sprzęcie;
- wynik testu NVDA i klawiatury, jeżeli wykonawca miał do nich dostęp;
- znane ograniczenia;
- plan aktualizacji, kopii zapasowej i wycofania;
- listę dostępów lub tymczasowych kluczy, które po odbiorze można odwołać.

Raport ma rozróżniać: zmienione źródła, zaliczone testy, udany build, wdrożony serwer, zainstalowany AMC, uruchomiony AMC i prawdziwy test na sprzęcie. Jedno nie jest dowodem drugiego.

## 15. Jak przekażę paczki do lokalnego sprawdzenia

Po otrzymaniu plików nie należy ich uruchamiać ani rozpakowywać do kanonicznego repozytorium. Należy zapisać je w osobnym katalogu:

`D:\Projekty Codex\AMC - pakiety do weryfikacji\`

Zalecany układ:

```text
D:\Projekty Codex\AMC - pakiety do weryfikacji\
  Sonos\RRRR-MM-DD\
  Apple Music\RRRR-MM-DD\
```

Następnie wystarczy powiedzieć Codexowi, że pliki znajdują się w tym dokładnym katalogu. Lokalny proces będzie następujący:

1. sprawdzenie nazw, rozmiarów, sum SHA-256 i manifestu bez uruchamiania plików;
2. kontrola, czy paczka nie zawiera sekretów, tokenów, prywatnych kluczy, niepotrzebnych binariów lub surowych logów;
3. porównanie źródeł z podanym commitem i GitHubem oraz przegląd zmian;
4. uruchomienie testów brokera i AMC w odizolowanym środowisku;
5. lokalny build AMC Test z dokładnie sprawdzonych źródeł;
6. osobne potwierdzenie wersji, sum i zawartości zbudowanego pakietu;
7. sprawdzenie, czy AMC nie nagrywa i czy bezpiecznie można zainstalować lub uruchomić nową wersję;
8. instalacja wyłącznie jako AMC Test;
9. prawdziwe testy konta, urządzeń, dźwięku, klawiatury i NVDA razem z użytkownikiem;
10. dopiero po akceptacji decyzja o wydaniu publicznym i usunięciu zbędnych artefaktów testowych.

Nie uruchamiamy w ciemno programu lub instalatora otrzymanego przez komunikator. Jeżeli źródeł nie da się powiązać z manifestem i dokładnym commitem, paczka wraca do uzupełnienia.

Serwerowej instalacji nie da się w całości zastąpić testem lokalnym. Kod, manifest i kontrakt brokera mogą zostać sprawdzone u mnie, ale stan firewalla, DNS, certyfikatu, kontenerów i magazynu sekretów musi również potwierdzić operator serwera. Potem z mojego komputera sprawdzimy publiczne endpointy i wykonamy prawdziwe logowanie.

## 16. Pakiet Apple Music dla tej samej osoby

Ta sama osoba może mieć dostęp do repozytorium i klucza Apple potrzebnego do Apple Music, ale nie wolno mieszać tego z brokerem Sonosa.

Dla obecnego AMC Test potrzebny jest gotowy Apple Music developer token JWT. Prywatny klucz `.p8` ma pozostać na bezpiecznym komputerze osoby z rolą Apple Developer Account Holder albo Admin. Token można wygenerować lokalnie skryptem repozytorium:

`narzedzia/apple-music/Utworz-DeveloperToken.ps1`

Wykonawca ma przygotować osobny bezsekretowy plik:

`AMC-APPLE-MUSIC-HANDOFF-RRRRMMDD.zip`

W nim mają znaleźć się:

- `HANDOFF.md` — opis wykonanej konfiguracji i tego, co mam sprawdzić;
- `MANIFEST.json` oraz `SHA256SUMS.txt`;
- `SOURCE.md` i `source.patch`, jeżeli zmieniano kod AMC;
- `TOKEN_INFO.md` z datą utworzenia, datą wygaśnięcia, przewidzianym katalogiem `pl` i informacją, jakim skryptem utworzono token, ale bez samego tokenu;
- `TEST_PLAN.md` z testami logowania MusicKit, biblioteki, wyszukiwania, odtwarzania DRM, pauzy, przewijania, głośności, zakończenia utworu, braku subskrypcji oraz NVDA;
- wyniki testów bez danych konta i poświadczeń.

Sam czasowy JWT ma wrócić jako osobny plik:

`apple-music-developer-token.jwt.txt`

Ten plik jest poświadczeniem. Nie może znaleźć się w zwykłym ZIP-ie, repozytorium, Issue, Pull Requeście, publicznym linku, zwykłej wiadomości ani prompcie agenta. Należy przekazać go uzgodnionym kanałem poufnym albo w zaszyfrowanym archiwum, a hasło podać innym kanałem. Do mnie nie należy przekazywać pliku `.p8`, Team ID, Key ID ani hasła do Apple ID.

Po otrzymaniu JWT lokalnie:

1. sprawdzę format i deklarowaną datę ważności bez wypisywania tokenu;
2. nie zapiszę tokenu w repozytorium ani dokumentacji;
3. wprowadzimy go przez okno Konto Apple Music w AMC Test, które zapisze go w Menedżerze poświadczeń Windows;
4. użytkownik zaloguje swoje Apple ID wyłącznie w oficjalnym oknie MusicKit;
5. sprawdzimy bibliotekę, wyszukiwanie, operacje dozwolone przez API i prawdziwe odtwarzanie DRM;
6. wykonamy odbiór klawiaturą i żywym NVDA;
7. osobno zapiszemy wynik: źródła, testy, build, instalacja i prawdziwe konto.

Szczegóły istniejącego wariantu są w `INSTRUKCJA_PRZYGOTOWANIA_APPLE_MUSIC_PL.md`.

Jeżeli w przyszłości ten serwer ma automatycznie wydawać krótkotrwałe developer tokeny Apple, należy przygotować osobne zlecenie, osobny endpoint, osobny magazyn sekretów i osobny audyt. Nie dodawać klucza Apple do kontenera, `.env`, wolumenu ani logów brokera Sonosa w ramach obecnego zadania.

## 17. Kryterium zakończenia

Zadanie jest zakończone dopiero wtedy, gdy jednocześnie:

- istnieje zweryfikowany, możliwy do odtworzenia deployment z dokładnym commitem i manifestem;
- publiczny HTTPS i callback działają;
- sekret Sonosa jest wyłącznie w chronionym magazynie serwera;
- prawdziwe logowanie, odmowa i odnowienie działają;
- AMC Test po restarcie widzi konto i prawdziwe urządzenia;
- podstawowe sterowanie działa na rzeczywistym Sonosie;
- NVDA i klawiatura przechodzą scenariusze odbiorcze;
- stary wariant nadal stanowi sprawdzony punkt powrotu;
- powstał kompletny pakiet zwrotny i zanonimizowany raport według punktów 14–16;
- pliki zostały niezależnie sprawdzone na moim komputerze przed lokalnym wdrożeniem.

Sama kompilacja, sam działający kontener albo samo HTTP 200 z endpointu stanu nie są dowodem zakończenia całej integracji.

## 18. Oficjalne źródła Sonosa

- Autoryzacja i wymagania redirect URI: https://docs.sonos.com/docs/authorize
- Utworzenie integracji Control: https://docs.sonos.com/docs/connected-home-get-started
- Parametry żądania autoryzacji: https://docs.sonos.com/reference/create-authorization-code
- Odnowienie tokenu: https://docs.sonos.com/reference/refreshtoken
- Control API: https://docs.sonos.com/docs/control
- Opcjonalne subskrypcje zdarzeń i podpisy: https://docs.sonos.com/docs/subscribe

