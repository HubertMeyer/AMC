# AMC — ustalenia projektu

- Kanoniczne repozytorium bieżącego, nowego AMC Python:
  `D:\Projekty Codex\AMC - integracja wxPython`.
- `D:\Projekty Codex\Accessible Multimedia Controller` zawiera wycofany z
  bieżących prac stary interfejs WPF. Można go czytać jako materiał historyczny,
  ale nie należy tam wdrażać nowych poprawek ani budować użytkowej aktualizacji.
- Stary AMC z serii WPF `alpha.4xx`, w tym używana dawniej wersja około
  `alpha.422`, jest od tej chwili nazywany **historycznym AMC**. Nie jest
  produktem rozwijanym ani kandydatem do następnego wydania. Może służyć
  wyłącznie jako wzorzec zachowania lub źródło sprawdzonego kodu silnika po
  świadomej analizie.
- **AMC Python jest jedynym bieżącym AMC.** Nazwa `AMC Python` jest nazwą
  przejściową używaną podczas rozwoju i nie oznacza pobocznego prototypu ani
  nakładki na historyczny program. Źródła są w tym repozytorium, a bieżąca
  instalacja użytkowa znajduje się w `D:\Projekty Codex\AMC Python`.
- Docelowo obecny, pełny profil AMC Python otrzyma nazwę użytkową **AMC Test**.
  Publiczne **AMC** powstanie z dokładnie tej samej bazy kodu i tego samego
  procesu wydania, ale z ograniczonym profilem możliwości. Nie utrzymujemy
  osobnego starego programu jako publicznego AMC i nie rozwijamy dwóch
  rozchodzących się implementacji.
- Funkcje niedopuszczone do publicznego AMC mają być wyłączone profilem
  możliwości także w interfejsie, pomocy, zależnościach, logowaniu i pakiecie,
  a nie tylko wizualnie ukryte. `AMC Test` może zawierać funkcje eksperymentalne
  i prywatne, których publiczne `AMC` jeszcze nie udostępnia.
- Logika funkcji AMC ma być oddzielona od sposobu wywołania. Zdarzenie wxPython,
  skrót, paleta poleceń, dodatek NVDA, przyszły wiersz poleceń i lokalny serwer
  sterowania dla AI mają przekazywać to samo jawne polecenie do wspólnej warstwy
  aplikacyjnej, zamiast naśladować klawisze albo implementować funkcję ponownie.
  Nowe funkcje projektuj tak, aby dało się je później bezpiecznie udostępnić
  kolejnemu adapterowi poleceń. Szczegóły: `docs/zadania/ARC-001-wspolny-rdzen-polecen-cli-ai.md`.
- Windows pozostaje jedynym planowanym i wspieranym systemem dla pierwszego
  publicznego AMC. Oficjalny port na macOS, Linux lub ARM jest odłożony bez
  terminu: wymaga osobnego hosta multimedialnego, integracji systemowej oraz
  pełnych testów z czytnikiem ekranu. Nie zwiększaj bieżącego zakresu prac w imię
  hipotetycznej przenośności. Zachowuj sensowne granice modułów i dokumentację,
  aby zainteresowana osoba mogła kiedyś przygotować port niezależnie.
- Użytkownik 9 października
  2026 r. wyraził stałą zgodę na pracę w tym katalogu także po wznowieniu
  zadania; nie pytaj ponownie o wybór katalogu roboczego.
- Zmiany z aktywnego katalogu integracji wxPython pozostają lokalne. Nie
  wysyłaj ich do GitHuba bez osobnej, aktualnej zgody użytkownika na publikację.
- Historyczna zgoda z 9 września 2026 r. na publikowanie starego AMC nie jest
  bieżącą zgodą na publikację nowego AMC Python. Dla tego projektu zawsze
  wymagana jest osobna decyzja dotycząca konkretnego przygotowanego stanu.
- Przed publikacją sprawdzaj zakres zmian i zawartość pakietu. Nie publikuj
  poświadczeń, danych kont, lokalnych kolekcji, prywatnych nagrań ani logów
  użytkownika. Zgoda nie obejmuje innych repozytoriów ani kontaktowania
  zewnętrznych osób w imieniu użytkownika.
