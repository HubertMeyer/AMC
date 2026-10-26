# SET-001 — audyt Ustawień, NVDA i integracja z Windows

Status: **W trakcie — kod priorytetów 1–3 i testy celowane zweryfikowane
27.10.2026; brak nowej paczki, instalacji i ręcznego odbioru NVDA**

## Zgłoszenie użytkownika

26 października 2026 r. użytkownik wskazał dwie luki w oknie **Ustawienia**:

- na kartach dotyczących Podcastów oraz nagrywania Tab przechodzi od razu do
  przycisku **Wybierz**, chociaż wcześniej NVDA powinien odczytać nazwę pola i
  bieżącą ścieżkę domyślnego folderu;
- ustawienia aplikacji nie pokazują integracji dodanej w instalatorze, w tym
  poleceń Eksploratora Windows, wpisu **Otwórz za pomocą** i wyboru typów
  plików.

Ta decyzja rozszerza wcześniejszy zakres AMC14. Integracja nie ma być
jednorazowym, niewidocznym wyborem instalatora: bieżący stan powinien być
czytelny i odwracalny również z Ustawień AMC.

### Korekta zakresu użytkownika — 27.10.2026

Użytkownik zaakceptował dodanie rekomendowanej karty **Aktualizacje** oraz
zmianę nazwy karty **Komunikaty** na **Dostępność i komunikaty**. Ta decyzja
zastępuje wcześniejsze ustalenie z pierwszego etapu realizacji, według którego
priorytet 3 miał pozostać jedynie rekomendacją do osobnego zadania. Publikacja
na GitHubie i instalator mają powstać dopiero po zakończeniu równoległej pracy.

## Wynik audytu

### 1. Potwierdzona przyczyna pomijania ścieżek przez Tab

Oba pola ścieżek są natywnymi `wx.TextCtrl` utworzonymi ze stylem
`wx.TE_READONLY`:

- `recording_folder` — **Domyślny folder nagrywania radia**;
- `podcast_folder` — **Domyślny folder pobierania podcastów**.

Pola mają jawne, użytkowe nazwy dostępności i pokazują wartość ścieżki. Test
na runtime bieżącej instalacji (`wxPython 4.3.1`, `wxWidgets 3.3.3`) wykazał
jednak:

- `AcceptsFocus=True`;
- `CanAcceptFocus=True`;
- `AcceptsFocusFromKeyboard=False`.

Wyjaśnia to całe zgłoszone zachowanie: pole może dostać fokus myszą albo przez
`SetFocus()` po wyborze folderu, lecz natywna nawigacja Tab je pomija. Obecny
test `test_general_settings_dialog.py` sprawdza jedynie istnienie nazw w
źródle. Nie uruchamia prawdziwej nawigacji i nie wykrywa tej regresji.

### 2. Nazwy i wartości pozostałych kontrolek

Statyczny przegląd bieżącego `GeneralPlaybackOptionsDialog` wykazał 51
przechowywanych kontrolek interaktywnych, w tym notebook. Każda z nich ma
jawne `SetName(...)`. Pola wyboru otrzymują użytkowe napisy oddzielone od
wewnętrznych wartości modelu, więc nie znaleziono wycieku reprezentacji
obiektu, nazwy enuma ani identyfikatora komendy.

Pozostały trzy problemy jakościowe:

1. Standardowy przycisk **Anuluj** polega na etykiecie tworzonej przez
   wxWidgets i nie ma własnej, stabilnej nazwy **Anuluj ustawienia**.
2. Opcje algorytmu tempa mówią **Mowa – Speedy**, **Muzyka – Signalsmith** i
   **Dotychczasowy – SoundTouch**. `Speedy`, `Signalsmith` oraz `SoundTouch`
   są nazwami implementacji. W zwykłej mowie powinny pozostać etykiety skutku,
   na przykład **Najlepsza czytelność mowy**, **Najlepsza jakość muzyki** i
   **Tryb zgodności**; nazwy techniczne mogą trafić do szczegółów.
