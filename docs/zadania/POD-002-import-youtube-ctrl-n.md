# POD-002 — jednoetapowy import linków YouTube pod Ctrl+N

## Status

**Zrobione i przyjęte przez użytkownika 23.10.2026. Korekta po ręcznym
zgłoszeniu NVDA została zbudowana, zweryfikowana automatycznie, zainstalowana
i uruchomiona w AMC Test, a użytkownik przyjął działanie `Ctrl+N` w sesji
`Podcasty i YouTube`. Ten zapis zastępuje niższe historyczne stwierdzenia
„nie została zainstalowana” oraz „czeka na ponowny odbiór NVDA”. AMC Public,
instalator publiczny i GitHub pozostały bez zmian. Szczegóły pierwszej
instalacji korekty:
[AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md](AMC-TEST-2026-10-23-1124-instalacja-zbiorcza.md).**

## Odbiór użytkownika — 23 października 2026

Użytkownik przyjął przepływ `Ctrl+N` w sesji `Podcasty i YouTube`. Odbiór
zamyka oczekiwanie na ponowne sprawdzenie tej funkcji z NVDA. Transmisje na
żywo, logowanie Google i inne zadania YouTube zachowują własne, niezależne
statusy i nie są domyślnie uznane za odebrane przez tę decyzję.

## Porządek po odbiorze — 23 października 2026

Po przyjęciu etapu usunięto 13 odtwarzalnych katalogów `bin`, `obj` i
`.pytest_cache` wyłącznie z
`D:\Projekty Codex\AMC worktrees\youtube-import-nvda`. Zwolniono około
292 MiB. Usunięcie nie jest odwracalne, ale całą zawartość można ponownie
wytworzyć przez build i testy. Nie usunięto źródeł, historii Git,
dokumentacji, instalacji AMC ani danych użytkownika.

**Korekta użytkownika z 23.10.2026 po odbiorze instalacji 11:24:** dodanie
kanału kończy się powodzeniem, lecz bardzo szybkie `Ctrl+V` zaraz po `Ctrl+N`
powoduje krótkie przymrożenie. Formularz nie przechwytywał własnego wklejania;
zdarzenie mogło jeszcze trafić do globalnego `Ctrl+V` listy, zanim fokus pola
edycyjnego ustabilizował się po otwarciu modalu. Nowa korekta wiąże `Ctrl+V`
bezpośrednio z polem adresu lub nazwy i odkłada samo wklejenie o jedną kolejkę
zdarzeń interfejsu. Nie dodaje nowego polecenia ani skrótu aplikacji. Kod,
pełna regresja, budowa i instalacja są gotowe w AMC Test
`23.10.2026, 12:56`; uruchomiona paczka ma rewizję `65b11661` i identyfikator
`94b08d59`. Szczegóły:
[AMC-TEST-2026-10-23-1256-korekta-spotify-youtube-frontier.md](AMC-TEST-2026-10-23-1256-korekta-spotify-youtube-frontier.md).
AMC Public pozostaje bez zmian.

Zgłoszenie potwierdziło, że kanał Wieniawski został dodany, ale podczas
oczekiwania NVDA wypowiedział techniczny komunikat przypominający „Windows 32”
i uruchamianie terminala, po czym użytkownik znów znalazł się na ekranie AMC.
Nowa korekta utrzymuje formularz modalny przez całą operację, stabilizuje fokus,
blokuje ponowne zatwierdzenie, ukrywa procesy potomne dwiema niezależnymi
barierami Windows i nie przekazuje technicznych szczegółów do zwykłej mowy.

Wcześniejsza instalacja AMC Test z 2026-10-23 zawierała wyłącznie poprawkę
idempotentnej normalizacji `%40`. Jej status „zainstalowana i czeka tylko na
odbiór” zostaje zastąpiony przez niniejszy zapis, ponieważ nie zawierała nowej
korekty formularza, fokusu i procesów potomnych.

## Zachowanie widoczne dla użytkownika

