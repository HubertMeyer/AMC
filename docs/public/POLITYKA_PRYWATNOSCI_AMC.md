# Polityka prywatności Accessible Multimedia Controller (AMC)

**Wersja dokumentu:** 0.1 — projekt do uzupełnienia przed publikacją  
**Data ostatniej aktualizacji:** 27 października 2026 r.  
**Planowana data obowiązywania:** dzień pierwszego publicznego wydania AMC

> Ten dokument nie jest jeszcze przeznaczony do publikacji. Przed publikacją
> należy uzupełnić oznaczony adres korespondencyjny administratora
> oraz zamknąć punkty wskazane w liście gotowości.

## 1. Administrator i kontakt

Administratorem danych przetwarzanych w związku z udostępnianiem AMC jest:

**Michał Kasperczak**  
**[ADRES POCZTOWY ALBO INNY WYMAGANY PRAWEM ADRES — DO UZUPEŁNIENIA]**  
**E-mail do spraw prywatności: michalkasperczak@gmail.com**

Strona projektu: <https://github.com/michalkasperczak/AMC>

Publiczne zgłoszenie w repozytorium nie jest właściwym miejscem do przesyłania
danych osobowych, tokenów, haseł ani poufnych próśb dotyczących praw osoby.
Takie sprawy należy kierować na podany wyżej dedykowany adres e-mail.

## 2. Zakres polityki

Polityka dotyczy publicznego wydania Accessible Multimedia Controller (AMC),
aplikacji komputerowej dla Windows służącej do obsługi lokalnych plików,
radia internetowego, podcastów, publicznych materiałów YouTube, urządzeń w
sieci lokalnej oraz — po dobrowolnym połączeniu konta — wybranych danych konta
YouTube.

AMC jest aplikacją lokalną. Większość ustawień, bibliotek, historii działania,
zakładek, pozycji odtwarzania, harmonogramów, nagrań i dzienników pozostaje na
komputerze użytkownika. Samo uruchomienie AMC nie tworzy konta AMC i nie wysyła
zawartości lokalnych bibliotek do administratora.

Ta polityka nie zastępuje polityk niezależnych usług, z którymi użytkownik
łączy się za pośrednictwem AMC.

## 3. Jakie dane są przetwarzane

W zależności od używanych funkcji AMC może przetwarzać następujące dane:

1. **Dane lokalnej konfiguracji i biblioteki** — ustawienia programu, zapisane
   stacje i kanały, podcasty, playlisty, zakładki, pozycje odtwarzania,
   harmonogramy, informacje o plikach i urządzeniach oraz lokalne komunikaty
   diagnostyczne.
2. **Dane sieciowe niezbędne do połączenia** — adres IP oraz podstawowe dane
   techniczne połączenia, które są przetwarzane przez dostawcę wybranej usługi,
   serwera strumienia, kanału RSS, GitHub, Google, YouTube albo innej strony,
   z którą użytkownik polecił AMC się połączyć.
3. **Dane autoryzowanego konta YouTube** — tokeny OAuth oraz dane potrzebne do
   pokazania i ręcznego zapisania subskrypcji i playlist: identyfikatory i nazwy
   kanałów lub playlist, status widoczności playlisty, liczba i podstawowe dane
   jej materiałów oraz informacje o transmisjach kanałów. AMC nie pobiera
   hasła do konta Google.
4. **Dane zgłoszenia problemu lub sugestii** — wyłącznie po jawnym poleceniu
   użytkownika: rodzaj zgłoszenia, tytuł, opis, kroki odtworzenia, opcjonalny
   adres e-mail i — po osobnym włączeniu — ograniczony fragment dziennika.
   Przed wysłaniem AMC pokazuje pełny podgląd i automatycznie usuwa wiele
   typowych danych prywatnych, lecz użytkownik powinien dodatkowo sprawdzić
   treść.
5. **Dane aktualizacji** — podczas sprawdzania aktualizacji GitHub otrzymuje
   zwykłe dane połączenia sieciowego. AMC pobiera metadane wydań i, po decyzji
   użytkownika, instalator.

AMC nie wykorzystuje tych danych do reklamy, śledzenia użytkownika pomiędzy
usługami, profilowania ani podejmowania decyzji wywołujących skutki prawne.

## 4. Cele i podstawy przetwarzania

Dane są przetwarzane wyłącznie w następujących celach:

- wykonanie funkcji wybranej przez użytkownika, w tym odtworzenie materiału,
  zapis ustawień, synchronizacja konta YouTube albo przygotowanie aktualizacji
  — art. 6 ust. 1 lit. b RODO, gdy przetwarzanie jest niezbędne do świadczenia
  żądanej funkcji;
- połączenie opcjonalnego konta Google/YouTube lub dobrowolne wysłanie
  zgłoszenia — art. 6 ust. 1 lit. a RODO, jeżeli podstawą danej operacji jest
  zgoda; zgodę można wycofać bez wpływu na zgodność wcześniejszego
  przetwarzania;
