# Plan zadań AMC od AMC01

Data ustalenia: 18 października 2026 r.

Kanoniczny projekt: `D:\Projekty Codex\Accessible Multimedia Controller`

## Stan realizacji

- AMC01: etap A przygotowany; kod i test źródłowy czekają na Bramkę 1.
- AMC02: etap A przygotowany; kod, testy źródłowe, pomoc i paleta czekają na Bramkę 1.
- AMC03: audyt i tabela docelowa zatwierdzone z korektą: `Ctrl+Shift+Page Up/Down` oznacza nazwane zakładki, nie rozdziały.
- AMC04: etap A rozpoczęty; wdrożono źródłowo osobne polecenia nawigacji po nazwanych zakładkach, routing klawiatury, pomoc `Ctrl+F1`, paletę `Ctrl+Shift+K`, menu i testy źródłowe. Bez kompilacji i uruchamiania.
- AMC05: wykonano audyt źródłowy i zatwierdzono specyfikację poziomu A do późniejszego wdrożenia produkcyjnego. Stan odtwarzania ma być osobną dekoracją jawnej etykiety wiersza, bez przestawiania fokusa i bez fałszywego oznaczania kontenerów. Szczegóły: `AMC05_ODTWARZANY_ELEMENT_NA_LISTACH_2026-10-18.md`.
- AMC06: wykonano audyt źródłowy i zatwierdzono rozszerzoną specyfikację poziomu A. Obejmuje dopasowanie dnia do daty, trwałą lokalną godzinę cyklu bez dryfu po zmianie czasu oraz pełne uporządkowanie wpisywania: segmenty daty i godziny obsługiwane lewo/prawo, góra/dół i cyframi, a także osobne pola długości, w których puste godziny oznaczają zero i samo `25` minut zapisuje 25 minut. Szczegóły: `AMC06_HARMONOGRAMY_DATA_CZAS_DZIEN_2026-10-18.md`.
- AMC07: wycofano z bieżącej serii i z Bramy 3. Obsługę obrazu przeniesiono do długoterminowego AMC15, aby nie ryzykować stabilności lokalnego audio, Radia, Time Shiftu i YouTube na żywo. Historyczny odsyłacz: `AMC07_OBRAZ_WIDEO_ALT_V_2026-10-18.md`.
- AMC08: wykonano audyt źródłowy i oficjalnego Spotify Web API oraz przygotowano specyfikację poziomu A. Użytkownik zatwierdził wdrożenie tej funkcji w `AMC Test`, niezależnie od ukrycia Spotify w profilu publicznym. `Ctrl+P` i `Ctrl+Shift+P` zachowają wspólną intencję między sesjami, ale w Spotify będą obsługiwać natywne playlisty Spotify. `Ctrl+Shift+P` pozwoli wybrać istniejącą albo utworzyć nową playlistę, bez osobnego `Alt+Shift+P`. Szczegóły: `AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.
- AMC09: wykonano audyt Menedżera sesji oraz pierwszego logowania. Zatwierdzono zwartą numerację aktywnych sesji: dodanie dopisuje na końcu, usunięcie zagęszcza numery, a przeniesienie zmienia `Ctrl+1–9`. Zatwierdzono też stałą nazwę `Radio`. WiiM należy do wydania publicznego, Sonos jest celem publicznym po zamknięciu bramy brokera, a Spotify i TIDAL pozostają wyłącznie w `AMC Test`. Szczegóły: `AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.
- AMC10: wykonano audyt istniejących adapterów Sonos/WiiM i przygotowano plan prostego uruchomienia przez wspólny Menedżer sesji. WiiM zatwierdzono publicznie. Sonos ma przejść przez publiczny broker HTTPS, odbiór z zewnętrznym kontem oraz kontrolowany etap `Sonos — wersja próbna` dla chętnych, a następnie stać się opcjonalną sesją publiczną. Nie scala się protokołów; wspólne będą stany, konfiguracja i bezpieczne wejście, a funkcje urządzeń pozostaną właściwe dla każdego adaptera. Szczegóły: `AMC10_SONOS_WIIM_URUCHOMIENIE_I_UJEDNOLICENIE_2026-10-18.md`.
- AMC12: zatwierdzono jeden kod i dwa profile wydania: publiczne `AMC` oraz prywatne `AMC Test`. Profile otrzymają osobne tożsamości instalacji, kanały aktualizacji i magazyny danych, lecz publiczne AMC będzie mogło bezpiecznie odświeżać zgodne dane użytkowe z `AMC Test`. Spotify nie będzie istniało w publicznym interfejsie ani pakiecie zależności do czasu osobnej decyzji po AMC16. Portable x64 oraz ARM odłożono poza bieżącą Bramę 5. Przed instalatorem powstaje aplikacyjna część AMC14, a instalator dopiero rejestruje jej sprawdzony kontrakt w Windows. Szczegóły: `AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`.
- AMC13: wykonano audyt źródłowy regresji `End` w otwartym odtwarzaczu Time Shiftu radia i przygotowano nieuruchomiony test pełnej drogi `End`/`NVDA+End`. Procentowa nawigacja cyframi `0–9` i zaznaczenie zakresu z zapisaniem jego kopii do nowego pliku pozostają osobnymi, późniejszymi rozszerzeniami. Nie planuje się destrukcyjnego wycinania bufora na żywo. Szczegóły: `AMC13_TIMESHIFT_RADIA_2026-10-18.md`.
- AMC14: wykonano wstępny audyt zadania otwierania folderów oraz integracji rozszerzeń z powłoką Windows. W źródle istnieją reguły rozszerzeń, `Otwórz w AMC`, `Dodaj do kolejki AMC`, parser argumentów i kod rejestracji per użytkownik. Zatwierdzono kolejność: najpierw działające argumenty, przekazanie do jednej instancji, kolejka, ustawienia i testy aplikacji; dopiero potem AMC12 rejestruje je przez instalator. Skróty `Ctrl+Enter` i `Ctrl+Alt+Enter` pozostają nieprzypisanymi kandydatami. Szczegóły: `AMC14_FOLDERY_I_INTEGRACJA_POWLOKI_2026-10-18.md`.
- AMC15: zapisano odroczone zadanie opcjonalnego wideo pełnoekranowego. Może rozpocząć się dopiero po AMC12, niezależnym instalatorze i stabilnym wydaniu audio. Funkcja będzie domyślnie wyłączona; TIDAL Video i transmisje YouTube traktowane jak radio nie należą do pierwszych faz. Szczegóły: `AMC15_WIDEO_PELNOEKRANOWE_PO_INSTALATORZE_2026-10-18.md`.
- AMC16: przygotowano audyt i eksperyment jednego logowania Spotify dla `AMC Test`. Librespot zostaje; porównane zostaną obecny kod `spotify.com/pair` i parowanie przez Spotify Connect w tej samej sieci. Publiczne `AMC` nie pokazuje Spotify w ogóle, dopóki funkcja nie przejdzie pełnej weryfikacji i nie otrzyma osobnej decyzji wydawniczej. Szczegóły: `AMC16_SPOTIFY_JEDNO_LOGOWANIE_LIBRESPOT_2026-10-18.md`.
- AMC17: zatwierdzono użytkowo i odłożono do późniejszej wersji po AMC12 oraz stabilnym instalatorze. `Enter` na liście `Alt+R` ma kiedyś otwierać zwykły odtwarzacz nagrywanego pliku, `End` przechodzić do jego bieżącego końca, `Escape` wracać do listy, a `Ctrl+R` bezpiecznie kończyć tylko wybrane nagranie. Podgląd ma osobne, formatowo neutralne źródło i nie może uszkodzić, przenieść ani usunąć pliku kodera. Szczegóły: `AMC17_PODGLAD_TRWAJACEGO_NAGRANIA_2026-10-18.md`.
- Bramka 1: niewykonana. Przed kompilacją i uruchomieniem trzeba potwierdzić, że AMC nie nagrywa.

