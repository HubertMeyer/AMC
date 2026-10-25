# STR-001 — laboratorium TIDAL i Apple Music

- Status: `Wstrzymane — Apple Music ma bezsekretny prototyp serwerowy, ale
  prawdziwy test i wdrożenie wymagają własnego zespołu Apple Developer
  należącego do właściciela AMC`
- Utworzono: 18 października 2026
- Obszar: usługi strumieniowe i profil testowy
- Polecenie uruchamiające: `Uruchom zadanie STR-001`

## Cel

Zbadać oficjalne możliwości TIDAL i Apple Music bez obiecywania użytkownikom
funkcji, których dostawcy nie pozwalają niezależnemu klientowi wykonać.
Najpierw powstaje raport i mały eksperyment w profilu testowym; dopiero potem
może zapaść osobna decyzja o wdrożeniu.

## TIDAL

- Ponownie sprawdzić aktualne Web API, SDK oraz warunki deweloperskie.
- Pełne odtwarzanie wolno realizować wyłącznie przez oficjalny, niezmieniony
  moduł Player udostępniony przez TIDAL; katalog, Biblioteka i playlisty nie są
  automatycznie dowodem możliwości odtwarzania.
- Zachować istniejące ustalenia i nie powtarzać identycznej próby logowania ani
  pytania do TIDAL bez nowego dowodu.

## Apple Music

- Sprawdzić Apple Music API, MusicKit on the Web i ewentualny natywny klient
  macOS oddzielnie.
- Apple wymaga identyfikatora MusicKit i podpisanego tokenu deweloperskiego;
  dane Biblioteki wymagają także zgody użytkownika i Music User Token.
- Odtwarzanie na Windows należy badać przez oficjalne MusicKit on the Web, a
  nie przez odtwarzanie przechwyconych adresów multimediów. Natywny macOS może
  korzystać z MusicKit dla Swift, ale jest to osobny adapter platformy.

## Korekty użytkownika

- 2026-10-25: użytkownik uruchomił równoległą pracę nad Sonosem i Apple Music
  oraz dopuścił użycie tego samego publicznego serwera. Następnie ustalił, że
  posiadany przez znajomego klucz należy do obcego zespołu Apple Developer, a
  zakup własnego członkostwa bez dowodu działania byłby ryzykiem. Zastępuje to
  założenie, że sam istniejący token można po prostu podłączyć do publicznego
  AMC. Dalsze prawdziwe wdrożenie jest wstrzymane; dopuszczalny pozostaje
  laboratoryjny test pod świadomą kontrolą właściciela klucza.
- 2026-10-25, korekta późniejsza: po sprawdzeniu aktualnej umowy Apple Developer
  Program License Agreement wycofano także propozycję rzeczywistego testu na
  koncie znajomego. Zastępuje ona ostatnie zdanie poprzedniej korekty. Sama
  zgoda znajomego ani prywatny charakter próby nie czynią AMC jego aplikacją i
  nie spełniają warunku pracy wykonawcy wyłącznie w jego imieniu. Projekt nie
  poprosi znajomego o plik `.p8`, developer token, dostęp do konta ani
  uruchomienie brokera dla AMC. To ostrożna decyzja projektowa na podstawie
  bieżącego tekstu umowy, a nie porada prawna.

## Wynik badania Apple Music z 25.10.2026

Oficjalny kontrakt Apple potwierdza:

- każde żądanie Apple Music API wymaga developer tokenu podpisanego ES256;
- token zawiera Team ID jako `iss`, Key ID w nagłówku `kid`, czas wydania i
  wygaśnięcia; Apple dopuszcza najwyżej sześć miesięcy, ale laboratorium AMC
  ogranicza własne tokeny do 5–1440 minut, domyślnie jednej godziny;
- dla klienta webowego Apple zaleca claim `origin`; prototyp AMC wydaje token
  tylko dla jednego wcześniej dozwolonego originu HTTPS;
