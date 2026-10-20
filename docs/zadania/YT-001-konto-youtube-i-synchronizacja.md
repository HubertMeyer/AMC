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
  `tests/AccessibleMediaController.Core.SmokeTests/YouTubeOAuthFoundationTests.cs`
  oraz rejestr testów w `Program.cs`.
- Testy: `dotnet run --project
  tests/AccessibleMediaController.Core.SmokeTests/AccessibleMediaController.Core.SmokeTests.csproj
  --no-restore -- --youtube-oauth-foundation` — zaliczone 5 z 5 scenariuszy.
- Commit źródła i testów: `ce723bff` (`feat(youtube): add safe OAuth protocol foundation`).
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

- Kod przygotowawczy nie uruchamia przeglądarki, serwera lokalnego ani sieci.
  Dzięki temu można przetestować zasady bezpieczeństwa bez dotykania konta.
- Weryfikator PKCE nie trafia do adresu przeglądarki. Adres zawiera tylko jego
  skrót S256 i losowy stan chroniący powrót do właściwej próby logowania.
- Akceptowany jest wyłącznie `http://127.0.0.1` z jawnie przydzielonym portem.
  `localhost`, zdalny host, HTTPS udające lokalny odbiornik i port domyślny są
  odrzucane przed rozpoczęciem logowania.
- Nie tworzymy jeszcze polecenia w menu, pomocy ani palecie. Bez identyfikatora
  klienta Google byłoby to martwe polecenie sprzeczne ze wspólnym katalogiem
  możliwości AMC.

## Testy i wynik

Zaliczono pięć syntetycznych scenariuszy: żądanie tylko do odczytu z PKCE S256,
odrzucanie niebezpiecznych adresów powrotu, wymianę kodu i odświeżenie bez
sekretu klienta, zachowanie refresh tokenu i zakresu oraz brak treści wadliwej
odpowiedzi Google w wyjątku. Test nie używał sieci, prawdziwego klienta Google,
przeglądarki ani danych użytkownika.

## Znane ograniczenia

- Brak jeszcze przydzielonego identyfikatora aplikacji Google dla AMC.
- Nie ma jeszcze odbiornika lokalnego, transportu HTTP, chronionego magazynu
  tokenów, koordynatora konta, synchronizacji subskrypcji ani interfejsu wx.
- Przed dodaniem widocznego polecenia trzeba zapewnić osobne poświadczenia dla
  profili AMC Test i AMC oraz testy parytetu Ctrl+F1, Ctrl+Shift+K i menu.
- Profil publiczny wymaga osobnej decyzji po konfiguracji i weryfikacji Google.

## Wersja i commit

Kod źródłowy i testy są zapisane w lokalnym commicie `ce723bff`, po
zainstalowanej kompilacji `2026.10.21-a947f79d...`. Nie zostały jeszcze
zbudowane do instalacji, zainstalowane ani opublikowane.