## Zasady wspólne dla wszystkich etapów

1. Prace wykonujemy kolejno. Jedno zadanie ma zamknięty zakres, własne testy i notatkę z uzasadnieniem.
2. Nie uruchamiamy AMC, instalatora ani NVDA po każdej zmianie. Zmiany źródłowe i testy niewymagające działającego programu można przygotowywać wcześniej, a kompilację i próbę na żywo łączymy w bramki opisane niżej.
3. Przed kompilacją, instalacją, restartem NVDA lub uruchomieniem AMC sprawdzamy, czy AMC nie nagrywa ręcznie ani z harmonogramu. Jeżeli nie można tego wiarygodnie potwierdzić, nie zamykamy i nie zastępujemy działającej instancji.
4. Każdy nowy skrót lub polecenie trafia równocześnie do:
   - logiki polecenia i właściwej warstwy klawiatury;
   - pomocy klawiatury pod `Ctrl+F1`;
   - palety poleceń pod `Ctrl+Shift+K`;
   - menu kontekstowego tam, gdzie ma to sens;
   - instrukcji użytkownika i notatki zadania.
5. Każda zmiana listy, pola wyboru lub menu ma jawne, użytkowe etykiety dostępności. NVDA nie może wypowiadać nazw klas, obiektów, enumów, identyfikatorów poleceń ani innych danych technicznych.
6. Dla zmienianych kontrolek sprawdzamy co najmniej: początkowo zaznaczony element, strzałki, ponowne otwarcie, powrót fokusa po Zapisz/Anuluj i brak podwójnych lub zagłuszających się komunikatów.
7. Po każdym zadaniu zapisujemy:
   - co zmieniono;
   - dlaczego wybrano dane rozwiązanie;
   - jakie testy wykonano i z jakim wynikiem;
   - czego świadomie nie objęto zakresem;
   - czy zmiana wymagała migracji ustawień lub danych.

## Poziomy zasobów

- **A — bez uruchamiania:** analiza kodu, porównanie starego AMC, projekt zachowania, testy czystej logiki i aktualizacja dokumentacji.
- **B — kompilacja skupiona:** jedna kompilacja i automatyczne testy dla powiązanej grupy zmian.
- **C — próba na żywo:** uruchomienie właściwej kompilacji, NVDA, klawiatura i ręczna weryfikacja mowy; tylko poza nagrywaniem.
- **D — wydanie:** pakiet, instalator, aktualizacja, integralność i publikacja na GitHubie.

Zasada architektoniczna: logika niezależna od systemu pozostaje w rdzeniu .NET, a WPF/Windows Forms, dźwięk, powłoka, poświadczenia i NVDA są adapterami Windows. Python nie przejmuje rdzenia, a ewentualny Rust jest dopuszczalny tylko jako uzasadniony, odizolowany składnik natywny.

## Kolejność zadań

### AMC01 — dodatek NVDA, opóźnione oznajmianie po Ctrl+C i wyszukiwanie

Zakres:

- ustalić źródło spóźnionego albo nakładającego się komunikatu po `Ctrl+C` i wprowadzić kontrolowane, krótkie opóźnienie tylko tam, gdzie jest potrzebne;
- usunąć wypowiadanie technicznego tekstu „AMC Python” po strzałce w prawo w wynikach wyszukiwania;
- zapewnić, że `Ctrl+Shift+L` wypowiada właściwy końcowy rezultat, na przykład „Dodano do biblioteki…”, i że komunikat nie jest przesłaniany;
- naprawić dodawanie z wyszukiwania kanału YouTube do Biblioteki za pomocą `Ctrl+Shift+L` oraz analogiczne usuwanie;
- zachować jawne etykiety wyników wyszukiwania dla NVDA i zwykłą funkcję kopiowania do schowka.

Kryteria odbioru:

- żadna nawigacja listy nie wypowiada „AMC Python” ani reprezentacji obiektu;
- po `Ctrl+C` słychać jeden celowy komunikat, po faktycznym skopiowaniu;
- po `Ctrl+Shift+L` słychać jeden końcowy wynik operacji;
- kanał YouTube można dodać i usunąć bez otwierania go;
- test obejmuje początkowy fokus, strzałki, ponowne otwarcie wyszukiwania i serię szybkich poleceń.

Zasoby: A, potem wspólna bramka B/C z AMC02.

### AMC02 — krótkie oznajmianie widoków nagrywania i czyste nazwy plików

Zakres:

- `Alt+R`: krótki nagłówek „Nagrywane”, potem zaznaczony element i pozycja, bez osobnego „X elementów”;
- `Alt+Shift+R`: krótki nagłówek „Historia nagrywania”, potem wynik, nazwa pliku i pozycja, bez nadmiarowego licznika listy;
- zachować osobne ostatnie zaznaczenie dla widoków `Alt+R` i `Alt+Shift+R` oraz przywracać je po ponownym wejściu, jeśli element nadal istnieje;
- w historii pozostawić na początku krótki wynik: „Nagrane”, „Zatrzymane”, „Przerwane” lub „Nieudane”;
- nie powtarzać nazwy harmonogramu, folderu lub stacji, gdy duplikuje nazwę pliku; zwykła lista nagranych plików ma przede wszystkim podawać nazwę pliku;
- zachować szczegóły techniczne lub pochodzenie poza zwykłą etykietą wiersza, wyłącznie tam, gdzie użytkownik świadomie otwiera informacje;
- na liście nagranych plików oraz w Historii odtwarzania otwieranej przez `Ctrl+H` `strzałka w lewo` ma podawać bitrate, wielkość i nazwę folderu lokalnego pliku, nadal bez dodawania folderu do zwykłego wiersza.

Kryteria odbioru:

- wejście na widok daje krótki nagłówek i od razu zaznaczony wiersz;
- NVDA podaje „1 z N” w standardowym komunikacie pozycji, bez drugiego licznika;
- nie występują duble w rodzaju „Hermanice, Hermanice” lub „Tarnobrzeg, Tarnobrzeg”;
- `strzałka w lewo` na nagranym pliku oraz lokalnym wpisie `Ctrl+H` podaje co najmniej bitrate, wielkość i folder, o ile te dane są dostępne;
- powrót do widoku ustawia fokus na poprzednio używanym pliku lub stacji.

Zasoby: A, potem wspólna bramka B/C z AMC01.

### AMC03 — audyt klawiszy starego AMC i obecnych warstw

To jest zadanie badawcze bez zmiany skrótów.

Zakres:

- porównać stare AMC z obecną wersją dla Plików lokalnych, Podcastów, YouTube, Radia i usług strumieniowych;
- zinwentaryzować rozdziały, zakładki tekstowe tworzone przez `Ctrl+Shift+B`, przechodzenie między zakładkami, historię widoków `Alt+lewo/prawo` oraz działanie `Alt+góra/dół`;
- rozstrzygnąć dokładne znaczenie `Ctrl+Shift+lewo/prawo`, `Shift+Page Up/Down` i kombinacji z `Ctrl+Alt` albo `Ctrl+Shift+Page Up/Down`;
- wskazać konflikty między WPF, dodatkiem NVDA i warstwą poleceń Pythona;
- przygotować tabelę: skrót, działanie w starym AMC, obecne działanie, właściwe działanie docelowe, dozwolone sesje i komunikat NVDA.

Kryterium odbioru: zatwierdzona tabela bez niejednoznacznych skrótów.

Zasoby: tylko A. Bez kompilacji i bez uruchamiania.

### AMC04 — ujednolicona nawigacja po rozdziałach, zakładkach i historii

Zakres wynika wyłącznie z tabeli AMC03.

- wdrożyć jeden model możliwości sesji zamiast oddzielnych wyjątków dla każdej listy;
- zachować rozdziały dostawcy w podcastach i plikach audio oraz zakładki użytkownika tworzone w AMC;
- ujednolicić przechodzenie do poprzedniego i następnego rozdziału lub zakładki;
- zachować `Alt+lewo/prawo` dla historii widoków i doprecyzować `Alt+góra/dół` zgodnie ze starym AMC;
- wystawić te same polecenia przez aplikację i dodatek NVDA, z właściwym komunikatem dla sesji, która danej funkcji nie obsługuje.

Zasoby: A/B, potem wspólna bramka C z AMC05.

### AMC05 — zaznaczenie odtwarzanego elementu we wszystkich listach

Status: audyt i specyfikacja poziomu A zatwierdzone; wdrożenie produkcyjne odłożone do Bramy 2. Szczegóły: `AMC05_ODTWARZANY_ELEMENT_NA_LISTACH_2026-10-18.md`.