- zapewnienie bezpieczeństwa usługi, ograniczanie nadużyć, diagnozowanie
  awarii i ochrona integralności aktualizacji — art. 6 ust. 1 lit. f RODO,
  czyli prawnie uzasadniony interes administratora polegający na utrzymaniu
  bezpiecznej i działającej usługi.

Podstawa prawna powinna zostać ostatecznie potwierdzona przez administratora
przed publikacją, z uwzględnieniem sposobu dystrybucji AMC.

## 5. Google i YouTube

AMC korzysta z usług YouTube API Services oraz autoryzacji Google OAuth 2.0.
Połączenie konta jest dobrowolne i korzysta wyłącznie z zakresu
`youtube.readonly`. AMC używa go do odczytu danych potrzebnych do pokazania
subskrypcji, playlist i transmisji. AMC nie subskrybuje kanałów, nie usuwa
subskrypcji, nie modyfikuje playlist ani nie publikuje treści na koncie
YouTube.

Synchronizacja jest ręczna i jednokierunkowa: z YouTube do lokalnej Biblioteki
AMC. Najpierw użytkownik wywołuje sprawdzenie bez zapisu, a następnie osobno
zatwierdza zapis. Zapisany lokalnie kanał lub playlista pozostaje w Bibliotece
AMC do czasu usunięcia przez użytkownika; usunięcie w AMC nie powoduje zmiany
na koncie YouTube. Nowa subskrypcja wykonana na stronie lub w aplikacji YouTube
zostanie pokazana przez AMC przy następnym ręcznym sprawdzeniu.

Tokeny dostępu i odświeżania są przechowywane w chronionym magazynie
poświadczeń Windows bieżącego użytkownika. Publiczne AMC nie zawiera sekretu
klienta Google. Wąski broker HTTPS przetwarza kod autoryzacyjny, zabezpieczenie
PKCE albo token odświeżania tylko przez czas potrzebny do wymiany ich w
oficjalnym punkcie Google. Broker nie zapisuje tokenów w trwałej bazie i ma
wyłączone rejestrowanie treści żądań. Adres IP może być krótkotrwale
przetwarzany w celu ograniczania nadużyć i zapewnienia bezpieczeństwa.

W docelowym publicznym wydaniu użytkownik może cofnąć autoryzację poleceniem
odłączenia konta w AMC. Polecenie ma programowo cofnąć token Google, usunąć
lokalne poświadczenie i rozpocząć usuwanie danych uzyskanych na podstawie tej
autoryzacji. Użytkownik może także cofnąć dostęp AMC na stronie ustawień
bezpieczeństwa Google:
<https://security.google.com/settings/security/permissions>. Cofnięcie dostępu
w Google nie
usuwa danych z komputera samo przez się. AMC musi okresowo potwierdzać ważność
autoryzacji, a po wykryciu cofnięcia usunąć powiązane dane API w terminie
wymaganym przez zasady YouTube. Zwykłe usunięcie lokalnego kanału lub playlisty
w AMC nie zmienia danych przechowywanych przez YouTube.

Korzystanie z funkcji YouTube podlega również:

- Warunkom korzystania z YouTube: <https://www.youtube.com/t/terms>;
- Polityce prywatności Google: <https://policies.google.com/privacy>;
- Warunkom korzystania z YouTube API Services:
  <https://developers.google.com/youtube/terms/api-services-terms-of-service>.

## 6. Odbiorcy i dostawcy usług

AMC przekazuje dane tylko wtedy, gdy jest to konieczne do wykonania polecenia
użytkownika. Odbiorcami lub podmiotami przetwarzającymi mogą być:

- Google LLC i YouTube LLC — autoryzacja konta oraz YouTube API Services;
- Cloudflare, Inc. — infrastruktura brokera OAuth oraz, jeżeli zostanie
  uruchomiona, infrastruktura wysyłania zgłoszeń;
- GitHub, Inc. — sprawdzanie i pobieranie aktualizacji oraz obsługa zgłoszeń;
- operator wybranej stacji, serwera podcastu, serwisu multimedialnego albo
  innego adresu internetowego otwartego na polecenie użytkownika;
- urządzenia wskazane przez użytkownika w jego sieci lokalnej.

Każdy niezależny dostawca przetwarza dane także zgodnie z własnymi warunkami i
polityką prywatności. Informacje o praktykach Cloudflare i GitHub znajdują się
odpowiednio pod adresami <https://www.cloudflare.com/privacypolicy/> oraz
<https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement>.

Nie sprzedajemy danych osobowych i nie udostępniamy ich sieciom reklamowym.

## 7. Przekazywanie danych poza Europejski Obszar Gospodarczy

Google, Cloudflare, GitHub oraz operatorzy wybranych przez użytkownika usług
mogą przetwarzać dane poza Europejskim Obszarem Gospodarczym. Podmioty te
odpowiadają za stosowanie właściwych podstaw i zabezpieczeń takiego transferu,
zgodnie ze swoimi dokumentami prawnymi. Administrator powinien przed
publikacją potwierdzić role tych podmiotów oraz stosowane mechanizmy transferu.

## 8. Okres przechowywania