- Publikacja źródeł, publikacja ZIP w Releases i uruchomienie programu są
  osobnymi czynnościami. Raportuj ich rzeczywiste wyniki, także blokady.
  Nie zamykaj programu w trakcie nagrywania.
- Użytkownik 11 września 2026 r. zezwolił na przyszłe instalowanie aktualizacji
  dodatku AMC do NVDA oraz uruchamianie/restartowanie NVDA i AMC, z uprzednim
  zamknięciem poprzednich instancji. Przed takim działaniem sprawdź, czy AMC
  nie nagrywa (także w tle lub z harmonogramu). Gdy nie da się tego potwierdzić,
  nie zamykaj programów i zapytaj. Sama publikacja nie wymaga restartu.
- Po publikacji wydania usuń jego lokalny ZIP z `publish` dopiero po
  zweryfikowaniu, że odpowiadający mu załącznik GitHub Releases został
  skutecznie wysłany i jest dostępny (nazwa, rozmiar i, gdy dostępny, SHA-256).
  Sam push źródeł nie oznacza wysłania ZIP-a. Niewysłane i niezweryfikowane
  paczki pozostaw; nie usuwaj przy tym rozpakowanej bieżącej wersji programu.
- Priorytet TIDAL: zweryfikowane pełne odtwarzanie, nie deklarowanie próbek
  jako pełnych utworów. Ustalenia i granice: `PROJEKT_TIDAL_PL.md`.
- Wynik zwykłego logowania do Embed i analiza jego kodu:
  `TIDAL_WERYFIKACJA_PELNEGO_ODTWARZANIA_2026-09-09.md`. Nie prosić ponownie
  o identyczne logowanie bez nowego dowodu. Za osobną zgodą użytkownika pytanie
  wysłano do TIDAL: https://github.com/orgs/tidal-music/discussions/384.
  Nie dublować zgłoszenia. Zgoda nie obejmuje podłączania tożsamości Nostr.
- Testy muszą kończyć się niezerowym kodem i diagnostyką po niepowodzeniu,
  nie pozostawionym oknem awarii CLR. Test negatywny nie jest zaliczeniem
  funkcji. Profile WebView2 testów są odizolowane od konta i stanu AMC.
- Narzędzia testowe muszą wykrywać programy przenośnie: najpierw jawna zmienna
  środowiskowa, potem bieżący `PATH`, a dopiero na końcu istniejąca ścieżka
  zgodności dla konkretnego systemu. Nie używaj linuksowej ścieżki jako
  bezwarunkowej wartości domyślnej na Windows ani odwrotnie. Ręczne uruchomienie
  tego samego testu na wspieranym systemie ma działać bez sekretnej zmiennej,
  jeżeli wymagane narzędzie jest dostępne w `PATH`.
- Test integracyjny zależny od nieobowiązkowego runtime'u albo wcześniej
  zbudowanego artefaktu ma używać standardowego mechanizmu pominięcia
  rozpoznawanego przez pytest/unittest. Własny wyjątek o nazwie `SkipTest` nie
  jest pominięciem i nie może zamieniać braku środowiska w pozorną regresję.
- Etykiety dostępności list, pól kombi i menu muszą być tekstem użytkowym,
  nigdy domyślną reprezentacją obiektu, enuma ani identyfikatorem komendy.
  Testuj początkowy fokus, strzałki, ponowne otwarcie i powrót po zamknięciu.

## Rejestr zadań

- Kanoniczny rejestr oczekujących, trwających i zakończonych prac znajduje się
  w `docs/zadania/README.md`. Szczegóły każdego większego zadania są w osobnym
  pliku w tym samym katalogu.
- Przed rozpoczęciem wskazanego zadania przeczytaj rejestr i jego plik. Nie
  uruchamiaj innych zapisanych zadań bez polecenia użytkownika.
- Po wykonaniu zadania zaktualizuj jego status oraz zapisz w jego pliku wynik,
  zmienione pliki, commit, testy i dokładną wersję instalacji, jeśli powstała.
  Następnie uaktualnij status w rejestrze.
- `AGENTS.md` przechowuje trwałe zasady całego projektu. Diagnozy pojedynczych
  błędów, plan pracy i dowody wykonania należą do pliku danego zadania, aby nie
  rozrastały się w instrukcjach obowiązujących każdą sesję.

