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

## Materiał do dokumentacji użytkownika

W Menedżerze sesji polecenie „Konfiguruj…” dla Sonosa prowadzi do istniejącego
okna konta. Rozpoczęcie logowania ma otworzyć oficjalną stronę Sonosa, a po
ukończeniu użytkownik wraca do AMC i wybiera sprawdzenie wyniku. AMC nie zna
i nie przechowuje sekretu integracji Sonos. Tokeny użytkownika są przechowywane
lokalnie przez istniejący magazyn chroniony systemem Windows.

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
- Produkcja wymaga HTTPS. Nie dodano ślepego zaufania do
  `X-Forwarded-Proto`; konfiguracja reverse proxy zależy od wybranego hostingu.
- Publiczny profil AMC nadal nie udostępnia Sonosa. Bieżący prywatny AMC Test
  nadal używa dotychczasowego brokera; przełączenie originu nastąpi dopiero po
  rzeczywistym wdrożeniu i odbiorze.

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
- `AccessibleMediaController.sln`
- `docs/zadania/README.md`

## Testy i wynik

- `dotnet build src/AccessibleMediaController.SonosBroker/AccessibleMediaController.SonosBroker.csproj -c Release --no-restore`
  — sukces, 0 ostrzeżeń, 0 błędów.
- `dotnet run --project tests/AccessibleMediaController.SonosBroker.SmokeTests/AccessibleMediaController.SonosBroker.SmokeTests.csproj -c Release`
  — 13/13 testów przeszło.
- `dotnet build AccessibleMediaController.sln -c Release --no-restore` — sukces;
  nowy broker i jego testy kompilują się razem z całym rozwiązaniem.
- Testy obejmują: brak i częściową konfigurację, zgodność originu i callbacku,
  PKCE, jednorazową sesję, zły verifier bez utraty wyniku, ochronę przed drugim
  callbackiem, wygaśnięcie, równoległy limit pojemności, dokładny adres Sonosa,
  serwerową wymianę kodu, odnowienie z rotacją i bez rotacji oraz zgodność
  endpointów start/odmowa/wynik z klientem AMC.
- Integracyjny test HTTP działał wyłącznie na lokalnym porcie w środowisku
  `Development`; nie otworzył przeglądarki, nie użył sieci Sonosa, konta ani
  głośnika.
- Nie wykonano instalacji, publikacji, logowania ani wdrożenia publicznego.

## Znane ograniczenia

- Brak publicznej domeny, certyfikatu, produkcyjnych danych integracji i wpisu
  callbacku w portalu Sonos. Tych danych nie wolno wymyślać ani zapisywać w Git.
- Magazyn sesji jest pamięciowy i przeznaczony dla jednej instancji. Skalowanie
  na wiele replik wymaga wspólnego atomowego magazynu.
- Reverse proxy wymaga osobnej listy zaufanych adresów. Broker nie ufa
  dowolnemu nagłówkowi przekazanemu przez Internet.
- Nie wykonano ręcznego odbioru NVDA istniejącego okna konta ani prawdziwego
  odnowienia tokenu. Potrzebna jest obecność użytkownika.
- Pomoc `Ctrl+F1`, pełna pomoc i paleta nie zmieniają się w tym etapie, ponieważ
  nie dodano polecenia ani nie odsłonięto Sonosa w żadnym nowym profilu.

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
- Commit źródeł i testów: do uzupełnienia po lokalnym zatwierdzeniu.
- Instalacja AMC: bez zmian.
- Publikacja: brak.
