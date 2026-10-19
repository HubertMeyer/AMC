# Roboczy indeks materiału do instrukcji i opisu zmian — 19 października 2026

## Status dokumentu

To jest indeks roboczy wygenerowany z zapisów zadań. Nie jest gotową
instrukcją ani opublikowanym opisem wydania. Wymaga korekty i zatwierdzenia
użytkownika. Nie zmienia statusu ręcznego odbioru NVDA poszczególnych funkcji.

## Punkt odniesienia wersji

- Najnowsza zainstalowana i uruchomiona paczka AMC Test:
  `2026.10.19-6c79bdd32904b9468b07489e79da715de512d3e0-972b46e1`.
- Fundament profili AMC12 istnieje później w źródłach i testach, ale nie został
  skompilowany, zainstalowany ani opublikowany.
- Nie wykonano publikacji na GitHubie ani publicznego wydania.

## Materiał do przyszłej instrukcji użytkownika

1. Kopiowanie nazwy i NVDA — `Ctrl+C`, jeden komunikat „Skopiowano nazwę”,
   zgodność z NVDAExtensionGlobalPlugin. Ręczny odbiór mowy i schowka nadal
   otwarty. Źródło:
   [NVDA-001-opoznienie-ctrl-c.md](NVDA-001-opoznienie-ctrl-c.md), sekcja
   „Materiał do dokumentacji użytkownika”.
2. Wyszukiwanie i Biblioteka — `Ctrl+Shift+L` w modalnych wynikach YouTube,
   Spotify i TIDAL; różnica między kanałem, podcastem, filmem i odcinkiem;
   pozostanie w wyszukiwarce oraz powrót do odświeżonej Biblioteki po
   `Escape`. Źródło:
   [SEARCH-001-youtube-biblioteka-komunikaty.md](SEARCH-001-youtube-biblioteka-komunikaty.md).
3. Nagrywane pliki i historia — krótkie widoki `Alt+R`, `Alt+Shift+R`,
   oddzielna pamięć zaznaczenia oraz szczegóły bitrate, wielkości i folderu pod
   lewą strzałką, również w `Ctrl+H`. Źródło:
   [AMC02-listy-nagrywania-i-historii.md](AMC02-listy-nagrywania-i-historii.md).
4. Harmonogramy — znaczenie lewej i prawej strzałki, Spacji, Enter i
   `Ctrl+D`; segmentowe wpisywanie daty, czasu i czasu trwania; powrót fokusu i
   komunikaty NVDA. Źródło:
   [SCHED-001-edytor-i-klawisze-harmonogramow.md](SCHED-001-edytor-i-klawisze-harmonogramow.md).
5. Playlisty Spotify — `Ctrl+P`, `Ctrl+Shift+P`, jedna lub wiele playlist,
   tworzenie playlisty prywatnej lub publicznej oraz uczciwe wyniki częściowe.
   Ręczny odbiór konta nadal otwarty. Źródło:
   [AMC08-playlisty-spotify.md](AMC08-playlisty-spotify.md).
6. Zakładki, nazwane zakładki, rozdziały i historia — rozróżnienie danych oraz
   skróty `B`, `Ctrl+Shift+B`, `Shift+Page Up/Down`,
   `Ctrl+Shift+Page Up/Down`, `Ctrl+Shift+lewo/prawo`, `Alt+lewo/prawo` i
   `Alt+góra/dół`. Źródło:
   [AMC04-nawigacja-zakladki-rozdzialy-historia.md](AMC04-nawigacja-zakladki-rozdzialy-historia.md).
7. Odtwarzany element na listach — znaczenie etykiet „Odtwarzane” i
   „Wstrzymane”, zachowanie szczegółów wiersza i ograniczenia stanu urządzeń
   Sonos/WiiM. Źródło:
   [AMC05-odtwarzany-element-na-listach.md](AMC05-odtwarzany-element-na-listach.md).