## Skróty globalne

- Widok sesji, urządzenia ani listy nie może przejmować skrótu globalnego i
  pozostawiać go bez działania. `Ctrl+H` otwiera Historię odtwarzania z każdego
  głównego miejsca programu, w szczególności z Radia internetowego, podcastów,
  WiiM i Sonosa. Po zamknięciu historii fokus wraca do elementu, z którego ją
  wywołano.
- Przy dodawaniu nowego widoku lub integracji sprawdź wspólną tablicę skrótów,
  co najmniej `Ctrl+H`, `Alt+R`, `Alt+Shift+R` i `Ctrl+L`. Dodawaj testy
  parametryzowane dla reprezentatywnych widoków zamiast osobnych, rozbieżnych
  obsług klawiszy.
- `Ctrl+Shift+0` uruchamia preset 10 we wszystkich sesjach, także w Radiu.
  Nie mapuj go przez znak `)` ani zwykłe `Ctrl+0`; układ klawiatury i kod
  klawisza z górnego rzędu wymagają jawnego testu regresji. `Ctrl+Shift+-` i
  `Ctrl+Shift+=` nie są dowodem, że wariant z zerem działa.
- Historia `Ctrl+H` jest oddzielna dla każdej sesji i zawiera odtworzenia
  wykonane przez AMC w tej sesji. Nie wolno pokazywać w WiiM, Sonosie,
  Spotify ani TIDAL historii plików lokalnych. Przekazanie materiału do obcej
  aplikacji lub urządzenia może nie zsynchronizować historii dostawcy; AMC ma
  uczciwie utrzymywać własną historię wykonanego przez siebie odtwarzania.

## Zwięzła mowa list i relacji

- Równoważne elementy usług mają ten sam porządek mowy na liście: tytuł, typ,
  wykonawca lub autor oraz czas, jeżeli czas jest już dostępny w danych.
  Albumy mogą podawać łączny czas bezpośrednio podczas góra/dół, ale nawigacja
  nie może wykonywać osobnego żądania sieciowego dla każdego wiersza tylko po
  to, aby go odczytać.
- `Lewa strzałka` podaje krótkie informacje uzupełniające i nie powtarza
  bez potrzeby tytułu ani nazwy aplikacji. Nie wypowiada stałych prefiksów
  `Katalog Spotify`, `Rodzaj`, `Wykonawca`, `Tytuł` ani `Czas`, jeśli kolejność
  wartości jest jednoznaczna. Brak danych należy nazwać krótko i uczciwie.
- `Prawa strzałka` otwiera zwartą listę relacji. Zwykły tryb nie mówi
  `menu kontekstowe`, `dialog lista`, nazwy procesu ani długiej instrukcji;
  podaje relację i pozycję, na przykład `Albumy, 1 z 2`. Rozszerzone wskazówki
  mogą być osobnym ustawieniem dostępności. Na odcinku relacja do źródła musi
  zawierać rzeczywistą nazwę podcastu lub kanału, nie ogólne `Podcasty`.
- `Alt+1`, `Alt+2` i `Alt+3` po zmianie sortowania ogłaszają użytkową nazwę
  wybranego porządku i nie pozostawiają systemowego sygnału sugerującego brak
  działania. Komunikat i fokus muszą przetrwać szybkie kolejne przełączenia.
- `Ctrl+C` i `Ctrl+Shift+C` nie mogą przepuszczać angielskiego `copy` z
  kontrolki. Potwierdzenie po polsku ma być krótkie i natychmiastowe, bez
  sztucznej pauzy wynikającej z podwójnej obsługi tego samego gestu.

## Wyjścia dźwięku i stan odtwarzania

- Zapamiętane wyjście audio jest wyborem użytkownika, nie nazwą urządzenia
  zaszytą w kodzie. Jeśli go brakuje, AMC wybiera bezpieczne dostępne wyjście
  lub prosi o wybór i podaje nazwę rzeczywiście użytego urządzenia. Komunikat
  nigdy nie zakłada, że inni użytkownicy mają konkretny model sprzętu.
