# AMC Python — stan prac 13 października 2026

## Decyzja architektoniczna

AMC Python nie jest przepisywaniem całego programu od zera. Docelowy układ to:

- natywny, dostępny interfejs w wxPython;
- istniejący rdzeń C# AMC jako jedyny właściciel odtwarzania, nagrywania,
  timeshiftu, harmonogramów i zapisów we wspólnych bazach;
- wąski LiteHost C# łączący interfejs z istniejącymi usługami rdzenia;
- prywatny stan interfejsu wxPython wyłącznie tam, gdzie równoczesny zapis do
  profilu głównego AMC byłby niebezpieczny.

Takie rozdzielenie zachowuje sprawdzony tor multimediów i zmienia przede
wszystkim interfejs. Python nie uruchamia drugiego harmonogramu ani drugiego
silnika nagrywania.

Proces `amc_lite_host.exe` jest wewnętrznym modułem tego samego programu, a
nie osobnym starym AMC wymaganym od użytkownika. Granica procesu jest celowa:
awaria lub wymiana interfejsu nie wymaga przepisywania sprawdzonego toru audio,
a protokół może być później użyty także przez wiersz poleceń. Pakiet
produkcyjny zawiera jedną kanoniczną kopię interfejsu i jedną kopię silnika w
folderze `host`; historyczne sloty `host-next*` zostały usunięte, ponieważ
utrudniały jednoznaczne ustalenie wersji uruchomionej po restarcie.

Nie należy osadzać Pythona z powrotem w starym oknie WPF. Zwiększyłoby to
sprzężenie i pozostawiło dwa interfejsy, nie rozwiązując problemów cyklu życia
procesów. Jeden uruchamiacz EXE nadzoruje start, jedną instancję,
zgodność wersji i bezpieczne zamknięcie całego pakietu.

Odbiór użytkownika potwierdził, że obecny start przez `AMC-wx-Lite.cmd` jest
zbyt niejednoznaczny: można trafić na niewłaściwy runtime lub widoczny proces
interpretera i nie mieć pewności, która kopia programu faktycznie ruszyła.
Od 12 października istnieje jeden użytkowy `AMC.exe`. Uruchamia dołączony
prywatny runtime i właściwy LiteHost bez konsoli oraz bez systemowego Pythona,
`PYTHONPATH` i skryptów wsadowych. Sprawdza zgodność wersji i manifest, pilnuje
jednej instancji i bezpiecznej odmowy zamknięcia podczas nagrywania, pokazuje
dostępny komunikat przy błędzie i uruchamia program ponownie po udanej
aktualizacji. Tytuł głównego okna zawiera wersję programu oraz etykietę
kompilacji z manifestu, na przykład `2026.10.13-e8fed82`; dzięki temu zgłoszenie
można jednoznacznie przypisać do uruchomionej paczki bez odczytywania ścieżek
ani identyfikatorów technicznych.

Istniejący `AMC-Python-Updater.exe` pozostaje osobnym wykonawcą bezpiecznej
podmiany i wycofania plików. Docelowe `AMC.exe` ma być stałym punktem wejścia,
a aktualizator działać za nim, bez ręcznego wybierania skryptu lub interpretera.

Jedynym użytkowym punktem wejścia jest
`D:\Projekty Codex\AMC Python\AMC.exe`. Katalogi `.test-output` są wyłącznie
technicznymi kandydatami do automatycznej weryfikacji i nie należy z nich
uruchamiać programu ani podawać ich użytkownikowi jako bieżącej wersji.
Pakiet nie zawiera `AMC-wx-Lite.cmd`. `AMC.exe` sprawdza wersję formatu
pakietu, interfejsu i protokołu hosta oraz sumy krytycznych plików przed
uruchomieniem.

Gdy działa główne AMC, LiteHost świadomie odmawia przejęcia zapisywalnego
profilu. Próby uruchomienia AMC Python 13 października o 21:05 i 21:26 nie były
awarią `AMC.exe`: dziennik zawiera odmowę z prośbą o zamknięcie głównego AMC,
aby dwie wersje nie zapisywały jednocześnie podcastów, harmonogramów i stanu.
Podczas nagrywania w głównym AMC nie wolno obchodzić tej blokady ani uruchamiać
drugiego harmonogramu. Aktualną paczkę można przygotować na dysku, ale żywy
odbiór AMC Python zaczyna się dopiero po zakończeniu nagrań i zamknięciu
głównego AMC.

### Niezależne odtwarzanie sesji i urządzenia audio

Wykryto poważną regresję względem głównego AMC: gdy gra radio internetowe,
uruchomienie pliku w sesji Multimedia zatrzymuje radio. Docelowo każda sesja
ma własny tor, urządzenie wyjściowe, stan pauzy i wyciszenia. Radio i plik mają
móc grać równolegle, także na dwóch różnych urządzeniach. Przejście do sesji
zmienia tylko cel sterowania; `Spacja` i `Ctrl+M` działają wyłącznie na
aktywnej sesji i nie wpływają na pozostałe.

12 października rozdzielono w LiteHost stan odtwarzania, pauzy, głośności,
tempa i urządzenia dla Radia oraz toru Plików/Podcastów. Wszystkie polecenia
transportu niosą teraz jawną nazwę sesji. Uruchomienie pliku nie zatrzymuje
Radia, a uruchomienie Radia nie odłącza kolejki plików. Pliki i Podcasty nadal
współdzielą jeden dekoder, tak jak przed tą zmianą, więc nie są jeszcze dwoma
równoległymi torami. Pozostaje odbiór dwóch rzeczywistych strumieni i osobnych
urządzeń. `Ctrl+M` ma już osobny stan dla obu torów i przywraca wcześniejszą
głośność. To samo polecenie jest widoczne w menu Odtwarzanie wyłącznie
dla lokalnych sesji audio; pozycja zmienia nazwę między „Wycisz bieżącą
sesję” i „Włącz dźwięk bieżącej sesji” oraz przekazuje NVDA rzeczywisty
stan zaznaczenia. Nadal wymaga to żywego odbioru; całego punktu nie uznaje
się jeszcze za zakończony.

