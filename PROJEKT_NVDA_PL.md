# Dodatek NVDA — architektura i decyzje, alpha 342 / 0.2.1

## Zakres

NVDA jest cienkim klientem AMC, nie osobnym odtwarzaczem Free Radio. Prefiks AMC pozostaje. Od 0.2.1 jest 65 dozwolonych poleceń i 65 domyślnych gestów Ctrl+Windows. Pełna aktualna mapa: [INSTRUKCJA_NVDA_PL.md](INSTRUKCJA_NVDA_PL.md); ta sama mapa jest w pomocy HTML paczki dodatku. Własne przypisania NVDA nie są modyfikowane.

Wymagane AMC alpha 342 i NVDA 2026.1. Stary podzbiór 14 poleceń zachowuje zgodność z AMC 339–340. Nowe polecenia nie zmieniają wersji protokołu: stary serwer bezpiecznie odmawia nieznanej komendy. Użytkownik zaakceptował wersję do publikacji 11 września 2026 r. Dalsze audyty innych modeli powinny uwzględniać poniższe granice testów; publikacja nie oznacza kompletnej weryfikacji mowy, urządzeń i usług.

## Zgodność z AMC Python — stan 13 października 2026

Istniejący dodatek ma współpracować również z AMC Python. Nie tworzymy drugiej
wtyczki ani drugiego zestawu gestów. Zachowujemy nazwę lokalnego potoku
`AMC.NVDA.v1.<sesja Windows>`, wersję JSON, allow-listę i dotychczasowe zasady
bezpieczeństwa, aby gotowy dodatek mógł połączyć się bez migracji ustawień.

Serwer dodatku należy teraz do LiteHosta, ponieważ tam znajduje się wspólny
rdzeń odtwarzania, nagrywania i usług. W danej sesji może działać tylko jeden
serwer tego potoku. Polecenia transportu, szybkich informacji, presetów,
Ulubionych i Kolejki korzystają z tych samych akcji co interfejs wxPython.
Polecenia jawnie otwierające AMC lub jego widok LiteHost przekazuje do
działającego frontendu wxPython; nie uruchamia w tym celu starego okna WPF.

Odpowiedź wraca raz przez dodatek NVDA jako tekst użytkowy do mowy i
brajla. Nazwy klas, identyfikatory poleceń, dane kont i reprezentacje obiektów
nie mogą trafić do odpowiedzi. Jeżeli frontend nie działa albo nie może
bezpiecznie otworzyć widoku, dodatek otrzymuje krótką odmowę zamiast
uruchamiania drugiej instancji lub wykonywania działania na innym elemencie.

Pierwszy etap obejmuje wszystkie 65 nazw poleceń gotowego dodatku. Funkcje,
których port wxPython jeszcze nie ma, są rozpoznawane, ale zwracają krótką
odmowę zamiast innej czynności: wyciszenie wszystkich sesji, rozdziały,
poprzedni i następny preset, lista sesji i paleta poleceń. Bez migawki
oryginalnego TIDAL-a odpowiedź nie wymyśla stanu pauzy ani odtwarzania.

Most ma testy korelacji odpowiedzi, odrzucenia obcego i spóźnionego
identyfikatora, anulowania przy zamknięciu, zgodności pełnej listy 65 komend,
mapowania wyłącznie na istniejące akcje oraz braku technicznych identyfikatorów
w odpowiedziach. Pozostaje żywy odbiór z NVDA. Musi się odbyć przy zamkniętym
starym AMC, bo obecny protokół świadomie nie ma selektora pomiędzy dwoma
jednocześnie uruchomionymi właścicielami tego samego potoku.

## Semantyka