- Dane lokalnej Biblioteki, ustawień, zakładek, harmonogramów i nagrań są
  przechowywane na komputerze do czasu ich usunięcia przez użytkownika albo
  usunięcia odpowiedniego profilu AMC.
- Tokeny Google/YouTube są przechowywane do wylogowania, cofnięcia dostępu,
  utraty ważności albo usunięcia magazynu poświadczeń profilu.
- Podgląd synchronizacji konta jest przechowywany wyłącznie w pamięci i wygasa
  najpóźniej po 10 minutach.
- Dane YouTube zapisane w Bibliotece są odświeżane lub usuwane zgodnie z
  obowiązującymi zasadami YouTube API Services. Ręczne ponowne sprawdzenie
  konta odnawia datę potwierdzenia danych. Jeżeli oznaczone dane konta nie
  zostaną potwierdzone przez 30 dni, AMC Public usuwa je przy następnym
  uruchomieniu skonfigurowanego klienta YouTube.
- Po cofnięciu autoryzacji bezpośrednio w AMC powiązane dane autoryzowane muszą
  zostać usunięte możliwie szybko, nie później niż w ciągu 7 dni. Gdy cofnięcie
  nastąpiło po stronie Google, AMC musi je wykryć i usunąć powiązane dane API
  możliwie szybko, nie później niż w ciągu 30 dni.
- Lokalnie zapisane raporty pozostają do ich usunięcia przez użytkownika.
- Raport wysłany do obsługi pozostaje przez okres potrzebny do diagnozy,
  usunięcia nadużyć i udokumentowania rozwiązania problemu, nie dłużej niż
  **[OKRES RETENCJI ZGŁOSZEŃ — DO UZUPEŁNIENIA]**.
- Krótkookresowe dane ochrony przed nadużyciem są usuwane albo wygasają po
  czasie niezbędnym do działania ograniczenia tempa.

## 9. Usuwanie danych i cofnięcie dostępu

W publicznym wydaniu użytkownik może:

- cofnąć autoryzację YouTube w AMC, co programowo unieważnia token, usuwa go z
  magazynu poświadczeń Windows i usuwa dane API powiązane z tym połączeniem;
- cofnąć dostęp w ustawieniach konta Google;
- usuwać kanały, playlisty, podcasty, zakładki, nagrania i inne elementy z
  lokalnej Biblioteki;
- usunąć lokalne dane profilu AMC albo odinstalować aplikację zgodnie z
  instrukcją wydania;
- zażądać usunięcia danych wysłanych administratorowi, kontaktując się na
  dedykowany adres podany w punkcie 1.

Opisane wyżej pełne cofnięcie autoryzacji i usunięcie danych API jest warunkiem
wydania AMC Public. Źródła profilu Public realizują ten proces, lecz przed
publikacją trzeba go jeszcze potwierdzić z produkcyjnym klientem Google,
wdrożonym brokerem i czystym profilem użytkownika. AMC Test zachowuje prywatne,
lokalne wylogowanie bez usuwania istniejącej Biblioteki.

Żądanie może wymagać potwierdzenia tożsamości w zakresie niezbędnym do ochrony
danych przed usunięciem przez osobę nieuprawnioną.

## 10. Prawa osoby

W zakresie wynikającym z RODO użytkownik może żądać dostępu do danych, ich
sprostowania, usunięcia, ograniczenia przetwarzania i przeniesienia, a także
wnieść sprzeciw wobec przetwarzania opartego na prawnie uzasadnionym interesie.
Jeżeli podstawą jest zgoda, można ją wycofać w dowolnym momencie.

Użytkownik może również złożyć skargę do Prezesa Urzędu Ochrony Danych
Osobowych: <https://uodo.gov.pl/>.

## 11. Bezpieczeństwo

AMC stosuje rozdzielone profile poświadczeń, magazyn poświadczeń Windows,
szyfrowany transport HTTPS, PKCE, ograniczony zakres OAuth, kontrolę integralności
aktualizacji oraz redakcję danych w raportach. Żaden środek bezpieczeństwa nie
eliminuje jednak całkowicie ryzyka. Użytkownik nie powinien umieszczać haseł,
tokenów ani innych poufnych danych w opisach zgłoszeń.

## 12. Pliki cookie, reklama i profilowanie

Aplikacja komputerowa AMC nie używa własnych plików cookie, nie wyświetla
reklam i nie prowadzi profilowania. Strony Google, YouTube, GitHub i innych
zewnętrznych usług otwierane poza AMC mogą korzystać z własnych plików cookie
zgodnie ze swoimi politykami.

## 13. Dzieci

AMC nie jest usługą kierowaną specjalnie do dzieci i nie służy do świadomego
zbierania ich danych. Opiekun powinien nadzorować korzystanie przez dziecko z
kont Google, YouTube i innych usług zgodnie z zasadami tych usług.

## 14. Zmiany polityki

Nowa wersja polityki otrzyma datę aktualizacji. Jeżeli zmiana rozszerzy sposób
wykorzystania autoryzowanych danych Google lub YouTube, AMC przed takim użyciem
przedstawi zmianę i — gdy będzie to wymagane — poprosi o ponowną zgodę.

