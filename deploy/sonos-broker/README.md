# Niezależne wdrożenie brokera Sonos

Ten katalog uruchamia jedną instancję brokera AMC za Caddy. Caddy obsługuje
publiczny HTTPS, a broker nie publikuje własnego portu. Rozwiązanie nie korzysta
z Hermesa i nie przechowuje tokenów użytkowników na dysku.

## Wymagania

- mały, stale działający serwer Linux z Docker Engine i wtyczką Compose;
- publiczna nazwa DNS wskazująca na ten serwer oraz dostępne porty 80 i 443;
- integracja typu Control utworzona w Sonos Integration Manager;
- jej publiczny identyfikator oraz sekret;
- dokładny redirect URI `https://NAZWA-DNS/login/callback` wpisany w portalu
  Sonos.

Broker ma pamięciowy magazyn dziesięciominutowych prób logowania, dlatego w tym
wariancie działa dokładnie jedna, stale uruchomiona replika. Hosting zasypiający
albo skalujący usługę do zera może przerwać logowanie między rozpoczęciem a
callbackiem i nie jest właściwym miejscem dla obecnej wersji.

## Przygotowanie bez ujawniania sekretu

1. Skopiuj `.env.example` do `.env` i wpisz publiczną nazwę DNS oraz
   identyfikator klienta. Ten plik nie zawiera sekretu.
2. Utwórz katalog `secrets` z prawami dostępu tylko dla administratora serwera.
3. Umieść sam sekret, bez nazwy zmiennej i bez dodatkowych wierszy, w
   `secrets/sonos_client_secret.txt`. Plik jest ignorowany przez Git i trafia
   do kontenera przez mechanizm Docker secrets.
4. W portalu Sonos wpisz dokładnie
   `https://NAZWA-DNS/login/callback`. Nazwa integracji będzie widoczna
   użytkownikowi na oficjalnej stronie zgody Sonosa.

Sekretu nie należy podawać w argumentach polecenia, commitować, dołączać do ZIP-a
ani wpisywać do `.env`. AMC dla Windows nigdy go nie otrzymuje.

## Uruchomienie i kontrola

Z katalogu `deploy/sonos-broker` operator serwera wykonuje:

```text
docker compose config
docker compose build --pull
docker compose up -d
docker compose ps
```

Następnie sprawdza przez publiczny adres:

- `/health/live` — proces działa;
- `/health/ready` — konfiguracja Sonosa jest kompletna;
- `/login/callback` bez parametrów — bezpieczna strona błędu, bez danych
  technicznych.

Caddy celowo nie ma włączonego dziennika dostępu, ponieważ query callbacku
zawiera krótkotrwały kod Sonosa i `state`. Logi aplikacji również filtrują
standardowy wpis żądania ASP.NET. Po pierwszym uruchomieniu trzeba zapisać
rzeczywisty digest obu obrazów kontenerów i wykonać kopię wolumenu Caddy, który
przechowuje stan certyfikatu.

## Odbiór przed włączeniem AMC

1. Potwierdzić ważny certyfikat oraz `200` z `/health/ready`.
2. Wykonać próbę zgody, odmowy, wygaśnięcia i ponowienia na zewnętrznym koncie.
3. Sprawdzić odnowienie tokenu po ponownym uruchomieniu AMC.
4. Dopiero wtedy wpisać publiczny origin do `SonosIntegrationDefaults`, włączyć
   `BrokerAvailable`, zbudować AMC Test i przeprowadzić odbiór z NVDA.
5. Profil publiczny odsłonić dopiero po osobnym odbiorze czystej instalacji.

Źródła wymagań Sonosa:

- https://docs.sonos.com/docs/authorize
- https://docs.sonos.com/docs/connected-home-get-started
