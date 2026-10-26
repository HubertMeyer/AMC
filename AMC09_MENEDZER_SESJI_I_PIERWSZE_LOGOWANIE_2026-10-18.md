# AMC09 — Menedżer sesji i pierwsze uruchomienie usług

Data przygotowania zakresu: 18 października 2026 r.

Status: audyt źródłowy wykonany. Zatwierdzono zwartą numerację aktywnych sesji, stałą nazwę użytkową `Radio` oraz rozdział profilu publicznego `AMC` od prywatnego profilu `AMC Test`. WiiM należy do wydania publicznego. Sonos jest celem publicznym po zamknięciu bramy brokera i testu zewnętrznego. Spotify i TIDAL pozostają całkowicie ukryte w wydaniu publicznym; Spotify może zostać kiedyś ponownie ocenione po AMC16, natomiast bieżąca decyzja dla TIDAL-u to profil testowy. Pozostałe decyzje są propozycją poziomu A do późniejszego zatwierdzenia. Nie zmieniono kodu produkcyjnego, ustawień ani danych kont; nie kompilowano i nie uruchamiano AMC.

## Cel

Nowy użytkownik ma od pierwszego uruchomienia widzieć wyłącznie użyteczne, prawdziwie dostępne sesje. Menedżer sesji ma rozróżniać:

1. czy integracja jest dostępna w danym wydaniu AMC;
2. czy użytkownik chce mieć ją włączoną w przełączaniu sesji;
3. czy konto albo urządzenie jest już skonfigurowane i gotowe.

Samo pojawienie się nazwy Spotify, TIDAL, Sonos albo WiiM nie może sugerować, że usługa jest zalogowana albo że pełne odtwarzanie działa. Wyłączenie sesji nie usuwa konta, danych ani ustawień i nie wysyła polecenia zatrzymania do urządzenia.

## Wynik audytu źródłowego

1. `SessionManager.CreateDemoSessions` zawsze tworzy TIDAL, Apple Music, WiiM, Spotify i Sonos. TIDAL, Apple Music i Spotify otrzymują demonstracyjne pozycje nawet wtedy, gdy konto nie jest skonfigurowane.
2. Pliki lokalne, Radio oraz Podcasty i YouTube są dołączane inną drogą jako sesje przejściowe. Przyszłe filtrowanie musi więc działać zarówno podczas startu, jak i przy późniejszym `AddOrUpdateTransientSession`.
3. `SessionSlotOrder.Normalize` uzupełnia wszystkie znane sesje. Nie istnieje osobny zapis `dostępna`, `włączona` ani `skonfigurowana`.
4. `SessionSelectionWindow` jest dziś oknem wyboru i zmiany kolejności. Pokazuje tylko numer oraz nazwę, nie pokazuje gotowości, nie włącza i nie wyłącza sesji ani nie prowadzi do konfiguracji.
5. Ustawienia zawierają drugą listę kolejności sesji. Dwie powierzchnie mogą z czasem rozjechać się znaczeniowo, jeśli jedna stanie się Menedżerem, a druga pozostanie wyłącznie listą kolejności.
6. Nowy profil ma `LastSessionId = tidal`. Świeża instalacja może więc zaczynać od demonstracyjnego TIDAL-u zamiast od lokalnej, zawsze dostępnej części programu.
7. Okna Spotify i TIDAL zaczynają od pól `Identyfikator aplikacji`, `Adres powrotu` i `Kraj katalogu`. Jest to procedura deweloperska, nie sensowna domyślna droga dla odbiorcy publicznego instalatora.
8. Dołączona instrukcja TIDAL wprost stwierdza, że w publicznym wydaniu użytkownik nie powinien tworzyć własnej aplikacji deweloperskiej.
9. Spotify ma dwa niezależne stany: OAuth katalogu i biblioteki oraz parowanie odtwarzacza Librespot. Obecny interfejs rozdziela je na dwa okna, ale nowemu użytkownikowi nie przedstawia jednego podsumowania gotowości.
10. Zalogowanie Spotify nie gwarantuje odtwarzania bez Premium i przy braku zakresu odtwarzania. Zalogowanie oraz synchronizacja TIDAL nie gwarantują pełnych utworów; obecny projekt potwierdził próbki, a nie pełne odtwarzanie.
11. Tokeny Spotify i TIDAL są już przechowywane w Menedżerze poświadczeń Windows, poza plikiem ustawień i kopiami zapasowymi. Ten kontrakt należy zachować.
12. Obecny model zachowuje historyczne numery i luki. Docelowo ma go zastąpić zatwierdzona przez użytkownika zwarta lista aktywnych sesji: numer wynika z aktualnej pozycji, a nie z trwale zarezerwowanego slotu.
13. Użytkowa nazwa sesji jest obecnie niespójnie zapisana jako `Radio internetowe`. Docelowa, stała nazwa brzmi `Radio`; wewnętrzny identyfikator `radio` i dane stacji pozostają bez zmian.

