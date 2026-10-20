# Broker logowania Sonos dla AMC

Ten projekt jest serwerową częścią logowania Sonos. Aplikacja AMC nie otrzymuje
sekretu integracji: wysyła do brokera jednorazowe wyzwanie PKCE, otwiera
oficjalną stronę Sonosa, a po powrocie odbiera wynik tylko raz za pomocą
weryfikatora znanego lokalnie.

## Konfiguracja

Broker czyta wyłącznie te wartości środowiskowe:

- `SONOS_BROKER_PUBLIC_ORIGIN` — publiczny adres główny HTTPS, zakończony `/`;
- `SONOS_CLIENT_ID` — klucz z portalu integracji Sonos;
- `SONOS_CLIENT_SECRET` — sekret przechowywany wyłącznie na serwerze;
- `SONOS_REDIRECT_URI` — dokładnie
  `SONOS_BROKER_PUBLIC_ORIGIN` + `login/callback`;
- `SONOS_TRUSTED_PROXIES` — opcjonalna, rozdzielona przecinkami lista dokładnych
  adresów IP reverse proxy, od których wolno przyjąć `X-Forwarded-For` i
  `X-Forwarded-Proto`.

Brak czterech wartości Sonosa uruchamia bezpieczny stan
nieskonfigurowany. Podanie tylko części albo adresu HTTP zatrzymuje start.
Pusta lista proxy oznacza, że nagłówki przekazywane nie są honorowane. Nazwy
hostów, zakresy i adresy ogólne nie są przyjmowane; trzeba podać najwyżej 16
konkretnych adresów IP infrastruktury, która naprawdę kończy TLS.
Sekretów nie wolno umieszczać w repozytorium, pakiecie AMC, pliku instalatora
ani argumentach wiersza poleceń widocznych innym procesom.

## Endpointy

- `POST /login/start` — tworzy dziesięciominutową sesję i adres logowania;
- `GET /login/callback` — odbiera kod albo odmowę z Sonosa;
- `POST /login/result` — jednorazowo wydaje wynik właścicielowi verifiera;
- `POST /login/refresh` — odnawia token bez ujawniania sekretu aplikacji;
- `GET /health/live` — proces działa;
- `GET /health/ready` — `200` tylko po pełnej konfiguracji Sonosa.

Odpowiedzi mają `no-store`. Zwykły log żądań zawierający query string jest
wyłączony, ponieważ callback przenosi krótkotrwały kod autoryzacyjny. Broker
nie zapisuje tokenów na dysku; niezakończone sesje i odebrane tokeny istnieją
krótko w pamięci procesu, a wynik można odebrać tylko raz.

## Warunki wdrożenia publicznego

1. Utworzyć produkcyjną integrację w portalu Sonos i wpisać dokładny callback
   HTTPS.
2. Uruchomić jedną instancję brokera za prawdziwym TLS. Bieżący magazyn sesji
   jest pamięciowy; restart bezpiecznie unieważnia rozpoczęte logowania, a
   wiele replik wymagałoby wspólnego atomowego magazynu.
3. Jeżeli TLS kończy reverse proxy, wpisać jego dokładny adres IP w
   `SONOS_TRUSTED_PROXIES`. Bez tej wartości broker oczekuje, że żądanie
   produkcyjne dociera do ASP.NET bezpośrednio jako HTTPS. Nie wolno wpisywać
   tam publicznych klientów ani szerokiego zakresu sieci.
4. Sprawdzić `/health/ready`, logowanie na zewnętrznym koncie, odnowienie po
   wygaśnięciu tokenu, odmowę, restart brokera i ograniczenie tempa.
5. Dopiero po tym ustawić publiczny origin w profilu AMC i odsłonić Sonosa.

Nie uruchamiaj prawdziwego logowania podczas automatycznych testów. Testy w
`tests/AccessibleMediaController.SonosBroker.SmokeTests` używają atrap Sonosa
i lokalnego portu HTTP wyłącznie w środowisku `Development`.

## Źródła kontraktu

- https://docs.sonos.com/docs/authorize
- https://docs.sonos.com/reference/create-authorization-code
- https://docs.sonos.com/reference/refreshtoken
