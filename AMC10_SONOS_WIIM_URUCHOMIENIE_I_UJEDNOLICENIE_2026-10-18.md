# AMC10 — Sonos i WiiM: proste uruchomienie oraz wspólne zasady

Data przygotowania zakresu: 18 października 2026 r.

Status: audyt istniejącej implementacji i dokumentacji wykonany. Kierunek wydawniczy zatwierdzony: WiiM ma być funkcją publiczną, a Sonos ma przejść przez etap kontrolowanego pilotażu i po odbiorze stać się publiczną, opcjonalną sesją. Nie zmieniono kodu, kont ani urządzeń; nie kompilowano, nie skanowano sieci i nie wysłano żadnego polecenia odtwarzania.

## Cel

AMC nie potrzebuje kolejnego wielkiego adaptera urządzeń. Sonos i WiiM mają już rozbudowane, osobne implementacje. AMC10 ma przede wszystkim uprościć pierwsze uruchomienie, ujednolicić stany widoczne w Menedżerze sesji i zachować właściwe różnice między usługami.

Użytkownik ma móc:

- włączyć sesję urządzenia w Menedżerze;
- wybrać `Konfiguruj…` i przejść krótką, właściwą drogę;
- jednoznacznie usłyszeć, czy urządzenie jest gotowe, chwilowo niedostępne czy wymaga konta;
- wejść do sesji bez automatycznego zatrzymywania lub zmieniania muzyki;
- wrócić do konfiguracji bez szukania technicznych ustawień.

## Wynik audytu

### WiiM

- istnieje wykrywanie UPnP/SSDP oraz ręczne dodanie lokalnego adresu IP;
- można wybrać i zapamiętać aktywne urządzenie;
- działa transport, przewijanie, głośność, wyciszenie, wejścia, wyjścia, korektor, powtarzanie, losowanie, timer oraz presety;
- sesja ma lokalne Strumienie sieciowe AMC oraz bezpieczne `Otwórz w WiiM`;
- wejście do sesji i uruchomienie aplikacji mogą odświeżyć zapamiętane urządzenie;
- brak wspieranego API pełnej biblioteki WiiM Home i brak wspieranego zapisu natywnych presetów; AMC nie może udawać tych funkcji;
- multiroom ma obecnie przede wszystkim bezpieczny odczyt. Zmiany grup wymagają osobnych testów na co najmniej dwóch urządzeniach.

### Sonos

- działa oficjalne logowanie, odnawianie dostępu i bezpieczne przechowywanie poświadczeń;
- aplikacja poprawnie nie pokazuje użytkownikowi Client ID ani sekretu; wymianę wymagającą sekretu wykonuje broker AMC;
- obecny broker ma prywatny adres `hermes.tail6caad7.ts.net`, dlatego nie jest jeszcze zapleczem dla zewnętrznych użytkowników publicznego instalatora;
- działa odczyt domów, grup i głośników oraz wybór aktywnego celu;
- działa sesja odtwarzacza grupy, transport, przewijanie, głośność i wyciszenie;
- istnieją biblioteka materiału, ulubione, playlisty, presety i własne strumienie w zakresie opisanym przez bieżące testy;
- `Ctrl+F5` w sesji Sonos jest świadomie wyborem celu sterowania, a konto Sonos pozostaje w menu i palecie;
- opóźnione odpowiedzi, zmiana konta i odświeżanie mają już rozbudowane zabezpieczenia przed utratą fokusa oraz użyciem starego wyniku.

### Wniosek

Nie należy scalać protokołów ani kopiować wszystkich funkcji jednego urządzenia do drugiego. Wspólny ma być tylko kontrakt użytkowy: włączenie sesji, konfiguracja, stan gotowości, wybór celu, bezpieczne wejście i komunikaty.

