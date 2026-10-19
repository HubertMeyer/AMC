# AMC12 — profile wydania publicznego i testowego

## Status

**W trakcie — fundament profili oraz rozdzielenie uruchamiacza i aktualizatora
są gotowe w źródłach i testach; nie zainstalowano ani nie opublikowano profilu
publicznego.**

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

AMC Test i publiczny AMC mają osobne blokady uruchomienia, dlatego mogą działać
równolegle. Drugie uruchomienie AMC Test pokazuje tylko okno AMC Test, a drugie
uruchomienie publicznego AMC pokazuje tylko okno AMC. Tak samo rozdzielone są
aktualizatory: paczka jednego wydania nie może zaktualizować drugiego.
Dzienniki uruchamiania trafiają do folderu właściwego profilu, a interfejs
zawsze otrzymuje jawny profil z zatwierdzonego manifestu.

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
- Uruchamiacz i aktualizator używają jednego zamkniętego kontraktu profili.
  Manifest może wybrać `test` albo `public`, ale nie może podmienić nazwy,
  katalogów, kanału aktualizacji, listy sesji ani przestrzeni poświadczeń.
- AMC Test zachowuje dotychczasową blokadę uruchamiacza oraz zgodność z dawnym
  tytułem „AMC Python”. Publiczny AMC ma nową blokadę i rozpoznaje wyłącznie
  własny tytuł „AMC”. Ułatwia to przejście bez uruchomienia dwóch kopii starego
  profilu testowego.
- Aktualizator sprawdza profil paczki i istniejącej instalacji przed prośbą o
  zamknięcie programu. Starsza instalacja bez pól profilu może zostać
  jednorazowo rozpoznana wyłącznie jako AMC Test w dotychczasowym folderze
  `AMC Python`; publiczny AMC nie korzysta z tego wyjątku.

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
- `src/Shared/ReleaseProfileContract.cs`
- `src/AccessibleMediaController.PythonLauncher/AccessibleMediaController.PythonLauncher.csproj`
- `src/AccessibleMediaController.PythonLauncher/BundleContract.cs`
- `src/AccessibleMediaController.PythonLauncher/ProductIdentity.cs`
- `src/AccessibleMediaController.PythonLauncher/ExistingInstancePolicy.cs`
- `src/AccessibleMediaController.PythonLauncher/PythonLaunchPlan.cs`
- `src/AccessibleMediaController.PythonLauncher/Program.cs`
- `src/AccessibleMediaController.PythonUpdater/AccessibleMediaController.PythonUpdater.csproj`
- `src/AccessibleMediaController.PythonUpdater/Program.cs`
- `src/AccessibleMediaController.PythonUpdater/SafeApplicationStop.cs`
- `src/AccessibleMediaController.PythonUpdater/UpdaterInstanceLease.cs`
- `tests/AccessibleMediaController.PythonLauncher.Tests/AccessibleMediaController.PythonLauncher.Tests.csproj`
- `tests/AccessibleMediaController.PythonLauncher.Tests/Program.cs`
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
- Dla pierwszego fundamentu nie wykonywano kompilacji, instalacji, podmiany
  działającego AMC ani publikacji. Odbiór NVDA profilu publicznego nadal
  wymaga późniejszej, bezpiecznej kompilacji Release i osobnej instalacji.
- Po etapie rozdzielenia uruchamiacza i aktualizatora: **20 testów C#
  zaliczonych**. Obejmują oba prawidłowe profile, odmowę zmienionego manifestu,
  osobne blokady, tytuły okien, prywatny runtime, bezpieczne wskazanie okna,
  procesy instalacji oraz przyjęcie zgodnej i odrzucenie obcej aktualizacji.
- Testy profilu i układu paczki Python po zmianie: **27 zaliczonych**.
- Uruchamiacz Debug i aktualizator Debug: obie kompilacje zaliczone z 0
  ostrzeżeń i 0 błędów. Są to kompilacje odizolowane w repozytorium, nie
  instalacja ani podmiana działającej aplikacji.
- Przed kompilacjami pięciosekundowa bramka wykazała 0 plików
  `.amc-partial` i 0 plików rosnących. Nie zamykano uruchomionego AMC.

## Znane ograniczenia

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
- Osobne tożsamości procesu są gotowe, ale nie ma jeszcze instalatora, który
  utworzy dwie niezależne instalacje i sprawdzi ich cykl aktualizacji od końca
  do końca. Z tego powodu publicznego AMC nadal nie instalujemy.

## Porządek dysku

- Testy tworzyły pozostałe po nowym module wyłącznie trzy odtwarzalne pliki
  `.pyc`. Po weryfikacji usunięto je dokładnymi ścieżkami spod katalogów
  nadrzędnych `wxlite/amc_wx_lite/__pycache__` i
  `wxlite/tests/__pycache__`.
- Odzyskano 61 685 bajtów. Pliki nie są odzyskiwane z kopii, ponieważ Python
  tworzy je ponownie automatycznie przy kolejnym uruchomieniu testu.
- Nie utworzono nowego katalogu build, staging ani publish. Nie usunięto
  zastanych `.test-output`, `.test-tmp`, `.pytest_cache`, źródeł, dokumentacji,
  ustawień, nagrań ani zainstalowanej paczki AMC Test.

## Wersja i commit

- Data pracy: 19 października 2026.
- Kod i testy fundamentu: lokalny commit `d2a34ecf`.
- Rozdzielenie uruchamiacza i aktualizatora: commit następujący po tym zapisie.
- Kompilacja: odizolowane kompilacje Debug uruchamiacza i aktualizatora —
  zaliczone; paczki Release nie zbudowano.
- Instalacja: nie wykonywano dla tego etapu.
- Publikacja: nie wykonywano; GitHub nie został użyty.