- `Ctrl+[` przełącza lokalne wyjścia w tym samym wspólnym mechanizmie dla
  Radia, plików, podcastów i Spotify Librespot, o ile dany silnik je obsługuje.
  Spotify Connect jest osobnym katalogiem urządzeń i nie może być udawany
  przez listę lokalnych wyjść Windows.
- WiiM i Sonos po rozpoczęciu odtwarzania aktualizują wiersz i mowę stanem
  `Odtwarzane`, tak jak Radio. Użytkownik musi móc ustalić, co rzeczywiście
  gra, bez przechodzenia do innej aplikacji.

## Edycja plików audio

- Polecenie wycięcia „do końca pliku” oznacza koniec rzeczywistej osi ramek
  odczytanej przez FFmpeg, a nie zaniżony czas z nagłówka, odtwarzacza albo
  ostatniej pozycji odsłuchu. Ręcznie ustawiona granica wcześniejsza niż koniec
  nadal pozostaje granicą ręczną.
- Każda zmiana destrukcyjnej edycji audio wymaga parametryzowanego testu całej
  listy formatów audio deklarowanej przez `LocalAudioFileDiscovery`, w tym
  aliasów rozszerzeń. Test ma przygotować prawdziwy plik danego kodeka,
  zasymulować zaniżony czas odtwarzacza, wyciąć ogon, sprawdzić rzeczywistą
  długość wyniku i brak plików roboczych. Kontenery wideo pozostają jawnie
  odrzucone, dopóki nie powstanie osobny, równie pełny kontrakt ich edycji.
- Nie uznawaj samego kodu wyjścia FFmpeg za dowód poprawności. Oryginał wolno
  zastąpić dopiero po odczytaniu wyniku i porównaniu jego osi czasu z
  oczekiwanym skutkiem operacji.

## Wyszukiwanie, relacje i biblioteka

- Wynik wyszukiwania zachowuje swój rzeczywisty typ i tożsamość. Enter na
  wykonawcy otwiera wykonawcę, na albumie album, na utworze utwór, a w
  podcastach odpowiednio podcast lub odcinek. Nie wolno podmieniać zaznaczenia
  na podobny albo wcześniej zapisany element z biblioteki.
- `Prawa strzałka` na wyniku otwiera jedno użytkowe menu relacji właściwe dla
  typu elementu. Dla wykonawcy obejmuje co najmniej albumy i utwory, jeżeli
  usługa je udostępnia. Relacje mają służyć przeglądaniu katalogu przed
  świadomym dodaniem czegokolwiek do biblioteki.
- Sama `Prawa strzałka` nie otwiera relacji w tle. Najpierw pokazuje i ogłasza
  listę rzeczywistych celów, zachowując zaznaczenie elementu źródłowego; dopiero
  Enter na wybranej relacji przechodzi do jej zawartości. Escape albo lewa
  strzałka zamykają listę relacji i przywracają fokus dokładnie na źródle.
- Wyszukiwanie, Enter, prawa strzałka i samo przeglądanie nigdy nie zmieniają
  biblioteki ani ulubionych. Dodanie wymaga osobnego, jawnego polecenia
  użytkownika. Zasada obowiązuje TIDAL, Radio Browser, podcasty, przyszłe
  Spotify i inne katalogi.
- Wynik i każde polecenie Biblioteki pozostają w usłudze, z której pochodzą.
  Album Spotify nie może trafić do TIDAL-a, element TIDAL-a do podcastów, a
  lokalny wynik do katalogu sieciowego wskutek zbieżnego typu lub identyfikatora.
  O routingu decyduje jawne `session_id` oraz tożsamość dostawcy, nie tytuł.
- Jeśli dostawca nie udostępnia zawartości playlisty, albumu lub innego
  kontenera, Enter podaje jeden jasny komunikat i pozostawia użytkownika na
  bieżącej liście. Nie wolno wcześniej dopisać pustego poziomu do stosu
  nawigacji ani zmuszać użytkownika do Escape z widoku, który nic nie zawiera.
- Test wyszukiwania porównuje bibliotekę przed i po przeglądaniu, obejmuje
  element już zapisany oraz niezapisany, sprawdza typ zaznaczenia, fokus,
  pojedynczą reakcję Enter i menu prawej strzałki. Nie wolno uznać samego
  poprawnego tekstu wyniku za dowód prawidłowego routingu.