3. Nazwa **Domyślny folder pobierania podcastów** jest za wąska, ponieważ ten
   sam folder obsługuje również pobierany dźwięk materiałów YouTube. Zalecana
   nazwa: **Domyślny folder zapisu pobranych podcastów i dźwięku YouTube**.

### 3. Integracja z Windows istnieje, ale nie jest widoczna w Ustawieniach

Źródło instalatora ma dwie dobrowolne opcje:

- polecenia **Otwórz w AMC Test** i **Dodaj do kolejki AMC Test** w menu
  kontekstowym obsługiwanych plików;
- obecność AMC Test na liście **Otwórz za pomocą** i w ustawieniach aplikacji
  domyślnych Windows.

Odczyt bieżącego rejestru potwierdził aktywną integrację AMC Test dla 48
rozszerzeń w obu miejscach. Profil publiczny nie ma obecnie takiej rejestracji.
Instalator stosuje jednak wybór do całej listy naraz. Nie udostępnia wyboru
grup ani pojedynczych rozszerzeń, a okno Ustawień nie pokazuje nawet stanu
dwóch głównych opcji.

W Core istnieje już pięć użytkowo nazwanych grup, które powinny stać się
wspólnym modelem instalatora i Ustawień:

- **Muzyka i nagrania**;
- **Rzadsze formaty dźwiękowe**;
- **Filmy i pojemniki wideo**;
- **Playlisty**;
- **Niedokończone nagrania AMC**.

## Zalecany zakres wdrożenia

### Priorytet 1 — naprawa dwóch pól folderów

- oba pola ścieżki muszą być osobnymi przystankami Tab przed przyciskiem
  **Wybierz**;
- NVDA ma podać pełną nazwę pola, bieżącą ścieżkę i stan tylko do odczytu;
- po **Wybierz**, anulowaniu systemowego dialogu, użyciu folderu domyślnego,
  Zapisz i Anuluj fokus ma wracać do przewidywalnego miejsca;
- test ma używać rzeczywistej kontrolki wx, a nie wyszukiwać napis w źródle.

Oczekiwana kolejność na karcie Podcasty i YouTube:

1. **Domyślny folder zapisu pobranych podcastów i dźwięku YouTube**, ścieżka;
2. **Wybierz domyślny folder zapisu**;
3. **Użyj domyślnego folderu AMC**.

Analogiczna kolejność obowiązuje na karcie Radio i nagrywanie.

### Priorytet 2 — karta Integracja z Windows

Nowa karta **Integracja z Windows** powinna zawierać:

- **Pokaż polecenia Otwórz w AMC Test i Dodaj do kolejki AMC Test w menu
  kontekstowym**;
- **Pokaż AMC Test na liście Otwórz za pomocą i w ustawieniach aplikacji
  domyślnych Windows**;
- pięć pól wyboru grup typów plików z listą rozszerzeń w pomocy dostępności;
- **Otwórz ustawienia aplikacji domyślnych Windows**;
- nazwany region stanu informujący, czy zapis zastosowano i ilu typów plików
  dotyczy.

Etykieta grup nie może mówić **Odtwarzaj te rozszerzenia**, ponieważ wyłączenie
integracji nie odbiera AMC możliwości ręcznego otwarcia pliku. Powinna mówić
**Udostępniaj AMC dla następujących typów plików**.

Ustawienia i instalator muszą korzystać z jednego modelu wyboru. Aktualizacja
instalatora nie może przywracać starego zestawu po zmianie wykonanej w
aplikacji. AMC Test i AMC Public zachowują osobne nazwy oraz wpisy rejestru.

### Priorytet 3 — karta Aktualizacje

Bieżący host respektuje odziedziczone ustawienia automatycznego sprawdzania i
pobierania składników FFmpeg oraz yt-dlp, lecz AMC Python nie pozwala ich
odczytać ani zmienić. Warto dodać kartę **Aktualizacje** z:

- automatycznym sprawdzaniem składników;
- automatycznym pobieraniem zweryfikowanych składników;
- przyciskiem ręcznego sprawdzenia;
- czytelnym stanem FFmpeg i yt-dlp.

Kanał `test` albo `stable` wynika z profilu wydania i powinien być pokazany
informacyjnie, a nie jako pozornie edytowalny wybór.

