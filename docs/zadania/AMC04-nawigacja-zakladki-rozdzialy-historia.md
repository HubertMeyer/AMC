# AMC04 — zakładki, rozdziały i historia nawigacji

- Status: **Rozdziały podcastów oraz zakładki i rozdziały Spotify są
  zweryfikowane automatycznie; czekają na zbiorczą instalację AMC Test i
  ręczny odbiór NVDA**
- Data rozpoczęcia w AMC Test: 2026-10-19
- Repozytorium wykonawcze: `D:\Projekty Codex\AMC - integracja wxPython`
- Materiał historyczny, tylko do odczytu:
  - `D:\Projekty Codex\Accessible Multimedia Controller\AMC03_AUDYT_SKROTOW_2026-10-18.md`
  - `D:\Projekty Codex\Accessible Multimedia Controller\AMC04_REALIZACJA_ETAP_A_2026-10-18.md`

## Zakres zakończonego etapu

W bieżącym AMC Test rozdzielono cztery niezależne pojęcia: zakładki,
zakładki nazwane, rozdziały oraz historię widoków. Dodano również nawigację po
historii odtwarzanych elementów. Polecenia klawiatury, menu Odtwarzanie i Widok,
Pomoc klawiatury `Ctrl+F1`, pełny spis skrótów, paleta `Ctrl+Shift+K` i most
poleceń NVDA prowadzą do tych samych akcji i są filtrowane przez bieżącą sesję
oraz stan odtwarzacza.

Zakładki i rozdziały są zapisywane tylko dla sesji z trwałym identyfikatorem
materiału i znaną osią czasu: Pliki lokalne, Podcasty i YouTube oraz Spotify.
Żądanie przekazuje identyfikator sesji jawnie, więc film YouTube albo odcinek
Spotify nie może zostać omyłkowo zapisany jako lokalny plik. TIDAL, WiiM i
Sonos nie otrzymały pozornych zakładek.

## Materiał do dokumentacji użytkownika

W otwartym odtwarzaczu Plików lokalnych, Podcastów i YouTube albo Spotify
działają:

- `B` — dodaje szybką zakładkę w bieżącym miejscu;
- `Ctrl+Shift+B` — pyta o nazwę i dodaje nazwaną zakładkę;
- `Shift+Page Up` oraz `Shift+Page Down` — przechodzą po wszystkich zakładkach;
- `Ctrl+Shift+Page Up` oraz `Ctrl+Shift+Page Down` — przechodzą tylko po
  zakładkach nazwanych;
- `Ctrl+Shift+strzałka w lewo` oraz `Ctrl+Shift+strzałka w prawo` — przechodzą
  po rzeczywistych rozdziałach materiału;
- `Ctrl+Alt+Page Up` oraz `Ctrl+Alt+Page Down` — zgodne skróty alternatywne do
  poprzedniego i następnego rozdziału;
- `Ctrl+Alt+B` — otwiera listę rozdziałów, wybiera rozdział właściwy dla
  bieżącej pozycji i pozwala przejść do wybranego początku Enterem;
- `Ctrl+Alt+Shift+B` — pyta o nazwę i dodaje rozdział użytkownika;
- `Alt+strzałka w dół` — przechodzi do starszego odtwarzanego elementu;
- `Alt+strzałka w górę` — przechodzi do nowszego odtwarzanego elementu.

`Alt+strzałka w lewo` wraca do poprzedniego widoku, a `Alt+strzałka w prawo`
idzie ponownie do następnego widoku. Historia widoków zachowuje sesję, rodzaj
listy, otwarty kontener i zaznaczenie, ale nie cofa aktualnego stanu odtwarzania.
Na listach o ręcznej kolejności `Alt+strzałka w górę` i `Alt+strzałka w dół`
nadal przenoszą element; historia odtwarzania działa tymi klawiszami tylko w
odtwarzaczu.

Zakładki nazwane nadal są zakładkami użytkownika. Nie są traktowane jak
rozdziały dostawcy. Jeden punkt czasu może pełnić obie funkcje, lecz oba widoki
i oba rodzaje nawigacji pozostają oddzielne. Zbiorcza lista wszystkich zakładek
pozostaje pod `Ctrl+B`; „Zakładki zaznaczonego” pozostają pozycją menu i nie
zajmują już `Ctrl+Shift+B`.

