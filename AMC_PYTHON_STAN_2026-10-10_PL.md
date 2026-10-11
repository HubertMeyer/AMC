# AMC Python — stan prac 10 października 2026

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
procesów. Docelowo jeden uruchamiacz EXE ma nadzorować start, jedną instancję,
zgodność wersji i bezpieczne zamknięcie całego pakietu.

Odbiór użytkownika potwierdził, że obecny start przez `AMC-wx-Lite.cmd` jest
zbyt niejednoznaczny: można trafić na niewłaściwy runtime lub widoczny proces
interpretera i nie mieć pewności, która kopia programu faktycznie ruszyła.
Przed dalszym normalnym używaniem trzeba dostarczyć jeden użytkowy `AMC.exe`.
Ma on uruchamiać dołączony prywatny runtime i właściwy LiteHost bez konsoli,
bez systemowego Pythona, `PYTHONPATH` i skryptów wsadowych; sprawdzać zgodność
wersji oraz manifest; pilnować jednej instancji i bezpiecznej odmowy zamknięcia
podczas nagrywania; pokazywać dostępny komunikat przy błędzie i uruchamiać
program ponownie po udanej aktualizacji.

Istniejący `AMC-Python-Updater.exe` pozostaje osobnym wykonawcą bezpiecznej
podmiany i wycofania plików. Docelowe `AMC.exe` ma być stałym punktem wejścia,
a aktualizator działać za nim, bez ręcznego wybierania skryptu lub interpretera.

### Niezależne odtwarzanie sesji i urządzenia audio

Wykryto poważną regresję względem głównego AMC: gdy gra radio internetowe,
uruchomienie pliku w sesji Multimedia zatrzymuje radio. Docelowo każda sesja
ma własny tor, urządzenie wyjściowe, stan pauzy i wyciszenia. Radio i plik mają
móc grać równolegle, także na dwóch różnych urządzeniach. Przejście do sesji
zmienia tylko cel sterowania; `Spacja` i `Ctrl+M` działają wyłącznie na
aktywnej sesji i nie wpływają na pozostałe.

Polityka zaniku urządzenia ma stać się ustawieniem. Użytkownik wybiera, czy po
utracie wybranego wyjścia odsłuch ma automatycznie trwać na urządzeniu
domyślnym, czy przejść w pauzę po bezpiecznym przełączeniu na urządzenie
domyślne. Pauza odsłuchu nie zatrzymuje nagrywania radia ani bufora timeshift.
Do odtwarzacza należy też dodać `Ctrl+[` i `Ctrl+]`, które cyklicznie wybierają
odpowiednio poprzednie i następne dostępne urządzenie audio dla bieżącej sesji
i podają wyłącznie jego użytkową nazwę. Wybór pozostaje zapamiętany osobno dla
sesji.

### Pełny audyt interfejsu i ustawień

`Ctrl+,` nie otwiera obecnie pełnych Ustawień. Działające opcje odtwarzania
sesji lub elementu są innymi dialogami i nie zastępują ustawień programu.
Nie wystarczy dopisać kart Ogólne, Podcasty i Radio: trzeba przepisać całe
Ustawienia dokładnie z głównego AMC, po uprzednim spisie wszystkich kart, pól,
wartości domyślnych, zależności, walidacji i miejsc zapisu. `Ctrl+Tab` i
`Ctrl+Shift+Tab` mają przechodzić pomiędzy wszystkimi kartami z prawidłowym
fokusem i odczytem NVDA; Zapisz, Anuluj i ponowne otwarcie muszą zachowywać
semantykę głównego AMC.

Cały interfejs wymaga porównania z głównym AMC: wszystkie menu i skróty,
organizacja Biblioteki, wejścia i powroty z podlist oraz właściwe warianty
sortowania `Alt+cyfra` dla każdej sesji i każdego widoku. Częściowe działanie
jednego widoku nie jest dowodem kompletnego portu. Audyt ma zakończyć się
jawną macierzą widok–skrót–działanie–powrót, bez technicznych identyfikatorów
w etykietach dostępności.

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

### Podcasty i YouTube

Działa przeglądanie źródeł i odcinków, odtwarzanie przez wspólny silnik,
zapisywanie postępu, kolejka, historia, pobrane materiały, import i eksport
OPML oraz obsługa źródeł YouTube. Eksport subskrypcji YouTube do przenośnego
formatu zgodnego z innymi aplikacjami pozostaje osobnym zadaniem.

### TIDAL

