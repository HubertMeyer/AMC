# MENU-001 — menu kontekstowe i skróty zależne od sesji

Status: **W trakcie; najnowsza korekta nazw i menu harmonogramów jest
przetestowana w źródłach, ale jeszcze niezainstalowana**.

## Materiał do dokumentacji użytkownika

`Shift+F10` albo klawisz menu otwiera menu bieżącej listy lub odtwarzacza.
Każda pozycja ma najpierw pełną nazwę czynności, a następnie w nawiasie jej
rzeczywisty skrót, na przykład „Szybkie informacje o elemencie (Alt+T)” albo
„Szukaj w bieżącej usłudze (Ctrl+F)”. Menu kontekstowe nie odczytuje osobno
technicznych klawiszy dostępu takich jak `0`, `j`, `t` lub `b`.

`F2` jest opisane według zaznaczonego elementu: „Zmień nazwę stacji”, „Zmień
nazwę playlisty”, „Zmień nazwę podcastu lub kanału” albo „Zmień nazwę pliku w
Bibliotece”. `Shift+F2` pozostaje osobnym poleceniem „Zmień nazwę pliku na
dysku”. Dla strumieni WiiM i własnych stacji Sonos nazwa uczciwie mówi, że
okno zmienia nazwę lub adres. `F2` na lokalnej playliście i playliście
podcastów rzeczywiście zmienia jej nazwę oraz zachowuje elementy.

Menu pokazuje tylko polecenia dozwolone przez bieżącą sesję, widok, rodzaj
wiersza i prawdziwy stan odtwarzania lub nagrywania. Korzysta z tych samych
akcji i bramek, co skróty, `Ctrl+F1`, pełna pomoc i paleta `Ctrl+Shift+K`.

Polecenie `Ctrl+Shift+Enter` nazywa się krótko „Odtwarzaj jako następne”, bez
mylącego dopisku „lub usuń”. `Ctrl+Shift+C` ma nazwę zależną od elementu:
na nagraniu lub innym lokalnym pliku menu mówi „Skopiuj ścieżkę do pliku”, a
w ogólnych powierzchniach „Skopiuj adres lub ścieżkę”.

Zakładki, nazwane zakładki, rozdziały i historia nadal mają rozdzielone
znaczenia z AMC04. `Alt+lewo/prawo` przechodzi po historii widoków.
`Alt+góra/dół` w odtwarzaczu wybiera starszy lub nowszy odtwarzany element,
natomiast na liście z ręczną kolejnością przenosi element. Menu nie reklamuje
tych poleceń w sesji lub widoku, który nie ma wymaganej tożsamości albo osi
czasu.

Ta sama zasada obowiązuje przy następnych funkcjach i w innych dużych
aplikacjach: klawisz dostępu menu nie jest drugim skrótem polecenia, a NVDA nie
może dostać technicznej cyfry, przypadkowej litery, identyfikatora polecenia ani
reprezentacji obiektu. Trwały kontrakt zapisano w instrukcjach repozytorium oraz
w osobistej umiejętności Codexa `accessible-desktop-contracts`.

## Uzasadnienie i decyzje

- **Korekta użytkownika z 19 października 2026:** usunięto z nazwy polecenia
  dopisek „lub usuń”, a lokalny plik nie jest już nazywany adresem. Zmiana
  objęła wspólny model menu, pomoc `Ctrl+F1`, pełną pomoc, paletę oraz
  kontekstową etykietę bieżącego wiersza.
- **Korekta użytkownika z 19 października 2026:** lista harmonogramów musi mieć
  własne menu kontekstowe. Jego pozycje prowadzą do tych samych metod co
  Insert, Enter, Ctrl+D, Spacja, strzałki i Delete.

- **Korekta użytkownika z 19 października 2026:** „Zmień stację” zastąpiono
  nazwą opisującą zmianę nazwy lub adresu, a ogólne `F2` opisuje dokładnie
  rodzaj zaznaczonego elementu.
- **Korekta użytkownika z 19 października 2026:** nazwa wyszukiwania brzmi
  „Szukaj w bieżącej usłudze”, nie samo „W bieżącej usłudze”.
- Pasek menu nadal zachowuje unikatowe klawisze dostępu, ponieważ są potrzebne
  do pełnej obsługi bez myszy. Menu kontekstowe nie czyta ich jako drugiego
  skrótu; pokazuje tylko rzeczywistą kombinację wykonującą polecenie.
- Menu kontekstowe nie ma własnych procedur wykonania. Filtruje aktualnie
  dostępne wpisy wspólnego modelu menu i wysyła tę samą akcję do jednego
  dispatchera.
