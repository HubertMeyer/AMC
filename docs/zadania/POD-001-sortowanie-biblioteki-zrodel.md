# POD-001 — sortowanie Biblioteki podcastów i kanałów

## Status

Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA.

## Stan obecny

Zbiorcza Biblioteka podcastów, kanałów YouTube, playlist YouTube i pozycji
`Media internetowe` jest czytana według trwałego pola `ordinal`. Jest to
kolejność własna odziedziczona z bazy, a nie porządek alfabetyczny ani według
daty dodania. Menu sortowania `Alt+1`, `Alt+2`, `Alt+3` działa obecnie tylko w
Skrzynce podcastów, nie na głównej liście źródeł.

## Cel

Dać użytkownikowi jawny wybór porządku głównej Biblioteki bez zmiany danych
współdzielonego profilu przez interfejs Python.

## Wstępna propozycja

- `Alt+1` — ostatnio dodane na początku;
- `Alt+2` — alfabetycznie;
- `Alt+3` — kolejność własna z bazy;
- wybrany tryb jest zapisany w prywatnych ustawieniach AMC Test;
- zmiana sortowania zachowuje zaznaczenie według stabilnego identyfikatora;
- pomoc `Ctrl+F1`, menu i paleta `Ctrl+Shift+K` opisują te same polecenia;
- tryb alfabetyczny używa polskiego porównania nazw, nie technicznych ID;
- sortowanie nie miesza podcastów, kanałów i `Media internetowe` z odcinkami.

Korekta użytkownika z 2026-10-19 zastępuje wcześniejsze zastrzeżenie, że skróty
i domyślny tryb wymagają potwierdzenia: `Alt+1`, `Alt+2` i `Alt+3` zostały
zatwierdzone do wdrożenia. Domyślnie zachowujemy kolejność własną, aby
aktualizacja nie przestawiła po cichu istniejącej Biblioteki. Zadanie nie jest
częścią poprawki `SEARCH-001` i nie opóźnia widocznego zaznaczenia elementu
właśnie dodanego z wyszukiwarki.

## Kryteria akceptacji

- trzy tryby zwracają przewidywalną kolejność na tej samej bibliotece;
- nowe źródło jest widoczne i zaznaczone po dodaniu w każdym trybie;
- ponowne uruchomienie zachowuje wybór sortowania;
- NVDA mówi nazwę trybu, pozycję elementu i użytkową nazwę źródła;
- testy nie zapisują bezpośrednio do `podcasts.db` z warstwy Python.

## Prace i weryfikacja

- Data rozpoczęcia: 2026-10-19.
- Data zakończenia kodu i testów: 2026-10-19.
- Zmienione pliki: `wxlite/amc_wx_lite/gui.py`, `menu_model.py`,
  `navigation.py`, `podcast_source.py`, `shortcuts.py`, `state_store.py`,
  `wxlite/tests/test_podcast_library_sort.py`,
  `test_menu_exposes_existing_actions.py`, `test_transport_parity.py`.
- Commit kodu: `b3768226` (`feat(pod-001): dodaj sortowanie biblioteki
  zrodel`).
- Zainstalowana kompilacja:
  `2026.10.19-d42d8d82cd76f4b19088e8962b69adca2e4547a9-86754006`.

## Materiał do dokumentacji użytkownika

Na głównej liście `Biblioteka` w sesji `Podcasty i YouTube` można wybrać sposób
ułożenia źródeł:

- `Alt+1` — ostatnio dodane na początku;
- `Alt+2` — alfabetycznie według polskich nazw;
- `Alt+3` — kolejność własna zapisana w Bibliotece.

Zmiana sortowania pozostawia zaznaczenie na tym samym podcaście, kanale
YouTube albo pozycji `Media internetowe`. NVDA mówi nazwę wybranego trybu,
nazwę źródła i jego pozycję, na przykład `Alfabetycznie. Żuraw, 3 z 3`.
Wybrany tryb jest pamiętany prywatnie przez AMC Test. Przy pierwszym
uruchomieniu po aktualizacji program zachowuje dotychczasową kolejność własną.

Te same trzy polecenia pojawiają się w menu, pomocy bieżącego miejsca pod
`Ctrl+F1`, pełnej pomocy klawiatury i palecie poleceń `Ctrl+Shift+K` tylko
wtedy, gdy otwarta jest główna Biblioteka. W Skrzynce podcastów `Alt+1–3`
nadal steruje jej osobnym sortowaniem. W pozostałych widokach sesji skróty nie
udają poleceń Biblioteki.

## Uzasadnienie i decyzje

