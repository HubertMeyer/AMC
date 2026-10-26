# REL-002 — kanoniczne wydania AMC Test i AMC Public na GitHubie

## Status

W trakcie. Mechanizm aktualizacji z programu, pełny instalator oraz wspólna
bramka wydań Test/Public są zaimplementowane i przeszły automatyczne testy.
Trwa przygotowanie pierwszego instalatora AMC Test do ręcznego odbioru z NVDA.
Publikacja pierwszego wydania Python nastąpi dopiero po sprawdzeniu tego
kandydata; kod, build, instalacja i GitHub Release pozostają osobnymi faktami.

## Nadrzędna korekta użytkownika z 26.10.2026

Ta decyzja zastępuje wcześniejsze opisy, które traktowały kolejne numery
`alpha.4xx`, osobną publiczną linię albo stare repozytorium WPF jako możliwą
bazę dalszych wydań.

- Interesuje nas wyłącznie najnowszy AMC Test w Pythonie. Bazą jest wersja
  złożona 26.10.2026 z czterech najnowszych zadań.
- AMC Public powstaje okresowo z dokładnie tego samego sprawdzonego commitu,
  ale z profilem wyłączającym funkcje niedopuszczone do publicznego wydania.
- Każde faktyczne, zweryfikowane wydanie ma zostać zapisane na GitHubie.
- AMC Test i AMC Public mają mieć niezależne kanały aktualizacji w aplikacji.
- Program może być standardowo zainstalowany na dysku C. Źródła, worktree,
  staging i build pozostają na dysku D w `D:\Projekty Codex`.
- Historyczny AMC WPF, `alpha.422` i przypadkowe późniejsze odnogi nie są bazą
  produktu. Usuwanie nastąpi dopiero po sklasyfikowaniu dokładnych celów i
  potwierdzeniu nowej instalacji Python.

## Stan wejściowy potwierdzony 26.10.2026

### Bieżący AMC Test

- Repozytorium: `D:\Projekty Codex\AMC - integracja wxPython`.
- Worktree bieżącej integracji:
  `D:\Projekty Codex\AMC worktrees\sonos-broker-handoff-20261024`.
- Commit: `bba5e92d687ade1998e79c88656e1a5d545abcf2`.
- Pakiet: `39f0d3f2`.
- Etykieta techniczna:
  `2026.10.26-bba5e92d687ade1998e79c88656e1a5d545abcf2-39f0d3f2`.
- Nazwa okna: `AMC Test — 26.10.2026, 13:32`.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Raport promocji: testy zaliczone, instalacja atomowa, uruchomienie zaliczone.
- Manifest: czyste źródła, profil `test`, kanał `test`, 1674 pliki.

### Konflikt historycznego AMC

Równolegle do właściwej promocji Python inny proces zbudował i zainstalował
historyczny WPF `0.1.0-alpha.427` z katalogu
`D:\Projekty Codex\Accessible Multimedia Controller`. Ten program nie jest
bieżącym AMC Test. Instalacja pozostaje tymczasowo nienaruszona, aby nie usuwać
jej w trakcie innych prac; zostanie odinstalowana dopiero po weryfikacji
systemowego instalatora AMC Test Python.

### GitHub

- Repozytorium `michalkasperczak/AMC` jest publiczne.
- Zdalny `main` nadal kończy się na historycznym WPF `alpha.422`.
- Zdalne gałęzie w chwili audytu: `main`,
  `integracja/wxpython-sonos-tidal-20261008`, `hermes/librespot-probe`,
  `hermes/sonos-group-account-messages` i `wydanie-379`.
- Najnowsze wydanie GitHub to wstępne WPF `v0.1.0-alpha.422`; repozytorium nie
  zawiera jeszcze wydania obecnego AMC Python.

### Lokalny Git

- 12 lokalnych gałęzi jest przodkami dzisiejszego commitu i po ustanowieniu
  kanonicznej gałęzi można je usunąć bez utraty commitów.
- 16 gałęzi ma własne, rozbieżne commity. Nie wolno usuwać ich zbiorczo;
  wymagają porównania commitów i patch-id z dzisiejszą bazą.
- Worktree mają czyste pliki śledzone. Część zawiera wyłącznie nieśledzone
  `.test-output` albo `.test-tmp`; ich sprzątanie nastąpi po odbiorze i
  potwierdzeniu zdalnego archiwum wydania.