Odtwarzanie pozostaje zgodne z obecnym, sprawdzonym rozwiązaniem głównego AMC:
AMC przekazuje utwór, album albo widoczną listę do oficjalnej aplikacji TIDAL.
Nie udajemy własnego pełnego odtwarzacza TIDAL ani możliwości, których nie daje
obecna integracja. Pauza i wznowienie zależą od sterowania sesją systemową;
następny i poprzedni utwór mogą zależeć od oficjalnej aplikacji.

Interfejs wxPython obsługuje teraz:

- `Ctrl+Shift+L` — dodanie lub usunięcie albumu, wykonawcy albo playlisty z
  Biblioteki TIDAL;
- `Ctrl+Shift+U` — dodanie lub usunięcie utworu albo materiału wideo z
  Ulubionych TIDAL;
- `Ctrl+Shift+Q` — dodanie lub usunięcie zaznaczonych utworów z prywatnej,
  trwałej Kolejki interfejsu wxPython;
- `Ctrl+Q` — otwarcie tej Kolejki;
- Enter na utworze lub albumie — przekazanie odtwarzania do oficjalnego TIDAL.

Biblioteka i Ulubione są zmieniane przez istniejącą oficjalną integrację C#.
Kolejka TIDAL jest na tym etapie prywatna dla interfejsu wxPython i nie jest
współdzielona z kolejką głównego AMC ani oficjalnej aplikacji TIDAL. Tokeny i
prywatne uchwyty odtwarzania nie przechodzą do Pythona ani do tekstu list.

Do poprawy w następnym etapie pozostaje porządek albumów. Obecnie albumy są
pokazywane według czasu dodania od najstarszych u góry i nie można zmienić
sortowania. Główne AMC udostępniało co najmniej porządek alfabetyczny,
własny/ręczny oraz według dodania, przy czym w tym ostatnim najnowsze pozycje
były u góry. Należy przenieść ten sam model, zapamiętanie wyboru i dostępne
etykiety opcji, po uprzednim porównaniu z kodem głównego AMC.

Trzeba też przywrócić kontekstową prawą strzałkę. Na albumie prowadziła do
wykonawcy; na wykonawcy otwierała właściwe zbiory wykonawcy, między innymi
albumy, utwory i podobnych wykonawców zgodnie z dokładnym zachowaniem głównego
AMC. Powrót, fokus i wszystkie działania na otwartych listach muszą zachować
się tak samo. Dla przyszłej sesji Spotify należy później przeprowadzić osobne
porównanie, ponieważ podobny cel nie oznacza identycznego API ani układu.

### Wyszukiwanie

`Ctrl+F` (wyszukiwanie w bieżącej sesji/usłudze) i `Ctrl+Shift+F`
(wyszukiwanie globalne) obecnie nie działają. Sprawdzenie kodu potwierdziło,
że nie jest to tylko brak wpisu w tablicy skrótów: pełna wyszukiwarka oraz
osobny widok wyników z głównego AMC nie zostały jeszcze przeniesione. Obecne
`Ctrl+K` jedynie filtruje elementy już widoczne na bieżącej liście i nie może
zastępować żadnego z tych poleceń.

Port musi zachować dwa zakresy wyszukiwania, osobną dostępną listę wyników,
powrót do poprzedniego widoku i komplet działań na wyniku zgodny z głównym
AMC: otwieranie i odtwarzanie, szybkie informacje, kopiowanie, zaznaczenie
wielokrotne oraz właściwe dla sesji operacje Biblioteki, Ulubionych, Kolejki,
playlist i pobierania. Przed kodowaniem należy odczytać z głównego AMC pełny
kontrakt wyników i skrótów, zamiast odtwarzać go z pamięci.

### WiiM

Sesja WiiM jest podłączona do istniejących usług AMC. Odbiór 10 października
potwierdził prawidłowe wykrycie urządzenia i odczyt jego stanu. Udało się także
uruchomić i zatrzymać stację. Obecny interfejs jest jednak tylko częściowy:
`F6` przełącza pomiędzy otwartym odtwarzaczem a listą urządzeń/odtwarzaczy,
natomiast nie udostępnia pełnej Biblioteki, Ulubionych, presetów i pozostałych
widoków znanych z głównego AMC. Brakuje również kompletnego podłączenia ich
skrótów, między innymi rodziny `Ctrl+L`, `Ctrl+Shift+U` i skrótów presetów.
Przed implementacją trzeba porównać pełną mapę funkcji z głównym AMC, aby nie
zgubić pozostałych poleceń ani nie tworzyć drugiej, niezgodnej semantyki.

