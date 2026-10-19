# AMC14 — foldery i integracja z powłoką Windows

Status: **W trakcie**

Źródło zatwierdzonego zakresu:
`D:\Projekty Codex\Accessible Multimedia Controller\AMC14_FOLDERY_I_INTEGRACJA_POWLOKI_2026-10-18.md`.
Historyczny projekt służy wyłącznie jako materiał do odczytu. Wdrożenie jest
prowadzone w bieżącym AMC Test.

## Zakres

- aplikacyjne polecenie otwarcia folderu lokalnego elementu i zaznaczenia
  istniejącego pliku;
- odbieranie pliku przekazanego przy uruchomieniu oraz bezpieczne przekazanie
  go do już działającej instancji tego samego profilu;
- jawne dodawanie pliku do kolejki przez parametr `/kolejka`, bez usuwania
  istniejącej pozycji;
- całkowite rozdzielenie kanałów AMC Test i publicznego AMC;
- dopiero po odbiorze warstwy aplikacyjnej: opcjonalne i odwracalne wpisy
  instalatora w powłoce Windows.

Nie przypisujemy obecnie `Ctrl+Enter` ani innego nowego skrótu. Integracja nie
ustawia AMC domyślnym programem bez decyzji użytkownika.

## Materiał do dokumentacji użytkownika

### Etap A — folder zawierający

W menu **Pliki** oraz w palecie poleceń `Ctrl+Shift+K` jest polecenie
**Otwórz folder zawierający**. Działa dla lokalnego pliku lub folderu
zaznaczonego na liście, a w widoku odtwarzacza — dla rzeczywiście odtwarzanego
lokalnego pliku. Dla pliku Eksplorator otwiera folder i zaznacza ten plik; dla
folderu otwiera sam folder.

Polecenie celowo nie ma jeszcze skrótu. Pełna pomoc `F1` podaje je jako
**Bez skrótu — Otwórz folder zawierający**. `Ctrl+F1` nadal opisuje wyłącznie
rzeczywiście naciśnięty gest i nie udaje nieistniejącego skrótu.

Jeżeli element internetowy nie ma lokalnej kopii, AMC mówi:
**Ten element nie ma lokalnego pliku**. Jeżeli zapamiętana ścieżka już nie
istnieje, mówi: **Nie znaleziono lokalnego pliku**. Adres internetowy nie jest
otwierany jako folder.

### Etap B — otwieranie pliku i dodawanie z powłoki

Launcher rozpoznaje istniejący, obsługiwany plik przekazany w wierszu poleceń.
Przy zwykłym otwarciu działający AMC przechodzi do sesji Pliki lokalne,
uruchamia wskazany plik i pokazuje jego folder. Parametr `/kolejka` dodaje jeden
lub wiele plików do istniejącej kolejki bez zmiany bieżącej sesji, odtwarzania
i fokusu. Ponowne dodanie tego samego pliku pozostawia go w kolejce i mówi
**Plik jest już w kolejce** zamiast go usuwać.

Jeżeli AMC danego profilu już działa, drugi launcher przekazuje zadanie przez
prywatny kanał bieżącego użytkownika i tylko uaktywnia okno. Nie prosi o
zamknięcie ani nie wykonuje bezpiecznej podmiany wersji, a więc nie przerywa
nagrywania. AMC Test i publiczny AMC mają osobne kanały.

### Etap C — opcjonalna integracja instalatora

Instalator ma dwie domyślnie odznaczone opcje w grupie **Integracja z
Eksploratorem Windows**:

- dodanie poleceń **Otwórz w AMC** oraz **Dodaj do kolejki AMC** do menu
  kontekstowego obsługiwanych plików;
- pokazanie AMC na liście **Otwórz za pomocą** i w ustawieniach aplikacji
  domyślnych Windows.

AMC Test otrzymuje własne etykiety i osobne wpisy. Instalator nie wybiera AMC
jako programu domyślnego. Wyłączenie opcji podczas aktualizacji usuwa wpisy
danego profilu, a odinstalowanie usuwa je wszystkie bez naruszania wpisów
drugiego profilu.