## Proponowany model sesji

Każda znana sesja ma trzy odrębne właściwości:

- `Dostępność wydania`: dostępna albo niedostępna w tym pakiecie AMC;
- `Włączenie użytkownika`: obecna albo nieobecna w zwykłym przełączaniu sesji;
- `Gotowość`: gotowa, wymaga konfiguracji, wymaga zalogowania, urządzenie niedostępne albo funkcja ograniczona.

Wartości wewnętrzne pozostają w modelu. Dostępna nazwa wiersza ma być użytkowa, na przykład:

- `Ctrl+1, Pliki lokalne, włączona, gotowa`;
- `WiiM, wyłączona, wymaga wybrania urządzenia`;
- `Sonos, niedostępna w tym wydaniu`;
- w `AMC Test`: `TIDAL, włączona, konto połączone, pełne odtwarzanie niepotwierdzone`.

NVDA nie może usłyszeć nazw klas, identyfikatorów sesji, wartości enuma, nazw zakresów OAuth ani technicznego powodu z manifestu wydania.

## Proponowany podział wydań

### Publiczny instalator

- domyślnie włączone: `Pliki lokalne`, `Radio`, `Podcasty i YouTube`;
- dostępne do świadomego włączenia: `WiiM`; jest to zatwierdzony składnik wydania publicznego, początkowo wyłączony i bez automatycznego skanowania sieci przy starcie;
- `Sonos` jest planowany do wydania publicznego, ale pojawia się w konkretnym pakiecie dopiero po zastąpieniu prywatnego brokera publicznym, stabilnym brokerem HTTPS i przejściu testu na koncie spoza środowiska autora;
- Spotify: całkowicie nieobecne w tym profilu, dopóki AMC16 nie potwierdzi stabilnego logowania i działania, a użytkownik nie zatwierdzi osobno jego publikacji; nie pokazujemy go jako sesji, pozycji `Niedostępne`, polecenia, ustawienia ani tematu pomocy;
- TIDAL: całkowicie nieobecny w tym profilu; nie pokazujemy sesji, pozycji `Niedostępne`, poleceń, ustawień ani tematów pomocy;
- Apple Music: niedostępne, dopóki nie istnieje prawdziwy adapter; nie pokazujemy demonstracyjnej sesji jako funkcji produktu;
- brak demonstracyjnych utworów udających zawartość kont zewnętrznych.

### Prywatne wydanie testowe użytkownika

- użytkowa nazwa wydania brzmi `Accessible Multimedia Controller — Test`, krótko `AMC Test`; nie używamy nazwy `AMC Python`, ponieważ technologia wykonania nie jest nazwą produktu i nie może wracać do komunikatów NVDA;
- może udostępniać Spotify, TIDAL i inne funkcje eksperymentalne wraz z istniejącymi ustawieniami oraz poświadczeniami;
- brak pola dostępności w starym pliku konfiguracji nie może wyłączyć dotychczasowych sesji; migracja zachowuje ich wzajemną kolejność i układa aktywną listę kolejno od `Ctrl+1`;
- profil wydania nie może zależeć od nazwy użytkownika Windows, lokalnej ścieżki ani obecności tokenu;
- identyfikatory aplikacji dostawców i poświadczenia użytkownika nie trafiają do publicznego repozytorium, dziennika ani kopii zapasowej.

To są dwa profile możliwości tego samego kodu, a nie dwie rozchodzące się aplikacje. Szczegóły tożsamości instalacji, aktualizacji i danych zapisano w `AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`. Pomoc i paleta pokazują tylko polecenia naprawdę dostępne w uruchomionym wydaniu.

## Menedżer sesji

Dotychczasowe `Ctrl+Shift+S` pozostaje drogą do okna, ale nazwa zmienia się z `Wybór sesji` na `Menedżer sesji`.

### Lista

- każdy wiersz zawiera skrót, nazwę, stan włączenia i krótki stan gotowości;
- Enter przełącza do zaznaczonej, włączonej sesji;
- Spacja włącza lub wyłącza sesję, jeżeli wydanie ją udostępnia;
- `Alt+strzałka w górę/w dół` zachowuje zmianę kolejności i numerów tylko na świadome polecenie użytkownika;
- przycisk `Konfiguruj…` prowadzi do właściwego konta albo urządzenia;
- przyciski i menu są dostępne także bez pamiętania skrótów;
- po każdej czynności fokus wraca na ten sam wiersz rozpoznany po stabilnym identyfikatorze, nie po pozycji.
- część `Aktywne sesje` jest zwarta i liczy najwyżej dziewięć pozycji; część `Dostępne do dodania` nie ma numerów `Ctrl+1–9`;
- kolejność początkowa świeżego profilu to `Ctrl+1 Pliki lokalne`, `Ctrl+2 Radio`, `Ctrl+3 Podcasty i YouTube`.