Polityka zaniku urządzenia jest już ustawieniem. Użytkownik wybiera, czy po
utracie wybranego wyjścia odsłuch ma automatycznie trwać na urządzeniu
domyślnym, czy przejść w pauzę po bezpiecznym przełączeniu na urządzenie
domyślne. Pauza odsłuchu nie zatrzymuje nagrywania radia ani bufora timeshift.
`Ctrl+[` i `Ctrl+]` cyklicznie wybierają
odpowiednio poprzednie i następne dostępne urządzenie audio dla bieżącej sesji
i podają wyłącznie jego użytkową nazwę. Wybór pozostaje zapamiętany osobno dla
sesji, a odłączone pozycje są pomijane. Oba zachowania wymagają jeszcze
żywego odbioru z rzeczywistym urządzeniem.

### Pełny audyt interfejsu i ustawień

`Ctrl+,` otwiera teraz natywne Ustawienia z czterema działającymi kartami:
Ogólne, Radio i nagrywanie, Podcasty i YouTube oraz Komunikaty. Ogólne obejmują zachowanie
odtwarzacza i wyjścia audio, normalizację, przejścia, ciszę oraz jawnie
nazwane algorytmy tempa; Komunikaty obejmują stany odtwarzania i nagrywania
Radia, oznajmianie automatycznie rozpoznanych utworów, szczegółowe podpowiedzi
oraz działające przełączniki komunikatów transportu: komunikaty odtwarzacza,
strzałki/Home/End, skoki cyframi, głośność i
odtwarzanie/pauzę. Dla skoku cyfrą można wybrać procent, czas albo oba. Do
pierwszego zapisu ustawienia dziedziczą odpowiednie wartości z głównego AMC;
potem AMC Python zapisuje własne wybory bez modyfikowania profilu starego
interfejsu. `Ctrl+Shift+G` również zapisuje swój przełącznik bezpośrednio w
AMC Python. Wyłączony komunikat odtwarzania/pauzy nadal aktualizuje dostępne
pole stanu, ale nie wymusza wypowiedzi NVDA.
`Shift+Page Up` i `Shift+Page Down` przechodzą odpowiednio do poprzedniej i
następnej zakładki bieżącego pliku. Powtarzanie skrótu w ciągu pięciu sekund
kontynuuje nawigację po kolejnych zakładkach, jak w głównym AMC. Nie koliduje
to z `Alt+Page Up` i `Alt+Page Down`, które pozostają nawigacją po granicach
zaznaczonego fragmentu. Karta Komunikaty ma rzeczywisty przełącznik
oznajmiania udanej nawigacji po zakładkach; brak poprzedniej lub następnej
zakładki nadal jest podawany jako potrzebna informacja graniczna.
`Ctrl+Shift+B` jest teraz prawidłowo kontekstowe: na liście otwiera zakładki
zaznaczonego pliku, natomiast w odtwarzaczu otwiera natywne, dostępne pole
nazwy i dodaje nazwaną zakładkę w bieżącym miejscu. `B` nadal dodaje szybką
zakładkę, a `Ctrl+B` pokazuje zbiorczą listę wszystkich zakładek. Nazwa jest
normalizowana i zapisywana w tym samym wierszu bazy co zakładka głównego AMC;
ponowne nazwanie zakładki w tej samej sekundzie aktualizuje nazwę zamiast
tworzyć duplikat. Techniczny identyfikator nie trafia do dialogu ani mowy.
Po włączeniu `Ctrl+K` podaje pełną instrukcję filtra, a pole zapytania i lista
wyników `Ctrl+F`/`Ctrl+Shift+F` udostępniają osobne teksty pomocy. Nazwy
kontrolek pozostają krótkie i nie zawierają podpowiedzi ani wartości modelu.
Karta Radio i
nagrywanie zapisuje długość TimeShift do 12 godzin,
domyślny folder, format, bitrate, preferowanie folderu stacji w nowym planie
oraz domyślne wybudzanie. Folder, format i bitrate trafiają do następnego
ręcznego nagrania i harmonogramów, a wybudzanie jest ponownie synchronizowane
z wykonawcą planów. Radio może zachować osobny folder albo użyć tego samego
folderu co Podcasty bez utraty zapamiętanego osobnego folderu. Nowa długość
TimeShift obowiązuje po ponownym uruchomieniu hosta. Karta Podcasty i YouTube
ustawia folder pobierania, osobne odstępy odświeżania RSS i YouTube oraz limit
źródeł w jednym automatycznym przebiegu. Host wybiera tylko należne źródła;
brak nowości nie powoduje rutynowej mowy. Działa też ręczne rozpoznawanie
utworu (`S` w odtwarzaczu Radia), automatyczna obserwacja (`Shift+S`), trwała
historia (`Ctrl+Alt+S`) i osobny przełącznik jej oznajmiania
(`Ctrl+Alt+Shift+S`). Zakres automatu może obejmować odtwarzaną stację,
nagrywane stacje albo oba rodzaje źródeł. Do usługi wychodzi podpis
akustyczny, nie adres stacji ani nagrany dźwięk. Enter uruchamia Zapisz, po
powodzeniu pada dokładnie jeden komunikat „Zapisano ustawienia”. To nadal nie
są pełne Ustawienia głównego AMC: brakuje trzech całych kart.
Nie wystarczy dopisać kart Ogólne, Podcasty i Radio: trzeba przepisać całe
Ustawienia dokładnie z głównego AMC, po uprzednim spisie wszystkich kart, pól,
wartości domyślnych, zależności, walidacji i miejsc zapisu. `Ctrl+Tab` i
`Ctrl+Shift+Tab` mają przechodzić pomiędzy wszystkimi kartami z prawidłowym
fokusem i odczytem NVDA; Zapisz, Anuluj i ponowne otwarcie muszą zachowywać
semantykę głównego AMC.

Odbiór użytkownika 12 października potwierdził, że Enter zapisuje i NVDA mówi
„Zapisano ustawienia”, choć komunikat dotarł z opóźnieniem po dwóch modalnych
alertach interpretera. Pomiar zapisu prawie 1 MB stanu wyniósł średnio 32 ms,
więc zapis nie był źródłem zauważalnego opóźnienia. Launcher używa teraz
bezokiennego `python.exe` z przechwyconym wyjściem zamiast `pythonw.exe`;
techniczny komunikat interpretera trafia do prywatnego `launcher.log`, nie do
okna z przyciskiem OK. Potwierdzenie ustawień nadal pada dopiero po atomowym
zapisie i dokładnie raz.

