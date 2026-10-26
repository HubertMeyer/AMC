# AMC — interakcje z rozpoznanymi utworami

Data decyzji i realizacji źródłowej: 2026-10-26.

## Zachowanie użytkowe

Okno **Rozpoznane utwory**, otwierane przez `Ctrl+Alt+S`, zachowuje krótki
wiersz listy: tytuł, wykonawca, stacja i czas. Pełny wielowierszowy opis jest
kopiowany dopiero przez `Ctrl+C`; nie jest odczytywany podczas zwykłego
chodzenia strzałkami.

- `Enter` wyszukuje na żądanie i odtwarza utwór w domyślnej usłudze.
- `Ctrl+Enter` otwiera album w domyślnej usłudze i ustawia fokus na
  rozpoznanym utworze.
- `Strzałka w prawo` otwiera krótką listę najważniejszych działań: wykonawcę
  i album w usłudze domyślnej, pokazanie utworu Spotify w AMC i otwarcie go w
  oryginalnej aplikacji, utwór Apple Music oraz pokazanie utworu TIDAL w AMC i
  odtworzenie go w oryginalnej aplikacji.
  Niedostępna, niezalogowana usługa nie pojawia się na liście.
- Menu kontekstowe jest powierzchnią pełną. Poza Enterem, `Ctrl+Enter`,
  kopiowaniem, zmianą kolejności, eksportem i usuwaniem zawiera rozwijane
  `Usługi, łącza i powiązania`: wszystkie warianty Spotify i TIDAL, dokładny
  utwór i album Apple Music, wyszukiwanie Apple Music, YouTube Music, Discogs,
  MusicBrainz oraz wynik Shazama, jeśli istnieje.
- `Strzałka w lewo` odczytuje skrócone informacje o bieżącym rekordzie.
- `Ctrl+C` kopiuje pełny opis wraz z publicznymi łączami lub wyszukiwaniami do
  Apple Music, Spotify, TIDAL, YouTube Music, Discogs i MusicBrainz. Ten tekst
  nie jest odczytywany podczas chodzenia po liście. `Ctrl+Shift+C` kopiuje
  dokładne łącze do utworu w domyślnej usłudze.
- W menu spod prawej strzałki `Ctrl+C` kopiuje nazwę pozycji, a
  `Ctrl+Shift+C` jej łącze. Dla albumu jest to łącze do albumu.
- `Alt+Strzałka w górę` i `Alt+Strzałka w dół` zmieniają trwałą kolejność.
  Komunikat NVDA ma formę `Nad …` albo `Pod …`.

Domyślną usługę wybiera się w **Ustawienia > Radio i nagrywanie >
Rozpoznawanie utworów**. Dostępne wartości to Spotify i TIDAL. Pole ma jawne
nazwy UI Automation dla pola oraz obu wartości.

## Integracja i pobieranie danych

Historia nie odpytuje usług podczas wyświetlania ani podczas chodzenia po
liście. Pierwsze jawne działanie wyszukuje katalog zalogowanej usługi, ocenia
zgodność tytułu i wykonawcy i odrzuca niepewne trafienie. Nie wolno przyjąć
pierwszego wyniku tylko dlatego, że jest pierwszy.

Po pewnym trafieniu rekord przechowuje wyłącznie niesekretne, stabilne
identyfikatory i publiczne łącza do utworu, albumu i wykonawcy. Tokeny i surowe
odpowiedzi usług nie trafiają do historii. Kolejne kopiowanie lub otwieranie
korzysta z cache bez ponownego wyszukiwania. Spotify i TIDAL pozostają
oddzielnymi trafieniami.

W Spotify album otwiera się w przeglądaniu AMC. W TIDAL album otwiera się w
przeglądaniu AMC, a odtwarzanie utworu korzysta z istniejącego sterowania
oryginalną aplikacją TIDAL. YouTube Music, Discogs, MusicBrainz i wynik Shazama
są przekazywane do zwykłej przeglądarki dopiero po zamknięciu okna modalnego.

Spotify ma dodatkowe pozycje otwierające dokładny utwór albo album przez
identyfikator obsługiwany przez oryginalną aplikację. `Ctrl+Shift+C` na takiej
pozycji kopiuje jednak publiczne łącze HTTPS, a nie techniczny identyfikator
aplikacji. Gdy system nie potrafi otworzyć aplikacji Spotify, AMC przechodzi do
publicznego łącza.

