# Broker OAuth Google/YouTube dla AMC Public

Ten katalog przygotowuje wąski broker wymiany tokenów dla publicznego wydania
AMC. Aplikacja wykonuje logowanie w przeglądarce z PKCE i lokalnym powrotem na
`127.0.0.1`. Broker przyjmuje wyłącznie dwa granty klienta AMC, dodaje sekret
po stronie serwera i przekazuje żądanie do oficjalnego punktu Google.

Broker nie jest stroną logowania, nie przyjmuje hasła Google i nie przechowuje
tokenów. Logowanie, odświeżanie i cofnięcie dostępu pozostają rozdzielone:

- wymiana kodu i odświeżanie: własny broker `/v1/google/token`;
- cofnięcie dostępu: bezpośrednio
  `https://oauth2.googleapis.com/revoke` z aplikacji;
- tokeny użytkownika: Menedżer poświadczeń Windows bieżącego profilu AMC.

## 1. Osobny projekt Google Cloud

Utwórz projekt przeznaczony wyłącznie dla AMC Public. Nie używaj prywatnego
projektu AMC Test. W projekcie:

1. włącz YouTube Data API v3;
2. skonfiguruj zewnętrzny ekran zgody produkcyjnej;
3. ustaw dokładną publiczną nazwę aplikacji, adres pomocy oraz zweryfikowaną
   domenę należącą do operatora;
4. podaj stronę główną, politykę prywatności i warunki korzystania na tej samej
   domenie HTTPS;
5. zadeklaruj tylko zakres
   `https://www.googleapis.com/auth/youtube.readonly`;
6. utwórz klienta OAuth typu `Aplikacja komputerowa`, przeznaczonego dla AMC
   Public na Windows;
7. pobrany plik JSON przechowuj poza repozytorium. Wzorce jego typowych nazw są
   ignorowane przez Git, ale nie zastępuje to kontroli przed commitem.

Identyfikator klienta można umieścić w publicznym pakiecie. Pole
`client_secret` z pobranego JSON-u wolno ustawić wyłącznie jako sekret Workera;
nie wolno go kopiować do źródeł, zasobów aplikacji, logów ani poleceń procesu.

## 2. Konfiguracja Workera

1. Odtwórz przypięte zależności poleceniem `npm ci`. Nie wdrażaj z drzewa
   zależności innego niż zapisane w `package-lock.json`.
2. Skopiuj `wrangler.jsonc.example` do ignorowanego pliku `wrangler.jsonc`.
3. Wpisz bezpieczny identyfikator klienta do `GOOGLE_OAUTH_CLIENT_ID`.
4. Skonfiguruj własną domenę HTTPS dla Workera. Nie pozostawiaj produkcyjnego
   brokera wyłącznie na współdzielonym adresie `workers.dev`.
5. Ustaw sekret interaktywnie, bez umieszczania wartości w historii powłoki:

   `npx wrangler secret put GOOGLE_OAUTH_CLIENT_SECRET`

6. Uruchom testy: `npm test`.
7. Wdróż dopiero po jawnym sprawdzeniu konfiguracji: `npm run deploy`.
8. Sprawdź `GET https://twoja-domena/health`. Poprawny wynik ma status 200 i
   `schemaVersion` równy 1. Odpowiedź nie może zawierać identyfikatora klienta
   ani sekretu.

Zdalne logi są wyłączone w konfiguracji przykładowej. Przed wdrożeniem należy
również potwierdzić ustawienia retencji i brak logowania treści żądań na
poziomie konta Cloudflare.

## 3. Bezpieczne zasoby aplikacji

Po utworzeniu klienta i uruchomieniu brokera wykonaj lokalnie:

```powershell
.\Prepare-PublicConfig.ps1 `
  -ClientId "1234567890-nazwa.apps.googleusercontent.com" `
  -BrokerEndpoint "https://oauth.twoja-domena.example/v1/google/token"
```

Skrypt waliduje wartości i zapisuje wyłącznie:

- `wxlite/amc_wx_lite/youtube-oauth-public-client-id.txt`;
- `wxlite/amc_wx_lite/youtube-oauth-public-token-broker.txt`;
- ignorowany lokalny `wrangler.jsonc` bez sekretu.

Skrypt nie przyjmuje i nie zapisuje sekretu. Budowanie profilu Public odrzuca
niepełną konfigurację i usuwa zasoby prywatnego klienta AMC Test.

## 4. Odbiór przed wydaniem

Przed uznaniem klienta za gotowy trzeba osobno potwierdzić:

- weryfikację domeny i marki w Google;
- zgodność adresów strony, polityki i warunków na ekranie zgody;
- pierwsze logowanie czystego konta, odmowę, anulowanie i wygaśnięcie;
- odświeżenie tokenu przez broker bez ponownego logowania;
- cofnięcie dostępu, usunięcie oznaczonych danych konta i zachowanie publicznych
  źródeł dodanych ręcznie;
- automatyczne usunięcie nieodświeżonych danych konta po 30 dniach;
- brak sekretu i tokenów w pakiecie, wierszu poleceń, logach i raportach;
- zachowanie fokusu, etykiet i komunikatów w rzeczywistym odbiorze NVDA.

Testy lokalne i zdrowy endpoint nie zastępują akceptacji Google ani
rzeczywistego odbioru publicznego klienta.