Cały interfejs wymaga porównania z głównym AMC: wszystkie menu i skróty,
organizacja Biblioteki, wejścia i powroty z podlist oraz właściwe warianty
sortowania `Alt+cyfra` dla każdej sesji i każdego widoku. Częściowe działanie
jednego widoku nie jest dowodem kompletnego portu. Audyt ma zakończyć się
jawną macierzą widok–skrót–działanie–powrót, bez technicznych identyfikatorów
w etykietach dostępności.

Ustalona reguła głównych widoków: Biblioteka, Ulubione, Playlisty i Kolejka
są równorzędne. `Escape` ani `Backspace` nie przełącza między nimi i na ich
najwyższym poziomie pozostaje cichy. Widoki zmieniają wyłącznie jawne skróty:
`Ctrl+L`, `Ctrl+U`, `Ctrl+P` oraz `Ctrl+Q`. Powrót działa tylko z rzeczywiście
zagnieżdżonej zawartości, na przykład z otwartej playlisty do listy playlist,
z zachowaniem poprzedniego zaznaczenia. Harmonogramy, bieżące nagrania,
zakładki i inne osobne podglądy zachowują własne reguły zamykania.

### Wiersz poleceń, agenci AI i wiele systemów

Obecny protokół JSON-lines jest dobrym punktem wyjścia dla przyszłego AMC CLI
i sterowania przez agentów AI. CLI oraz agent powinny wywoływać tę samą,
ograniczoną listę poleceń silnika co interfejs, a nie automatyzować klawisze i
okna. Operacje usuwające, zapisujące lub rozpoczynające nagranie muszą mieć
jawne granice i potwierdzenia.

Wieloplatformowość wymaga dalszego podziału: modele, kolejki i reguły mogą
pozostać we wspólnym rdzeniu .NET, natomiast Media Foundation, urządzenia
Windows i część toru audio potrzebują adapterów dla Linuxa i macOS. Sam
wxPython ułatwia przeniesienie widoku, ale nie gwarantuje identycznej
dostępności; osobno trzeba testować NVDA, VoiceOver i Orcę. CLI bez interfejsu
graficznego może stać się wieloplatformowe wcześniej niż pełny odtwarzacz.

## Stan funkcjonalny

### Radio i multimedia

Interfejs korzysta z istniejącego toru C# dla odtwarzania, nagrywania w tle,
historii nagrań, harmonogramów, timeshiftu oraz edycji nagrań. Tych mechanizmów
nie należy zastępować odpowiednikami napisanymi w Pythonie bez osobnej,
udowodnionej potrzeby. Zmiany mają dotyczyć przede wszystkim dostępności,
kompletności skrótów i zgodności zachowania z głównym AMC.

13 października domknięto zapis Biblioteki stacji w samodzielnym AMC Python.
`Ctrl+N` nie jest już martwe we wspólnym profilu: dodaje nową stację przez
wąską bramę hosta C#, a ponowne podanie tego samego adresu aktualizuje nazwę
i przywraca istniejący wpis do Biblioteki dokładnie jak główne AMC. `Ctrl+O`
w sesji Radio korzysta ze wspólnego parsera M3U/PLS/XSPF/JSON, dopisuje nowe
stacje, przywraca znalezione wpisy katalogowe bez niszczenia ich bogatszych
nazw i metadanych oraz pomija rzeczywiste duplikaty. Identyfikatory powstają
wyłącznie w hoście i służą tylko do zapisu oraz przywrócenia fokusu; NVDA
otrzymuje nazwę stacji i krótkie podsumowanie importu.

`Ctrl+E` eksportuje Ulubione radia również z listy i z odtwarzacza. Natywne
okno zapisu udostępnia przenośny M3U oraz JSON zgodny z VRadio i ponownym
importem AMC. Eksporter C# zachowuje aktualny porządek Ulubionych: według
dodania z najnowszymi u góry, alfabetyczny albo własny. Do pliku trafiają
wyłącznie użytkowa nazwa oraz stabilny adres HTTP(S); nie trafiają
identyfikatory AMC, chwilowe adresy odtwarzania ani adresy zawierające dane
logowania. Zapis jest atomowy i kończy się krótkim komunikatem z liczbą stacji.

Host pozostaje jedynym właścicielem `state.json` i trwałych kolejności w
`library.db`. Dodanie oraz import aktualizują jednocześnie kolejność własną i
według dodania, a zapis jest blokowany, jeśli działa stare główne AMC, aby dwa
procesy nie mogły nadpisać sobie profilu. Prywatny tryb demonstracyjny nadal
korzysta z własnego magazynu i z importera jedynie odczytującego plik.

### Podcasty i YouTube

Działa przeglądanie źródeł i odcinków, odtwarzanie przez wspólny silnik,
zapisywanie postępu, kolejka, historia, pobrane materiały, import i eksport
OPML oraz obsługa źródeł YouTube. Działa również automatyczne odświeżanie
według indywidualnego terminu źródła i globalnego limitu partii; zapis wykonuje
wyłącznie właściciel bazy po stronie C#. Eksport subskrypcji YouTube do przenośnego
formatu zgodnego z innymi aplikacjami pozostaje osobnym zadaniem.

### TIDAL

Odtwarzanie pozostaje zgodne z obecnym, sprawdzonym rozwiązaniem głównego AMC:
AMC przekazuje utwór, album albo widoczną listę do oficjalnej aplikacji TIDAL.
Nie udajemy własnego pełnego odtwarzacza TIDAL ani możliwości, których nie daje
obecna integracja. Pauza i wznowienie zależą od sterowania sesją systemową;
następny i poprzedni utwór mogą zależeć od oficjalnej aplikacji.

Odbiór użytkownika 11 października pozostawił odtwarzanie do weryfikacji.
Oficjalna aplikacja TIDAL była uruchomiona i znajdowała się w pauzie. AMC
przekazało utwór, a interfejs sprawiał wrażenie, że materiał jest odtwarzany,
jednak nie było słyszalnego dźwięku. Nie należy uznawać tej drogi za odebraną
wyłącznie na podstawie widocznego stanu. Trzeba sprawdzić rzeczywisty start w
oficjalnym TIDAL, stan sesji systemowej, wyciszenie, głośność i wybrane
urządzenie wyjściowe oraz potwierdzić słyszalny odsłuch. Przyczyna nie została
jeszcze ustalona.

