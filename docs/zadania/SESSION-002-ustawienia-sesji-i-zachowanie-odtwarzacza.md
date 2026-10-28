# SESSION-002 — Ustawienia sesji i zachowanie odtwarzacza

## Status

**Zrobione w źródłach 28.10.2026.** Niewidoczne testy celowane są zaliczone.
Nie wykonano builda, instalacji, publikacji ani ręcznego odbioru z NVDA.

## Zakres

- Polecenie i dialog nazywają się wszędzie **Ustawienia sesji**.
- `Ctrl+Alt+Enter` nadal otwiera ustawienia aktywnej sesji.
- `Ctrl+Shift+S` pokazuje osobny przycisk **Ustawienia sesji…** dla zaznaczonej,
  włączonej sesji. Ustawienia nie są już mylone z folderami, kontem ani
  urządzeniami.
- Zachowanie po uruchomieniu materiału Enterem jest ustawieniem dziedziczonym:
  `Jak ustawienie ogólne`, `Otwórz odtwarzacz` albo `Pozostań na liście`.
- Ustawienie Entera wykonują Pliki lokalne, Radio, Podcasty i YouTube,
  Spotify, materiały Sonos oraz strumienie sieciowe WiiM. Obejmuje też lokalne
  kolejki i zakładki oraz wyniki katalogu Radia i Spotify.
- Pliki lokalne i Radio mają również sesyjny wybór zachowania presetów.
- Ustawienia ogólne zachowują zgodność profilu, ale ich etykiety mówią teraz
  wprost, że są wartościami domyślnymi dla sesji bez własnego wyboru.

## Korekta użytkownika z 28.10.2026

Ta decyzja zastępuje wcześniejsze ograniczenie zapisane w `SESSION-001`, według
którego ustawienia można było otworzyć wyłącznie dla aktywnej sesji. Menedżer
sesji może teraz otworzyć ten sam dialog dla sesji zaznaczonej. Nie zmienia się
natomiast znaczenie `Ctrl+Alt+Enter`: skrót pozostaje kontekstowy i dotyczy
aktywnej sesji.

## Materiał do dokumentacji użytkownika

### Projekt instrukcji

1. Otwórz Menedżer sesji skrótem `Ctrl+Shift+S`.
2. Wybierz włączoną sesję i przejdź do przycisku **Ustawienia sesji…**.
3. W polu **Po uruchomieniu materiału Enterem** wybierz:
   - **Jak ustawienie ogólne** — dialog od razu podaje wynik dziedziczenia;
   - **Otwórz odtwarzacz** — po Enterze AMC przechodzi do odtwarzacza;
   - **Pozostań na liście** — materiał zaczyna grać, a lista i fokus pozostają
     dostępne.
4. Zapisz zmiany. Po zamknięciu ustawień fokus wraca do Menedżera sesji.

Dla aktywnej sesji ten sam dialog można otworzyć szybciej skrótem
`Ctrl+Alt+Enter` albo z menu **Dźwięk > Ustawienia sesji…**.

### Projekt wpisu do changelogu

- Dodano ustawienie sesyjne decydujące, czy uruchomienie materiału Enterem
  otwiera odtwarzacz, czy pozostawia użytkownika na liście. Działa ono także
  dla plików lokalnych, podcastów, Spotify, Sonosa, WiiM, kolejek, zakładek i
  obsługiwanych wyników wyszukiwania.
- Menedżer sesji ma osobną czynność **Ustawienia sesji…**, niezależną od
  konfiguracji folderów, kont i urządzeń.

## Uzasadnienie i decyzje

- Zachowano stare pola ogólne jako domyślne, aby istniejące profile nie
  zmieniły zachowania po aktualizacji. Nowe pola sesji są opcjonalne;
  `None` oznacza dziedziczenie.
- Użyto jednej funkcji rozstrzygającej zachowanie Entera i jednej dla presetów.
  GUI przekazuje wynik do wspólnej nawigacji zamiast utrzymywać wyjątki dla
  Radia i Sonosa.