W sesji **Podcasty i YouTube** `Ctrl+N` otwiera natywny formularz dodawania
źródła. Po wklejeniu publicznego adresu kanału, playlisty, filmu albo
transmisji jeden Enter uruchamia przycisk **Sprawdź i dodaj**. AMC najpierw
sprawdza adres, a po powodzeniu zapisuje źródło w Bibliotece. Nie trzeba
wykonywać osobno operacji „Sprawdź” i „Dodaj”.

Obsługiwany jest również zwykły adres kanału z uchwytem, na przykład
`https://www.youtube.com/@NazwaKanału`. Pomoc w formularzu podaje ten format
wprost.

Po pierwszym Enterze formularz pozostaje otwarty. Pola adresu i nazwy stają się
tylko do odczytu, fokus pozostaje w nazwanym polu adresu, a przyciski
**Sprawdź i dodaj** oraz **Anuluj** są zablokowane. Status i mowa podają
„Sprawdzanie i dodawanie źródła. Czekaj”. Drugi Enter jest ignorowany i nie
może przejść do listy głównego okna.

Po błędzie ten sam formularz nadal jest otwarty, pole adresu znów jest
edytowalne, zaznaczone i ma fokus. Po sukcesie formularz zamyka się dokładnie
raz, Biblioteka zostaje otwarta na zapisanym źródle, a NVDA podaje wynik bez
prywatnego identyfikatora. Ponowne `Ctrl+N` tworzy świeży formularz z początkowym
fokusem w polu adresu.

Procesy hosta, `yt-dlp`, FFmpeg i pakietowego Pythona nie mogą tworzyć ani
aktywować okna konsoli. Komunikat błędu przeznaczony do zwykłej mowy nie ujawnia
nazwy procesu, terminala, `Win32` lub „Windows 32”, ścieżki ani reprezentacji
obiektu.

## Uzasadnienie i decyzje

- Zakończone 2026-10-22 zadanie historycznego interfejsu WPF potwierdziło, że
  tamten formularz wymagał ujednolicenia do jednego Entera.
- Bieżący AMC Test w wxPython już realizował docelowy jednoetapowy przebieg.
  Ręczny odbiór wykazał jednak, że samo okno działało, lecz LiteHost odrzucał
  poprawny kanał przed uruchomieniem `yt-dlp`.
- **Korekta użytkownika z 2026-10-22 zastępuje wcześniejszą ocenę, że
  zainstalowany przebieg jest zweryfikowany i czeka tylko na odbiór.** Pierwsza
  normalizacja poprawnie tworzyła adres
  `https://www.youtube.com/%40WieniawskiSociety/videos`. `FetchAsync`
  normalizował go ponownie, ale analizował nieodkodowany segment `%40…`, nie
  rozpoznawał początku `@` i zgłaszał błąd jeszcze przed wywołaniem `yt-dlp`.
- Segmenty ścieżki są teraz odkodowywane przed ścisłą walidacją. Normalizacja
  jest idempotentna: adres użytkownika i jego stabilna postać `%40…/videos`
  prowadzą do tego samego kanału. Odkodowane ukośniki i inne znaki spoza
  bezpiecznego alfabetu nadal są odrzucane.
- **Korekta użytkownika z 2026-10-23 zastępuje wcześniejszą ocenę, że po
  poprawce `%40` przebieg wymaga już tylko powtórnego odbioru.** Formularz
  korzystał z modalnego wyniku `wx.ID_OK`, dlatego pierwszy Enter zamykał go
  przed rozpoczęciem pracy asynchronicznej. Użytkownik widział ponownie główne
  okno, a drugi Enter mógł trafić na jego kontrolkę. Operacja działała, lecz jej
  stan nie miał już własnego, stabilnego miejsca fokusu.
- Formularz posiada teraz własny stan oczekiwania i kończy modal dopiero po
  sukcesie. W trakcie pracy nie można zatwierdzić ani zamknąć formularza;
  niepowodzenie przywraca edycję i fokus bez tworzenia kolejnego okna.
