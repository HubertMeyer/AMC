# AMC — projekt interfejsu wxPython

Stan decyzji: 7 października 2026 r. Ten dokument opisuje kierunek portu
interfejsu. Nie oznacza, że wymienione funkcje są już przeniesione.

## 1. Decyzja technologiczna

Nie przepisujemy teraz całego AMC do Pythona ani do Rusta. Wymieniamy przede
wszystkim zawodną warstwę WPF na interfejs wxPython oparty na natywnych
kontrolkach Windows. Sprawdzona logika, odtwarzanie i integracje pozostają na
razie w bezokiennym hoście .NET.

Docelowy podział:

- wxPython odpowiada za okna, listy, menu, dialogi, fokus, lokalną obsługę
  klawiatury oraz dostępne komunikaty;
- dodatek NVDA pozostaje osobnym, niewidzialnym interfejsem w Pythonie i
  obsługuje jawne globalne polecenia AMC;
- bezokienny host .NET wykonuje logikę Biblioteki, odtwarzania, Radia, TIDAL-a,
  Sonosa, harmonogramów, zapisu stanu i innych istniejących usług;
- Rust może pozostać w wyspecjalizowanych procesach pomocniczych, na przykład
  w hoście Librespot. Nie jest planowaną technologią całego interfejsu.

Spójność zapewnia jeden wersjonowany protokół poleceń i zdarzeń, a nie jeden
język programowania. Każda komenda ma stabilny identyfikator niezależny od
przypisanego klawisza. Interfejs nigdy nie wypowiada identyfikatorów, enumów,
nazw klas ani reprezentacji obiektów.

## 2. Stan prototypu i granice wiedzy

Dostarczona próba `AMC-Python-proba-list-20261005` potwierdza działanie
wxPython dla plików lokalnych i Radia internetowego, nawigacji po listach,
lewej strzałki z informacją o pozycji oraz części ustawień sesji. Nie uznajemy
za ukończone Kolejki ani Ulubionych bez ponownego pomiaru źródeł i żywego
interfejsu.

Paczka zawiera kod interfejsu, lecz nie pełny katalog źródłowy, 1062 testy ani
źródła małego hosta .NET. Manifest wskazuje nieopublikowaną gałąź
`hermes/wx-session-options-final-20261007`. Przed dalszą implementacją trzeba
odzyskać pełny katalog roboczy z Hermesa albo jawnie odtworzyć brakujące
elementy w głównym repozytorium. Nie rozwijamy długotrwale kodu wyłącznie na
podstawie gotowego pliku EXE.

## 3. Widoczny interfejs i niewidzialny interfejs NVDA

Są to dwie współpracujące, ale odrębne warstwy.

### wxPython

- pokazuje jedną główną listę i właściwe okna pomocnicze;
- utrzymuje rzeczywisty fokus klawiatury oraz zaznaczenie po stabilnym ID;
- ustawia jawne, użytkowe nazwy dostępnościowe wszystkich pozycji;
- nie ogłasza rutynowo zmian, które NVDA już prawidłowo czyta z natywnej
  kontrolki;
- po Zapisz, Anuluj i Escape oddaje fokus dokładnie do kontrolki, z której
  otwarto dialog.

### Dodatek NVDA

- pozostaje napisany w Pythonie, ponieważ działa wewnątrz NVDA;
- jest cienkim klientem wersjonowanego IPC, a nie drugim odtwarzaczem ani
  kopią logiki AMC;
- rejestruje wyłącznie udokumentowane globalne gesty AMC i pozwala użytkownikowi
  przemapować je w NVDA;
- nie modyfikuje własnych przypisań użytkownika i nie wysyła dowolnych komend,
  ścieżek lub danych konta;
- nie przejmuje standardowych poleceń odczytu NVDA.

## 4. `NVDA+strzałka w górę` i pasek stanu

Użytkownik potwierdził ważną regresję starego interfejsu: w aplikacji WPF
`NVDA+strzałka w górę` odczytywało zawartość paska stanu, podobnie jak
`NVDA+End`, zamiast odczytać element mający fokus. W próbie wxPython standardowy
odczyt bieżącego elementu działał prawidłowo.

Obowiązują dwa niezależne kanały:

- `NVDA+strzałka w górę` odczytuje kontrolkę lub wiersz mający rzeczywisty
  fokus;
- `NVDA+End` odczytuje natywny pasek stanu z informacją o aktualnym
  odtwarzaniu.

Dodatek NVDA ani router klawiatury AMC nie mogą przechwytywać tych gestów.
Pasek stanu może istnieć w wxPython, ale nie może stać się źródłem nazwy
bieżącego wiersza ani przestawiać obiektu nawigatora NVDA. Komunikat chwilowy
i tekst dostępny później na żądanie są osobnymi mechanizmami.

Nie przypisujemy poprawy automatycznie samemu brakowi lub istnieniu paska
stanu. Rozstrzygający jest test żywym NVDA: fokus na kilku różnych wierszach,
`NVDA+strzałka w górę`, następnie `NVDA+End`, zmiana sesji, powrót i ponowne
otwarcie programu. Zapis z Podglądu mowy jest częścią wyniku.

## 5. Klawiatura i zmiana skrótów

Warstwa klawiatury należy głównie do interfejsu wxPython, natomiast globalne
gesty poza oknem programu należą do dodatku NVDA. Obie drogi wywołują te same
identyfikatory komend w hoście.

Wymagany model:

1. katalog komend z użytkowymi polskimi nazwami;
2. osobna domyślna mapa klawiatury;
3. profile użytkownika z możliwością skopiowania i zmiany;
4. wykrywanie konfliktów i odmowa niejednoznacznego przypisania;
5. import i eksport mapy bez danych kont oraz ścieżek prywatnych;
6. pomoc klawiatury generowana z aktywnej mapy, nie z drugiej ręcznie
   utrzymywanej listy;
7. zachowanie własnych przypisań gestów NVDA.

Pełne moduły edycji skrótów przygotowane na Hermesie nie znajdują się w
dostarczonej paczce. Trzeba je odzyskać razem z testami przed ponownym
projektowaniem tej funkcji.

## 6. Zgłaszanie błędów i sugestii — Sygnalista