8. Time Shift Radia — `Home` przechodzi na początek, `End` wraca do transmisji
   na żywo i tempa normalnego; `NVDA+End` pozostaje skrótem NVDA. Źródło:
   [AMC13-timeshift-end-na-zywo.md](AMC13-timeshift-end-na-zywo.md).
9. Sortowanie Biblioteki Podcastów i YouTube — trzy tryby, trwałość wyboru,
   zachowanie zaznaczenia oraz wspólne powierzchnie poleceń. Źródło:
   [POD-001-sortowanie-biblioteki-zrodel.md](POD-001-sortowanie-biblioteki-zrodel.md).
10. Menedżer sesji — `Ctrl+Shift+S`, Enter, Spacja,
    `Alt+strzałka w górę/dół`, „Konfiguruj…”, zwarta numeracja `Ctrl+1–9` i
    zabezpieczenia przed wyłączeniem aktywnej lub ostatniej sesji. Źródło:
    [AMC09-menedzer-sesji.md](AMC09-menedzer-sesji.md).
11. AMC Test i przyszły publiczny AMC — osobne dane i możliwości, publiczne
    sesje Pliki lokalne, Radio, Podcasty i YouTube oraz WiiM, bez reklamowania
    ukrytych usług w menu, pomocy i palecie. Ten rozdział opisuje na razie kod,
    nie dostępną instalację. Źródło:
    [AMC12-profile-wydania-publicznego-i-testowego.md](AMC12-profile-wydania-publicznego-i-testowego.md).

## Materiał do przyszłego opisu zmian

- Poprawiono kolejność i jednoznaczność komunikatów NVDA po kopiowaniu i po
  zmianach Biblioteki z wyszukiwarki.
- Uporządkowano listy nagrywania, historię nagrań i szczegóły plików bez
  powtarzania stacji, harmonogramu i folderu w zwykłym wierszu.
- Przebudowano dostępny edytor harmonogramów oraz nawigację daty i czasu.
- Dodano zarządzanie natywnymi playlistami Spotify, bez obiecywania
  nieobsługiwanego odtwarzania całych playlist.
- Ujednolicono zakładki, nazwane zakładki, rozdziały i historię we wspólnym
  katalogu poleceń.
- Dodano wiarygodne oznaczenie odtwarzanego elementu oraz przywrócono `End` na
  żywo w Time Shifcie.
- Dodano trwałe sortowanie zbiorczej Biblioteki Podcastów i YouTube.
- Dodano Menedżer sesji i dynamiczne, zwarte skróty `Ctrl+1–9`.
- Rozpoczęto fundament dwóch izolowanych profili wydania; ta ostatnia zmiana
  nie jest jeszcze częścią zainstalowanej paczki.

## Odbiory i ograniczenia do zachowania w instrukcji

- Nie oznaczać ręcznych testów NVDA jako zaliczonych, dopóki użytkownik ich nie
  potwierdzi.
- Nie przedstawiać testów atrap Spotify/TIDAL jako próby prawdziwego konta.
- Nie przedstawiać kodu AMC12 jako kompilacji, instalacji albo wydania.
- Nie obiecywać publicznego Sonosa przed działającym brokerem HTTPS i odbiorem
  z zewnętrznym kontem.
- Nie opisywać logowania YouTube; `YT-001` jest odłożone do czasu po
  instalatorze i pierwszych stabilnych wydaniach.
- Pomoc `Ctrl+F1`, pełna pomoc klawiatury, menu i paleta `Ctrl+Shift+K` mają
  być opisywane jako różne powierzchnie jednego katalogu poleceń, a nie jako
  niezależne listy funkcji.

## Następny krok redakcyjny

Po ręcznym odbiorze użytkownika złożyć z powyższych źródeł dwa osobne teksty:

1. instrukcję funkcji według codziennych czynności użytkownika;
2. opis zmian według wersji faktycznie zbudowanej i zainstalowanej.

Żadnego z tych tekstów nie publikować automatycznie.