## Docelowy model produktu

### Jedno źródło, dwa profile

AMC Test i AMC Public powstają z jednego repozytorium i jednego commitu. Nie
utrzymujemy osobnej gałęzi rozwojowej Public. Różnica jest jawnie wyliczana z
profilu możliwości.

Samo ukrycie pozycji interfejsu nie wystarcza. Funkcja wyłączona w Public:

- nie występuje w menu, `Ctrl+F1`, pełnej pomocy ani `Ctrl+Shift+K`;
- nie ma aktywnego skrótu ani drogi wykonania;
- nie trafia do logów jako dostępna funkcja;
- nie wnosi prywatnego modułu, hosta, zależności ani zasobu do paczki, jeśli
  można go fizycznie odfiltrować;
- ma test parytetu dostępności i wykonania w profilach `test` i `public`.

Kod wspólny może pozostać w jednym publicznym repozytorium, jeśli funkcja ma
być jedynie niedostępna w publicznym instalatorze. Jeżeli jakaś funkcja lub
integracja ma być poufna, nie może trafić do publicznego repozytorium; wymaga
zewnętrznego brokera albo osobnego prywatnego modułu. Sekret nie jest funkcją
i nigdy nie jest dopuszczalnym przełącznikiem wydania.

### Instalacja Windows

Docelowe katalogi użytkownika:

- `%LOCALAPPDATA%\Programs\AMC Test`;
- `%LOCALAPPDATA%\Programs\AMC Public`.

Oba instalatory mają osobne AppId, InstallId, skróty, App Paths, blokady
uruchomienia, deinstalatory i kanały aktualizacji. Integracja systemowa obejmuje
menu Start, opcjonalny skrót pulpitu, rejestrację obsługiwanych plików i
polecenia Eksploratora wyłącznie dla właściwego profilu. Źródła i artefakty
robocze pozostają na D; C zawiera tylko normalnie zainstalowaną aplikację.

Publiczny katalog nazywa się `AMC Public`, a nie samo `AMC`, aby podczas
migracji nie zderzyć się ze starą instalacją WPF w
`%LOCALAPPDATA%\Programs\AMC`.

### Dane użytkownika

Profile Test i Public pozostają fizycznie oddzielone. Nie wolno kierować dwóch
działających aplikacji do tych samych żywych baz SQLite i `state.json`.

Do sprawdzania Public na rzeczywistych danych służy istniejące polecenie
`Odśwież dane z AMC Test`: wersjonowana migawka przenosi wspólne dane do
osobnego profilu Public, nie przenosi tokenów ani poświadczeń i zatrzymuje się
przy konflikcie. Oba profile mogą wskazywać te same istniejące pliki audio bez
ich kopiowania. To jest bezpieczny model używania raz jednej, raz drugiej
aplikacji. Dwukierunkowa synchronizacja zmian Public → Test nie jest obecnie
obiecana; wymagałaby osobnego projektu konfliktów, blokady pisarza i migracji
schematu.

## Docelowy model GitHub i aktualizacji

### Kanał Test

- Tag: `test-YYYY.MM.DD.HHMM`.
- GitHub Release: wydanie wstępne, nieoznaczane jako `Latest`.
- Instalator: `AMC-Test-YYYY-MM-DD-HHMM.exe`.
- Aktualizator AMC Test sprawdza wyłącznie kanał `test` i nigdy nie przyjmuje
  paczki `public`.

### Kanał Public

- Tag: `public-YYYY.MM.DD.HHMM`.
- GitHub Release: zwykłe stabilne wydanie, oznaczane jako `Latest`.
- Instalator: `AMC-Public-YYYY-MM-DD-HHMM.exe`.
- Aktualizator AMC Public sprawdza wyłącznie kanał `stable` i nigdy nie
  przyjmuje paczki `test`.

Każde wydanie zawiera instalator, manifest, SHA-256 i informację o dokładnym
commicie. Publikacja źródeł, publikacja instalatora, instalacja lokalna i
uruchomienie są raportowane jako cztery osobne fakty. Lokalny kandydat albo
build do ręcznego odbioru nie staje się wydaniem tylko dlatego, że się
skompilował.

## Bramki bezpieczeństwa przed pierwszym wydaniem Python