## Realizacja 27.10.2026

Zrealizowano priorytety 1–3 oraz korekty nazw znalezione podczas audytu:

- dodano wspólną kontrolkę `FocusableReadOnlyTextCtrl`, która pozostaje tylko
  do odczytu, ale jest prawdziwym przystankiem Tab;
- pola Radia oraz Podcastów i YouTube pokazują rzeczywiste ścieżki domyślne
  zwracane przez host, a nie ogólny tekst zastępczy;
- etykieta pola oraz nazwy obu przycisków Podcastów mówią konsekwentnie o
  podcastach i dźwięku YouTube;
- przycisk anulowania ma stabilną nazwę **Anuluj ustawienia**, a trzy sposoby
  zmiany tempa mają nazwy opisujące skutek zamiast nazw bibliotek;
- dodano kartę **Integracja z Windows** z dwoma niezależnymi przełącznikami,
  pięcioma grupami typów plików, dostępną pomocą z rozszerzeniami, stanem oraz
  przyciskiem otwierającym ustawienia aplikacji domyślnych Windows;
- AMC Test i AMC Public używają oddzielnych nazw klas, poleceń, możliwości i
  trwałych ustawień w rejestrze bieżącego użytkownika;
- zapis z aplikacji przyjmuje tylko pięć znanych identyfikatorów grup; klient
  nie może przekazać dowolnego rozszerzenia, klucza rejestru ani polecenia;
- instalator zachowuje wybór zapisany później przez aplikację i podczas
  aktualizacji nie przywraca automatycznie wszystkich 48 rozszerzeń;
- współbieżnie rozwijana karta **Klawiatura** z zadania KEY-001 używa tej samej
  dostępnej kontrolki tylko do odczytu dla pola nowego skrótu.
- dodano kartę **Aktualizacje** z informacyjnym kanałem wydania, dwoma
  przełącznikami automatyki, osobnymi polami stanu FFmpeg i yt-dlp oraz
  przyciskiem ręcznego sprawdzenia;
- karta nie tworzy drugiej implementacji aktualizacji: przycisk wywołuje to
  samo polecenie **Sprawdź, pobierz i zweryfikuj składniki FFmpeg i yt-dlp**,
  które jest w menu Narzędzia, palecie poleceń i pomocy;
- oba wybory automatyki są prywatnymi ustawieniami AMC Python. Do hosta trafiają
  jako wąskie opcjonalne wartości; brak wyboru nadal dziedziczy dotychczasową
  politykę profilu, a stary wspólny `state.json` nie jest zapisywany;
- karta **Komunikaty** otrzymała nazwę **Dostępność i komunikaty** bez zmiany
  działania istniejących przełączników i szablonów.

Ponowny audyt statyczny wykazał 65 przechowywanych kontrolek interaktywnych
tego okna. Wszystkie 65 mają jawne `SetName(...)`; dynamiczne pola grup
integracji również dostają nazwę użytkową i pomoc. Nie znaleziono nazwy enuma,
identyfikatora komendy, reprezentacji obiektu ani nazwy klasy wystawionej jako
zwykła etykieta kontrolki.

Wcześniejszy zapis, że priorytet 3 pozostaje rekomendacją, został zastąpiony
decyzją użytkownika z 27.10.2026. Karta ma pełny model stanu i testy, ale nie
weszła jeszcze do zbudowanego instalatora ani zainstalowanej aplikacji.

### Pliki zmienione w zakresie SET-001

- `wxlite/amc_wx_lite/accessible_controls.py` — kontrolka tylko do odczytu,
  osiągalna klawiaturą;
- `wxlite/amc_wx_lite/gui.py` — pola folderów, nazwy, karta integracji i
  obsługa zapisu; ten plik zawiera też równoległą pracę KEY-001, której nie
  należy przypisywać wyłącznie temu zadaniu;
- `wxlite/amc_wx_lite/host_client.py` — wąskie operacje integracji, stanu
  składników i uruchamiania wspólnego aktualizatora;
- `wxlite/amc_wx_lite/state_store.py` — prywatne, opcjonalne wybory automatyki
  aktualizacji składników;
