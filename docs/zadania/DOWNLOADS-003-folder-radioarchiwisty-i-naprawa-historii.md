# DOWNLOADS-003 — folder Radio Archiwisty i naprawa Historii pobrań

- Data zgłoszenia i korekty: 15.11.2026 po 18:00.
- Produkt: AMC Test i AMC Public, aplikacja wxPython. Wersja: `0.1.0-alpha.510`.
- Stan: źródła, testy celowane, obie paczki, instalatory i wydania GitHub
  gotowe. Lokalna instalacja i próba NVDA nieodbyte.

## Zachowanie i decyzje

- Ustawienia → Radio → „Pobieranie Radio Archiwisty” zawierają folder i
  przycisk wyboru. Osobny folder jest opcjonalny. Bez niego Radio Archiwista
  korzysta z aktualnego folderu pobierania Podcastów. Zarówno `Ctrl+D`, jak
  i pobieranie fragmentu `Ctrl+Shift+D`, stosują tę samą regułę.
- Dotychczasowy katalog w danych aplikacji pozostaje odczytywany przez
  Historię pobrań dla starych plików. AMC nie przenosi ich samoczynnie.
- `Ctrl+J` otwiera wspólną Historię pobrań. Enter odtwarza istniejący plik,
  `Ctrl+C` kopiuje zapisaną pełną ścieżkę także dla brakującego wpisu,
  `Ctrl+Shift+C` kopiuje istniejący plik do wklejenia. Nowe polecenie
  „Kopiuj nazwę pobranego pliku” kopiuje samą nazwę. „Wskaż przeniesiony
  pobrany plik” naprawia brakujący wpis przez dialog wyboru pliku.
  Polecenia są w menu, menu kontekstowym, palecie i pomocy, bez nowych skrótów.
- `Shift+F2` w Historii zmienia nazwę fizycznego pliku i aktualizuje jej
  ścieżkę w historii oraz w bazie Podcastów, jeśli to pobrany odcinek.
  Ręczne wskazanie przeniesionego odcinka uzgadnia oba zapisy. Dla
  brakującego pliku operacje wymagające pliku są nieaktywne; zapisaną
  ścieżkę i informacje nadal można odczytać i skopiować.

Decyzja z 15.11.2026 uzupełnia `DOWNLOADS-001` i korektę użytkownika
z 31.10.2026 w `DOWNLOADS-002`. Nie zmienia znaczenia `Ctrl+C` na liście
pobrań. Odrębny folder Radio Archiwisty jest w istniejącej karcie Radio.

Korekta użytkownika z 15.11.2026 zastępuje wcześniejszy plan wydania tylko
AMC Test: poprawka pobierania jest w AMC Test i AMC Public. Test zawiera
również wcześniejsze zmiany Apple Music, a Public nie zawiera Apple Music.
Użytkownik polecił opublikować oba profile na GitHubie i samodzielnie
zaktualizować później swoją instalację Test. Nie instalowano żadnego profilu.

## Dowody i ograniczenia

- Analiza działającego profilu wykazała wpisy pobrań po 18:00 i wpisy,
  których zapisane ścieżki przestały istnieć. Dla jednego pliku Radio
  Archiwisty istnieje plik o nazwie rozszerzonej o prefiks, zgodny czasowo
  i rozmiarem; historia nadal wskazywała dawną nazwę. Innego brakującego
  wpisu nie powiązano pewnie z plikiem, więc danych użytkownika nie
  aktualizowano automatycznie.
- Kod pobierania wideo zgłasza sukces po zwróceniu ścieżki przez komponent
  pobierający. Zgłoszony niedostępny film może wynikać z późniejszej
  zmiany nazwy lub przeniesienia; bez jednoznacznego pliku nie potwierdzono
  tej przyczyny dla tamtego filmu.
- W chwili inspekcji użytkownik korzystał z wyszukiwania TIDAL w AMC.
  Nie przełączano jego sesji ani nie sprawdzano klawiszy w tym oknie.
  Przed instalacją trzeba odczytowo ustalić stan nagrywania.