Przykładowe krótkie komunikaty NVDA to nazwa i czas znalezionej zakładki lub
rozdziału, „Brak następnej nazwanej zakładki w tym materiale”, „Brak poprzedniego
rozdziału”, „Brak wcześniejszego widoku” i „Ten materiał nie ma rozdziałów”.
Okna nazwy zakładki i rozdziału oraz lista rozdziałów otrzymują wyłącznie
użytkowe etykiety; nie ujawniają nazw klas, identyfikatorów ani reprezentacji
obiektu.

## Uzasadnienie i decyzje

- Zakładka nazwana jest ręcznie opisanym punktem użytkownika. Rozdział jest
  strukturą materiału pochodzącą od dostawcy albo świadomie utworzoną jako
  rozdział. Wspólna tabela zapisu nie oznacza wspólnej funkcji w interfejsie.
- Nawigacja po widokach i nawigacja po odtwarzanych elementach dostały osobne
  osie klawiszy, aby `Alt+lewo/prawo` nigdy nie zmieniało materiału.
- Migawka historii widoku nie zawiera żywego tytułu, pozycji ani stanu
  odtwarzania. Powrót do listy nie może cofnąć transportu.
- Host C# otrzymuje jawne `files`, `podcasts` albo `spotify` przy zapisie i
  odczycie.
  To usuwa zgadywanie rodzaju sesji z typu elementu i obejmuje także filmy
  YouTube odtwarzane w sesji Podcasty i YouTube.
- Lista rozdziałów składa etykiety z nazwy i czasu. Modelowe identyfikatory
  rozdziałów nie są przekazywane do nazwy dostępnej kontrolki.

### Korekta użytkownika z 2026-10-18

Ta decyzja zastępuje wcześniejsze utożsamienie nazwanych zakładek z rozdziałami
oraz wcześniejsze zajęcie `Ctrl+Shift+B` na liście przez „Zakładki
zaznaczonego”. `Ctrl+Shift+B` służy teraz wyłącznie dodaniu nazwanej zakładki w
odtwarzaczu. Rozdziały mają `Ctrl+Shift+lewo/prawo`, a nazwane zakładki
`Ctrl+Shift+Page Up/Page Down`.

Ta sama korekta zastępuje pomocniczy skrót `Shift+B` dla nazwanej zakładki
trwającego nagrania radiowego. W aktywnym kontekście nagrywania obowiązują
spójnie `B` oraz `Ctrl+Shift+B`.

### Korekta użytkownika z 2026-10-22 — hierarchia bieżącego produktu

AMC Test, nazywany także AMC Python, jest główną i bieżącą wersją rozwijanego
produktu. Nie jest bocznym repozytorium ani pomocniczą odmianą starego AMC.
Publiczny instalator powstaje z tej samej, wcześniej sprawdzonej wersji AMC
Test, z publicznym profilem możliwości. Stare AMC/WPF pozostaje wyłącznie
materiałem archiwalnym i nie jest rozwijaną linią produktu. Ta korekta zastępuje
wcześniejsze sformułowania, które mogły sugerować, że AMC Test jest tylko
równoległym albo podrzędnym interfejsem.

Numer `alpha.43x` może być mylony z historyczną linią starego AMC. Do osobnej
decyzji wydaniowej obowiązuje korekta użytkownika z 22.10.2026: nazwa widoczna
ma mieć wyłącznie postać `AMC Test — dd.mm.rrrr, gg:mm` albo
`AMC Public — dd.mm.rrrr, gg:mm`. Przyszły instalator ma nazwę w rodzaju
`AMC-Public-2026-10-22-2125.exe`. Numery `alpha`, commit i identyfikator paczki
pozostają danymi technicznymi. Ta decyzja zastępuje wcześniejszą propozycję
widocznych nazw z numerem wersji i słowem „kompilacja”.

## Audyt i naprawa z 2026-10-22

Audyt rozdzielił obecność skrótu od dostępności danych, po których skrót ma
nawigować. `Ctrl+Shift+lewo/prawo` był zarejestrowany w skrótach, menu, pomocy,
palecie i moście NVDA, a LiteHost wykonywał `chapter.navigate`. Host odczytywał
jednak wyłącznie już istniejące wpisy tabeli rozdziałów. Bieżący AMC Test nie
uruchamiał przy tym poleceniu pobrania Podcasting 2.0 JSON, ponownego odtworzenia
rozdziałów ze znacznika czasu w opisie RSS ani zapasowego odczytu strony
odcinka. Dlatego prawidłowo rozpoznany skrót kończył się komunikatem o braku
rozdziału.

