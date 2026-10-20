# Migracja z dawnego brokera Sonos

Ta instrukcja przenosi logowanie AMC do niezależnego brokera bez wyłączania
działającego wariantu na Hermesie przed odbiorem następcy. Nie przenosi tokenów
użytkowników i nie wymaga ponownego wdrażania sterowania głośnikami.

## Potwierdzony punkt wyjścia

- dawne źródła: `/home/test/projekty/amc-sonos-auth-refresh1`, commit
  `b27ed4b2e31fcc232677f9fe2f36aa36f237d1d3`;
- działające usługi: `amc-sonos-auth.service` i `amc-sonos-proxy.service`;
- reverse proxy: nginx;
- dotychczasowy redirect URI:
  `https://hermes.tail6caad7.ts.net/sonos/callback`;
- identyfikator integracji jest zgodny z AMC, a chroniona konfiguracja zawiera
  niepusty sekret. Wartość sekretu nie należy do tej instrukcji ani pakietu.

Odpowiedź `404` pod dawnymi adresami `/health/live` i `/health/ready` nie jest
dowodem awarii. Historyczna usługa nie udostępniała tych endpointów.

## Zasady bezpieczeństwa

1. Nie zatrzymywać usług na Hermesie i nie usuwać starego redirect URI, dopóki
   nowy broker, świeże logowanie i odnowienie tokenu nie przejdą odbioru.
2. Nie kopiować tokenów użytkownika. Po zmianie originu AMC wykonuje świeże,
   świadome logowanie do tej samej integracji.
3. Sekret przenieść wyłącznie bezpośrednio między chronionymi magazynami
   administratora. Nie umieszczać go w czacie, repozytorium, ZIP-ie, `.env`,
   argumentach poleceń ani logach.
4. Na nowym serwerze zapisać sekret jako pojedynczy wiersz w
   `secrets/sonos_client_secret.txt`, ograniczyć dostęp do administratora i
   usługi, a potem przekazać go kontenerowi przez Docker secrets.
5. Nie zmieniać ani nie usuwać istniejącego pliku `sonos.bin` na komputerze
   autora. Pozostaje bezpiecznym punktem powrotu dla zainstalowanej wersji AMC
   Test korzystającej z dawnego originu.

## Kolejność migracji

1. Przygotować stale działający serwer Linux, publiczny DNS oraz porty 80 i
   443. Hosting nie może zasypiać ani skalować pojedynczej instancji do zera.
2. Ustalić nowy adres, na przykład `https://sonos.example.org/`, i wynikający z
   niego callback `https://sonos.example.org/login/callback`.
3. W Sonos Integration Manager dodać nowy callback do tej samej integracji,
   pozostawiając dotychczasowy callback Hermesa. Sonos wymaga, aby
   `redirect_uri` odpowiadał jednemu z adresów zapisanych dla klucza:
   https://docs.sonos.com/docs/authorize
4. Skopiować `.env.example` do `.env`, wpisać wyłącznie nazwę hosta i publiczny
   identyfikator klienta. Sekret zapisać osobno zgodnie z zasadami powyżej.
5. Uruchomić `docker compose config`, następnie zbudować i uruchomić dokładnie
   jedną instancję brokera. Zachować wynik `docker compose ps` oraz digesty
   obrazów.
6. Potwierdzić publiczny HTTPS oraz `200` z `/health/live` i `/health/ready`.
   Wywołanie `/login/callback` bez parametrów ma zwrócić krótką stronę błędu,
   bez danych technicznych.
7. Z użytkownikiem wykonać świeże logowanie, odmowę, ponowne logowanie i
   odnowienie tokenu. Nie automatyzować konta ani poleceń głośników.
8. Dopiero po odbiorze wpisać nowy origin do AMC Test, włączyć dostępność
   brokera, zbudować kandydat i sprawdzić okno konta, `Ctrl+F5`, pomoc
   `Ctrl+F1`, pełną pomoc, menu i paletę `Ctrl+Shift+K` z NVDA.
9. Po potwierdzeniu ciągłości konta przygotować osobny publiczny profil AMC.
   Stary broker i callback wolno wyłączyć dopiero po ustaleniu, że żaden
   wspierany klient nie potrzebuje już odnowienia przez dawny origin.

## Wycofanie nieudanej próby

Jeżeli nowy broker nie przejdzie odbioru, nie instalować kandydata ze zmienionym
originem. Pozostawić działającą instalację AMC Test, jej zaszyfrowany magazyn i
usługi Hermesa bez zmian. Usunąć jedynie nowy, nieodebrany callback oraz
zatrzymać nowy serwer po zachowaniu diagnostyki niezawierającej sekretów.

