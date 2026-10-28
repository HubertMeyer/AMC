# KEY-001 — konfigurowalne skróty klawiaturowe

Status: **Zrobione — kod, pełna regresja, czysta paczka, instalator, wydanie
GitHub i rzeczywista aktualizacja instalacji zweryfikowane; użytkownik
zatwierdził obsługę klawiatury i skróty 28.10.2026**

## Zgłoszenie użytkownika

26 października 2026 r. użytkownik wskazał jako wzorzec dostępnego klienta
WinZapp: zmieniona kombinacja jest natychmiast widoczna w polu edycyjnym i na
liście, ale do działania wchodzi dopiero po zatwierdzeniu okna. Użytkownik
zaproponował osobną kartę **Klawiatura** w Ustawieniach AMC.

## Zachowanie użytkowe

- **Ustawienia programu**, `Ctrl+,`, zawierają osobną kartę **Klawiatura**.
- Pole **Filtruj polecenia klawiatury** ogranicza listę po użytkowej nazwie.
- Lista **Polecenia i przypisane skróty** pokazuje wyłącznie jawne nazwy i
  etykiety klawiszy, na przykład `Pauza albo wznowienie; skrót: Spacja
  (domyślny)`. Nie mówi nazw enumów, klas ani identyfikatorów komend.
- Pole **Nowy skrót dla wybranego polecenia** pokazuje zmianę oczekującą i
  przechwytuje następną bezpieczną kombinację.
- **Usuń skrót**, **Przywróć domyślny** i **Przywróć wszystkie domyślne**
  zmieniają wyłącznie roboczą kopię w otwartym oknie.
- **Zapisz** atomowo utrwala cały zestaw i dopiero wtedy przełącza działający
  resolver, menu, paletę `Ctrl+Shift+K`, pełną pomoc `F1` oraz interaktywną
  Pomoc klawiatury `Ctrl+F1`. **Anuluj ustawienia** odrzuca zmiany.
- Brak osobnego przycisku **Zastosuj** w pierwszej wersji. Jedna granica zapisu
  upraszcza przewidywanie stanu i komunikat NVDA.

## Komunikaty czytnika ekranu

Po przyjęciu kombinacji AMC mówi:

> Nazwa polecenia: nowy skrót. Zmiana zacznie działać po zapisaniu ustawień.

Konflikt otwiera komunikat **Nie zmieniono skrótu** z nazwą polecenia, które
już używa kombinacji. Po zapisie pozostaje istniejące pojedyncze
**Zapisano ustawienia**. Przywrócenie wszystkich wartości również wyraźnie
mówi, że zmiana oczekuje na zapis.

## Jeden model poleceń i różnice kontekstowe

Nadpisanie jest zapisane dla `Action`, nie dla jednej powierzchni. Nowy skrót
zachowuje dotychczasową dostępność polecenia. Przykładowo skrót dodawania stacji
działa nadal wyłącznie na właściwej liście Radia, a menu i paleta nie reklamują
go w obcej sesji.

Zmiana akcji wyłącza wszystkie jej stare aliasy. Zapobiega to sytuacji, w
której lista pokazuje nową kombinację, lecz stara nadal po cichu działa.

Stałe pozostają gesty odzyskania i natywnej nawigacji: Enter, Backspace,
Escape, `F1`, `Ctrl+F1`, `F6`, zmiana sesji, natywne presety, kolejka TIDAL i
globalne zatrzymanie wszystkich nagrań. AMC rezerwuje też gesty Windows i
dynamiczne `Ctrl+1–9`. Nowa kombinacja musi zawierać `Ctrl` lub `Alt`, chyba że
jest klawiszem funkcyjnym `F1–F24`; dzięki temu zwykłe pisanie i nawigacja list
nie są przejmowane.

## Uzasadnienie i decyzje

- Wybrano osobną kartę **Klawiatura**, ponieważ lista poleceń, filtr,
  przechwytywanie i przywracanie tworzą samodzielny obszar, a nie pojedynczą
  opcję ogólną.
- Stan oczekujący jest kopią. Działającego okna nie zmieniamy podczas
  eksperymentowania ani po **Anuluj**.
