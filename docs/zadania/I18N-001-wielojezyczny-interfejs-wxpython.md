# I18N-001 — wielojęzyczny interfejs wxPython

Status: **Zrobione — wspólna warstwa, polski, angielski i wybór systemowy,
pełny zinwentaryzowany katalog interfejsu, osobne szablony komunikatów,
parytet menu/pomocy/palety oraz kompletna paczka testowa są zweryfikowane**

Data rozpoczęcia: 28.10.2026.  Zadanie dotyczy wyłącznie bieżącej aplikacji
wxPython w `D:\Projekty Codex\AMC - integracja wxPython`. Wycofane repozytorium
WPF nie było otwierane, przeszukiwane ani modyfikowane.

## Zachowanie użytkowe

- W Ustawieniach na karcie **Ogólne** jest wybór języka: **Zgodny z
  systemem**, **Polski** albo **Angielski**. Ustawienie jest trwałe i zaczyna
  obowiązywać po zapisaniu oraz następnym uruchomieniu AMC.
- Dla wyboru systemowego polskie ustawienia regionalne wybierają polski, a
  pozostałe obsługiwane przypadki angielski.
- Karty, wspólne przyciski, etykiety i nazwy dostępności Ustawień, menu,
  pomoc klawiatury, pełna pomoc oraz paleta poleceń korzystają z jednej
  warstwy językowej.
- Polecenia nadal są identyfikowane przez stabilne wartości `Action`.
  Tłumaczenie zmienia wyłącznie nazwę i opis dla użytkownika; nie zmienia
  skrótu, routingu, widoczności ani wykonania polecenia.
- Własne teksty komunikatów mają osobny wybór **Polski/Angielski**. Każdy
  język ma własne domyślne szablony i własne nadpisania. Dotychczasowe własne
  teksty z pojedynczego pola są migrowane wyłącznie do polskiego katalogu.
- Neutralna prędkość jest jawnie nazwana `1,00 razy — normalna prędkość` po
  polsku i `1.00x — normal speed` po angielsku; pozostałe wartości mówią
  odpowiednio „wolniej” albo „szybciej”.
- Wartości użytkownika — tytuły, stacje, ścieżki, adresy i nazwy urządzeń —
  nie są automatycznie traktowane jako tekst interfejsu. Statyczne pozycje
  wyboru są tłumaczone tylko po jawnym włączeniu tej operacji dla kontrolki.
- Warstwa zgodności obejmuje 713 unikalnych statycznych napisów i 312
  szablonów komunikatów dynamicznych. Inwentaryzator rozpoznaje 888 wystąpień
  napisów w kontrolkach wxPython i sprawdza je przy każdym teście katalogu.

## Komunikaty czytnika ekranu

Przykłady domyślnych tekstów:

- polski: `Dodano do ulubionych: {item}`;
- angielski: `Added to favorites: {item}`;
- polski: `1,00 razy — normalna prędkość`;
- angielski: `1.00x — normal speed`.

Nazwy techniczne, takie jak `Action`, identyfikator zdarzenia, nazwa klasy lub
reprezentacja obiektu, nie są używane jako zapasowa nazwa dostępności. Gdy
polecenie nie ma ręcznego angielskiego wariantu, zapasowa nazwa powstaje z
kontrolowanego słownika słów użytkowych, a test zabrania ujawnienia
identyfikatora polecenia.

## Różnice między trybami i migracja

- `system` jest zapisywaną preferencją, a `pl` lub `en` jest konkretnym
  językiem wybranym dla danego uruchomienia.
- Zmiana języka w otwartym oknie Ustawień nie wykonuje częściowej podmiany
  działającego interfejsu. Zapis utrwala wybór, a pełny katalog jest stosowany
  przy następnym starcie.
- Brak nowego pola w starym profilu oznacza `system`.
- Stare `message_templates` jest przy odczycie przenoszone do
  `message_templates_by_language.pl`; angielski zachowuje własne wartości
  domyślne.
- Profil `test` i przyszły `public` korzystają z tego samego katalogu poleceń;
  istniejące filtry możliwości nadal decydują, które polecenia są widoczne.

## Uzasadnienie i decyzje

- Wprowadzono jedną warstwę `i18n.py` zamiast osobnych tabel dla menu, pomocy,
  palety i dostępności.
- Stabilne klucze są źródłem dla nowych elementów interfejsu, poleceń i
  komunikatów. Istniejące polskie napisy zachowano jako polski katalog oraz
  warstwę zgodności, aby nie przepisywać zachowania kontrolek w jednym ryzykownym
  kroku.
- Własne szablony są rozdzielone według języka, ponieważ polski tekst nie może
  nadpisywać angielskiego komunikatu po zmianie interfejsu.
