# AMC12 — profile wydania publicznego i testowego

## Status

**W trakcie — spójny fundament etapu 1 jest gotowy w źródłach i testach; nie
zbudowano, nie zainstalowano ani nie opublikowano profilu publicznego.**

Źródłowa, zatwierdzona specyfikacja pozostaje w pliku tylko do odczytu:
`D:\Projekty Codex\Accessible Multimedia Controller\AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`.

## Zakres etapu 1

- Dodano wersjonowany katalog dwóch profili wydania: `test` i `public`.
- Każdy profil ma osobną nazwę użytkową, identyfikator produktu i instalacji,
  kanał aktualizacji, katalog interfejsu, katalog danych rdzenia, pamięć
  podręczną, logi i przestrzeń nazw poświadczeń.
- Obecny AMC Test zachowuje istniejące katalogi, więc ten etap nie przenosi i
  nie zeruje danych użytkownika.
- Publiczny AMC ma od początku osobne katalogi i dopuszcza tylko sesje:
  Pliki lokalne, Radio, Podcasty i YouTube oraz WiiM. Sonos pozostaje ukryty do
  odbioru brokera, a Spotify i TIDAL są ukryte.
- Ten sam model możliwości filtruje kolejność `Ctrl+1–9`, Menedżer sesji,
  menu, pomoc `Ctrl+F1`, pełną pomoc klawiatury, paletę `Ctrl+Shift+K`,
  wykonanie poleceń sesji i zakres wyszukiwania we wszystkich usługach.
- Próba włączenia sesji niedopuszczonej w profilu jest odrzucana, a stary
  zapis kolejności nie może jej ponownie ujawnić.
- Narzędzie składania paczki przyjmuje `--profile test` albo
  `--profile public` i zapisuje w manifeście pełną tożsamość oraz listę
  możliwości. Odświeżenie istniejącej paczki nie może po cichu zmienić jej
  profilu.
- Interfejs odczytuje profil z jawnego środowiska uruchomieniowego albo z
  wersjonowanego manifestu paczki. Nieznany profil zatrzymuje wybór zamiast
  uruchamiać przypadkowy wariant.

## Materiał do dokumentacji użytkownika

AMC Test i przyszły publiczny AMC powstają z tego samego kodu, ale są dwoma
różnymi wydaniami. AMC Test zachowuje wszystkie sesje przeznaczone do prób.
Publiczny AMC pokazuje tylko Pliki lokalne, Radio, Podcasty i YouTube oraz
WiiM. Ukrytej usługi nie będzie ani w Menedżerze sesji, ani w menu, pomocy
`Ctrl+F1`, pełnej pomocy klawiatury i palecie `Ctrl+Shift+K`; jej stary skrót
również jej nie uruchomi.

Oba wydania mają osobne ustawienia, logi, pamięć podręczną i dane kont. Samo
uruchomienie jednego wydania nie zmienia danych drugiego. Planowane kopiowanie
wybranych danych z AMC Test do AMC będzie osobną, jawną czynnością opartą na
wersjonowanej migawce. Ten etap jeszcze jej nie udostępnia.

Nie ma jeszcze instalatora publicznego AMC. Kod i testy fundamentu nie są
dowodem kompilacji, instalacji ani publikacji.

## Uzasadnienie i decyzje

- Jedna definicja profilu jest bezpieczniejsza niż osobne listy w interfejsie,
  pomocy i pakowaniu. Zapobiega sytuacji, w której ukryta usługa nadal pojawia
  się w palecie albo daje się uruchomić skrótem.
- Profil testowy zachowuje dotychczasowe ścieżki. Zmiana ich w tym etapie
  stworzyłaby niepotrzebną migrację i mogłaby wyglądać jak utrata ustawień.
- Profil publiczny otrzymał nowe katalogi od pierwszego uruchomienia. Nie
  współdzieli żywej bazy, tokenów ani stanu nagrywania z AMC Test.
- Manifest przechowuje celowe identyfikatory i listy wartości modelu. Nazwy
  techniczne nie są używane jako etykiety kontrolek ani komunikaty NVDA.
- Korekta użytkownika z 18–19 października 2026 zastępuje wcześniejszy pomysł
  równoległego używania tych samych żywych magazynów. Dane wspólne mają być
  później przenoszone wyłącznie przez kontrolowaną migawkę AMC Test → AMC.

## Zmienione pliki

- `wxlite/amc_wx_lite/release_profile.py`
- `wxlite/amc_wx_lite/state_store.py`
- `wxlite/amc_wx_lite/profile_layout.py`
- `wxlite/amc_wx_lite/version_info.py`
- `wxlite/amc_wx_lite/session_order.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/tools/build_bundle.py`
- `wxlite/tests/test_release_profile.py`
- `wxlite/tests/test_bundle_layout.py`
- `docs/zadania/README.md`
- `docs/zadania/AMC12-profile-wydania-publicznego-i-testowego.md`

## Testy i wynik

- Testy profilu, kolejności sesji i manifestu paczki: **35 zaliczonych**.
- Rozszerzona regresja profilu, magazynów, menu, pomocy i palety:
  **162 zaliczone, 4 pominięte**.
- Pierwszy pełny przebieg wykonał **1789 testów poprawnie, 116 pominął i
  zaliczył 11 podtestów**. Jeden test integracyjny nie wystartował, ponieważ
  po wcześniejszym, udanym etapie AMC09 zgodnie z regułą porządku dysku
  usunięto odtwarzalny katalog `LiteHost/bin/Release`; nie był to błąd kodu.
- Pełny przebieg powtórzony z jawnym pominięciem wyłącznie tego testu:
  **1789 zaliczonych, 116 pominiętych, 1 jawnie niewybrany, 11 podtestów
  zaliczonych** w 77,64 s.
- Nie wykonywano kompilacji, instalacji, podmiany działającego AMC ani
  publikacji. Odbiór NVDA profilu publicznego wymaga późniejszej, bezpiecznej
  kompilacji i osobnej instalacji.

## Znane ograniczenia

- Uruchamiacz i aktualizator nie mają jeszcze rozdzielonych blokad jednej
  instancji, katalogów diagnostycznych i pełnego kontraktu aktualizacji dla
  obu profili. Dlatego nie wolno jeszcze instalować profilu publicznego obok
  AMC Test.
- Manifest deklaruje możliwości profilu, ale paczka publiczna nie usuwa
  jeszcze binarnych zależności ukrytych usług. Ograniczenie pakowania zostaje
  do następnego spójnego etapu.
- Nie ma jeszcze wersjonowanej, atomowej migawki AMC Test → AMC ani ekranu
  wyboru zakresu kopiowanych danych.
- Nie ma jeszcze migracji poświadczeń; zgodnie ze specyfikacją tokeny nie będą
  kopiowane migawką.
- Jednorazowe otwarcie Menedżera sesji na czystej publicznej instalacji czeka
  na etap instalatora.
- Sonos publiczny pozostaje ukryty do czasu prawdziwego brokera HTTPS i
  odbioru z zewnętrznym kontem.

## Wersja i commit

- Data pracy: 19 października 2026.
- Kod i testy fundamentu: lokalny commit `d2a34ecf`.
- Kompilacja: nie wykonywano dla tego etapu.
- Instalacja: nie wykonywano dla tego etapu.
- Publikacja: nie wykonywano; GitHub nie został użyty.
