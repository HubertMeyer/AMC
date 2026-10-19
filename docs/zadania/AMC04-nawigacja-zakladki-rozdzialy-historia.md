# AMC04 — zakładki, rozdziały i historia nawigacji

- Status: **W trakcie — kod i testy zakończone, brak instalacji i ręcznego odbioru NVDA**
- Data rozpoczęcia w AMC Test: 2026-10-19
- Repozytorium wykonawcze: `D:\Projekty Codex\AMC - integracja wxPython`
- Materiał historyczny, tylko do odczytu:
  - `D:\Projekty Codex\Accessible Multimedia Controller\AMC03_AUDYT_SKROTOW_2026-10-18.md`
  - `D:\Projekty Codex\Accessible Multimedia Controller\AMC04_REALIZACJA_ETAP_A_2026-10-18.md`

## Zakres zakończonego etapu

W bieżącym AMC Test rozdzielono cztery niezależne pojęcia: zakładki,
zakładki nazwane, rozdziały oraz historię widoków. Dodano również nawigację po
historii odtwarzanych elementów. Polecenia klawiatury, menu Odtwarzanie i Widok,
Pomoc klawiatury `Ctrl+F1`, pełny spis skrótów, paleta `Ctrl+Shift+K` i most
poleceń NVDA prowadzą do tych samych akcji i są filtrowane przez bieżącą sesję
oraz stan odtwarzacza.

Zakładki i rozdziały są zapisywane tylko dla sesji z trwałym identyfikatorem
materiału i znaną osią czasu: Pliki lokalne oraz Podcasty i YouTube. Żądanie
przekazuje identyfikator sesji jawnie, więc film YouTube nie może zostać omyłkowo
zapisany jako lokalny plik. TIDAL, Spotify, WiiM i Sonos nie otrzymały pozornych
zakładek.

## Materiał do dokumentacji użytkownika

W otwartym odtwarzaczu Plików lokalnych albo Podcastów i YouTube działają:

- `B` — dodaje szybką zakładkę w bieżącym miejscu;
- `Ctrl+Shift+B` — pyta o nazwę i dodaje nazwaną zakładkę;
- `Shift+Page Up` oraz `Shift+Page Down` — przechodzą po wszystkich zakładkach;
- `Ctrl+Shift+Page Up` oraz `Ctrl+Shift+Page Down` — przechodzą tylko po
  zakładkach nazwanych;
- `Ctrl+Shift+strzałka w lewo` oraz `Ctrl+Shift+strzałka w prawo` — przechodzą
  po rzeczywistych rozdziałach materiału;
- `Ctrl+Alt+Page Up` oraz `Ctrl+Alt+Page Down` — zgodne skróty alternatywne do
  poprzedniego i następnego rozdziału;
- `Ctrl+Alt+B` — otwiera listę rozdziałów, wybiera rozdział właściwy dla
  bieżącej pozycji i pozwala przejść do wybranego początku Enterem;
- `Ctrl+Alt+Shift+B` — pyta o nazwę i dodaje rozdział użytkownika;
- `Alt+strzałka w dół` — przechodzi do starszego odtwarzanego elementu;
- `Alt+strzałka w górę` — przechodzi do nowszego odtwarzanego elementu.

`Alt+strzałka w lewo` wraca do poprzedniego widoku, a `Alt+strzałka w prawo`
idzie ponownie do następnego widoku. Historia widoków zachowuje sesję, rodzaj
listy, otwarty kontener i zaznaczenie, ale nie cofa aktualnego stanu odtwarzania.
Na listach o ręcznej kolejności `Alt+strzałka w górę` i `Alt+strzałka w dół`
nadal przenoszą element; historia odtwarzania działa tymi klawiszami tylko w
odtwarzaczu.

Zakładki nazwane nadal są zakładkami użytkownika. Nie są traktowane jak
rozdziały dostawcy. Jeden punkt czasu może pełnić obie funkcje, lecz oba widoki
i oba rodzaje nawigacji pozostają oddzielne. Zbiorcza lista wszystkich zakładek
pozostaje pod `Ctrl+B`; „Zakładki zaznaczonego” pozostają pozycją menu i nie
zajmują już `Ctrl+Shift+B`.

Przykładowe krótkie komunikaty NVDA to nazwa i czas znalezionej zakładki lub
rozdziału, „Brak następnej nazwanej zakładki w tym materiale”, „Brak poprzedniego
rozdziału”, „Brak wcześniejszego widoku” i „Ten materiał nie ma rozdziałów”.
Okna nazwy zakładki i rozdziału oraz lista rozdziałów otrzymują wyłącznie
użytkowe etykiety; nie ujawniają nazw klas, identyfikatorów ani reprezentacji
obiektu.