### Zasady włączania i wyłączania

- sesji niedostępnej w danym wydaniu nie można włączyć; wiersz wyjaśnia powód użytkowo;
- wyłączenie usuwa sesję z aktywnej listy, `Ctrl+Page Up/Down`, bezpośredniego wyboru i bieżących menu kontekstowych, ale zachowuje jej dane, konto, kolejkę i historię;
- po usunięciu późniejsze aktywne sesje przesuwają się o jedno miejsce. Przykład: po usunięciu `Ctrl+3 Podcasty i YouTube`, dotychczasowy `Ctrl+4 Sonos` staje się `Ctrl+3 Sonos`;
- ponowne włączenie zachowuje dane, lecz traktowane jest jak ponowne dodanie: sesja trafia na koniec aktywnej listy i otrzymuje pierwszy kolejny numer;
- wyłączenie nie wylogowuje konta, nie usuwa urządzenia i nie zatrzymuje Sonosa ani WiiM;
- jeżeli wyłączana sesja jest bieżąca i niczego wewnętrznie nie odtwarza ani nie nagrywa, AMC przełącza się na sesję, która po zagęszczeniu zajęła tę samą pozycję, a gdy takiej nie ma — na poprzednią; końcowy komunikat podaje nową aktywną sesję i jej numer;
- sesji z aktywnym wewnętrznym odtwarzaniem albo nagrywaniem nie można wyłączyć do czasu bezpiecznego zakończenia tej czynności;
- wyłączenie bieżącego Sonosa albo WiiM może zmienić sesję interfejsu, ale nie wysyła polecenia zatrzymania do autonomicznego urządzenia;
- każdą podstawową sesję, także `Podcasty i YouTube`, można usunąć z aktywnej listy. Menedżer nie pozwala jedynie usunąć ostatniej aktywnej sesji;
- próba włączenia dziesiątej sesji prosi o wcześniejsze usunięcie albo wyłączenie jednej z dziewięciu aktywnych sesji.

### Skróty i migracja

- `Ctrl+1–9` zawsze odpowiada bieżącej pozycji na zwartej liście aktywnych sesji, a `Ctrl+Page Up/Down` przechodzi po tej samej kolejności;
- dodanie sesji umieszcza ją na końcu; usunięcie zagęszcza numery; `Alt+strzałka w górę/w dół` natychmiast zamienia pozycje i związane z nimi skróty;
- nie istnieje zarezerwowany numer sesji wyłączonej. Skrót o numerze większym niż liczba aktywnych sesji mówi `Brak sesji pod Ctrl+N` i niczego nie uruchamia;
- migracja starego profilu zachowuje wszystkie dotychczasowe sesje jako włączone oraz zachowuje ich wzajemną kolejność, po czym usuwa luki i przypisuje `Ctrl+1` do `Ctrl+N`;
- świeży profil otrzymuje nowe bezpieczne wartości domyślne oraz `LastSessionId = local`;
- rozpoznanie profilu świeżego i istniejącego ma wynikać z wersji schematu lub jawnego znacznika inicjalizacji, nie z pustej biblioteki.

### Stała nazwa `Radio`

- użytkowa nazwa sesji zostaje skrócona z `Radio internetowe` do `Radio` we wszystkich nowych i istniejących profilach;
- zmiana obejmuje Menedżer, menu, paletę, `Ctrl+F1`, komunikaty, tytuły widoków, ustawienia oraz dokumentację użytkownika;
- nie zmienia się identyfikator `radio`, struktura Biblioteki, stacje, presety, harmonogramy ani skróty;
- tekst opisowy może nadal mówić `radio internetowe`, gdy chodzi o rodzaj medium, lecz nazwa własna sesji brzmi zawsze `Radio`;
- test statyczny wyszukuje pozostałe użytkowe etykiety `Radio internetowe`, aby skrócenie nie było częściowe.

## Pierwsze uruchomienie

Proponowany przebieg dla nowej instalacji:

1. AMC otwiera raz `Menedżer sesji` z krótkim komunikatem, że podstawowe sesje są już gotowe, a urządzenia można włączyć później.
2. Początkowy fokus trafia na `Pliki lokalne`, nie na opis ani techniczne pole.
3. Użytkownik może od razu nacisnąć Enter i rozpocząć pracę albo włączyć WiiM i użyć `Konfiguruj…`. Sonos pojawia się jako możliwy do włączenia dopiero w wydaniu, które ma gotowy publiczny broker i zaliczony test zewnętrznego konta.
4. Anulowanie nie pozostawia programu bez sesji: aktywna zostaje sesja lokalna.
5. Przy kolejnych uruchomieniach menedżer nie otwiera się automatycznie; pozostaje pod `Ctrl+Shift+S`, w menu i palecie.

Nie należy prowadzić nowego użytkownika przez obowiązkowy wielostronicowy kreator. Jedna lista stanów jest łatwiejsza do ponownego odnalezienia z NVDA i może służyć również później.

## Ocena usług dla nowego użytkownika i publicznego instalatora

Stan oceny: 18 października 2026 r. Kolejność oznacza gotowość do prostego, zgodnego z zasadami wdrożenia publicznego, a nie liczbę funkcji już obecnych w kodzie AMC.

### 1. WiiM — nadaje się jako pierwsza integracja publiczna

- nowy użytkownik musi mieć urządzenie skonfigurowane w WiiM Home i komputer w tej samej sieci lokalnej;
- AMC może potem wykryć urządzenie przez UPnP/SSDP albo przyjąć jego lokalny adres; użytkownik nie tworzy konta deweloperskiego i nie wpisuje Client ID;
- oficjalna strona WiiM udostępnia HTTP API oraz UPnP API do sterowania urządzeniami;
- największe ryzyka instalatora to zapora Windows, izolacja klientów Wi-Fi, VPN i brak multicastu, a nie zgoda dostawcy konta;
- dlatego WiiM może być dostępne w publicznym instalatorze jako opcjonalna, początkowo wyłączona sesja.

### 2. Sonos — prosty dla użytkownika, ale wymaga publicznego brokera AMC

- docelowy przebieg jest dobry: użytkownik naciska `Zaloguj`, loguje się zwykłym kontem Sonos w przeglądarce, a potem wybiera dom i grupę; nie wpisuje żadnych danych deweloperskich;
- oficjalny Control API wymaga integracji, poświadczeń klienta i wymiany kodu z użyciem sekretu po stronie serwera. Sekret nie może być osadzony w aplikacji desktopowej;
- obecny kod poprawnie używa brokera, lecz jego `DefaultBrokerOrigin` wskazuje prywatny adres `hermes.tail6caad7.ts.net`. Nie można na nim oprzeć instalatora dla zewnętrznych użytkowników;
- przed wydaniem potrzebny jest publicznie osiągalny broker HTTPS, bezpieczne przechowywanie sekretu, polityka prywatności, monitoring, kopia konfiguracji i plan awarii;
- Sonos pozwala wydać integrację Control API po rejestracji i zaakceptowaniu wymaganych umów, bez używania oznaczenia `Works with Sonos`;
- po zamknięciu bramy brokera Sonos będzie drugą najprostszą usługą dla użytkownika.

### 3. Spotify — Librespot pozostaje wyłącznie w profilu testowym do zakończenia weryfikacji