- `src/AccessibleMediaController.LiteHost/LiteComponentUpdateCoordinator.cs`
  i `Protocol/LiteComponentUpdatePolicy.cs` — stan użytkowy oraz bezpieczne
  nadpisania polityki dla bieżącego wywołania;
- `tests/AccessibleMediaController.LiteHost.ProtocolTests/ComponentUpdatePolicyTests.cs`
  i `wxlite/tests/test_component_updates.py` — dziedziczenie, nadpisania,
  klient protokołu, wspólne wykonanie i callback karty;
- `src/AccessibleMediaController.Core/ShellIntegration/ShellIntegrationRules.cs`
  — stabilne identyfikatory grup i tożsamości profili Test/Public;
- `src/AccessibleMediaController.LiteHost/LiteGeneralSettingsCoordinator.cs`
  oraz `LiteShellIntegrationCoordinator.cs` — odczyt folderów i integracja
  bieżącego profilu;
- `src/AccessibleMediaController.LiteHost/Program.cs` — rejestracja operacji;
- `installer/AMC_Wx_Setup.iss` — zachowanie wyboru zarządzanego przez
  aplikację;
- `wxlite/tests/test_general_settings_dialog.py`,
  `test_focusable_readonly_text_ctrl_native.py`,
  `test_shell_integration_host_client.py` oraz
  `tests/AccessibleMediaController.Core.SmokeTests/InstallerOfflineContractTests.cs`
  — testy kontraktowe i natywny test fokusu.

Niezwiązane z tą kartą fragmenty `shortcuts.py`, `menu_model.py`,
`state_store.py` i innych plików KEY-001 widoczne równocześnie w drzewie
roboczym należą do osobnego zadania i zostały zachowane bez cofania.

## Materiał do dokumentacji użytkownika

Projekt tekstu po instalacji i ręcznym odbiorze:

> Na kartach **Radio i nagrywanie** oraz **Podcasty i YouTube** Tab najpierw
> przechodzi do pola z bieżącą ścieżką, a dopiero potem do przycisku
> **Wybierz**. Pole jest tylko do odczytu i nie pozwala przypadkowo zmienić
> ścieżki podczas pisania.
>
> Karta **Integracja z Windows** pokazuje, czy AMC jest dostępny w menu
> kontekstowym i na liście **Otwórz za pomocą**. Można osobno wybrać grupy
> plików audio, wideo, playlist i niedokończonych nagrań. Nie ustawia to AMC
> jako programu domyślnego bez decyzji użytkownika.
>
> Karta **Aktualizacje** podaje kanał bieżącego wydania, ustawienia
> automatycznego sprawdzania i pobierania oraz stan FFmpeg i yt-dlp. Pola
> kanału i stanu są tylko do odczytu, ale Tab zatrzymuje się na nich, aby NVDA
> podał nazwę i wartość. Przycisk ręcznego sprawdzenia wykonuje to samo
> polecenie co menu Narzędzia i paleta poleceń.
>
> Dotychczasowa karta **Komunikaty** nazywa się teraz **Dostępność i
> komunikaty**, aby jej nazwa obejmowała także szczegółowe podpowiedzi
> klawiatury i pozostałe opcje dla czytnika ekranu.

## Uzasadnienie i decyzje

- Pole ścieżki pozostaje tylko do odczytu; poprawiamy możliwość osiągnięcia go
  klawiaturą, a nie zmieniamy go w edytowalne pole podatne na przypadkowe
  nadpisanie.
- Pięć grup jest dostępniejsze niż 48 kolejnych pól wyboru. Dokładne
  rozszerzenia pozostają w pomocy każdej grupy. Ewentualny wybór pojedynczych
  rozszerzeń może być osobnym przyciskiem **Dostosuj rozszerzenia**.
- Stan rzeczywisty należy odczytywać z wpisów danego profilu w Windows, a
  trwały zamiar przechowywać we wspólnym modelu używanym przez instalator i
  aplikację.
- Konta, urządzenia i Foldery Biblioteki pozostają pod kontekstowym
  **Konfiguruj**, czyli `Ctrl+F5`; nie należy dublować wieloetapowych menedżerów
  w Ustawieniach ogólnych.