- Nie zmieniono mapowania ani mechaniki skrótów. Korekta użytkownika z
  28.10.2026 zastępuje wcześniejsze oczekiwanie na odbiór KEY-001: użytkownik
  zatwierdził skróty i obsługę klawiatury jako gotowe.
- Ogólna lokalizacja drzewa okna nie zmienia pozycji list będących danymi
  użytkownika. To chroni NVDA przed odczytaniem zmienionego tytułu, stacji,
  ścieżki lub nazwy urządzenia.
- 28.10.2026 użytkownik zezwolił na przekazanie do Google Translate wyłącznie
  statycznych napisów interfejsu zapisanych w źródłach. Zgoda nie obejmowała
  i narzędzie nie wysyłało danych profilu, kont, ścieżek, tytułów, stacji,
  urządzeń ani innych wartości powstających podczas działania AMC.
- Korekta użytkownika z 28.10.2026 rozstrzyga dwuznaczność terminologiczną:
  **karta** interfejsu Ustawień to po angielsku `tab`, natomiast **zakładka**
  oznaczająca zapisane miejsce w materiale lub pliku to `bookmark`. Korekta
  zastępuje każde wcześniejsze ogólne utożsamienie słowa „zakładka” z kartą
  interfejsu; test katalogu pilnuje rozdzielenia obu znaczeń.

## Zmienione źródła

- `wxlite/amc_wx_lite/i18n.py` — wybór języka, katalogi, angielskie nazwy
  poleceń, statyczne teksty interfejsu i bezpieczna lokalizacja kontrolek;
- `wxlite/amc_wx_lite/state_store.py` — trwała preferencja języka, migracja i
  osobne szablony komunikatów;
- `wxlite/amc_wx_lite/transport_parity.py` — polskie i angielskie domyślne
  szablony oraz etykiety zdarzeń;
- `wxlite/amc_wx_lite/shortcuts.py`, `menu_model.py`,
  `command_palette.py`, `session_order.py` — jedna prezentacja stabilnych
  poleceń w menu, pomocy i palecie bez zmiany skrótów;
- `wxlite/amc_wx_lite/gui.py` — wybór języka, język szablonów, uruchomienie
  katalogu przed utworzeniem ramki oraz tłumaczenie nazw dostępności i
  komunikatów;
- `wxlite/amc_wx_lite/live_region.py`, `playlist_dialog.py`,
  `spotify_playlist_dialog.py`, `problem_report_dialog.py`,
  `radio_schedule_dialogs.py`, `schedule_segments.py` i `radio_recording.py`
  — wspólne komunikaty na żywo, stany wyboru oraz komunikaty playlist,
  harmonogramów i nagrywania;
- `wxlite/amc_wx_lite/locales/en_legacy.json` — kompletny angielski katalog
  zgodności dla istniejących bezpośrednich tekstów wxPython;
- `wxlite/amc_wx_lite/locales/template.json` i `locales/README.md` — szablon
  oraz procedura dodania przyszłego języka;
- `wxlite/tools/export_translation_template.py` — deterministyczny eksport
  pełnej bieżącej listy stabilnych poleceń do szablonu;
- `wxlite/tools/translation_inventory.py` — inwentaryzacja AST, bezpieczne
  szablony `{argN}`, pamięć podręczna i kontrolowany eksport do katalogu;
- `wxlite/tools/build_bundle.py` — dołączanie katalogów JSON do paczki oraz
  usuwanie nieaktualnych zasobów językowych przy odświeżeniu;
- `wxlite/tests/test_i18n.py` i powiązane testy ustawień — kompletność
  katalogów, migracja, parytet powierzchni poleceń i ochrona danych
  użytkownika;
- `wxlite/tests/test_bundle_layout.py` — regresja obecności katalogów
  tłumaczeń w samowystarczalnej paczce;
- `wxlite/requirements-test.txt` — przypięte zależności użyte wyłącznie do
  testów źródłowych.

## Zainstalowane zależności testowe

Systemowy Python 3.14 nie miał modułu `pytest`, chociaż osiem istniejących
modułów testowych go importuje. Za zgodą użytkownika wykonano:

```powershell
python -m pip install pytest==9.0.2
```

Zainstalowano globalnie dla tego interpretera: `pytest 9.0.2`, `colorama
0.4.6`, `iniconfig 2.3.1`, `packaging 26.3`, `pluggy 1.7.0` i `Pygments
2.21.0`. Te pakiety nie są kopiowane do prywatnego runtime ani paczki AMC.
Przypięto je w `wxlite/requirements-test.txt`. Bezpieczne cofnięcie samego
narzędzia testowego: `python -m pip uninstall pytest`; współdzielonych
zależności nie należy usuwać automatycznie bez sprawdzenia innych programów.

