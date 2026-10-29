# I18N-001 — wielojęzyczny interfejs wxPython

Status: **Poprawka po odbiorze wydana w AMC Test `0.1.0-alpha.444` — wspólna
warstwa, polski, angielski i wybór systemowy,
pełny zinwentaryzowany katalog interfejsu, osobne szablony komunikatów,
parytet menu/pomocy/palety oraz kompletna paczka testowa są zweryfikowane;
poprawka natychmiastowej zmiany języka i mieszanej nazwy listy z 29.10.2026
została zbudowana i opublikowana w AMC Test `0.1.0-alpha.442`. Poprawka
przerwanego przełączenia z angielskiego na polski ma 31 zaliczonych testów i
dwie zaliczone sondy prawdziwego wxPython; zbudowano instalator i opublikowano
wydanie testowe. Lokalnej instalacji nie zmieniono**

Data rozpoczęcia: 28.10.2026.  Zadanie dotyczy wyłącznie bieżącej aplikacji
wxPython w `D:\Projekty Codex\AMC - integracja wxPython`. Wycofane repozytorium
WPF nie było otwierane, przeszukiwane ani modyfikowane.

## Zachowanie użytkowe

- W Ustawieniach na karcie **Ogólne** jest wybór języka: **Zgodny z
  systemem**, **Polski** albo **Angielski**. Ustawienie jest trwałe i po
  zapisaniu Enterem przełącza otwarty interfejs bez ponownego uruchamiania AMC.
- Dla wyboru systemowego polskie ustawienia regionalne wybierają polski, a
  pozostałe obsługiwane przypadki angielski. Obejmuje to rzeczywistą nazwę
  `Polish_Poland`, którą Python zwraca w polskim Windows.
- Karty, wspólne przyciski, etykiety i nazwy dostępności Ustawień, menu,
  pomoc klawiatury, pełna pomoc oraz paleta poleceń korzystają z jednej
  warstwy językowej.
- Nazwa dostępności głównej listy, etykieta sesji i nagłówki kolumn korzystają
  z tego samego aktywnego katalogu. Odświeżenie widoku nie może ponownie
  wstawić polskiego `Ulubione` do interfejsu angielskiego ani odwrotnie.
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
- Zmiana języka nie tłumaczy ani nie nadpisuje wartości pól edycyjnych, w tym
  własnych tekstów komunikatów. Tłumaczone pozostają ich jawne nazwy
  dostępności i opisy.
- Przyciski **Zapisz** i **Anuluj** w Ustawieniach mają osobne, jawne etykiety
  widoczne i nazwy dostępności w obu językach.
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
- Zmiana języka po zapisaniu tłumaczy otwarte kontrolki i nazwy dostępności,
  odświeża komunikaty oraz przebudowuje menu, pomoc i paletę z tego samego
  katalogu. Pozycje list będące tytułami, ścieżkami, stacjami lub nazwami
  urządzeń nie są tłumaczone.
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
- Korekta użytkownika z 29.10.2026 zastępuje wcześniejszą decyzję, że zmiana
  języka wymaga ponownego uruchomienia AMC. Zapis ustawień Enterem ma od razu
  przełączyć istniejący interfejs. Ta sama korekta wymaga, aby opcja zgodna z
  systemem rozpoznawała rzeczywisty polski identyfikator locale Windows
  `Polish_Poland`.
- Późniejsza obserwacja użytkownika z 29.10.2026 ujawniła mieszany interfejs:
  NVDA czytał `Ulubione, lista`, podczas gdy menu było angielskie. Przyczyną
  było ponowne wpisywanie surowej polskiej nazwy dostępności przez
  `_sync_views` po początkowym tłumaczeniu okna. Korekta obejmuje wspólną
  lokalizację nazwy listy, etykiety sesji i nagłówków kolumn, a nie dane
  wierszy użytkownika.
- Kolejne zgłoszenie użytkownika z 29.10.2026 wykazało, że zapis ustawienia
  **Polski** pozostawiał angielskie menu. Przyczyną nie był zapis preferencji:
  podczas przejścia z angielskiego na polski zamknięty dialog Ustawień nadal
  znajdował się przez jedną iterację w drzewie okna. Ogólna lokalizacja
  próbowała wywołać `SetLabel` na polu tekstowym własnego komunikatu, a wx
  przerwał obsługę przed przebudową menu. Korekta rozdziela wartość pola od
  jego nazwy i opisu, omija okna jawnie usuwane i pozwala dojść do przebudowy
  menu. Ta decyzja zastępuje wcześniejsze założenie, że sama ogólna
  lokalizacja drzewa nie może dotknąć wartości pola tekstowego.