- katalog, biblioteka i playlisty AMC korzystają z Web API. W trybie deweloperskim aplikacja ma najwyżej pięciu wskazanych użytkowników, a właściciel aplikacji musi mieć Premium; to nie jest model publicznego instalatora;
- tryb rozszerzony usuwa listę pięciu użytkowników, lecz obecne kryteria przyjmują zgłoszenia organizacji i wymagają między innymi działającej usługi oraz co najmniej 250 tysięcy aktywnych użytkowników miesięcznie;
- obecny Librespot jest łatwy do sparowania i działa z legalnym kontem Premium. Użytkownik dostaje jednorazowy kod oraz adres `spotify.com/pair`, zatwierdza dostęp na stronie Spotify, a AMC zapisuje token w Menedżerze poświadczeń Windows; hasło nie przechodzi przez AMC;
- ta łatwa droga działa już dla odtwarzania, ale katalog, biblioteka i playlisty korzystają dziś z osobnego OAuth Web API, wymagającego własnego Client ID. To właśnie drugie logowanie jest główną przeszkodą dla nowego użytkownika;
- używany obecnie przepływ urządzenia korzysta z identyfikatora klienta Spotify dla aplikacji desktopowej, tak samo jak przykładowa implementacja upstream Librespot. Jest to mechanizm technicznie skuteczny, lecz niedokumentowany jako publiczna droga dla obcej aplikacji. Zwykłe, opłacone konto użytkownika nie usuwa ryzyka związanego z tożsamością klienta, regulaminem ani możliwością zablokowania mechanizmu przez Spotify;
- alternatywą do sprawdzenia jest parowanie Spotify Connect przez wykrywanie lokalne: użytkownik uruchamia oficjalną aplikację Spotify na telefonie lub komputerze i wybiera `AMC` na liście urządzeń. Librespot obsługuje taki model Zeroconf bez wpisywania hasła, ale bieżący natywny host AMC został świadomie zbudowany bez discovery/Spirc i wymaga osobnego rozszerzenia;
- publiczne repozytoria Elten 2 i Elten 3 nie zawierają kodu `spotify` ani `librespot`. Istnienie wygodnego programu Spotify w Eltenie jest użytecznym dowodem produktowym, lecz na podstawie dostępnych źródeł nie wolno przypisać mu konkretnego sposobu logowania ani kopiować implementacji;
- oficjalny Spotify Soloist jest obiecującą przyszłą drogą odtwarzania i lokalnego sterowania, ale obecnie Spotify publikuje tylko wersje linuksowe. Każdy użytkownik musi wygenerować własny prywatny klucz API, a binariów Soloist nie wolno redystrybuować w instalatorze AMC;
- zatwierdzony kierunek: nie usuwamy Librespota z kodu ani profilu `AMC Test`. Przygotowujemy osobny eksperyment jednego logowania, lecz pierwszy publiczny instalator w ogóle nie zawiera widocznego Spotify. Nawet pomyślny test techniczny nie publikuje go automatycznie: potrzebna będzie osobna decyzja użytkownika. Nie obchodzimy opłat, reklam, ograniczeń konta Free, zabezpieczeń geograficznych ani ochrony przed kopiowaniem.

### 4. TIDAL — pozostaje wyłącznie w `AMC Test`

- obecna droga wymaga własnej aplikacji deweloperskiej oraz Client ID, a dokumentacja TIDAL rozróżnia tryb produkcyjny wymagający zatwierdzenia;
- oficjalna platforma umożliwia autoryzację i katalog, ale zasady odtwarzania są węższe; bieżący AMC potwierdził próbki, nie pełne utwory;
- API katalogu, biblioteki i synchronizacji jest użyteczne dla właściciela i może być nadal rozwijane w `AMC Test`, lecz nie równoważy przewidywalnego, prostego odtwarzania dla użytkownika publicznego;
- samo udane logowanie albo synchronizacja nie daje podstawy, by reklamować pełny odtwarzacz TIDAL;
- TIDAL pozostaje prywatną funkcją `AMC Test`. Nie planujemy go w pierwszym publicznym profilu, nawet jeżeli część biblioteczna działa dobrze na koncie właściciela.

### Wniosek wydawniczy

Pierwszy publiczny instalator ma oferować WiiM. Sonos jest również celem publicznym, lecz może dołączyć dopiero po uruchomieniu publicznego brokera AMC i teście z zewnętrznym kontem; jeżeli nie zamknie tej bramy, pozostaje ukryty w danym wydaniu. Spotify i TIDAL pozostają zachowane w kodzie oraz `AMC Test`, ale w publicznym `AMC` są całkowicie ukryte. Spotify może wrócić do oceny po AMC16 i osobnej decyzji wydawniczej. TIDAL w obecnym planie pozostaje funkcją prywatną, mimo użytecznego API biblioteki.

Źródła oficjalne i pierwotne:

- https://www.wiimhome.com/support
- https://docs.sonos.com/docs/connected-home-get-started
- https://docs.sonos.com/docs/authorize
- https://developer.spotify.com/documentation/web-api/concepts/quota-modes
- https://developer.spotify.com/terms
- https://developer.spotify.com/documentation/soloist/tutorials/getting-started
- https://github.com/librespot-org/librespot
- https://github.com/librespot-org/librespot/blob/dev/docs/device-authorization.md
- https://github.com/librespot-org/librespot/blob/dev/docs/authentication.md
- https://github.com/dawidpieper/elten3
- https://elten.link/pl/forum/thread/28097
- https://developer.tidal.com/documentation/guidelines/guidelines-developer-terms
- https://developer.tidal.com/documentation/guidelines/guidelines-changelog

## Spotify — propozycja jednego prostego połączenia

Jeżeli Spotify jest dostępne w danym wydaniu, `Konfiguruj…` otwiera jeden punkt wejścia `Konto Spotify`, który pokazuje oddzielnie:

- `Biblioteka i playlisty`: niepołączone, połączone albo wymagające ponownej zgody;
- `Odtwarzanie w AMC`: niesparowane, sparowane, niedostępne bez Premium albo niedostępne w tym wydaniu;
- `Ostatnia synchronizacja`: data użytkowa albo `jeszcze nie wykonywano`.