- Zmiana nazwy playlisty używa pełnej, atomowej migawki playlist danej sesji.
  Nie usuwa elementów, nie zmienia kolejności i po zapisie przywraca fokus na
  ten sam stabilny identyfikator playlisty.
- **Korekta użytkownika z 19 października 2026:** uporządkowanie nie może być
  jednorazową łatką AMC. Reguła rozdzielenia mnemoniców od rzeczywistych
  skrótów, semantycznych nazw i dostępnych etykiet została zapisana jako
  trwały kontrakt projektu oraz automatycznie wykrywana umiejętność Codexa.

## Testy i wynik

- Po korekcie nazw i harmonogramów: **136/136** testów ukierunkowanych oraz
  pełna regresja **1845 zaliczonych, 110 pominiętych, 11 podtestów**.
  Test kolizji mnemoniców wykrył pierwszą nieprawidłową literę dostępu;
  poprawiono ją przed powtórną zieloną bramką.

- 19.10.2026: wspólna bramka nagrywania, Spotify, menu, ustawień i
  harmonogramów — **204 zaliczone**.
- Testy potwierdzają kolejność „nazwa, rzeczywisty skrót”, usunięcie z menu
  kontekstowego `(&0)`, dynamiczną nazwę `F2`, atomową zmianę nazwy playlisty,
  zgodność podpisu skrótu z resolverem oraz unikatowe klawisze dostępu paska.
- Szeroki audyt sesji, skrótów AMC04, pomocy i palety: **403 zaliczone i 5
  podtestów zaliczonych**.
- Pełna regresja wxPython: **1837 zaliczonych, 110 pominiętych i 11 podtestów
  zaliczonych**. Kompilacja, instalacja i uruchomienie nadal pozostają
  osobnymi, jeszcze niewykonanymi krokami.
- Po dodaniu trwałego kontraktu ponownie zaliczono **121** testów menu,
  skrótów, pomocy i palety. Struktura umiejętności, odsyłacze i kodowanie UTF-8
  zostały sprawdzone; dostarczony walidator nie mógł ruszyć bez nieobecnego
  lokalnie modułu `yaml`, dlatego nie pobierano zależności z sieci.
- Pełna regresja po połączeniu kontraktu menu i wspólnego mechanizmu usług:
  **1842 zaliczone, 110 pominiętych i 11 podtestów zaliczonych** w 78,80 s.
- 19 października 2026 procedura promocji ponownie zaliczyła pełne **1842**
  testy wxPython, przy **110 pominiętych** i **11 podtestach zaliczonych**.
  Kompilacje Release przeszły bez ostrzeżeń i błędów; paczka 1666 plików
  przeszła manifest, SHA-256, instalację, kontrolę integralności z kodem 0 i
  weryfikację procesu oraz tytułu „AMC Test”.

## Znane ograniczenia

- Najnowsze nazwy i menu harmonogramów są w commicie `4b85e0c8`, ale nie w
  bieżącej instalacji użytkownika; wymagają jeszcze instalacji i odbioru NVDA.

- Odbiór NVDA musi potwierdzić menu listy i odtwarzacza w Plikach lokalnych,
  Radiu, Podcastach i YouTube, Spotify, TIDAL, WiiM i Sonos.
- Pozycje niedostępne są pomijane w menu kontekstowym; pasek menu może je
  pozostawić wyszarzone, aby uczciwie pokazać chwilowy brak warunku.
- Zadanie nie zmienia przypisań AMC04 ani nie dodaje zakładek do sesji bez
  stabilnej pozycji.

## Wersja i commit

- Korekta po ręcznym odbiorze: `4b85e0c8` — źródła i testy. Instalacja oraz
  uruchomienie tej rewizji jeszcze niewykonane.

- Źródła: commit `fdc26b83` — `fix(amc): uporzadkuj nagrania menu i playlisty
  Spotify`.
- Trwały kontrakt repozytorium: commit `e317cbbc` — `refactor(amc): ujednolic
  listy uslug i kontrakt menu`. Umiejętność osobista
  `accessible-desktop-contracts` jest zapisana poza repozytorium w katalogu
  umiejętności Codexa.
- Testy ukierunkowane: zaliczone.
- Kompilacja, instalacja i uruchomienie:
  `2026.10.19-8093e22adfa9b6abfc72c35c5c7029eaaade88c8-718893c9`;
  zweryfikowane 19 października 2026.
- Publikacja: niewykonana i niedozwolona bez osobnego polecenia użytkownika.
