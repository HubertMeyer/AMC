# AMC 0.1.0-alpha.429 — szkic zmian do odbioru

## Odczyt aktywnego nagrania

Po naciśnięciu `Alt+R` AMC najpierw odświeża listę aktywnych nagrań, a potem
podaje pełny komunikat wejścia. Gdy nagrywany jest tylko jeden plik, komunikat
zawiera teraz widok, pozycję i nazwę pliku, na przykład: „Nagrywane, 1 z 1,
TVP Info - data i godzina.mp3”. Nazwa technicznego identyfikatora nagrania nie
jest przekazywana do NVDA.

## Profil publiczny

Publiczny AMC powstaje z tego samego kodu co AMC Test. W tej paczce dostępne są
Pliki, Radio, Podcasty/YouTube, WiiM, Sonos oraz pełny eksport i import danych.
Wyłączone i usunięte z paczki pozostają niedopracowane funkcje TIDAL, Spotify i
Frontier Smart.

`Ctrl+0` nie jest skrótem historii i pozostaje wolny. Historia odtwarzania jest
pod `Ctrl+H`, aktywne nagrania pod `Alt+R`, a historia nagrywania pod
`Alt+Shift+R`.

## Stan sprawdzenia

Pełna regresja źródeł, budowa Release, integralność paczki, instalacja i
kontrolowany start są zaliczone. Wypowiedź `Alt+R` pozostaje do ręcznego
odsłuchu z NVDA; ten dokument jest szkicem do korekty i akceptacji użytkownika.