- Kolejność własna pozostaje odczytem trwałego pola porządku z bazy i jest
  domyślna dla istniejącego profilu. Python nie zapisuje sortowania do
  `podcasts.db`.
- `Ostatnio dodane` odwraca kolejność własną, ponieważ nowe źródła są
  dopisywane na jej końcu.
- Sortowanie alfabetyczne korzysta ze wspólnej polskiej kolacji hosta C#.
  Jeżeli host nie może jej dostarczyć, AMC używa deterministycznej kolejności
  zastępczej i uczciwie dopowiada `kolejność zastępcza`.
- Podcast, kanał YouTube i `Media internetowe` zachowują swój użytkowy typ;
  odcinki nie trafiają na listę źródeł. Pole techniczne `ordinal` pozostaje w
  modelu i nie jest wypowiadane przez NVDA.
- Zaznaczenie jest odtwarzane po stabilnym identyfikatorze. Ten sam mechanizm
  pozwala po wyjściu z wyszukiwarki wskazać właśnie dodane źródło niezależnie
  od aktywnego sortowania.
- Pomoc pełna filtruje polecenia przez ten sam bieżący stan menu i model
  możliwości, którego używa paleta poleceń.

## Testy i wynik

- Testy ukierunkowane dla źródła, stanu, skrótów, menu, palety, pomocy i
  fokusu: `165 passed in 3.85s`.
- Poprawiony test parytetu po dodaniu nowego kontekstu skrótów:
  `1 passed in 0.32s`.
- Pełna regresja Python po poprawce: `1777 passed, 110 skipped, 11 subtests
  passed in 86.05s`.
- Test bazy porównuje SHA-256 przed i po trzech sortowaniach; wynik pozostaje
  identyczny. Osobne testy potwierdzają brak źródła ukrytego, właściwe etykiety
  typów, trwałość prywatnego wyboru, odrzucenie technicznej wartości, fokus po
  zmianie kolejności i parytet menu–skrót–pomoc–paleta.
- `git diff --check` zakończył się bez błędów; wystąpiło jedynie informacyjne
  ostrzeżenie Git o przyszłej normalizacji LF do CRLF.
- Przed kompilacją i instalacją bramka bezpieczeństwa sprawdziła 15 jawnych
  katalogów nagrań: 0 aktywnych okien harmonogramów, 0 plików
  `.amc-partial`, 0 plików rosnących i 0 zablokowanych.
- Procedura promocji zbudowała 1660 plików, zweryfikowała manifest i sumy
  SHA-256, zainstalowała paczkę w `D:\Projekty Codex\AMC Python` oraz
  potwierdziła proces i tytuł `AMC Test — 19.10.2026, 04:18`.
- Promocja została uruchomiona z `-SkipTests`, ponieważ pełna regresja Python
  zakończyła się powodzeniem bezpośrednio przed promocją. Potwierdzenie
  instalacji nie jest przedstawiane jako ponowne wykonanie testów.
- Po potwierdzeniu instalacji usunięto wyłącznie odtwarzalny katalog roboczy
  `C:\Users\<użytkownik>\Documents\Codex\2026-10-18\ma\work\pod-001`: 11 plików,
  1 462 589 bajtów (około 1,4 MB). Usunięcie jest bez odzysku z Kosza, ale
  źródła i dokumentacja są w lokalnych commitach, a zainstalowana paczka i
  kandydat odbiorczy pozostały zachowane.

## Znane ograniczenia

- Ręczny odbiór NVDA i klawiatury na rzeczywistej Bibliotece pozostaje do
  wykonania; automaty potwierdzają etykiety i fokus, ale nie zastępują odsłuchu.
- Tryb `Ostatnio dodane` opiera się na kolejności dopisywania `ordinal`, bo
  współdzielona baza nie przechowuje osobnej daty dodania źródła.
- Przy niedostępnej polskiej kolacji hosta program nie przedstawia zastępczego
  porządku jako pełnego sortowania AMC.
- Zadanie nie zmienia ręcznie ustawionej kolejności w bazie i nie dodaje
  interfejsu jej przesuwania.

## Wersja i commit

- Kod i testy: commit `b3768226`.
- Pierwszy zapis dokumentacji: commit `d42d8d82`.
- Kompilacja i instalacja:
  `2026.10.19-d42d8d82cd76f4b19088e8962b69adca2e4547a9-86754006`,
  1660 plików, manifest i SHA-256 zgodne, uruchomienie potwierdzone.
- Publikacja: nie wykonywano; zgodnie z zakresem nocnym nic nie wysłano na
  GitHub.