## Zmienione źródła

- `wxlite/amc_wx_lite/i18n.py` — wybór języka, katalogi, angielskie nazwy
  poleceń, statyczne teksty interfejsu, bezpieczna lokalizacja kontrolek oraz
  rozdzielenie wartości pól tekstowych od ich nazw dostępności;
- `wxlite/amc_wx_lite/state_store.py` — trwała preferencja języka, migracja i
  osobne szablony komunikatów;
- `wxlite/amc_wx_lite/transport_parity.py` — polskie i angielskie domyślne
  szablony oraz etykiety zdarzeń;
- `wxlite/amc_wx_lite/shortcuts.py`, `menu_model.py`,
  `command_palette.py`, `session_order.py` — jedna prezentacja stabilnych
  poleceń w menu, pomocy i palecie bez zmiany skrótów;
- `wxlite/amc_wx_lite/gui.py` — wybór języka, język szablonów, uruchomienie
  katalogu przed utworzeniem ramki, tłumaczenie nazw dostępności i komunikatów
  oraz jawna widoczna etykieta przycisku **Anuluj**;
- `wxlite/amc_wx_lite/live_region.py`, `playlist_dialog.py`,
  `spotify_playlist_dialog.py`, `problem_report_dialog.py`,
  `radio_schedule_dialogs.py`, `schedule_segments.py` i `radio_recording.py`
  — wspólne komunikaty na żywo, stany wyboru oraz komunikaty playlist,
  harmonogramów i nagrywania;
- `wxlite/amc_wx_lite/locales/en_legacy.json` — kompletny angielski katalog
  zgodności dla istniejących bezpośrednich tekstów wxPython;
- `wxlite/amc_wx_lite/locales/template.json` i `locales/README.md` — szablon
  oraz procedura dodania przyszłego języka; szablon zawiera również bieżące
  robocze teksty wideo, aby test kompletności pozostawał zgodny z katalogiem;
- `wxlite/tools/export_translation_template.py` — deterministyczny eksport
  pełnej bieżącej listy stabilnych poleceń do szablonu;
- `wxlite/tools/translation_inventory.py` — inwentaryzacja AST, bezpieczne
  szablony `{argN}`, pamięć podręczna i kontrolowany eksport do katalogu;
- `wxlite/tools/build_bundle.py` — dołączanie katalogów JSON do paczki oraz
  usuwanie nieaktualnych zasobów językowych przy odświeżeniu;
- `wxlite/tests/test_i18n.py` i powiązane testy ustawień — kompletność
  katalogów, migracja, parytet powierzchni poleceń, ochrona danych użytkownika
  oraz rzeczywisty przypadek angielski → polski z zamykanym dialogiem i
  natywną przebudową menu;
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

### Przerwane przełączenie angielski → polski — 29.10.2026

- kompilacja składniowa `i18n.py`, `gui.py`, `test_i18n.py` i
  `test_general_settings_dialog.py`: zaliczona;
- celowane testy bez widocznego interfejsu: **31 zaliczonych, 1 kontrolowanie
  pominięty** w 4,24 s. Pominięta próba wymaga wxPython, którego nie ma w
  systemowym Pythonie;
- tę samą próbę wykonano prywatnym runtime zainstalowanego AMC Test. Prawdziwy
  wxPython potwierdził stan z usterki: zniszczony dialog nadal był dzieckiem
  ramki i nie zgłaszał jeszcze `IsBeingDeleted()`. Przełączenie zachowało
  dokładny tekst `Added to favorites: {item}`, przetłumaczyło jawną nazwę
  dostępności i przebudowało natywne menu na **Pliki**:
  `NATIVE_EN_TO_PL_MENU_OK`;
- osobna ukryta sonda prawdziwego dialogu Ustawień potwierdziła widoczną
  etykietę **Anuluj** i nazwę dostępności **Anuluj ustawienia**:
  `NATIVE_CANCEL_PL_OK`;
- nie otwierano widocznego GUI, nie restartowano działającego AMC, nie
  zmieniano profilu użytkownika i nie uruchamiano pełnej regresji;
- dla tej poprawki nie instalowano żadnej nowej biblioteki.