- Kanał aktualizacji programu wynika z wariantu instalacji. Jest polem
  informacyjnym **Testowy — wydania wstępne AMC Test** albo **Stabilny —
  publiczne wydania AMC**, a nie pozornie edytowalnym wyborem.
- Oba przełączniki automatyki pozostają dostępne w kolejności Tab również wtedy,
  gdy automatyczne sprawdzanie jest wyłączone. Drugi wybór może dzięki temu
  zostać przygotowany wcześniej; jego pomoc wyjaśnia, że działa dopiero przy
  automatycznym sprawdzaniu.

## Testy i wynik

Audyt początkowy 26.10.2026:

- porównano ówczesne źródło `gui.py` z plikiem zainstalowanym w
  `D:\Projekty Codex\AMC Python`; SHA-256 był identyczny;
- runtime: Python 3.14, wxPython 4.3.1, wxWidgets 3.3.3;
- zwykła kontrolka `wx.TextCtrl(..., style=wx.TE_READONLY)` zwróciła
  `AcceptsFocusFromKeyboard=False`, co potwierdziło przyczynę;
- bezpośredni odczyt rejestru wykazał wtedy 48 rozszerzeń AMC Test w
  **Otwórz za pomocą** i 48 w menu kontekstowym.

Weryfikacja wdrożenia 27.10.2026:

- rzeczywisty test wxPython potwierdził kolejność: przycisk przed polem,
  pole ścieżki tylko do odczytu, przycisk **Wybierz**; pole zwraca
  `IsEditable=False` i `AcceptsFocusFromKeyboard=True`;
- kontrola składni trzech zmienionych modułów Pythona: zaliczona;
- 58 celowanych testów ustawień, klienta hosta, natywnej kontrolki wx oraz
  skrótów klawiaturowych: **58 zaliczonych, 0 pominiętych, 0 błędów**;
- kompilacja `AccessibleMediaController.LiteHost` Debug: **0 ostrzeżeń,
  0 błędów**;
- test `--installer-offline`: zaliczony; potwierdza opcjonalną i odwracalną
  integrację w skrypcie, ale nie jest dowodem instalacji;
- samowystarczalna paczka Test v2 została zbudowana w
  `D:\Projekty Codex\AMC - integracja wxPython\.test-output\SET-001-settings-accessibility-20261027-v2`;
- manifest v2: `installId=AMC.Test.win-x64`, 2136 wpisów plików,
  `sourceRevision=73279fbb15a1cd34c6813f24e097e0467889a197`,
  `sourceDirty=true`;
- pełna kontrola integralności paczki: zaliczona;
- kontrolowany start interfejsu i hosta z paczki: zaliczony;
- host paczki zwrócił rzeczywiste foldery
  `C:\Users\micha\Music\AMC — Nagrania radia` i
  `C:\Users\micha\Music\AMC — Pobrane podcasty`, dostępność profilu
  **AMC Test** oraz wszystkie pięć grup użytkowych;
- podczas tej weryfikacji wywołano tylko operacje odczytowe stanu. Nie
  zastosowano integracji, nie otwarto Ustawień Windows i nie zmieniono
  rejestru.

Weryfikacja rozszerzenia o karty 27.10.2026:

- rzeczywisty test wxPython otworzył całe okno Ustawień i potwierdził kolejność
  Tab na karcie Aktualizacje: **Kanał aktualizacji programu**, automatyczne
  sprawdzanie, automatyczne pobieranie, **Stan składnika FFmpeg**;
- oba pola stanu oraz kanał używają `FocusableReadOnlyTextCtrl`, zachowują
  wartość tylko do odczytu i mają jawne nazwy dostępności;
- cztery bezpośrednio związane moduły testowe: **77 zaliczonych, 0 błędów**;
- szersza regresja ustawień, startu, opcji sesji, pomocy/transportu i klienta
  hosta: **172 zaliczone, 0 błędów**;
- zestaw C# `--component-updates`: zaliczony;
- kompilacja `AccessibleMediaController.LiteHost` Debug: **0 ostrzeżeń,
  0 błędów**;