Interfejs wxPython obsługuje teraz:

- `Ctrl+Shift+L` — dodanie lub usunięcie albumu, wykonawcy albo playlisty z
  Biblioteki TIDAL;
- `Ctrl+Shift+U` — dodanie lub usunięcie utworu albo materiału wideo z
  Ulubionych TIDAL;
- `Ctrl+Shift+Q` — dodanie lub usunięcie zaznaczonych utworów z prywatnej,
  trwałej Kolejki interfejsu wxPython;
- `Ctrl+Q` — otwarcie tej Kolejki;
- `Alt+1` — porządek według dodania, z najnowszymi pozycjami na początku;
- `Alt+2` — porządek alfabetyczny zgodny z porównywaniem hosta AMC;
- `Alt+3` — kolejność własna zapisana przez TIDAL;
- Enter na utworze lub albumie — przekazanie odtwarzania do oficjalnego TIDAL.

Biblioteka i Ulubione są zmieniane przez istniejącą oficjalną integrację C#.
Kolejka TIDAL jest na tym etapie prywatna dla interfejsu wxPython i nie jest
współdzielona z kolejką głównego AMC ani oficjalnej aplikacji TIDAL. Tokeny i
prywatne uchwyty odtwarzania nie przechodzą do Pythona ani do tekstu list.

Sortowanie jest podłączone w trzech równorzędnych korzeniach kolekcji TIDAL:
Bibliotece, Ulubionych i Playlistach. Wybrany tryb jest pamiętany osobno dla
każdego widoku, zachowuje bieżący element według jego stabilnego ID i nie
przechodzi na album, wykonawcę ani Kolejkę. Znacznik czasu dodania pozostaje
wewnętrzną wartością modelu i nie trafia do nazwy dostępnej ani mowy NVDA.
Brak prywatnego wyboru dziedziczy ustawienie z profilu głównego AMC, ale zapis
AMC Python nie modyfikuje tego profilu. Pozostaje żywy odbiór kolejności na
rzeczywistym koncie TIDAL i mowy po każdej zmianie.

Kontekstowa prawa strzałka jest przywrócona zgodnie z głównym AMC. Gdy są dwa
rzeczywiste cele, otwiera natywne menu z przejściem do albumu lub wykonawcy.
Gdy cel jest tylko jeden, na przykład wykonawca z dostępną listą albumów,
przechodzi od razu bez zbędnej zapowiedzi „menu kontekstowe”. Enter na
wykonawcy nadal otwiera osobny przegląd trzech kategorii:
Albumy, Utwory i Podobni wykonawcy. Po zamknięciu menu fokus wraca na listę,
Backspace z otwartej relacji przywraca wcześniejszy element, a techniczne ID
albumu i wykonawcy pozostają wyłącznie w modelu. Pozostaje odbiór z żywym
kontem i NVDA. Dla przyszłej sesji Spotify należy później przeprowadzić osobne
porównanie, ponieważ podobny cel nie oznacza identycznego API ani układu.

### Wyszukiwanie

12 października przeniesiono pierwszą działającą całość `Ctrl+F`
(bieżąca sesja/usługa) i `Ctrl+Shift+F` (wyszukiwanie globalne). To osobne,
natywne okno z polem zapytania i zwykłą listą Windows; `Ctrl+K` nadal jedynie
filtruje elementy już widoczne i nie zmienił znaczenia. Wyszukiwanie lokalne
ignoruje wielkość liter oraz znaki diakrytyczne, wymaga wszystkich słów i
obejmuje komplet zapisanych Plików, Bibliotekę Radia, wszystkie zapisane
podcasty wraz ze wszystkimi odcinkami (bez ograniczenia do pierwszych 150)
oraz zapisany katalog TIDAL. Awaria jednego źródła nie usuwa wyników z innych.

Enter wraca do właściwej sesji, listy i stabilnego elementu. Lista obsługuje
lewą strzałkę, wielokrotne zaznaczenie Shift/Ctrl+Spacja, `Ctrl+C`,
`Ctrl+Shift+C` oraz skróty działań znane z głównego AMC: odtwarzanie,
Kolejkę/„jako następne”, Ulubione, Bibliotekę, playlistę, preset, informacje i
pobieranie podcastu. Wartości techniczne, identyfikatory i reprezentacje
obiektów nie trafiają do nazw dostępnościowych.

Historia zapytań jest zapisywana osobno dla bieżących sesji i zakresu
globalnego; przy pustym polu strzałki w dół/w górę przeglądają ją jak w
głównym AMC. Do domknięcia parytetu pozostają wyniki pobierane na żywo z
internetowych katalogów (Radio Browser, Apple/Spreaker/YouTube i wyszukiwanie
TIDAL). Relacje katalogowe TIDAL pod prawą strzałką są podłączone osobno.
Obecne wyniki wyszukiwania są prawdziwe, ale
pochodzą wyłącznie z kompletnego lokalnego cache'u. Potrzebny jest też żywy
odbiór NVDA okna, skrótów i powrotu fokusu; testy automatyczne nie zastępują
tego pomiaru.

### WiiM

Sesja WiiM jest podłączona do istniejących usług AMC. Odbiór 10 października
potwierdził prawidłowe wykrycie urządzenia i odczyt jego stanu. Udało się także
uruchomić i zatrzymać stację. `F6` przełącza pomiędzy otwartym odtwarzaczem a
listą urządzeń/odtwarzaczy. Pełne AMC celowo nie pokazuje w WiiM Biblioteki
ani Ulubionych: lokalne API urządzenia nie udostępnia katalogów WiiM Home,
dlatego `Ctrl+L` pozostaje nieaktywny, a materiały AMC są osobnym widokiem
Strumieni sieciowych pod `Ctrl+O`.

Strumienie sieciowe są już przeniesione: działają lista, odtwarzanie, dodanie,
edycja i usunięcie, import M3U/PLS, eksport M3U, trzy sposoby sortowania oraz
powrót do właściwego urządzenia. Do wxPython nie przechodzą adresy urządzeń;
adres strumienia jest pobierany wyłącznie do jawnie otwartego okna edycji.

