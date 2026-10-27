# RECOG-001 — interakcje z rozpoznanymi utworami

- Status: **W trakcie; korekty oznajmiania kopiowania oraz dostępności
  `Ctrl+Alt+S` z 27.10.2026 mają gotowe źródła i testy celowane, ale nie
  zostały jeszcze zbudowane ani zainstalowane; pozostaje ręczny odbiór z
  NVDA**.
- Data wdrożenia: 26.10.2026.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Profil: wyłącznie AMC Test. AMC Public i GitHub nie zostały zmienione.

## Zachowanie widoczne dla użytkownika

Lista `Ctrl+Alt+S` zachowuje zwięzłe wiersze. Wielowierszowy tekst z tytułem,
wykonawcą, albumem, stacją i łączami pozostaje wynikiem `Ctrl+C`, a nie mową
podczas chodzenia strzałkami.

- `Ctrl+Alt+S` otwiera listę z każdego widoku sesji Pliki lokalne i Radio:
  zarówno z listy, jak i z odtwarzacza. Polecenie nie jest obsługiwane ani
  pokazywane w menu, Pomocy, Pomocy klawiatury i palecie w Podcastach,
  TIDAL-u, Spotify, WiiM, Sonosie oraz Frontier Smart. `Escape` zamyka okno.
- `Enter` otwiera utwór w domyślnej usłudze. Spotify korzysta z obsługi AMC;
  TIDAL używa istniejącego przekazania do oryginalnej aplikacji.
- `Ctrl+Enter` otwiera album w domyślnej usłudze wewnątrz AMC i ustawia fokus
  na rozpoznanym utworze.
- `Strzałka w prawo` pokazuje lekką, krótką listę najważniejszych działań i
  od razu ustawia fokus na pierwszym działaniu, zgodnie z listami relacji
  Spotify i TIDAL. W zwykłym trybie NVDA nie otrzymuje wcześniej nagłówka ani
  instrukcji klawiszy. Opis `Enter`, `Ctrl+C`, `Ctrl+Shift+C`, lewej strzałki
  i `Escape` jest pomocą kontrolki wyłącznie po włączeniu rozszerzonych
  komunikatów programu. `Strzałka w lewo` na liście głównej podaje krótko
  album, wydanie i stację, a `Escape` zachowuje fokus po powrocie.
- Menu kontekstowe zawiera pełny zestaw w podmenu `Usługi, łącza i
  powiązania`. Obie powierzchnie korzystają z tego samego modelu działań.
- `Ctrl+C` na liście głównej kopiuje dotychczasowy wielowierszowy opis.
  `Ctrl+Shift+C` rozwiązuje na żądanie i kopiuje dokładne łącze do utworu w
  usłudze domyślnej. Na krótkiej liście `Ctrl+C` kopiuje nazwę działania, a
  `Ctrl+Shift+C` związane z nim łącze.
- Po udanym kopiowaniu aktywne okno przekazuje NVDA krótki komunikat:
  `Skopiowano opis`, `Skopiowano łącze do utworu w Spotify` albo
  `Skopiowano łącze do utworu w TIDAL` na liście głównej oraz `Skopiowano
  nazwę działania` lub `Skopiowano łącze` na liście spod prawej strzałki.
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
- Korekta użytkownika z 26.10.2026 zastępuje modalny dialog prawej strzałki z
  zawsze czytanym tytułem i instrukcją: zwykły tryb przechodzi bezpośrednio na
  pierwszy wiersz, a instrukcja pozostaje tylko w rozszerzonych komunikatach.
- Korekta użytkownika z 27.10.2026 zastępuje samo wizualne ustawienie tekstu
  po kopiowaniu. Potwierdzenie musi wysłać pojedyncze zdarzenie lokalnego
  regionu aktywnego w aktualnym oknie, ponieważ komunikator nieaktywnej ramki
  głównej celowo nie wchodzi NVDA w słowo.
- Korekta użytkownika z 27.10.2026 rozszerza dostępność historii rozpoznanych
  utworów z samego Radia na wszystkie widoki sesji Pliki lokalne i Radio.
  Nie rozszerza jej na sesje usługowe ani Podcasty i YouTube, które nie są
  źródłem tego podglądu.
- Krótka lista pod prawą strzałką i pełne menu nie są dwiema implementacjami;
  są dwoma widokami jednego katalogu działań.
- Dokładne wyniki są pobierane dopiero po działaniu użytkownika i buforowane.
  Dzięki temu nawigacja jest natychmiastowa i nie obciąża usług.

## Testy i wynik

- Pełna regresja wxPython podczas promocji: **2062 zaliczone, 111
  kontrolowanie pominiętych, 13 podtestów zaliczonych**.
- Celowany zestaw rozpoznawania, ustawień, menu, skrótów, palety i zgodności
  ze Spotify/TIDAL: **182/182**.