Korekta użytkownika z 2026-10-26 zastępuje wcześniejsze założenie, że TIDAL ma
osobną drogę odtwarzania `w AMC`. Pozycje zostały nazwane `pokaż utwór w AMC`:
przechodzą do odpowiedniej sesji Spotify albo TIDAL, ustawiają fokus na utworze
i niczego nie odtwarzają. Osobne pozycje uruchamiają oryginalną aplikację;
odtwarzanie TIDAL ostatecznie odbywa się przez oryginalny TIDAL.

## Apple Music — korekta decyzji z 2026-10-26

Ta decyzja zastępuje zapis z 2026-10-25 wykluczający Apple Music z menu.
Apple Music wraca wyłącznie jako integracja publicznych łączy; nie staje się
domyślną usługą rozpoznawania i nie wymaga konta, Apple ID, developer tokenu ani
Music User Tokenu.

Menu spod prawej strzałki zawiera:

- `Apple Music — utwór (strona lub aplikacja)`;
- album rozpoznanego utworu w Apple Music;
- `Apple Music — wyszukaj w przeglądarce` jako zawsze dostępny wariant
  awaryjny.

Dokładny utwór i album są wyszukiwane dopiero po Enterze albo
`Ctrl+Shift+C`. AMC używa publicznego katalogu, ocenia zgodność tytułu i
wykonawcy, a pewne trafienie zapisuje w tym samym niesekretnym cache co inne
usługi. Enter przekazuje publiczne łącze HTTPS do systemu. Może ono otworzyć
stronę Apple Music albo zostać przekazane do zainstalowanej aplikacji, ale AMC
nie obiecuje bezpośredniego uruchomienia aplikacji na każdym Windowsie, bo Apple
nie dokumentuje stabilnego schematu desktopowego dla takiego wywołania.
`Ctrl+Shift+C` kopiuje dokładne publiczne łącze utworu lub albumu. Wariant
`wyszukaj w przeglądarce` nie odpytuje katalogu i od razu otwiera adres
wyszukiwania.

## Dostępność i wspólny model poleceń

Nazwy, skróty i opisy lokalnych poleceń mają jedno źródło używane przez
obsługę klawiatury, instrukcję okna, pełną pomoc i testy parytetu. Każdy wiersz
oraz element menu ma jawny tekst użytkowy dla UI Automation; modele, enumy,
identyfikatory i reprezentacje obiektów nie mogą trafić do mowy NVDA. Menu
relacji ustawia fokus na pierwszej pozycji, a po anulowaniu oddaje go na
poprzedni rekord.

Prawa strzałka i menu kontekstowe nie są dwiema kopiami. Korzystają z jednego
modelu działań, ale pokazują dwie projekcje: krótką i pełną. `Ctrl+Enter` nie
otwiera aplikacji zewnętrznej: otwiera album w domyślnej usłudze wewnątrz AMC i
ustawia fokus na rozpoznanym utworze.

## Zmiany źródłowe

- model ustawienia domyślnej usługi i trwałego cache dopasowań;
- resolver Spotify/TIDAL działający na żądanie;
- publiczny resolver łączy Apple Music działający na żądanie, bez logowania;
- polityka pewnego dopasowania oraz wyboru utworu po otwarciu albumu;
- bezpieczne otwieranie utworu i albumu w oryginalnej aplikacji Spotify z
  awaryjnym przejściem do publicznego adresu;
- nowe działania i dostępne menu historii;
- zachowanie własnej kolejności historii podczas zapisu i ponownego otwarcia;
- wspólny katalog poleceń i wpisy pełnej pomocy;
- testy zapisu, dopasowania, cache, linków i etykiet dostępności.

## Dołączony zakres: strzałki w Nagrywanych i Harmonogramie

W tym samym katalogu roboczym pozostaje również wykonane zadanie dotyczące
informacji odczytywanych strzałkami podczas nagrywania:

- w widoku `Nagrywane` lewa strzałka podaje parametry odbieranego strumienia;
- prawa strzałka podaje bitrate albo format pliku, nazwę pliku i miejsce zapisu,
  na przykład `192 kb/s, plik audycja.mp3, folder domyślny`;
- przed utworzeniem pliku pojawia się użytkowy tekst `plik przygotowywany`;
- prawa strzałka w Harmonogramie używa tego samego krótkiego opisu i nie
  zaczyna od słowa `Źródło` ani adresu stacji;
- oba widoki korzystają ze wspólnego formattera tekstu, a fokus pozostaje na
  liście.

Pełny zapis zachowania i wcześniejszych wyników testów znajduje się w
`AMC_NAGRYWANE_PRAWA_STRZALKA_2026-10-26.md`.

## Stan weryfikacji

- Zmiany źródłowe: przygotowane wspólnie z obsługą strzałek w nagraniach i
  harmonogramach.