- Następny/poprzedni rozpoczyna sąsiedni element również po pauzie. To nie przesunięcie zaznaczenia. Lista odtwarzania została ustalona przy rozpoczęciu odtwarzania i nie zmienia się od samego oglądania innej listy.
- Preset ustala kontekst Presety. Oddzielne globalne komendy presetów korzystają z zapisanych miejsc, pomijają puste i zawijają; kontener wymagający widocznego wyboru nie otwiera się ukradkiem. W WiiM pozostaje rozróżnienie transportu urządzenia i jego presetów/strumieni.
- Odczyt kontekstu podaje intencjonalną nazwę widoku, sesję i pozycję. Nigdy surowy identyfikator widoku, obiekt, enum ani dane autoryzacji.
- Ulubione, kolejka i nagrywanie dotyczą bieżącego nagrania aktywnej sesji. Ukryte wielozaznaczenie, kategoria artysty i folder nie mogą przejąć takiej komendy. Brak bieżącego materiału powoduje odmowę, nie wybór pierwszego elementu.
- Pauza odsłuchu, wyciszenie i pauza nagrania są odrębne. Nagrywanie korzysta z istniejącej obsługi harmonogramów, formatów, folderów i podziału, bez drugiego silnika. Nie udostępniamy globalnego usuwania plików ani zatrzymania wszystkich nagrań bez przejścia do interfejsu.
- Polecenia nieobsługiwane w sesji odmawiają zamiast przełączać sesję. Ograniczenia API i odtwarzania TIDAL nie zmieniają się.

## Transport i fokus

- Lokalny named pipe ograniczony do konta oraz sesji Windows: CurrentUserOnly, identyfikacyjny poziom SQOS klienta, bez portu sieciowego.
- Wersjonowany JSON, allow-list, maksymalnie 512 bajtów zapytania i 2000 znaków komunikatu odpowiedzi. Nie przyjmujemy dowolnego ID routera, ścieżek, danych konta, poleceń powłoki ani udawanych naciśnięć klawiszy.
- Jedno połączenie to najwyżej jedna komenda. Klient nie ponawia wysłanego przełącznika; ponowienia obejmują tylko otwarcie połączenia zanim cokolwiek wysłano.
- Serwer ma limit 2 sekund wraz z oczekiwaniem na Dispatcher. Klient: 0,4 sekundy na zestawienie i 2,5 sekundy na wymianę, pojedynczy wątek roboczy, kolejka 4, ważność niepodjętej komendy 1,5 sekundy. Brak odpowiedzi nie oznacza, że rozpoczęta komenda nie została wykonana.
- Sterowanie nie blokuje wątku klawiatury NVDA. Blokada ekranu, secure mode i wyłączenie dodatku blokują dalszą obsługę.
- Natychmiastowa informacja zwrotna trafia raz przez NVDA (mowa i brajl), bez drugiego komunikatu UIA. Jawne odczyty i odpowiedzi mogą być słyszane poza AMC. Asynchroniczne błędy dostawcy zachowują drogę AMC — przyjęcie komendy nie potwierdza udanego połączenia.
- NvdaBackgroundScope to AsyncLocal: opóźniony kod po await nadal zna pochodzenie komendy i nie wywołuje odtwarzacza ani nie przywraca tam fokusa. Równoległa zwykła akcja użytkownika nie dziedziczy tego ograniczenia. Dla opóźnionego sterowania WiiM dodatkowo zachowujemy lokalny znacznik przed await.
- Komendy show... jawnie otwierają AMC. Dla nich i 12 jawnych wywołań presetów klient próbuje udzielić AllowSetForegroundWindow PID-owi serwera ustalonemu z otwartego pipe; nigdy ASFW_ANY. Odmowa systemu powoduje prośbę o Alt+Tab, bez wymuszonego always-on-top.
- Dialog nie jest wykonywany na stosie oczekującego zapytania pipe. NvdaUiHandoff odkłada pracę na Dispatcher, ma jeden slot i termin ważności, sprawdza aktywne okno, sesję i brak innego dialogu. Dzięki temu otwarty modalny wybór nie powoduje timeoutu transportu ani kolejnych dialogów po szybkich naciśnięciach.
- Otwarty dialog/menu AMC blokuje pozostałe globalne komendy. Dalsze zachowanie Escape, tabulacji i powrotu do listy należy do istniejącego interfejsu AMC.
- Diagnostyka nvda-bridge zapisuje nazwę dozwolonej komendy, sesję i typ działania, bez tokenów i danych schowka.

## Lista i bezpośrednie presety, 342

