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

1. Uzupełnienie WiiM i Sonos o pełną warstwę interfejsu z głównego AMC:
   Bibliotekę, Ulubione, wybór materiałów, presety, wszystkie skróty oraz
   prawidłowe wykonanie transportu po zakończeniu odczytu stanu. Następnie
   ponowny odbiór na obudzonych urządzeniach.
2. Sprawdzenie zaniku wybranego urządzenia audio: automatyczny powrót na
   urządzenie domyślne i dalsze odtwarzanie tej samej stacji bez przełączania.
3. Uzupełnienie wykrytych braków w istniejących sesjach, bez regresji radia,
   nagrywania, harmonogramów i timeshiftu.
4. Odzyskanie źródła lub ticketu „Sygnalisty”, analiza i wdrożenie aktualizacji.
5. Dopiero później decyzja o Spotify.