- Nie pokazuje się martwych pól. TIDAL odtwarza w aplikacji zewnętrznej i
  pozostaje na liście. Frontier Smart wybiera urządzenie sterujące, a nie
  materiał. Zachowanie presetów jest konfigurowalne sesyjnie tylko w Plikach i
  Radiu, bo te dwie drogi obecnie wykonują tę politykę.
- Przycisk konfiguracji w Menedżerze otrzymuje nazwę zależną od sesji, np.
  **Foldery Biblioteki…**, **Konto Spotify…** albo **Urządzenia WiiM…**.
  Dla Radia i Podcastów nie dubluje przycisku ustawień.
- Model przechowuje wartości logiczne osobno od etykiet mówionych. Każda nowa
  lista wyboru ma jawne, użytkowe nazwy i wariant dziedziczony opisujący skutek.

## Komunikaty i fokus czytnika ekranu

- Tytuł: `Ustawienia sesji: <nazwa sesji>`.
- Nazwy pól: `Po uruchomieniu materiału Enterem` i, gdzie dostępne,
  `Po uruchomieniu presetu`.
- Potwierdzenie: `Zapisano ustawienia sesji <nazwa>.`.
- Brak zmiany: `Ustawienia sesji bez zmian.`.
- Po zamknięciu dialogu wywołanego z Menedżera fokus wraca do listy sesji;
  po `Ctrl+Alt+Enter` wraca do listy lub odtwarzacza aktywnej sesji.

## Testy i wynik

Uruchomiono wyłącznie testy bez widocznego GUI, zgodnie z korektą użytkownika
z 27.10.2026.

- Końcowy, połączony przebieg wszystkich dotkniętych zestawów na ostatecznym
  drzewie: **509 zaliczonych** w 84,91 s.
- Główny zestaw ustawień, dialogu, zapisu, nawigacji, Menedżera, pomocy i
  tłumaczeń: **238 zaliczonych** w 74,14 s.
- Regresje zakładek, kolejek, Podcastów, Spotify, WiiM, ustawień ogólnych,
  menu, skrótów i profilu: **268 zaliczonych** w 9,90 s.
- Końcowa kontrola Spotify, wyszukiwania, polityk sesji i i18n po domknięciu
  wyników katalogu: **116 zaliczonych** w 10,61 s.
- Dodatkowa kontrola konfliktów klawiszy dostępu, Spotify i i18n:
  **14 zaliczonych** w 6,06 s.
- Funkcjonalny kontrakt przycisków Menedżera, powrotu fokusu i doboru pól dla
  wszystkich sesji: **27 zaliczonych** w 58,67 s.
- `git diff --check`: zaliczony; jedynie informacyjne ostrzeżenia Git o
  przyszłej normalizacji LF/CRLF w trzech istniejących plikach.

Zestawy częściowo się pokrywają; liczby nie są sumą unikalnych testów.

## Znane ograniczenia

- Nie wykonano widocznego testu wxPython ani odsłuchu NVDA. Do ręcznego odbioru
  pozostają: początkowy fokus, odczyt rozwiniętych wyborów, zapis, anulowanie,
  powrót fokusu i ponowne otwarcie dla kilku sesji.
- `Ctrl+O` i otwieranie pliku przez powłokę Windows nie są uruchomieniem
  materiału Enterem i zachowują dotychczasową nawigację.
- Presety Spotify i Sonosa zachowują własne, istniejące reguły nawigacji; nowa
  sesyjna opcja presetów nie jest tam pokazywana bez wykonawcy.
- Nie powstał build, instalator, instalacja ani wydanie. Nie uruchamiano AMC.

## Zmienione pliki

- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/navigation.py`
- `wxlite/amc_wx_lite/session_options.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/i18n.py`
- `wxlite/amc_wx_lite/locales/en_legacy.json`
- `wxlite/amc_wx_lite/locales/template.json`
- testy celowane w `wxlite/tests/`.

## Wersja i commit

- Wersja źródłowa pakietu: `0.1.0`.
- Commit bazowy: `b15479fc7114e48de5fc838a79d05a4cc5992d7d`.
- Zmiany są w drzewie roboczym; nie utworzono nowego commitu.
- Build: nie wykonano.
- Instalacja: nie wykonano.
- Publikacja: nie wykonano.