Do inwentaryzacji pozostałych napisów utworzono odseparowane środowisko
`.test-output\translation-tools` i zainstalowano w nim poleceniem
`python -m pip install deep-translator==1.11.4`: `deep-translator 1.11.4`,
`beautifulsoup4 4.15.0`, `certifi 2026.10.23`, `charset-normalizer 3.5.2`,
`idna 3.20`, `requests 2.34.2`, `soupsieve 3.0.4`, `typing-extensions 4.16.0`
i `urllib3 2.8.0`. Środowisko nie jest częścią runtime ani paczki AMC.
Wywołanie Google przez `deep-translator` zwróciło HTTP 429. Po uzyskaniu wyżej
opisanej zgody użyto zainstalowanego `requests 2.34.2` bezpośrednio z publicznym
punktem `translate.googleapis.com/translate_a/single`. Wysłano wyłącznie
statyczne polskie literały źródłowe z technicznymi markerami placeholderów;
odpowiedzi zapisano w `.test-output\google-translation-cache.json`. Narzędzie
odrzuca odpowiedź, jeśli marker lub zestaw placeholderów został zmieniony.
Wynik został uzupełniony ręcznymi wariantami terminów kontekstowych, między
innymi karta, historia, stan konta, dziennik, tasowanie i gospodarstwo Sonos.
Żaden z tych pakietów nie trafia do runtime ani paczki AMC.

## Testy i wynik

- `py_compile` wszystkich zmienionych modułów, narzędzi katalogu i
  `build_bundle.py`: zaliczone;
- końcowy szeroki zakres lokalizacji, szablonów, menu, pomocy, palety, stanu,
  sesji, kont usług, harmonogramów, nagrywania, skrótów, startu i okablowania
  GUI: **599 zaliczonych, 1 wyłączony** w 22,88 s;
- wyłączona w systemowym Pythonie sonda prawdziwego wxPython została wykonana
  prywatnym runtime AMC: `MODELLESS_OK`;
- końcowa kontrola kompletności katalogu i układu paczki: **43 zaliczone,
  1 wyłączony** w 29,32 s; wyłączony import publicznego profilu został
  wykonany prywatnym runtime: `PUBLIC_IMPORT_OK`;
- test katalogu już wewnątrz gotowej paczki: `PACKAGED_ENGLISH_OK`;
- pełna integralność i kontrolowany, ukryty start interfejsu oraz świeżo
  zbudowanego hosta: zaliczone.

Dwie pierwsze próby pełnej bramki paczki zakończyły się pozornym
`HostError: Silnik przestał odpowiadać`. Zachowany kandydat wykazał, że
przyczyną był systemowy katalog TEMP piaskownicy bez prawa zapisu. Po
ustawieniu `TEMP` i `TMP` na projektowy
`.test-output\i18n-temp` ta sama paczka przeszła kontrolowany start. Nie była
to usterka kodu i18n ani hosta.

## Build

Końcowa samowystarczalna paczka profilu `test` została zbudowana poleceniem
`wxlite\tools\Build-AMCBundle.ps1` z prywatnym runtime bieżącej instalacji.
Pierwszy kandydat po rozszerzeniu katalogu ujawnił brak kopiowania plików JSON;
nie został uznany za wynik. Po dodaniu testu regresji i poprawieniu pakowania
wykonano pełną budowę od zera. Wynik:
Wynik:

- katalog: `D:\Projekty Codex\AMC - integracja wxPython\.test-output\I18N-001-final-20261028-153736`;
- identyfikator paczki: `224499f5`;
- etykieta: `2026.10.28-301c7fcf5c54473bfa1307d3b1c6961b25115ef3-224499f5-robocza`;
- profil: `test`, `sourceDirty=true`;
- manifest: 2139 kontrolowanych plików; katalog zawiera 2210 plików i
  447175891 bajtów;
- SHA-256 `bundle-manifest.json`:
  `57F8EDA012CAF33A82E0D3CAB0EF5FB7BC66AA2E3D296C71C2081D75E5354C83`;
- `en_legacy.json` i `template.json`: obecne na dysku, w manifeście i objęte
  kontrolą integralności;
- pełna kontrola integralności: zaliczona;
- kontrolowany, ukryty start interfejsu i hosta na jednorazowym profilu:
  zaliczony;
- procesy testowej paczki po zakończeniu: brak.

Tego roboczego kandydata nie instalowano, nie uruchamiano jako wydania
użytkowego, nie przekształcano w instalator i nie publikowano.

## Publikacja AMC Test alpha.438 — 28.10.2026