WiiM ma wejść do pierwszego publicznego instalatora bez konta dostawcy jako opcjonalna, początkowo wyłączona sesja. Sonos jest również planowany publicznie, lecz może wejść dopiero po zastąpieniu prywatnego brokera trwałą publiczną usługą HTTPS i sprawdzeniu całej drogi z zewnętrznym kontem. Do tego czasu prywatna funkcja Sonosa pozostaje zachowana, ale profil publiczny jej nie udostępnia.

## Ocena nakładu Sonosa

To nie jest budowa integracji od początku. W repozytorium istnieją już między innymi:

- oficjalny przepływ konta, odnowienie tokenu i magazyn poświadczeń chroniony przez Windows;
- odczyt gospodarstw domowych, grup i głośników oraz wybór stabilnego celu;
- transport, pozycja, głośność, wyciszenie, ulubione, playlisty i własne strumienie;
- testy Core i Windows obejmujące konto, odnowienie, grupy, odtwarzacz, opóźnione odpowiedzi, fokus i dostępność;
- kontrakt brokera, dzięki któremu sekret aplikacji Sonos nie trafia do klienta AMC.

Największym brakującym elementem jest obecnie trwała usługa publicznego logowania. Kod wskazuje prywatny adres `https://hermes.tail6caad7.ts.net/`, który nie nadaje się dla użytkowników zewnętrznych. Dlatego zakres oceniamy jako średnie zadanie wydawniczo-infrastrukturalne, a nie duże zadanie odtwarzaczowe. Trudność leży głównie w bezpiecznym utrzymaniu brokera i sprawdzeniu prawdziwych kont poza środowiskiem autora.

## Droga Sonosa od prywatnej funkcji do wydania publicznego

### Etap 1 — publiczna brama logowania

1. Zarejestrować docelową integrację w portalu Sonos i przypisać jej publiczny adres przekierowania HTTPS.
2. Wystawić broker AMC pod trwałą publiczną domeną, niezależną od prywatnej sieci i komputera autora.
3. Pozostawić Client ID i sekret wyłącznie po stronie brokera. Instalator i zwykłe ustawienia AMC nie mogą ich ujawniać ani wymagać od użytkownika.
4. Zachować obecny kontrakt `login/start`, `login/result` i `login/refresh`, ale dodać kontrolę stanu, jednorazowości sesji, limitu czasu, ponownego użycia kodu i bezpiecznego odświeżania.
5. Dodać kontrolę zdrowia usługi, rotację sekretu, limitowanie ruchu i dziennik bez tokenów, kodów logowania oraz danych prywatnych.
6. Klient ma korzystać z odświeżania i zdarzeń zamiast agresywnego odpytywania, aby zachować limity Sonos.

### Etap 2 — odbiór techniczny na prawdziwym koncie

Sprawdzić pełną drogę na publicznym brokerze, najpierw na koncie autora:

- świeże połączenie, anulowanie oraz ponowienie logowania;
- zamknięcie i ponowne uruchomienie AMC bez utraty konta;
- rzeczywiste odnowienie dostępu po wygaśnięciu tokenu oraz kontrolowany test błędnego odnowienia;
- wybór domu, grupy i głośnika, również po zmianie składu grupy;
- zniknięcie urządzenia, jego powrót i brak samoczynnej zmiany celu;
- Play/Pause, następny/poprzedni, pozycja, głośność, wyciszenie, ulubione i playlisty;
- wylogowanie, ponowne logowanie oraz uczciwe komunikaty dla 401, 403, 429 i błędów usługi;
- NVDA: pierwszy fokus, strzałki, zatwierdzenie celu, powrót po przeglądarce, Zapisz, Anuluj i ponowne otwarcie.

### Etap 3 — kontrolowany pilotaż dla chętnych

Przed zwykłym udostępnieniem Sonos może działać jako `Sonos — wersja próbna` dla świadomie zgłoszonych użytkowników:

