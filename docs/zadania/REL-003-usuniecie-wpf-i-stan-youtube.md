# REL-003 — usunięcie starego WPF i stan synchronizacji YouTube

- Data decyzji użytkownika: 26 października 2026
- Repozytorium kanoniczne: `D:\Projekty Codex\AMC - integracja wxPython`
- Worktree wykonawczy: `D:\Projekty Codex\AMC worktrees\sonos-broker-handoff-20261024`
- Status: stara instalacja i artefakty WPF usunięte; źródła historyczne zachowane do archiwizacji

## Decyzja użytkownika

Użytkownik potwierdził, że bieżący AMC Test w Pythonie jest jedyną rozwijaną
wersją testową. Nie chce obecnie nadinstalowywać jej instalatorem systemowym.
Stara aplikacja WPF oraz jej lokalne artefakty mogą zostać usunięte, ale
niezweryfikowane źródła i historia mają zostać zachowane do czasu bezpiecznej
archiwizacji.

Ta decyzja uzupełnia REL-002. Nie zmienia rozdzielenia kanałów Test i Public.

### Korekta decyzji z 26 października 2026

Po pierwszym bezpiecznym zatrzymaniu użytkownik jawnie zatwierdził usunięcie
lokalnych instalatorów 424–427 oraz oczyszczenie gałęzi. Ta późniejsza decyzja
zastępuje wcześniejsze tymczasowe ustalenie, aby zachować katalog `publish` do
potwierdzenia zdalnego archiwum. Nadal nie obejmuje kasowania gałęzi z
unikalnymi commitami ani worktree należących do innych zadań bez ich kontroli.

## Bieżący AMC Test

Po równoległym wdrożeniu z 26 października potwierdzono:

- instalacja: `D:\Projekty Codex\AMC Python`;
- rewizja źródłowa paczki: `4c8fceda738afd0163040a400150007d16f8409c`;
- identyfikator paczki: `faef4e7f`;
- etykieta użytkowa: `26.10.2026, 14:01`;
- profil: `test`;
- kanał aktualizacji: `test`;
- paczka miała `sourceDirty=false`;
- po zakończeniu aktualizatora uruchomiło się okno `AMC Test — 26.10.2026, 14:01`.

Nie budowano ani nie instalowano systemowego instalatora AMC Test w ramach
REL-003.

## Usunięta instalacja WPF

Usunięto wyłącznie starą instalację WPF:

- katalog: `C:\Users\micha\AppData\Local\Programs\AMC`;
- początkowy rozmiar: 278 563 974 bajty;
- deinstalator zakończył się kodem `0`;
- po deinstalatorze usunięto 47 565 480 bajtów pozostawionych bibliotek i cache;
- usunięto stary skrót `C:\Users\micha\Desktop\AMC.lnk`;
- usunięto stare menu Start `...\Programs\AMC`;
- zachowano skróty pulpitu i menu Start `AMC Test`;
- natychmiast po operacji AMC Test nadal działał.

Usunięcie jest trwałe. Profil użytkownika, bazy biblioteki, poświadczenia oraz
instalacja `D:\Projekty Codex\AMC Python` nie były celem operacji.

## Oczyszczenie artefaktów starego repozytorium

W katalogu `D:\Projekty Codex\Accessible Multimedia Controller` usunięto 13
odtwarzalnych katalogów `bin`, `obj` i `wyniki-testow\temp-alpha424`.

- odzyskano 822 774 251 bajtów;
- zachowano źródła i katalog `.git`;
- po późniejszej jawnej zgodzie użytkownika trwale usunięto katalog `publish`
  z instalatorami 424–427 i odzyskano dalsze 1 783 765 696 bajtów;
- usuniętych katalogów kompilacji i testów nie można odzyskać, ale można je
  odtworzyć ze źródeł.

