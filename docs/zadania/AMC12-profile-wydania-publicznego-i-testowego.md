# AMC12 — profile wydania publicznego i testowego

## Status

**W trakcie — fundament profili, rozdzielenie uruchamiacza i aktualizatora,
kontrolowana migawka AMC Test → AMC, publiczne pakowanie i instalator są gotowe.
Wariant ochronny przeszedł odizolowaną instalację i odinstalowanie. Końcowa
paczka bez prywatnych modułów usług oraz lokalny instalator są zweryfikowane,
ale tego wariantu nie zainstalowano ponownie ani nie opublikowano.**

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

Lokalny kandydat instalatora publicznego istnieje. Wariant ochronny przeszedł
czystą instalację, pełną kontrolę i odinstalowanie, ale późniejszy wariant z
dobrowolnymi skrótami oraz bez prywatnych modułów usług nie był ponownie
instalowany. Żaden z nich nie został opublikowany ani odebrany z NVDA.

AMC Test i publiczny AMC mają osobne blokady uruchomienia, dlatego mogą działać
równolegle. Drugie uruchomienie AMC Test pokazuje tylko okno AMC Test, a drugie
uruchomienie publicznego AMC pokazuje tylko okno AMC. Tak samo rozdzielone są
aktualizatory: paczka jednego wydania nie może zaktualizować drugiego.
Dzienniki uruchamiania trafiają do folderu właściwego profilu, a interfejs
zawsze otrzymuje jawny profil z zatwierdzonego manifestu.

Publiczna paczka nie zawiera dedykowanego hosta Spotify Librespot, jego zestawu
licencji zależności ani modułów interfejsu Spotify i TIDAL. AMC Test nadal
zawiera te moduły. Każdy dołączony plik ma w manifeście dokładny rozmiar i
SHA-256. Przed utworzeniem instalatora oraz po instalacji AMC wykonuje pełną
kontrolę wszystkich plików, a nie tylko plików potrzebnych do startu.

Nowy instalator ma osobne warianty `AMC-<wersja>-win-x64.exe` i
`AMC-Test-<wersja>-win-x64.exe`, różne identyfikatory produktu, katalogi,
skróty, wpisy systemowe i blokady uruchomienia. Nie wymusza zamknięcia
działającego AMC. Jeśli właściwy profil nadal działa, instalacja zostaje
zatrzymana; program trzeba zamknąć zwykłą drogą, która chroni nagrywanie.
Paczka zawiera prywatny runtime Pythona oraz samowystarczalne procesy .NET i
nie pobiera środowiska uruchomieniowego podczas instalacji.

Skrót na pulpicie jest dobrowolnym, domyślnie wyłączonym zadaniem instalatora.
Użytkownik może też zaznaczyć „Nie twórz folderu w menu Start”. Tryb
administracyjny `/NOICONS` ma to samo znaczenie i nie tworzy żadnego z tych
skrótów.

## Uzasadnienie i decyzje

- **Korekta użytkownika z 20 października 2026:** nie budujemy kolejnego
  publicznego instalatora po każdej poprawce AMC Test. Istniejący kandydat
  pozostaje lokalnym punktem kontrolnym, a następny publiczny wariant powstanie
  dopiero z zestawu domkniętych i odebranych funkcji. Zastępuje to roboczą
  praktykę natychmiastowego przebudowywania profilu publicznego po małej
  korekcie wspólnego kodu.

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
- Ta sama zasada obejmuje kod interfejsu prywatnych usług. Pakowanie publiczne
  usuwa moduły Spotify, okna playlist Spotify i TIDAL, a wspólny interfejs
  importuje je tylko wtedy, gdy manifest profilu rzeczywiście dopuszcza daną
  sesję. Odświeżenie starszej paczki także usuwa dokładnie te odziedziczone
  pliki, zamiast pozostawiać je poza manifestem.
- Instalator wxPython jest osobnym skryptem od historycznego instalatora WPF.
  Używa zamkniętych identyfikatorów obu profili i `CloseApplications=no`;
  działającego nagrania nie wolno chronić przez wymuszenie zakończenia procesu.
- Instalator odmawia nałożenia nowego AMC na niepusty folder historycznego albo
  obcego programu. Aktualizacja jest dozwolona tylko wtedy, gdy manifest
  istniejącej paczki ma dokładny `installId` bieżącego profilu. Chroni to
  szczególnie domyślny folder `AMC`, który na starszym komputerze może nadal
  należeć do historycznego WPF.