Natywne presety urządzenia są już podłączone technicznie pod `Ctrl+Alt+P`.
Host zwraca dokładnie 12 miejsc bez adresów urządzenia i strumieni, wskazuje
bieżące miejsce, blokuje puste pozycje oraz zachowuje wyjaśnienie z głównego
AMC dla presetów TIDAL/Spotify Connect, których urządzenie nie potrafi samo
uruchomić. Dialog obsługuje cyfry, Page Up/Page Down, Enter i Spację, a po
powodzeniu przechodzi do odtwarzacza WiiM. Pozostaje odbiór z żywym
urządzeniem. `Ctrl+Shift+1–0/-/=` uruchamia teraz mapowanie właściwe dla
wybranego urządzenia, a `Ctrl+Alt+Shift+P` przypisuje istniejący natywny
preset bez zmiany ustawień samego WiiM. Brak prywatnej zmiany dziedziczy
istniejące mapowanie głównego AMC, a gdy go nie ma — odpowiadające miejsce
natywne. Identyfikator urządzenia i numer modelu nie trafiają do etykiet
dostępnościowych. W odtwarzaczu przeniesiono również klawisze pełnego AMC:
`I` wybiera wejście, `O` wyjście, `E` ustawienie korektora, `R` tryb
powtarzania, `S` przełącza losowanie, a `T` ustawia timer uśpienia. Każdy
dialog otrzymuje od hosta osobne wartości modelu i jawne etykiety użytkowe;
adres urządzenia, obiekt stanu i nazwy właściwości nie trafiają do NVDA.
Pozycje menu są widoczne wyłącznie w sesji WiiM i aktywne dopiero w jej
odtwarzaczu. `Alt+Page Up` i `Alt+Page Down` przenoszą ten sam mechanizm co
pełne AMC: jeżeli bieżącym źródłem jest zapisany strumień AMC, przechodzą
kołowo po strumieniach w aktualnym porządku widoku; w przeciwnym razie
przechodzą po zajętych presetach urządzenia. Presety TIDAL Connect, Spotify
Connect i inne źródła odbiorcze są pomijane, ponieważ urządzenie nie potrafi
uruchomić ich samodzielnie. Host pamięta źródło osobno dla urządzenia, a do
Pythona zwraca wyłącznie bezpieczną migawkę i komunikat użytkowy. Pozostaje
żywy odbiór wszystkich nowych dróg.

### Sonos

Dodano sesję Sonos korzystającą z tego samego magazynu poświadczeń Windows i
istniejącego klienta C# co główne AMC. Python otrzymuje wyłącznie celowe nazwy
grup i bezpieczny stan odtwarzania. Dostępne są wybór grupy, odtwarzanie,
pauza, następny/poprzedni, seek i głośność. Tokeny Sonos nie opuszczają C#.

Odbiór użytkownika 10 października ujawnił błąd: AMC widział grupę Sonos i
odczytywał jej stan (np. „Radio Opole, myTuner Radio, Zatrzymane, 5 procent,
bez wyciszenia”), ale polecenia sterowania nie były wykonywane. Program mówił:
„Nie udało się sterować grupą Sonos: Trwa odczyt informacji. Powtórz skrót za
chwilę”, a ponowienie po chwili nie odblokowywało sterowania.

Poprawka techniczna jest już wprowadzona. Odczyt początkowy, ciche
odświeżanie z timera i polecenia transportu korzystają z jednego kolejnego
toru. Polecenie naciśnięte podczas odczytu czeka i wykonuje się po nim, zamiast
zajmować następne miejsce współbieżne hosta. Chwilowa odmowa
`operation_busy` jest ponawiana w tle do pięciu sekund bez odczytywania tego
technicznego stanu użytkownikowi. Nowy wybór grupy zastępuje oczekujący stary
wybór, a nie uruchamia drugiego odczytu równolegle. Testy automatyczne obejmują
blokadę timera, kolejkę poleceń oraz ponowienie odczytu i transportu. Pozostaje
odbiór na żywej, obudzonej grupie Sonos.

Warstwa materiałów Sonos jest już przeniesiona: osobny korzeń Biblioteki,
Ulubione Sonos, Playlisty Sonos i własne strumienie AMC, odczyt zawartości,
uruchamianie na aktywnej grupie, edycja/import/sortowanie i ręczna kolejność
własnych strumieni oraz ich eksport M3U. Materiał można przypisać do jednego z
12 presetów sesji i uruchomić przez `Ctrl+Shift+1–0/-/=`. Opcjonalny cel stały
zapisuje dokładny zestaw głośników i przed odtworzeniem wymaga jednej zgodnej
grupy w tym samym domu; nie przegrupowuje urządzeń po cichu. Identyfikatory
domu, grupy, odtwarzaczy i materiałów pozostają wyłącznie w modelu.

Próba uruchomienia widocznego Radia Opole ze starego przyrostu została
przyjęta przez interfejs, ale radio faktycznie nie zaczęło grać. Dlatego
automatyczne testy nowej warstwy nie zastępują ponownego odbioru na obudzonej
grupie. Pozostają wejścia/wyjścia, korektor, powtarzanie, timer i inne opcje
urządzeń, których jeszcze nie przeniesiono.

Obecna konfiguracja rozpoznaje zapisane konta i urządzenia, więc do tej
naprawy nie potrzeba ponownej autoryzacji. Przed przekazaniem programu innym
testerom trzeba osobno zaprojektować zrozumiałe, dostępne logowanie i zapis
poświadczeń. Użytkownik nie powinien być pozostawiany z niewyjaśnionymi
kodami aplikacji ani technicznymi identyfikatorami; ten etap pozostaje na
koniec, po ustabilizowaniu funkcji streamerów.