- korzysta z tego samego docelowego brokera, a nie z prywatnego adresu ani samodzielnie wpisywanych sekretów;
- włącza się go jawnie w sekcji funkcji próbnych lub przez pilotażowy manifest możliwości;
- użytkownik wykonuje zwykłe logowanie do Sonosa i wybór grupy; instrukcja nie każe tworzyć aplikacji deweloperskiej;
- AMC zbiera wyłącznie techniczny wynik i jawnie zapisany raport, bez tokenów i danych biblioteki;
- pilotaż powinien objąć co najmniej jedno konto i gospodarstwo domowe inne niż autora, a w miarę dostępności kilka modeli głośników i konfigurację wielopokojową;
- awaria Sonosa nie może utrudniać startu AMC ani pracy Plików lokalnych, Radia, nagrywania i WiiM.

To jest zalecana postać „półpubliczna”: ograniczamy liczbę użytkowników i jawnie oznaczamy etap próbny, ale nie przerzucamy na nich utrzymania brokera ani konfiguracji deweloperskiej.

### Etap 4 — sesja publiczna

Po zaliczeniu pilotażu Sonos staje się opcjonalną, początkowo wyłączoną sesją publicznego AMC. Nie wymaga osobnej instrukcji technicznej: `Menedżer sesji` → `Sonos` → `Włącz` → `Konfiguruj…` → `Połącz konto Sonos…` → wybór grupy.

Publikacja integracji sterującej nie wymaga automatycznie programu certyfikacyjnego, ale musi zachować warunki Sonos. AMC może opisywać się jako zgodne lub kompatybilne z Sonosem; nie używa oznaczenia ani znaku `Works with Sonos` bez osobnej zgody i certyfikacji.

## Kryterium otwarcia Sonosa publicznie

Sonos przechodzi z pilotażu do zwykłego wydania dopiero, gdy łącznie:

1. broker działa pod publicznym HTTPS i nie zależy od prywatnej sieci autora;
2. sekret nie występuje w pakiecie, ustawieniach, logach ani komunikatach;
3. nowe konto zewnętrzne przechodzi logowanie, wybór celu, sterowanie i ponowne uruchomienie;
4. sprawdzono odnowienie dostępu, ograniczenie ruchu oraz zachowanie przy niedostępności brokera i API;
5. NVDA nie odczytuje identyfikatorów, rekordów ani adresów technicznych, a fokus wraca przewidywalnie;
6. czysta instalacja i aktualizacja nie włączają Sonosa samoczynnie i nie wpływają na nagrywanie;
7. instrukcja pilotażowa została zastąpiona krótką instrukcją zwykłego połączenia konta.

## Wspólny kontrakt w Menedżerze sesji

Wiersze mają krótkie, prawdziwe stany:

- `WiiM, wyłączona, nieskonfigurowana`;
- `WiiM, włączona, urządzenie Salon gotowe`;
- `WiiM, włączona, urządzenie Salon niedostępne`;
- `Sonos, wyłączona, konto niepołączone`;
- `Sonos, włączona, wymaga wybrania grupy`;
- `Sonos, włączona, grupa Salon gotowa`.

`Konfiguruj…` jest wspólnym działaniem Menedżera, ale otwiera właściwą powierzchnię:

- WiiM: `Urządzenia WiiM`;
- Sonos bez konta: `Konto Sonos`;
- Sonos z kontem, ale bez celu: wybór domu i grupy;
- Sonos gotowy: wybór celu sterowania z możliwością przejścia do konta osobnym przyciskiem.

Wiersz nie może zawierać adresu IP, identyfikatora domu, identyfikatora grupy, typu modelu C# ani surowego stanu API. Szczegóły techniczne są dostępne dopiero w świadomie otwartych właściwościach.

## Pierwsza konfiguracja WiiM