- `Ctrl+F` działa w każdym sensownie przeszukiwalnym widoku, również w WiiM i
  Sonosie. Wyszukiwanie lokalne filtruje lub odnajduje elementy już wczytanej
  listy, na przykład strumienie i playlisty. Wyszukiwanie globalne korzysta z
  katalogu usługi tylko wtedy, gdy oficjalne API udostępnia taką możliwość.
  Interfejs zawsze jasno podaje zakres i nie przełącza go po cichu.
- Lokalne i globalne wyszukiwanie używają wspólnego zachowania klawiatury:
  przewidywalny fokus, Enter na rzeczywistym wyniku, Escape do poprzedniego
  miejsca i brak automatycznego zapisu. Adapter dostawcy dostarcza dane oraz
  możliwości, ale nie tworzy osobnego, rozbieżnego interfejsu wyszukiwarki.
- `Ctrl+Shift+L` zmienia członkostwo w Bibliotece, natomiast `Delete` usuwa
  wybrany wpis z otwartego widoku Biblioteki. `Delete` nie jest operacją na
  katalogowych wynikach wyszukiwania. W plikach lokalnych usuwa tylko rekord
  i nigdy nie kasuje pliku; fizyczne kasowanie pozostaje osobnym, wyraźnym
  poleceniem. W podcaście lub kanale `Delete` usuwa pojedynczy odcinek albo
  materiał, a nie całe źródło.
- Pojedynczy film YouTube zapisany z wyszukiwania trafia jako odcinek do
  użytkowego źródła `Media internetowe`. Ten pojemnik nie jest jednym kanałem:
  `Delete` oraz ponowne `Ctrl+Shift+L` na zapisanym filmie dotyczą wyłącznie
  tego filmu. Zwykłe `Ctrl+Shift+L` na podcaście, kanale albo ich odcinku nadal
  zmienia członkostwo całego rzeczywistego źródła nadrzędnego.
- Usunięty pojedynczy odcinek podcastu albo materiał kanału jest zapamiętany
  jako świadome wykluczenie i nie wraca przy odświeżeniu RSS/YouTube. Jawne
  ponowne dodanie pojedynczego filmu z katalogu usuwa jego wykluczenie i
  przywraca go do `Media internetowe`. Usuwanie rekordu nie usuwa pobranych
  plików z dysku; komunikat ma mówić o tym bez zakładania, czy plik istnieje.

## Wspólny kontrakt interfejsu źródeł

- Zachowanie, które użytkownik odebrał i jednoznacznie potwierdził jako dobre,
  staje się wzorcem akceptacyjnym dla równoważnych funkcji w innych źródłach.
  Nie projektuj ponownie bez wskazanej potrzeby. Przenoś ten sam układ skrótów,
  nawigację, kolejność komunikatów, fokus, powrót i znaczenie Entera oraz
  strzałek wszędzie, gdzie możliwości usługi na to pozwalają.
- Dopracowany TIDAL jest wzorcem funkcjonalnym interfejsu Spotify: wejście do
  biblioteki, wyszukiwanie lokalne i globalne, rzeczywista tożsamość wyniku,
  relacje wykonawca–album–utwór, przeglądanie przed zapisem, odtwarzanie,
  dodawanie i usuwanie, sortowanie, historia, Escape i przywracanie fokusu.
  Stare AMC i librespot mogą dostarczyć rozwiązania techniczne, lecz nie są
  wzorcem zachowania interfejsu.
- W Spotify działający silnik, logowanie i integrację Librespot można przenosić
  ze starego AMC, ale interfejs zawsze pozostaje współczesnym kontraktem AMC
  Python. Dotyczy to także wyszukiwania, relacji pod prawą strzałką, zwięzłej
  mowy list, opisów `Alt+D`, filtrów i sortowania `Alt+1–3`, historii,
  komunikatów oczekiwania, błędów oraz obsługi niedostępnej zawartości.
- `Ctrl+Shift+L` w usługach sieciowych ogłasza `Dodano do Biblioteki` albo
  `Usunięto z Biblioteki` dopiero po potwierdzonym wyniku właściwego API.
  Odświeżenie, oczekiwanie lub przeładowanie bez zmiany członkostwa nie może
  zostać przedstawione jako sukces. Fokus zostaje na logicznie tym samym
  elemencie, nawet gdy po usunięciu jego wiersz znika.