Docelowy przebieg dla zwykłego użytkownika:

1. Jedno polecenie `Połącz Spotify…` pokazuje dwie użytkowe możliwości, jeżeli obie przejdą próbę techniczną: `Połącz kodem na stronie Spotify` oraz `Połącz przez aplikację Spotify na tym samym Wi-Fi`.
2. Pierwsza możliwość wykorzystuje istniejący kod urządzenia i `spotify.com/pair`. Druga uruchamia na ograniczony czas wykrywalne urządzenie `AMC` i prosi o wybranie go w oficjalnej aplikacji Spotify.
3. Zwykły użytkownik nigdy nie widzi pól Client ID, Redirect URI, nazw zakresów ani tokenów. Ustawienia deweloperskie pozostają w osobnej, wyraźnie oznaczonej sekcji i nigdy nie żądają Client Secret.
4. Po zgodzie AMC sprawdza konto Premium i gotowość odtwarzania, a następnie ustala, czy ten sam zatwierdzony stan może legalnie i technicznie obsłużyć katalog, bibliotekę oraz playlisty. Tego nie uznajemy za potwierdzone bez próby integracyjnej.
5. Jeżeli pojedyncze logowanie nie daje katalogu i playlist, AMC nie uruchamia po cichu drugiego procesu. W `AMC Test` podaje jeden komunikat oraz pozostawia niedziałające funkcje wyłączone. Publiczne `AMC` nadal nie pokazuje Spotify.
6. Ponowne uprawnienia playlist z AMC08 są przedstawione użytkowo jako możliwość zarządzania prywatnymi i publicznymi playlistami.
7. Sukces odtwarzania nie jest komunikowany jako sukces biblioteki. Okno kończy się jednoznacznym podsumowaniem faktycznie sprawdzonych możliwości.

### Osobny eksperyment Spotify przed decyzją wydawniczą

1. Na świeżym koncie Premium sprawdzić istniejące parowanie kodem, ponowne uruchomienie AMC, odświeżenie tokenu i odłączenie konta.
2. W odizolowanej gałęzi prototypowej dodać discovery Librespot i sprawdzić parowanie przez listę urządzeń oficjalnej aplikacji Spotify. Nie łączyć prototypu z wydaniem przed oceną zapory, wielu kart sieciowych, bezpieczeństwa lokalnego serwera i zachowania po zamknięciu okna.
3. Sprawdzić bez założeń, jakie dane uwierzytelniające uzyskuje każda droga i czy mogą zasilać istniejący katalog, bibliotekę oraz funkcje playlist. Nie poszerzać zakresów ani nie podstawiać cudzej tożsamości klienta tylko po to, żeby ominąć limit Web API.
4. Porównać zachowanie z programem Spotify w Eltenie na poziomie widocznym dla użytkownika: liczba kroków, komunikaty, powrót fokusa, ponowne uruchomienie i odłączenie. Poza zakresem pozostają instalowanie, debugowanie i kopiowanie programu Eltena.
5. Kryterium sukcesu: nowy użytkownik podaje wyłącznie zgodę na swoim prawdziwym koncie Premium, nie tworzy aplikacji deweloperskiej, nie wpisuje hasła w AMC i po jednym procesie otrzymuje jasno wymienione działające funkcje.
6. Kryterium wycofania: mechanizm wymaga obchodzenia płatności, reklam, blokad geograficznych, ochrony treści albo podszywania się pod klienta w sposób, którego nie chcemy świadomie rozpowszechniać.

Szczegółowy zakres eksperymentu zapisano jako `AMC16_SPOTIFY_JEDNO_LOGOWANIE_LIBRESPOT_2026-10-18.md`.

## TIDAL — propozycja pierwszego połączenia

Jeżeli TIDAL jest dostępny w `AMC Test`:

1. jedno okno podaje osobno stan konta, synchronizacji oraz pełnego odtwarzania;
2. zwykła ścieżka nie zaczyna się od Client ID i Redirect URI; pola deweloperskie są w osobnej sekcji;
3. naciśnięcie `Połącz konto TIDAL…` jest świadomą zgodą na uruchomienie logowania w zwykłej przeglądarce;
4. po zalogowaniu synchronizacja może rozpocząć się automatycznie, ale okna nie można zamknąć w trakcie bez jasnego komunikatu;
5. udana synchronizacja nie mówi, że pełne utwory zagrają. Stan odtwarzania brzmi zgodnie z dowodem, na przykład `Pełne odtwarzanie niedostępne w tej konfiguracji` albo `Potwierdzono tylko próbki`;
6. publiczne wydanie nie pokazuje formularza, sesji TIDAL ani pozycji `Niedostępne`; cała droga konta pozostaje w `AMC Test`.