1. Ręcznie odebrać dzisiejszy AMC Test z NVDA.
2. Usunąć możliwość kopiowania `youtube-oauth-client-secret.txt` do dowolnej
   publikowanej paczki. Lokalna konfiguracja deweloperska musi znajdować się
   poza repozytorium i paczką. Czysta instalacja musi użyć PKCE bez sekretu albo
   bezsekretnego brokera; do tego czasu konto YouTube nie może blokować wydania
   pozostałego programu.
3. Dodać test publikacyjny odrzucający sekrety, tokeny, profile, nagrania,
   logi, nieznane pliki i dane użytkownika.
4. Zmienić instalator na dwa jednoznaczne katalogi na C i przetestować
   instalację obok siebie, aktualizację, anulowanie, rollback i deinstalację.
5. Dodać podpisany lub co najmniej hashowany indeks dwóch kanałów oraz test, że
   pakiet obcego profilu zostaje odrzucony przed zamknięciem programu.
6. Zbudować Test i Public z tego samego commitu, porównać manifesty możliwości
   oraz przeskanować zawartość Public pod kątem wyłączonych modułów.
7. Opublikować najpierw wydanie wstępne Test, odczytać z GitHuba nazwę,
   rozmiar i SHA-256, a następnie wykonać aktualizację z poprzedniej wersji.
8. Dopiero po odbiorze Public opublikować stabilne wydanie Public.

## Wykonany etap 1 — źródła bez publikacji

- Publiczny instalator otrzymał oddzielny katalog
  `%LOCALAPPDATA%\Programs\AMC Public`; nie próbuje już wejść do historycznego
  `%LOCALAPPDATA%\Programs\AMC`.
- `Build-AMCInstaller.ps1` odrzuca paczkę, jeżeli manifest albo rzeczywisty
  katalog zawiera lokalny plik sekretu YouTube lub Sonos. Zaliczone przejście
  zapisuje `secretScan: passed` w pliku integralności instalatora.
- Nowy `Publish-AMCRelease.ps1` obsługuje oba profile. Test dostaje tag
  `test-YYYY.MM.DD.HHMM`, kanał `test` i GitHub prerelease; Public dostaje tag
  `public-YYYY.MM.DD.HHMM`, kanał `stable` i zwykłe wydanie.
- Stary `Publish-AMCPublicRelease.ps1` pozostaje zgodnym punktem wejścia, ale
  deleguje do wspólnej profilowanej bramki.
- Tryb bez `-Publish` tylko sprawdza instalator, SHA-256, rewizję, profil,
  skan sekretów i przygotowuje opis oraz manifest gotowości. W tym etapie
  użyto wyłącznie tego kontraktu testowego; nic nie wysłano na GitHub.
- Nie usunięto starego pliku OAuth z działającej instalacji. Próba dodania
  automatycznego usuwania została zatrzymana, ponieważ mogłaby przerwać
  logowanie YouTube przed gotową migracją.

## Wykonany etap 2 — aktualizacja z poziomu programu

### Zachowanie użytkowe

- W menu `Pomoc` działa nowe polecenie `Sprawdź aktualizację AMC…`. Ta sama
  nazwa i akcja występują w palecie `Ctrl+Shift+K`, pomocy kontekstowej
  `Ctrl+F1` oraz pełnej pomocy klawiatury; polecenie nie ma osobnego skrótu.
- Po sprawdzeniu otwiera się dostępne okno. Początkowy fokus trafia do pola
  tylko do odczytu `Informacje o aktualizacji AMC`, zawierającego wersję i
  krótkie podsumowanie zmian. Dalej znajduje się `Aktualizuj AMC` albo, gdy
  nie ma nowej wersji, tylko `Zamknij okno aktualizacji`.
- Nie ma wyboru kanału. Profil Test przyjmuje wyłącznie prerelease z tagiem
  `test-YYYY.MM.DD.HHMM`, a Public wyłącznie stabilne wydanie z tagiem
  `public-YYYY.MM.DD.HHMM`. Obcy profil, kanał, produkt, InstallId, nazwa
  instalatora, rozmiar albo SHA-256 są odrzucane przed zamknięciem AMC.
- Aktualizacja pobiera ten sam pełny instalator EXE, który służy nowemu
  użytkownikowi. Pomocnik prosi AMC o zwykłe, bezpieczne zamknięcie, odmawia
  podmiany przy nagrywaniu albo żywym składniku instalacji, uruchamia Inno
  Setup bez dodatkowych pytań i po sukcesie ponownie otwiera AMC.
