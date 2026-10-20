# YT-001 — konto YouTube i synchronizacja

- Status: `W trakcie — bezpieczny fundament OAuth gotowy, brak jeszcze klienta Google i interfejsu`
- Utworzono: 18 października 2026
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
  losowym porcie `127.0.0.1`. Nie używamy osadzonej przeglądarki, wycofanego
  przepisywania kodu OOB ani sekretu klienta w instalatorze. Oficjalne źródła:
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
  `src/AccessibleMediaController.Windows/Services/YouTubeCredentialStore.cs`,
  powiązanie magazynu z LiteHostem oraz testy Core i Windows.
- Testy: `dotnet run --project
  tests/AccessibleMediaController.Core.SmokeTests/AccessibleMediaController.Core.SmokeTests.csproj
  --no-restore -- --youtube-oauth-foundation` — zaliczone 10 z 10 scenariuszy.
  Test granicy poświadczeń Windows `--youtube-credential-boundary` — zaliczone
  6 z 6 sprawdzeń. Test `--youtube-account-coordinator` — zaliczone 5 z 5
  scenariuszy cyklu konta. Test `--youtube-subscriptions` — zaliczone 5 z 5
  scenariuszy odczytu, stronicowania i błędów API. Test
  `--youtube-subscription-sync-plan` — zaliczone 5 z 5 scenariuszy polityki
  jednokierunkowej. Projekty Windows i LiteHost zbudowane bez ostrzeżeń i błędów.
- Commity źródła i testów: `ce723bff` (`feat(youtube): add safe OAuth protocol foundation`)
  `0c15fbcb` (`feat(youtube): isolate token exchange and credentials`) oraz
  `cbd2a5d3` (`feat(youtube): add guarded loopback callback`) i `161cb856`
  (`feat(youtube): coordinate account lifecycle safely`) oraz `86309bb0`
  (`feat(youtube): read account subscriptions safely`) i `436c5e3d`
  (`feat(youtube): plan one-way subscription sync`).
- Zainstalowana kompilacja: brak. Ten etap nie zmienia jeszcze interfejsu ani
  bieżącej instalacji AMC Test.

## Materiał do dokumentacji użytkownika

Logowanie do YouTube nie jest jeszcze widoczne w AMC. Przygotowany mechanizm
ma docelowo otworzyć oficjalną stronę Google w zwykłej przeglądarce i wrócić
do AMC przez lokalny adres na komputerze. AMC nie poprosi o hasło Google i nie
wyświetli pola na sekret aplikacji. Pierwsza wersja poprosi wyłącznie o odczyt
subskrypcji i playlist; zwykłe wyszukiwanie oraz pobieranie pozostaną dostępne
bez konta.

## Uzasadnienie i decyzje

- Samo uruchomienie AMC nadal nie otwiera przeglądarki, nie uruchamia odbiornika
  i nie łączy się z Google. Odbiornik powstanie dopiero po przyszłym, jawnym
  poleceniu logowania użytkownika.
- Weryfikator PKCE nie trafia do adresu przeglądarki. Adres zawiera tylko jego
  skrót S256 i losowy stan chroniący powrót do właściwej próby logowania.
- Akceptowany jest wyłącznie `http://127.0.0.1` z jawnie przydzielonym portem.
  `localhost`, zdalny host, HTTPS udające lokalny odbiornik i port domyślny są
  odrzucane przed rozpoczęciem logowania.
- Nie tworzymy jeszcze polecenia w menu, pomocy ani palecie. Bez identyfikatora
  klienta Google byłoby to martwe polecenie sprzeczne ze wspólnym katalogiem
  możliwości AMC.
- Wymiana kodu i odświeżenie korzystają wyłącznie z oficjalnego punktu tokenów
  Google. Nie wysyłają `client_secret`, a odświeżenie nie prosi po cichu o
  szerszy zakres.
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

## Znane ograniczenia

- Brak jeszcze przydzielonego identyfikatora aplikacji Google dla AMC.
- Nie ma jeszcze warstwy wykonującej zatwierdzony plan w Bibliotece AMC ani
  interfejsu wx. Koordynator, lokalny odbiornik, transport tokenów, odczyt API,
  plan synchronizacji i chroniony, profilowo rozdzielony magazyn są gotowe,
  ale nie są jeszcze połączone z widocznym poleceniem ani z identyfikatorem
  aplikacji Google.
- Przed dodaniem widocznego polecenia trzeba połączyć magazyn z profilem hosta
  i dodać testy parytetu Ctrl+F1, Ctrl+Shift+K i menu.
- Profil publiczny wymaga osobnej decyzji po konfiguracji i weryfikacji Google.

## Wersja i commit

Kod źródłowy i testy są zapisane w lokalnych commitach `ce723bff`, `0c15fbcb`,
`cbd2a5d3`, `161cb856`, `86309bb0` oraz `436c5e3d`, po zainstalowanej kompilacji
`2026.10.21-a947f79d...`. Projekty
źródłowe zostały pomyślnie zbudowane, ale nie powstał nowy pakiet, instalacja
ani publikacja.