1. Włączenie WiiM samo nie rozpoczyna skanowania sieci.
2. `Konfiguruj…` otwiera Menedżer urządzeń z fokusem na `Wykryj urządzenia` przy braku zapisu albo na aktualnym urządzeniu przy ponownym otwarciu.
3. `Wykryj urządzenia` jest świadomym poleceniem i ma ograniczony czas. Podczas wykrywania jeden komunikat mówi, że trwa wyszukiwanie; po zakończeniu jeden komunikat podaje wynik.
4. `Dodaj ręcznie…` przyjmuje lokalny adres urządzenia i sprawdza go przed zapisem. Nie przyjmuje dowolnego publicznego hosta ani adresu z danymi logowania.
5. Zaznaczenie urządzenia nie wysyła Play, Pause, Stop ani zmiany źródła. Dopiero `Użyj tego urządzenia` ustawia cel sterowania.
6. Po zapisie fokus wraca na wybrane urządzenie, a Menedżer sesji podaje `WiiM gotowy: nazwa`.
7. Urządzenie chwilowo offline pozostaje zapisane. Stan zmienia się na `niedostępne`, ale AMC nie usuwa go ani nie uruchamia ponownie wykrywania w pętli.
8. Wejście do sesji może wykonać ciche, ograniczone odświeżenie wyłącznie zapisanego urządzenia. Nie skanuje całej sieci i nie ogłasza cyklicznych wyników.

## Pierwsza konfiguracja Sonos

1. Włączenie Sonosa bez konta nie rozpoczyna OAuth ani nie otwiera przeglądarki.
2. `Konfiguruj…` podaje stan i przycisk `Połącz konto Sonos…`. Dopiero jego naciśnięcie rozpoczyna oficjalne logowanie.
3. Po połączeniu konto jest sprawdzane, a użytkownik przechodzi do wyboru domu i grupy. Nie trzeba szukać drugiego okna w menu.
4. Samo przesuwanie zaznaczenia po domach i grupach niczego nie uruchamia. Dopiero zatwierdzenie ustawia cel sterowania.
5. Wybranie celu nie wysyła Play, Pause, Stop, zmiany kolejki ani zmiany składu grupy.
6. Ponowne otwarcie ustawia fokus na ostatnim domu i grupie po stabilnym identyfikatorze. Gdy zniknęły, fokus trafia na krótką instrukcję, a nie na przypadkowy pierwszy cel.
7. `Ctrl+F5` zachowuje obecne znaczenie wyboru celu sterowania. Konto Sonos pozostaje osobnym poleceniem menu i palety; Menedżer może kierować do niego, gdy konto nie jest połączone.
8. Odłączenie konta wymaga potwierdzenia, czyści wyłącznie poświadczenie oraz zdalny stan Sonosa w AMC i nie wpływa na WiiM ani inne sesje.

## Różnice, których nie ujednolicamy

- WiiM może działać po lokalnym adresie bez konta; Sonos wymaga oficjalnego konta i wyboru domu/grupy.
- WiiM ma lokalne presety sprzętowe i Strumienie sieciowe AMC; Sonos ma ulubione i zasoby konta. Nazwy nie są zamienne.
- `Ctrl+F5` może otwierać inną powierzchnię zgodnie z utrwalonym kontraktem sesji.
- Grupa Sonosa nie jest tym samym co multiroom WiiM. Nie tworzymy wspólnego modelu zapisu grup dopóki oba protokoły nie dają równoważnych, sprawdzonych możliwości.
- Brak biblioteki urządzenia nie jest błędem konta. WiiM nie otrzymuje pozornej Biblioteki z samych presetów lub strumieni.

## Zachowanie sesji i odtwarzania