## Testy i etapy wydania

- 15.11.2026: 73 celowane testy Python przeszły. Obejmują historię,
  schowek, ustawienia, kontrakt hosta, skróty, menu, paletę i pomoc.
- 15.11.2026: kompilacja hosta Release przeszła, 0 ostrzeżeń i 0 błędów.
- 15.11.2026: celowany zestaw protokołu i bazy Podcastów przeszedł.
- Pełna regresja: nieuruchomiona dla tego zadania.
- Paczka Test: 4730 plików, profil Test, Radio Archiwista i Apple Music;
  paczka Public: 3459 plików, profil Public, Radio Archiwista bez Apple
  Music i bez hosta Apple Music. Obie mają `sourceDirty=false`, commit
  `2b6b061db22523ed9cfb66d26e2808b3d7bf00a7`, pełną kontrolę
  integralności i zaliczony ukryty start interfejsu oraz hosta.
- Instalator Test: `AMC-Test-2026-11-15-2036.exe`, 218531931 bajtów,
  SHA-256 `078ce7cddb4461552071192f7d83bc4623d02bac0d2b55e587d5fde41d7f8591`.
  Instalator Public: `AMC-Public-2026-11-15-2040.exe`, 136550658 bajtów,
  SHA-256 `85b24bb9eac43c5bb855a3e8e94771b5804e07f2c3cd5979802646d4e374475f`.
  Oba mają `secretScan=passed`, zgodny profil, commit i wersję.
- Commit źródłowy został wypchnięty na istniejącą gałąź GitHub i
  potwierdzony przez API. Wydania opublikowano i odczytowo sprawdzono:
  `test-2026.11.15.2036` jest wydaniem wstępnym, a
  `public-2026.11.15.2040` zwykłym wydaniem kanału stable. Skrypt
  potwierdził nazwy, rozmiary i stan `uploaded` trzech załączników
  każdego wydania. Lokalne sumy SHA-256 są w opisie i manifestach wydań.
- Lokalna instalacja: nieodbyta na życzenie użytkownika. Działający AMC
  Test pozostaje przy wcześniejszej wersji. Publikacja źródeł i instalatorów
  nie jest dowodem instalacji ani działania klawiszy w NVDA.
- NVDA: do sprawdzenia fokus po otwarciu Ctrl+J, Enter, obie operacje
  schowka, wybór folderu i odczyt wartości, wskazanie przeniesionego
  pliku, anulowanie, powrót fokusu i ponowne otwarcie.

Lokalizacje instalatorów:

- `D:\Projekty Codex\AMC - integracja wxPython\publish\installers\test-alpha510-20261115-downloads\AMC-Test-2026-11-15-2036.exe`
- `D:\Projekty Codex\AMC - integracja wxPython\publish\installers\public-alpha510-20261115-downloads\AMC-Public-2026-11-15-2040.exe`

Wydania GitHub:

- `https://github.com/michalkasperczak/AMC/releases/tag/test-2026.11.15.2036`
- `https://github.com/michalkasperczak/AMC/releases/tag/public-2026.11.15.2040`

## Projekt instrukcji i opisu zmian do korekty użytkownika

Instrukcja: „W Ustawieniach, na karcie Radio, można wybrać folder pobierania
Radio Archiwisty. Jeśli nie zostanie wybrany, audycje i fragmenty trafiają
do folderu pobierania Podcastów. Historię otwiera Ctrl+J. Enter odtwarza
istniejący plik, Ctrl+C kopiuje jego zapisaną ścieżkę, a Ctrl+Shift+C kopiuje
plik do wklejenia. Jeśli po zmianie nazwy lub przeniesieniu wpis pokazuje
brak pliku, wybierz Wskaż przeniesiony pobrany plik.”

Opis zmian: „Radio Archiwista zapisuje nowe pobrania w folderze wybranym
przez użytkownika. Historia pobrań pomaga odnaleźć pliki po zmianie nazwy
lub przeniesieniu i uzgadnia ścieżki po zmianie nazwy w AMC.”