### Sonos

Dodano sesję Sonos korzystającą z tego samego magazynu poświadczeń Windows i
istniejącego klienta C# co główne AMC. Python otrzymuje wyłącznie celowe nazwy
grup i bezpieczny stan odtwarzania. Dostępne są wybór grupy, odtwarzanie,
pauza, następny/poprzedni, seek i głośność. Tokeny Sonos nie opuszczają C#.

Odbiór użytkownika 10 października ujawnił błąd wymagający poprawy: AMC widzi
grupę Sonos i odczytuje jej stan (np. „Radio Opole, myTuner Radio, Zatrzymane,
5 procent, bez wyciszenia”), ale polecenia sterowania nie są wykonywane.
Program najpierw mówi: „Nie udało się sterować grupą Sonos: Trwa odczyt
informacji. Powtórz skrót za chwilę”, a ponowienie po chwili nie odblokowuje
sterowania. Do sprawdzenia jest zatrzymany lub stale ponawiany odczyt stanu,
brak zwolnienia blokady po odświeżeniu oraz wykonywanie kliknięć i skrótów po
ukończeniu odczytu. Poprawkę i test na żywej grupie odłożono orientacyjnie na
piątek; nie jest to automatycznie zaplanowane zadanie.

Podobnie jak w WiiM, brakuje pełnego interfejsu Biblioteki, Ulubionych,
wyboru materiałów, presetów i odpowiadających im skrótów z głównego AMC.
Obecny widok pokazuje głównie grupę oraz ostatni stan lub ostatnio aktywny
materiał. Próba uruchomienia widocznego Radia Opole została przyjęta przez
interfejs, ale radio faktycznie nie zaczęło grać. W piątek prace mają zacząć
się od uporządkowania i przeniesienia kompletnej warstwy WiiM i Sonos z
głównego AMC, a nie tylko od poprawienia pojedynczego komunikatu odświeżania.

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

W widoku nagranych plików `Alt+Shift+R` każdy ukończony wpis ma obecnie
wbudowany prefiks „Nagrane”, mimo że sama lista już nazywa się „Nagrane”.
NVDA powtarza więc to słowo przy każdym pliku. Przy poprawce zwykły ukończony
wiersz ma zaczynać się od nazwy stacji lub pliku; znaczące stany wyjątkowe,
takie jak „Przerwane”, „Nieudane” albo brak pliku, muszą pozostać czytelne.

Na liście harmonogramów otwieranej przez `Ctrl+Shift+H` Spacja nie włącza ani
nie wyłącza zaznaczonego planu. Kod ma już metodę zmiany pola `enabled` i
gałąź `WXK_SPACE`, ale wymaga ona, aby `FindFocus()` zwrócił dokładnie obiekt
listy; obecne testy nie odtwarzają rzeczywistej drogi fokusu wx/NVDA. Nie jest
to więc brak samej operacji, lecz otwarta regresja podłączenia klawisza lub
rozpoznawania fokusu. Poprawka ma zachować wiersz, podać nazwę planu i nowy
stan dokładnie raz, zapisać zmianę w hoście i pokazać ten sam stan po ponownym
otwarciu okna oraz restarcie programu.

Odbiór użytkownika w paczce
`.test-output\AMC-Python-next-status-20261010` wykazał również, że po
`Ctrl+C` NVDA nadal mówi angielskie „Copy”. Paczka zawiera bieżącą próbę
przechwycenia skrótu, a jej `gui.py` ma ten sam SHA-256 co źródło, więc nie
jest to pomylenie wersji. Dotychczasowa poprawka i test bezokienny są
niewystarczające; błąd pozostaje otwarty i wymaga pomiaru kolejności zdarzeń
klawiatury/UI Automation z żywym NVDA.

Do domknięcia pozostaje połączenie AMC Python z gotowym dodatkiem AMC do NVDA.
Docelowo LiteHost ma wystawiać ten sam bezpieczny, lokalny protokół
`AMC.NVDA.v1`, z którego korzysta główne AMC. Dzięki temu pozostają jedna
wtyczka, jedna mapa gestów i dotychczasowe ustawienia użytkownika. Polecenia
silnika mają trafiać do wspólnego rdzenia, a polecenia otwierające widoki do
frontendu wxPython. Stary proces AMC nie może być wymaganym pośrednikiem.
Szczegółowy kontrakt i testy są opisane w `PROJEKT_NVDA_PL.md`.

## Aktualizacje i zgłaszanie błędów