### Poprawka rozpoznawania Windows i zmiany bez restartu — 29.10.2026

- celowane testy bez interfejsu `test_i18n.py` i
  `test_general_settings_dialog.py`: **30 zaliczonych** w 6,97 s;
- kompilacja składniowa `i18n.py` i `gui.py`: zaliczona;
- sonda w rzeczywistym środowisku Windows: locale `Polish_Poland` rozwiązuje
  się teraz do `pl`;
- test przełącza istniejące drzewo kontrolek z polskiego na angielski i z
  angielskiego na polski, sprawdza komunikat dynamiczny oraz potwierdza, że
  dane pozycji listy nie są zmieniane;
- test kodu Ustawień potwierdza, że przełączenie następuje dopiero po udanym
  zapisie, przed wyborem szablonów komunikatów i przed przebudową menu;
- nie uruchamiano widocznego GUI ani pełnej regresji, zgodnie z zasadą
  nieuciążliwego testowania.
- po zgłoszeniu mieszanego `Ulubione, lista` rozszerzono katalog o stabilne
  klucze list, sesji i widoków oraz ponowiono trzy celowane moduły testowe w
  środowisku z wxPython: **39 zaliczonych** w 5,66 s. Test obejmuje nazwę
  dostępną listy, nagłówki kolumn, zmianę języka po zapisie i ochronę tekstów
  wierszy. Pierwsza próba systemowym Pythonem została przerwana przy zbieraniu,
  ponieważ ten interpreter nie zawiera `wx`; nie była to regresja kodu.

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

Poprawki po ręcznym odbiorze z 29.10.2026 jeszcze nie budowano, nie
instalowano i nie publikowano. Poniższy wynik dotyczy wcześniejszego wydania
warstwy wielojęzycznej.

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

## Publikacja AMC Test alpha.442 — 29.10.2026

- Wydanie przygotowano w czystym commicie
  `2b772d066d0e54188354dfb2e024a76833d14033` po poprawkach `e7f02107` i
  `0c891379`.
- Celowany zestaw języka, Ustawień, dostępnych nazw listy, aktualizatora,
  profili instalatora i bramki publikacji zakończył się wynikiem **76/76**.
  Pierwszy przebieg miał 65 zaliczeń i 11 błędów tworzenia systemowego katalogu
  tymczasowego; po wskazaniu projektowego `TEMP` ten sam zestaw przeszedł w
  całości. Nie była to usterka AMC.
- Końcowa paczka `6b27fa6d` ma profil `test`, `sourceDirty=false`, 2139 plików
  manifestu i zawiera `en_legacy.json` oraz `template.json`. Pełna integralność
  i kontrolowany ukryty start interfejsu oraz hosta zostały zaliczone podczas
  budowy paczki i ponownie przed utworzeniem instalatora.
- Instalator `AMC-Test-2026-10-29-0057.exe` ma 134383471 bajtów i SHA-256
  `f1ebe22f1a69e5c1c8f205ffa8fbeb72d394a3a4b0145363eff6871bb071a6db`.
  Skan sekretów przeszedł; integralność potwierdza Quick App Switcher 0.1.6,
  17920 bajtów, SHA-256
  `16dc660e6b3fece58af8ccb84ccc43824bcb7744e1f18a37ffa629685349a61f`.
- Sucha bramka i publikacja prerelease `test-2026.10.29.0057` zostały
  zaliczone. GitHub potwierdził tag na dokładnym commicie oraz instalator,
  plik integralności i manifest aktualizacji w stanie `uploaded`, z takim
  samym rozmiarem i digestem instalatora.
- Instalatora ani aktualizatora nie uruchamiano. Zainstalowany AMC Test
  pozostał na commicie `9b2f6246`, paczce `908e5dd5`, z 28.10.2026, 20:22.
  Ręczna aktualizacja i odbiór z NVDA pozostają po stronie użytkownika.
- Adres wydania:
  `https://github.com/michalkasperczak/AMC/releases/tag/test-2026.10.29.0057`.

## Znane ograniczenia

- AMC Test `0.1.0-alpha.442` zawierał błąd, który przerywał przełączenie
  z angielskiego na polski przed przebudową menu. Poprawka jest wydana w
  `0.1.0-alpha.444`; odbiór po lokalnej aktualizacji pozostaje do wykonania.

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
> **Zapisz** język otwartego interfejsu zmienia się od razu. Własne teksty na
> karcie **Dostępność i komunikaty** są przechowywane osobno dla polskiego i
> angielskiego. Przełączenie języka nie zmienia treści wpisanych w polach
> własnych komunikatów. Przycisk **Anuluj** ma polską etykietę także wtedy,
> gdy okno zostało otwarte po przełączeniu z angielskiego.