Potwierdzono to na rzeczywistych danych profilu bez ich zmieniania:

- aktualny odcinek TyfloPodcast miał bezpieczny adres JSON dostawcy i zero
  rozdziałów w indeksie AMC; ten sam publiczny plik zwrócił `17` poprawnie
  sparsowanych rozdziałów, począwszy od „Intro”;
- bieżące odcinki „Bo czemu nie?” oraz „Kawa. Bo czemu nie?” miały
  `HasFeedChapters = true`, celową sekcję „Rozdziały” w opisie, na przykład
  `(00:00:00) PARTNERZY`, i zero rozdziałów w indeksie AMC.

Naprawa dodaje wewnętrzne `chapter.prepare`, wykonywane poza szeregową kolejką
transportu. Przed listą albo nawigacją rozdziałów w sesji Podcasty i YouTube
host kolejno:

1. pobiera zapisany plik Podcasting 2.0 JSON, jeżeli jest nowy albo indeks
   wymaga odbudowania;
2. przy braku wyniku parsuje zapisany opis RSS, także format w nawiasach używany
   przez „Bo czemu nie?”;
3. przy dalszym braku wyniku sprawdza publiczną stronę bieżącego odcinka;
4. zapisuje wyłącznie rozdziały bieżącego materiału przez wspólny
   `ChapterIndex`, po czym zwykłe `chapter.navigate` wykonuje przewinięcie.

Pobieranie nie blokuje pauzy, statusu ani nagrywania. Przy pierwszym
sprawdzeniu danego odcinka NVDA dostaje komunikat „Sprawdzanie rozdziałów”;
kolejne przejścia nie powtarzają tego komunikatu. Modelowe adresy i
identyfikatory nie trafiają do nazw kontrolek ani komunikatów NVDA.

### Rozszerzenie Spotify i Librespot — 22.10.2026

Przed tą zmianą Librespot potrafił przewijać bieżący utwór albo odcinek, lecz
warstwa zakładek i rozdziałów odrzucała sesję Spotify. Wspólny model poleceń
nie pokazywał więc w tej sesji `B`, zakładek nazwanych, listy rozdziałów ani
`Ctrl+Shift+lewo/prawo`.

Po zmianie bieżący utwór lub odcinek Spotify otrzymuje trwały klucz zapisu
`spotify:track:…` albo `spotify:episode:…`, niezależny od tego, z której
playlisty został uruchomiony. Zakładki, rozdziały użytkownika i ich nawigacja
korzystają z rzeczywistej pozycji Librespot i z tego samego magazynu co
pozostałe sesje. Skróty, menu, `Ctrl+F1`, pełna pomoc oraz paleta poleceń są
włączane przez ten sam model możliwości.

Oficjalny obiekt odcinka Spotify nie zawiera osobnej listy rozdziałów podcastu.
AMC pobiera zatem opis bieżącego odcinka i, jeśli wydawca umieścił w nim co
najmniej dwa poprawne znaczniki czasu, buduje z nich rozdziały. Brak sieci albo
brak takich znaczników nie blokuje rozdziałów dodanych wcześniej przez
użytkownika. Automatyczny import Podcasting 2.0 JSON i rozdziałów z kanału RSS
pozostaje właściwością sesji Podcasty i YouTube; Spotify nie udostępnia AMC
adresu RSS ani podcastowego JSON-a rozdziałów.

Osobno sprawdzono publiczną paczkę `alpha.433` utworzoną 2026-10-21 około
21:25. Zawiera skrót `B`, wspólną akcję `ADD_BOOKMARK`, obsługę w GUI oraz
możliwości `bookmarks` i `chapters`. Wywołanie z kodu zainstalowanej paczki
publicznej poprawnie przeszło do wspólnego zapisu zakładki. Nie znaleziono więc
dowodu, że wdrożenie publicznego instalatora pominęło kod zakładek. Ręczny
odbiór klawisza `B` z NVDA w tej konkretnej instalacji nadal jest potrzebny,
bo przyczyna zgłoszenia może zależeć od fokusu albo uruchomionej kopii.

## Zmienione miejsca

