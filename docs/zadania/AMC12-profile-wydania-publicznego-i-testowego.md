# AMC12 — profile wydania publicznego i testowego

## Status

**W trakcie — fundament profili, rozdzielenie uruchamiacza i aktualizatora oraz
kontrolowana migawka AMC Test → AMC oraz źródła publicznego pakowania i
instalatora są gotowe i sprawdzone testami. Nie zbudowano jeszcze instalatora,
ponieważ na komputerze nie ma kompilatora Inno Setup; nie zainstalowano ani nie
opublikowano profilu publicznego.**

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
uruchomienie jednego wydania nie zmienia danych drugiego. Kopiowanie wybranych
danych z AMC Test do AMC jest osobną, jawną czynnością opartą na wersjonowanej
migawce. AMC Test przygotowuje ostatnią kompletną migawkę przy bezpiecznym
uruchomieniu silnika. Publiczne AMC udostępnia w menu Ustawienia, pełnej pomocy
i palecie polecenia „Odśwież dane z AMC Test” oraz „Stan synchronizacji danych”.
Polecenia pojawiają się tylko wtedy, gdy istnieje drugi profil albo migawka.

Migawka przenosi bibliotekę lokalną, stacje, podcasty i kanały YouTube,
historię wyszukiwania i odtwarzania, zakładki użytkownika, playlisty AMC,
harmonogramy oraz historię nagrywania. Nie kopiuje plików audio — oba profile
mogą wskazywać te same istniejące pliki. Nie przenosi Spotify, TIDAL-u,
poświadczeń, kolejności sesji, ostatniej sesji, bieżącego okna, fokusu ani stanu
trwającego nagrywania.

Przy pierwszym odświeżeniu publiczne AMC nie nadpisuje bez pytania istniejących
danych wspólnych. Przy następnych odświeżeniach porównuje stan z ostatnio
zastosowaną migawką. Jeśli dane publiczne zmieniły się osobno, pyta, czy
przyjąć dane z AMC Test, czy zachować dane publiczne. Po odświeżeniu pozostaje
ten sam widok i, o ile element nadal istnieje, ten sam zaznaczony wiersz.

Nie ma jeszcze instalatora publicznego AMC. Kod i testy fundamentu nie są
dowodem kompilacji, instalacji ani publikacji.

AMC Test i publiczny AMC mają osobne blokady uruchomienia, dlatego mogą działać
równolegle. Drugie uruchomienie AMC Test pokazuje tylko okno AMC Test, a drugie
uruchomienie publicznego AMC pokazuje tylko okno AMC. Tak samo rozdzielone są
aktualizatory: paczka jednego wydania nie może zaktualizować drugiego.
Dzienniki uruchamiania trafiają do folderu właściwego profilu, a interfejs
zawsze otrzymuje jawny profil z zatwierdzonego manifestu.

Publiczna paczka nie zawiera dedykowanego hosta Spotify Librespot ani jego
zestawu licencji zależności. Każdy dołączony plik ma w manifeście dokładny
rozmiar i SHA-256. Przed utworzeniem instalatora oraz po instalacji AMC wykonuje
pełną kontrolę wszystkich plików, a nie tylko plików potrzebnych do startu.

Nowy instalator ma osobne warianty `AMC-<wersja>-win-x64.exe` i
`AMC-Test-<wersja>-win-x64.exe`, różne identyfikatory produktu, katalogi,
skróty, wpisy systemowe i blokady uruchomienia. Nie wymusza zamknięcia
działającego AMC. Jeśli właściwy profil nadal działa, instalacja zostaje
zatrzymana; program trzeba zamknąć zwykłą drogą, która chroni nagrywanie.
Paczka zawiera prywatny runtime Pythona oraz samowystarczalne procesy .NET i
nie pobiera środowiska uruchomieniowego podczas instalacji.

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
- Migawka ma własny format wersji 1 niezależny od schematów `state.json` i
  SQLite. Powstaje przez jawne złożenie dopuszczonych pól; nie jest kopią
  żadnego żywego magazynu.