- Kompilacja kontrolna całego rozwiązania: powodzenie, 0 ostrzeżeń i 0 błędów.
- Pełne testy Core: powodzenie.
- Izolowany kontrakt Windows historii rozpoznawania: powodzenie; obejmuje
  ustawienia, skróty, krótki i pełny wariant menu, fokus, cache oraz publiczne
  łącza Spotify, TIDAL i Apple Music.
- Kontrola po połączeniu obu zadań: `--active-recording-output` zaliczony, a
  `--schedule-copy` zakończony wynikiem 9/9. Pierwsze uruchomienia w ograniczonej
  piaskownicy nie mogły zapisać stanu tymczasowego; te same testy uruchomione
  poza piaskownicą przeszły bez zmiany kodu.
- Testy Frontier Smart: 13/13; Frontier Smart Windows: 6/6.
- Rzeczywiste testy schowka: powodzenie dla tekstu, łączy i FileDrop. Przy tej
  okazji standardowe formaty schowka odłączono od niebezpiecznej ścieżki
  BinaryFormatter, a testowy zapis znacznika otrzymał ponawianie przy czasowym
  zajęciu schowka.
- Automatyczne testy rzeczywistych okien WPF objęły fokus początkowy, Escape,
  powrót fokusu i ponowne otwarcie.
- Monolityczny zestaw Windows: funkcjonalne asercje rozpoznawania, fokusu,
  Escape, ponownego otwarcia i schowka przeszły, lecz wielogodzinny proces WPF
  nie kończy się stabilnie na tym komputerze. Po wielu setkach tworzonych okien
  runtime kończy proces w `HwndSubclass` podczas sprzątania zasobów. Nie jest to
  zielony pełny przebieg i nie jest tak przedstawiany.
- Ręczny odsłuch żywego NVDA: niewykonany, aby nie uruchamiać równolegle drugiej
  aplikacji i nie zakłócać działającego AMC Python.

## Korekta obsługi `Ctrl+Alt+S` z 26 października 2026 r.

Po zgłoszeniu użytkownika sprawdzono również fizyczne rozpoznawanie skrótu.
WPF przekazuje gest zawierający Alt jako `Key.System`, a literę umieszcza w
`SystemKey`. Odtwarzacz uwzględniał tę regułę, lecz główna lista Radia miała
osobne porównanie z surowym `e.Key`, przez co `Ctrl+Alt+S` mógł tam nie otworzyć
historii.

Skróty `S`, `Shift+S`, `Ctrl+Alt+S` oraz `Ctrl+Alt+Shift+S` mają teraz jeden
router dla głównej listy, odtwarzacza i pomocy klawiatury. Test regresji
potwierdza, że `Ctrl+Alt+S` otwiera historię poza odtwarzaczem Radia,
`Ctrl+Alt+Shift+S` przełącza oznajmianie, zwykłe `S` działa tylko w
odtwarzaczu, a inne sesje nie przejmują skrótu. Izolowany test
`--recognition-history-ui` oraz pełna kompilacja Release zakończyły się
powodzeniem.

## Plan testu rzeczywistego

Po bezpiecznym zbudowaniu sprawdzić z NVDA: fokus początkowy, oba warianty
domyślnej usługi, pierwsze wyszukiwanie i ponowne użycie cache, Enter,
Ctrl+Enter z fokusem na utworze albumu, prawe/lewe strzałki, oba skróty
kopiowania, ruch jednego i wielu zaznaczeń, anulowanie menu, powrót fokusu,
ponowne otwarcie okna oraz komunikaty braku logowania i braku pewnego trafienia.
Osobno sprawdzić trzy pozycje Apple Music: dokładny utwór, dokładny album oraz
wyszukiwanie; dla dwóch pierwszych sprawdzić Enter, `Ctrl+Shift+C`, cache i
zachowanie z zainstalowaną oraz niezainstalowaną aplikacją Apple Music. W
Spotify sprawdzić oryginalną aplikację i awaryjne publiczne łącze.

## Roboczy changelog do zatwierdzenia

- Rozpoznane utwory otrzymały działania Apple Music niewymagające logowania:
  dokładny utwór, album i wyszukiwanie w przeglądarce.
- Spotify może otworzyć rozpoznany utwór lub jego album w oryginalnej
  aplikacji; TIDAL nadal odtwarza rozpoznany utwór w oryginalnej aplikacji.
- `Ctrl+Shift+C` w menu działań kopiuje publiczne łącze wybranej pozycji,
  również dla Apple Music i albumów.
- W widoku `Nagrywane` lewa strzałka opisuje strumień, a prawa parametry i
  miejsce zapisywanego pliku; Harmonogram używa tego samego krótkiego opisu.