- Cichy przebieg instalatora zachowuje wcześniejszy katalog oraz zadania Inno
  Setup, między innymi decyzję o skrócie pulpitu i integracji Eksploratora.
  Windows dostaje poprawny nowy AppVersion i stan deinstalatora; aktualizacja
  nie omija instalatora przez prostą podmianę plików.

### Kontrakt wydania

- `Publish-AMCRelease.ps1` tworzy `amc-update-test.json` albo
  `amc-update-public.json` z profilem, kanałem, wersją użytkową, commitem,
  krótkim opisem oraz nazwą, rozmiarem i SHA-256 pełnego instalatora.
- Wydanie GitHub zawiera instalator, manifest kanału i plik integralności.
  Oddzielny ZIP aktualizacyjny nie jest potrzebny i nie jest publikowany.
- Budowa instalatora wymaga czystych źródeł oraz zgodności commitu paczki z
  commitem instalatora. Pełna paczka nadal zawiera prywatny runtime Python,
  samowystarczalny LiteHost, launcher i helper aktualizacji; nowy komputer nie
  musi mieć zainstalowanego Pythona ani .NET.

### Sprawdzenie aktualizacji składników

- Droga `Pomoc > Sprawdź i zaktualizuj składniki: FFmpeg i yt-dlp` nadal
  prowadzi przez wspólną akcję do LiteHosta. Testy potwierdzają menu, paletę,
  pomoc, dispatcher, tryb automatyczny oraz bezpieczny komunikat błędu bez
  ujawniania ścieżek.
- Zainstalowane składniki zostały rzeczywiście uruchomione: FFmpeg zgłosił
  `n9.0.2-29-g6dfaba896f-20261020`, a yt-dlp `2026.08.19`; suma pliku yt-dlp
  zgadza się z zapisanym stanem.
- Pełne sieciowe pobranie w piaskownicy doszło do uruchomieniowej kontroli
  nowego yt-dlp, lecz system testowy zablokował wykonanie pobranego EXE.
  Próba zmiany współdzielonych składników poza piaskownicą nie otrzymała zgody
  bezpieczeństwa. Rzeczywista kontrola sieciowa z menu pozostaje więc punktem
  ręcznego odbioru, a nie zaliczonym testem aktualizacji dostawcy.

## Kolejność porządkowania

1. Zamrozić dzisiejszy commit jako pierwszy kandydat kanoniczny i dokończyć
   ręczny odbiór.
2. Wprowadzić bramki sekretów i kanały aktualizacji.
3. Zbudować i zweryfikować systemowy instalator AMC Test Python na C.
4. Po działającym zastępstwie usunąć starą instalację WPF `alpha.427`, jej
   skróty i wpisy systemowe; repozytorium WPF zachować jako archiwum historii,
   dopóki porównanie zmian nie potwierdzi, że nic potrzebnego nie zginie.
5. Utworzyć zabezpieczający tag lub bundle wszystkich lokalnych końcówek,
   porównać 16 rozbieżnych gałęzi, a następnie usuwać tylko gałęzie w pełni
   zintegrowane albo jednoznacznie odrzucone.
6. Przenieść kanoniczną linię Python na GitHub `main`. Przed zmianą zachować
   stary koniec WPF pod jednoznacznym tagiem archiwalnym. Nie wykonywać ślepego
   force-push ani kasowania bez weryfikacji zdalnego punktu odniesienia.
7. Po potwierdzeniu zdalnych commitów i artefaktów usunąć wyłącznie dokładnie
   wskazane stare worktree, staging, cache, paczki i katalogi aktualizacji.

## Materiał do dokumentacji użytkownika

AMC Test jest bieżącą, pełną wersją programu. Otrzymuje częstsze wydania
wstępne i aktualizuje się wyłącznie z kanału Test. AMC Public jest okresowym,
sprawdzonym wydaniem tego samego kodu z wyłączonymi funkcjami, które nie są
jeszcze gotowe do przekazania innym osobom. Aktualizuje się wyłącznie z kanału
Public.

Obie aplikacje mogą być zainstalowane obok siebie. Mają osobne ustawienia,
konta i logi. Polecenie `Odśwież dane z AMC Test` pozwala sprawdzić AMC Public
na kopii rzeczywistych danych bez współdzielenia żywych baz i bez przenoszenia
haseł lub tokenów. Nie należy uruchamiać obu programów jako dwóch pisarzy do
tych samych plików profilu.