## Korekta z 22 października 2026 r. — ponowne otwarcie i wylogowanie

Ta zasada rozszerza ustalenie z pierwszego uruchomienia na wszystkie trwałe
integracje. Nie zmienia jeszcze układu okien; przy późniejszym uproszczeniu
można połączyć niektóre ekrany, ale dopóki nie zapadnie jawna decyzja, obowiązuje
następujący kontrakt:

- pierwsze otwarcie uruchamia właściwe dodanie, wykrywanie albo logowanie;
- po zapisaniu konta, urządzenia lub folderu ponowne `Ctrl+F5` pokazuje od razu
  zapisany stan albo listę, bez samoczynnego ponawiania logowania, parowania czy
  wykrywania;
- TIDAL, Spotify, Sonos i każda przyszła integracja konta udostępniają jawną
  akcję **Wyloguj** albo **Odłącz konto**, jeżeli logowanie jest zapisane;
- wylogowanie wymaga potwierdzenia, usuwa wyłącznie lokalne poświadczenie i
  pamięć zależną od konta opisaną dla danej usługi; nie usuwa konta ani danych
  na serwerze dostawcy;
- integracje urządzeń, które nie mają konta, używają użytkowego działania
  **Usuń urządzenie**; Foldery Biblioteki używają **Odłącz folder**. Nie
  nazywamy tych operacji wylogowaniem;
- samo wyłączenie lub usunięcie sesji z listy nie może po cichu wylogować
  konta, usunąć urządzenia ani odłączyć folderu;
- po wylogowaniu okno pozostaje w czytelnym stanie niepołączonym i pozwala
  ponownie rozpocząć logowanie. Nie otwiera przeglądarki bez jawnego polecenia.

Stan bieżącego `AMC Test`: TIDAL i Spotify mają już osobne okna konta pod
`Ctrl+F5` z przyciskiem **Odłącz konto…**; Sonos ma analogiczne wylogowanie.
Frontier Smart i WiiM zarządzają urządzeniami, a lokalna Biblioteka folderami.
Ta korekta nie wykonuje wylogowania żadnego prawdziwego konta.

## Stany i komunikaty

Wspólne stany użytkowe:

- `Gotowa`;
- `Wymaga konfiguracji`;
- `Wymaga zalogowania`;
- `Połączona, synchronizacja jeszcze niewykonana`;
- `Połączona, odtwarzanie ograniczone`;
- `Urządzenie jest teraz niedostępne`;
- `Niedostępna w tym wydaniu`.

Nie używamy w zwykłym interfejsie: `OAuth`, `PKCE`, `scope`, `token`, `ClientId`, `DeviceCode`, `enum`, kodu HTTP ani identyfikatora sesji. Szczegóły deweloperskie mogą istnieć wyłącznie w świadomie otwartym raporcie diagnostycznym po usunięciu poświadczeń.

## Pomoc, paleta i menu

- `Ctrl+F1` opisuje `Ctrl+Shift+S — Menedżer sesji`, Enter, Spację, konfigurację i zmianę kolejności;
- `Ctrl+Shift+K` zawiera `Otwórz Menedżer sesji`, `Włącz sesję…`, `Wyłącz bieżącą sesję…` oraz kontekstowe `Konfiguruj konto lub urządzenie…`;
- menu Sesje pokazuje tylko włączone sesje jako cele szybkiego przełączenia, a osobno zawsze zawiera Menedżer;
- ustawienia kolejności nie pozostają drugą, sprzeczną kopią Menedżera. Albo używają tego samego modelu, albo przycisk w Ustawieniach otwiera ten sam Menedżer;
- niedostępne usługi nie wystawiają martwych poleceń konta w menu głównym.

## Testy do przygotowania przy wdrożeniu