## Projekt wpisu do changelogu

Projekt do korekty i zatwierdzenia użytkownika:

- Przygotowano wspólną warstwę językową AMC z polskim, angielskim i wyborem
  zgodnym z systemem. Menu, pomoc, paleta poleceń, Ustawienia, nazwy
  dostępności i domyślne komunikaty korzystają ze stabilnych poleceń i
  osobnych katalogów. Dotychczasowe własne teksty pozostają polskie, a nowy
  szablon upraszcza dodawanie następnych języków.
- Poprawiono wykrywanie polskiego języka Windows i umożliwiono zmianę języka
  otwartego interfejsu bez restartowania AMC.
- Usunięto mieszanie języków, w którym NVDA czytał polską nazwę listy
  `Ulubione`, gdy menu i pozostały interfejs były angielskie.
- Naprawiono przełączenie z angielskiego na polski, które mogło zatrzymać się
  przed przebudową menu na zamykanym oknie Ustawień. Wartości własnych
  komunikatów pozostają niezmienione, a przycisk **Anuluj** ma jawną polską
  etykietę.

## Wersja i commit

- gałąź: `codex/konfigurowalne-skroty-20261026`;
- poprawka rozpoznawania `Polish_Poland` i natychmiastowej zmiany języka:
  commit `e7f02107` (`fix(i18n): apply Windows language changes immediately`);
  testy źródłowe, build i publikacja zaliczone; instalacji nie wykonano;
- poprawka mieszanych nazw listy i nagłówków po odświeżeniu widoku: commit
  `0c891379` (`fix(i18n): keep list accessibility labels localized`); 39
  celowanych testów zaliczonych, build i publikacja zaliczone; instalacji nie
  wykonano;
- commit wdrożenia wielojęzycznego interfejsu:
  `11f6459d` (`feat(i18n): add Polish and English interface catalogs`);
- stan źródeł po commicie: zapisany na gałęzi wydania AMC Test;
- paczka robocza: `224499f5`, profil `test`, `sourceDirty=true`, 2139 plików
  manifestu; pełna integralność i kontrolowany start zaliczone;
- commit wydania: `9b2f6246f6c24d4cfc21d453b094e4dc2baddec9`;
- wydana paczka: `908e5dd5`, profil `test`, `sourceDirty=false`;
- instalacja: nie wykonano;
- publikacja: `test-2026.10.28.2022`, wykonana i odczytowo zweryfikowana;
- najnowszy commit wydania: `2b772d066d0e54188354dfb2e024a76833d14033`;
- najnowsza wydana paczka: `6b27fa6d`, profil `test`, `sourceDirty=false`;
- najnowszy instalator: `AMC-Test-2026-10-29-0057.exe`, SHA-256
  `f1ebe22f1a69e5c1c8f205ffa8fbeb72d394a3a4b0145363eff6871bb071a6db`;
- najnowsza publikacja: `test-2026.10.29.0057`, wykonana i odczytowo
  zweryfikowana;
- adres: `https://github.com/michalkasperczak/AMC/releases/tag/test-2026.10.29.0057`.
- poprawka po ręcznym odbiorze: zapisana w roboczym drzewie tej samej gałęzi;
  **31/31** testów celowanych i dwie sondy prawdziwego wxPython zaliczone;
  bez nowego commitu, builda, instalacji i publikacji, ponieważ repozytorium
  zawiera również istniejące, niescommitowane prace innych zadań.

Korekta stanu z 29.10.2026: powyższy wpis opisuje etap przed wspólnym wydaniem.
Poprawka trafiła do commitu `3e6e7303e8a6f12daaa9d47b219ea5d12da3ab46`
razem z funkcją filmów Facebooka i Instagrama. Paczka `5ce8af5d` przeszła
kontrolę integralności i cichy start, instalator
`AMC-Test-2026-10-29-1243.exe` został zbudowany, a prerelease
`test-2026.10.29.1243` opublikowany i odczytowo zweryfikowany. Lokalnej
instalacji i odbioru NVDA nie wykonano. Adres wydania:
`https://github.com/michalkasperczak/AMC/releases/tag/test-2026.10.29.1243`.
