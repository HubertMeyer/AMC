# Broker Sonos — przekazanie dla systemd i Cloudflare Tunnel

Ten dokument dotyczy bezkontenerowego wdrożenia brokera na Ubuntu x86_64.
Wartości przygotowane przez operatora dla `sonos.stareaudycje.pl` są zgodne z
kontraktem aplikacji. Paczka nie zawiera sekretu ani tokenów.

## Zawartość i uruchomienie

- główny plik: `app/AccessibleMediaController.SonosBroker.dll`;
- target: `.NET 8`, `linux-x64`, framework-dependent, bez apphosta;
- wymagany runtime: ASP.NET Core Runtime 8;
- uruchomienie: `dotnet /opt/sonos-broker/current/AccessibleMediaController.SonosBroker.dll`;
- broker powinien słuchać wyłącznie na `http://127.0.0.1:5080`.

Minimalny snapshot źródeł i testów znajduje się w katalogu `source`. Na
komputerze z SDK .NET 8 testy uruchamia polecenie zapisane także w
`deployment-manifest.json`:

```text
dotnet run --project source/tests/AccessibleMediaController.SonosBroker.SmokeTests/AccessibleMediaController.SonosBroker.SmokeTests.csproj --configuration Release
```

Oczekiwany wynik: `Wszystkie testy brokera Sonos przeszły: 20.` Testy używają
atrap Sonosa i lokalnego portu; nie logują konta i nie sterują głośnikami.

## Dokładna konfiguracja

Broker czyta następujące wartości Sonosa:

```text
ASPNETCORE_URLS=http://127.0.0.1:5080
ASPNETCORE_ENVIRONMENT=Production
SONOS_BROKER_PUBLIC_ORIGIN=https://sonos.stareaudycje.pl/
SONOS_CLIENT_ID=b051a8f0-499c-4deb-9f66-843a752c36e4
SONOS_CLIENT_SECRET_FILE=/run/credentials/sonos-broker.service/sonos_client_secret
SONOS_REDIRECT_URI=https://sonos.stareaudycje.pl/login/callback
SONOS_TRUSTED_PROXIES=127.0.0.1
```

`ASPNETCORE_URLS` i `ASPNETCORE_ENVIRONMENT` są standardowymi ustawieniami
ASP.NET Core. `SONOS_CLIENT_SECRET_FILE` musi być bezwzględną ścieżką do
niepustego, jednowierszowego pliku. Nie wolno jednocześnie ustawiać
`SONOS_CLIENT_SECRET`.

TTL i limity nie mają obecnie zmiennych środowiskowych. Są celowo stałe:

- sesja logowania: 10 minut;
- maksymalnie 1024 aktywne sesje w pamięci jednej instancji;
- `/login/start`: 10 żądań na minutę na efektywny adres klienta;
- `/login/result`: 30 żądań na minutę na adres;
- `/login/refresh`: 12 żądań na minutę na adres;
- maksymalny request body: 4096 bajtów;
- maksymalna odpowiedź OAuth czytana od Sonosa: 64 KiB.

Poziomy logów można ustawiać standardowymi kluczami ASP.NET Core, na przykład
`Logging__LogLevel__Default=Information`. Nie są wymagane do startu.

## Cloudflare Tunnel, adres klienta i HTTPS

Middleware nagłówków przekazanych działa przed kontrolą HTTPS i limiterem.
Nagłówki są honorowane tylko wtedy, gdy bezpośredni peer ma adres podany w
`SONOS_TRUSTED_PROXIES`. Dla lokalnego `cloudflared` jest to `127.0.0.1`.

- `X-Forwarded-For` zastępuje `RemoteIpAddress`; właśnie ten adres tworzy
  osobną partycję limitera. Test obejmuje wyczerpanie limitu jednego adresu i
  niezależne dopuszczenie drugiego.
- `X-Forwarded-Proto: https` ustawia bezpieczny schemat przed kontrolą
  produkcyjną. Bez poprawnego nagłówka żądanie po lokalnym HTTP otrzyma `400`
  z kodem `https_required`.
- `CF-Connecting-IP` nie jest potrzebny i nie jest bezpośrednio honorowany.
  Źródłem adresu dla aplikacji pozostaje `X-Forwarded-For` dostarczony przez
  jedyne zaufane proxy.
- Broker przyjmuje najwyżej jeden krok przekazania i wymaga symetrii nagłówków
  `X-Forwarded-For` oraz `X-Forwarded-Proto`.

## Ochrona logów

Broker nie dodaje logowania treści żądań ani nagłówków. Kategoria standardowego
logu żądań ASP.NET Core, która mogłaby zawierać query string callbacku, jest
wyłączona niezależnie od globalnego poziomu Debug lub Trace. Diagnostyka
nazwanego klienta HTTP `sonos-oauth`, który przenosi nagłówek Basic, kod i
refresh token, jest ograniczona co najmniej do poziomu Warning. Kod aplikacji
nie zapisuje wartości `code`, `state`, tokenów, sekretu ani nagłówka
`Authorization`.

Przy odbiorze należy mimo to przejrzeć `journalctl` po kontrolowanej odmowie i
błędzie oraz nie przekazywać surowego dziennika, dopóki operator nie potwierdzi
redakcji.

## Pamięć i pojedyncza instancja

Stan jest wyłącznie pamięciowy i przewidziany dla jednej stale działającej
instancji. Restart unieważnia rozpoczęte logowania. Limit systemd 300 MB jest
zgodny z małą aplikacją ASP.NET Core i twardym limitem 1024 krótkich sesji.
Kontrolny proces Release na Windows 24.10.2026, po odpowiedzi `200` z
`/health/ready`, zajmował w pięciu próbkach 48,59–50,26 MiB working set oraz
40,39–40,96 MiB private memory. To pomiar orientacyjny, a nie dowód dla
docelowego Linuksa. Po starcie oraz podczas kontrolowanej próby operator
powinien zapisać `MemoryCurrent` i `MemoryPeak` z systemd; przekroczenie limitu
nie może być maskowane automatycznym restartem.

## Kolejność odbioru

1. Zweryfikować SHA-256 ZIP-a i wszystkie pliki z manifestu.
2. Uruchomić testy ze snapshotu źródeł na hoście z SDK .NET 8.
3. Rozpakować `app` do nowego katalogu `/opt/sonos-broker/releases/<commit>` i
   dopiero potem atomowo przełączyć link `current`.
4. Sprawdzić lokalnie i publicznie `/health/live` oraz `/health/ready`.
5. Sprawdzić brak parametrów callbacku w dzienniku, rozdzielenie limitów dwóch
   adresów i zachowanie po restarcie w trakcie rozpoczętej sesji.
6. Nie wyłączać starego brokera ani starego callbacku przed świeżym logowaniem,
   odnowieniem tokenu i odbiorem AMC Test z NVDA.

Przed prawdziwym logowaniem autor musi dodać w tej samej integracji Sonos
redirect URI `https://sonos.stareaudycje.pl/login/callback`, bez usuwania
starego callbacku i bez rotowania sekretu.