Do projektowania sesji Sonos w AMC dodano pomocniczy materiał z Hermesa:
`D:\Projekty Codex\Hermes\AMC-Python-proba-list-20261005\SONOS-REDUX-2026-10-11-DLA-AMC.md`.
Nie jest to gotowa implementacja Sonosa ani zadanie testowania dodatku Sonos
Redux. Przy poprawkach AMC można wziąć pod uwagę wyłącznie ogólne wskazówki,
jeżeli ten sam przypadek rzeczywiście występuje w naszym interfejsie: skróty
zależne od kontekstu, nieprzejmowanie klawiszy własnych kontrolek oraz brak
spóźnionego powrotu fokusu po opuszczeniu widoku. Nie należy analizować ani
naprawiać zachowania fokusu w obcym dodatku, uruchamiać go z NVDA ani tworzyć
dla niego osobnych testów. Funkcje Sonosa w AMC nadal przenosimy z głównego
AMC i jego klienta C#, a nie z Sonos Redux. Sonos Redux steruje aplikacją
Sonos Desktop przez UI Automation i jest objęty GPL-2.0-only, dlatego nie
kopiujemy jego implementacji. Szczegółowy podział zakresu jest także w
`PROJEKT_SONOS_PL.md`.

### Spotify

Nowa sesja Spotify jest świadomie odłożona. Nie należy jej wdrażać w obecnym
etapie ani zużywać na nią czasu przed odbiorem istniejących sesji.

## Dostępność i NVDA

Listy i dialogi pozostają natywnymi kontrolkami wxPython. Nie dodajemy własnych
nakładek dostępnościowych bez potwierdzonej potrzeby. Każdy wiersz ma celową,
użytkową etykietę; identyfikatory, nazwy klas, rekordy i reprezentacje obiektów
nie mogą być czytane przez NVDA. Po zmianie listy należy sprawdzić pierwszy
element, ruch strzałkami, zaznaczenia Shift i Ctrl+Spacja, powrót fokusu,
ponowne otwarcie widoku oraz mowę po Escape.

W widoku nagranych plików `Alt+Shift+R` usunięto powtarzany prefiks „Nagrane”
ze zwykłych ukończonych wpisów. Wiersz zaczyna się od nazwy stacji lub pliku;
znaczące stany wyjątkowe, takie jak „Przerwane”, „Nieudane” albo brak pliku,
pozostają czytelne.

Historia nagrywania `Alt+Shift+R` zachowuje teraz ostatnie wpisy także po
restarcie AMC Python, scala je bez duplikatów z bieżącą sesją i nie zastępuje
historii szerokim skanem całych folderów Biblioteki. Ukończony wpis jest
pokazywany tylko wtedy, gdy jego dokładny plik nadal istnieje; wpisy nieudane
pozostają jako diagnostyka. Lista jest ograniczona do 100 najnowszych pozycji.
`Shift+F2` przekazuje hostowi rzeczywistą ścieżkę wiersza historii, więc zmiana
nazwy nie zależy już od technicznego identyfikatora listy. Host odnajduje
odpowiadający wpis Biblioteki, a gdy go nie ma, bezpiecznie zmienia nazwę
istniejącego pliku i aktualizuje ścieżkę historii.

Dziennik 13 października potwierdza uruchomienie harmonogramu o 18:13. Nagranie
z Jarosławia zakończyło się powodzeniem, natomiast Tarnobrzeg i Dominikanie
Rzeszów nie zostały nagrane, ponieważ nie udało się odtworzyć ich źródeł
YouTube Live. Była to odmowa konkretnych strumieni, a nie brak uruchomienia
harmonogramu.

Przy zaznaczaniu fragmentu `I`/`O` interfejs pyta host jawnie o tor Plików
albo Podcastów. Okresowy odczyt Radia nie może już podmienić kontekstu i
wywołać fałszywego komunikatu, że nagranie nie jest plikiem multimedialnym.
Prywatny dziennik interfejsu zapisuje przy odmowie techniczny stan sesji,
tożsamości, ścieżki, czasu i dostępności pliku, ale NVDA otrzymuje wyłącznie
krótki komunikat użytkowy. Na rzeczywistym pliku
`2 - 2026-10-12 22-02-19.mp3` potwierdzono metadanymi Windows stan lokalny i
zgodę wspólnej polityki Core na edycję; sama ścieżka iCloud nie jest podstawą
do żądania ponownego pobrania.

Na liście harmonogramów `Ctrl+Shift+H` Spację podłączono bezpośrednio do
natywnej listy, oprócz dotychczasowego haka całego okna. Rozpoznanie celu
uwzględnia obiekt zdarzenia i rzeczywisty fokus; zmiana zachowuje wiersz, podaje
nazwę planu i nowy stan oraz zapisuje ją w hoście. Pozostaje żywy odbiór z
NVDA, ponowne otwarcie okna i restart programu.

Odbiór użytkownika w paczce
`.test-output\AMC-Python-next-status-20261010` wykazał również, że po
`Ctrl+C` NVDA nadal mówi angielskie „Copy”. Paczka zawiera bieżącą próbę
przechwycenia skrótu, a jej `gui.py` ma ten sam SHA-256 co źródło, więc nie
jest to pomylenie wersji. Dotychczasowa poprawka i test bezokienny są
niewystarczające; błąd pozostaje otwarty i wymaga pomiaru kolejności zdarzeń
klawiatury/UI Automation z żywym NVDA.

13 października podłączono AMC Python do gotowego dodatku AMC do NVDA.
LiteHost wystawia ten sam zabezpieczony, lokalny protokół
`AMC.NVDA.v1.<sesja Windows>`, z którego korzysta główne AMC. Dzięki temu
pozostają jedna wtyczka, jedna mapa gestów i dotychczasowe ustawienia
użytkownika; stary proces AMC nie jest pośrednikiem. Host C# zachowuje
ograniczenie potoku do bieżącego konta, wersję protokołu, allow-listę i limity,
a zweryfikowane polecenie przekazuje do działającego frontendu wxPython.

Za pośrednictwem tego mostu dostępne są transport, przewijanie i czasy,
głośność i wyciszenie, zakładki, Ulubione, Kolejka, radio i nagrywanie,
przełączanie sesji, 12 bezpośrednich presetów oraz polecenia otwierające
istniejące widoki. Odczyty stanu, kontekstu i bieżącego materiału zwracają
wyłącznie tekst użytkowy. Dla TIDAL-a nie są zgadywane pauza ani odtwarzanie:
bez zapamiętanej migawki aplikacja mówi tylko, że sterowanie odbywa się w
oryginalnym TIDAL-u. W sesji Radia odczyt stanu rozróżnia również nagrywanie,
nagrywanie wstrzymane, przygotowywanie i zatrzymywanie nagrania. Stan jest
dopisywany tylko wtedy, gdy aktywne nagranie należy do faktycznie odtwarzanej
stacji; nagranie innej stacji w tle nie jest błędnie przypisywane do odsłuchu.

