# AMC Test 23.10.2026, 16:30 — wyjście Spotify i rzetelny wynik OAuth YouTube

- Status: `Zbudowane, atomowo zainstalowane i uruchomione; automatyczny
  odbiór paczki zaliczony, czeka na ręczny test dźwięku Spotify i ponowne
  prawdziwe logowanie YouTube`.
- Data instalacji: 23 października 2026
- Obszar: AMC08, YT-001, wyjście audio Spotify, OAuth YouTube
- Instalacja: `D:\Projekty Codex\AMC Python`

## Zachowanie widoczne dla użytkownika

Jeżeli profil Spotify pamięta nazwane urządzenie, którego nie ma na liście
hosta Librespot, AMC sprawdza je już podczas konfiguracji sesji. Bieżący tor
przechodzi na domyślne urządzenie Windows przed pierwszym odtworzeniem, ale
zapamiętana preferencja pozostaje w profilu i może zostać użyta po ponownym
podłączeniu sprzętu.

Po faktycznym uruchomieniu dźwięku NVDA ma jednorazowo powiedzieć:
`Zapamiętane urządzenie audio Cyfrowy interfejs audio (PMA-1700NE) jest
niedostępne. Spotify odtwarza na domyślnym urządzeniu systemowym`.

W logowaniu YouTube strona powrotu nie ogłasza już przedwcześnie sukcesu.
Mówi, że Google przekazał zgodę, a AMC nadal kończy logowanie. Dopiero stan
`YouTube: zalogowano` potwierdza zapis tokenu. Znane błędy konfiguracji klienta
są zamieniane na bezpieczne komunikaty użytkowe bez kodu autoryzacyjnego,
tokenu ani surowej odpowiedzi Google.

Logowanie nie nadpisuje Biblioteki i samo nie pobiera kanałów. `Sprawdź
subskrypcje` tworzy wyłącznie podgląd nowych lub możliwych do przywrócenia
kanałów. Dopiero osobne `Zapisz subskrypcje w Bibliotece AMC` scala zatwierdzony
plan z istniejącą sesją `Podcasty i YouTube`; nie usuwa dotychczasowych pozycji.

## Dokładne polecenia i lokalizacje

- Program: `D:\Projekty Codex\AMC Python\AMC.exe`.
- Polecenie konta: w sesji `Podcasty i YouTube` nacisnąć `Ctrl+Shift+K`, wpisać
  `Konto YouTube` i nacisnąć Enter.
- Kandydat:
  `.test-output/AMC-Python-next-2026.10.23-cfe4f432cdb69ec6e10d5e6d0f4cab6f47040705-c57a249b`.
- Instalację wykonano skryptem `wxlite/tools/Promote-AMCPythonTestBuild.ps1`
  w PowerShell 7, z `-InstallRoot "D:\Projekty Codex\AMC Python" -SkipTests`.
  Pełnych testów nie powtarzano, ponieważ były już zaliczone dla dokładnie tego
  samego czystego commita; promocja ponownie sprawdziła manifest, sumy i start.

## Komunikaty i obsługa czytnika ekranu

Po udanym OAuth NVDA otrzymuje instrukcję:
`Zalogowano do YouTube. Teraz wybierz Sprawdź subskrypcje; lista nie zmieni
Biblioteki, dopóki osobno nie wybierzesz Zapisz subskrypcje w Bibliotece AMC.`
Przycisk po połączeniu konta ma nazwę `Zaloguj ponownie konto YouTube przez
Google w przeglądarce`. Lista planu nadal ma jawne etykiety użytkowe; nazwy
typów, rekordów i identyfikatory techniczne nie są przekazywane do UIA.

Rzeczywista mowa NVDA, kolejność fokusu po powrocie z przeglądarki i odbiór
nowego komunikatu Google pozostają do ręcznego sprawdzenia.

## Różnice między trybami

- `AMC Test`: konto YouTube i klient OAuth są dostępne, a poświadczenia mają
  własny magazyn profilu testowego.
- `AMC Public`: konto YouTube nadal nie jest reklamowane ani dołączone.
- Spotify zachowuje nazwane urządzenie jako preferencję profilu, lecz bieżąca
  sesja może bezpiecznie użyć domyślnego wyjścia, gdy sprzętu nie ma.