Preset1–preset12 to zamknięta lista poleceń IPC, bez dowolnego parametru czy identyfikatora komendy. Każde mapuje się na canonical RadioPreset(slot), więc zachowuje sesję, kontekst odtwarzania, puste miejsca i lokalne mapowanie gotowych presetów WiiM. Wywołanie nie przypisuje ani nie zastępuje presetu. Odtwarzalne elementy są wykonywane w NvdaBackgroundScope; kontener otwiera widok przez NvdaUiHandoff. Zgoda foreground jest udzielana wyłącznie PID-owi serwera, a otwarcie nadal wymaga kontroli aktualnej sesji i fokusa.

Przypisanie z listy presetów jest osobnym dialogiem należącym do listy. Po Save/Cancel wracamy na listę, odświeżamy etykiety i zaznaczenie. WiiM zapisuje tylko lokalną mapę skrótów, nie urządzenie. PreviewKeyDown list nie przejmuje Enter/Spacji przycisków ani ich anulowania. Widok Playlisty ma przycisk utworzenia pustej playlisty, również przez istniejące API TIDAL; nie zmienia zawartości innych playlist.

Mapa: Ctrl+Windows+Tab / Shift+Tab sesje; przecinek/kropka i Shift+kropka prędkość; A urządzenie; Alt+1–9/0/-/= bezpośrednie presety. Własnych gestów NVDA nie migrujemy siłowo. Stare domyślne Y i Page Up/Down nie są już rejestrowane przez dodatek.

## Skróty Windows

Dotychczasowe Ctrl+Windows+lewo/prawo świadomie zajmują skróty pulpitów, zgodnie z wyborem użytkownika. Nie przypisujemy podstawowych kombinacji Ctrl+Windows z Enter, cyframi, C, D, F, N, O, Q, S, V, Spacją, F4 ani Ctrl+Windows+Shift+B. Nowa mapa nie stanowi gwarancji wobec wszystkich programów trzecich. Polecenia mają opis w pomocy NVDA i mogą zostać przemapowane.

## Testy i dalszy audyt

Testy obejmują protokół, całą allow-listę Python/.NET, Unicode, brak ponownego wykonania, przeciążenie kolejki, brak serwera, timeout, kontrolę foreground PID, odłożone/zdublowane/przeterminowane otwarcie interfejsu, przepływ AsyncLocal, bezpieczny cel działań na ukrytej liście, pauzę i zakres następny/poprzedni. Test właściwości MainWindow omija konstruktor aplikacji; używa oddzielnych modeli i kontrolki na STA, bez kont, prawdziwego pipe AMC, odtwarzania czy stanu użytkownika.

To nie są ręczne testy NVDA. Przed publikacją sprawdzić pierwszą pozycję, mowę/brajl, Tab/strzałki, powrót po dialogu, globalne sterowanie z edytora, minimalizację, blokadę Windows, szybkie zmiany sesji, rzeczywiste WiiM, opóźnioną usługę, nagrywanie i niedostępne urządzenie. Ten sam odbiór trzeba wykonać z uruchomionym AMC Python: połączenie gotowego dodatku, transport, szybkie informacje, sesje, Ulubione, Kolejkę, presety oraz każde polecenie otwierające widok wxPython. Należy potwierdzić, że stary AMC nie jest do tego potrzebny i że nie działa drugi serwer potoku. Szczególnie obserwować odziedziczone ścieżki fokusa, które uruchamiają się później z osobnych timerów/zdarzeń silnika. Nie traktować transportowego OK jako gwarancji pełnego odtwarzania lub zapisu nagrania.

Dla dalszego audytu innymi modelami/Hermesem: sprawdzić spójność głównego routera i warstwy globalnej, zakres odtwarzania po presetach i przy usunięciu elementu, odziedziczone asynchroniczne przywracanie fokusa, ukryte wielozaznaczenia, uprawnienia foreground i konflikty z innymi dodatkami. Nie dostarczać modeli do testów z prywatnymi tokenami, logami konta lub rzeczywistymi nagraniami bez osobnej decyzji użytkownika.

## Źródła

- [NV Access — developer guide](https://download.nvaccess.org/documentation/developerGuide.html).
- [NVDA inputCore](https://github.com/nvaccess/nvda/blob/master/source/inputCore.py).
- [Microsoft — skróty Windows](https://support.microsoft.com/en-us/accessibility/windows/keyboard-shortcuts-in-windows).
- [AllowSetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-allowsetforegroundwindow).
- [GetNamedPipeServerProcessId](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getnamedpipeserverprocessid).