Wykorzystujemy projekt Michała Dziwisza
[Sygnalista](https://github.com/michaldziwisz/sygnalista), udostępniony na
licencji MIT. Jego klient Python pasuje do warstwy wxPython i pozwala wysłać
zgłoszenie do GitHub Issues bez konta GitHub użytkownika.

Integracja jest planowana osobno w dwóch programach: w AMC oraz w EdSharp NG.
Możemy wykorzystać ten sam sprawdzony klient i wzorzec dostępnego formularza,
ale każdy program ma własne `appId`, wersję, diagnostykę, docelowe repozytorium
zgłoszeń i zasady dołączania logów. Nie tworzymy jednego wspólnego zgłoszenia
ani nie przesyłamy stanu jednego programu w raporcie drugiego.

Docelowe okno `Pomoc → Zgłoś błąd lub sugestię` zawiera:

- rodzaj zgłoszenia, tytuł i opis;
- opcjonalny adres kontaktowy z jednoznacznym ostrzeżeniem, czy będzie
  publiczny;
- odznaczone domyślnie pole `Dołącz log diagnostyczny`;
- opis danych, które zostaną wysłane, oraz możliwość przejrzenia lub zapisania
  treści przed wysłaniem;
- wynik z numerem i adresem utworzonego zgłoszenia.

Przed integracją klient wymaga warstwy prywatności AMC. Usuwamy tokeny,
ciasteczka, adresy usług zawierające dane uwierzytelniające, nazwy kont,
prywatne ścieżki, zawartość schowka i nazwy odtwarzanych prywatnych plików.
Samo zaznaczenie logu jest świadomą zgodą dotyczącą konkretnego wysłania, nie
ustawieniem włączanym na stałe. Token Workera nie trafia do publicznego
repozytorium ani logu.

## 7. Aktualizacje AMC jak w EdSharp NG, z zabezpieczeniami AMC

Wyraźnym wymaganiem jest przeniesienie do AMC sposobu obsługi aktualizacji
znanego z
[EdSharp NG](https://github.com/michalkasperczak/EdSharpNG): ręczne polecenie
sprawdzenia aktualizacji, opcjonalne sprawdzenie przy starcie, czytelne
rozróżnienie braku nowej wersji od błędu sieci, pobranie instalatora z GitHub
Releases i weryfikacja SHA-256.

Nie kopiujemy prostszego kodu aktualizacji w miejsce istniejącego mechanizmu
AMC. Zachowujemy mocniejsze właściwości obecnego backendu:

- weryfikację sumy kontrolnej przed uruchomieniem instalatora;
- bezpieczny katalog oczekującej aktualizacji i ochronę przed wyjściem poza
  niego;
- zapis stanu oraz rozróżnienie aktualizacji ręcznej i automatycznej;
- zakaz zamknięcia lub instalacji przy aktywnym nagrywaniu albo niepewnym
  wyniku kontroli nagrań;
- zachowanie materiału, pozycji, pauzy, widoku i głośności;
- potwierdzenie wersji rzeczywiście zainstalowanego i uruchomionego programu;
- niezależne wersjonowanie aplikacji i dodatku NVDA.

wxPython dostarcza dostępne okno i komunikaty, a pobieranie, weryfikacja oraz
plan instalacji pozostają usługą backendu. Operacje sieciowe nie blokują
wątku interfejsu ani klawiatury NVDA.

## 8. Projekty referencyjne i silnik zmiany tempa

Trzy dostępne programy traktujemy jako źródła rozwiązań i przypadków
testowych, nie jako kod do automatycznego kopiowania:

- [SARA](https://github.com/michaldziwisz/sara) Michała Dziwisza jest napisana
  w Pythonie i używa wxPython. Warto porównać jej natywne listy, obsługę wielu
  playlist, rozbudowane sterowanie klawiaturą, zarządzanie fokusem oraz cienki
  dodatek NVDA, który ogranicza zbędne komunikaty bez uciszania zwykłej
  nawigacji po elementach. SARA jest punktem odniesienia przede wszystkim dla
  widocznego interfejsu AMC i współpracy z NVDA, nie gotowym zamiennikiem
  backendu odtwarzania;
- [Paperback](https://github.com/trypsynth/paperback), rozwijany także w
  [forku Michała Dziwisza](https://github.com/michaldziwisz/paperback), nie
  jest programem w Pythonie. Jest napisany w Rust i buduje natywny interfejs
  wxWidgets przez `wxDragon`. Odtwarzanie narracji wykorzystuje `rodio 0.22.2`,
  a zmianę tempa bez zmiany wysokości głosu — `rodio-wsola 0.2.0`, czyli
  implementację algorytmu WSOLA na licencji Apache-2.0. To potwierdzony
  kandydat do porównania jakości przyspieszonej mowy i audiobooków;
- [FastPlay](https://github.com/masonasons/FastPlay) projektu `masonasons` jest
  napisanym w C++ dostępnym odtwarzaczem dla Windows i macOS z interfejsem
  wxWidgets oraz obsługą czytników ekranu przez Universal Speech. Stosuje dwa
  różne tory zmiany tempa: [Google
  Speedy](https://github.com/google/speedy) do mowy oraz [Signalsmith
  Stretch](https://github.com/Signalsmith-Audio/signalsmith-stretch) do
  muzyki. Speedy używa Sonic i nieliniowo kompresuje mowę, aby ważne dla
  zrozumiałości krótkie fragmenty, zwłaszcza spółgłoski, przyspieszać mniej niż
  samogłoski i części nieakcentowane. Speedy i Sonic są na licencji
  Apache-2.0, Signalsmith Stretch na MIT. Repozytorium FastPlay opisuje
  licencje bibliotek, ale nie zawiera licencji samego programu; można więc
  badać jego zachowanie i architekturę, lecz nie kopiować kodu FastPlay do AMC
  bez jednoznacznego pozwolenia autora lub dodania licencji projektu.

Obecny AMC korzysta z `SoundTouch.Net 2.3.2` i warstwy NAudio. Zwykłe
odtwarzanie 1,00x omija procesor SoundTouch, a istniejący kod obsługuje osobno
zmianę tempa bufora timeshift. Sam port interfejsu do wxPython nie wymusza
wymiany tego silnika. `rodio-wsola` ani rozwiązania FastPlay nie mogą go
zastąpić wyłącznie na podstawie opinii, nazwy algorytmu lub technologii
programu.

Przed decyzją przygotowujemy powtarzalne porównanie SoundTouch i kandydatów:

1. te same próbki polskiej mowy, audiobooka, podcastu, muzyki i trudnych
   spółgłosek przy 0,50x, 0,75x, 1,25x, 1,50x, 1,75x i 2,00x;
2. ślepy odsłuch artefaktów, zrozumiałości, naturalności głosu i stabilności
   wysokości, z użytkownikiem NVDA jako obowiązkowym recenzentem;
3. pomiar opóźnienia, zużycia procesora i pamięci, startu, pauzy, przewijania,
   zmiany pliku, krótkich klipów, końca materiału oraz luk między blokami;
4. osobne próby dla plików lokalnych, Radia, podcastów, audiobooków i
   doganiania transmisji z bufora timeshift;
5. ocenę obsługiwanych formatów, odporności na błędy, pakowania Windows,
   utrzymania biblioteki, licencji oraz wymaganych informacji o autorach;
6. wybór dopiero po zapisaniu wyników A/B i zachowaniu bezpiecznej drogi
   powrotu do obecnego toru.

W interfejsie wartość modelu pozostaje liczbą, lecz każda pozycja prędkości ma
jawny tekst dla NVDA: `1,00x, prędkość normalna`, wartości mniejsze —
`wolniej`, a większe — `szybciej`. Lista lub pole wyboru prędkości podlega
testom początkowego zaznaczenia, strzałek, Zapisz, Anuluj, powrotu fokusu i
ponownego otwarcia; nie może wypowiadać typu obiektu ani surowego
mnożnika bez znaczenia.

## 9. Obowiązkowe testy odbioru

- początkowy fokus każdej nowej listy, strzałki, wielokrotny wybór i filtr;
- pierwsza pozycja każdej listy oraz brak wypowiadania typów, enumów i ID;
- `NVDA+strzałka w górę` na różnych kontrolkach oraz osobno `NVDA+End`;
- lewa strzałka na pliku, stacji, folderze, elemencie zdalnym i pozycji bez
  dodatkowych danych;
- Enter, Spacja, Escape, Zapisz i Anuluj oraz powrót fokusu;
- wielokrotne otwieranie dialogu skrótów, zmiana profilu i konflikt klawisza;
- globalny gest dodatku z AMC aktywnym, zminimalizowanym i zamkniętym;
- zgłoszenie bez logu, z logiem, anulowane i nieudane sieciowo;
- aktualizacja przy bezczynności, odtwarzaniu, pauzie, nagrywaniu i odmowie
  zapisu stanu;
- próba na starym kodzie lub kontrolna mutacja musi wykazać, że test wykrywa
  właściwy błąd.

Test obiektu UIA lub modelu nie zastępuje zapisu rzeczywistej mowy NVDA.

## 10. Kolejność wdrożenia

1. Odzyskać z Hermesa pełne źródła portu, testy i projekt hosta.
2. Umieścić odtwarzalny port w głównym repozytorium na osobnej gałęzi.
3. Odtworzyć zielony stan testów prototypu i żywy pomiar NVDA.
4. Domknąć powłokę wxPython: lista, odtwarzacz, pasek stanu i fokus.
5. Przygotować odsłuch i pomiary SoundTouch, `rodio-wsola`, Google Speedy oraz
   Signalsmith Stretch; zmianę silnika prowadzić osobno od migracji interfejsu
   i nie kopiować kodu FastPlay bez wyjaśnienia licencji całego projektu.
6. Przenieść profile klawiatury i edytor skrótów.
7. Podłączyć dostępne okna aktualizacji i Sygnalisty.
8. Przenosić kolejne sesje przez istniejący host: najpierw mniejszy zakres
   TIDAL Desktop, następnie rozbudowany Sonos, bez utraty ich testów i
   zabezpieczeń.
9. Usuwać WPF dopiero po potwierdzeniu pełnej równoważności danej funkcji.

EdSharp NG pozostaje osobnym projektem i osobnym repozytorium. Możemy rozwijać
go równolegle i w przyszłości podłączyć w nim Sygnalistę, ale nie mieszamy jego
kodu, wydań, zgłoszeń ani stanu użytkownika z AMC.