- Skróty nie są bezwarunkowe. Strona folderu menu Start pozostaje dostępna,
  pulpit jest osobnym niezaznaczonym zadaniem, a wszystkie trzy wpisy skrótów
  respektują wybór „bez skrótów”.

## Zmienione pliki

- `wxlite/amc_wx_lite/release_profile.py`
- `wxlite/amc_wx_lite/state_store.py`
- `wxlite/amc_wx_lite/profile_layout.py`
- `wxlite/amc_wx_lite/version_info.py`
- `wxlite/amc_wx_lite/session_order.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/search_sources.py`
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
- 19.10.2026 pierwsza pełna bramka późniejszej instalacji zbiorczej wykazała,
  że odizolowany test uruchamiania hosta nie przekazywał nowych zależności
  profilu wydania i ścieżki migawki. Uzupełniono atrapę o profil `test` i
  odizolowaną ścieżkę migawki. Był to brak testu, nie próba obejścia jawnego
  kontraktu profili; instalacja została zatrzymana do zielonego powtórzenia.
- Zielone powtórzenie zaliczyło **1830 testów, 110 pominiętych i 11
  podtestów**, a następnie kontrola kandydata zatrzymała instalację kodem 2.
  Wszystkie 92 pliki startowe miały zgodne rozmiary i SHA-256. Przyczyną była
  rozbieżność katalogów możliwości: manifest Python zawierał lokalny formularz
  zgłoszeń, a zamknięty kontrakt launchera .NET jeszcze go nie dopuszczał.
  Kontrakty ujednolicono i dodano automatyczny test pełnej listy możliwości
  obu profili Python–.NET. Kandydat nie został zainstalowany ani uruchomiony.
- Końcowa zbiorcza bramka profilu testowego: **1831 zaliczonych, 110
  pominiętych i 11 podtestów**. Zbudowano 1665 plików, potwierdzono manifest,
  SHA-256, profil `test`, stałą instalację i jedno uruchomione okno AMC Test.
  Nie była to próbna instalacja publicznego AMC; publiczny instalator nadal
  czeka na osobny odbiór.
- Rzeczywista samowystarczalna paczka publicznego AMC Release powstała w
  `.test-output/AMC-public-2026.10.19-bd80db01`. Manifest wskazuje profil
  `public`, czystą rewizję `bd80db01`, 1070 jawnych plików, 1070 rozmiarów i
  1070 sum SHA-256. Niezależna pełna kontrola zakończyła się kodem **0**;
  paczka nie zawiera plików Librespot. Ma 422 452 757 bajtów. Nie uruchamiano
  jej jako aplikacji użytkowej i nie instalowano.
- Inno Setup 6.7.3 skompilował lokalny instalator
  `.test-output/installers/amc12-2026.10.19/AMC-0.1.0-alpha.422-win-x64.exe`.
  Ma 123 320 342 bajty. Ponowne obliczenie SHA-256 dało
  `23f0df0d10910ba9e0e32867ffbf06651226b30f0ee02b1597a0dec969777ea3`
  i jest zgodne z osobnym plikiem integralności. Instalatora nie uruchamiano.
- 20.10.2026 strukturalny kontrakt instalatora zaliczył **7/7** przypadków.
  Inno Setup 6.7.3 skompilował wariant z ochroną istniejącego folderu.
  Próba cicha przeciw projektowemu katalogowi zawierającemu jeden plik
  kontrolny zakończyła się oczekiwanym kodem 7 i komunikatem odmowy; liczba i
  treść plików katalogu nie zmieniły się. Nie wykonywano tej próby przeciw
  rzeczywistemu historycznemu AMC.
- Czysta instalacja publicznego profilu do odizolowanego katalogu zakończyła
  się kodem **0**. Zainstalowano 1079 plików łącznie z deinstalatorem i jego
  danymi; manifest wskazał profil `public`, źródło `863539bd` i paczkę
  `00ab4530`. Ponowna pełna kontrola zainstalowanych 1076 plików zakończyła
  się kodem **0**, a próbne odinstalowanie także kodem **0** i usunęło katalog.
- Próba ujawniła, że `/NOICONS` było ignorowane przez wcześniejsze
  `DisableProgramGroupPage=yes`, przez co próbny instalator utworzył skróty.
  Przed odinstalowaniem rozpoznano oba zainstalowane produkty, a po nim
  odtworzono trzy skróty historycznego AMC; prowadzą ponownie do
  `AccessibleMediaController.exe` i jego deinstalatora.
