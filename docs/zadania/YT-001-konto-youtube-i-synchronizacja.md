# YT-001 — konto YouTube i synchronizacja

- Status: `Wdrożone do ręcznego odbioru — logowanie, kanały i opisy zostały
  przyjęte przez użytkownika; playlisty, trwałe respektowanie usunięć,
  uczciwa kolejka odświeżania, build, atomowa instalacja i kontrolowany start
  AMC Test są zaliczone. Pozostaje sprawdzenie z NVDA pustych kanałów po
  napełnieniu kolejki oraz zwykłej playlisty konta`. Bieżąca instalacja:
  [AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md](AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md).
- Utworzono: 18 października 2026
- Ostatnia aktualizacja: 24 października 2026
- Obszar: YouTube, OAuth, Biblioteka, wyszukiwanie i bezpieczne poświadczenia
- Polecenie uruchamiające: `Uruchom zadanie YT-001`

## Kolejność realizacji

Korekta użytkownika z 21 października 2026 zastępuje wcześniejsze odłożenie:
po przygotowaniu instalatora wolno rozpocząć bezpieczny etap przygotowawczy.
Nie oznacza to zgody na samoczynne logowanie konta ani otwarcie przeglądarki.
Do czasu ukończenia i odbioru utrzymujemy działające publiczne wyszukiwanie,
Bibliotekę i pobieranie YouTube bez logowania do konta.

## Cel

Dodać dostępne logowanie do konta YouTube oraz użyć go przede wszystkim do
synchronizacji subskrypcji i zwykłych playlist. Rekomendacje strony głównej i
komentarze nie są warunkiem pierwszej wersji. Obecne publiczne wyszukiwanie,
odtwarzanie, zapis do `Media internetowe` i pobieranie nie mogą zależeć od
zalogowania.

## Ustalenie techniczne

Pierwszy wariant AMC ma korzystać z oficjalnego OAuth 2.0 dla aplikacji
komputerowej, z PKCE i zwykłą przeglądarką systemową. Tokeny pozostają wyłącznie
w hoście C# i są przechowywane mechanizmem chronionym Windows; interfejs Python
otrzymuje tylko stan użytkowy i dane potrzebne do wyświetlenia. Token, kod
autoryzacyjny, identyfikator konta ani odpowiedź serwera nie mogą trafić do
logu, dostępnej nazwy kontrolki, argumentów procesu ani pliku ustawień.

## Wzorzec BlindRSS i granica wykorzystania

- Źródło obserwacji: `serrebidev/BlindRSS`, plik
  `core/youtube_account.py`, stan gałęzi `main` sprawdzony 18 października
  2026. Projekt jest dostępny na licencji MIT.
- Użyteczny wzorzec doświadczenia: aplikacja pokazuje prosty stan konta,
  pozwala się zalogować i wylogować, okresowo pobiera subskrypcje, dodaje nowe
  kanały bez przywracania kanałów świadomie usuniętych przez użytkownika i nie
  widzi hasła.
- BlindRSS używa danych klienta YouTube TV i wewnętrznego interfejsu Innertube
  do subskrypcji oraz rekomendacji. Nie kopiujemy tego mechanizmu do
  publicznego AMC i nie używamy cudzych danych klienta. Może być wyłącznie
  dowodem, że prosty dostępny przepływ konta jest możliwy.
- Rekomendacje są niskim priorytetem. Brak ich w oficjalnym API nie blokuje
  zadania.

## Etap 1 — logowanie tylko do odczytu

1. Status konta, `Zaloguj do YouTube`, `Odśwież dostęp` i `Wyloguj` w
   ustawieniach sesji Podcasty i YouTube oraz w palecie poleceń.
2. Przepływ dostępny bez osadzonej przeglądarki: użytkownik może otworzyć
   systemową przeglądarkę albo skopiować adres. Anulowanie, odmowa, limit czasu
   i ponowienie wracają do AMC z jednoznacznym komunikatem i fokusem.
3. Minimalny zakres `youtube.readonly`, o ile wystarcza do zatwierdzonego
   odczytu. Nie żądamy z góry zakresu pozwalającego modyfikować konto.
4. `subscriptions.list(mine=true)` pobiera wszystkie strony subskrypcji.
   Zwykłe playlisty użytkownika i ich elementy są osobnym, opcjonalnym
   podetapem. `Do obejrzenia` i historia oglądania nie są obiecywane, ponieważ
   oficjalne API ich normalnie nie udostępnia.

## Model synchronizacji

Pierwsza wersja ma być bezpiecznie jednokierunkowa: YouTube → AMC.

- Nowa subskrypcja YouTube może zostać dodana do wskazanej kategorii
  Biblioteki AMC.
- Brak kanału w późniejszej odpowiedzi YouTube nie usuwa automatycznie źródła,
  historii, pobrań ani zakładek AMC.
- Kanał świadomie usunięty lokalnie nie wraca sam przy kolejnym odświeżeniu;
  użytkownik może jawnie wybrać `Przywróć z YouTube`.
- Zbieżność wykrywamy po stabilnym identyfikatorze kanału, nigdy po nazwie.
- Synchronizacja nie uruchamia masowo setek odświeżeń kanałów na wątku GUI;
  używa porcji i istniejącego harmonogramu odświeżania Podcastów i YouTube.

Dwukierunkowa zmiana konta jest późniejszym, jawnym etapem. Polecenia
`Subskrybuj na YouTube` i `Anuluj subskrypcję na YouTube` nie mogą być ukryte
pod zwykłym `Ctrl+Shift+L`, które nadal oznacza członkostwo w Bibliotece AMC.
Automatyczne usuwanie po obu stronach jest wykluczone.

## Wyszukiwanie, zapis i pobieranie

- Publiczne wyszukiwanie ma nadal działać bez konta. Po zalogowaniu wolno
  dodać wariant oparty na oficjalnym API tylko po pomiarze limitów i bez
  pogorszenia obecnego wyszukiwania.
- Z wyniku nadal można dodać kanał do Biblioteki albo film do
  `Media internetowe`. Logowanie nie zmienia znaczenia `Ctrl+Shift+L`.
- Pobieranie lub zapis publicznego filmu korzysta z istniejącego, odrębnego
  toru medialnego. OAuth YouTube Data API nie jest traktowany jako sposób
  uzyskiwania chronionego adresu strumienia.
- Dodawanie filmu do własnej playlisty YouTube można rozważyć po etapie tylko
  do odczytu, z osobnym poleceniem, zakresem zapisu i potwierdzeniem API.
- Komentarze są osobnym późniejszym rozszerzeniem: wymagają dodatkowych
  zakresów, moderacji błędów i osobnego odbioru dostępności. Nie blokują
  subskrypcji ani playlist.

## Profil testowy i publiczny

- Najpierw działa w `AMC Test` na odizolowanym koncie testowym.
- Publiczne `AMC` otrzyma funkcję dopiero po weryfikacji ekranu zgody,
  wymagań Google, strony projektu, polityki prywatności i limitów API.
- Publiczny użytkownik nie może być zmuszony do tworzenia własnego projektu
  deweloperskiego, chyba że Google rzeczywiście nie pozwala na wspólnego
  klienta AMC; wtedy potrzebny jest osobny dostępny kreator i jawna decyzja.

### Decyzja o identyfikatorze Google — 23.10.2026

Użytkownik końcowy nie ma tworzyć własnego identyfikatora. Aplikacja
komputerowa jest publicznym klientem OAuth i nie potrafi bezpiecznie ukryć
sekretu; AMC potrzebuje jednego klienta typu „Desktop app” w projekcie Google
Cloud należącym do opiekuna AMC, z włączonym YouTube Data API, PKCE i
minimalnym zakresem `youtube.readonly`. Identyfikator klienta może być częścią
aplikacji, natomiast token użytkownika pozostaje chronionym poświadczeniem
lokalnym.

Korekta z 23.10.2026: konkretny klient utworzony w Google Cloud ma również
`client_secret` i punkt tokenów odrzuca żądanie bez tej wartości. W aplikacji
komputerowej nie jest to sekret, który da się kryptograficznie ukryć przed
właścicielem komputera, ale nadal nie wolno umieszczać go w Git, logu, nazwie
dostępnościowej ani wierszu poleceń procesu.

Dla AMC Test ekran zgody może działać w trybie Testing, a konto użytkownika
zostanie dodane jako nazwany test user. Google ogranicza taki tryb do 100
użytkowników, a autoryzacja testowa wygasa po 7 dniach. Dlatego nie jest to
model końcowy. AMC Public powinien używać osobnego projektu produkcyjnego i
przejść wymaganą weryfikację marki oraz zakresu, aby zwykły użytkownik jedynie
wybrał konto Google. Użytkownik końcowy nie przekazuje tokenu ani własnego
identyfikatora. Dla bieżącego prototypu opiekun projektu musi jednak jednorazowo
zapisać lokalnie sekret tego samego klienta desktopowego; ta korekta z
23.10.2026 zastępuje wcześniejsze założenie, że sam identyfikator wystarczy.

