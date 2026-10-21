# FRONTIER-001 — Frontier Smart przez FSAPI

Status: **Gotowe w źródłach AMC Test — przed instalacją i odbiorem na prawdziwym urządzeniu**

Data rozpoczęcia: 2026-10-21

## Polecenie użytkownika i źródła

Użytkownik chce w istniejącym Menedżerze sesji pod `Ctrl+Shift+S` włączyć nową
sesję „Frontier Smart”, skonfigurować lub wykryć własne urządzenie, a następnie
sprawdzić rzeczywiste możliwości sterowania. Presety i pozostałe funkcje mają
korzystać ze wspólnych wzorców AMC i WiiM tam, gdzie FSAPI rzeczywiście je
udostępnia.

Materiały wskazane przez użytkownika:

- dokumentacja FSAPI: <https://github.com/flammy/fsapi/blob/master/FSAPI.md>;
- znane obrazy firmware: <https://github.com/cweiske/frontier-silicon-firmwares/>;
- narzędzia i analiza firmware:
  <https://github.com/MatrixEditor/fsapi-tools> oraz
  <https://matrixeditor.github.io/fsapi-tools/firmware-analysis.html>.

## Zakres bieżącego etapu

- nowa sesja dostępna początkowo tylko w profilu AMC Test;
- włączenie, wyłączenie, kolejność i konfiguracja przez istniejący Menedżer
  sesji, bez drugiego konkurencyjnego kreatora;
- wykrywanie SSDP oraz ręczne podanie lokalnego adresu IP;
- weryfikacja PIN-u przez rzeczywisty odczyt urządzenia; PIN poza `state.json`,
  osobno dla profilu wydania w Menedżerze poświadczeń Windows;
- zapis nazwy, adresu, wersji firmware i wybranego urządzenia;
- odczyt stanu, odtwarzanie/pauza, poprzedni/następny, głośność i wyciszenie;
- dostępne tryby i presety pobierane z urządzenia, bez założenia stałej listy;
- wspólny model nazw, menu, pomocy, palety i wykonania poleceń;
- automatyczne testy protokołu, zapisu i powierzchni poleceń oraz ręczny odbiór
  klawiaturą i NVDA na urządzeniu użytkownika.

## Zachowanie użytkowe i komunikaty czytnika

- Menedżer sesji pokazuje celową nazwę „Frontier Smart”, stan włączenia i
  lokalnie znaną gotowość. Samo otwarcie listy nie skanuje sieci.
- „Konfiguruj…” otwiera okno „Urządzenia Frontier Smart”. Lista, pola i
  przyciski mają jawne nazwy użytkowe; obiekty, enumy i identyfikatory nie są
  tekstem dostępnościowym.
- Pole PIN jest chronione. Zwykłe listy i komunikaty nie pokazują PIN-u ani
  pełnych adresów żądań FSAPI.
- Automatyczne wykrywanie rozpoczyna się tylko po jawnym poleceniu użytkownika.
  Ręczny adres pozostaje dostępny, gdy SSDP jest blokowane przez sieć.
- Po Zapisz, Anuluj, błędzie i ponownym otwarciu fokus wraca do właściwej listy
  albo pola, a zaznaczenie zapisanego urządzenia jest zachowane.

## Różnice względem WiiM

- Frontier Smart używa lokalnego XML FSAPI i PIN-u, a WiiM własnego protokołu
  HTTP bez PIN-u.
- Lista trybów oraz lista presetów pochodzą z urządzenia i mogą różnić się
  pomiędzy firmware. AMC nie reklamuje trybu albo presetu, którego urządzenie
  nie zwróciło.
- Nie jest tworzona sesja powiadomień FSAPI (`CREATE_SESSION`), aby nie
  unieważniać połączenia aplikacji UNDOK/SmartRadio. Stan jest odczytywany
  krótkimi żądaniami z PIN-em.

## Uzasadnienie i bezpieczeństwo

- `GET_MULTIPLE` jest używane dla migawki, z bezpiecznym powrotem do
  pojedynczych `GET` w starszym firmware.
- Klient przyjmuje wyłącznie lokalne adresy IP, nie podąża za przekierowaniami,
  ogranicza czas i rozmiar odpowiedzi oraz bezpiecznie parsuje XML bez DTD.
- Wydanie publiczne pozostaje bez tej sesji do czasu odbioru na prawdziwym
  urządzeniu i osobnej decyzji o publikacji.

## Zmienione miejsca

- `src/AccessibleMediaController.Core/Devices/FrontierSmart/` — ograniczony do
  sieci lokalnej klient FSAPI, bezpieczny parser XML, wykrywanie SSDP oraz
  modele migawki, trybów i presetów;
