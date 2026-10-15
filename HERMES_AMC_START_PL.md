# AMC — punkt startowy dla zewnętrznego Hermesa

Ten plik jest przeznaczony dla Hermesa działającego na osobnym komputerze i
połączonego z Telegramem. Nie zakłada, że ma on dostęp do osobistych
umiejętności, pamięci ani historii czatów Codex. Przed rozpoczęciem pracy Hermes
ma odczytać ten plik oraz dokumenty wskazane poniżej bezpośrednio z projektu.

## Właściwe miejsca

- Kanoniczne repozytorium nowego AMC Python:
  `D:\Projekty Codex\AMC - integracja wxPython`.
- Użytkowa instalacja:
  `D:\Projekty Codex\AMC Python\AMC.exe`.
- Trwałe środowisko i cache zależności:
  `D:\Projekty Codex\AMC - zależności`.
- Stare AMC WPF:
  `D:\Projekty Codex\Accessible Multimedia Controller`.
  Jest wyłącznie źródłem historycznych rozwiązań technicznych. Nie wolno tam
  wdrażać nowych poprawek, budować aktualizacji ani uruchamiać go jako wersji
  użytkowej.

## Obowiązkowy odczyt przed pracą

W tej kolejności przeczytaj:

1. `AGENTS.md` — trwałe zasady projektu, dostępności i zachowania wspólnych
   funkcji.
2. `AMC_PYTHON_STAN_2026-10-10_PL.md` — architektura i szerszy stan aplikacji.
3. `PRZEKAZANIE_2026-10-14_WTOREK_PL.md` — ostatnie przekazanie prac.
4. `ZALEZNOSCI_AMC_STAN_PL.md` — przygotowane, trwałe środowisko kompilacji.

Następnie wykonaj odczytowo `git status --short`, `git branch --show-current`,
`git log -n 12 --oneline` i `git worktree list`. Nie porządkuj automatycznie
brudnego drzewa i nie cofaj zmian, których sam nie utworzyłeś.

## Stan rozdzielonych prac 15 października 2026

- Główne repozytorium jest na gałęzi
  `integracja/wxpython-sonos-tidal-20261008`. Bieżący HEAD zawiera ten plik
  przekazania, a jego ostatnim commitem kodu jest `8c5b61e5`. W drzewie
  roboczym znajdują się niezakończone, niezacommitowane zmiany implementacji i
  testów Spotify. Trzeba je zachować.
- Zachowane worktree wydania:
  `D:\Projekty Codex\AMC worktrees\shift-f2-release-20261015`, gałąź
  `local/shift-f2-release-20261015`, HEAD dokumentacji `b50fffbd`.
- Ostatni kompletnie przetestowany i zainstalowany kod pochodzi z commita
  `90e5f750`; pełny przebieg zakończył się wynikiem 1571 testów zaliczonych,
  110 pominiętych testów historycznych i 11 zaliczonych podtestów. Kompilacja
  miała etykietę
  `2026.10.15-90e5f75095451697e59ead84fb036b54f670322b-e95d4c4d`.
- Nowszy commit `b50fffbd` dodaje dokumentację modułowych sesji, ale sam nie
  jest źródłem zainstalowanej paczki.
- Przed następną kompilacją trzeba kontrolowanie zintegrować poprawki wydania z
  rozpoczętą pracą Spotify. Nie wykonuj ślepego merge, rebase ani cherry-pick
  na brudnym drzewie.

## Kierunek implementacji Spotify

Używaj modelu GPT-6.1 Sol. Migracja nie wymaga Astry, ponieważ mechanizm
Spotify już działał i ma sprawdzone źródło odniesienia. Astra może być później
przydatna do rzeczywiście nowej lub niejednoznacznej architektury TIDAL-a albo
Apple Music.

Spotify powstaje z dwóch świadomie różnych wzorców:

1. Ze starego AMC WPF bierz sprawdzony mechanizm techniczny: LibreSpot,
   uwierzytelnianie, protokół, uruchamianie hosta i tor audio. Najpierw ustal,
   które elementy da się przenieść bez zmiany zachowania silnika.
2. Z aktualnego TIDAL-a w AMC Python bierz cały kontrakt interfejsu: bibliotekę,
   wyszukiwanie, prawdziwy typ wyniku, relacje wykonawca–album–utwór,
   odtwarzanie, playlisty, historię, sortowanie, Enter, Escape, strzałki,
   skróty, komunikaty, zachowanie fokusu i etykiety dla NVDA.

Nie kopiuj ze starego interfejsu błędów takich jak podwójny Enter, powtarzane
komunikaty, nieprawidłowa lewa lub prawa strzałka, wyciek identyfikatorów albo
odrębna obsługa wspólnych skrótów. `Ctrl+H` i pozostałe skróty globalne mają
działać w Spotify tak samo jak w innych sesjach. Każdą wspólną funkcję pokryj
testem kontraktowym dla TIDAL-a i Spotify, a zmienione listy sprawdź również z
NVDA. Ograniczenie API ma być jawną różnicą możliwości, nie pozornym sukcesem.

## Bezpieczne budowanie, instalacja i uruchamianie

Zewnętrzny Hermes nie może zakładać, że widzi osobistą umiejętność Codex
`safe-application-builds`. Obowiązują więc bezpośrednio poniższe reguły:

- przed zamknięciem, instalacją lub restartem sprawdź procesy AMC, stan
  nagrywania i pliki `.amc-partial`; nie przerywaj nagrania;
- korzystaj z przygotowanego środowiska w
  `D:\Projekty Codex\AMC - zależności` i istniejących skryptów repozytorium;
- katalogi `.test-output`, `.test-tmp`, `publish` i worktree są zapleczem, a
  nie instalacją użytkową;
- instaluj i uruchamiaj wyłącznie
  `D:\Projekty Codex\AMC Python\AMC.exe`;
- po instalacji sprawdź manifest, commit źródłowy, etykietę kompilacji, sumy
  paczki, tytuł okna oraz to, czy działa tylko jeden logiczny stos AMC;
- nie ogłaszaj sukcesu na podstawie samego zakończenia kopiowania plików;
- nie publikuj kodu ani paczki na GitHubie bez osobnej, aktualnej zgody
  użytkownika dotyczącej konkretnego stanu.

## Moduły i sesje

Docelowo użytkownik może włączać, wyłączać i ustawiać kolejność osobnych sesji
lub usług. Wyłączenie modułu nie usuwa konta, biblioteki ani historii. Skróty są
oddzielną konfiguracją; konflikt albo wyłączona sesja nie mogą powodować
cichego przypisania klawisza do innej usługi. Model danych, komendy i reguły
dostępności mają pozostać wspólne, a różnice dostawcy należą do adaptera.

## Zakończenie każdej sesji pracy

Podaj użytkownikowi i zapisz w dokumentacji: używaną ścieżkę, gałąź, commit
bazowy i końcowy, pozostawione niezacommitowane pliki, uruchomione testy z
wynikami oraz dokładną tożsamość zbudowanej lub zainstalowanej wersji. Jeżeli
drugi agent albo użytkownik pracuje równolegle, nie instaluj i nie scalaj bez
sprawdzenia aktualnego stanu.
