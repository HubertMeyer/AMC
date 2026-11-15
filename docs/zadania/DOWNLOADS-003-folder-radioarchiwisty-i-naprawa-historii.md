# DOWNLOADS-003 — folder Radio Archiwisty i naprawa Historii pobrań

- Data zgłoszenia i korekty: 15.11.2026 po 18:00.
- Produkt: AMC Test, aplikacja wxPython. Wersja: `0.1.0-alpha.510`.
- Stan: źródła i testy celowane gotowe. Pakiet, instalator, instalacja,
  publikacja i próba NVDA mają osobne wyniki poniżej.

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
- Pakiet i instalator: oczekują na przygotowanie i weryfikację.
- Instalacja lokalna: nieodbyta. Publikacja GitHub: nieodbyta.
- NVDA: do sprawdzenia fokus po otwarciu Ctrl+J, Enter, obie operacje
  schowka, wybór folderu i odczyt wartości, wskazanie przeniesionego
  pliku, anulowanie, powrót fokusu i ponowne otwarcie.

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