## Rzeczywiste testy i wyniki

- Spotify: test cyklu życia, test wyjścia i natywny start zaliczone. Izolowana
  scena dokładnie odtwarza `zapisany Denon → tylko domyślne Realtek → pierwszy
  Play`; sprawdzanie nie żąda tokenu, pierwsze `initialize` dostaje
  `device=null`, a komunikat fallbacku pojawia się raz.
- Kody `trackUnavailable` i `track_unavailable` są rozpoznawane, a dziennik
  zachowuje tylko znormalizowany kod z zamkniętego zbioru.
- OAuth YouTube: 11/11 scenariuszy fundamentu i 7/7 scenariuszy kontraktu.
- Interfejs YouTube i komunikat Spotify: 38/38 testów celowanych.
- Pełna regresja wxPython: 2016 zaliczonych, 111 kontrolowanie pominiętych i
  11 podtestów zaliczonych. Protokół LiteHost: 27/27 zestawów.
- Całe rozwiązanie Release: 0 ostrzeżeń i 0 błędów.
- Pierwsze równoległe wywołanie trzech testów Spotify zderzyło się na wspólnych
  plikach pośrednich WPF. Natywny start uruchomiony następnie osobno w Release
  zaliczył test; nie był to błąd produktu.
- Pierwsze uruchomienie promocji przez starszy `powershell.exe` zakończyło się
  na analizie UTF-8 skryptu, przed budową i przed zamknięciem AMC. To samo
  polecenie w `pwsh` zakończyło się powodzeniem.
- Kandydat i zainstalowana kopia: 1672 pliki, pełna integralność i kontrolowany
  start zaliczone.
- Uruchomiona aplikacja: `AMC Test — 23.10.2026, 16:30`; procesy `AMC.exe`,
  prywatny `runtime\python.exe` i `host\amc_lite_host.exe` pochodzą z D:.
- Rzeczywisty host Spotify widzi obecnie wyłącznie `Głośniki (2 — Realtek(R)
  Audio)` jako urządzenie domyślne. Denon jest faktycznie nieobecny.
- Zainstalowany host YouTube w izolowanej sondzie zwrócił `available=true`,
  `readOnly=true` i osobne poświadczenia profilu. Sonda nie użyła Biblioteki
  użytkownika.

## Bezpieczeństwo instalacji i znane ograniczenia

Przed instalacją AMC nagrywał cztery pliki rozpoczęte około 16:00 i 16:07.
Aktualizacja czekała na naturalne zakończenie wszystkich czterech; ostatni
zapis zakończył się o 16:29:15. Dopiero osobna kontrola dziennika potwierdziła
brak aktywnego nagrania. Następnie wykonano atomową podmianę i uruchomienie.

Poprzednia próba OAuth nie utworzyła poświadczenia
`AccessibleMediaController/test/YouTube`: przeglądarka odebrała kod, lecz
Google odrzucił późniejszą wymianę na token. Po tej instalacji trzeba ponowić
logowanie. Dopiero wynik w AMC rozstrzygnie, czy konfiguracja klienta Google
wymaga dalszej korekty.

Ręczny test fizycznego dźwięku Spotify nadal jest potrzebny. Automatyczny test
potwierdza wybór urządzenia i pierwszą komendę hosta, ale nie zastępuje odsłuchu
na komputerze użytkownika. Nie utworzono instalatora AMC Public, nie wykonano
publikacji ani wysłania zmian do GitHuba. Wyniki i kandydat pozostają lokalnie
do czasu akceptacji tej instalacji.

## Wersja i commit

- Rewizja źródła paczki:
  `cfe4f432cdb69ec6e10d5e6d0f4cab6f47040705`.
- Identyfikator zawartości: `c57a249b`.
- Etykieta:
  `2026.10.23-cfe4f432cdb69ec6e10d5e6d0f4cab6f47040705-c57a249b`.
- Promocja zakończona: 23.10.2026, 16:31:39 czasu lokalnego.
- Niniejszy zapis powstał po instalacji i nie zmienia tożsamości już
  zainstalowanej paczki.