- `src/AccessibleMediaController.Core/Configuration/BookmarkIndex.cs`
- `src/AccessibleMediaController.Core/Configuration/PodcastLibraryDatabase.cs`
- `src/AccessibleMediaController.Core/Configuration/PodcastLibraryMutationStore.cs`
- `src/AccessibleMediaController.LiteHost/LiteBookmarkStore.cs`
- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `src/AccessibleMediaController.LiteHost/LitePodcastChapterCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/LitePodcastProgressStore.cs`
- `src/AccessibleMediaController.LiteHost/LiteSpotifyCatalogCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/LiteSpotifyPlaybackCoordinator.cs`
- `src/AccessibleMediaController.LiteHost/Program.cs`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/navigation.py`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/nvda_bridge.py`
- testy rdzenia, hosta, skrótów, menu, mostu NVDA i GUI wymienione w commicie.
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/PodcastChapterCoordinatorTests.cs`
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/SpotifyCatalogContractTests.cs`

## Testy i wynik

- Ukierunkowane testy skrótów, menu, zakładek, mostu NVDA i nagrywania:
  `165 passed`.
- Dodatkowa regresja historii widoków i lewej strzałki: `65 passed`.
- Testy po jawnym dodaniu identyfikatora sesji do zapisu zakładki:
  `16 passed`.
- Końcowa regresja menu, etykiet i pomocy: `85 passed`.
- Pełny zestaw wxPython: `1760 passed, 110 skipped, 11 subtests passed`.
- Testy protokołu LiteHost po kompilacji Release: wszystkie zestawy przeszły,
  `20` zestawów.
- Testy Core Smoke po kompilacji Release: kod wyjścia `0`, w tym trwałe
  zakładki i chronologiczne rozdziały.
- `git diff --check`: bez błędów białych znaków; ostrzeżenia dotyczyły tylko
  repozytoryjnej konwersji końców linii LF/CRLF.

Po połączeniu z AMC05 i AMC13 wykonano pełną regresję wxPython: **1770
zaliczonych, 110 pominiętych i 11 podtestów zaliczonych** w 85,32 s. Następnie
utworzono paczkę 1660 plików, zweryfikowano manifest i sumy SHA-256,
zainstalowano ją oraz uruchomiono proces z tytułem „AMC Test”. Instalacja nie
jest jeszcze dowodem ręcznego odbioru z NVDA.

Naprawa z 2026-10-22:

- testy magazynu zakładek, postępu podcastu i przygotowania rozdziałów:
  wszystkie `3` zestawy przeszły;
- pełny LiteHost ProtocolTests po kompilacji Release: wszystkie `27` zestawów
  przeszło poza piaskownicą; wcześniejsze błędy atomowych operacji plikowych w
  piaskownicy były ograniczeniem uprawnień testu, nie awarią produktu;
- kompilacja LiteHost Release: sukces, `0` ostrzeżeń i `0` błędów;
- ukierunkowany kontrakt Python skrótów, pomocy, protokołu i przygotowania
  źródeł przed nawigacją: `6` testów zaliczonych;
- rzeczywisty `PodcastChapterClient` pobrał i sparsował `17` rozdziałów
  aktualnego przykładu TyfloPodcast;
- nie zbudowano instalatora, nie podmieniono stałej instalacji AMC Test ani
  AMC Public i nie uruchomiono nowej kompilacji.

Ponowna weryfikacja z 2026-10-22 po pytaniu użytkownika o stan rozdziałów:

- ukierunkowane testy bieżących źródeł dla rozdziałów, zakładek, protokołu,
  menu i pomocy: **17 zaliczonych** w 2,35 s;
- zainstalowany AMC Test pochodzi z paczki utworzonej 21.10.2026 o 21:43 czasu
  polskiego, rewizja techniczna `20a3ca68dd2a078554821e9a2bdea21cd478a88e`;
- zainstalowany AMC Public pochodzi z paczki utworzonej 21.10.2026 o 21:21
  czasu polskiego, rewizja techniczna
  `8ab21a25bb61a0807fc4870b558b39a1eeb93c57`;
- bezokienny test kodu dokładnie z obu zainstalowanych paczek potwierdził
  mapowanie `B` na dodanie zakładki oraz `Ctrl+Shift+lewo/prawo` na nawigację
  rozdziałów, lecz w obu paczkach wykazał brak nowej operacji
  `prepare_chapters`;
- wniosek: publiczny instalator nie pominął obsługi `B`, natomiast obie
  zainstalowane kopie są starsze od naprawy przygotowywania rozdziałów na
  żądanie. Dla odcinka bez wcześniej zbudowanego indeksu skrót rozdziałów może
  więc nadal kończyć się komunikatem o braku rozdziału;