## Uzasadnienie i decyzje

- Zakładka nazwana jest ręcznie opisanym punktem użytkownika. Rozdział jest
  strukturą materiału pochodzącą od dostawcy albo świadomie utworzoną jako
  rozdział. Wspólna tabela zapisu nie oznacza wspólnej funkcji w interfejsie.
- Nawigacja po widokach i nawigacja po odtwarzanych elementach dostały osobne
  osie klawiszy, aby `Alt+lewo/prawo` nigdy nie zmieniało materiału.
- Migawka historii widoku nie zawiera żywego tytułu, pozycji ani stanu
  odtwarzania. Powrót do listy nie może cofnąć transportu.
- Host C# otrzymuje jawne `files` albo `podcasts` przy zapisie i odczycie.
  To usuwa zgadywanie rodzaju sesji z typu elementu i obejmuje także filmy
  YouTube odtwarzane w sesji Podcasty i YouTube.
- Lista rozdziałów składa etykiety z nazwy i czasu. Modelowe identyfikatory
  rozdziałów nie są przekazywane do nazwy dostępnej kontrolki.

### Korekta użytkownika z 2026-10-18

Ta decyzja zastępuje wcześniejsze utożsamienie nazwanych zakładek z rozdziałami
oraz wcześniejsze zajęcie `Ctrl+Shift+B` na liście przez „Zakładki
zaznaczonego”. `Ctrl+Shift+B` służy teraz wyłącznie dodaniu nazwanej zakładki w
odtwarzaczu. Rozdziały mają `Ctrl+Shift+lewo/prawo`, a nazwane zakładki
`Ctrl+Shift+Page Up/Page Down`.

Ta sama korekta zastępuje pomocniczy skrót `Shift+B` dla nazwanej zakładki
trwającego nagrania radiowego. W aktywnym kontekście nagrywania obowiązują
spójnie `B` oraz `Ctrl+Shift+B`.

## Zmienione miejsca

- `src/AccessibleMediaController.Core/Configuration/BookmarkIndex.cs`
- `src/AccessibleMediaController.LiteHost/LiteBookmarkStore.cs`
- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/navigation.py`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/nvda_bridge.py`
- testy rdzenia, hosta, skrótów, menu, mostu NVDA i GUI wymienione w commicie.

## Testy i wynik

- Ukierunkowane testy skrótów, menu, zakładek, mostu NVDA i nagrywania:
  `165 passed`.
- Dodatkowa regresja historii widoków i lewej strzałki: `65 passed`.
- Testy po jawnym dodaniu identyfikatora sesji do zapisu zakładki:
  `16 passed`.
- Końcowa regresja menu, etykiet i pomocy: `85 passed`.
- Pełny zestaw wxPython: `1760 passed, 110 skipped, 11 subtests passed`.
- Testy protokołu LiteHost po kompilacji Release: wszystkie zestawy przeszły,
  `20` zestawów.
- Testy Core Smoke po kompilacji Release: kod wyjścia `0`, w tym trwałe
  zakładki i chronologiczne rozdziały.
- `git diff --check`: bez błędów białych znaków; ostrzeżenia dotyczyły tylko
  repozytoryjnej konwersji końców linii LF/CRLF.

To są wyniki kodu i testów. Nie są dowodem instalacji ani ręcznego odbioru z
NVDA. AMC04 nie weszło do wcześniej zainstalowanej wersji
`2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`.

## Znane ograniczenia

- Ręczny odbiór na żywym NVDA pozostaje do wykonania po instalacji nowszej
  paczki: początkowy fokus listy rozdziałów, strzałki, Enter, Escape, powrót
  fokusu, ponowne otwarcie oraz kolejność komunikatów.
- Zakładki i rozdziały nie są reklamowane dla TIDAL, Spotify, WiiM i Sonosa,
  ponieważ te sesje nie zapewniają w tym kontrakcie wspólnej trwałej osi czasu.
- Rozdziały dostawcy pojawią się tylko tam, gdzie importer zapisał rzeczywiste
  dane rozdziałów. Brak rozdziałów jest komunikowany wprost.
- Nie wykonano instalacji ani uruchomienia nowej paczki po tym commicie, aby
  połączyć bezpiecznie AMC04 z następną małą bramką AMC05/AMC13.

## Wersja i commit

- Implementacja i testy: `b1786e1a` —
  `feat(amc04): ujednolic nawigacje zakladek i rozdzialow`.
- Dokumentacja zadania: commit następujący po commicie implementacji.
- Kompilacja: projekty testowe Core i LiteHost, konfiguracja Release — sukces.
- Instalacja: nie wykonano dla tego commita.
- Publikacja: nie wykonano; brak wysyłania do GitHuba i brak wydania publicznego.