Z kanonicznego repozytorium usunięto również trzy czyste, odłączone worktree
testowe alpha 425 spod `.test-tmp`, odzyskując 132 014 259 bajtów. Łącznie ze
starą instalacją WPF wszystkie operacje REL-003 odzyskały 3 016 118 180 bajtów.

Nie usunięto całego starego repozytorium. Kontrola wykazała:

- jeden lokalny commit przed `origin/main`;
- 231 zmienionych lub nieśledzonych ścieżek;
- tylko 1 plik identyczny z bieżącym worktree;
- 87 plików o innej treści;
- 143 pliki bez odpowiednika w bieżącym worktree.

Przed usunięciem repozytorium potrzebna jest jawna archiwizacja lub
udokumentowane odrzucenie tych różnic. Nie wolno usuwać ich zbiorczo jako
„już przepisanych”, dopóki nie zostanie to udowodnione dla każdej grupy.

## Oczyszczenie lokalnych gałęzi AMC Python

Punktem odniesienia był commit `24615e0a89d590ecaca06b2831719a1e612a7c81`
gałęzi `integration/sonos-broker-20261024`.

Usunięto cztery nieużywane gałęzie, których końce są przodkami bieżącej linii:

- `hermes/wx-session-options-final-20261007` — `ec1d9ffc`;
- `integracja/sonos-wiim-20261014` — `17901f41`;
- `integracja/wxpython-sonos-tidal-20261008` — `dcd37ffd`;
- `task/youtube-descriptions` — `f8668937`.

Usunięto sześć nieużywanych gałęzi rozbieżnych topologicznie, dla których
`git cherry` potwierdził brak choćby jednego unikalnego patcha względem
bieżącej linii:

- `task-development-dependencies` — `d591f8d1`;
- `task-development-spotify-bundle` — `a03cdb0a`;
- `task-shift-f2-real-rename` — `45cbaeb3`;
- `task-speaker-navigation-search` — `a6adc391`;
- `task-spotify-readonly-litehost` — `134c0657`;
- `task-spotify-session-model` — `22631499`.

### Korekta z 26.10.2026: audyt i decyzja dotycząca pozostałych gałęzi

Ten wpis zastępuje wcześniejsze ustalenie, że wszystkie pozostałe 18 gałęzi
wymagają dalszego zachowania. Porównano je z commitem
`404b6919a019eb50206b4f55557bafdaebc57e48`, sprawdzono unikalne patche,
odpowiedniki funkcjonalne w bieżącej linii, stan worktree oraz obecność kopii
zdalnych. Użytkownik jawnie wskazał do usunięcia 15 pozycji:

- `codex/item-actions-20261016` — `b43163f1`;
- `integracja/sonos-wiim-parity-20261014` — `b0311bdb`;
- `integration/amc-test-20261023-late` — `aadfb4ca`;
- `local/update-build-identity-20261014` — `bd6e76ca`;
- `public/release-line` — `670870d4`;
- `task-global-shortcuts-history` — `56e4296a`;
- `task/frontier-odkrywanie` — `bd92d123`;
- `task/podcasty-tyflo` — `357fccbf`;
- `task/spotify-rozdzialy` — `719e57ed`;
- `task/stabilnosc-okna` — `e932e418`;
- `task/youtube-google-login` — `879aa355`;
- `task/youtube-import-nvda` — `a1581e35`;
- `task/youtube-playlists` — `e0d4f931`;
- `task/youtube-refresh-fairness` — `05621539`;
- `youtube/audit-fixes-20261014` — `2d632946`.

Przed usunięciem potwierdzono brak zmian śledzonych we wszystkich powiązanych
worktree. Dziewięć starych worktree usunięto. Trzy z nich zawierały wyłącznie
odtwarzalne katalogi `.test-output`; łącznie usunięte katalogi zajmowały około
2964 MiB. Nie zostały przeniesione do Kosza i nie można ich odzyskać zwykłym
przywróceniem, ale wyniki kompilacji można ponownie wytworzyć ze źródeł.