- w tym sprawdzeniu nie uruchomiono aplikacji, nie zbudowano paczki ani
  instalatora i nie zmieniono żadnej zainstalowanej kopii.

Weryfikacja rozszerzenia Spotify/Librespot z 2026-10-22:

- ukierunkowane testy skrótów, menu, pomocy, zakładek i rozdziałów:
  **18 zaliczonych**;
- test opisu odcinka potwierdził utworzenie dwóch rozdziałów z jednego
  bezpiecznego odczytu katalogu Spotify, bez mutacji konta;
- pełne **27 zestawów** protokołu LiteHost przeszło po kompilacji;
- pełna regresja wxPython: **1978 zaliczonych, 110 pominiętych i 11 podtestów
  zaliczonych** w 133,05 s;
- testy launchera i aktualizatora: **30 z 30 zaliczonych**;
- na tym etapie źródła są gotowe do wspólnej promocji AMC Test razem z
  opcjami sesji i pozostałymi dzisiejszymi zmianami; instalacja jest osobnym
  następnym krokiem.

## Szkic instrukcji i changelogu do zatwierdzenia

Szkic instrukcji użytkownika: w odtwarzaczu Podcastów i YouTube naciśnij
`Ctrl+Shift+strzałkę w lewo` albo `Ctrl+Shift+strzałkę w prawo`, aby przejść do
poprzedniego lub następnego rozdziału. To samo działa w odtwarzaczu Spotify.
Przy pierwszym użyciu dla danego odcinka AMC może przez chwilę sprawdzać spis
rozdziałów dostawcy, opis RSS, stronę odcinka albo — w Spotify — znaczniki czasu
w opisie. Kolejne użycia korzystają z zapisanego indeksu. `Ctrl+Alt+B` otwiera
pełną listę rozdziałów. `B` dodaje zakładkę w bieżącym miejscu i nie jest
skrótem rozdziałów.

Szkic changelogu: naprawiono nawigację po rozdziałach podcastów, gdy skróty
były dostępne, lecz bieżący odcinek nie miał jeszcze zaimportowanego indeksu.
AMC przygotowuje teraz na żądanie rozdziały Podcasting 2.0 JSON, znaczniki
czasu w opisie RSS i spis ze strony odcinka. Potwierdzono działanie parsera na
TyfloPodcast oraz formacie „Bo czemu nie?”. Dodano zakładki i rozdziały
użytkownika dla odtwarzania Spotify oraz rozdziały z oznaczeń czasu w opisie
odcinka Spotify. Tekst jest szkicem i nie został opublikowany.

## Znane ograniczenia

- Ręczny odbiór na żywym NVDA pozostaje do wykonania po instalacji nowszej
  paczki: początkowy fokus listy rozdziałów, strzałki, Enter, Escape, powrót
  fokusu, ponowne otwarcie oraz kolejność komunikatów.
- Zakładki i rozdziały nie są reklamowane dla TIDAL, WiiM i Sonosa, ponieważ
  te sesje nie zapewniają w tym kontrakcie wspólnej trwałej osi czasu.
- Spotify obsługuje zakładki i ręczne rozdziały dla utworów oraz odcinków.
  Automatyczne rozdziały odcinka powstają tylko wtedy, gdy jego opis zawiera
  co najmniej dwa poprawne znaczniki czasu; oficjalne API nie przekazuje
  osobnego spisu rozdziałów podcastu.
- Rozdziały dostawcy są teraz przygotowywane na żądanie dla podcastów z JSON,
  opisu RSS albo strony odcinka. Odcinek bez danych rozdziałów nadal jest
  komunikowany wprost.
- Ręczny odbiór z NVDA pozostaje osobnym etapem mimo poprawnej instalacji.

## Wersja i commit

- Implementacja i testy: `b1786e1a` —
  `feat(amc04): ujednolic nawigacje zakladek i rozdzialow`.
- Dokumentacja zadania: commit następujący po commicie implementacji.
- Kompilacja: projekty testowe Core i LiteHost, konfiguracja Release — sukces.
- Instalacja: `2026.10.19-ca7dfa167728317728be534da7a71f8484ebe573-b9d47b3d`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonano; brak wysyłania do GitHuba i brak wydania publicznego.
- Naprawa rozdziałów RSS/Podcasting 2.0 oraz rozszerzenie Spotify z 2026-10-22:
  zmiany robocze na bazie `b9cedf7641c2`; identyfikator wspólnego commitu i
  paczki zostanie dopisany po zakończeniu promocji AMC Test. Bez publikacji.