- Po korekcie dobrowolnych skrótów test strukturalny zaliczył **8/8**
  przypadków, a Inno Setup 6.7.3 ponownie skompilował instalator. Drugiej
  instalacji na głównym koncie nie wykonywano bez dodatkowej zgody, aby po
  wcześniejszym wykryciu kolizji nie ryzykować ponownej zmiany skrótów.
- Końcowa paczka po tej korekcie powstała w
  `.test-output/AMC-public-2026.10.20-20babb7b`. Manifest wskazuje profil
  `public`, czystą rewizję `20babb7ba7b4485211f8da769b37156a5045f7e7`,
  paczkę `29558d7d` i 1076 plików kontrolowanych; katalog zawiera 1077 plików
  razem z manifestem i zajmuje 422 624 783 bajty. Ponowna pełna kontrola
  zakończyła się kodem **0**.
- Końcowy lokalny instalator znajduje się w
  `.test-output/installers/amc12-2026.10.20-20babb7b/AMC-0.1.0-alpha.422-win-x64.exe`.
  Ma 123 354 484 bajty, a jego SHA-256 to
  `3d9e969e3d9a51b4e0ace9f95b06091761970ad2ae31501f3d624e61a237df23`;
  wynik jest zgodny z osobnym plikiem integralności. Ten końcowy wariant został
  zbudowany i sprawdzony, lecz nie został ponownie zainstalowany ani uruchomiony.
- Fizyczne rozdzielenie modułów usług: **44 testy ukierunkowane zaliczone**.
  Obejmują usunięcie starych plików przy odświeżeniu, odmowę niedozwolonego
  manifestu, syntetyczne złożenie profilu publicznego oraz import kompletnego
  interfejsu bez modułów Spotify i TIDAL.
- Pełna regresja wxPython po zmianie: **1856 zaliczonych, 116 pominiętych,
  1 jawnie niewybrany i 11 podtestów zaliczonych**. Jedyny niewybrany test
  wymagał wcześniej zbudowanego `LiteHost` w innej ścieżce; właściwy host został
  następnie zbudowany przez pełny proces paczki.
- Końcowa odchudzona paczka
  `.test-output/AMC-public-2026.10.20-cf6d1e2c` ma 1073 pliki kontrolowane,
  1074 pliki razem z manifestem i 422 575 507 bajtów. Manifest wskazuje czystą
  rewizję `cf6d1e2c65cc99d87217fa01187125b5a3428715`, paczkę `6030732f`, zero
  prywatnych modułów Spotify/TIDAL i zero składników Librespot. Pełna kontrola
  zakończyła się kodem **0**.
- Odpowiadający instalator ma 123 363 456 bajtów i SHA-256
  `65e34d13dd7ff2449f7b3d356b354646cf991d3875c15cf1f434757c3b9673b5`.
  Plik integralności podaje tę samą wartość. Instalatora nie uruchamiano.
- Po wspólnej poprawce granicy klawiatury oraz zachowania nagrania po awarii
  strumienia zbudowano następcę
  `.test-output/AMC-public-2026.10.20-6e1f6bc9`. Manifest wskazuje profil
  `public`, czystą rewizję `6e1f6bc93e0fbcafb22c7a12a127471d325c0442`,
  paczkę `9bc38937`, 1073 pliki kontrolowane i 1074 pliki razem z manifestem.
  Katalog ma 422 602 524 bajty, nie zawiera prywatnych modułów Spotify,
  TIDAL ani Librespot, a pełna kontrola paczki zakończyła się kodem **0**.
- Nowy lokalny instalator znajduje się w
  `.test-output/installers/amc12-2026.10.20-6e1f6bc9/AMC-0.1.0-alpha.422-win-x64.exe`.
  Ma 123 357 916 bajtów i SHA-256
  `58caaa28b367a63f049c0a86ada8061e2940992468195736abce702a402d6680`;
  niezależny odczyt pliku i plik integralności podają tę samą wartość.
  Instalatora nie uruchamiano, nie instalowano i nie publikowano.

## Znane ograniczenia

- Publiczne pakowanie usuwa dedykowany binarny host Librespot i trzy moduły
  interfejsu prywatnych usług. Wspólny samowystarczalny host .NET nadal powstaje
  z jednego kodu, lecz uruchomiony profil publiczny blokuje niedopuszczone sesje
  i operacje przez manifest możliwości; nie otrzymuje poświadczeń ani osobnego
  hosta Spotify.
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
- Osobne tożsamości procesu i instalator są gotowe, ale nie sprawdzono jeszcze
  aktualizacji istniejącego publicznego profilu od końca do końca. Czysta
  instalacja, pełna kontrola i odinstalowanie przeszły; wykonawcza próba
  ostatecznej korekty `/NOICONS` wymaga osobnej zgody albo maszyny izolowanej.