## Uzasadnienie i decyzje

- 2026-10-19: etap aplikacyjny powstaje przed rejestracją powłoki i przed
  instalatorem. Pozwala to sprawdzić zachowanie bez zmiany skojarzeń Windows.
- Polecenie jest jedną akcją wspólną dla wykonania, menu, pełnej pomocy i
  palety. Dostępność wynika z bieżącej sesji oraz z lokalnej ścieżki elementu.
- Ścieżka jest przekazywana Eksploratorowi jako osobna lista argumentów, bez
  `shell=True` i bez składania tekstowej komendy. Nazwy ze spacjami, przecinkami,
  średnikami i polskimi znakami nie zmieniają znaczenia polecenia.
- Sprawdzenie istnienia następuje dopiero po wykonaniu polecenia. Dzięki temu
  odświeżanie menu nie blokuje interfejsu przy niedostępnym dysku sieciowym.
- Internetowy element bez pobranej kopii otrzymuje krótką odmowę; jego adres
  nie trafia do komunikatu NVDA.
- Launcher ponownie sprawdza pełną ścieżkę, istnienie i obsługiwane rozszerzenie
  przed przekazaniem żądania. Interfejs sprawdza istnienie jeszcze raz przed
  wykonaniem, aby usunięcie pliku w krótkim oknie czasowym nie kończyło się
  technicznym błędem.
- Dane kanału są jednoliniowym JSON-em, a nie składaną komendą. Kanał named
  pipe jest ograniczony do bieżącego użytkownika i rozdzielony profilem.
- `/kolejka` korzysta z osobnej, idempotentnej operacji hosta. Nie używa
  przełącznika członkostwa, bo drugie wywołanie przełącznika usuwałoby plik.
- Lista rozszerzeń instalatora jest sprawdzana automatycznie względem katalogu
  Core. Rozbieżność zatrzymuje test zamiast pozostawiać częściowo działające
  skojarzenia.
- Opcje instalatora są domyślnie wyłączone. Rejestracja ogranicza się do
  bieżącego użytkownika, nie zapisuje chronionego `UserChoice` i nie wymusza
  domyślnej aplikacji.
- 2026-10-19: kontrola przed kolejną instalacją wykryła, że w menu **Pliki**
  litera dostępu `Z` była wspólna dla poleceń **Otwórz folder zawierający** i
  **Zakończ**. Polecenie otwarcia folderu otrzymało literę dostępu `L` w
  słowie „folder”. Jego nazwa, brak skrótu, dostępność, wykonanie, pomoc i
  paleta nie zmieniły się.

## Testy i wynik

2026-10-19, etap A:

- `python wxlite/run_tests.py shell_paths_and_folder_command` — wszystkie 7
  testów AMC14 przeszły;
- sprawdzono rozpoznawanie ścieżki dyskowej i UNC oraz odrzucanie `https:` i
  identyfikatora usługi;
- sprawdzono osobne argumenty Eksploratora dla folderu i zaznaczanego pliku,
  także dla spacji, przecinka, średnika, nawiasu i polskich znaków;
- sprawdzono wspólną nazwę i dostępność w menu, pełnej pomocy oraz palecie dla
  sesji Pliki i Podcasty i YouTube oraz brak polecenia w Radiu;
- sprawdzono lokalny wiersz oraz krótką odmowę dla elementu internetowego.

Uruchamiacz testów zgłosił dodatkowo cztery zastane błędy importu innych
modułów testowych wymagających nieobecnego pakietu `pytest`. Nie są to
niepowodzenia testów AMC14; wszystkie siedem uruchomionych prób tego etapu
zakończyło się wynikiem `OK`.

2026-10-19, etap B:

- testy launchera — **27/27 zaliczone**, w tym prywatny kanał, osobne nazwy
  profili, stdin interfejsu, ścieżka UNC, spacje, polskie znaki, przecinek,
  średnik, nawias i jednoliniowy JSON;