Główny katalog `D:\Projekty Codex\AMC - integracja wxPython` zachowano wraz z
jego `.test-output` i `.test-tmp`; odłączono go tylko od usuniętej gałęzi i
ustawiono na commit `404b6919`. Bieżąca instalacja `D:\Projekty Codex\AMC Python`,
profil użytkownika, biblioteki i poświadczenia nie były celem operacji.

Po pierwszym etapie pozostały dokładnie trzy gałęzie lokalne:

- `integration/sonos-broker-20261024` — bieżąca linia AMC Test;
- `integracja/search-completion-20261014` — tymczasowe zabezpieczenie starszych
  wariantów wyszukiwania i aktualizacji;
- `local/shift-f2-release-20261015` — tymczasowe zabezpieczenie kilku
  niezależnych eksperymentów. Samo Shift+F2 ma już odpowiedniki w bieżącej
  linii; dalszego rozstrzygnięcia wymagają przede wszystkim nieprzeniesione
  warianty obsługi playlist TIDAL i identyfikacji uruchomionej kompilacji.

### Korekta późniejsza z 26.10.2026: usunięcie gałęzi Shift+F2

Po wyjaśnieniu, że wszystkie poprawki samego Shift+F2 działają już w bieżącej
aplikacji, użytkownik zdecydował o usunięciu również
`local/shift-f2-release-20261015`. Ta decyzja zastępuje wcześniejsze tymczasowe
zachowanie tej gałęzi wraz ze starszymi eksperymentami playlist TIDAL i
identyfikacji uruchomionej kompilacji.

Przed usunięciem ponownie potwierdzono brak zmian śledzonych. Powiązany worktree
`D:\Projekty Codex\AMC worktrees\shift-f2-release-20261015` zawierał wyłącznie
odtwarzalne `.test-output` i `.test-tmp`; jego usunięcie odzyskało około
1239,5 MiB. Łącznie dziesięć worktree usuniętych podczas audytu 18 gałęzi
zajmowało około 4203 MiB, czyli 4,1 GiB.

Pozostały dokładnie dwie gałęzie lokalne:

- `integration/sonos-broker-20261024` — bieżąca linia AMC Test;
- `integracja/search-completion-20261014` — tymczasowe zabezpieczenie starszych
  wariantów wyszukiwania i aktualizacji.

Żadna z tych dwóch gałęzi nie ma upstreamu, tagu ani kopii zawierającej jej
koniec na GitHubie. Nie zmieniono żadnej gałęzi zdalnej.

### Usunięcie starych kandydatów Frontier z 26.10.2026

Na życzenie użytkownika sprawdzono dwa odłączone worktree utworzone podczas
wcześniejszego odbioru Frontier:

- `D:\Projekty Codex\AMC - kandydat Frontier` — commit `19ae6089`,
  `fix(frontier): wykryj radio UNDOK i uprosc konfiguracje` z 21.10.2026;
- `D:\Projekty Codex\AMC - kandydat Frontier CtrlF5` — commit `86727573`,
  `fix(frontier): skanuj automatycznie tylko pusta sesje` z 21.10.2026.

Oba commity są przodkami bieżącej linii i nie mają wobec niej unikalnych
commitów. Worktree nie zawierały zmian śledzonych, a jedynymi nieśledzonymi
pozycjami były odtwarzalne katalogi `.test-output`. Uruchomiony AMC Test został
niezależnie zidentyfikowany pod `D:\Projekty Codex\AMC Python`, więc nie
korzystał z żadnego kandydata.

Oba worktree trwale usunięto i wykonano `git worktree prune`. Odzyskano około
728 MiB. Łącznie audyt pozostałych gałęzi i kandydatów odzyskał około 4931 MiB,
czyli 4,8 GiB. Nie zmieniono kodu Frontier, instalacji AMC Test ani danych
urządzenia.