- MusicKit on the Web sam zarządza Music User Tokenem po zgodzie użytkownika.
  Prywatna Biblioteka, playlisty i historia wymagają tej zgody;
- MusicKit on the Web oficjalnie obsługuje odtwarzanie muzyki, teledysków i
  radia w przeglądarce. Nadal trzeba osobno potwierdzić zachowanie w WebView2,
  kontrolę z natywnego interfejsu AMC i pełną dostępność z NVDA;
- Apple Music API udostępnia katalog, wyszukiwanie, Bibliotekę, playlisty,
  ostatnio odtwarzane elementy, rekomendacje i oceny. Nie znaleziono
  oficjalnego kontraktu pobierania chronionych plików do własnego odtwarzacza;
  AMC nie będzie przechwytywał adresów mediów ani budował pobierania offline;
- członkostwo Apple Developer Program kosztuje obecnie 99 USD rocznie lub
  równowartość lokalną. Samo bezpłatne konto nie daje potrzebnego zestawu
  Media ID i klucza do tej publicznej integracji.

Źródła oficjalne, sprawdzone 25.10.2026:

- https://developer.apple.com/support/terms/
- https://developer.apple.com/fr/support/terms/apple-developer-program-license-agreement/
- https://developer.apple.com/documentation/applemusicapi/generating-developer-tokens
- https://developer.apple.com/documentation/applemusicapi/user-authentication-for-musickit
- https://developer.apple.com/musickit/
- https://developer.apple.com/help/account/capabilities/create-a-media-identifier-and-private-key
- https://developer.apple.com/help/account/membership/program-enrollment

## Prototyp bez sekretów

Powstała osobna usługa `AccessibleMediaController.AppleMusicTokenBroker`.
Czyta prywatny klucz wyłącznie z pliku na serwerze, sprawdza klucz EC P-256,
wydaje krótki token ES256, wymaga dokładnego originu HTTPS, stosuje wąski CORS,
limit osobno dla klienta, kontrolę zaufanego reverse proxy i bezpieczne
endpointy stanu. Nie zawiera prawdziwego Team ID, Key ID, Media ID, klucza,
developer tokenu ani Music User Tokenu.

Testy laboratoryjne zaliczyły 12/12 przypadków: konfigurację, origin, zakres
czasu, walidację klucza, podpis i claimy JWT, endpoint, CORS, HTTPS, zaufane
proxy, limit per klient oraz brak identyfikatorów w stanie usługi.

Prototyp nie został spakowany, wdrożony ani podłączony do AMC. Nie dowodzi
jeszcze logowania użytkownika, odtwarzania, zgodności terytorialnej ani NVDA.

## Najtańsza zgodna bramka decyzji

1. Nie używamy konta, klucza ani tokenu znajomego — ani publicznie, ani do
   rzeczywistej prywatnej próby AMC.
2. Bez konta Apple wolno kontynuować jedynie lokalne testy naszej architektury:
   konfiguracji, podpisu testowym kluczem, CORS, limitów i dostępnego interfejsu
   na danych pozorowanych. Nie nazywamy tego testem integracji z Apple Music.
3. Kasperczak albo formalny właściciel AMC, na przykład FIRR, ustala kto ma być
   właścicielem produktu i zespołu Apple Developer. Dopiero ten podmiot może
   rozważyć własne członkostwo i zaakceptować aktualne warunki Apple.
4. Dopiero na własnym zespole powstaje osobny Media ID i klucz. Pierwszym
   etapem jest niepubliczny pilot: logowanie użytkownika, pełny utwór, pauza,
   przewijanie, zmiana pozycji, odnowienie sesji i cały przebieg NVDA.
5. Publikacja następuje tylko po udanym pilocie, sprawdzeniu aktualnej umowy,
   wytycznych marki i ustaleniu modelu utrzymania. Sam prywatny zasięg nie
   pozwala użyć poświadczeń zespołu, do którego AMC nie należy.

## Organizacja pracy

