# AMC Sygnalista Worker

Worker przyjmuje zredagowany i jawnie zatwierdzony raport z AMC, ponownie
usuwa typowe dane prywatne, zapisuje pełną treść w prywatnym repozytorium
`amc-support-intake`, a w publicznym repozytorium AMC tworzy krótkie issue.
Użytkownik AMC nie potrzebuje konta GitHub.

## Bezpieczeństwo

- Token GitHuba jest wyłącznie sekretem Cloudflare Workera. Nie wolno umieszczać
  go w aplikacji, pliku endpointu, `wrangler.jsonc` ani repozytorium.
- Aplikacja nie ma wspólnego „sekretu aplikacji”, ponieważ taki sekret dałoby
  się wyjąć z publicznego instalatora.
- `REPORT_RATE_LIMITER` ogranicza nadużycia, a przypisany koordynator Durable
  Object serializuje operacje i trwale zapamiętuje kolejne etapy zgłoszenia.
  Ten sam `reportId` zwraca to samo issue i nie tworzy duplikatu; inna treść z
  tym samym identyfikatorem jest odrzucana.
- Pełna treść trafia wyłącznie do prywatnego repozytorium. Publiczne issue ma
  rodzaj, informację o logu i odsyłacz dla opiekuna do prywatnego wpisu.

## Przygotowanie do wdrożenia

1. Utwórz prywatne repozytorium `amc-support-intake` i etykiety `bug`,
   `enhancement`, `from-app` w obu repozytoriach.
2. Utwórz fine-grained token GitHuba z prawem zapisu Issues tylko w publicznym
   AMC i prywatnym repozytorium zgłoszeń. Nie zapisuj jego wartości do pliku,
   argumentu polecenia ani dziennika; będzie potrzebny dopiero w osobnym,
   interaktywnym etapie po bootstrapie Workera.
3. Zaloguj Wrangler świadomie na właściwe konto Cloudflare. Bez samoczynnego
   otwierania przeglądarki można użyć
   `npx wrangler login --device --browser=false --use-keyring`, a podany adres
   i jednorazowy kod otworzyć samodzielnie. `--use-keyring` przechowuje dane
   OAuth w systemowym magazynie poświadczeń zamiast jawnego pliku.
4. Bez przełączników zdalnych uruchom skrypt `Deploy-AMCSygnalistaWorker.ps1`
   bez adresu. Wykona czyste `npm ci`, testy i lokalne pakowanie, ale niczego nie
   wyśle ani nie utworzy lokalnej konfiguracji konta.
5. Pierwsze zdalne utworzenie Workera wykonaj jawnie z `-Bootstrap`. Skrypt
   tworzy z wersjonowanego wzoru lokalny `wrangler.jsonc`, który jest
   ignorowany przez Git. Do pierwszego wdrożenia tworzy też jednorazową kopię
   konfiguracji bez deklaracji nieistniejącego jeszcze sekretu, po czym zawsze
   ją usuwa. Worker zostaje wdrożony bez aktywowania endpointu w AMC.
   Migracja Wranglera tworzy powiązany koordynator Durable Object i jego
   magazyn; nie trzeba kopiować identyfikatora zasobu. Bootstrap odmawia
   działania, gdy Worker już istnieje.
   W tej krótkiej fazie `/v1/report` nie tworzy zgłoszeń, ponieważ nie ma
   jeszcze sekretu GitHuba.
6. Osobnym, jawnym poleceniem uruchom skrypt z `-SetGitHubToken`. Wrangler
   poprosi o wartość `GITHUB_TOKEN` w interaktywnym monicie. `secret put`
   tworzy i od razu wdraża nową wersję Workera; skrypt uprzedza o tym przed
   monitem, nie przyjmuje tokenu w parametrze i nie zapisuje go w pliku ani
   dzienniku. Po potwierdzeniu nazwy sekretu endpoint AMC nadal pozostaje
   wyłączony.
7. Uruchom właściwe wdrożenie z `-Deploy`. Dla zwykłego adresu `workers.dev`
   skrypt odczyta adres z potwierdzenia Wranglera; `-WorkerBaseUrl` jest potrzebny
   tylko przy własnym adresie albo gdy Cloudflare nie zwróci go w wyniku.
   Przed jakąkolwiek aktywacją skrypt wykonuje trzy próby bez tworzenia issue:
   `GET /health` musi zwrócić schemat 1, `GET /v1/report` musi zwrócić 405, a
   `POST /v1/report` z nieobsługiwaną wersją schematu musi zwrócić 400. Ta
   ostatnia próba potwierdza obecność sekretu, koordynatora Durable Object i
   limitera, lecz jest odrzucana przed limiterem i wywołaniem GitHuba. Dopiero
   jawne połączenie
   `-Deploy -ActivateEndpoint` zapisuje końcowy adres
   `https://.../v1/report` do
   `wxlite/amc_wx_lite/problem-report-endpoint.txt` przed budową wydania.
   Własna domena nie jest wymagana; `workers_dev: true` publikuje usługę pod
   adresem HTTPS w `workers.dev`.
8. Osobno wykonaj kontrolowany raport próbny i sprawdź prywatny oraz publiczny
   wpis. Skrypt wdrożeniowy celowo nie tworzy zgłoszenia bez tej decyzji.

Repozytorium celowo nie zawiera działającego endpointu ani tokenów. Konfiguracja
Durable Object jest wersjonowana, ale treść sekretu nigdy nie trafia do pliku.
Samo zbudowanie AMC pozostawia więc formularz w bezpiecznym trybie lokalnym.