- `git diff --check` dla zmienionych plików nie wykazał błędów białych znaków;
- nie zbudowano nowej paczki ani instalatora i nie uruchomiono publikacji,
  zgodnie z decyzją o oczekiwaniu na zakończenie równoległego zadania.

Najważniejsze użyte polecenia i wejścia kontrolne:

- `uv run --no-project --python 3.14 --with pytest --with wxpython python -B
  -m pytest ... -q -p no:cacheprovider` dla 77 testów bezpośrednich i 172
  testów szerszej regresji;
- `dotnet run --project
  tests\AccessibleMediaController.LiteHost.ProtocolTests\AccessibleMediaController.LiteHost.ProtocolTests.csproj
  --configuration Debug --no-restore -- --component-updates`;
- `dotnet build src\AccessibleMediaController.LiteHost\AccessibleMediaController.LiteHost.csproj --no-restore --configuration Debug`;
- bezpośredni runner czterech modułów testowych z prywatnego runtime Python,
  ponieważ `pytest` nie jest w nim zainstalowany;
- `dotnet run --project tests\AccessibleMediaController.Core.SmokeTests\AccessibleMediaController.Core.SmokeTests.csproj --configuration Debug --no-restore -- --installer-offline`;
- `wxlite\tools\Build-AMCBundle.ps1 -Profile test` z prywatnym runtime
  bieżącej instalacji oraz wyjściem do katalogu paczki v2;
- operacje protokołu hosta `settings.defaults` i
  `shellIntegration.status` z paczki v2.

## Znane ograniczenia

- Nie wykonano instalacji ani ręcznej próby całego poprawionego okna z NVDA.
  Odbiór musi objąć Tab, Shift+Tab, zmianę kart, strzałki w polach wyboru,
  Zapisz, Anuluj, powrót fokusu oraz ponowne otwarcie.
- Natywny test wx dowodzi rzeczywistego fokusu klawiatury, ale nie zastępuje
  odsłuchu dokładnej wypowiedzi NVDA na komputerze użytkownika.
- Nie zastosowano wpisów integracji z paczki roboczej, aby audyt nie zmieniał
  rejestru. Ścieżka zapisu jest skompilowana i objęta testami kontraktowymi,
  lecz wymaga odbioru po bezpiecznej instalacji AMC Test.
- `ISCC.exe` nie jest dostępny na tym komputerze, dlatego nie skompilowano
  instalatora Inno Setup. Zbudowano i sprawdzono samowystarczalną paczkę, nie
  instalator.
- Prywatny runtime bieżącej instalacji nie zawiera `pytest`; w pierwszym
  etapie uruchomiono więc 58 testów bezpośrednio. Rozszerzenie kart sprawdzono
  później w przypiętym środowisku `uv` z pytest i wxPython. Pełna regresja
  całego projektu nadal pozostaje wymagana przed promocją instalacji.
- Samo zgłoszenie rozszerzenia w Windows nie dowodzi, że każdy z 48 formatów
  faktycznie dekoduje się na danej instalacji.
- Paczka testowa SET-001 v2 powstała przed dodaniem karty **Aktualizacje** i
  nowej nazwy **Dostępność i komunikaty**. Nie wolno przedstawiać jej jako
  artefaktu zawierającego ten końcowy etap; potrzebny będzie wspólny build po
  zakończeniu równoległego zadania.

## Wersja i commit

- Zainstalowana aplikacja pozostaje AMC Test z commitu
  `4c8fceda738afd0163040a400150007d16f8409c`, pakiet `faef4e7f`, zainstalowany
  26.10.2026 o 14:03.
- Wcześniejsza paczka robocza v2 bazuje na HEAD `73279fbb`; manifest ma świadomie
  `sourceDirty=true`, ponieważ zmiany nie zostały jeszcze zacommitowane.
- Źródła końcowego etapu kart: zmienione. Testy i build LiteHosta: zaliczone.
  Nowy bundle i instalator: niewykonane. Instalacja: niewykonana. Publikacja i
  wydanie: niewykonane.
- Commit realizacji: jeszcze nie utworzony.