- Plik jest zapisywany przez plik tymczasowy, opróżnienie bufora i atomową
  podmianę. Przed podmianą host ponownie czyta plik tymczasowy i sprawdza
  SHA-256. Poprzednia poprawna migawka pozostaje jako wersja awaryjna.
- Metadane ostatniego importu są zapisywane dopiero po udanym zapisie obu baz
  i `state.json`. Brak wiarygodnych metadanych przy istniejących danych
  publicznych jest konfliktem, a nie zgodą na ciche nadpisanie.
- Historia wyszukiwania interfejsu wxPython jest przekazywana jawnie przez
  ograniczony kontrakt hosta, ponieważ celowo nie należy do baz C#. Przy
  imporcie wraca także do osobnego magazynu interfejsu publicznego AMC.
- Manifest integralności zawiera teraz zarówno SHA-256, jak i rozmiar każdego
  pliku. Zwykły start nadal sprawdza krytyczne pliki startowe, natomiast jawna
  kontrola instalatora sprawdza całą paczkę strumieniowo.
- Dedykowany binarny host Librespot jest składnikiem profilu testowego. Samo
  ukrycie sesji w interfejsie nie wystarczało, dlatego publiczny proces
  pakowania w ogóle go nie odczytuje ani nie kopiuje.
- Instalator wxPython jest osobnym skryptem od historycznego instalatora WPF.
  Używa zamkniętych identyfikatorów obu profili i `CloseApplications=no`;
  działającego nagrania nie wolno chronić przez wymuszenie zakończenia procesu.

## Zmienione pliki

- `wxlite/amc_wx_lite/release_profile.py`
- `wxlite/amc_wx_lite/state_store.py`
- `wxlite/amc_wx_lite/profile_layout.py`
- `wxlite/amc_wx_lite/version_info.py`
- `wxlite/amc_wx_lite/session_order.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/tools/build_bundle.py`
- `wxlite/tools/Build-AMCBundle.ps1`
- `wxlite/tools/Build-AMCInstaller.ps1`
- `installer/AMC_Wx_Setup.iss`
- `wxlite/tests/test_release_profile.py`
- `wxlite/tests/test_bundle_layout.py`
- `wxlite/tests/test_installer_profiles.py`
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
- `src/AccessibleMediaController.Core/Configuration/CommonDataSnapshotStore.cs`
- `src/AccessibleMediaController.Core/Configuration/ConfigurationStore.cs`
- `src/AccessibleMediaController.LiteHost/LiteCommonDataSnapshotCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `src/AccessibleMediaController.LiteHost/LiteRadioRecordingCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/Program.cs`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/tests/test_host_client.py`
- `tests/AccessibleMediaController.Core.SmokeTests/CommonDataSnapshotTests.cs`
- `tests/AccessibleMediaController.Core.SmokeTests/InstallerOfflineContractTests.cs`
- `tests/AccessibleMediaController.Core.SmokeTests/LibrespotHostClientTests.cs`
- `tests/AccessibleMediaController.Core.SmokeTests/Program.cs`
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
- Migawka, profil, menu, pełna pomoc, paleta i klient protokołu Python:
  **157 testów zaliczonych**. Dodatkowa kontrola składni zmienionych modułów
  Python zaliczona.
- Przed planowaną kompilacją nowej warstwy C# kolejne pięciosekundowe bramki
  wykazały **1 rosnący plik `.amc-partial`**. Kompilacji, testów C#,
  instalacji i restartu świadomie nie wykonano; nagranie użytkownika ma
  pierwszeństwo.
- Przy późniejszej bramce nie było żadnego pliku `.amc-partial`. Odizolowany
  test migawki C# zaliczył eksport, filtrowanie danych, atomową podmianę,
  integralność SHA-256, zapis i ponowne otwarcie obu baz SQLite, zachowanie
  prywatnych ustawień, pierwszy konflikt, następny konflikt oraz uszkodzony
  znacznik synchronizacji.