Pakiet zawiera już wykonywalny `AMC-Python-Updater.exe`. Aktualizator sprawdza
kompletny manifest i sumy SHA-256, przygotowuje kopię zapasową oraz potrafi
wycofać nieudaną podmianę. Nie ma jeszcze opublikowanego kanału wydań AMC
Python ani automatycznego pobierania paczki, więc nie należy przedstawiać go
jako ukończonej aktualizacji internetowej. EdSharp NG pozostaje punktem
odniesienia dla zachowania pełnego mechanizmu aktualizacji.

„Sygnalista” (`michaldziwisz/sygnalista`) jest osobnym modułem zgłaszania
błędów, a nie nazwą aktualizatora. Przed jego integracją trzeba sprawdzić
licencję i rzeczywisty kontrakt biblioteki; nie wolno kopiować niesprawdzonego
kodu ani wysyłać logów bez wiedzy użytkownika.

## Dowody automatyczne tego przyrostu

- pełny runner Python: 1192 zaliczone, 0 błędów, 138 historycznych pominięć;
- testy protokołu C#: 14 zestawów zaliczonych;
- LiteHost zbudowany i opublikowany dla Windows x64 bez błędów i ostrzeżeń;
- pakiet uruchomieniowy przeszedł sprawdzenie środowiska z Pythonem 3.14.7,
  wxPython 4.3.1 i nowym hostem.

Testy protokołu dowodzą granic danych i obsługi poleceń. Nie zastępują odbioru
żywego konta TIDAL, urządzeń WiiM/Sonos ani mowy NVDA.

Drugie równoległe uruchomienie interfejsu jest blokowane przed otwarciem okna.
Zapobiega to sytuacji, w której starszy host trzyma zapis postępu podcastów,
a nowe okno pokazuje listy, lecz nie wykonuje Enter, Ctrl+R ani informacji pod
lewą strzałką.

## Najbliższa kolejność prac

1. Zastąpienie testowego startu przez `.cmd` jednym `AMC.exe`, który uruchamia
   dołączony runtime bez konsoli, sprawdza manifest i wersje, pilnuje jednej
   instancji oraz współpracuje z `AMC-Python-Updater.exe` przy aktualizacji,
   wycofaniu i ponownym uruchomieniu.
2. Przywrócenie niezależnych torów sesji: równoczesne radio i Multimedia,
   osobne urządzenia, pauza i wyciszenie sterowane po wejściu do danej sesji.
3. Przeniesienie pełnego wyszukiwania z głównego AMC: `Ctrl+F` w bieżącej
   sesji, `Ctrl+Shift+F` globalnie, dostępna lista wyników, wszystkie działania
   na wynikach i prawidłowy powrót do wcześniejszego widoku. Przy tym usunąć
   powtarzany prefiks „Nagrane” z ukończonych wierszy `Alt+Shift+R`.
4. Przepisanie całych Ustawień głównego AMC pod `Ctrl+,`, ze wszystkimi
   kartami, polami, zależnościami i zapisem oraz nawigacją `Ctrl+Tab`; dodanie
   wyboru pauzy po utracie wyjścia, `Ctrl+[` do poprzedniego i `Ctrl+]` do
   następnego urządzenia bieżącej sesji. W tym samym etapie pełny audyt
   Biblioteki, menu, skrótów i sortowań `Alt+cyfra` względem głównego AMC oraz
   naprawa przełączania harmonogramu Spacją w żywym oknie.
5. Uzupełnienie WiiM i Sonos o pełną warstwę interfejsu z głównego AMC:
   Bibliotekę, Ulubione, wybór materiałów, presety, wszystkie skróty oraz
   prawidłowe wykonanie transportu po zakończeniu odczytu stanu. Następnie
   ponowny odbiór na obudzonych urządzeniach. Materiał Sonos Redux z Hermesa
   traktować tylko jako krótką wskazówkę projektową, gdy analogiczny problem
   wystąpi w AMC; nie przeznaczać przebiegów na analizę, uruchamianie ani testy
   tego obcego dodatku NVDA i nie kopiować kodu GPL.
6. Przywrócenie w TIDAL sortowania albumów (alfabetycznego, własnego i według
   dodania z najnowszymi u góry) oraz kontekstowej prawej strzałki na albumach
   i wykonawcach, po porównaniu z głównym AMC.
7. Podłączenie gotowego dodatku AMC do NVDA bezpośrednio do LiteHosta i
   wxPython, bez uruchamiania starego AMC, oraz żywy odbiór mowy i brajla.
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