- testy protokołu hosta — **20/20 zestawów zaliczonych**, w tym idempotentne
  `queue.addMembership`, brak duplikatu i brak usunięcia przy drugim dodaniu;
- testy Python dotyczące AMC14 i kolejki — **16 prób zaliczonych**; ten sam
  uruchamiacz nadal kończy się kodem 1 wyłącznie przez cztery zastane moduły
  wymagające nieobecnego `pytest`;
- kompilacja `AccessibleMediaController.PythonLauncher` — sukces, 0 ostrzeżeń,
  0 błędów;
- kompilacja `AccessibleMediaController.LiteHost` oraz Core — sukces,
  0 ostrzeżeń, 0 błędów.

2026-10-19, etap C:

- pełny projekt `AccessibleMediaController.Core.SmokeTests` — zaliczony, w tym
  kontrakt dobrowolnej i odwracalnej integracji, brak `UserChoice` oraz pełna
  zgodność rozszerzeń instalatora z `ShellIntegrationRules.AllExtensions`;
- Inno Setup 6.7.3 — rzeczywista kompilacja próbnego instalatora zakończona
  sukcesem w 125,375 s; instalatora nie uruchomiono i nie zainstalowano;
- po próbie usunięto wyłącznie katalog
  `D:\Projekty Codex\AMC - integracja wxPython\.test-tmp\amc14-iss-check`:
  1 odtwarzalny plik, 123 321 674 bajty. Odzyskanie po usunięciu wymagałoby
  ponownej kompilacji; zachowano właściwy zweryfikowany instalator AMC12.

2026-10-19, korekta litery dostępu przed instalacją zbiorczą:

- pojedynczy test wszystkich widocznych wariantów menu i sesji: **1
  zaliczony**; nie pozostała kolizja liter dostępu w menu **Pliki**;
- zmiana dotyczy wyłącznie znacznika litery dostępu w menu, dlatego nie tworzy
  nowej nazwy ani nowego skrótu w `Ctrl+F1`, pełnej pomocy i palecie
  `Ctrl+Shift+K`.

2026-10-19, pierwsza pełna bramka instalacji zbiorczej:

- pełna regresja zatrzymała instalację wynikiem **1827 zaliczonych, 110
  pominiętych, 11 podtestów zaliczonych i 3 niezaliczone**;
- dwa niezaliczone przypadki wykazały, że odświeżenie menu polecenia folderu
  zakładało obecność pola ścieżki także w uproszczonym wierszu innego typu;
  warunek dostępności odtąd traktuje brak ścieżki jako brak lokalnego pliku,
  bez błędu technicznego i bez udostępniania martwego polecenia;
- instalacja nie została rozpoczęta. Wynik nie jest uznany za zaliczenie;
  wymaga zielonego powtórzenia pełnej bramki.

## Znane ograniczenia

- Etap A jest zmianą źródłową i testową. Nie zbudowano ani nie zainstalowano
  nowej wersji, nie otwierano też prawdziwego Eksploratora w teście.
- Rejestracja systemowa jest gotowa w źródle instalatora, ale celowo nie została
  zastosowana w rejestrze bieżącego komputera.
- Kanał został sprawdzony testem odizolowanym, lecz nie zainstalowano nowego
  launchera i nie wykonano jeszcze ręcznej próby z Eksploratorem.

## Wersja i commit

- Profil: źródła wspólne AMC Test i publicznego AMC, z późniejszym rozdzieleniem
  kanału przekazywania żądań według profilu.
- Instalacja: bez zmian.
- Commit etapu A: `515898c8`.
- Commit etapu B: `662f9c52`.
- Commit etapu C: `c9d01839`.
- Korekta litery dostępu menu: `c07e6c21` —
  `fix(amc14): usuń kolizję litery dostępu menu`; instalacja i publikacja
  jeszcze bez zmian.
