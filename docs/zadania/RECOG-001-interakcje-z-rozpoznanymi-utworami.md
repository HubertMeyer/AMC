# RECOG-001 — interakcje z rozpoznanymi utworami

- Status: **W trakcie; kod, testy, build i instalacja AMC Test są gotowe,
  pozostaje ręczny odbiór z NVDA**.
- Data wdrożenia: 26.10.2026.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Profil: wyłącznie AMC Test. AMC Public i GitHub nie zostały zmienione.

## Zachowanie widoczne dla użytkownika

Lista `Ctrl+Alt+S` zachowuje zwięzłe wiersze. Wielowierszowy tekst z tytułem,
wykonawcą, albumem, stacją i łączami pozostaje wynikiem `Ctrl+C`, a nie mową
podczas chodzenia strzałkami.

- `Enter` otwiera utwór w domyślnej usłudze. Spotify korzysta z obsługi AMC;
  TIDAL używa istniejącego przekazania do oryginalnej aplikacji.
- `Ctrl+Enter` otwiera album w domyślnej usłudze wewnątrz AMC i ustawia fokus
  na rozpoznanym utworze.
- `Strzałka w prawo` pokazuje krótką listę najważniejszych działań. `Strzałka
  w lewo` podaje krótko album, wydanie i stację. `Escape` wraca z zachowaniem
  fokusu.
- Menu kontekstowe zawiera pełny zestaw w podmenu `Usługi, łącza i
  powiązania`. Obie powierzchnie korzystają z tego samego modelu działań.
- `Ctrl+C` na liście głównej kopiuje dotychczasowy wielowierszowy opis.
  `Ctrl+Shift+C` rozwiązuje na żądanie i kopiuje dokładne łącze do utworu w
  usłudze domyślnej. Na krótkiej liście `Ctrl+C` kopiuje nazwę działania, a
  `Ctrl+Shift+C` związane z nim łącze.
- `Alt+strzałka w górę` i `Alt+strzałka w dół` zmieniają trwałą kolejność.
  NVDA otrzymuje komunikat `Nad …` albo `Pod …` z nazwą sąsiedniego utworu.
- Ustawienie `Domyślna usługa rozpoznanych utworów` pozwala wybrać Spotify
  albo TIDAL. Apple Music celowo nie jest usługą domyślną.

`Spotify — pokaż utwór w AMC` i `TIDAL — pokaż utwór w AMC` wyłącznie
przechodzą do odpowiedniej sesji, otwierają album i ustawiają fokus na utworze;
nie rozpoczynają odtwarzania. Oddzielne działania otwierają oryginalne
aplikacje.

Apple Music działa bez Apple ID i bez tokenów. Na jawne polecenie AMC odpytuje
publiczny katalog, zachowuje dokładne łącze do utworu i albumu w pamięci
podręcznej, a zawsze dostępne wyszukiwanie otwiera stronę publiczną. Spotify i
TIDAL są rozwiązywane tak samo na żądanie, aby zwykłe poruszanie się po liście
nie wykonywało zapytań sieciowych.

## Uzasadnienie i decyzje

- Korekta użytkownika z 26.10.2026 zastępuje wcześniejsze rozważanie pełnej
  integracji Apple Music: obecny etap obejmuje wyłącznie publiczne łącza.
- Korekta użytkownika z 26.10.2026 zastępuje pomysł czytania pełnego rekordu
  na liście: długi opis pochodził ze schowka i ma tam pozostać.
- Krótka lista pod prawą strzałką i pełne menu nie są dwiema implementacjami;
  są dwoma widokami jednego katalogu działań.
- Dokładne wyniki są pobierane dopiero po działaniu użytkownika i buforowane.
  Dzięki temu nawigacja jest natychmiastowa i nie obciąża usług.

## Testy i wynik

- Pełna regresja wxPython podczas promocji: **2057 zaliczonych, 111
  kontrolowanie pominiętych, 13 podtestów zaliczonych**.
- Końcowy zestaw nowych poleceń, menu, skrótów i pomocy: **106/106**.
- Testy obejmują wspólny model krótkiej i pełnej listy, konserwatywne
  dopasowanie katalogowe, publiczne Apple Music bez nagłówka autoryzacji,
  trwały cache, domyślną usługę oraz niezmieniony wielowierszowy `Ctrl+C`.
- Automatyczna kontrola paczki, sum i izolowany start interfejsu oraz hosta:
  zaliczone.

## Znane ograniczenia i ręczny odbiór

- Dopasowanie może uczciwie zwrócić brak dokładnego wyniku; AMC nie podstawia
  wtedy podobnego utworu.
- TIDAL nie ma drugiego wewnętrznego odtwarzacza. Odtwarzanie rozpoznanego
  utworu kończy się w oryginalnej aplikacji TIDAL.
- Do ręcznego odbioru z NVDA pozostają: fokus początkowy, prawa i lewa
  strzałka, Escape, ponowne otwarcie, `Ctrl+C`, `Ctrl+Shift+C`, `Ctrl+Enter`,
  oba kierunki przenoszenia oraz fokus utworu po otwarciu albumu w Spotify i
  TIDAL.

## Materiał do dokumentacji użytkownika

> Otwórz Rozpoznane utwory skrótem Ctrl+Alt+S. Enter otwiera utwór, Ctrl+Enter
> jego album, a prawa strzałka pokazuje najważniejsze działania dla Spotify,
> TIDAL i Apple Music. Ctrl+C kopiuje pełny opis, a Ctrl+Shift+C dokładne
> łącze w wybranej domyślnej usłudze. Pełny zestaw znajduje się w menu
> kontekstowym, w pozycji Usługi, łącza i powiązania.

## Projekt opisu zmian

> Rozpoznane utwory otrzymały wspólne działania klawiatury i menu, otwieranie
> albumu z fokusem na właściwym utworze, trwałą ręczną kolejność oraz publiczne
> łącza Apple Music rozwiązywane dopiero na żądanie.

## Wersja i commit

- Commit źródłowy: `bba5e92d687ade1998e79c88656e1a5d545abcf2` —
  `feat(amc-test): rozbuduj rozpoznane utwory i pobieranie wideo`.
- Pakiet: `39f0d3f2`.
- Etykieta: `2026.10.26-bba5e92d687ade1998e79c88656e1a5d545abcf2-39f0d3f2`.
- Okno: `AMC Test — 26.10.2026, 13:32`.
- Promocja zakończona 26.10.2026 o 13:34 czasu lokalnego.
- Publikacja: nie wykonywano.