Oficjalne źródła sprawdzone 23.10.2026:
[OAuth dla aplikacji zainstalowanych](https://developers.google.com/youtube/data/guides/auth/installed-apps),
[gotowość produkcyjna i zgodność](https://developers.google.com/identity/protocols/oauth2/production-readiness/policy-compliance),
[weryfikacja zakresów](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification)
oraz [tryb Testing](https://support.google.com/cloud/answer/15549945?hl=en).

## Kryteria akceptacji

1. Token nigdy nie opuszcza hosta C# i po restarcie odświeża się bez pytania o
   hasło; wylogowanie rzeczywiście usuwa lokalne poświadczenie.
2. Czysty profil z NVDA przechodzi logowanie, anulowanie, odmowę, wygaśnięcie,
   ponowienie i wylogowanie bez technicznych nazw ani utraty fokusu.
3. Synchronizacja wielu stron subskrypcji jest idempotentna, nie duplikuje
   kanałów i nie odtwarza świadomie usuniętych źródeł.
4. Brak sieci, unieważniony token, brak kanału YouTube na koncie i wyczerpany
   limit API mają osobne, użytkowe komunikaty.
5. Publiczne wyszukiwanie, zapis filmu, pobieranie i odtwarzanie działają tak
   jak wcześniej także bez logowania.
6. Pomoc `Ctrl+F1`, ustawienia oraz paleta `Ctrl+Shift+K` opisują zakres konta,
   kierunek synchronizacji i różnicę między Biblioteką AMC a kontem YouTube.

## Prace i weryfikacja

- Data rozpoczęcia: 21 października 2026 — na nowe jawne polecenie użytkownika.
- Decyzja o kliencie Google i weryfikacji: aplikacja komputerowa, zwykła
  przeglądarka systemowa, Authorization Code z PKCE S256 i odpowiedź na
  losowym porcie `127.0.0.1`. Nie używamy osadzonej przeglądarki ani wycofanego
  przepisywania kodu OOB. AMC Test otrzymuje dane konkretnego klienta z dwóch
  lokalnych zasobów ignorowanych przez Git; do procesu potomnego przekazuje
  tylko ścieżkę pliku sekretu. Oficjalne źródła:
  [OAuth dla aplikacji komputerowych](https://developers.google.com/identity/protocols/oauth2/native-app),
  [autoryzacja YouTube Data API](https://developers.google.com/youtube/data/guides/auth/installed-apps),
  [wycofanie OOB](https://developers.google.com/identity/protocols/oauth2/resources/oob-migration).
- Zakresy OAuth: tylko
  `https://www.googleapis.com/auth/youtube.readonly` w pierwszym etapie.
- Weryfikacja publikacji: profil publiczny pozostaje wyłączony, dopóki AMC nie
  ma własnego projektu Google, skonfigurowanego ekranu zgody, polityki
  prywatności i wymaganej weryfikacji zakresu. W trybie testowym Google pozwala
  wskazać ograniczoną listę kont testowych; nie jest to jeszcze przepływ dla
  wszystkich użytkowników. Oficjalne źródła:
  [wymagania weryfikacji](https://support.google.com/cloud/answer/13463073?hl=en),
  [status testowy ekranu zgody](https://support.google.com/cloud/answer/15549945?hl=en).
- Zmienione pliki: `src/AccessibleMediaController.Core/YouTube/YouTubeOAuthProtocol.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeOAuthTokenClient.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeOAuthLoopbackReceiver.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeAccountCoordinator.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeSubscriptionClient.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeSubscriptionSyncPlanner.cs`,
  `src/AccessibleMediaController.Core/YouTube/YouTubeSubscriptionSyncApplier.cs`,
  `src/AccessibleMediaController.Windows/Services/YouTubeCredentialStore.cs`,
  `src/AccessibleMediaController.LiteHost/LiteYouTubeAccountCoordinator.cs`,
  `src/AccessibleMediaController.LiteHost/LiteYouTubeWindowsAccountBackend.cs`,
  `src/AccessibleMediaController.LiteHost/Protocol/LiteYouTubeAccountContract.cs`,
  powiązanie magazynu z LiteHostem oraz testy Core, Windows i protokołu.
- Testy: `dotnet run --project
  tests/AccessibleMediaController.Core.SmokeTests/AccessibleMediaController.Core.SmokeTests.csproj
  --no-restore -- --youtube-oauth-foundation` — zaliczone 10 z 10 scenariuszy.
  Test granicy poświadczeń Windows `--youtube-credential-boundary` — zaliczone
  6 z 6 sprawdzeń. Test `--youtube-account-coordinator` — zaliczone 5 z 5
  scenariuszy cyklu konta. Test `--youtube-subscriptions` — zaliczone 5 z 5
  scenariuszy odczytu, stronicowania i błędów API. Test
  `--youtube-subscription-sync-plan` — zaliczone 5 z 5 scenariuszy polityki
  jednokierunkowej. Test `--youtube-subscription-sync-apply` — zaliczone 4 z 4
  scenariuszy prawdziwej bazy SQLite. Kompilacja Release Core SmokeTests oraz
  projekty Windows i LiteHost zakończyły się bez ostrzeżeń i błędów. Test
  protokołu `--youtube-account` — zaliczone 5 z 5 scenariuszy, kompilacja
  ProtocolTests Release — zaliczona bez ostrzeżeń i błędów.
- Commity źródła i testów: `ce723bff` (`feat(youtube): add safe OAuth protocol foundation`)
  `0c15fbcb` (`feat(youtube): isolate token exchange and credentials`) oraz
  `cbd2a5d3` (`feat(youtube): add guarded loopback callback`) i `161cb856`
  (`feat(youtube): coordinate account lifecycle safely`) oraz `86309bb0`
  (`feat(youtube): read account subscriptions safely`) i `436c5e3d`
  (`feat(youtube): plan one-way subscription sync`) oraz `904c8011`
  (`feat(youtube): apply subscription sync atomically`) i `8f0c1341`
  (`feat(youtube): connect guarded account host protocol`).
- Zainstalowana kompilacja AMC Test zawierająca niewidoczny fundament:
  `2026.10.21-b258fb69fef580f7899c30abd0d48e6b877119be-726f0791`, 1668 plików.
  Kandydat i zainstalowana kopia przeszły integralność oraz kontrolowany start.
  Instalacja nie włączyła polecenia, nie skonfigurowała klienta Google, nie
  otworzyła przeglądarki i nie zalogowała konta.

## Materiał do dokumentacji użytkownika

Logowanie do YouTube jest przygotowane w źródle AMC Test, lecz polecenie
pojawia się dopiero w kompilacji z prawidłowym identyfikatorem OAuth AMC.
Otwiera oficjalną stronę Google w zwykłej przeglądarce i wraca do AMC przez
lokalny adres na komputerze. AMC nie prosi użytkownika końcowego o hasło Google
ani o sekret aplikacji; dane klienta przygotowuje opiekun kompilacji. Pierwsza
wersja prosi wyłącznie o odczyt subskrypcji; zwykłe
wyszukiwanie, odtwarzanie i pobieranie pozostają dostępne bez konta. Najpierw
użytkownik sprawdza plan zmian, a dopiero osobnym przyciskiem zapisuje kanały
w Bibliotece AMC.

## Uzasadnienie i decyzje

- Samo uruchomienie AMC nadal nie otwiera przeglądarki, nie uruchamia odbiornika
  i nie łączy się z Google. Odbiornik powstanie dopiero po przyszłym, jawnym
  poleceniu logowania użytkownika.
- Weryfikator PKCE nie trafia do adresu przeglądarki. Adres zawiera tylko jego
  skrót S256 i losowy stan chroniący powrót do właściwej próby logowania.
- Akceptowany jest wyłącznie `http://127.0.0.1` z jawnie przydzielonym portem.
  `localhost`, zdalny host, HTTPS udające lokalny odbiornik i port domyślny są
  odrzucane przed rozpoczęciem logowania.
- Polecenie ma jeden wpis w menu, palecie i pełnej pomocy, ale trafia do tych
  powierzchni dopiero po potwierdzeniu możliwości przez uruchomiony host.
  Bez identyfikatora klienta Google pozostaje niewidoczne, więc nie tworzy
  martwej funkcji.
- Wymiana kodu i odświeżenie korzystają wyłącznie z oficjalnego punktu tokenów
  Google. Po korekcie z 23.10.2026 wysyłają wymagany przez tego klienta
  `client_secret` tylko w treści żądania do punktu tokenów; wartość nie trafia
  do adresu logowania, wiersza poleceń, logu ani UI. Odświeżenie nie prosi po
  cichu o szerszy zakres.
- Poświadczenia AMC Test i publicznego AMC mają różne cele w Menedżerze
  poświadczeń Windows. Nie są częścią migawki wspólnych danych i nie mogą
  przejść z profilu testowego do publicznego.
- Jednorazowy odbiornik słucha wyłącznie na `127.0.0.1`, przydziela losowy
  port, sprawdza dokładną ścieżkę i losowy stan stałoczasowo oraz odrzuca
  powtórzone lub nadmiernie duże pola. Strona powrotu nie zawiera kodu i ma
  zakaz zapisu w pamięci podręcznej.
- Jeden koordynator jest właścicielem całego cyklu konta. Dopiero jawne
  logowanie może uruchomić stronę Google; anulowanie nie nadpisuje poprzedniego
  konta, świeży token nie powoduje żądania sieciowego, wygasły jest odświeżany
  dokładnie raz, a wylogowanie usuwa tylko magazyn bieżącego profilu.
- Odczyt subskrypcji używa oficjalnego `subscriptions.list` z `mine=true`,
  pobiera wszystkie strony po 50 pozycji, przekazuje token wyłącznie w nagłówku
  Bearer i scala duplikaty po stabilnym identyfikatorze kanału. Nie zapisuje
  jeszcze niczego w Bibliotece AMC. Oficjalne źródła:
  [subscriptions.list](https://developers.google.com/youtube/data/reference/rest/v3/subscriptions/list?hl=en),
  [błędy YouTube Data API](https://developers.google.com/youtube/data/reference/rest/v3/errors).
- Plan synchronizacji jest czysty i niedestrukcyjny: nie zapisuje bazy przed
  potwierdzeniem. Rozróżnia nowe, już obecne i świadomie usunięte kanały,
  ignoruje zdalny brak bez usuwania danych, a przywrócenie oznacza osobną akcję
  wskazującą istniejący rekord AMC.
- Zatwierdzony plan może zostać zapisany jedną transakcją do bazy Podcastów.
  Nowe kanały trafiają jako źródła bez masowego pobierania materiałów; mają
  zerowy czas ostatniego odświeżenia, więc istniejący harmonogram uzupełnia je
  później w skonfigurowanych porcjach. Wyłączony automat pozostaje wyłączony i
  wtedy użytkownik może odświeżyć źródła ręcznie.
- Protokół hosta rozdziela status, jawne logowanie, wylogowanie, podgląd i
  zastosowanie synchronizacji. Zastosowanie wymaga podglądu nie starszego niż
  dziesięć minut i dokładnie tego samego wyboru przywracania usuniętych kanałów.
  Odpowiedzi zawierają tylko użytkowe nazwy oraz liczniki; tokeny, kody, adresy,
  identyfikatory klienta, konta i kanału nie przechodzą do Pythona.
- Host rejestruje te operacje tylko w profilu `AMC Test`, gdy otrzyma prawidłowy
  identyfikator klienta Google i ścieżkę bazy Podcastów. Sam brak konfiguracji
  nie tworzy martwych poleceń. Publiczny profil pozostaje twardo wyłączony.

## Testy i wynik

Zaliczono dziesięć syntetycznych scenariuszy Core: żądanie tylko do odczytu z PKCE S256,
odrzucanie niebezpiecznych adresów powrotu, wymianę kodu i odświeżenie bez
sekretu klienta, zachowanie refresh tokenu i zakresu oraz brak treści wadliwej
odpowiedzi Google w wyjątku. Sześć dalszych sprawdzeń Windows potwierdziło
osobne cele magazynu dla AMC Test/AMC, odrzucenie nieznanego profilu, pełny
zapis i odczyt syntetycznego rekordu oraz odrzucenie rekordu niepełnego i zbyt
dużego. Testy nie używały sieci, prawdziwego klienta Google, przeglądarki ani
danych użytkownika; nie zapisały także syntetycznych tokenów w prawdziwym
Menedżerze poświadczeń. Dwa scenariusze odbiornika użyły wyłącznie lokalnego
połączenia `127.0.0.1` na losowym porcie i potwierdziły prawidłowy powrót oraz
odrzucenie odpowiedzi z obcym stanem. Pięć scenariuszy koordynatora potwierdziło
zapis dopiero po prawidłowym powrocie, zachowanie konta po odmowie, odświeżenie
wygasłego tokenu, brak sieci dla świeżego tokenu i wylogowanie. Pięć scenariuszy
klienta subskrypcji potwierdziło wszystkie strony, usuwanie duplikatów po ID,
zatrzymanie powtarzającej się strony, użytkowe błędy limitu i konta bez kanału
oraz pomijanie wpisów bez stabilnej tożsamości. Pięć scenariuszy planu
synchronizacji potwierdziło nowe kanały, brak duplikatów, zachowanie lokalnie
usuniętego źródła, jawne przywrócenie i brak usuwania po zniknięciu z Google.
Cztery scenariusze prawdziwej tymczasowej bazy SQLite potwierdziły atomowy
zapis pustych źródeł oczekujących na odświeżenie, idempotentne ponowienie,
ochronę świadomie usuniętego kanału, jawne przywrócenie istniejącego rekordu,
brak usuwania przy pustej odpowiedzi oraz brak częściowego zapisu przy kolizji.
Sześć scenariuszy protokołu potwierdziło oddzielenie podglądu od zapisu, brak
sekretów i technicznych identyfikatorów w JSON, jednoznaczny wybór przywracania,
redakcję nieznanego błędu, zachowanie konkretnego komunikatu o limicie oraz
jawne anulowanie trwającego logowania bez technicznego tekstu wyjątku.
Wspólna regresja pustego profilu, katalogu i nawigacji wyszukiwania zakończyła
się wynikiem 88/88. Kompilacja Release uruchamiacza, aktualizatora i LiteHosta
zakończyła się bez błędów; złożony pakiet miał 1668 plików, a odizolowany start
przeszedł przed i po atomowej instalacji.

## Znane ograniczenia

- Nie wykonano jeszcze prawdziwego logowania, odmowy na stronie Google,
  synchronizacji konta użytkownika ani ręcznego przejścia fokusu i mowy NVDA.
  Klient Google jest już gotowy; te próby wymagają obecności użytkownika i
  świadomego wyboru konta na stronie Google.
- Projekt Google pozostaje w trybie Testing. Działa tylko dla wpisanych
  użytkowników testowych, a zgoda testowa może wygasać po siedmiu dniach.
- Profil publiczny wymaga osobnej decyzji po konfiguracji i weryfikacji Google.

## Wersja i commit

Kod źródłowy i testy są zapisane w lokalnych commitach `ce723bff`, `0c15fbcb`,
`cbd2a5d3`, `161cb856`, `86309bb0`, `436c5e3d`, `904c8011` oraz `8f0c1341`.
Interfejs wx, wspólny model poleceń, anulowanie logowania i pakowanie lokalnej
konfiguracji testowej zapisano w commicie `40ad286c`.
Zainstalowany AMC Test pochodzi z rewizji
`eea8e9f50fc39e64542ed59119cf7c6273dcae7f`, paczki `cd5a4c27`; publikacji
nie wykonywano. Lokalny, ignorowany przez Git zasób identyfikatora OAuth jest
częścią wyłącznie tej paczki testowej. Odbiór użytkowy blokuje już tylko
prawdziwe logowanie i ręczne sprawdzenie NVDA, a nie brak konfiguracji.

## Aktualizacja implementacyjna — 23 października 2026

Ta aktualizacja zastępuje zapis z 21 października mówiący, że interfejs wx
jeszcze nie istnieje. Fundament hosta pozostał bez zmian zakresu uprawnień,
a nowa warstwa użytkowa jest nadal ograniczona do `AMC Test`.

### Zachowanie widoczne dla użytkownika

- Po prawidłowym skonfigurowaniu klienta Google sesja `Podcasty i YouTube`
  otrzymuje polecenie `Konto YouTube i synchronizacja subskrypcji…` w menu
  Pliki, palecie `Ctrl+Shift+K` i pełnej pomocy `F1`. Bez konfiguracji nie ma
  go w żadnej z tych powierzchni.
- Okno rozpoczyna fokus od `Zaloguj konto YouTube przez Google w przeglądarce`
  albo, gdy konto jest połączone, od `Sprawdź subskrypcje YouTube bez
  zapisywania`.
- Lista ma jawną nazwę dostępnościową `Kanały planowane do zapisania w
  Bibliotece AMC`; zawiera wyłącznie oczyszczone nazwy kanałów, nigdy rekord,
  identyfikator kanału ani adres.
- `Zapisz sprawdzone subskrypcje w Bibliotece AMC` jest niedostępne przed
  świeżym podglądem. Zmiana pola `Przywróć kanały wcześniej usunięte z
  Biblioteki AMC` unieważnia podgląd i wymaga ponownego sprawdzenia.
- Zamknięcie okna podczas logowania najpierw anuluje lokalne oczekiwanie.
  Wylogowanie ma osobne potwierdzenie wyjaśniające, że usuwa tylko połączenie
  z bieżącego profilu AMC i nie zmienia hasła ani konta Google.

### Kod, tryby i konfiguracja

- Interfejs: `wxlite/amc_wx_lite/gui.py`; bezpieczne parsowanie etykiet i
  konfiguracji: `wxlite/amc_wx_lite/youtube_account.py`; klient protokołu:
  `wxlite/amc_wx_lite/host_client.py`.
- Jedno polecenie `Action.YOUTUBE_ACCOUNT` zasila menu, paletę, pomoc i ten sam
  dispatcher. Jego widoczność pochodzi z odpowiedzi
  `youtube.accountCapabilities`, nie z oddzielnych stałych GUI.
- `AMC Test` ma możliwość `youtube.account.readonly`; `AMC Public` jej nie ma.
  Publiczny pakiet nie kopiuje zasobu klienta Google, nawet gdy leży on w
  źródłach testowych.
- Lokalny identyfikator aplikacji komputerowej należy umieścić w ignorowanym
  pliku `wxlite/amc_wx_lite/youtube-oauth-client-id.txt`. Builder waliduje
  format i kopiuje go tylko do paczki testowej. Zmienna
  `AMC_YOUTUBE_CLIENT_ID` służy wyłącznie do uruchomień deweloperskich.
- Identyfikator klienta nie jest sekretem aplikacji komputerowej. Tokeny,
  kody, stan OAuth i dane konta nadal należą wyłącznie do hosta C# i magazynu
  poświadczeń Windows.

### Testy i rzeczywiste wyniki

- Python: 66/66 testów klienta, profili, palety i kontraktu YouTube; szersza
  regresja menu, GUI i startu: najpierw 150/152, następnie po poprawie izolacji
  importu 15/15; końcowy zestaw konfiguracji, pakowania, startu i powierzchni
  poleceń: 103/103.
- Końcowa pełna regresja Python po poprawce i zbudowaniu LiteHosta Release:
  1961 zaliczonych, 139 kontrolowanie pominiętych i 11 zaliczonych podtestów;
  bez błędów. LiteHost zbudował się w Release bez ostrzeżeń i błędów.
- C# ProtocolTests: wszystkie 27 zestawów, w tym sześć scenariuszy konta
  YouTube. Składnia Python i `git diff --check` również zaliczone.
- Nie użyto prawdziwego konta, sieci Google ani przeglądarki. Nie zbudowano i
  nie uruchomiono instalatora, nie zainstalowano nowej wersji i niczego nie
  opublikowano.

### Odbiór i migracja

Nie ma migracji danych ani automatycznego włączenia funkcji. Do odbioru trzeba
utworzyć własny klient OAuth typu Desktop dla AMC, dodać konto testowe w
ekranie zgody Google, zapisać identyfikator w zasobie testowym, zbudować nową
paczkę `AMC Test`, a potem ręcznie przejść z NVDA: stan początkowy, logowanie,
anulowanie, odmowę, powrót fokusu, podgląd, zmianę pola przywracania, zapis,
wylogowanie i ponowne otwarcie okna. Dopiero ten odbiór rozstrzyga o instalacji
aktualizacji; profil publiczny pozostaje poza zakresem.

## Aktualizacja odbiorcza — 23 października 2026, 15:14

Ta aktualizacja zastępuje wcześniejszą informację, że brakuje identyfikatora
klienta Google i że nie zbudowano wersji do odbioru.

### Zachowanie widoczne dla użytkownika

- W projekcie Google Cloud `AMC Test YouTube` utworzono klienta OAuth typu
  aplikacja komputerowa pod nazwą `AMC Test Windows`.
- Zakres zgody pozostał ograniczony do
  `https://www.googleapis.com/auth/youtube.readonly`; na ekranie zgody jest
  jeden nazwany użytkownik testowy.
- Pole `Aplikacja działa jako agent wykorzystujący AI` pozostawiono wyłączone.
  AMC jest zwykłą aplikacją komputerową wykonującą jawne polecenia użytkownika,
  a nie autonomicznym agentem działającym w jego imieniu.
- W `AMC Test` polecenie `Konto YouTube i synchronizacja subskrypcji…` może
  pojawić się w menu Plik, palecie `Ctrl+Shift+K` i pełnej pomocy. Sam start
  programu nadal nie otwiera przeglądarki i nie łączy konta.
- W profilu publicznym polecenie oraz zasób klienta pozostają wyłączone.

### Dokładna konfiguracja i lokalizacja

- Stan historyczny instalacji 15:14: publiczny identyfikator klienta zapisano
  bez sekretu w lokalnym, ignorowanym
  przez Git pliku
  `wxlite/amc_wx_lite/youtube-oauth-client-id.txt`.
- Builder zwalidował końcówkę `.apps.googleusercontent.com`, brak białych
  znaków oraz długość, po czym skopiował zasób tylko do
  `app/amc_wx_lite/youtube-oauth-client-id.txt` paczki testowej.
- Sekret klienta nie został pobrany, zapisany ani dodany do repozytorium.
  Token użytkownika nadal ma trafić wyłącznie do chronionego magazynu Windows.
- Kanoniczna instalacja pozostaje w `D:\Projekty Codex\AMC Python`; nie
  utworzono instalatora ani wydania publicznego.

### Komunikaty i odbiór NVDA

Po wejściu do okna fokus ma rozpocząć się od `Zaloguj konto YouTube przez
Google w przeglądarce`. Po zalogowaniu stan ma zostać wypowiedziany tekstem
użytkowym, a lista ma nazywać się `Kanały planowane do zapisania w Bibliotece
AMC`. Ręczny odbiór ma objąć początkowy fokus, Tab i Shift+Tab, anulowanie,
odmowę Google, powrót fokusu, podgląd subskrypcji, zmianę pola przywracania,
zapis, wylogowanie i ponowne otwarcie okna. Nie wolno wypowiadać identyfikatora
klienta, kanału, nazwy typu ani surowej odpowiedzi protokołu.

### Uzasadnienie i decyzje

- Identyfikator klienta aplikacji komputerowej jest publiczną konfiguracją,
  dlatego może być dołączony do paczki testowej; nie jest hasłem ani sekretem.
- Tryb Google Testing wystarcza do prywatnego odbioru, lecz nie jest modelem
  dystrybucji publicznej. Publiczne AMC będzie wymagać odrębnej decyzji,
  projektu produkcyjnego, polityki prywatności i ewentualnej weryfikacji Google.
- Pierwsza próba instalacji nie naruszyła starej instalacji: aktualizator
  odmówił podmiany, gdy po bezpiecznym zamknięciu nadal istniały procesy AMC.
  Nie trwało nagrywanie. Frontend zapisał stan, a aktywna operacja sieciowa
  rozpoznawania utworu zakończyła się po limicie; procesy zamknęły się
  samodzielnie bez wymuszonego zabicia. Dopiero wtedy ponowiono atomową
  instalację zweryfikowanego kandydata.

### Testy i wynik

- Testy launchera i aktualizatora: 30/30 zaliczonych.
- Kompilacja serwera testowego protokołu i LiteHosta: 0 ostrzeżeń, 0 błędów.
- Pełna regresja Python/wx: 2014 zaliczonych, 111 kontrolowanie pominiętych,
  11 zaliczonych podtestów w 142,89 s.
- Kandydat: 1672 pliki, pełna tożsamość `cd5a4c27`, kontrolowany start
  interfejsu i hosta zaliczony.
- Instalacja: atomowa podmiana zakończona, szybka i pełna kontrola integralności
  zainstalowanej paczki zaliczone, ponowny kontrolowany start zaliczony.
- Uruchomiona aplikacja: `AMC Test — 23.10.2026, 15:14`, proces Pythona z
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.
- Nie wykonano jeszcze prawdziwego żądania OAuth ani synchronizacji danych;
  wymagają ręcznej czynności użytkownika w przeglądarce i odbioru NVDA.

### Znane ograniczenia

- Logowanie zadziała tylko dla kont dodanych do użytkowników testowych projektu
  Google, dopóki aplikacja pozostaje w trybie Testing.
- Zgoda testowa może wygasać po siedmiu dniach i wymagać ponownego logowania.
- Nie potwierdzono jeszcze komunikatów ekranu zgody Google ani powrotu fokusu
  na prawdziwym koncie.
- Funkcja nie jest częścią AMC Public i nie została opublikowana.

### Wersja i commit

Zainstalowana paczka ma etykietę
`2026.10.23-eea8e9f50fc39e64542ed59119cf7c6273dcae7f-cd5a4c27`,
rewizję źródła `eea8e9f50fc39e64542ed59119cf7c6273dcae7f` i identyfikator
zawartości `cd5a4c27`. Dokumentację odbioru zapisano po instalacji, dlatego
jej późniejszy commit nie zmienia tożsamości już zainstalowanej paczki.

## Korekta po ręcznym odbiorze — 23 października 2026

Ta informacja zastępuje wcześniejsze założenie, że po instalacji 15:14 można
od razu rozpocząć logowanie. Użytkownik potwierdził, że polecenia nie ma w
palecie `Ctrl+Shift+K`. Rzeczywisty host zwracał typowany wynik z nazwami
`Available`, `Connected` i `Message`, podczas gdy Python oczekiwał wariantu
`available`, `connected` i `message`. W efekcie możliwość była dostępna, lecz
interfejs odczytywał ją jako niedostępną i prawidłowo — na podstawie błędnej
wartości — ukrywał polecenie na wszystkich powierzchniach.

Poprawka wymusza `camelCase` w serializerze całego protokołu LiteHost, nadaje
jawne nazwy przewodowe wszystkim wynikom konta YouTube i pozostawia po stronie
Pythona zgodność przejściową z obydwoma wariantami. Testy obejmują teraz
prawdziwy proces C# i klienta Python, a nie tylko ręcznie zbudowany słownik.
Wynik przed promocją: 22/22 testy celowane, 2016 testów Python zaliczonych,
111 kontrolowanie pominiętych, 11 podtestów zaliczonych, 27/27 zestawów
protokołu oraz 30/30 testów launchera i aktualizatora. Całe rozwiązanie
zbudowało się bez ostrzeżeń i błędów. Był to wynik przed promocją opisaną
poniżej; ponowny ręczny odbiór NVDA jest nadal wymagany.

## Promocja poprawki — 23 października 2026, 15:42

Poprawkę zainstalowano atomowo w `D:\Projekty Codex\AMC Python`. Kandydat i
zainstalowana kopia przeszły integralność oraz kontrolowany start. Bezpośrednia
próba nowego `amc_lite_host.exe` zwróciła wyłącznie oczekiwane nazwy
`available`, `readOnly`, `separateProfileCredentials` i `message`, a
zainstalowany runtime utworzył jeden wpis `Konto YouTube i synchronizacja
subskrypcji…` w palecie. Program działa jako `AMC Test — 23.10.2026, 15:42`.
Prawdziwy przepływ Google i mowa NVDA pozostają do ręcznego odbioru.

## Korekta po pierwszym prawdziwym OAuth — 23 października 2026, 16:04

Ta informacja zastępuje wcześniejsze oczekiwanie, że strona w przeglądarce z
tekstem `Logowanie zakończone` dowodzi zapisanego konta w AMC. O 15:49:18
Google przekazał kod do lokalnego odbiornika i przeglądarka pokazała stronę
AMC, lecz późniejsza wymiana kodu na token została odrzucona. Dziennik hosta
zapisał użytkowy błąd `Google odrzucił logowanie YouTube`, a magazyn
`AccessibleMediaController/test/YouTube` nie powstał. Konto nie było więc
zalogowane, mimo mylącego tekstu w karcie przeglądarki.

### Poprawione zachowanie i organizacja biblioteki

- Strona powrotu mówi teraz: `Google przekazał zgodę do AMC. AMC jeszcze kończy
  logowanie. Możesz zamknąć tę kartę i sprawdzić wynik w aplikacji.` Nie ogłasza
  sukcesu przed odpowiedzią punktu tokenów.
- Znane bezpieczne błędy konfiguracji Google rozróżniają niewłaściwy typ klienta,
  nieprawidłowe żądanie i niezgodny adres powrotu. Surowy opis odpowiedzi Google,
  kod autoryzacyjny i token nadal nie trafiają do komunikatu ani dziennika.
- Po faktycznym sukcesie stan ma powiedzieć `YouTube: zalogowano`, przycisk ma
  nazwę `Zaloguj ponownie konto YouTube przez Google w przeglądarce`, a NVDA
  otrzymuje instrukcję wybrania `Sprawdź subskrypcje`.
- Samo logowanie niczego nie nadpisuje i nie pobiera kanałów do Biblioteki.
  `Sprawdź subskrypcje` tworzy tylko plan i pokazuje wyłącznie kanały nowe lub
  możliwe do przywrócenia. `Zapisz subskrypcje w Bibliotece AMC` osobno scala
  zatwierdzony plan z istniejącymi podcastami i kanałami. Nie ma odrębnego trybu
  widoku: zapisane kanały trafiają do tej samej sesji `Podcasty i YouTube`.

### Testy i stan

- Fundament OAuth: 11/11 scenariuszy, w tym komunikat strony pośredniej i trzy
  bezpieczne diagnozy konfiguracji klienta.
- Kontrakt konta YouTube: 7/7 scenariuszy. Interfejs YouTube razem z komunikatem
  Spotify: 38/38 testów.
- Pełna regresja wxPython: 2016 zaliczonych, 111 kontrolowanie pominiętych, 11
  podtestów zaliczonych. Pełny protokół: 27/27 zestawów. Build Release: bez
  ostrzeżeń i błędów.
- Nie ma jeszcze udanego prawdziwego tokenu ani pobranej listy subskrypcji.
  Po instalacji poprawionej wersji należy ponowić logowanie; nowy komunikat ma
  wskazać konkretną klasę błędu konfiguracji, jeżeli Google ponownie odrzuci
  wymianę kodu.

## Instalacja diagnozy OAuth — 23 października 2026, 16:30

Poprawioną wersję zainstalowano po naturalnym zakończeniu wszystkich aktywnych
nagrań. Kandydat i instalacja `c57a249b` przeszły integralność oraz kontrolowany
start, a lokalna sonda zainstalowanego hosta zwróciła `available=true`,
`readOnly=true` i osobne poświadczenia testowe. Prawdziwy token nadal nie
istnieje: należy ponowić logowanie, a o wyniku rozstrzyga stan w AMC, nie sama
strona powrotu w przeglądarce. Publikacji nie wykonano. Pełny zapis:
[AMC-TEST-2026-10-23-1630-spotify-output-youtube-oauth.md](AMC-TEST-2026-10-23-1630-spotify-output-youtube-oauth.md).

## Korekta po drugim prawdziwym OAuth — 23 października 2026

Użytkownik ponowił logowanie w instalacji 16:30. Strona powrotu podała już
prawidłowy komunikat pośredni, lecz AMC pozostał niezalogowany: przycisk
logowania nadal był dostępny, podgląd i zapis pozostawały nieaktywne, a lista
była pusta. To zastępuje wcześniejsze założenie, że ponowienie na samym
identyfikatorze klienta może zakończyć konfigurację.

Bezpieczna sonda oficjalnego punktu tokenów, z błędnym kodem testowym i bez
danych konta, zwróciła `invalid_request`; klasyfikacja opisu wskazała wyłącznie
brak `client_secret`. Kod AMC rzeczywiście wysyłał identyfikator, kod, PKCE,
adres powrotu i rodzaj żądania, ale pomijał sekret klienta. Przyczyna nie leżała
w koncie użytkownika, zgodzie, zakresie ani obsłudze NVDA.

Commit `3e57b68656ee06c1742a3775bac3d810f792646f` dodaje kompletną parę
konfiguracji tylko do AMC Test. Sekret pozostaje w ignorowanym pliku
`wxlite/amc_wx_lite/youtube-oauth-client-secret.txt`; Python przekazuje
LiteHostowi wyłącznie ścieżkę, a wartość odczytuje C# i wysyła tylko do
oficjalnego punktu tokenów. Niepełna para powoduje ukrycie całej możliwości,
zamiast wystawienia martwego logowania. Wynik operacji jest zapisywany w
prywatnym `frontend.log`, a po błędzie fokus wraca na przycisk, którego nazwa
zawiera bezpieczny ostatni wynik dla NVDA.

Testy źródła: 12 ukierunkowanych testów Python, 11 scenariuszy fundamentu
OAuth, 5 scenariuszy koordynatora oraz zestaw protokołu konta YouTube przeszły.
Kompilacja LiteHosta przeszła przez projekt testów protokołu. Pierwsze z dwóch
równoległych wywołań Core chwilowo zderzyło się o wspólny plik `obj`; po
uruchomieniu sekwencyjnym oba zestawy przeszły. Nie zbudowano ani nie
zainstalowano nowej paczki, ponieważ na komputerze nie ma jeszcze pliku z
sekretem klienta. AMC Public nadal nie zawiera tej możliwości.

## Instalacja kompletnego klienta OAuth — 23 października 2026, 19:28

Ta informacja zastępuje końcowe zdanie poprzedniej sekcji o braku lokalnego
sekretu i paczki. Google nie udostępnia już pobrania ani ponownego wyświetlenia
istniejącego sekretu. Po osobnym potwierdzeniu użytkownika utworzono drugi
sekret w istniejącym kliencie `AMC Test Windows`, pobrano JSON i porównano jego
identyfikator klienta z lokalną konfiguracją AMC. Sekret zapisano w ignorowanym
pliku testowym; nie trafił do Git, dokumentacji, argumentów procesu ani logu.

### Materiał do dokumentacji użytkownika

- W AMC Test 19:28 można otworzyć `Konto YouTube i synchronizacja
  subskrypcji…` z menu Plik, palety `Ctrl+Shift+K` albo pełnej pomocy.
- `Zaloguj konto YouTube przez Google w przeglądarce` rozpoczyna jawny OAuth.
  Samo uruchomienie AMC nie otwiera strony ani nie zmienia Biblioteki.
- Dopiero stan `YouTube: zalogowano` potwierdza zakończenie. Strona powrotu
  oznacza wyłącznie przekazanie zgody do AMC.
- `Sprawdź subskrypcje YouTube bez zapisywania` tworzy podgląd. Osobne
  `Zapisz sprawdzone subskrypcje w Bibliotece AMC` scala zatwierdzony plan z
  bieżącą sesją `Podcasty i YouTube`.

### Uzasadnienie i decyzje

Pakiet zawiera konfigurację tylko w profilu AMC Test. AMC Public nadal nie ma
tej możliwości ani zasobów klienta. Przed promocją wykryto aktywne nagranie i
odłożono kompilację oraz instalację do jego naturalnego zakończenia o 19:25.
Nie przerywano nagrania ani działającego hosta.

### Testy i wynik

- Konfiguracja YouTube i układ pakietu: 37/37 zaliczonych.
- Launcher i aktualizator: 30/30 zaliczonych.
- Pełna regresja wxPython: 2019 zaliczonych, 111 kontrolowanie pominiętych,
  11 zaliczonych podtestów.
- Build C#: bez ostrzeżeń i błędów. Kandydat: 1673 pliki.
- Kontrolowany start kandydata oraz zainstalowanej kopii: zaliczony.
- Instalacja atomowa: zaliczona. Uruchomiony proces pochodzi z
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.

### Znane ograniczenia

Nie wykonano jeszcze prawdziwego OAuth na nowym sekrecie, podglądu ani zapisu
subskrypcji i ręcznego odbioru NVDA. Dwie pobrane kopie JSON pozostają w
niestandardowym, synchronizowanym katalogu pobierania Chrome do czasu
potwierdzenia działania. Po odbiorze należy je usunąć i osobno wyłączyć stary,
utracony sekret w konsoli Google.

### Wersja i commit

Zainstalowano `AMC Test — 23.10.2026, 19:28`, rewizja
`b162b4d113acd3de7c6ad7370428e16d80a972f0`, identyfikator paczki
`892705d2`. Publikacji, instalatora AMC Public ani wysłania do GitHuba nie
wykonywano.

## Korekta po pierwszym OAuth z kompletnym klientem — 23 października 2026

Ta sekcja zastępuje wcześniejsze ograniczenie mówiące, że prawdziwego OAuth na
nowym sekrecie jeszcze nie wykonano. Użytkownik ukończył zgodę Google, lecz
Chrome pokazał `ERR_CONNECTION_REFUSED` dla lokalnego adresu powrotu, a AMC
sprawiał wrażenie zawieszonego. Prywatny dziennik frontendu rozstrzygnął
przyczynę bez odczytywania kodu autoryzacyjnego: dokładnie o 19:40:22 zapisano
`Upłynął czas oczekiwania na logowanie YouTube.`. Pięciominutowy odbiornik
został zamknięty przed powrotem z dostępnego przepływu Google; konfiguracja
klienta, zakres i przekazanie zgody działały.

### Materiał do dokumentacji użytkownika

- Po wybraniu `Zaloguj konto YouTube przez Google w przeglądarce` AMC czeka na
  powrót z Google do 15 minut i mówi o tym w stanie okna.
- Podczas oczekiwania można wybrać `Anuluj oczekiwanie na logowanie YouTube`
  albo `Zamknij okno konta YouTube`. Zamknięcie najpierw bezpiecznie zatrzymuje
  lokalny odbiornik, a potem oddaje fokus do głównego okna.
- Błąd strony `127.0.0.1` po upływie limitu nie oznacza problemu z hasłem ani
  kontem. Należy rozpocząć nowe logowanie; kod z poprzedniego adresu jest
  jednorazowy i nie powinien być kopiowany do AMC.
- Dopiero komunikat `YouTube: zalogowano` jest potwierdzeniem. Następne jawne
  kroki pozostają bez zmian: `Sprawdź subskrypcje`, a potem osobno `Zapisz
  subskrypcje w Bibliotece AMC`.

### Uzasadnienie i decyzje

Domyślny czas hosta zmieniono z 5 na 15 minut, a limit klienta protokołu z 6 na
16 minut, tak aby klient nie zakończył oczekiwania przed hostem. Górna granica
hosta pozostaje kontrolowana i wynosi 30 minut. Przycisk `Zamknij` dostał jawny
handler: nie może już zniszczyć modalnego okna i zostawić działającego odbiornika
w tle. W trakcie anulowania wynik starszego logowania nadal jest odrzucany przez
wspólną bramę generacji.

### Testy i wynik

- Koordynator konta YouTube: 6/6 scenariuszy zaliczonych, w tym minimalne
  piętnastominutowe okno dostępnego logowania.
- Testy Python kontraktu konta i etykiet okna: 6/6 zaliczonych.
- Fundament OAuth: 11/11 scenariuszy; protokół LiteHost: 27/27 zestawów.
- Pełna regresja wxPython: 2019 zaliczonych, 111 kontrolowanie pominiętych,
  11 zaliczonych podtestów. Testy launchera i aktualizatora: 30/30.
- Kompilacja składników .NET: bez ostrzeżeń i błędów. Kandydat: 1673 pliki;
  integralność i kontrolowany start zaliczone przed instalacją.
- Pierwsze uruchomienie testów w zainstalowanym runtime nie było testem kodu:
  ten runtime celowo nie zawiera `pytest`. Test powtórzono w istniejącym
  środowisku testowym projektu, bez instalowania zależności globalnych.

Pierwsza próba instalacji została bezpiecznie zatrzymana przez aktualizator:
po ręcznym zamknięciu okna pozostał proces starego AMC Test PID 3284. Proces
pochodził dokładnie z `D:\Projekty Codex\AMC Python\runtime\python.exe`, nie
miał już potomnego silnika ani aktywnego nagrywania. Zwykłe zamknięcie zostało
odrzucone, więc zakończono tylko ten jeden potwierdzony PID. Ponowiona atomowa
instalacja przeszła, a ponieważ aktualizator kończy kopiowanie w osobnym
procesie, zaczekano na jego rzeczywiste zakończenie i dopiero wtedy odczytano
nowy manifest. Integralność i kontrolowany start zainstalowanej kopii przeszły.

### Znane ograniczenia

Nie wykonano jeszcze ponownego prawdziwego OAuth w poprawionej instalacji ani
podglądu subskrypcji. Dwie pobrane kopie konfiguracji Google pozostają
zachowane do potwierdzenia działania; potem należy je usunąć i osobno wyłączyć
stary, utracony sekret w konsoli Google.

### Wersja i commit

Zainstalowano i uruchomiono `AMC Test — 23.10.2026, 20:14`, rewizja
`4fc7abfe281b919b0a68eba3ae7334d74ba85b2b`, identyfikator paczki `5810063c`.
Potwierdzony proces PID 18752 pochodzi z
`D:\Projekty Codex\AMC Python\runtime\python.exe`. AMC Public i GitHub
pozostają bez zmian.

## Wynik ponownego prawdziwego OAuth — 23 października 2026

Ta korekta zastępuje ograniczenie z poprzedniej sekcji, według którego nie
wykonano jeszcze ponownego prawdziwego OAuth ani podglądu subskrypcji.
Użytkownik potwierdził komunikat poprawnego zakończenia logowania, następnie
zobaczył własne kanały i zapisał je do Biblioteki AMC. Okno konta pozostało
otwarte po zapisie; było to zachowanie modalnego menedżera, a nie brak zapisu.
Można je bezpiecznie zamknąć przyciskiem `Zamknij`.

### Materiał do dokumentacji użytkownika

- `Sprawdź subskrypcje YouTube bez zapisywania` pokazuje plan zmian.
- `Zapisz sprawdzone subskrypcje w Bibliotece AMC` zapisuje kanały, ale nie
  zamyka automatycznie menedżera konta. Stan i wynik pozostają dostępne do
  odczytu; `Zamknij` wraca do głównego okna.
- Zapis nie zastępuje ręcznie dodanych podcastów ani kanałów. Scala nowe
  subskrypcje z Biblioteką i respektuje wcześniej świadomie usunięte kanały.

### Test rzeczywisty i ograniczenia

- Prawdziwy OAuth z klientem `Aplikacja komputerowa`: zaliczony.
- Odczyt listy subskrypcji konta: zaliczony.
- Zapis kanałów do Biblioteki AMC: zaliczony przez użytkownika.
- Zwykłe playlisty konta nie są jeszcze częścią działającego kontraktu;
  dlatego YT-001 pozostaje `W trakcie`, mimo że logowanie i kanały działają.

## Synchronizacja zwykłych playlist konta — 23 października 2026, 22:41

Ta sekcja zastępuje ostatnie ograniczenie powyżej. Zwykłe playlisty konta są
już częścią kontraktu AMC Test. Kod, testy, build, instalacja i kontrolowany
start są zakończone; do zamknięcia YT-001 pozostaje ręczny odbiór prawdziwej
playlisty i nawigacji NVDA przez użytkownika.

### Materiał do dokumentacji użytkownika — wersja robocza

- Polecenie ma wspólną nazwę `Konto YouTube, subskrypcje i playlisty…` w menu,
  palecie `Ctrl+Shift+K` i pomocy. Nie ma osobnego skrótu klawiszowego.
- Jeżeli stan brzmi `YouTube: zalogowano`, nie trzeba logować się ponownie.
  AMC używa chronionego lokalnie tokenu odświeżania. Ponowne logowanie jest
  potrzebne po wylogowaniu, cofnięciu zgody, unieważnieniu dostępu albo po
  wygaśnięciu autoryzacji testowej Google.
- `Sprawdź playlisty YouTube bez zapisywania` pobiera własne playlisty konta i
  pokazuje wyłącznie użytkowe etykiety: nazwa, dostępność oraz liczba materiałów.
  Techniczny identyfikator playlisty i token nie są czytane przez NVDA.
- `Zapisz sprawdzone playlisty w Bibliotece AMC` jest osobnym poleceniem.
  Dopiero ono dodaje nowe playlisty, przywraca jawnie wybrane usunięte
  playlisty i aktualizuje zawartość istniejących.
- Pole wyboru nazywa się `Przywróć kanały i playlisty wcześniej usunięte z
  Biblioteki AMC`. Zmiana tego wyboru unieważnia wcześniejszy podgląd i wymaga
  ponownego sprawdzenia.
- Podgląd playlist kieruje fokus na przycisk ich zapisu; po zapisie fokus wraca
  na `Sprawdź playlisty`. Zamknięcie okna oddaje fokus do głównej listy.
- Zapis działa tylko w kierunku YouTube → AMC. Nie tworzy, nie usuwa i nie
  zmienia playlist na koncie Google ani YouTube.

### Zachowanie danych i uzasadnienie

- Klient używa oficjalnych, autoryzowanych metod `playlists.list(mine=true)` i
  `playlistItems.list` z zakresem `youtube.readonly`; wszystkie żądania są GET.
- Podgląd nie zapisuje bazy. Zapis przyjmuje tylko podgląd młodszy niż dziesięć
  minut i dokładnie ten sam wybór przywracania.
- Nieobecność playlisty w późniejszej odpowiedzi YouTube nie usuwa jej z AMC.
  Playlista wcześniej usunięta lokalnie nie wraca bez jawnego zaznaczenia.
- Istniejąca lokalna nazwa własna, historia odtwarzania, pozycje, stan nowych
  materiałów i lokalne archiwum są scalane przez wspólny mechanizm Biblioteki.
- Nie zmieniono schematu bazy danych. Nie jest potrzebna migracja profilu.
- Profil AMC Public nadal nie udostępnia konta YouTube; zmiana jest aktywna
  wyłącznie w AMC Test.

### Komunikaty dostępnościowe

- Podczas odczytu: `Sprawdzanie playlist YouTube bez zapisywania zmian.`
- Pusta lista: `Brak playlist do zapisania`.
- Przed zapisem lista ma nazwę `Playlisty planowane do zapisania w Bibliotece
  AMC`.
- Podsumowanie rozróżnia nowe, przywracane i aktualizowane playlisty oraz mówi,
  ile playlist objął limit pierwszych 100 materiałów.
- Błędy logowania, limitu API, odmowy dostępu, nieczytelnej odpowiedzi i
  nieaktualnego podglądu mają zamknięty zestaw komunikatów użytkowych. Surowa
  odpowiedź serwera, identyfikator i reprezentacja obiektu nie wychodzą do GUI.

### Testy i rzeczywiste wyniki

- Nowy klient oficjalnego API playlist: 3/3 scenariusze.
- Atomowa synchronizacja playlist: 4/4 scenariusze, w tym brak mutacji w
  podglądzie, zachowanie lokalnej nazwy, jawne przywracanie i brak usuwania przy
  nieobecności po stronie YouTube.
- Cała ukierunkowana regresja Core YouTube: 41/41 scenariuszy; obejmuje OAuth,
  konto, subskrypcje, playlisty oraz transmisje live/upcoming.
- Kontrakt konta LiteHost: 9/9 scenariuszy. Etykiety playlist nie zawierają ID
  ani adresów technicznych.
- Okno konta YouTube: 6/6 testów; wspólne menu, paleta, pomoc i skróty: 127/127.
- Pełna regresja wxPython: 2025 zaliczonych, 111 kontrolowanie pominiętych,
  13 podtestów zaliczonych. Launcher i aktualizator: 30/30.
- Kompilacja Core, LiteHost i testów protokołu: 0 błędów i 0 ostrzeżeń.
- Ostateczny scalony kandydat zawierał 1674 pliki. Integralność i kontrolowany start
  kandydata oraz zainstalowanej kopii przeszły przed widocznym uruchomieniem.
- Instalacja atomowa i ponowny start zostały wykonane dopiero po potwierdzeniu,
  że żaden plik roboczy nagrania AMC nie jest aktywnie zapisywany.

### Znane ograniczenia i ręczny odbiór

- AMC zapisuje najwyżej pierwszych 100 pozycji każdej playlisty i mówi o tym w
  podsumowaniu. Dalsze pozycje nie są w tej wersji pobierane.
- Materiał usunięty albo niedostępny dla API może zostać pominięty. Prywatność
  samej playlisty jest odczytywana, lecz OAuth Data API nie jest przekazywany
  do odtwarzacza; możliwość odtworzenia prywatnego filmu nadal zależy od
  publicznego toru medialnego YouTube.
- Oficjalne API nie udostępnia w ten sposób systemowej listy `Do obejrzenia`
  ani historii oglądania. AMC ich nie obiecuje.
- Użytkownik ma jeszcze sprawdzić z NVDA: ponowne otwarcie okna bez logowania,
  `Sprawdź playlisty`, strzałki po liście, zapis, powrót fokusu, ponowne
  otwarcie oraz widok playlisty w Bibliotece.

### Korekta po odbiorze: puste kanały z konta — 23.10.2026

Użytkownik potwierdził działanie przyspieszania Spotify oraz opisów `Alt+D`,
ale zgłosił dużą liczbę materiałów i puste kanały, których wcześniej nie było
w lokalnej Bibliotece. Wykonano wyłącznie diagnostykę tylko do odczytu; bazy i
ustawień nie zmieniano.

Rzeczywisty stan `podcasts.db`:

- 421 źródeł typu kanał YouTube i 23 406 zapisanych materiałów;
- 86 wcześniejszych publicznych importów — wszystkie zawierają materiały;
- 335 źródeł utworzonych z subskrypcji konta, z czego 315 pozostaje w
  Bibliotece;
- 162 kanały konta zostały odświeżone, natomiast 153 kanały pozostające w
  Bibliotece są puste i mają zerowy czas ostatniego odświeżenia;
- kontrola po stabilnym identyfikatorze kanału, znormalizowanym adresie oraz
  identyfikatorze filmu wykazała 0 podwójnych kanałów, 0 dodatkowych kopii
  filmu między kanałami i 0 powtórzeń filmu wewnątrz jednego kanału.

Przyczyna jest potwierdzona. Automatyczne odświeżanie wybiera co minutę pięć
źródeł o najstarszym czasie poprawnego odświeżenia. Pierwsze pięć źródeł z
czasem zero nie ma standardowej karty `/videos`; `yt-dlp` kończy każde z nich
błędem `This channel does not have a videos tab`. Nieudana próba nie zapisuje
osobnego czasu próby ani odroczenia. Następna minuta wybiera więc ponownie te
same pięć źródeł i pozostałe 153 kanały nie dostają swojej kolejki.

Publiczna próba stron głównych tych samych pięciu kanałów przeszła bez
logowania: trzy zwróciły co najmniej jeden materiał z innej karty, dwa
poprawnie odpowiedziały pustą listą. Oznacza to, że naprawa powinna rozdzielić
dwa problemy:

1. po braku karty `Filmy` sprawdzić bezpieczny publiczny widok kanału lub
   obsługiwane karty, zamiast zawsze wymuszać `/videos`;
2. zapisywać osobny czas nieudanej próby i stosować uczciwą kolejkę z
   odroczeniem, bez fałszywego oznaczania źródła jako poprawnie odświeżonego.

Potrzebne testy regresji miały objąć pięć kolejnych błędów, przejście do
szóstego źródła, ponowienie po odroczeniu, kanał bez standardowej karty
`Filmy`, komunikat użytkowy NVDA i brak technicznej nazwy karty w zwykłym
interfejsie. Poniższa korekta z 24.10.2026 zastępuje zdanie, że diagnoza nie
była jeszcze implementacją, buildem ani instalacją.

### Naprawa kolejki i trwałość usunięć — 24.10.2026

- Schemat bazy Podcastów ma wersję 3 i osobno zapisuje czas każdej próby
  automatycznego odświeżenia. Nieudane źródło czeka własny skonfigurowany
  odstęp, a kolejna porcja dostaje swoją kolejkę. Udanej próby nie udajemy,
  więc czas ostatniego poprawnego odświeżenia zachowuje dotychczasowe
  znaczenie. Ręczne `F5` pozostaje dostępne bez tego odroczenia.
- Jeżeli publiczny kanał nie ma standardowej karty `/videos`, AMC próbuje
  dokładnie raz jego publiczną stronę główną. Obejście nie jest stosowane do
  playlist, błędów sieci ani innych błędów YouTube.
- Sam start AMC i samo logowanie do Google nie synchronizują ani nie
  przywracają Biblioteki. Kanał usunięty lokalnie ma `IsInLibrary=false` i
  pozostaje ukryty po restarcie oraz kolejnej synchronizacji. Wraca wyłącznie
  po jawnym zaznaczeniu pola przywracania w oknie konta.
- Pojedynczy usunięty film ma trwały wpis usunięcia w
  `podcast_removed_episodes`; kolejne odświeżenie tego samego kanału nie dodaje
  go ponownie. Usunięcie kanału i usunięcie filmu są więc chronione osobno.
- Okno konta wyjaśnia te zasady zwykłym tekstem dostępnym dla NVDA.

Test trwałości ponownie otworzył prawdziwą tymczasową bazę, wykonał kolejną
synchronizację i potwierdził, że usunięty kanał nie wrócił. Test kolejki
oznaczył pięć nieudanych prób, ponownie otworzył bazę, przekazał kolejkę
szóstemu źródłu, zachował ręczne odświeżanie i po 60 minutach wrócił do
najstarszej porcji. Po instalacji rzeczywista baza użytkownika przeszła do
schematu 3; pierwszy automatyczny przebieg zapisał pięć osobnych prób, z czego
trzy zakończyły się poprawnym odświeżeniem, a dwie zachowały brak czasu
sukcesu. To potwierdza działanie nowego rozdzielenia próby od sukcesu na
zainstalowanej kopii. Kolejne minuty zwiększyły licznik do 13 różnych prób,
zamiast wracać do pierwszej piątki; liczba kanałów w Bibliotece, które nigdy
nie były odświeżone, spadła z 96 do 86. Wszystkie 123 kanały usunięte lokalnie
pozostały poza Biblioteką.

### Historia wersji, commit i publikacja

Korekta z 23.10.2026: opisy playlist i materiałów zwracane przez oficjalne API
są teraz zapisywane podczas synchronizacji. Wspólne zachowanie `Alt+D`, w tym
obsługa starszych publicznych importów bez ponownego logowania, jest opisane w
[YT-003-opisy-youtube-alt-d.md](YT-003-opisy-youtube-alt-d.md). Ta korekta
uzupełnia wcześniejszy zapis playlist; nie zmienia zakresu OAuth ani zasad
ponownego logowania.

Implementacja playlist ma commit
`0e8d219f5c759b28183063cefd8d9cedde06de19`. Zainstalowano i uruchomiono
ostateczną scaloną wersję `AMC Test — 23.10.2026, 22:41`, rewizja źródłowa
`9e8d3eab643b579215719bc52ac77b215f0c6fea`, identyfikator paczki `ce7898a4`.
Uruchomione procesy `AMC.exe`, `python.exe` i `amc_lite_host.exe` pochodzą z
`D:\Projekty Codex\AMC Python`. AMC Public, instalator i GitHub pozostają bez
zmian.

Korekta z 24.10.2026 zastępuje tę pozycję jako bieżącą instalację: commit
`05621539cba449a06986e3544557d7d039b0e2d9`, pakiet `0ca58fd4`, okno
`AMC Test — 24.10.2026, 00:21`. Szczegóły zawiera
[AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md](AMC-TEST-2026-10-24-0021-youtube-refresh-shortcuts.md).

## Ponowne logowanie w zainstalowanym AMC Test — 27 października 2026

Ta korekta odpowiada na pytanie użytkownika, czy przed następnym wydaniem musi
ponownie tworzyć albo konfigurować projekt Google Cloud. Dla profilu AMC Test
odpowiedź brzmi: nie. Bieżące źródła oraz zainstalowana paczka zawierają pełną
parę klienta `Aplikacja komputerowa` w prywatnych zasobach wyłączonych z Git;
podczas tego odbioru nie zmieniano projektu, ekranu zgody ani klientów w Google
Cloud.

### Rzeczywisty wynik

- Odczyt tylko do odczytu z Menedżera poświadczeń Windows zwrócił
  `YouTube: zalogowano`.
- Ponowne logowanie uruchomiono przez ten sam LiteHost i tę samą konfigurację,
  które zawiera stała instalacja `D:\Projekty Codex\AMC Python`. Oficjalna
  strona Google została otwarta w domyślnej przeglądarce, a powrót nastąpił do
  lokalnego adresu AMC na `127.0.0.1`.
- Google wykorzystało istniejącą sesję oraz wcześniejszą zgodę, dlatego nie
  pojawił się ekran wpisywania hasła ani ręcznego wyboru konta. Końcowa strona
  podała użytkowy komunikat, że zgoda została przekazana do AMC.
- LiteHost zakończył operację wynikiem `Zalogowano do YouTube`, a bezpośredni
  odczyt po operacji potwierdził, że konto nadal jest połączone.
- Próba korzystała z tymczasowej pustej bazy Podcastów, żeby nie otwierać do
  zapisu żywej bazy używanej przez uruchomione AMC. Katalog tymczasowy został
  usunięty po wyniku. Nie zmieniano Biblioteki, ustawień ani nagrań.

Ta próba potwierdza prosty przepływ ponownego logowania, lokalny powrót i zapis
poświadczenia. Nie jest próbą pierwszego logowania obcego konta: nie sprawdza
ekranu ostrzegawczego aplikacji testowej, dodawania nowego testera ani pierwszej
zgody. Taki odbiór wymagałby drugiego konta dodanego jako tester albo jawnego
cofnięcia istniejącej zgody; cofnięcia nie wykonywano.

### Rozdzielenie AMC Test i przyszłego AMC Public

- AMC Test zachowuje obecny projekt testowy. W trybie `Testing` Google dopuszcza
  maksymalnie 100 jawnie dodanych testerów, a ich autoryzacja wygasa po siedmiu
  dniach od udzielenia zgody.
- Dla publicznego wydania Google zaleca osobny projekt produkcyjny. Trzeba w nim
  włączyć YouTube Data API, utworzyć klienta typu `Aplikacja komputerowa`,
  ustawić odbiorców zewnętrznych, opublikować nazwę i dane kontaktowe, podać
  stronę programu oraz politykę prywatności w zweryfikowanej własnej domenie,
  zadeklarować wyłącznie `youtube.readonly` i przejść weryfikację marki oraz
  dostępu do zakresu.
- Po zaakceptowaniu projektu użytkownicy publiczni nie tworzą własnych projektów
  Google Cloud. W AMC wybierają tylko logowanie przez Google w przeglądarce.
  Osobny serwer nie jest potrzebny do lokalnego powrotu OAuth; może natomiast
  udostępniać stronę programu i politykę prywatności wymaganą przy weryfikacji.

### Stan prac i wersja

- Zmiana źródeł: nie wykonano; istniejący mechanizm okazał się wystarczający.
- Test rzeczywisty OAuth: zaliczony 27.10.2026.
- Testy automatyczne, build, instalacja i publikacja: nie były częścią tej
  korekty i nie zostały wykonane ponownie.
- Sprawdzona stała instalacja: rewizja
  `4c8fceda738afd0163040a400150007d16f8409c`, pakiet `faef4e7f`, etykieta
  `2026.10.26-4c8fceda738afd0163040a400150007d16f8409c-faef4e7f`.
- AMC Public, instalator publiczny i GitHub pozostały bez zmian.

## Korekta techniczna AMC Public — 27 października 2026

Ta decyzja zastępuje wcześniejsze założenie z sekcji „Rozdzielenie AMC Test i
przyszłego AMC Public”, że osobny serwer nie będzie potrzebny. Bieżący klient
Google utworzony dla AMC wymaga sekretu przy wymianie i odświeżaniu tokenu, a
publiczny instalator nie może zawierać sekretu. Dlatego AMC Public korzysta z
wąskiego brokera HTTPS tylko do wymiany tokenów. Przeglądarka, PKCE i lokalny
powrót na `127.0.0.1` pozostają w aplikacji. Broker nie zapisuje tokenów, nie
zwraca sekretu i przepuszcza wyłącznie klienta AMC, dwa dozwolone granty oraz
lokalny adres `/youtube/callback/`.

### Zachowanie i rozdzielenie profili

- AMC Test zachowuje dotychczasową konfigurację: identyfikator klienta i
  lokalny plik sekretu przekazywany do hosta poza wierszem poleceń.
- AMC Public przyjmuje wyłącznie publiczny identyfikator klienta i endpoint
  `https://…/v1/google/token`; przekazanie pliku sekretu wyłącza tę konfigurację.
- Profil Public deklaruje `youtube.account.readonly`, ale polecenie konta nadal
  pojawia się dopiero po potwierdzeniu możliwości przez uruchomiony host.
- Budowanie paczki usuwa wszystkie lokalne zasoby AMC Test i sekret. Dwa
  publiczne zasoby bez sekretu są kopiowane wyłącznie do profilu Public i tylko
  jako komplet po walidacji.
- Magazyn poświadczeń pozostaje osobny dla AMC Test i AMC Public.

### Wyniki

- Źródła: zmienione; commit jeszcze nieutworzony.
- Broker Cloudflare Worker: 5 z 5 testów zaliczone.
- Fundament OAuth C#: 13 z 13 scenariuszy zaliczonych.
- Koordynator konta C#: 7 z 7 scenariuszy zaliczonych.
- Build Core, LiteHost, launchera, aktualizatora i testów Core: udany,
  0 ostrzeżeń i 0 błędów.
- Python: składnia zmienionych modułów poprawna; ukierunkowane testy
  konfiguracji, argumentów hosta, profili i pakowania zaliczone. Pełnego
  `pytest` nie uruchomiono, ponieważ dostępny interpreter nie ma tego pakietu.
- Instalacja, rzeczywiste logowanie AMC Public, wdrożenie brokera i publikacja:
  niewykonane. Wymagają produkcyjnego klienta Google, sekretu ustawionego
  wyłącznie po stronie brokera oraz docelowego adresu HTTPS.

## Dokumenty i kontrola zgodności AMC Public — 27 października 2026

Korekta użytkownika z 27.10.2026 zezwala na przygotowanie polityki prywatności
w neutralnym, formalnym języku. Nie jest to artykuł ani tekst pisany stylem
użytkownika. Przygotowano projekt polityki obejmujący cały AMC Public, osobny
projekt warunków korzystania wymagany dla funkcji YouTube oraz listę gotowości
Google/YouTube. Dokumenty są robocze i mają wyraźny zakaz publikacji do czasu
uzupełnienia danych administratora i zamknięcia blokad technicznych.

### Uzasadnienie i decyzje

- YouTube wymaga, aby polityka była łatwo dostępna, opisywała dostęp,
  przechowywanie, użycie i udostępnianie danych, prowadziła do polityki Google
  i ustawień cofnięcia dostępu oraz była zaakceptowana przed funkcjami API.
- Warunki AMC wskazują, że korzystanie z funkcji YouTube oznacza związanie
  Warunkami korzystania z YouTube.
- Google wymaga publicznej strony programu, polityki na tej samej
  zweryfikowanej domenie oraz zgodnych adresów na ekranie zgody OAuth.
- Zasady YouTube wymagają odświeżenia albo usunięcia większości zapisanych
  danych API po 30 dniach. Obecna Biblioteka nie egzekwuje jeszcze tego
  kontraktu.
- Obecne `Wyloguj z YouTube w AMC` usuwa tylko lokalne poświadczenie. Nie
  unieważnia tokenu w Google i nie usuwa wszystkich danych uzyskanych z
  autoryzowanego konta. Publiczne cofnięcie autoryzacji musi programowo
  unieważnić token i rozpocząć usunięcie danych możliwie szybko, najpóźniej
  w ciągu 7 dni. Cofnięcie po stronie Google trzeba wykryć i obsłużyć
  najpóźniej w ciągu 30 dni.
- Dokument nie zgaduje tożsamości administratora, adresu ani okresu retencji
  zgłoszeń. Pozostawiono jawne pola do uzupełnienia.

### Materiał do dokumentacji użytkownika

- Połączenie Google/YouTube jest dobrowolne i ma zakres tylko do odczytu.
- Synchronizacja jest ręczna i jednokierunkowa z YouTube do AMC. Nowa
  subskrypcja wykonana w serwisie YouTube pojawi się przy następnym ręcznym
  sprawdzeniu, a zapis do Biblioteki wymaga osobnego potwierdzenia.
- AMC nie pobiera hasła Google i nie wykonuje na koncie operacji zapisu.
- Cofnięcie dostępu w Google nie jest operacją usunięcia danych zapisanych
  lokalnie. Docelowe polecenie cofnięcia autoryzacji w AMC Public musi jasno
  wyjaśniać oba zakresy i usuwać lokalne dane API zgodnie z zasadami YouTube.
- Polityka, warunki, zgoda i odmowa muszą być dostępne z klawiatury i NVDA;
  powrót fokusu po ich zamknięciu ma być przewidywalny.

### Zmienione i dodane pliki

- `docs/public/POLITYKA_PRYWATNOSCI_AMC.md`;
- `docs/public/WARUNKI_KORZYSTANIA_AMC.md`;
- `docs/public/GOTOWOSC_GOOGLE_YOUTUBE.md`;
- `wxlite/tests/test_public_google_policy_documents.py`.

### Testy i wynik

- Statyczny kontrakt wymaganych ujawnień, odsyłaczy, ostrzeżeń i blokad:
  4 z 4 testów zaliczone.
- Kompilacja składni nowego testu Python: zaliczona.
- Nie uruchamiano interfejsu, pełnej regresji, builda, instalatora ani
  publikacji. Dokumentów nie opublikowano.

### Znane ograniczenia

- Brakuje danych administratora, dedykowanego adresu kontaktowego i okresu
  retencji zgłoszeń.
- Brakuje technicznego odświeżania/usuwania danych API po 30 dniach, pełnego
  cofnięcia autoryzacji, wersjonowanej zgody przed API oraz zawsze dostępnego
  polecenia polityki i warunków w wspólnym modelu interfejsu.
- Brakuje docelowej zweryfikowanej domeny, wdrożonego brokera, konfiguracji
  produkcyjnego projektu Google i rzeczywistego odbioru AMC Public z NVDA.
- Przed publikacją podstawy prawne, role dostawców i transfery wymagają
  krótkiej kontroli właściwej dla tożsamości i sposobu dystrybucji operatora.

### Wersja i commit

- Źródła i dokumenty: zmienione; commit jeszcze nieutworzony.
- Build, pakiet, instalacja i publikacja: niewykonane w tym etapie.

## Cofnięcie zgody, retencja i konfiguracja klienta Public — 27 października 2026

Na polecenie użytkownika kontynuowano przygotowanie klienta Google dla AMC
Public. Ta sekcja zastępuje wcześniejszy stan, w którym wylogowanie profilu
Public usuwało wyłącznie lokalne poświadczenie, a trzydziestodniowa retencja
była tylko blokadą na liście gotowości.

### Zachowanie użytkowe

- AMC Public oznacza kanały i playlisty utworzone albo zaktualizowane z
  autoryzowanego konta oraz zapisuje datę ostatniego potwierdzenia tych danych.
  Publiczne źródła dodane ręcznie nie otrzymują tego znacznika.
- Przy uruchomieniu skonfigurowanego klienta Public oznaczone dane starsze niż
  30 dni są usuwane z Biblioteki wraz z należącymi do nich materiałami.
- Przycisk profilu Public ma nazwę `Cofnij dostęp Google i usuń dane konta z
  AMC`. Najpierw unieważnia refresh token w oficjalnym punkcie Google, potem
  usuwa oznaczone dane z lokalnej bazy, a na końcu usuwa poświadczenie Windows.
- Awaria Google albo lokalnego zapisu nie jest przedstawiana jako sukces.
  Poświadczenie pozostaje, aby użytkownik mógł bezpiecznie ponowić operację.
- Potwierdzenie jasno mówi, że operacja nie usuwa danych zapisanych przez
  YouTube i nie usuwa publicznych źródeł, których synchronizacja konta nie
  utworzyła ani nie zaktualizowała.
- AMC Test zachowuje dotychczasowe prywatne wylogowanie tylko z bieżącego
  profilu i nie usuwa istniejącej Biblioteki użytkownika.

### Uzasadnienie i decyzje

- Cofnięcie tokenu odbywa się bezpośrednio pod
  `https://oauth2.googleapis.com/revoke`; ten endpoint nie wymaga sekretu
  klienta i przyjmuje refresh token.
- Wymiana kodu oraz odświeżanie Public nadal przechodzą przez wąski broker,
  ponieważ tylko on ma sekret produkcyjnego klienta.
- Oddzielny znacznik pochodzenia chroni ręcznie dodane kanały przed usunięciem
  podczas cofnięcia zgody. Sama zgodność adresu albo nazwy nie jest wystarczającą
  podstawą do kasowania.
- Usuwanie po 30 dniach wybrano jako bezpieczne zachowanie zgodnościowe. AMC
  nie rozpoczyna w tle logowania ani autoryzowanego odświeżenia bez działania
  użytkownika.

### Konfiguracja i ochrona sekretu

- Dodano instrukcję `deploy/amc-youtube-oauth-broker/README.md` oraz skrypt
  `Prepare-PublicConfig.ps1`.
- Skrypt przyjmuje wyłącznie publiczny identyfikator klienta oraz adres HTTPS
  brokera. Nie ma parametru sekretu i nie zapisuje go na dysku aplikacji.
- Dodano blokadę `package-lock.json`. Wrangler podniesiono do 4.153.0 po tym,
  jak audyt starszej przypiętej wersji wykazał podatności w zależnościach
  deweloperskich. Ponowny pełny audyt zwrócił 0 podatności.
- `.gitignore` chroni pobrane pliki `client_secret_*.json`, lokalne zmienne
  Workera, katalog `.wrangler` i lokalny `wrangler.jsonc`.

### Testy i rzeczywiste wyniki

- Fundament OAuth: 15 z 15 scenariuszy, w tym oficjalny endpoint cofnięcia i
  bezpieczna obsługa tokenu już unieważnionego.
- Koordynator konta: 9 z 9 scenariuszy, w tym kolejność: Google, lokalne dane,
  poświadczenie, oraz zachowanie możliwości ponowienia po awarii.
- Zapis subskrypcji i retencja: 6 z 6 scenariuszy. Test usuwa stare i jawnie
  cofnięte dane konta, zachowując świeże dane oraz kanał dodany ręcznie.
- Synchronizacja playlist: 4 z 4 scenariusze; zapis pochodzenia i daty jest
  potwierdzony.
- Broker: 5 z 5 testów; `npm audit`: 0 podatności.
- Celowane buildy Core, LiteHost i Core SmokeTests: sukces, 0 ostrzeżeń i
  0 błędów.
- Bezinterfejsowy test etykiet okna YouTube: zaliczony.

### Znane ograniczenia

- Nie utworzono jeszcze rzeczywistego projektu ani klienta produkcyjnego w
  Google Cloud. Wymaga to własnej zweryfikowanej domeny, docelowych adresów
  strony, polityki i warunków oraz zalogowanej sesji właściciela projektu.
- Broker nie został wdrożony, a sekret nie został ustawiony w Cloudflare.
- Nie wykonano prawdziwego logowania, odświeżenia ani cofnięcia na koncie
  produkcyjnym.
- Nadal brakuje wersjonowanej zgody przed pierwszym użyciem API oraz zawsze
  dostępnych poleceń polityki i warunków w menu, palecie i pomocy.
- Nie uruchamiano widocznego interfejsu ani ręcznego odbioru NVDA.

### Wersja i commit

- Źródła: zmienione; commit jeszcze nieutworzony.
- Build celowanych projektów: wykonany pomyślnie.
- Pakiet, instalacja, wdrożenie Workera i publikacja: niewykonane.

## Opcjonalny moduł bez wdrożenia domeny — 27 października 2026

Korekta użytkownika z 27.10.2026 zastępuje rozważany wariant użycia domeny
`stareaudycje.pl`. Ta domena nie będzie stroną AMC, miejscem dokumentów Google
ani adresem brokera OAuth. Użytkownik nie planuje kupować osobnej domeny
wyłącznie dla logowania Google.

### Uzasadnienie i decyzje

- Implementacja klienta i brokera pozostaje w źródłach jako gotowy,
  opcjonalny moduł.
- Brak kompletnej pary publiczny identyfikator klienta–broker jest zwykłym
  stanem AMC Public, a nie błędem uruchomienia.
- Bez konfiguracji host nie dostaje argumentów Google. Wspólny model możliwości
  nie pokazuje wtedy konta YouTube w menu, palecie poleceń ani pomocy.
- Publiczne wyszukiwanie, ręcznie dodane kanały i odświeżanie YouTube, które nie
  wymagają konta, pozostają niezależne od tej decyzji.
- Późniejsze włączenie wymaga nowej, świadomie wybranej domeny, produkcyjnego
  projektu Google, wdrożonego brokera oraz pełnego odbioru. Nie wymaga ponownego
  projektowania protokołu ani umieszczania sekretu w aplikacji.

### Materiał do dokumentacji użytkownika

- AMC Public może być używane bez logowania Google. W takim wydaniu pozycja
  konta YouTube nie jest wyświetlana i nie prowadzi do niedziałającego okna.
- Kanały oraz materiały YouTube dostępne publicznie nadal działają bez konta.
- Synchronizacja prywatnej listy subskrypcji i playlist konta pojawi się
  dopiero w wydaniu, które ma kompletną, zweryfikowaną konfigurację Google.

### Testy i wynik

- Celowany zestaw konfiguracji konta i paczki Public: 9 z 9 testów zaliczonych.
  Obejmuje brak identyfikatora, sekretu i brokera, brak argumentów OAuth hosta,
  brak polecenia konta w menu i palecie oraz brak wszystkich czterech zasobów
  Google w nieskonfigurowanej paczce Public.
- Statyczny kontrakt dokumentów Google/YouTube: 4 z 4 testów zaliczone.
- Testy były bezokienne. Nie uruchamiały AMC, przeglądarki ani logowania.

### Znane ograniczenia

- Moduł nie jest wdrożony i nie ma produkcyjnej domeny, klienta Google ani
  działającego endpointu brokera.
- Bez tych elementów nie można wykonać rzeczywistego logowania AMC Public.
- Zgoda na politykę, stałe publiczne adresy dokumentów i odbiór NVDA pozostają
  pracą wymaganą dopiero przed faktycznym włączeniem modułu.

### Wersja i commit

- Źródła i dokumentacja: zmienione w kopii roboczej; commit nieutworzony.
- Build, pakiet, instalacja, wdrożenie i publikacja: niewykonane w tym etapie.