- Host LiteHost Debug zbudował się z **0 ostrzeżeń i 0 błędów**.
- Pierwsze uruchomienie pełnej regresji Core wykryło wyścig w istniejącym
  teście zakończenia osobnego procesu Librespot: błąd polecenia docierał przed
  równoległym zdarzeniem awarii. Test poprawiono tak, by czekał na oba wymagane
  skutki. Powtórzona pełna regresja Core zakończyła się kodem **0**.
- Publiczne pakowanie, profile, instalator i manifest integralności:
  **38 testów Python zaliczonych**. Obejmują pełne syntetyczne złożenie profilu
  publicznego bez odczytu Librespot oraz zgodność rozmiaru i SHA-256 każdego
  pliku.
- Uruchamiacz i aktualizator po dodaniu pełnej kontroli wszystkich plików:
  **22 testy C# zaliczone**.
- Test strukturalny samowystarczalności instalatora zaliczony. Potwierdza trzy
  publikacje `.NET --self-contained true`, prywatny runtime Pythona, brak
  pobierania runtime i brak wymuszonego zamknięcia programu. Nie jest dowodem
  zbudowania ani uruchomienia instalatora.
- Oba nowe skrypty PowerShell przeszły kontrolę składni bez błędów.

## Znane ograniczenia

- Publiczne pakowanie usuwa dedykowany binarny host Librespot, ale wspólna
  paczka nadal zawiera część modułów źródłowych usług prywatnych, ponieważ
  obecny interfejs importuje je przy starcie. Profil blokuje ich sesje i
  polecenia. Fizyczne odchudzenie pozostałych modułów wymaga rozdzielenia
  importów i jest osobną bramką przed publikacją publiczną.
- Wersjonowana, atomowa migawka została skompilowana i sprawdzona na
  odizolowanych magazynach testowych, ale nie została jeszcze odebrana w
  zainstalowanych AMC Test i AMC. Pierwsza wersja ma stały bezpieczny zakres;
  nie ma jeszcze ekranu ręcznego wyboru pojedynczych kategorii.
- Migawka automatyczna jest obecnie przygotowywana przy uruchomieniu AMC Test.
  Odświeżenie jej po zmianach wykonanych w tej samej długiej sesji oraz
  globalny właściciel wykonywania harmonogramów wymagają następnego podetapu.
- Nie ma jeszcze migracji poświadczeń; zgodnie ze specyfikacją tokeny nie będą
  kopiowane migawką.
- Jednorazowe otwarcie Menedżera sesji na czystej publicznej instalacji czeka
  na etap instalatora.
- Sonos publiczny pozostaje ukryty do czasu prawdziwego brokera HTTPS i
  odbioru z zewnętrznym kontem.
- Osobne tożsamości procesu są gotowe, ale nie ma jeszcze instalatora, który
  utworzy dwie niezależne instalacje i sprawdzi ich cykl aktualizacji od końca
  do końca. Z tego powodu publicznego AMC nadal nie instalujemy.
- Źródło instalatora jest gotowe, ale `ISCC.exe` (Inno Setup) nie jest obecny
  na tym komputerze. Nie powstał więc jeszcze plik `.exe` instalatora ani jego
  końcowy plik integralności.

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
- Rozdzielenie uruchamiacza i aktualizatora: `f9a70db8` —
  `feat(amc12): rozdziel launcher i updater profili`.
- Kompilacja: odizolowane kompilacje Debug uruchamiacza i aktualizatora —
  zaliczone; paczki Release nie zbudowano.
- Instalacja: nie wykonywano dla tego etapu.
- Publikacja: nie wykonywano; GitHub nie został użyty.
- Migawka danych wspólnych: `cdf9cb05` —
  `feat(amc12): dodaj kontrolowana migawke danych`; testy i kompilacja
  zaliczone, instalacji nie wykonywano.
- Publiczne pakowanie, pełna integralność i źródło instalatora: testy
  zaliczone; commit zostanie wpisany po zapisaniu spójnego etapu.