Poprzedni i następny preset są już wykonywane bez otwierania okna: puste
miejsca są pomijane, koniec listy zawija się na początek, a stan jest liczony
osobno dla każdej sesji. `Ctrl+Shift+S` oraz polecenie dodatku „Lista sesji”
otwierają natywną listę sześciu sesji z jednoznacznymi etykietami
`Ctrl+1`–`Ctrl+6`; wybrana jest bieżąca sesja, Enter przełącza, a Escape wraca
bez zmiany. `Ctrl+0` nie ma już przypisanej funkcji, ponieważ dublował tę samą
listę. Kolejność sześciu sesji można zmienić w Ustawieniach; ta sama kolejność
określa znaczenie `Ctrl+1`–`Ctrl+6`, menu, listę sesji i paletę poleceń.
`Ctrl+Page Up` i `Ctrl+Page Down` przechodzą do poprzedniej lub następnej sesji
w tej kolejności, z zawinięciem na końcach.
Paleta poleceń jest dostępna pod `Ctrl+Shift+K` i przez gotowy dodatek NVDA.
Pokazuje wyłącznie jawne nazwy i skróty poleceń widocznych dla bieżącej sesji,
filtruje bez rozróżniania wielkości liter i polskich znaków, a Enter wykonuje
wybraną istniejącą akcję tą samą drogą co menu lub skrót.
Jawnie, bez podstawiania podobnej czynności, odmawiane są funkcje jeszcze
nieobecne w AMC Python: wyciszenie wszystkich sesji oraz rozdziały. Dodatek
może sterować tylko jednym właścicielem wspólnego potoku.
Dlatego żywy odbiór AMC Python trzeba
wykonać przy zamkniętym starym AMC; równoległe uruchomienie dwóch wersji nie
daje wyboru celu w obecnym protokole. Szczegółowy kontrakt i kryteria odbioru
są opisane w `PROJEKT_NVDA_PL.md`.

## Aktualizacje i zgłaszanie błędów

Pakiet zawiera już wykonywalny `AMC-Python-Updater.exe`. Aktualizator sprawdza
kompletny manifest i sumy SHA-256, przygotowuje kopię zapasową oraz potrafi
wycofać nieudaną podmianę. Nie ma jeszcze opublikowanego kanału wydań AMC
Python ani automatycznego pobierania paczki, więc nie należy przedstawiać go
jako ukończonej aktualizacji internetowej. EdSharp NG pozostaje punktem
odniesienia dla zachowania pełnego mechanizmu aktualizacji.

13 października rzeczywista próba ujawniła dwa problemy samowymiany. Kopia
robocza mogła rozpocząć podmianę, zanim proces uruchomiony z katalogu programu
faktycznie zwolnił swój plik, a `File.Move` z zastąpieniem istniejącego EXE
zwracał odmowę dostępu mimo braku działającego procesu. Pomocnik dostaje teraz
osobny identyfikator procesu-rodzica i czeka na jego zakończenie; po wykonaniu
kopii bezpieczeństwa usuwa stary plik i przenosi nowy, nadal korzystając z
pełnego wycofania całej transakcji przy dowolnym błędzie. Błędy trafiają także
na standardowe wyjście diagnostyczne, a nie tylko do okna komunikatu. Pełną
samowymianę sprawdzono na osobnej kopii 597-plikowej paczki: aktualizator i
LiteHost miały po operacji właściwe sumy, a katalog transakcji nie pozostał.
Aktualizator sprawdza teraz przed utworzeniem katalogu transakcji wszystkie
procesy uruchomione z folderu instalacji, nie tylko PID przekazany przez
launcher. Pozostawiony `runtime\python.exe` albo `host\amc_lite_host.exe`
powoduje bezpieczną odmowę z kodem 3, bez częściowej podmiany i bez nowego
katalogu `.aktualizacja-*`. Osobny test uruchamia rzeczywisty proces z próbnej
instalacji i potwierdza jego wykrycie.
Aktualizację kanonicznego katalogu wolno wykonać przy zamkniętym AMC Python.
Działającego głównego AMC nie zamyka się w tym celu, jeżeli trwa w nim
nagrywanie. Po podmianie nie uruchamia się AMC Python równolegle z głównym AMC,
ponieważ host i tak bezpiecznie odmówi zapisu do wspólnego profilu.

„Sygnalista” (`michaldziwisz/sygnalista`) jest osobnym modułem zgłaszania
błędów, a nie nazwą aktualizatora. Przed jego integracją trzeba sprawdzić
licencję i rzeczywisty kontrakt biblioteki; nie wolno kopiować niesprawdzonego
kodu ani wysyłać logów bez wiedzy użytkownika.

## Dowody automatyczne tego przyrostu

- pełny runner Python: 1465 zaliczonych, 0 błędów, 138 historycznych pominięć;
- testy protokołu C#: 15 zestawów zaliczonych;
- całe rozwiązanie .NET zbudowane sekwencyjnie: 0 ostrzeżeń, 0 błędów;
- sześć celowanych testów Windows rozpoznawania, ustawień, historii, podpisu
  Shazam i łączy wyszukiwania: wszystkie zaliczone;
- LiteHost zbudowany i opublikowany dla Windows x64 bez błędów i ostrzeżeń;
- pakiet uruchomieniowy przeszedł sprawdzenie środowiska z Pythonem 3.14.7,
  wxPython 4.3.1 i nowym hostem.
- 9 testów kontraktu `AMC.exe` i aktualizatora: poprawna paczka, uszkodzenie,
  niezgodny protokół, wyjście ścieżką poza katalog, prywatny runtime,
  diagnostyka, jedna instancja oraz rozpoznanie ścieżek i żywego procesu
  instalacji;
- 21 celowanych testów układu paczki, startu i komunikatów: 21 zaliczonych,
  0 błędów;