## Uzasadnienie i decyzje

- Jedna baza kodu usuwa ryzyko naprawiania tego samego błędu dwa razy.
- Dwa profile kompilacji pozwalają fizycznie usunąć niedopuszczone moduły z
  paczki Public, zamiast polegać tylko na ukrytym przycisku.
- Osobne kanały GitHub pozwalają aktualizować Test często, bez proponowania
  tych samych buildów użytkownikom Public.
- Standardowa instalacja na C zapewnia normalny deinstalator i integrację z
  Windows. D pozostaje bezpiecznym miejscem źródeł i buildów.
- Stare wydania GitHub są historią, nie bazą rozwoju. Ich masowe usuwanie nie
  jest wymagane do działania aktualizatora; decyzja o ich późniejszym
  ukryciu lub usunięciu nastąpi po migracji `main`.

## Testy i wynik

- Pełna promocja AMC Test z commitu `bba5e92d…`: zaliczona.
- Atomowa instalacja pakietu `39f0d3f2`: zaliczona.
- Kontrolowany start: zaliczony.
- Ręczny odbiór czterech nowych zakresów z NVDA: oczekuje.
- Kod mechanizmu aktualizacji z GitHuba: zaimplementowany; profil, kanał,
  manifest, rozmiar i SHA-256 są sprawdzane przed zamknięciem aplikacji.
- Ukierunkowane testy Pythona mechanizmu, instalatora, publikacji i składników:
  **80 zaliczonych**.
- Pełna regresja wxPython: **2075 zaliczonych, 111 pominiętych i 13 podtestów
  zaliczonych**.
- Testy launchera i aktualizatora .NET: **33 z 33 zaliczone**, w tym przyjęcie
  pełnego instalatora właściwego profilu i odrzucenie obcego profilu oraz
  niezgodnej sumy.
- LiteHost Release: build zaliczony, 0 ostrzeżeń i 0 błędów.
- Pierwsza próba pakowania wykryła wyścig kontrolowanego startu: interfejs
  zapisywał `READY`, lecz natychmiastowe `ExitMainLoop` mogło ominąć oczekujące
  zdarzenie zniszczenia ramki i pozostawić procesy testowe. Wyjście jest teraz
  planowane przez `wx.CallAfter` po `Close`; bramka nadal wymaga naturalnego
  zakończenia wszystkich procesów i niczego nie zabija. Testy ukierunkowane po
  tej korekcie: **38 zaliczonych**.
- Instalator systemowy Python na C: kandydat jeszcze nie został zbudowany w
  chwili tego zapisu.
- Aktualizacja z prawdziwego GitHub Release: oczekuje na publikację pierwszego
  odebranego wydania AMC Test.
- Publikacja GitHub bieżącego Python: niewykonana.

## Znane ograniczenia

- Bieżąca instalacja na D nadal używa pozostawionego ze starszego builda,
  niezarządzanego pliku `youtube-oauth-client-secret.txt`. Dzisiejszy manifest
  go nie zawiera, ale uruchomiony host odnalazł go w katalogu instalacji.
  Pliku nie wolno publikować. Nie usuwać go podczas działania programu;
  migracja OAuth musi zachować lub uczciwie wyłączyć logowanie YouTube.
- Historyczny WPF `alpha.427` został dziś zainstalowany przez równoległe
  zadanie. Nie jest dowodem aktualności AMC i nie może zastąpić Python.
- Publiczny GitHub pokazuje obecnie historię WPF; zmiana `main` jest osobną,
  jeszcze niewykonaną operacją.

## Wersja i commit

- Wersja techniczna przygotowywanego kandydata: `0.1.0-alpha.434`.
- Bazowy stan przed zmianą: `73279fbb15a1cd34c6813f24e097e0467889a197`.
- Commit mechanizmu aktualizacji: `66118f651309efc711c2f090c2e0e4c42e37a80c`.
- Dokładna rewizja paczki będzie zapisana automatycznie w jej
  `bundle-manifest.json` oraz pliku integralności instalatora.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Publikacja: brak.
- Wcześniejszy commit etapu źródłowego: `d87a27f6`
  (`build(release): rozdziel kanały Test i Public`).
