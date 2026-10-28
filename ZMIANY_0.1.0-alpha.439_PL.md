# AMC Public 0.1.0-alpha.439 — projekt opisu zmian

> Projekt do korekty i zatwierdzenia użytkownika. Nie jest automatycznie
> publikowaną instrukcją ani dowodem instalacji.

AMC Public powstaje z najnowszej bazy AMC Test i zachowuje jej nowe funkcje,
w tym polski i angielski interfejs, konfigurowalne skróty oraz poprawki
dostępności. Różnice wynikają wyłącznie z jawnego profilu Public.

## Najważniejsze różnice profilu Public

- osobna instalacja, proces, kanał stabilny, ustawienia, pamięć podręczna,
  logi i magazyn poświadczeń;
- brak logowania Google do YouTube i brak konfiguracji OAuth Google w paczce;
- brak prywatnych sesji Spotify i TIDAL oraz ich modułów i hosta Spotify;
- zachowane sesje Pliki lokalne, Radio, Podcasty i YouTube, WiiM oraz Sonos;
- w historii rozpoznanych utworów publiczne wyszukiwanie Spotify/TIDAL na
  stronie zamiast przejścia do tych usług wewnątrz AMC;
- zachowany publiczny kanał aktualizacji `stable`, niezależny od częstych
  wydań AMC Test.

## Odbiór z NVDA

Do ręcznej kontroli pozostają: początkowy fokus `Ctrl+Alt+S`, prawa strzałka,
Enter, `Ctrl+Enter`, `Ctrl+Shift+C`, Escape, powrót fokusu i ponowne otwarcie.
NVDA powinien czytać wyłącznie użytkowe nazwy działań i jednoznacznie odróżniać
łącze wyszukiwania od dokładnego łącza do utworu.

## Stan techniczny

- testy celowane Pythona: 109/109 zaliczone;
- testy Launchera i aktualizatora: 37/37 zaliczone;
- pełna regresja GUI: niepowtarzana dla tej różnicy profilu;
- paczka Public `e44af269`: zbudowana, kontrola integralności i cichy start
  zaliczone;
- instalator `AMC-Public-2026-10-28-2109.exe`: zbudowany, skan sekretów
  zaliczony i opublikowany w stabilnym wydaniu `public-2026.10.28.2109`;
- instalacja i ręczny odbiór z NVDA: niewykonane; lokalnego AMC nie
  zmieniano.