- rzeczywisty `AMC.exe --sprawdz-pakiet-cicho`: kod 0; próbna pełna podmiana
  przez `AMC-Python-Updater.exe`: kod 0; ponowna weryfikacja celu: kod 0.

Testy protokołu dowodzą granic danych i obsługi poleceń. Nie zastępują odbioru
żywego konta TIDAL, urządzeń WiiM/Sonos ani mowy NVDA.

Drugie równoległe uruchomienie interfejsu jest blokowane przed otwarciem okna.
Zapobiega to sytuacji, w której starszy host trzyma zapis postępu podcastów,
a nowe okno pokazuje listy, lecz nie wykonuje Enter, Ctrl+R ani informacji pod
lewą strzałką.

## Najbliższa kolejność prac

1. Wykonane technicznie 12 października: zastąpienie wydaniowego startu przez
   `.cmd` jednym `AMC.exe`, który uruchamia dołączony runtime bez konsoli,
   sprawdza manifest i wersje oraz współpracuje z `AMC-Python-Updater.exe`.
   Pozostaje trzyczęściowy żywy odbiór jednej instancji z NVDA i nagrywaniem.
2. W toku: technicznie rozdzielono Radio i Multimedia, ich stan, pauzę,
   głośność, tempo i urządzenie. `Ctrl+M` ma osobny stan, dynamiczną
   nazwę i zaznaczenie w menu bieżącej lokalnej sesji. Pozostaje żywy odbiór
   równoczesnego dźwięku, przełączania wyjść i wyciszenia.
3. W toku: `Ctrl+F` i `Ctrl+Shift+F` mają już osobne natywne okno, pełny
   lokalny cache, historię zapytań, skróty działań oraz powrót do właściwej
   listy. Domknąć zdalne katalogi i żywy odbiór NVDA. Prawa strzałka TIDAL ma
   już natywne menu relacji zgodne z głównym AMC.
   Powtarzany prefiks „Nagrane” usunięto z ukończonych wierszy `Alt+Shift+R`;
   stany nieudane, przerwane, zatrzymane i brak pliku pozostają w etykiecie.
4. W toku: `Ctrl+,` ma już natywne karty Ogólne, Radio i nagrywanie oraz
   Komunikaty, zapis Enterem i jedno potwierdzenie. Karta Radia wykonuje
   ustawienia TimeShift, folderu, formatu, bitrate'u i wybudzania. Działają też
   wybór pauzy po utracie wyjścia oraz `Ctrl+[` i `Ctrl+]`; Spację harmonogramu
   podłączono bezpośrednio do listy. Karta Komunikaty zapisuje już rzeczywiste
   przełączniki przewijania, głośności i odtwarzania/pauzy, a
   także nadrzędny przełącznik „Włącz komunikaty dostępności”. Ten ostatni
   jest zapisywany prywatnie przez AMC Python, działa od razu po zatwierdzeniu
   i nie modyfikuje profilu starego interfejsu. `Ctrl+Shift+G` korzysta z tego
   samego prywatnego stanu. Rozpoznawanie
   utworów i wspólny folder z Podcastami są już przeniesione technicznie;
   pozostaje żywy odbiór wyniku, historii i komunikatów z NVDA. Następnie
   przepisać pozostałe trzy karty
   głównego AMC ze wszystkimi polami, zależnościami i zapisem oraz wykonać
   pełny audyt Biblioteki, menu, skrótów i sortowań `Alt+cyfra`.
5. W toku: WiiM ma Strumienie sieciowe, natywne presety i ich mapowania
   `Ctrl+Shift+1–0/-/=` osobno dla urządzeń. Jego odtwarzacz ma już wejście,
   wyjście, korektor, powtarzanie, losowanie, timer oraz przechodzenie
   `Alt+Page Up`/`Alt+Page Down` po faktycznie aktywnym rodzaju źródła. Sonos ma
   Bibliotekę, Ulubione, playlisty, własne strumienie, presety oraz cel bieżącej
   lub stałej grupy. Wykonać ponowny odbiór obu transportów i materiałów na
   obudzonych urządzeniach, a potem uzupełnić wyłącznie brakujące opcje
   swoiste dla Sonosa. Techniczna kolejka operacji jest już podłączona. Materiał
   Sonos Redux z Hermesa
   traktować tylko jako krótką wskazówkę projektową, gdy analogiczny problem
   wystąpi w AMC; nie przeznaczać przebiegów na analizę, uruchamianie ani testy
   tego obcego dodatku NVDA i nie kopiować kodu GPL.
6. Sortowanie Biblioteki, Ulubionych i Playlist TIDAL jest przywrócone
   technicznie pod `Alt+1`, `Alt+2` i `Alt+3`, a prawa strzałka ma natywne menu
   relacji; pozostaje odbiór obu funkcji na żywym koncie. Następnie
   zweryfikować słyszalne odtwarzanie przekazanego utworu w oficjalnej
   aplikacji TIDAL, łącznie z sesją systemową i urządzeniem wyjściowym.
7. Podłączenie gotowego dodatku AMC do NVDA bezpośrednio do LiteHosta i
   wxPython, bez uruchamiania starego AMC, jest wykonane technicznie. Działają
   też poprzedni/następny preset, natywna Lista sesji oraz Paleta poleceń.
   Pozostaje żywy odbiór mowy, brajla, filtrowania i fokusu po Enter/Escape
   oraz po ponownym otwarciu obu list.
8. Uzupełnienie wykrytych braków w istniejących sesjach, bez regresji radia,
   nagrywania, harmonogramów i timeshiftu.
9. Odzyskanie źródła lub ticketu „Sygnalisty”, analiza i wdrożenie aktualizacji.
10. Dopiero później decyzja o Spotify; wtedy osobno przenieść właściwe dla
   Spotify sortowanie i kontekstową nawigację, bez kopiowania założeń TIDAL.

Publikacja AMC Python na GitHubie jest końcowym krokiem, nie częścią bieżącego
zapisu planu. Przed nią trzeba odebrać działanie samodzielnego pakietu, radia,
nagrywania i harmonogramów, WiiM, Sonosa oraz gotowego dodatku NVDA, sprawdzić
pakiet pod kątem prywatnych danych i uzyskać aktualną decyzję użytkownika o
publikacji konkretnego stanu. Do tego czasu zmiany pozostają lokalne.