- Instalator nie jest jeszcze podpisany cyfrowo ani opublikowany. Plik
  integralności potwierdza lokalny wynik budowy, nie zastępuje podpisu kodu.
- Na głównym komputerze domyślny publiczny folder
  `%LOCALAPPDATA%\Programs\AMC` nadal zawiera historyczne AMC WPF. Próba
  odbiorcza nowego publicznego AMC musi użyć osobnego pustego katalogu albo
  nastąpić dopiero po świadomym odinstalowaniu starego programu.

## Porządek dysku

- Testy tworzyły pozostałe po nowym module wyłącznie trzy odtwarzalne pliki
  `.pyc`. Po weryfikacji usunięto je dokładnymi ścieżkami spod katalogów
  nadrzędnych `wxlite/amc_wx_lite/__pycache__` i
  `wxlite/tests/__pycache__`.
- Odzyskano 61 685 bajtów. Pliki nie są odzyskiwane z kopii, ponieważ Python
  tworzy je ponownie automatycznie przy kolejnym uruchomieniu testu.
- Pierwszą próbną paczkę z niezapisanej jeszcze poprawki usunięto po
  zweryfikowaniu czystego następcy. Usunięto dokładnie katalog
  `.test-output/AMC-public-2026.10.19-1cc6cc85` spod repozytorium i odzyskano
  422 452 640 bajtów. Był to odtwarzalny artefakt; nie ma potrzeby odzyskiwania.
- Zachowano jedyny czysty kandydat publiczny
  `.test-output/AMC-public-2026.10.19-bd80db01`. Skrypt sam usunął swoje
  jednoznacznie nazwane katalogi `.test-tmp/bundle-build-*`. Nie usunięto
  zastanych `.test-output`, `.test-tmp`, `.pytest_cache`, źródeł, dokumentacji,
  ustawień, nagrań ani zainstalowanej paczki AMC Test.
- Zachowano też jedyny zbudowany instalator i jego plik integralności w
  `.test-output/installers/amc12-2026.10.19`; nie ma jeszcze zweryfikowanej
  kopii zdalnej, więc tych plików nie wolno usuwać.
- Po udanej instalacji zbiorczej usunięto dokładnie odrzucony katalog
  `.test-output/AMC-Python-next-2026.10.19-acb81034e44cc818d27221c143c47f8773a44a74-b90cd4ee`.
  Zawierał niespójny kandydat profilu testowego i nie został zainstalowany.
  Pozostawione okno „Diagnostyka AMC” z tego katalogu zamknięto zwykłym
  żądaniem zamknięcia; działającego AMC Test ze stałej instalacji nie ruszano.
  Odzyskano około 133,45 MiB, oszacowane na podstawie równoważnej poprawnej
  paczki 139 933 384 bajtów. Kandydat był odtwarzalny z commitu `acb81034`,
  lecz jako odrzucony nie wymaga odzyskania. Zachowano poprawnego kandydata
  `fb9ba25f`, instalator publiczny, źródła, ustawienia i dane użytkownika.
- 20.10.2026 po sprawdzeniu następcy usunięto dokładnie dwa zastąpione katalogi
  paczek publicznych, dwa odpowiadające im katalogi instalatorów, dwa próbne
  katalogi kompilacji Inno Setup, katalog kontrolny obcej instalacji oraz dwa
  logi z bieżącego przebiegu. Wszystkie znajdowały się wyłącznie pod
  `.test-output` albo `.test-tmp` tego repozytorium. Odzyskano 1 339 154 013
  bajtów, około 1,25 GiB. Były to odtwarzalne artefakty z rewizji `cdad1bdf`
  i `863539bd`; odzyskanie wymagałoby ich ponownego zbudowania.
- Zachowano końcową paczkę i instalator z rewizji `20babb7b`, wcześniejszy
  jedyny historyczny instalator z 19.10.2026, źródła, dokumentację, ustawienia,
  dane użytkownika, nagrania oraz zastane niepewne katalogi testowe.