- wejście do sesji odczytuje stan, ale nie zmienia muzyki;
- wyjście, wyłączenie sesji w Menedżerze oraz zamknięcie AMC nie wysyła Stop ani Pause do autonomicznego urządzenia;
- Enter na gotowym celu otwiera odtwarzacz bieżącego stanu; nie zaczyna automatycznie innego materiału;
- polecenia zmieniające stan są wysyłane tylko po jawnej czynności użytkownika;
- polecenia POST o niepewnym wyniku nie są automatycznie ponawiane;
- brak odpowiedzi nie jest komunikowany ani jako sukces, ani jako pewne odrzucenie, jeżeli transport tego nie potwierdził;
- cykliczne odświeżanie nie przejmuje fokusa i nie zagłusza komunikatów klawiatury;
- starsza odpowiedź nie może nadpisać stanu nowo wybranego urządzenia, domu albo grupy.

## Dostępność NVDA

- listy urządzeń, domów i grup mają jawne `AutomationProperties.Name`, `TextSearch.TextPath` oraz użytkowe `ToString()` dla obiektów wiązanych;
- początkowy fokus zależy od stanu: przycisk konfiguracji przy pustym stanie, ostatni stabilny wiersz przy ponownym otwarciu;
- strzałki tylko wybierają; Enter lub jawny przycisk zatwierdza cel;
- po wykrywaniu, odświeżaniu, zapisie, Anuluj i ponownym otwarciu fokus wraca przewidywalnie;
- okresowe odświeżanie nie wypowiada nic, dopóki nie wymaga działania użytkownika;
- komunikat zawiera nazwę urządzenia albo grupy, ale nie IP, identyfikator, rekord, enum lub pełny adres usługi;
- niedostępność jednego urządzenia nie czyści listy i nie przenosi zaznaczenia na inne bez decyzji użytkownika.

## Pomoc, paleta i menu

- Menedżer sesji podaje `Konfiguruj WiiM…` albo `Konfiguruj Sonos…` zależnie od wiersza;
- `Ctrl+F1` opisuje rzeczywiste znaczenie `Ctrl+F5` osobno dla obu sesji;
- `Ctrl+Shift+K` zawiera konto Sonos, wybór celu Sonos, urządzenia WiiM oraz właściwości aktualnego urządzenia, lecz tylko gdy funkcja jest dostępna;
- menu kontekstowe nie pokazuje `Otwórz w WiiM` bez aktywnego urządzenia; zamiast martwego polecenia może pokazać `Najpierw skonfiguruj WiiM…` prowadzące do Menedżera;
- analogicznie polecenia Sonosa wymagające celu prowadzą do wyboru grupy, a nie kończą się technicznym błędem;
- żadne nowe polecenie nie przejmuje `Ctrl+Enter` ani skrótów z AMC14.

## Testy automatyczne bez urządzeń

1. Włączenie sesji nie rozpoczyna skanowania, logowania ani polecenia zmieniającego odtwarzanie.
2. Wyłączenie Sonosa/WiiM nie wysyła żadnego żądania do urządzenia.
3. `Konfiguruj…` wybiera właściwe okno według stanu konta i urządzenia.
4. WiiM wykryty, dodany ręcznie, offline i ponownie dostępny zachowuje stabilny identyfikator oraz fokus.
5. Sonos bez konta, z kontem bez grupy, z grupą oraz po odłączeniu ma właściwe stany i drogi konfiguracji.
6. Strzałki po listach nie wysyłają Play, Pause, Stop ani zmiany celu.
7. Spóźniony wynik starego wykrywania, konta, domu albo grupy nie zmienia nowszego wyboru.
8. Błąd jednej możliwości WiiM wyłącza tylko tę możliwość, nie całe urządzenie.
9. Niepewny wynik polecenia Sonosa/WiiM nie jest automatycznie ponawiany i ma uczciwy komunikat.
10. Pomoc, paleta i menu odpowiadają dostępności, włączeniu i gotowości sesji.
11. Dane techniczne nie trafiają do etykiet UI Automation ani zwykłego dziennika.
12. Menedżer i okna urządzeń zachowują fokus po Zapisz, Anuluj, odświeżeniu i ponownym otwarciu.

## Próby na prawdziwym sprzęcie