- Testy obejmują wspólny model krótkiej i pełnej listy, konserwatywne
  dopasowanie katalogowe, publiczne Apple Music bez nagłówka autoryzacji,
  trwały cache, domyślną usługę, niezmieniony wielowierszowy `Ctrl+C` oraz
  zwięzłe okno prawej strzałki bez stałej instrukcji.
- Automatyczna kontrola paczki, sum i izolowany start interfejsu oraz hosta:
  zaliczone.
- Korekta oznajmiania z 27.10.2026: **18/18 testów celowanych bez widocznego
  interfejsu**. Sprawdzono lokalny region aktywny obu list, cztery komunikaty
  kopiowania oraz brak natychmiast nadpisywanego `Sprawdzam…` przy łączu z
  pamięci podręcznej. Pełnej regresji ani testów GUI nie uruchamiano.
- Korekta zakresu `Ctrl+Alt+S` z 27.10.2026: **142/142 testy celowane bez
  widocznego interfejsu**. Sprawdzono wykonanie z listy i odtwarzacza Plików
  lokalnych oraz Radia, brak polecenia w sześciu pozostałych sesjach i parytet
  nazwy, skrótu, menu, Pomocy, Pomocy klawiatury i palety poleceń. Kontrola
  składni oraz `git diff --check` także zakończyły się powodzeniem. Pełnej
  regresji ani testów GUI nie uruchamiano.

## Znane ograniczenia i ręczny odbiór

- Dopasowanie może uczciwie zwrócić brak dokładnego wyniku; AMC nie podstawia
  wtedy podobnego utworu.
- TIDAL nie ma drugiego wewnętrznego odtwarzacza. Odtwarzanie rozpoznanego
  utworu kończy się w oryginalnej aplikacji TIDAL.
- Do ręcznego odbioru z NVDA pozostają: fokus początkowy, prawa i lewa
  strzałka, brak wstępnego nagłówka i instrukcji w zwykłym trybie, opis przy
  rozszerzonych komunikatach, Escape, ponowne otwarcie, `Ctrl+C`,
  `Ctrl+Shift+C`, `Ctrl+Enter`, oba kierunki przenoszenia oraz fokus utworu po
  otwarciu albumu w Spotify i TIDAL.
- Najnowsza korekta oznajmiania nie jest jeszcze zbudowana ani zainstalowana,
  a korekta zakresu `Ctrl+Alt+S` również pozostaje wyłącznie w źródłach.
  Bieżąca instalacja może zatem nadal kopiować poprawnie bez wypowiedzenia
  potwierdzenia i udostępniać historię tylko w dotychczasowym kontekście.

## Materiał do dokumentacji użytkownika

> Otwórz Rozpoznane utwory skrótem Ctrl+Alt+S. Enter otwiera utwór, Ctrl+Enter
> jego album, a prawa strzałka pokazuje najważniejsze działania dla Spotify,
> TIDAL i Apple Music. Ctrl+C kopiuje pełny opis, a Ctrl+Shift+C dokładne
> łącze w wybranej domyślnej usłudze. Po skopiowaniu NVDA potwierdza, co
> zostało skopiowane. Pełny zestaw znajduje się w menu kontekstowym, w pozycji
> Usługi, łącza i powiązania.

## Projekt opisu zmian

> Rozpoznane utwory otrzymały wspólne działania klawiatury i menu, otwieranie
> albumu z fokusem na właściwym utworze, trwałą ręczną kolejność oraz publiczne
> łącza Apple Music rozwiązywane dopiero na żądanie.

## Wersja i commit

- Najnowsza korekta źródeł: `e16588c0` —
  `fix: expose recognized tracks in local session`.
- Zmienione pliki: `wxlite/amc_wx_lite/shortcuts.py`,
  `wxlite/amc_wx_lite/menu_model.py`, `wxlite/amc_wx_lite/gui.py`,
  `wxlite/tests/test_command_palette.py` i
  `wxlite/tests/test_menu_exposes_existing_actions.py`.
- Stan korekty zakresu sesji: źródła i 142/142 testy celowane gotowe; build,
  instalacja i publikacja nie były wykonywane.
- Wcześniejsza korekta źródeł: `38e0acc8` —
  `fix: announce recognized track copies locally`.
- Zmienione pliki: `wxlite/amc_wx_lite/gui.py`,
  `wxlite/amc_wx_lite/live_region.py` i
  `wxlite/tests/test_recognition_actions.py`.
- Stan korekty: źródła i testy celowane gotowe; build, instalacja i publikacja
  nie były wykonywane.
- Ostatni zainstalowany commit tego zadania: `4c8fceda738afd0163040a400150007d16f8409c` —
  `fix(amc-test): skroc mowe listy rozpoznanych utworow`.
- Pakiet: `faef4e7f`.
- Etykieta: `2026.10.26-4c8fceda738afd0163040a400150007d16f8409c-faef4e7f`.
- Okno: `AMC Test — 26.10.2026, 14:01`.
- Promocja zakończona 26.10.2026 o 14:03 czasu lokalnego.
- Publikacja korekty z 27.10.2026: nie wykonywano.