- `src/AccessibleMediaController.Core/Configuration/` — opcjonalny, zgodny
  wstecz zapis urządzeń Frontier i bieżącego wyboru;
- `src/AccessibleMediaController.LiteHost/` — koordynator urządzeń, magazyn
  PIN-u w Menedżerze poświadczeń Windows oraz wąskie operacje hosta;
- `src/Shared/ReleaseProfileContract.cs` i
  `wxlite/amc_wx_lite/release_profile.py` — możliwość dostępna wyłącznie w
  profilu AMC Test;
- `wxlite/amc_wx_lite/frontier_smart_source.py`, `host_client.py`, `gui.py`,
  `navigation.py`, `session_order.py` — sesja, konfiguracja, lista urządzeń,
  odtwarzacz, tryby i presety;
- `wxlite/amc_wx_lite/shortcuts.py`, `menu_model.py`, `search_catalog.py`,
  `search_sources.py`, `session_options.py` — wspólna powierzchnia poleceń,
  pomocy, palety i nazw;
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/` oraz
  `wxlite/tests/test_frontier_smart_session.py` — kontrakt protokołu,
  bezpieczeństwa, profilu, nazw dostępnościowych i klawiatury.

## Testy i rzeczywiste wyniki

- 21.10.2026: kompilacja `AccessibleMediaController.LiteHost` w konfiguracji
  Release przeszła z **0 ostrzeżeń i 0 błędów**.
- 21.10.2026: pełne **25/25 zestawów testów protokołu LiteHost** przeszło,
  w tym walidacja lokalnych adresów, odrzucanie XML z DTD, jawne etykiety
  trybów/presetów oraz brak adresu i technicznych reprezentacji w danych
  czytanych przez NVDA.
- 21.10.2026: ukierunkowana bramka Python przeszła **72/72 testy**.
- 21.10.2026: pełna bramka Python przeszła **1926 testów**, **110 testów
  środowiskowych celowo pominięto**, a **11 podtestów** również przeszło.
- Pierwsza promocja kandydata z rewizji `c3258214` ponownie zaliczyła pełną
  bramkę Python i odizolowany start paczki `1debd5a9`, po czym zatrzymała się
  bez podmiany stałej instalacji: starszy manifest AMC Test nie znał jeszcze
  sesji Frontier Smart, a updater wymagał identycznej listy sesji.
- Walidator migracji nadal wymaga dokładnie tej samej tożsamości, kanału,
  katalogów i przestrzeni poświadczeń, lecz przyjmuje starszy podzbiór znanych
  sesji i możliwości niezależnie od ich dawnej kolejności. Nieznana sesja lub
  możliwość nadal powoduje odmowę. Nowy kontrakt przeszedł **29/29 testów
  launchera i updatera** oraz **52/52 ukierunkowane testy profili i pakowania**.
  Testy launchera/updatera są od tej pory obowiązkową bramką skryptu promocji.
- To są wyniki źródeł i kompilacji. Nie są jeszcze dowodem instalacji ani
  połączenia z fizycznym radiem; te dwa wyniki zostaną zapisane osobno.

## Znane ograniczenia i dalszy odbiór

- Środowisko deweloperskie nie ma urządzenia FSAPI, więc automatyczne testy nie
  zastąpią odbioru użytkownika.
- Wykrywanie SSDP zależy od multicastu w lokalnej sieci; ręczny adres jest
  obowiązkowym obejściem.
- Dokładne węzły wspierane przez konkretny firmware zostaną potwierdzone dopiero
  po pierwszym połączeniu.
- Bieżący etap nie dodaje nagrywania, historii odtwarzania ani przewijania
  urządzenia. Polecenia, których sesja nie obsługuje, są ukryte w jej menu i
  pomocy albo odmawiane z komunikatem zamiast wysyłania przypadkowego żądania.
- Ręczny odbiór obejmie `Ctrl+Shift+S`, pierwsze włączenie i konfigurację,
  `Ctrl+F5`, wykrywanie, ręczny adres, błędny i prawidłowy PIN, Enter oraz
  dwuklik na liście urządzeń, powrót fokusu po Zamknij, ponowne otwarcie,
  odtwarzanie, głośność, wyciszenie, tryby i presety z NVDA.

## Migracja, wersja i commit

Nowa sekcja konfiguracji jest opcjonalna i nie wymaga migracji istniejących
profili. Profil publiczny nie otrzymuje możliwości `session.frontier-smart`.
Commit źródłowy implementacji i testów: `412adf67` —
`feat(amc): dodaj Frontier Smart i domknij poprawki Radia`. Identyfikator
poprawki zgodnej migracji profilu oraz zainstalowanej kompilacji zostanie
dopisany po następnej promocji AMC Test. Nie publikować ani nie promować do
profilu publicznego bez nowej zgody użytkownika.