Zakres:

- na każdej właściwej liście, nie tylko w Radiu, bieżący element ma stan „Odtwarzane”, a element zatrzymany pauzą stan „Wstrzymane”;
- stan ma być osobną dekoracją jawnej nazwy dostępności wiersza, nie może podwajać tytułu ani usuwać szczegółów właściwych dla widoku;
- po zmianie utworu, odświeżeniu listy i powrocie do widoku zaznaczenie oraz stan mają pozostać spójne;
- foldery, nagłówki i wiersze techniczne nigdy nie otrzymują fałszywego stanu „Odtwarzane”.
- samo oznaczenie nie przestawia fokusa; przeniesieniem fokusa nadal steruje istniejące ustawienie śledzenia odtwarzanego elementu po wyjściu z odtwarzacza;
- wyniki wyszukiwania włączyć po AMC01, a Sonos i WiiM tylko przy wiarygodnym stanie z adaptera w AMC10.

Zasoby: A/B, potem wspólna bramka C z AMC04.

### AMC06 — harmonogramy: data, czas i dzień tygodnia

Status: audyt i specyfikacja poziomu A zatwierdzone; wdrożenie produkcyjne odłożone do Bramy 3. Szczegóły: `AMC06_HARMONOGRAMY_DATA_CZAS_DZIEN_2026-10-18.md`.

Zakres:

- wybór daty i czasu ma wyliczać dzień tygodnia z daty planowanego nagrania, nie z dnia zapisywania harmonogramu;
- data i godzina rozpoczęcia mają działać jako dostępne pola segmentowe: lewo/prawo wybiera część, góra/dół ją zmienia, cyfry zastępują wartość i po ukończeniu prawidłowej części przechodzą dalej;
- długość ma osobne pola godzin i minut; puste godziny oznaczają zero, więc samo `25` w minutach oznacza 25 minut i zachowuje ten układ po ponownym otwarciu;
- edycja, kopiowanie, zmiana strefy czasowej, przejście czasu letniego/zimowego i ponowne otwarcie nie mogą przesuwać terminu;
- etykiety pól daty i czasu mają być jednoznaczne dla NVDA.
- cykliczny plan ma przechowywać zamierzoną lokalną godzinę niezależnie od najbliższego wystąpienia UTC, aby jednorazowe przesunięcie w luce czasu letniego nie zmieniało wszystkich następnych terminów;
- ręczny wybór dni ma wyłączać dalsze automatyczne zastępowanie ich dniem pierwszej daty.
- zatwierdzone usprawnienia menedżera obejmują krótkie wiersze, boczne strzałki z terminem i parametrami, historię planu pod `Shift+Enter`, pomijanie najbliższego wystąpienia pod `Shift+Spacja`, szybką nazwę pod `F2`, właściwości pod `Alt+Enter`, kopiowanie pod `Ctrl+C` i pełne menu kontekstowe;
- `Ctrl+Enter` nie otrzymuje w tym zadaniu żadnego nowego działania.

Zasoby: A/B/C we własnej Bramce 3. AMC06 nie czeka już na obsługę obrazu.

### AMC07 — zadanie przeniesione

Status: usunięte z bieżącej serii i przeniesione do AMC15. Szczegóły decyzji i historyczny odsyłacz: `AMC07_OBRAZ_WIDEO_ALT_V_2026-10-18.md`.

AMC07 nie ma kodu do wdrożenia, testów do uruchomienia ani własnej bramki. Numer pozostaje w planie, aby wcześniejsze notatki nie prowadziły do błędnego zadania.

### AMC08 — tworzenie playlist Spotify i dodawanie do playlist