- Jawny wyjątek potwierdzony przez użytkownika: działające `Shift+F2` ze
  starego AMC jest wzorcem funkcjonalnym zmiany nazwy pliku w AMC Python.
  Zachowaj nazwę bez rozszerzenia w dialogu, niezmienne rozszerzenie, brak
  nadpisywania, zatrzymanie aktualnie wczytanego pliku z zachowaniem pozycji,
  zmianę fizycznej nazwy na dysku, stabilną tożsamość rekordu, aktualizację
  Biblioteki, historii i zakładek oraz powrót fokusu. Sukces wolno ogłosić
  dopiero po potwierdzeniu nowej ścieżki. Operację plikową wykonuje host C#;
  wxPython prowadzi dialog i odświeża interfejs, więc sama technologia Python
  nie jest powodem różnicy w zachowaniu.
- Nie kopiuj osobnych przepływów ekran po ekranie. Utrzymuj wspólny model
  elementu, nawigacji i możliwości oraz wspólną warstwę poleceń; adapter
  dostawcy ma jedynie pobierać dane, mapować tożsamość i jawnie zgłaszać
  obsługiwane możliwości. Dzięki temu poprawka wspólnej funkcji obejmuje
  wszystkie porównywalne usługi zamiast rozchodzić się na rozbieżne wersje.
- Kontekst nawigacji obejmuje co najmniej źródło i sesję, zakres wyszukiwania,
  zapytanie, rzeczywisty typ i identyfikator zaznaczenia, stos powrotu,
  sortowanie oraz bieżące urządzenie, jeśli dotyczy. Wynik asynchroniczny musi
  należeć do aktualnej generacji żądania; spóźniona odpowiedź nie może
  podmienić nowszego widoku, zaznaczenia ani źródła.
- Źródło liczone w setkach lub tysiącach elementów nie może blokować jednego
  wątku ani tworzyć całej listy naraz. Stosuj porcje około 150 elementów z
  kontrolowanym doczytywaniem, stabilnym fokusem i anulowaniem starej
  generacji. Sortowanie ma dotyczyć pełnego logicznego zbioru, jeśli adapter
  potrafi je wykonać przed stronicowaniem; w przeciwnym razie interfejs musi
  jasno powiedzieć, że porządek obejmuje tylko wczytany zakres.
- Każda nowa funkcja współdzielona dostaje test kontraktowy uruchamiany dla
  wszystkich odpowiednich adapterów. Test obejmuje nie tylko tekst listy, ale
  też tożsamość elementu, brak niejawnego zapisu, fokus początkowy i powrotny,
  Enter, Escape, lewą i prawą strzałkę, skróty oraz odpowiedź spóźnionego
  żądania. Po teście automatycznym wykonaj próbę z NVDA.
- Ograniczenia API są dozwoloną różnicą, lecz mają być reprezentowane jako
  brak możliwości z jasnym komunikatem. Nie zgaduj brakujących relacji, nie
  podstawiaj podobnego elementu z biblioteki i nie pokazuj technicznego
  identyfikatora w miejsce danych, których dostawca nie udostępnia.

## Pierwsze uruchomienie i logowanie do usług

- Docelowy instalator prowadzi zwykłego użytkownika przez dostępny, oficjalny
  przepływ logowania. Nie powinien żądać ręcznego tworzenia aplikacji
  deweloperskiej, wyszukiwania identyfikatora klienta ani przepisywania
  technicznych wartości, jeżeli regulamin i API pozwalają użyć rejestracji AMC
  oraz publicznego przepływu autoryzacji.
- Dla każdej usługi osobno wybierz najprostszy bezpieczny mechanizm wspierany
  przez dostawcę, na przykład OAuth z PKCE, kod urządzenia, dostęp lokalny lub
  wykrywanie urządzenia. Nie ujednolicaj protokołów pozornie; ujednolicaj
  doświadczenie użytkownika, komunikaty, anulowanie, ponawianie i wylogowanie.
