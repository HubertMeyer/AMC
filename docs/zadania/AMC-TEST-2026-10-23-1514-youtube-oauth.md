# AMC Test 23.10.2026, 15:14 — klient OAuth YouTube

- Status: `Zbudowane, zainstalowane i uruchomione; czeka na prawdziwe logowanie oraz ręczny odbiór NVDA`.
- Data instalacji: 23 października 2026
- Obszar: YT-001, Google OAuth, profil AMC Test
- Instalacja: `D:\Projekty Codex\AMC Python`

## Zachowanie widoczne dla użytkownika

AMC Test ma teraz lokalną konfigurację klienta Google dla aplikacji
komputerowej. W sesji `Podcasty i YouTube` polecenie `Konto YouTube i
synchronizacja subskrypcji…` jest zasilane tym samym modelem w menu Plik,
palecie `Ctrl+Shift+K` i pełnej pomocy. Samo uruchomienie programu nie otwiera
strony Google. Przeglądarka ma zostać użyta dopiero po jawnym wybraniu
przycisku `Zaloguj konto YouTube przez Google w przeglądarce`.

Profil AMC Public nie został zbudowany, zainstalowany ani opublikowany i nie
otrzymał tego zasobu.

## Dokładne polecenia i lokalizacje

- Źródło lokalnej konfiguracji testowej:
  `wxlite/amc_wx_lite/youtube-oauth-client-id.txt`.
- Zasób w zainstalowanej paczce:
  `D:\Projekty Codex\AMC Python\app\amc_wx_lite\youtube-oauth-client-id.txt`.
- Kandydat:
  `.test-output/AMC-Python-next-2026.10.23-eea8e9f50fc39e64542ed59119cf7c6273dcae7f-cd5a4c27`.
- Program:
  `D:\Projekty Codex\AMC Python\AMC.exe`.

Identyfikator klienta jest ignorowany przez Git. Nie zapisano sekretu klienta,
tokenu użytkownika ani kodu autoryzacyjnego.

## Komunikaty czytnika ekranu

Przy pierwszym otwarciu okna fokus ma otrzymać etykietę `Zaloguj konto YouTube
przez Google w przeglądarce`. Lista podglądu ma nazwę `Kanały planowane do
zapisania w Bibliotece AMC`, a zamknięcie `Zamknij okno konta YouTube`.
Automatyczne testy potwierdziły obecność etykiet i brak technicznych
reprezentacji obiektów. Rzeczywista mowa NVDA, powrót fokusu z przeglądarki,
anulowanie i odmowa wymagają jeszcze ręcznego odbioru.

## Ważne różnice między trybami

- `AMC Test`: klient OAuth, możliwość `youtube.account.readonly` i polecenie
  konta są dostępne po potwierdzeniu możliwości przez host.
- `AMC Public`: zasób klienta nie jest kopiowany, możliwość nie jest
  reklamowana i polecenie pozostaje niewidoczne.
- Google Testing: tylko użytkownicy testowi; możliwe wygaśnięcie zgody po
  siedmiu dniach.

## Uzasadnienie i decyzje

Klient typu Desktop nie potrafi ukryć sekretu, dlatego AMC używa wyłącznie
publicznego identyfikatora i PKCE. Zaznaczenie Google dotyczące aplikacji
działającej jako agent AI pozostawiono wyłączone: AMC nie jest autonomicznym
agentem wykonującym zadania za użytkownika. Zakres zgody pozostaje tylko do
odczytu subskrypcji.

Pierwsza próba instalacji zatrzymała się bez zmiany starej paczki, ponieważ
bezpieczne zamykanie AMC trwało dłużej niż limit 30 sekund. Nie trwało
nagrywanie. Frontend zapisał stan, operacja rozpoznawania utworu zakończyła
żądanie sieciowe, a procesy starej wersji zamknęły się samodzielnie. Ponowiono
wyłącznie atomową instalację już zweryfikowanego kandydata; nie użyto
wymuszonego kończenia procesów.

## Testy i rzeczywiste wyniki

- Launcher i aktualizator: 30/30.
- Kompilacje .NET wymagane przez bramkę: bez ostrzeżeń i błędów.
- Python/wx: 2014 zaliczonych, 111 pominiętych, 11 podtestów zaliczonych.
- Kandydat: 1672 pliki; kontrolowany start interfejsu i hosta zaliczony.
- Po instalacji: szybka i pełna kontrola integralności zaliczone; kontrolowany
  start zainstalowanej paczki zaliczony.
- Uruchomione okno: `AMC Test — 23.10.2026, 15:14`.
- Uruchomiony plik runtime:
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.

Nie wykonano jeszcze prawdziwego logowania Google ani synchronizacji konta.

## Znane ograniczenia i migracja

Nie ma migracji danych. Token zostanie utworzony dopiero przez jawne logowanie
użytkownika i ma pozostać w chronionym magazynie Windows. Odbiór ręczny musi
objąć wybór konta, zgodę, powrót do AMC, podgląd subskrypcji, zapis, wylogowanie
oraz ponowne otwarcie okna. Publiczne wydanie wymaga osobnej decyzji i
weryfikacji Google.

## Materiał do dokumentacji użytkownika

W AMC Test otwórz sesję `Podcasty i YouTube`, naciśnij `Ctrl+Shift+K`, wpisz
`Konto YouTube` i uruchom polecenie Enterem. W oknie wybierz `Zaloguj konto
YouTube przez Google w przeglądarce`. AMC nie pyta o hasło i prosi wyłącznie o
odczyt subskrypcji. Po powrocie najpierw sprawdź plan zmian; zapis do Biblioteki
AMC jest osobną czynnością.

## Wersja i commit

- Rewizja źródła paczki: `eea8e9f50fc39e64542ed59119cf7c6273dcae7f`.
- Identyfikator zawartości: `cd5a4c27`.
- Etykieta kompilacji:
  `2026.10.23-eea8e9f50fc39e64542ed59119cf7c6273dcae7f-cd5a4c27`.
- Dokumentacja odbioru jest zmianą następującą po instalacji i nie zmienia
  rewizji ani zawartości już zainstalowanej paczki.