Status: audyt i specyfikacja poziomu A przygotowane; wdrożenie produkcyjne odłożone do Bramy 4. Szczegóły: `AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.

Decyzja wydawnicza: AMC08 jest obowiązkowym zakresem prywatnego `AMC Test`. Brak Spotify w publicznym `AMC` nie oznacza rezygnacji z tworzenia i edycji natywnych playlist na koncie użytkownika.

Zakres:

- `Ctrl+P` otwiera w sesji Spotify natywne playlisty konta Spotify, analogicznie do playlist właściwych dla pozostałych sesji;
- `Ctrl+Shift+P` dodaje zaznaczone utwory i odcinki do jednej albo wielu edytowalnych playlist Spotify oraz pozwala w tym samym oknie utworzyć nową playlistę Spotify;
- nowa playlista może być prywatna albo publiczna i jest prawdziwą playlistą konta, którą można udostępnić przez Spotify;
- brak osobnego `Alt+Shift+P`; lokalne playlisty AMC nie przejmują w sesji Spotify wspólnego skrótu `Ctrl+Shift+P`;
- użycie aktualnych endpointów `POST /me/playlists`, `POST /playlists/{id}/items` i `GET /playlists/{id}/items`, bez przestarzałej ścieżki `/tracks`;
- ponowne, świadome logowanie dla zakresów `playlist-modify-private` i `playlist-modify-public`, bez automatycznego otwierania przeglądarki;
- rozróżnienie własnej, współtworzonej i obcej playlisty po danych modelu, nie po wyświetlanej nazwie właściciela;
- odświeżenie listy i zachowanie fokusa po operacji;
- partie najwyżej po 100 URI, ochrona przed przypadkowymi duplikatami i prawdziwy wynik częściowy przy błędzie późniejszej partii;
- zrozumiałe komunikaty o braku zakresu, prawa do playlisty, ograniczeniu konta deweloperskiego i limitach 429;
- integracja z `Ctrl+F1`, `Ctrl+Shift+K`, menu kontekstowym, wynikami wyszukiwania i odtwarzaczem;
- brak deklaracji odtwarzania playlist Spotify — nie należy do tego zadania.

Zasoby: A/B, testy API na atrapach; próba na rzeczywistym koncie tylko świadomie i bez tworzenia zbędnych danych.

### AMC09 — Menedżer sesji i pierwsze logowanie Spotify/TIDAL

Status: audyt i robocza specyfikacja poziomu A przygotowane do zatwierdzenia. Szczegóły: `AMC09_MENEDZER_SESJI_I_PIERWSZE_LOGOWANIE_2026-10-18.md`.

Zakres:

- rozdzielić dostępność integracji w danym wydaniu, włączenie sesji przez użytkownika oraz rzeczywistą gotowość konta lub urządzenia;
- przebudować `Ctrl+Shift+S` z samego wyboru na dostępny Menedżer sesji: Enter wybiera, Spacja włącza lub wyłącza, `Alt+strzałka` zachowuje świadomą zmianę kolejności, a `Konfiguruj…` prowadzi do właściwego konta albo urządzenia;
- utrzymywać zwartą aktywną listę najwyżej dziewięciu sesji: dodanie dopisuje na końcu, usunięcie przesuwa późniejsze numery, a `Alt+strzałka` od razu zmienia kolejność i skróty `Ctrl+1–9`;
- dla świeżej instalacji ustawić `Ctrl+1 Pliki lokalne`, `Ctrl+2 Radio`, `Ctrl+3 Podcasty i YouTube`; każdą z nich można później wyłączyć, lecz zawsze musi pozostać co najmniej jedna sesja;
- zmienić wszędzie użytkową nazwę sesji z `Radio internetowe` na `Radio`, bez zmiany identyfikatora, stacji, presetów i harmonogramów;
- po usunięciu `Ctrl+3 Podcasty i YouTube` dotychczasowy `Ctrl+4 Sonos` staje się `Ctrl+3 Sonos`; ponowne włączenie Podcastów dopisuje je na końcu;
- migracja istniejącego użytkownika zachowuje wszystkie aktywne sesje, ich wzajemną kolejność, dane i prywatne logowania, po czym usuwa luki w numeracji;
- usunąć demonstracyjne utwory z normalnego pierwszego uruchomienia usług zewnętrznych; ewentualny tryb demonstracyjny ma być jawnie deweloperski;
- zmienić świeży `LastSessionId` z TIDAL-u na Pliki lokalne i rozważyć jednorazowe otwarcie Menedżera po instalacji;
- połączyć pierwsze kroki Spotify w jeden punkt wejścia; w AMC16 sprawdzić kod `spotify.com/pair` oraz wybór AMC jako urządzenia Spotify Connect, a osobno raportować rzeczywiście gotowe odtwarzanie, bibliotekę i playlisty;
- w TIDAL-u osobno raportować konto, synchronizację i potwierdzony zakres odtwarzania; nie przedstawiać próbek jako pełnych utworów;
- zwykły publiczny interfejs nie zaczyna od Client ID i Redirect URI. Ustawienia aplikacji dostawcy są wyłącznie drogą prywatną/deweloperską;
- żadna przeglądarka nie otwiera się bez jawnego polecenia logowania; tokeny nadal pozostają wyłącznie w Menedżerze poświadczeń Windows;
- zintegrować Menedżer z `Ctrl+F1`, `Ctrl+Shift+K`, menu i Ustawieniami bez dwóch sprzecznych list sesji.
- publiczny instalator udostępnia WiiM; Sonos jest celem publicznym po wdrożeniu brokera HTTPS i teście zewnętrznego konta; Spotify i TIDAL są całkowicie ukryte w publicznym `AMC` i pozostają w `AMC Test`. Spotify może kiedyś wrócić do oceny po AMC16, a obecny plan TIDAL-u pozostaje prywatny mimo użytecznego API biblioteki.

Zasoby: A/B/C. Zależność: AMC08 dostarcza ostateczne zakresy Spotify.

### AMC10 — Sonos i WiiM

Status: audyt i specyfikacja poziomu A zatwierdzone kierunkowo. Istniejące adaptery są rozbudowane; zadanie dotyczy przede wszystkim pierwszego uruchomienia, stanów i wspólnego wejścia. Dla Sonosa dopisano osobną drogę: publiczny broker, odbiór techniczny, ograniczony pilotaż dla chętnych i dopiero później zwykłe wydanie publiczne. Szczegóły: `AMC10_SONOS_WIIM_URUCHOMIENIE_I_UJEDNOLICENIE_2026-10-18.md`.

Zakres:

- udostępnić WiiM w publicznym wydaniu jako opcjonalną, początkowo wyłączoną sesję, bez skanowania sieci przy świeżym starcie;
- przygotować Sonosa do takiego samego włączenia, ale wystawić go publicznie dopiero po zastąpieniu prywatnego brokera AMC trwałą usługą HTTPS i próbie z zewnętrznym kontem;
- przed pełnym udostępnieniem przeprowadzić kontrolowany pilotaż `Sonos — wersja próbna`, bez wymagania od użytkownika Client ID, sekretu albo własnego brokera;
- zapewnić wspólne działanie `Konfiguruj…` w Menedżerze, ale zachować osobne drogi: lokalne wykrywanie lub ręczny adres WiiM oraz konto, dom i grupę Sonosa;
- pokazywać krótkie stany `wymaga konfiguracji`, `gotowa`, `urządzenie niedostępne` i `wymaga wybrania grupy` bez technicznych identyfikatorów;
- samo włączenie, zaznaczenie celu, wejście do sesji, wyjście albo wyłączenie sesji nie wysyła Play, Pause, Stop ani zmiany źródła;
- zachować obecne znaczenie `Ctrl+F5`: urządzenia w WiiM i wybór celu sterowania w Sonosie; konto Sonos pozostaje osobnym poleceniem;
- spóźnione odpowiedzi nie mogą zmieniać nowszego celu ani przejmować fokusa;
- urządzenie offline pozostaje zapisane, a błąd jednej możliwości nie unieważnia całego adaptera;
- nie scalać ulubionych Sonosa z presetami WiiM, grup Sonosa z multiroom WiiM ani katalogów usług z biblioteką urządzenia;
- wszystkie listy i stany przechodzą test dostępności NVDA, a prawdziwe próby urządzeń pozostają oddzielne od kompilacji.

Zasoby: A/B/C; testy sieciowe oddzielone od podstawowej kompilacji.

### AMC11 — aktualizacje aplikacji i GitHub

Zakres:

- uporządkować kanał stabilny i testowy, manifest, wersję, sumy kontrolne i komunikaty o aktualizacji;
- zweryfikować pobranie właściwego pakietu z repozytorium `michalkasperczak/AMC`;
- aktualizacja nie może przerwać nagrywania ani uruchomić innej kopii programu;
- obecne wymuszone zamykanie przez instalator nie może pozostać domyślną drogą wydania: instalator najpierw uzgadnia stan z właściwym profilem AMC, a podczas nagrywania odkłada aktualizację bez podmiany plików;
- publikacja źródeł, publikacja ZIP i instalacja pozostają osobnymi, weryfikowanymi krokami.
- przed upublicznieniem wykonać audyt sekretów, danych prywatnych, licencji, źródeł zależności, dokumentacji i profilu możliwości; samo wysłanie plików do GitHuba nie jest odbiorem wydania;
- pierwsze publiczne artefakty ograniczyć do instalatora `win-x64` i odpowiadającego mu pakietu integralności. Portable x64 dołączyć po ustabilizowaniu instalatora, a natywnego ARM64 nie włączać do pierwszej publikacji;
- automatyzacja wydania ma budować z czystego źródła, nadawać jeden numer wersji, tworzyć sumy SHA-256 i odmawiać publikacji przy brakującym albo nieoczekiwanym składniku.

Zasoby: B/C/D. Zależność: stabilna tożsamość wersji i pakietu przed AMC12.

### AMC12 — niezależny instalator i pełna integralność

Zakres:

- z jednego kodu tworzyć dwa jawne profile: publiczne `Accessible Multimedia Controller` (`AMC`) i prywatne `Accessible Multimedia Controller — Test` (`AMC Test`); nie używać użytkowej nazwy `AMC Python`;
- nadać profilom osobne identyfikatory instalacji, foldery programu, kanały aktualizacji oraz magazyny ustawień, pamięci podręcznej, logów i poświadczeń, aby mogły bezpiecznie działać obok siebie;
- w publicznym profilu zawsze udostępnić WiiM, Sonosa udostępnić po zaliczeniu jego bramy, a TIDAL całkowicie pominąć wraz z sesją, kontem, pomocą i poleceniami;
- dodać wersjonowaną, atomową migawkę danych wspólnych oraz opcję `Odświeżaj dane z AMC Test przy uruchomieniu`, zamiast współdzielenia żywych plików `state.json`, `library.db` i `podcasts.db`;
- przenosić z `AMC Test` do publicznego AMC zgodne dane Biblioteki, radia, Podcastów i YouTube, historii, zakładek, lokalnych playlist, nagrań oraz definicji harmonogramów, bez kopiowania fizycznych plików;
- wspólne ustawienia użytkowe synchronizować opcjonalnie i filtrować według możliwości wydania; identyfikacja profilu, kolejność niedostępnych sesji i chwilowy stan interfejsu pozostają osobne;
- nadać tylko jednemu profilowi naraz prawo wykonywania harmonogramów, domyślnie `AMC Test`, z jawnym poleceniem bezpiecznego przejęcia przez publiczne AMC;
- nie kopiować tokenów, wpisów Menedżera poświadczeń, Spotify, TIDAL-u, logów, pamięci podręcznej ani aktywnego stanu nagrywania;
- Spotify do czasu osobnej decyzji umieszczać tylko w `AMC Test`; w publicznym `AMC` pominąć sesję, polecenia, pomoc, paletę, ustawienia i zależności właściwe wyłącznie dla Spotify;
- początkowy import danych ze starej alfy wykonać jako jawną, jednorazową migrację; późniejsze odświeżanie `AMC Test` → `AMC` korzysta z filtrowanych migawek i nigdy ze wspólnego zapisu obu instalacji do tych samych baz;
- instalator niezależny od środowiska programistycznego;
- kontrola obecności i wersji elementów potrzebnych do odtwarzania, nagrywania, zapisywania i pobierania;
- bezpieczna aktualizacja komponentów bez mieszania plików ze starych i nowych wydań;
- weryfikacja wersji, rozmiaru i SHA-256 gotowego pakietu;
- po stabilizacji instalatora przygotować osobny Portable x64 z własnym katalogiem danych, bez skojarzeń powłoki i bez współdzielenia blokady jednej instancji z wydaniem instalowanym;
- najpierw sprawdzić zwykły pakiet x64 na prawdziwym Windows 11 ARM pod emulacją. Natywny `win-arm64` pozostawić jako osobny późniejszy projekt zależności i wydania;
- test czystej instalacji, aktualizacji istniejącej instalacji, naprawy, deinstalacji i zachowania danych użytkownika;
- test ręcznie uruchomionego instalatora podczas nagrywania i finalizacji pliku: brak zamknięcia procesu, brak wymiany plików i bezpieczne odłożenie operacji;
- uruchomienie dokładnie zainstalowanej wersji oraz potwierdzenie jednej instancji.

Zasoby: pełne B/C/D. To jedyny etap wymagający kompletnej walidacji wydania. Szczegóły profili: `AMC12_PROFILE_WYDANIA_PUBLICZNEGO_I_TESTOWEGO_2026-10-18.md`.

### AMC13 — regresja End w Time Shifcie radia

Priorytet: regresja podstawowego sterowania. Etap 1 należy połączyć z najbliższą Bramką 2, a nie odkładać za instalator.

Zakres naprawy regresji:

- zapewnić, że `End` zawsze przechodzi z odsłuchu bufora do transmisji na żywo, niezależnie od kontrolki mającej fokus;
- `End` nie może korzystać z długości `MediaItem` stacji ani odpowiadać „nieznany czas odtwarzania”;
- zachować `Home` jako przejście do najstarszego miejsca nadal dostępnego w aktualnym buforze;
- `End` ma wrócić na żywo i do normalnego tempa `1,00x`;
- nie przejmować `NVDA+End`, który pozostaje poleceniem czytnika ekranu.

Osobne, późniejsze rozszerzenia Time Shiftu:

- zweryfikować na żywo istniejącą w źródle nawigację cyframi `0–9` do `0–90%` aktualnego okna bufora;
- umożliwić ustawienie początku i końca fragmentu w Time Shifcie;
- zapisać wybrany fragment do nowego pliku przy dalszym odbieraniu transmisji;
- nie udostępniać destrukcyjnego „usuń z oryginału”, ponieważ pierścień Time Shiftu nie jest plikiem źródłowym;
- unieważnić albo czytelnie oznajmić zaznaczenie po zmianie stacji lub nadpisaniu jego początku przez obracający się bufor;
- kodować kopię fragmentu przez bezpieczny plik tymczasowy i publikować dopiero po poprawnym zakończeniu kodera.

Kryteria odbioru:

- test pełnej drogi `End` w rzeczywistym oknie potwierdza komunikat „Na żywo” i minimalne opóźnienie względem transmisji;
- test obejmuje fokus na przycisku, utratę fokusa do okna, otwarte menu oraz `NVDA+End`, którego AMC nie może przejąć;
- `Home` nadal wybiera najstarsze dostępne miejsce po zawinięciu pierścienia;
- zmiana stacji nie pozwala przewijać ani eksportować starego bufora;
- zapisany fragment ma prawidłowy czas, format i nie zawiera materiału spoza zaznaczenia;
- `Ctrl+F1`, paleta `Ctrl+Shift+K`, menu i instrukcja podają ten sam zakres działania.

Zasoby: naprawa `End` — A/B i próba C przy Bramce 2; procenty i fragmenty — osobne A/B/C po świadomym rozpoczęciu tych rozszerzeń.

### AMC14 — foldery lokalne i integracja z powłoką Windows

Zakres:

- otwieranie folderu i zaznaczanie lokalnego pliku z Biblioteki, Historii nagrywania, nagranych plików, pobranych podcastów i odtwarzacza;
- otwieranie folderu źródłowego Biblioteki oraz domyślnych folderów nagrań i pobierania;
- krótka odmowa dla materiału bez lokalnego pliku;
- opcjonalne, odwracalne skojarzenia obsługiwanych rozszerzeń przez niezależny instalator;
- przekazywanie pliku uruchomionego z Eksploratora do jednej istniejącej instancji AMC bez przerywania nagrywania;
- audyt konfliktów przed ewentualnym użyciem `Ctrl+Enter` albo `Ctrl+Alt+Enter`; obecnie żaden skrót nie jest zatwierdzony.

Zasoby: AMC14A/B — A/B/C przed instalatorem; AMC14C — końcowe C/D razem z AMC12 i testami instalatora oraz powłoki.

### AMC15 — opcjonalne wideo pełnoekranowe po wydaniu instalatora

Status: zadanie długoterminowe, bez terminu. Nie rozpoczynać przed ukończeniem AMC12, stabilnym wydaniem audio i ponownym świadomym zatwierdzeniem. Szczegóły: `AMC15_WIDEO_PELNOEKRANOWE_PO_INSTALATORZE_2026-10-18.md`.

Zakres przyszły:

- osobny, opcjonalny i domyślnie wyłączony moduł pełnoekranowy zamiast obrazu osadzonego na stałe w głównym odtwarzaczu;
- pierwsza faza wyłącznie dla lokalnych, skończonych plików wideo; druga faza może objąć zwykłe, skończone materiały YouTube;
- `Alt+V` przełącza obraz bieżącego materiału chwilowo, a `Alt+Shift+V` zmienia i zapisuje ustawienie automatycznego pokazywania obrazu;
- transmisje YouTube traktowane jako radio, radiowe HLS, TIDAL Video, Spotify, Sonos i WiiM pozostają poza pierwszym wdrożeniem;
- kandydaci na silnik, między innymi mpv/libmpv, VLC/LibVLCSharp i FFmpeg, zostaną porównani dopiero w osobnym prototypie;
- brak, wyłączenie lub awaria modułu obrazu nie może zmienić działania audio, Time Shiftu, nagrywania, zakładek, rozdziałów ani urządzenia wyjściowego;
- oba polecenia muszą trafić do `Ctrl+F1`, `Ctrl+Shift+K`, menu odtwarzacza, Ustawień i instrukcji.

Zasoby: osobna przyszła sekwencja A/B/C/D po AMC12. Nie łączyć z obecną Bramką 3 ani z najbliższym wydaniem.

### AMC16 — jedno proste logowanie Spotify z Librespot

- zachować istniejący Librespot i wymóg prawdziwego konta Premium;
- porównać istniejący kod urządzenia na `spotify.com/pair` z parowaniem przez oficjalną aplikację Spotify i lokalne discovery;
- nie wymagać od zwykłego użytkownika Client ID, Redirect URI ani tworzenia aplikacji deweloperskiej;
- ustalić testem, czy jeden zatwierdzony stan konta może obsłużyć odtwarzanie, katalog, bibliotekę i playlisty, bez zakładania tego z góry;
- nie obchodzić opłat, reklam, kont Free, ograniczeń geograficznych ani ochrony przed kopiowaniem;
- potraktować wygodną obsługę Spotify w aplikacji Elten Link jako wzorzec użytkowy, bez instalowania, debugowania i kopiowania jej implementacji;
- po eksperymencie przygotować raport; Spotify nie przechodzi automatycznie do publicznego `AMC`, a jego publikacja wymaga osobnej decyzji.

Zasoby: A wykonane; B/C w osobnej sesji. Zależności: AMC08 dla playlist, AMC09 dla Menedżera sesji, AMC12 dla profilu instalatora.

### AMC17 — podgląd trwającego nagrania

- `Alt+R`, a następnie `Enter` otwiera zwykły odtwarzacz dokładnie wybranego, nadal nagrywanego pliku;
- `Home` przechodzi na początek, `End` do bieżącego końca i dalej śledzi dopisywany dźwięk, a `Escape` wraca do właściwego wiersza;
- podgląd korzysta z osobnego kursora i formatowo neutralnego źródła ramek, nie z technicznego pliku roboczego kodera;
- otwarcie, pauza, przewijanie, zamknięcie i błąd podglądu nie mogą zatrzymać ani zmienić nagrywania;
- `Ctrl+R` w takim odtwarzaczu kończy tylko wybrane nagranie, czeka na publikację gotowego pliku i pozostawia jego zawartość możliwą do dalszego odtwarzania;
- aktywna lista pokazuje osobno każdy fizycznie zapisywany plik, także dwa nagrania tej samej stacji;
- `Ctrl+X`, `Delete`, `Shift+Delete`, zmiana nazwy, przeniesienie i destrukcyjne usunięcie fragmentu są jawnie blokowane do czasu zakończenia nagrania;
- pomoc `Ctrl+F1`, paleta `Ctrl+Shift+K` i menu kontekstowe opisują ten sam zakres bez nazw technicznych.

Zasoby: A wykonane; B/C odłożone do własnej przyszłej sekwencji po AMC12 i stabilnym wydaniu instalatora. Nie łączyć z bieżącą Bramką 2. Szczegóły: `AMC17_PODGLAD_TRWAJACEGO_NAGRANIA_2026-10-18.md`.

## Bramki kompilacji i uruchomienia

1. **Bramka 1 po AMC01 i AMC02:** jedna kompilacja aplikacji oraz dodatku NVDA, testy automatyczne i jedna sesja ręczna z NVDA.
2. **Bramka 2 po AMC04 i AMC05 oraz naprawie `End` z AMC13:** jedna kompilacja, test wszystkich warstw klawiszy i list oraz powrotu z Time Shiftu na żywo.
3. **Bramka 3 po AMC06:** jedna kompilacja i test harmonogramu; bez obrazu wideo.
4. **Bramka 4 po AMC08–AMC10:** jedna kompilacja integracyjna; osobne próby kont i urządzeń tylko wtedy, gdy są potrzebne.
5. **Przygotowanie AMC14A/B:** przed instalatorem wdrożyć i sprawdzić argumenty plików, przekazanie do działającej instancji, kolejkę, ustawienia oraz dostępność; bez rejestracji systemowej w tej części.
6. **Bramka 5 po AMC11, AMC12 i aplikacyjnej części AMC14:** pełna kompilacja wydania, instalator, opcjonalna rejestracja sprawdzonych rozszerzeń, aktualizacja, integralność i kontrolowane uruchomienie.

AMC15 i AMC17 otrzymają kiedyś własne, osobne bramki dopiero po Bramce 5 i po ponownym zatwierdzeniu rozpoczęcia odpowiednich prac. Nie należy ich łączyć ze sobą tylko dlatego, że oba są zadaniami późniejszymi.

Przed każdą bramką C lub D ponownie sprawdzamy, czy nie trwa nagrywanie. Jeżeli trwa, odkładamy uruchomienie, ale możemy dalej wykonywać bezpieczną analizę i zmiany źródłowe z poziomu A.

## Pierwszy krok wykonawczy

Rozpoczynamy od AMC01. Najpierw zapisujemy reprodukcję czterech zachowań: `Ctrl+C`, strzałka w prawo w wyszukiwaniu, `Ctrl+Shift+L` oraz dodanie kanału YouTube. Dopiero potem zmieniamy kolejność komunikatów i routing Biblioteki. Nie uruchamiamy aplikacji aż do wspólnej bramki z AMC02, chyba że statycznie nie da się rozstrzygnąć źródła komunikatu.