- Po zbudowaniu i pełnym sprawdzeniu następcy `cf6d1e2c` usunięto dokładnie
  zastąpioną paczkę `AMC-public-2026.10.20-20babb7b`, odpowiadający jej katalog
  instalatora oraz trzy jawne katalogi tymczasowe pełnej regresji tego etapu.
  Cele znajdowały się wyłącznie pod `.test-output` i `.test-tmp`; odzyskano
  546 252 450 bajtów, około 521 MiB. Artefakty można odtworzyć z commitu
  `20babb7b` albo ponownym uruchomieniem testów.
- Zachowano bieżącą paczkę i instalator `cf6d1e2c`, wcześniejszy instalator z
  19.10.2026, zastane katalogi testowe o niepewnym pochodzeniu oraz mieszane
  katalogi `__pycache__`; nie usunięto źródeł, danych użytkownika ani nagrań.
- Po pełnym sprawdzeniu następcy `6e1f6bc9` usunięto dokładnie zastąpioną
  paczkę `.test-output/AMC-public-2026.10.20-cf6d1e2c` oraz odpowiadający jej
  katalog `.test-output/installers/amc12-2026.10.20-cf6d1e2c`. Usunięto 1076
  plików i odzyskano 545 939 294 bajty, około 520,6 MiB. Były to odtwarzalne
  artefakty z commitu `cf6d1e2c`; lokalne odzyskanie wymaga ponownej budowy.
  Zachowano nową paczkę i instalator `6e1f6bc9`, źródła, dokumentację,
  ustawienia, dane użytkownika, nagrania oraz zastane niepewne katalogi
  testowe.

## Wersja i commit

- Data pracy: 19–20 października 2026.
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
- Publiczne pakowanie, pełna integralność i źródło instalatora: `7b586c14` —
  `feat(amc12): dodaj publiczne pakowanie i instalator`; testy zaliczone,
  pliku instalatora `.exe` nie zbudowano z powodu braku Inno Setup.
- Poprawka rzeczywistej budowy: `bd80db01` —
  `fix(amc12): ustabilizuj budowe publicznej paczki`. Kompilacja Release,
  złożenie czystej paczki i pełna kontrola integralności zaliczone; instalacji
  ani publikacji nie wykonywano.
- Wykrywanie użytkowej instalacji Inno Setup: `6571a4de` —
  `fix(amc12): znajdz uzytkowy kompilator instalatora`. Lokalny instalator
  zbudowany, rozmiar i SHA-256 zgodne; instalacji i publikacji nie wykonywano.
- Domknięcie pełnej regresji profili i menu: `acb81034`; zgodność możliwości
  Sygnalisty Python–.NET: `fb9ba25f`.
- Zbiorcza instalacja AMC Test:
  `2026.10.19-fb9ba25fe0680cf7bf5435d53eb5b073de091cca-0debb6aa`;
  publicznego instalatora nadal nie uruchamiano.
- Ochrona istniejącej instalacji: `863539bd` —
  `fix(amc12): nie nadpisuj historycznej instalacji`. Ten wariant przeszedł
  czystą instalację, pełną kontrolę i odinstalowanie w katalogu projektowym;
  nie został wydany publicznie.
- Dobrowolne skróty instalatora: `20babb7b` —
  `fix(amc12): zrob skroty instalatora dobrowolne`. Końcowy wariant został
  skompilowany i sprawdzony przez test strukturalny 8/8 oraz pełną kontrolę
  paczki; jego ponownej instalacji na głównym koncie nie wykonywano.
- Instalacja publiczna: wykonano wyłącznie odizolowaną próbę wariantu
  `863539bd`, po czym go odinstalowano. Końcowy wariant `20babb7b` pozostaje
  lokalnym kandydatem, a nie zainstalowanym wydaniem.
- Publikacja: nie wykonywano; GitHub nie został użyty.
- Fizyczne usunięcie prywatnych modułów z publicznej paczki: `cf6d1e2c` —
  `fix(amc12): usun prywatne moduly z publicznej paczki`. Testy ukierunkowane i
  pełna regresja zaliczone, paczka i instalator z pełną integralnością zbudowane;
  instalacji końcowego wariantu ani publikacji nie wykonywano.
- Aktualny publiczny kandydat: rewizja źródłowa `6e1f6bc9`, paczka `9bc38937`
  i instalator `AMC-0.1.0-alpha.422-win-x64.exe`. Zawiera kod poprawki
  `4d87189e`, obejmującej wspólne mapowanie `F1`–`F24`, nawigację bloku
  numerycznego oraz zachowanie niepustego nagrania po awarii strumienia.
  Paczka, manifest i integralność instalatora są potwierdzone lokalnie;
  instalacji publicznego wariantu ani publikacji nie wykonywano.