- Zweryfikowany zakres zapisano najpierw w commicie funkcjonalnym `11f6459d`,
  a wydanie przygotowano w czystym commicie
  `9b2f6246f6c24d4cfc21d453b094e4dc2baddec9`.
- Przed wydaniem ponowiono 70 celowanych testów bez interfejsu. Jedyny test
  wymagający wxPython wykonano osobno w środowisku projektowym; również
  zaliczony. Pierwsza próba tego testu w systemowym Pythonie zakończyła się
  wyłącznie brakiem modułu `wx`, a nie błędem AMC.
- Końcowa paczka profilu `test` ma identyfikator `908e5dd5`, `sourceDirty=false`,
  2139 plików manifestu i zawiera `en_legacy.json` oraz `template.json`.
  Pełna integralność i kontrolowany ukryty start interfejsu oraz hosta zostały
  zaliczone.
- Instalator `AMC-Test-2026-10-28-2022.exe` ma 134355952 bajty i SHA-256
  `6e16f2b392e5957365fee856c62778096a23d1fef46a6f0f09fe3bac8ef50c96`.
  Kontrola integralności potwierdziła profil Test, kanał Test, brak sekretów
  oraz Quick App Switcher 0.1.6.
- Wydanie wstępne `test-2026.10.28.2022` zostało opublikowane i odczytowo
  zweryfikowane na GitHubie. Zdalna gałąź, tag i wydanie wskazują commit
  `9b2f6246f6c24d4cfc21d453b094e4dc2baddec9`; GitHub podał zgodny rozmiar i
  SHA-256 instalatora oraz potwierdził oba manifesty.
- Instalatora ani aktualizatora nie uruchamiano. Bieżąca instalacja użytkownika
  nie została zmieniona; ręczna aktualizacja i odbiór z NVDA pozostają po
  stronie użytkownika.

## Znane ograniczenia

- Nie wykonano ręcznego odsłuchu całego angielskiego interfejsu z NVDA.
  Automatyczne testy sprawdzają jawne nazwy, brak technicznych identyfikatorów,
  kompletność Ustawień oraz parytet menu, pomocy i palety, ale nie zastępują
  odsłuchu prawdziwego okna.
- Duży katalog zgodności powstał z tłumaczenia maszynowego i przejrzanych
  poprawek kontekstowych. Jest kompletny technicznie, lecz przed publikacją
  angielskiego wydania warto wykonać pełną korektę językową w prawdziwym GUI.
- Pełna regresja GUI, Sonosa i WiiM nie została uruchomiona, zgodnie z decyzją
  użytkownika z 27.10.2026 wymagającą osobnej zgody na testy otwierające okna,
  przejmujące fokus albo używające urządzeń.
- Ruff nie jest zainstalowany w używanym środowisku; nie przedstawia się lintu
  jako zaliczonego.

## Materiał do dokumentacji użytkownika

Projekt do korekty i zatwierdzenia użytkownika:

> Język AMC można wybrać w **Ustawienia programu**, na karcie **Ogólne**.
> Opcja **Zgodny z systemem** używa polskiego przy polskich ustawieniach
> regionalnych, a w pozostałych przypadkach angielskiego. Po wybraniu
> **Zapisz** uruchom AMC ponownie. Własne teksty na karcie **Dostępność i
> komunikaty** są przechowywane osobno dla polskiego i angielskiego.

## Projekt wpisu do changelogu

Projekt do korekty i zatwierdzenia użytkownika:

- Przygotowano wspólną warstwę językową AMC z polskim, angielskim i wyborem
  zgodnym z systemem. Menu, pomoc, paleta poleceń, Ustawienia, nazwy
  dostępności i domyślne komunikaty korzystają ze stabilnych poleceń i
  osobnych katalogów. Dotychczasowe własne teksty pozostają polskie, a nowy
  szablon upraszcza dodawanie następnych języków.

## Wersja i commit

- gałąź: `codex/konfigurowalne-skroty-20261026`;
- commit wdrożenia wielojęzycznego interfejsu:
  `11f6459d` (`feat(i18n): add Polish and English interface catalogs`);
- stan źródeł po commicie: zapisany na gałęzi wydania AMC Test;
- paczka robocza: `224499f5`, profil `test`, `sourceDirty=true`, 2139 plików
  manifestu; pełna integralność i kontrolowany start zaliczone;
- commit wydania: `9b2f6246f6c24d4cfc21d453b094e4dc2baddec9`;
- wydana paczka: `908e5dd5`, profil `test`, `sourceDirty=false`;
- instalacja: nie wykonano;
- publikacja: `test-2026.10.28.2022`, wykonana i odczytowo zweryfikowana;
- adres: `https://github.com/michalkasperczak/AMC/releases/tag/test-2026.10.28.2022`.