- Samo `CreateNoWindow` nie jest jedyną barierą. Wspólna fabryka procesów C#
  ustawia również ukryty styl okna, klient hosta Python przekazuje
  `STARTUPINFO` z `SW_HIDE`, a launcher pakietowego Pythona stosuje tę samą
  politykę. Audyt objął wszystkie uruchomienia `yt-dlp`, FFmpeg, LiteHosta i
  pakietowego Pythona; wywołania narzędzi C# dziedziczą politykę z jednego
  miejsca.
- Techniczny tekst wyjątku jest oddzielony od komunikatu dla użytkownika.
  Bezpieczny opis domenowy hosta może pozostać, lecz ścieżki, nazwy procesów,
  terminal, `Win32`/„Windows 32” i reprezentacje obiektów są zastępowane
  neutralną instrukcją dalszego działania.
- Polecenie, skrót i menu pozostają filtrowane przez sesję. `Ctrl+N` w innych
  sesjach może oznaczać inną, kontekstową czynność. Test parytetu porównuje
  resolver skrótu, menu, paletę poleceń, pomoc kontekstową i pełną pomoc
  klawiatury.

## Testy i wynik

### Korekta fokusu i procesów z 2026-10-23

- Celowane testy formularza, klienta hosta, menu, skrótu i palety w
  udokumentowanym środowisku `uv`: **145 zaliczonych, 0 nieudanych**.
- Pełna regresja wxLite: **1961 zaliczonych, 139 pominiętych i 11 podtestów
  zaliczonych** w 3 min 19 s. Testy pominięte wymagają opcjonalnych usług,
  składników lub jawnych zmiennych środowiskowych.
- Po doprecyzowaniu filtra dokładnej formy „Windows 32” ponownie uruchomiono
  testy formularza: **7 zaliczonych, 0 nieudanych**.
- Rzeczywisty LiteHost Release z lokalnym serwerem RSS i tymczasową bazą:
  **1 zaliczony, 1 prawidłowo pominięty**. Pominięto tylko opcjonalny test
  sieciowy YouTube, ponieważ `AMC_LIVE_YOUTUBE_ADDRESS` był jawnie usunięty.
- Testy launchera i aktualizatora: **30/30 zaliczonych**. Sprawdzają także
  `CreateNoWindow` i ukryty styl startowy pakietowego Pythona.
- Testy protokołu LiteHosta: **27/27 zestawów zaliczonych**. Wypisany stos
  kontrolowanego wyjątku pochodził z testu zamiany awarii handlera na odpowiedź,
  a nie z niepowodzenia zestawu.
- Kompilacja Release testów Windows: **0 ostrzeżeń, 0 błędów**. Izolowany test
  uruchomił atrapę procesu przez wspólną fabrykę, potwierdził brak głównego
  okna i zakończył się kodem 0. Test pozostał częścią zwykłego zestawu smoke.
- Ukierunkowany test `--youtube-collection-normalization`: **zaliczony**.
- Kompilacja LiteHost Release: **0 ostrzeżeń, 0 błędów**.
- `git diff --check`: **bez błędów**.
- Pierwsza próba przez systemowy Python nie była miarodajną regresją: wykonała
  **198 testów poprawnie i 2 pominęła**, po czym 6 modułów nie zaimportowało się
  z powodu braku pakietu `pytest`. Wszystkie właściwe wyniki powyżej pochodzą z
  wymaganego środowiska `uv --with pytest --with wxpython`.
- Nie uruchamiano żywego AMC, instalatora ani sieciowego importu YouTube. Nie
  użyto biblioteki użytkownika; testy korzystały z atrap i katalogów
  tymczasowych.

### Wcześniejsza weryfikacja poprawki `%40`

- Deterministyczna regresja obejmuje dokładny adres
  `https://www.youtube.com/@WieniawskiSociety` oraz ponowną normalizację
  `https://www.youtube.com/%40WieniawskiSociety/videos`.
- Wcześniejszy, jawnie włączony test sieciowy rozpoznał kanał jako
  `UCpFEKtbJxKnsOcraylnuNsA`, nazwę „Wieniawski Society - Videos” i stabilny
  adres `%40…/videos`. Ten historyczny wynik nie zastępuje ręcznego odbioru ani
  nie dowodzi zachowania nowej korekty fokusu i procesów.
