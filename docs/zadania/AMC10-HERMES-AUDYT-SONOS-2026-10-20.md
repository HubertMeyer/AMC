# AMC10 — odczytowy audyt dawnego brokera Sonos

Zakres: tylko odczyt. Nie zmieniono konfiguracji, usługi, kontenerów ani repozytoriów. Nie wykonano restartu, kopiowania danych uwierzytelniających, wdrożenia ani commitu.

1. Repozytorium

- Dokładna ścieżka `/home/test/projekty/amc-sonos-auth` nie istnieje.
- Znaleziony następca: `/home/test/projekty/amc-sonos-auth-refresh1`.
- Commit: `b27ed4b2e31fcc232677f9fe2f36aa36f237d1d3`.
- Gałąź: `master`.
- Niezapisane zmiany: nie.

2. `/etc/amc-sonos-auth/sonos.env`

- `SONOS_CLIENT_ID`: BRAK.
- `SONOS_CLIENT_SECRET`: BRAK.
- `SONOS_REDIRECT_URI`: BRAK.
- `SONOS_BROKER_PUBLIC_ORIGIN`: BRAK.
- Plik istnieje, ale aktywna konfiguracja używa nazw z prefiksem `AMC_SONOS_`, nie nazw wymienionych wyżej.

3. Identyfikator klienta

- TAK — zapisany identyfikator w aktywnej zmiennej `AMC_SONOS_CLIENT_ID` jest równy wskazanemu publicznemu identyfikatorowi.

4. Niesekretne adresy

- Publiczny adres brokera: `https://hermes.tail6caad7.ts.net`.
- Callback OAuth z konfiguracji: `https://hermes.tail6caad7.ts.net/sonos/callback`.

5. Uruchomienie brokera

- `amc-sonos-auth.service`: działa; plik usługi `/etc/systemd/system/amc-sonos-auth.service`.
- `amc-sonos-proxy.service`: działa; plik usługi `/etc/systemd/system/amc-sonos-proxy.service`.
- Kontenera Dockera dla brokera: brak.
- Reverse proxy: nginx; konfiguracja `/etc/amc-sonos-auth/nginx.conf`.

6. Endpointy zdrowia

- Lokalne `/health/live` i `/health/ready` na portach brokera i proxy: HTTP 404 — endpoint nieudostępniony pod wskazaną ścieżką.
- Publiczne `/health/live` i `/health/ready`: HTTP 404 — endpoint nieudostępniony pod wskazaną ścieżką.

7. Sekret i możliwość odnowienia

- TAK — w chronionym pliku istnieje niepusty sekret pod aktywną nazwą `AMC_SONOS_CLIENT_SECRET`; identyfikator klienta pasuje. Kod następcy zawiera obsługę mechanizmu `refresh_token`. Nie wykonywano rzeczywistego odnowienia.

8. Przeniesienie na niezależny serwer

- TAK — sekret można później zapisać bezpośrednio do chronionego pliku na nowym serwerze, bez przekazywania go przez czat. Należy użyć bezpiecznego kanału administracyjnego i uprawnień ograniczonych do usługi.

9. Inne magazyny

- Nie dotyczy: sekret jest obecny w `/etc/amc-sonos-auth/sonos.env` pod nazwą `AMC_SONOS_CLIENT_SECRET`.
- Nie stwierdzono kontenera ani pliku Compose brokera. Nie odczytywano ani nie ujawniano wartości danych uwierzytelniających.
