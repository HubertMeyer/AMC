# YT-001 — konto YouTube i synchronizacja

- Status: `W trakcie — odbiór instalacji 16:30 potwierdził, że Google przekazuje zgodę, lecz utworzony klient desktopowy wymaga także client_secret przy wymianie kodu. Poprawka źródłowa 3e57b686 jest przetestowana; nowa paczka czeka na lokalne zapisanie sekretu tego samego klienta OAuth, potem na instalację i prawdziwy odbiór NVDA`. Zapis bieżącej, jeszcze niepoprawionej instalacji: [AMC-TEST-2026-10-23-1630-spotify-output-youtube-oauth.md](AMC-TEST-2026-10-23-1630-spotify-output-youtube-oauth.md). Bieżąca diagnoza: [AMC-TEST-2026-10-23-youtube-secret-frontier-choice.md](AMC-TEST-2026-10-23-youtube-secret-frontier-choice.md).
- Utworzono: 18 października 2026
- Ostatnia aktualizacja: 23 października 2026
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
- Pierwsze uruchomienie testów w zainstalowanym runtime nie było testem kodu:
  ten runtime celowo nie zawiera `pytest`. Test powtórzono w istniejącym
  środowisku testowym projektu, bez instalowania zależności globalnych.

### Znane ograniczenia

To jest na razie zmiana źródłowa z zaliczonymi testami ukierunkowanymi. Nie
zbudowano jeszcze pakietu, nie zainstalowano poprawionej wersji i nie wykonano
ponownego prawdziwego OAuth ani podglądu subskrypcji.

### Wersja i commit

Wersja i commit zostaną wpisane po zbudowaniu, instalacji i weryfikacji
konkretnego kandydata AMC Test. AMC Public i GitHub pozostają bez zmian.