## Archiwizacja źródeł WPF na GitHubie

26.10.2026 użytkownik zdecydował o zachowaniu starego WPF wyłącznie jako
archiwum możliwe do wyjątkowego odkopania. W repozytorium
`https://github.com/michalkasperczak/AMC` opublikowano:

- gałąź `archive/wpf-final-20261026`;
- oznaczony tag `archive-wpf-final-20261026`;
- końcowy commit `c59cfc6c56deb8b4b2c43ec2f8e048558123e46f`.

Snapshot objął jeden wcześniejszy lokalny commit oraz 181 przygotowanych
ścieżek: 84 zmodyfikowane, 96 wcześniej nieśledzonych i nową notę archiwalną.
Przed publikacją sklasyfikowano pliki, sprawdzono wzorce sekretów oraz
potwierdzono brak kluczy prywatnych, nowych tokenów i plików poświadczeń.
Pliki `.p8`, `.jwt` i `client_secret*.json` są ignorowane i nie występowały w
snapshotcie.

Zdalny `main` przed i po operacji pozostał na commicie
`1f5dccb6e0e14fab31d3d492459b820eed157456`. Gałąź i rozwinięty tag zweryfikowano
na GitHubie jako wskazujące dokładnie commit `c59cfc6c`. Nie utworzono pull
requesta ani wydania GitHub Releases.

Nie wykonano nowej kompilacji, testów ani instalacji WPF. Publikacja potwierdza
jedynie kompletne archiwum źródeł; nie jest dowodem działającego wydania.
Lokalny katalog repozytorium WPF pozostaje na razie zachowany. Bieżąca
instalacja AMC Test i równoległe zadanie mechanizmu aktualizacji nie zostały
zmienione.

## YouTube bez ponownego logowania Google

W kodzie istnieją dwa niezależne mechanizmy:

1. Konto Google odczytuje listę subskrypcji i playlist z YouTube. Synchronizacja
   jest jednokierunkowa `YouTube -> AMC`, najpierw pokazuje plan, a zapis do
   Biblioteki wymaga osobnego działania użytkownika. Nie usuwa dotychczasowych
   źródeł i niczego nie wysyła do YouTube.
2. Kanał zapisany już w Bibliotece jest zwykłym publicznym źródłem AMC.
   Odświeżanie korzysta z publicznego adresu kanału, `yt-dlp` i publicznego
   feedu; nie wymaga tokenu Google, ciasteczek przeglądarki ani logowania konta.

Stan rzeczywistej bazy `podcasts.db` sprawdzono wyłącznie zbiorczo, bez
odczytywania nazw kanałów i bez dostępu do poświadczeń:

- 287 aktywnych zapisanych kanałów YouTube;
- 284 mają zapis co najmniej jednego wcześniejszego odświeżenia;
- odstęp automatycznego odświeżania YouTube: 60 minut;
- maksymalnie 5 należnych źródeł w jednym przebiegu;
- interfejs co minutę zleca hostowi sprawdzenie, które źródła są należne.

Wniosek: użytkownik nie musi teraz ponownie logować się do Google, aby AMC
odświeżał już zapisane kanały. Bez logowania AMC nie odczyta nowych subskrypcji
dodanych później na koncie YouTube. Nowe logowanie publicznego klienta z PKCE
pozostaje osobnym przyszłym zadaniem.

## Następny bezpieczny etap

1. Rozstrzygnąć, czy z jednej tymczasowej gałęzi wyszukiwania należy odzyskać
   pojedyncze rozwiązania, czy świadomie usunąć ją po opublikowaniu bieżącej
   linii.
2. Po ostatecznej decyzji usunąć lokalny katalog WPF, korzystając z
   zweryfikowanej gałęzi i tagu GitHub jako punktu odzyskania.
3. Opublikować kanoniczną linię Pythona, nie zmieniając archiwalnego WPF w
   równoległą linię rozwoju.

