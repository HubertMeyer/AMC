# MENU-001 — menu kontekstowe i skróty zależne od sesji

Status: **W trakcie; korekta źródłowa i testy ukierunkowane gotowe, pełna
regresja, instalacja i odbiór NVDA jeszcze niewykonane**.

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

Zakładki, nazwane zakładki, rozdziały i historia nadal mają rozdzielone
znaczenia z AMC04. `Alt+lewo/prawo` przechodzi po historii widoków.
`Alt+góra/dół` w odtwarzaczu wybiera starszy lub nowszy odtwarzany element,
natomiast na liście z ręczną kolejnością przenosi element. Menu nie reklamuje
tych poleceń w sesji lub widoku, który nie ma wymaganej tożsamości albo osi
czasu.

## Uzasadnienie i decyzje

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

## Testy i wynik

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

## Znane ograniczenia

- Odbiór NVDA musi potwierdzić menu listy i odtwarzacza w Plikach lokalnych,
  Radiu, Podcastach i YouTube, Spotify, TIDAL, WiiM i Sonos.
- Pozycje niedostępne są pomijane w menu kontekstowym; pasek menu może je
  pozostawić wyszarzone, aby uczciwie pokazać chwilowy brak warunku.
- Zadanie nie zmienia przypisań AMC04 ani nie dodaje zakładek do sesji bez
  stabilnej pozycji.

## Wersja i commit

- Źródła: commit `fdc26b83` — `fix(amc): uporzadkuj nagrania menu i playlisty
  Spotify`.
- Testy ukierunkowane: zaliczone.
- Kompilacja, instalacja i uruchomienie: jeszcze niewykonane.
- Publikacja: niewykonana i niedozwolona bez osobnego polecenia użytkownika.