- Sekretu klienta, tokenu odświeżania ani danych konta nie wolno osadzać w
  publicznym instalatorze, repozytorium, logu ani nazwie kontrolki. Dane sesji
  przechowuj mechanizmem chronionym systemu operacyjnego. Sam publiczny
  identyfikator aplikacji można dołączyć wyłącznie zgodnie z modelem i
  regulaminem konkretnego dostawcy.
- Jeżeli dostawca naprawdę wymaga od każdego użytkownika własnej rejestracji
  deweloperskiej, nie ukrywaj tego obejściem. Przygotuj dostępny kreator z
  jasnym wyjaśnieniem i minimalną liczbą kroków. Ostateczny projekt tego etapu
  powstaje po integracji Spotify i po ponownej weryfikacji aktualnych wymagań
  Sonosa, WiiM, Spotify i pozostałych usług.
- Odbiór wykonuj na czystym profilu lub maszynie: od pierwszego uruchomienia do
  gotowej sesji, z NVDA, bez wcześniej zapisanych tokenów i bez narzędzi
  deweloperskich. Test obejmuje anulowanie, wygaśnięcie kodu, odmowę dostępu,
  ponowienie, wylogowanie i aktualizację programu bez utraty ważnej sesji.

## Równoległe integracje systemów głośnikowych

- WiiM i Sonos są wzorcem wspólnego kontraktu dla przyszłych systemów
  głośnikowych z otwartym API. Nowa integracja ma używać wspólnego modelu
  możliwości i zachowania interfejsu wszędzie tam, gdzie urządzenia oferują
  równoważne funkcje; różnice producenta należy izolować w adapterze API.
- Każda poprawka dotycząca jednego systemu wymaga przeglądu wszystkich
  równoległych integracji. Nie kończ zadania po naprawieniu tylko zgłoszonej
  marki, jeżeli ten sam wzorzec listy, skrótu, fokusa, transportu lub błędu
  występuje także w pozostałych adapterach.
- Jednorodna lista zapisanych strumieni przekazuje NVDA nazwę strumienia i
  natywną informację o pozycji na liście. Nie dopisuj do każdego wiersza
  stałych tekstów „stacja zapisana w AMC”, „strumień sieciowy”, nazwy źródła
  ani marki urządzenia. Adres pozostaje danymi modelu i jest odczytywany lub
  kopiowany wyłącznie na jawne polecenie użytkownika.
- `Lewa strzałka` jest wspólnym, jawnym poleceniem odczytu parametrów stacji
  lub strumienia. W WiiM, Sonosie i przyszłych integracjach ma podawać te same
  użytkowe dane, które są dostępne w Radiu internetowym, w tym adres lub
  ścieżkę źródła, jeżeli adapter rzeczywiście je udostępnia. Działanie nie
  zależy od prawa do edycji albo usunięcia pozycji: obejmuje także ulubione i
  inne listy tylko do odczytu. Gdy API nie zwraca danego parametru, nie wolno
  go zgadywać ani zastępować identyfikatorem technicznym.
- Dla każdej integracji zachowaj ten sam kontrakt klawiatury i fokusa, o ile
  API wspiera daną funkcję: wybór ostatnio używanego urządzenia, wejście i
  powrót z Biblioteki, `Ctrl+Shift+C`, transport, kierunki regulacji głośności,
  komunikaty ładowania, pustej listy i błędu. Brak możliwości API ma być
  uczciwie zakomunikowany, a nie zastąpiony zachowaniem pozornym.
- Identyfikatory urządzeń, grup, strumieni i wartości protokołu pozostają w
  modelu. Nazwy dostępne, kolumny i komunikaty muszą być złożone wyłącznie z
  zamierzonych tekstów użytkowych.
- Dodawaj wspólne lub parametryzowane testy kontraktowe, które uruchamiają ten
  sam scenariusz dla WiiM, Sonos i każdego nowego adaptera. Test ma sprawdzać
  rzeczywisty tekst wszystkich kolumn listy, początkowy i przywrócony fokus,
  Enter, Escape, strzałki, kopiowanie adresu oraz ponowne otwarcie. Zmiana
  adaptera wymaga też krótkiej próby z NVDA; sam poprawny tekst wizualny nie
  jest wystarczający.