- Wcześniejsza instalacja `1badabbe` przeszła pełną integralność i kontrolowany
  start, lecz nie zawiera commita bieżącej korekty.

## Znane ograniczenia

- Ręczny odbiór podstawowego przepływu `Ctrl+N` został przyjęty przez
  użytkownika. Szczegółowe ścieżki awarii sieciowej i niedostępnego materiału
  pozostają dodatkowo chronione testami automatycznymi.
- Sieciowego importu YouTube nie powtarzano dla tej korekty. Poprzedni wynik
  prawdziwego kanału potwierdza normalizację i usługę, nie nową obsługę okna.
- Rzeczywisty import zależy od dostępności publicznego materiału i odpowiedzi
  YouTube oraz `yt-dlp`. Materiał prywatny albo wymagający logowania nie jest
  traktowany jako publiczne źródło.
- Pliki `bin` i `obj` powstałe podczas weryfikacji pozostają w worktree do
  akceptacji wyniku; nie są instalacją ani paczką wydania.

## Wersja i commit

- Bazowy commit bieżącej korekty:
  `609aa64447c6eb2c8775341157ef243952b61942`.
- Commit bieżącej poprawki źródeł i testów:
  `f6d3389f2e240aa7e7fe63f4378f6d8121c0d5c3`.
- Commit dokumentujący ręczny odbiór użytkownika:
  `60bc7b476bd598af878e72d26cb1a4e60b573ec1`.
- Gałąź: `task/youtube-import-nvda`; wyłączny worktree:
  `D:\Projekty Codex\AMC worktrees\youtube-import-nvda`.
- Wcześniejszy zainstalowany kandydat `%40`:
  `2026.10.23-1badabbeeacde3d8853457683ef750d558b3f1fd-7353e273`.
  Nie zawiera bieżącego commita.
- Korekta została później scalona do gałęzi integracyjnej i znajduje się
  również w przyjętym AMC Test `23.10.2026, 21:25`, którego rewizją źródłową
  jest `4119476314529741741639de6ee662951e656092`. AMC Public, instalator
  publiczny i GitHub pozostały bez zmian.

## Materiał do dokumentacji użytkownika

W sesji **Podcasty i YouTube** naciśnij `Ctrl+N`, wpisz pełny publiczny adres,
na przykład `https://www.youtube.com/@NazwaKanału`, i naciśnij Enter na
przycisku **Sprawdź i dodaj**. AMC sam rozpoznaje źródło, pobiera najwyżej 100
najnowszych materiałów i zapisuje je w Bibliotece. Formularz pozostaje otwarty,
a NVDA mówi „Sprawdzanie i dodawanie źródła. Czekaj”. Podczas operacji drugi
Enter nie uruchamia duplikatu. Po powodzeniu NVDA podaje rodzaj źródła, nazwę i
liczbę pozycji, a fokus przechodzi do zapisanego źródła w Bibliotece. Błąd
pozostawia formularz do poprawienia z fokusem i zaznaczeniem w polu adresu.
Funkcja działa bez logowania i bez cookies; kanały prywatne lub wymagające
logowania nie są obsługiwane.

## Roboczy wpis do changelogu

- Naprawiono import kanałów YouTube z adresów zawierających uchwyt `@` pod
  `Ctrl+N`. Stabilny, zakodowany adres `%40…/videos` może być ponownie
  sprawdzony bez błędnego odrzucenia kanału przed uruchomieniem `yt-dlp`.
- Po zgłoszeniu NVDA z 2026-10-23 formularz `Ctrl+N` pozostaje otwarty przez
  całe sprawdzanie, blokuje drugi Enter, zachowuje przewidywalny fokus i kończy
  się dopiero sukcesem. Błąd przywraca pole adresu. Procesy pomocnicze są
  uruchamiane bez okna, a zwykła mowa nie ujawnia terminala, `Win32`, ścieżek
  ani nazw technicznych. Korekta została zainstalowana w AMC Test i przyjęta
  przez użytkownika 23.10.2026.