- Badanie może zostać wykonane w osobnym zadaniu Codex albo przez Hermesa,
  kiedy użytkownik jawnie je uruchomi. Raport musi wrócić do tego pliku i
  zawierać źródła, datę, ograniczenia konta oraz rozdzielenie faktów od
  hipotez.
- Żadne zewnętrzne zadanie nie otrzymuje tokenów, danych kont ani prywatnego
  profilu AMC. Próby logowania i odtwarzania wykonuje się dopiero lokalnie, po
  osobnej zgodzie i w odizolowanym profilu testowym.
- TIDAL i Apple Music pozostają poza publicznym profilem do czasu osobnego
  odbioru prawnego, funkcjonalnego i dostępnościowego.

## Kryteria zakończenia badania

1. Macierz: katalog, wyszukiwanie, Biblioteka, playlisty, historia,
   odtwarzanie, sterowanie, pobieranie i ograniczenia terytorialne.
2. Opis oficjalnego logowania bez sekretu osadzonego w publicznym kliencie.
3. Prototyp nie zapisuje ani nie odtwarza chronionych adresów poza oficjalnym
   SDK.
4. Decyzja: odrzucić, pozostawić w laboratorium albo przygotować osobny plan
   wdrożenia testowego.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data etapu: 25 października 2026
- Wersje API i warunków:
- Apple Music API i MusicKit on the Web v3 według dokumentacji dostępnej
  25.10.2026; członkostwo 99 USD/rok według strony Apple.
- Wynik TIDAL: nie był przedmiotem tego etapu.
- Wynik Apple Music: architektura i podpisywanie tokenu są wykonalne, lecz
  brakuje dowodu realnego MusicKit/WebView2/NVDA i stabilnego właściciela
  zespołu deweloperskiego.
- Rekomendacja: pozostawić w laboratorium bez połączenia z Apple. Nie używać
  zespołu znajomego nawet do rzeczywistego testu. Wrócić do pilota dopiero po
  wskazaniu właściciela AMC i założeniu przez niego własnego zespołu Apple
  Developer; przed kosztem można nadal oceniać makietę interfejsu i dostępność.

## Materiał do dokumentacji użytkownika

Apple Music nie jest jeszcze sesją AMC Test ani AMC Public. Żaden przycisk,
skrót ani ekran logowania nie został dodany. Użytkownik nie przekazuje AMC
hasła Apple ani prywatnego klucza deweloperskiego. Przyszłe logowanie będzie
odbywać się wyłącznie w oficjalnym MusicKit, a odtwarzanie na Windows pozostanie
w oficjalnym odtwarzaczu webowym Apple sterowanym przez dostępny interfejs AMC.

## Uzasadnienie i decyzje

- Ten sam fizyczny serwer może później utrzymywać Sonosa i Apple Music, lecz
  będą to osobne procesy, sekrety, limity, hosty i procedury wycofania.
- Obcy klucz i token nie są importowane, używane ani uruchamiane dla AMC.
- Brak realnej próby oznacza brak obietnicy publicznego Apple Music.

## Testy i wynik

- `dotnet run --project tests/AccessibleMediaController.AppleMusicTokenBroker.SmokeTests/AccessibleMediaController.AppleMusicTokenBroker.SmokeTests.csproj -c Release`
  — 12/12 zaliczone 25.10.2026.

## Znane ograniczenia

- brak prawdziwego klucza i realnego developer tokenu;
- brak próby Music User Token i konta subskrybenta;
- brak hosta HTTPS, strony odtwarzacza, WebView2 i sterowania z AMC;
- brak ręcznego testu NVDA;
- brak decyzji o docelowym właścicielu Apple Developer Team.

## Wersja i commit

Kod laboratoryjny powstał lokalnie 25.10.2026 w commicie
`8655c063353ac4ffe8803f3da9adb0e691885d40`. Późniejsza korekta tego samego
dnia wycofuje zawartą w nim propozycję testu na koncie znajomego. Nie wykonano
instalacji, publikacji ani prawdziwego połączenia z Apple.