1. Świeży profil uruchamia się w Plikach lokalnych i nie pokazuje demonstracyjnego Spotify, TIDAL-u ani Apple Music jako gotowych usług.
2. Migracja istniejącego profilu zachowuje bieżącą sesję, włączenie, dane oraz wzajemną kolejność, a następnie przypisuje aktywnym sesjom zwarte numery od `Ctrl+1`.
3. Wyłączenie sesji przesuwa późniejsze sesje o jeden numer; ponowne włączenie dopisuje ją na końcu; ręczne przeniesienie natychmiast zmienia oba numery.
4. `Ctrl+Page Up/Down` i `Ctrl+1–9` korzystają z tej samej zwartej kolejności, bez luk i bez odwołań do sesji wyłączonych.
5. Nie można wyłączyć ostatniej aktywnej sesji ani sesji z aktywnym nagrywaniem lub wewnętrznym odtwarzaniem bez bezpiecznego zakończenia.
6. Wyłączenie Sonosa albo WiiM nie wysyła Stop, Pause, Leave Group ani żadnego innego polecenia do urządzenia.
7. Lista Menedżera ma jawne nazwy dostępności, właściwy początkowy fokus, strzałki, Spację, Enter, zmianę kolejności, Anuluj i poprawny powrót fokusa.
8. Zmiana stanu podczas wolnej odpowiedzi nie pozwala starszemu wynikowi przełączyć sesji ani ukraść fokusa.
9. Wydanie publiczne nie zawiera Spotify ani TIDAL-u w Menedżerze sesji, ustawieniach, pomocy, palecie i menu oraz nie pozwala ich przywrócić ręczną edycją zwykłego ustawienia.
10. Wydanie prywatne zachowuje istniejące logowania z Menedżera poświadczeń bez kopiowania ich do konfiguracji.
11. Spotify raportuje oddzielnie bibliotekę, playlisty, Premium i parowanie Librespot.
12. W `AMC Test` TIDAL raportuje oddzielnie konto, synchronizację i potwierdzony zakres odtwarzania.
13. Żadne okno nie otwiera przeglądarki przed jawnym naciśnięciem przycisku logowania lub otwarcia strony.
14. Zapis, Anuluj i ponowne otwarcie zachowują prawidłowe zaznaczenie oraz nie wypowiadają reprezentacji obiektu.
15. `Ctrl+F1`, paleta i menu są generowane z tej samej dostępności wydania i nie reklamują wyłączonych funkcji jako gotowych.
16. Świeży profil ma `Ctrl+1 Pliki lokalne`, `Ctrl+2 Radio`, `Ctrl+3 Podcasty i YouTube`; dodanie Sonosa daje `Ctrl+4`, a usunięcie Podcastów przesuwa Sonosa na `Ctrl+3`.
17. W żadnej użytkowej nazwie sesji, menu, palety, pomocy ani tytułu widoku nie pozostaje `Radio internetowe`; tekst opisujący medium nie jest błędnie zmieniany.
18. Menedżer nie pozwala włączyć dziesiątej aktywnej sesji i wskazuje, że najpierw trzeba usunąć jedną z dziewięciu.

## Świadomie poza zakresem AMC09

- ewentualna przyszła ponowna ocena publicznego Spotify albo TIDAL-u; nie należy do pierwszego instalatora;
- naprawa ograniczenia pełnego odtwarzania TIDAL;
- implementacja playlist Spotify z AMC08;
- sterowanie grupami i urządzeniami Sonos/WiiM, które należy do AMC10;
- instalator i wybór profilu wydania, który ostatecznie zamyka AMC12;
- usuwanie konta u dostawcy albo danych na jego serwerze;
- automatyczne przenoszenie zawartości między usługami.

## Decyzje do późniejszego zatwierdzenia

1. Czy świeża instalacja ma otworzyć Menedżer sesji jeden raz, czy od razu wejść do Plików lokalnych? Rekomendacja: otworzyć Menedżer raz, z fokusem na Plikach lokalnych.
2. Rozstrzygnięto: WiiM jest dostępne publicznie, ale początkowo wyłączone. Sonos jest celem publicznym dopiero po wdrożeniu i odbiorze brokera AMC; bez tego pozostaje ukryty.
3. Rozstrzygnięto: Spotify i TIDAL są całkowicie ukryte w publicznym `AMC` i dostępne tylko w `AMC Test`. Spotify może później otrzymać osobną ponowną decyzję po AMC16. Sposób prezentacji Apple Music pozostaje do późniejszego rozstrzygnięcia.
4. Zatwierdzone: można wyłączyć każdą podstawową sesję, w tym `Podcasty i YouTube`; musi pozostać co najmniej jedna aktywna sesja, a lista jest zawsze zwarta.
5. Czy puste demonstracyjne pozycje zachować w specjalnym trybie prezentacyjnym? Rekomendacja: tak, ale wyłącznie jako jawny tryb deweloperski, nigdy jako domyślna biblioteka usługi.

## Bramka

- Poziom A: model dostępności, włączenia i gotowości; migracja; Menedżer; pomoc i testy bez kont oraz bez sieci.
- Poziom B: kompilacja i automatyczne testy wspólnie z AMC08 i AMC10.
- Poziom C: ręczny test świeżego oraz migrowanego profilu z NVDA. Próby kont tylko w prywatnym wydaniu i tylko po osobnym potwierdzeniu.
- Poziom D: publiczny profil możliwości jest weryfikowany razem z instalatorem AMC12.

Przed kompilacją albo uruchomieniem AMC nadal trzeba potwierdzić, że nie trwa nagrywanie.