Próby C są oddzielne od kompilacji i wymagają świadomego rozpoczęcia:

- najpierw tylko odczyt stanu i wybór celu, bez zmiany muzyki;
- następnie pojedyncze Play/Pause, głośność i przewijanie na wskazanym urządzeniu;
- osobno test utraty sieci oraz powrotu urządzenia;
- Sonos: potwierdzenie właściwego domu i grupy przed każdym poleceniem;
- WiiM: potwierdzenie modelu i adresu lokalnego w szczegółach, ale nie w zwykłym komunikacie;
- multiroom WiiM wymagający dwóch urządzeń nie jest testowany ani produkowany bez dwóch jawnie wskazanych urządzeń;
- próba nie może przerwać nagrywania AMC ani zmienić innego aktywnego urządzenia bez zgody.

## Świadomie poza zakresem AMC10

- nowy protokół Sonosa lub WiiM;
- przeglądanie pełnych katalogów Spotify/TIDAL przez urządzenie;
- tworzenie i rozłączanie grup WiiM;
- automatyczny zapis natywnych presetów WiiM;
- udawana Biblioteka WiiM;
- ujednolicanie ulubionych Sonosa z presetami WiiM;
- administracja siecią, restart i przywracanie ustawień fabrycznych;
- automatyczne wykrywanie przy każdym starcie świeżej instalacji;
- instalacja składników sieciowych i reguł zapory, które należą do AMC12.

## Decyzje i otwarte szczegóły

1. Rozstrzygnięto: WiiM jest w publicznym instalatorze dostępne, ale początkowo wyłączone. Sonos ma ten sam cel publiczny po wdrożeniu i odbiorze brokera AMC. Wcześniej może być dostępny jako jawnie oznaczona wersja próbna dla chętnych; bez działającego publicznego brokera nie pojawia się w wydaniu publicznym.
2. Czy `Konfiguruj…` ma być przyciskiem oraz `F4` w Menedżerze? Rekomendacja: przycisk od pierwszej wersji; skrót `F4` dopiero po audycie konfliktów.
3. Czy przy niedostępnym aktywnym urządzeniu Enter otwiera odtwarzacz z ostatnim stanem, czy od razu konfigurację? Rekomendacja: otwiera listę z komunikatem `Urządzenie niedostępne`; konfiguracja pozostaje osobnym poleceniem, aby Enter nie zmieniał ustawień.
4. Czy po pierwszym połączeniu Sonosa automatycznie przechodzić do wyboru grupy? Rekomendacja: tak, ale bez automatycznego zatwierdzania pierwszej grupy.
5. Czy po wykryciu jednego WiiM automatycznie go wybrać? Rekomendacja: zaznaczyć, lecz wymagać Enter lub `Użyj tego urządzenia`, żeby sam skan nie zmienił celu.

## Bramka

- Poziom A: wspólne stany i routing Menedżera, testy na atrapach oraz dokumentacja.
- Poziom B: kompilacja wspólna z AMC08 i AMC09; testy bez prawdziwych kont i urządzeń.
- Poziom C: ręczna próba NVDA, następnie oddzielne, jawne próby Sonosa i WiiM.
- Poziom D: sprawdzenie pierwszej konfiguracji z czystego instalatora w AMC12.

Przed kompilacją, uruchomieniem AMC lub testem urządzeń trzeba ponownie potwierdzić, że nie trwa nagrywanie.

## Źródła oficjalne Sonos

- Connected Home i zasady publikacji: https://docs.sonos.com/docs/connected-home-get-started
- autoryzacja, publiczne HTTPS i odnowienie po stronie serwera: https://docs.sonos.com/docs/authorize
- odkrywanie gospodarstw domowych, grup i odtwarzaczy: https://docs.sonos.com/docs/discover
- limity i unikanie nadmiernego odpytywania: https://docs.sonos.com/docs/quotas-and-spike-arrests
