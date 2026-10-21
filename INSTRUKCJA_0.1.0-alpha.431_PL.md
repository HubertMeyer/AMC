# AMC 0.1.0-alpha.431 — szkic krótkiego odbioru NVDA

Ten dokument jest szkicem do sprawdzenia i korekty użytkownika. Nie jest
automatycznie publikowany.

Publiczny kandydat jest zainstalowany i uruchomiony z:

- `D:\Projekty Codex\AMC Public\AMC.exe`.

AMC Test pozostał uruchomiony z własnym profilem i nie został podmieniony.

## Ctrl+Shift+U w folderze otwartym przez Ctrl+O

1. Otwórz zwykły folder skrótem `Ctrl+O`.
2. Zaznacz plik, który znajduje się również w dodanym źródle Biblioteki.
3. Naciśnij `Ctrl+Shift+U`.
4. NVDA powinien powiedzieć `Dodano do ulubionych: nazwa pliku` albo
   `Usunięto z ulubionych: nazwa pliku`.
5. Lista ma pozostać w tym samym folderze. Nie powinna przełączyć się na
   Bibliotekę ani powiedzieć `zero elementów`.
6. Otwórz `Ulubione` skrótem `Ctrl+U` i sprawdź zmianę. `Ctrl+L` wraca do
   Biblioteki i nie usuwa pliku.

Jeżeli folder nie został jeszcze dodany do Biblioteki, `Ctrl+O` nadal pozwala
go przeglądać, ale samo przeglądanie nie wykonuje trwałego importu. AMC podaje
wtedy, że pliku nie ma w Bibliotece i wskazuje `Foldery Biblioteki, Ctrl+F5`.

## Profile wydania

Publiczny AMC i AMC Test powstają z tego samego kodu. Publiczna paczka ma
Pliki, Radio, Podcasty/YouTube, WiiM, Sonos oraz eksport i import danych. Nie
zawiera jeszcze TIDAL-a, Spotify ani Frontier Smart.
