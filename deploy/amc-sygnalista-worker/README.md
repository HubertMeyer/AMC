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
- `REPORT_RATE_LIMITER` ogranicza nadużycia, a `REPORT_RESULTS` zapamiętuje
  kolejne etapy zgłoszenia. Ten sam `reportId` zwraca to samo issue i nie tworzy
  duplikatu; inna treść z tym samym identyfikatorem jest odrzucana.
- Pełna treść trafia wyłącznie do prywatnego repozytorium. Publiczne issue ma
  rodzaj, informację o logu i odsyłacz dla opiekuna do prywatnego wpisu.

## Przygotowanie do wdrożenia

1. Utwórz prywatne repozytorium `amc-support-intake` i etykiety `bug`,
   `enhancement`, `from-app` w obu repozytoriach.
2. Utwórz Cloudflare KV dla idempotencji i wpisz jego identyfikator do kopii
   `wrangler.jsonc.example` zapisanej jako `wrangler.jsonc`.
3. Utwórz fine-grained token GitHuba z prawem zapisu Issues tylko w publicznym
   AMC i prywatnym repozytorium zgłoszeń. Zapisz go poleceniem
   `wrangler secret put GITHUB_TOKEN`; nie zapisuj wartości do pliku.
4. Zaloguj Wrangler świadomie na właściwe konto Cloudflare. Bez samoczynnego
   otwierania przeglądarki można użyć
   `npx wrangler login --device --browser=false --use-keyring`, a podany adres
   i jednorazowy kod otworzyć samodzielnie. `--use-keyring` przechowuje dane
   OAuth w systemowym magazynie poświadczeń zamiast jawnego pliku.
5. Uruchom testy, a następnie `npm run deploy`. Własna domena nie jest wymagana;
   `workers_dev: true` publikuje usługę pod adresem HTTPS w `workers.dev`.
6. Sprawdź `/health` i kontrolowany raport testowy. Dopiero potem wpisz końcowy
   adres `https://.../v1/report` do pliku
   `wxlite/amc_wx_lite/problem-report-endpoint.txt` przed budową wydania.

Repozytorium celowo nie zawiera działającego endpointu, identyfikatora KV ani
tokenów. Samo zbudowanie AMC pozostawia więc formularz w bezpiecznym trybie
lokalnym.