- Konflikty są blokowane globalnie, również gdy dwie komendy zwykle występują
  w innych sesjach. Jest to bardziej przewidywalne niż ten sam gest o wielu
  znaczeniach po późniejszej zmianie kontekstu.
- Model przechowuje identyfikatory i kanoniczne klawisze osobno od polskich
  etykiet mówionych.

## Zmienione źródła

- `wxlite/amc_wx_lite/shortcuts.py` — katalog edytowalnych poleceń,
  walidacja, konflikty, serializacja i resolver nadpisujący domyślne skróty;
- `wxlite/amc_wx_lite/state_store.py` — prywatny zapis
  `shortcut_overrides` z odrzucaniem obcych i chronionych wartości;
- `wxlite/amc_wx_lite/menu_model.py` — bieżąca etykieta skrótu z tego samego
  modelu oraz nazwa **Ustawienia programu**;
- `wxlite/amc_wx_lite/command_palette.py` — ten sam skrót w palecie;
- `wxlite/amc_wx_lite/gui.py` — karta, robocza kopia, nazwy dostępności,
  zapis/anulowanie i podłączenie resolvera, menu oraz obu rodzajów pomocy;
- `wxlite/tests/test_shortcut_customization.py` i
  `wxlite/tests/test_transport_parity.py` — kontrakty i regresja nazwy.

## Testy i wynik

27 października 2026 r.:

- `py_compile` pięciu zmienionych modułów oraz `gui.py`: zaliczone;
- przypięty Python 3.14 / wxPython 4.3.1, sześć plików testowych obejmujących
  skróty, paletę, stan, dialog i parytet transportu: **181 zaliczonych, 0
  błędów** w 9,43 s;
- nowy kontrakt KEY-001: **9 zaliczonych** także przez projektowy runner
  standardowej biblioteki;
- pierwsza próba runnerem systemowym zgłosiła siedem błędów importu modułu
  `pytest`; nie były to wyniki funkcjonalne AMC. Powtórzenie w przypiętym
  środowisku usunęło to ograniczenie;
- pełna regresja po poprawkach: **2074 zaliczone, 112 kontrolowanie
  pominiętych i 13 zaliczonych podtestów** w 194,29 s;
- po końcowym zaostrzeniu walidacji nazw klawiszy ponowiono związany zestaw:
  **190 zaliczonych** w 6,87 s;
- budowa samowystarczalnej paczki v2 zakończyła się powodzeniem, a skrypt
  potwierdził integralność i kontrolowany start interfejsu oraz hosta.

Wspólna weryfikacja wydania SET-001 i KEY-001 27.10.2026:

- pełna regresja wxPython: **2094 zaliczone, 113 kontrolowanie pominiętych i 13
  zaliczonych podtestów** w 199,80 s;
- wszystkie **27** zestawów testów protokołu LiteHosta zaliczone;
- testy Launchera i Updatera: **33 z 33 zaliczone**; pełne testy dymne Core
  zakończone kodem 0;
- czysta paczka z commitu `4cb57da5a6bda7bb82696ff426c00f2b9f655704`
  zawiera 2136 plików, przeszła pełną kontrolę integralności i kontrolowany
  start;
- instalator `AMC-Test-2026-10-27-0057.exe` przeszedł skan danych poufnych i
  zawiera Quick App Switcher 0.1.6;
- wydanie testowe `test-2026.10.27.0057` opublikowano i odczytowo
  zweryfikowano na GitHubie wraz z sumami plików.

Rzeczywista aktualizacja 27.10.2026:

- oficjalny `AMC-Python-Updater.exe` bezpiecznie zamknął poprzednią instancję,
  zainstalował pełny instalator i uruchomił AMC Test ponownie;
- manifest instalacji zmienił wersję z `26.10.2026, 19:54`, commit
  `251e163a`, na `27.10.2026, 00:57`, commit `4cb57da5`, pakiet `73ec48a6`;
- pełna kontrola integralności zainstalowanego pakietu zakończyła się kodem 0,
  a po starcie działała jedna instancja AMC Test;
