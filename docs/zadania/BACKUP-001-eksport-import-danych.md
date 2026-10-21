# BACKUP-001 — eksport i import danych AMC

Status: W trakcie — wdrożone i zweryfikowane w źródłach; czeka na instalację
kandydata oraz ręczny odbiór NVDA

## Cel

AMC ma tworzyć bezpieczną pełną kopię bieżącego profilu oraz osobne kopie
ustawień, Biblioteki, playlist AMC, Radia, harmonogramów, Podcastów i YouTube
oraz ustawień urządzeń i usług. Import ma rozpoznawać zakres z pliku,
walidować całość przed zapisem i zastępować wyłącznie zawarte działy.

Historyczne AMC WPF służy jako wzorzec zgodności dla plików
`*.amcbackup.json`, `*.amcsettings.json` i map klawiatury. Nie jest miejscem
wdrożenia tej poprawki.

## Kryteria akceptacji

- pełna kopia obejmuje stan rdzenia C#, obie bazy SQLite i prywatny stan
  interfejsu wxPython;
- pojedynczy eksport nie zawiera danych z niewybranego działu;
- import pojedynczego działu nie zmienia pozostałych danych;
- Radio i harmonogramy są niezależnymi zakresami;
- starsza pełna kopia historycznego AMC pozostaje możliwa do importu;
- zapis pliku eksportu jest atomowy, a nieudany import przywraca wcześniejszy
  stan profilu;
- hasła, tokeny i dane logowania nie trafiają do pliku;
- menu, paleta poleceń i pomoc korzystają z tych samych dwóch poleceń;
- wybór zakresu ma wyłącznie jawne etykiety użytkowe i przewidywalny fokus.

## Materiał do dokumentacji użytkownika

Projekt instrukcji użytkownika:

1. Otwórz **Ustawienia > Eksportuj dane AMC…** albo uruchom to samo polecenie
   z palety `Ctrl+Shift+K`.
2. Na liście wybierz pełną kopię albo jeden zakres. Enter zatwierdza, Escape
   anuluje. Pełna kopia jest zaznaczona przy każdym otwarciu.
3. Wskaż plik. Po sukcesie AMC poda nazwę, liczby elementów i potwierdzi, że
   nie zapisał haseł ani tokenów.
4. Przy imporcie wybierz dowolny obsługiwany plik. AMC sam rozpozna zakres,
   powie, co zostanie zastąpione, zachowa inne działy i poprosi o zgodę.
5. Po udanym imporcie uruchom AMC ponownie. W razie błędu zapis jest wycofywany
   z pełnej kopii ratunkowej.

Projekt opisu zmian:

- Dodano pełną kopię profilu i siedem niezależnych działów danych.
- Radio i harmonogramy można przenosić osobno.
- Import nie zeruje działów nieobecnych w pliku i zachowuje zgodność ze starą
  pełną kopią AMC.
- Pliki są zapisywane atomowo, prywatna sekcja interfejsu ma kontrolę
  integralności, a przed importem powstaje kopia ratunkowa.
- Hasła, tokeny, pliki audio, nagrania i pobrane odcinki nie są eksportowane.

Tekst jest projektem do korekty i zatwierdzenia użytkownika; nie został
opublikowany.

## Uzasadnienie i decyzje

- 2026-10-21: użytkownik poprosił o eksport i import wszystkiego oraz osobno
  konfiguracji, Radia, harmonogramów, Biblioteki i playlist. Wskazał
  historyczne AMC jako możliwe źródło wcześniejszego rozwiązania.
- Zachowujemy osobny eksport playlist pojedynczej sesji. Kopia działu
  „Playlisty AMC” zabezpiecza wszystkie lokalne kontenery playlist programu;
  nie kopiuje plików audio ani zdalnych playlist należących do konta usługi.
- Jeden plik niesie jawny manifest zakresów. Import nie pozwala, aby brakujący
  dział został potraktowany jak pusty i skasował bieżące dane.
- Rozwiązanie pierwotnego AMC zachowano jako format zgodności pełnej kopii.
  Stary program nie miał bezpiecznego manifestu osobnych działów, dlatego
  podział jest nowym rozszerzeniem, a nie kopiowaniem nieistniejącej funkcji.
- Lista zakresów ma osiem stałych, jawnych polskich etykiet. W modelu pozostają
  stabilne identyfikatory, ale nie są przekazywane do nazwy dostępnej NVDA.

## Testy i wynik

- `pytest test_full_backup.py test_host_client.py test_release_profile.py`:
  57 testów — zaliczone.
- `pytest test_gui_logic.py test_state_store.py test_command_palette.py
  test_shortcuts.py`: 140 testów — zaliczone.
- `dotnet run ... -- --profile-backup`: testy magazynu C#, rozdzielenia Radia
  i harmonogramów, zgodności pełnej kopii oraz odrzucenia złego zakresu —
  zaliczone.
- `dotnet build AccessibleMediaController.LiteHost.csproj -c Release
  --no-restore`: kompilacja hosta — zaliczona, 0 ostrzeżeń i 0 błędów.
- `pytest test_fresh_public_profile_host_e2e.py`: rzeczywisty proces LiteHost,
  pełny cykl eksport–import na świeżym profilu — 1 test zaliczony.
- Pełna regresja `pytest tests -q`: 1940 testów zaliczonych, 110 świadomie
  pominiętych, 11 podtestów zaliczonych.
- Pełny zestaw `AccessibleMediaController.Core.SmokeTests`: zaliczony, w tym
  nowy `ProfileBackupTests`.
- Końcowy zestaw po przeglądzie bezpieczeństwa: 58 testów kopii, protokołu,
  parytetu poleceń i menu — zaliczone; końcowy E2E hosta — 1 zaliczony.

## Znane ograniczenia

- Żywy odbiór NVDA nastąpi po zbudowaniu i zainstalowaniu kandydata; testy
  automatyczne nie są dowodem rzeczywistej mowy czytnika.
- Kopia danych nie zawiera plików audio, nagrań ani pobranych odcinków.
- Eksport playlist AMC zabezpiecza lokalne kontenery programu. Eksport
  pojedynczej playlisty sesji i zdalne playlisty kont pozostają osobnymi
  mechanizmami.

## Wersja i commit

- Kod i pełna regresja: commit `3ed70f7d` (`feat(backup): dodaj bezpieczne
  kopie profilu`).
- Build hosta Release: udany; nie jest to dowód instalacji.
- Instalacja i publikacja: nie wykonano.