- interfejs natywny sterowania oknem nie był dostępny w sesji automatyzacji,
  dlatego w tym dniu menedżer skrótów nadal wymagał ręcznego odbioru z NVDA.

Korekta użytkownika z 28.10.2026 zastępuje wcześniejsze ustalenie „ręczny
odbiór NVDA pozostaje”: użytkownik zatwierdził skróty i całą obsługę
klawiatury jako gotowe i działające prawidłowo. Ewentualny później wykryty,
konkretny defekt będzie osobną poprawką, a nie powodem dalszego blokowania
KEY-001.

Nie uruchomiono Ruffa, ponieważ moduł nie jest dostępny w przypiętym
środowisku. Nie jest to przedstawiane jako zaliczony lint.

## Znane ograniczenia

- Ręczny odbiór klawiatury i skrótów został zatwierdzony przez użytkownika
  28.10.2026; nie pozostaje otwarta bramka odbioru dla KEY-001.
- Pierwsza wersja nie zmienia chronionych gestów ratunkowych i natywnych.
- Nie ma osobnego **Zastosuj**; ewentualne dodanie wymaga osobnej decyzji po
  odbiorze prostszego wariantu.

## Migracja

Brak wpisu `shortcut_overrides` oznacza wszystkie wartości domyślne, więc
dotychczasowe profile nie wymagają konwersji. Nieznane akcje i uszkodzone albo
sprzeczne skróty są pomijane przy odczycie zamiast blokować start programu.

## Materiał do dokumentacji użytkownika

Projekt do korekty i zatwierdzenia użytkownika:

> Aby zmienić skrót, otwórz **Ustawienia programu** skrótem `Ctrl+,` i wybierz
> kartę **Klawiatura**. Wyszukaj polecenie, przejdź do pola **Nowy skrót dla
> wybranego polecenia** i naciśnij kombinację. Nowy skrót pojawi się od razu
> na liście, lecz zacznie działać dopiero po wybraniu **Zapisz**. **Anuluj
> ustawienia** zachowuje wcześniejsze skróty. Przyciski na karcie pozwalają
> usunąć skrót albo przywrócić wartości domyślne.

## Projekt wpisu do changelogu

Projekt do korekty i zatwierdzenia użytkownika:

- Dodano kartę **Klawiatura** w Ustawieniach programu. Pozwala filtrować
  polecenia, przechwycić bezpieczną kombinację, wykryć konflikt, usunąć skrót
  albo przywrócić wartości domyślne. Zmiany są widoczne przed zatwierdzeniem,
  ale zaczynają działać dopiero po wybraniu **Zapisz**; menu, paleta poleceń i
  obie pomoce korzystają z tego samego zestawu skrótów.

## Wersja i commit

- gałąź robocza: `codex/konfigurowalne-skroty-20261026`;
- commit funkcjonalny SET-001 i KEY-001: `d43d24b566a5c31fd1f862fa92ae65b7adbc8c84`;
- commit źródłowy wydania: `4cb57da5a6bda7bb82696ff426c00f2b9f655704`;
- wersja techniczna: `0.1.0-alpha.435`; wersja widoczna dla użytkownika:
  `27.10.2026, 00:57`;
- czysty manifest paczki: identyfikator `73ec48a6`, profil `test`, 2136 plików,
  `sourceDirty=false`;
- instalator: `AMC-Test-2026-10-27-0057.exe`, 134290649 bajtów, SHA-256
  `a09a957923afd708a78445d4bb9574181d222ce9ee557c776118bb5cb86a2329`;
- wydanie GitHub: `test-2026.10.27.0057`, opublikowane i odczytowo
  zweryfikowane;
- lokalna aktualizacja przez oficjalny aktualizator: wykonana i zweryfikowana;
- ręczny odbiór menedżera skrótów i klawiatury: zatwierdzony przez użytkownika
  28.10.2026.

Wspólny artefakt końcowy powstał z czystego, odizolowanego worktree. Równoległa
niezwiązana zmiana użytkownika w głównym drzewie roboczym została zachowana i
nie weszła do wydania.
