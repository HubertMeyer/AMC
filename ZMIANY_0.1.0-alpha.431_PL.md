# AMC 0.1.0-alpha.431 — szkic zmian do odbioru

## Poprawione Ulubione plików lokalnych

`Ctrl+Shift+U` rozpoznaje teraz ten sam plik niezależnie od tego, czy został
wybrany w Bibliotece, czy w folderze otwartym przez `Ctrl+O`. Dodanie do
Ulubionych zapewnia członkostwo pliku w Bibliotece i zapisuje oba trwałe
porządki w jednej transakcji. Usunięcie z Ulubionych nie usuwa pliku z
Biblioteki ani z dysku.

Zmiana Ulubionych nie przełącza już folderu z `Ctrl+O` na pustą Bibliotekę.
Widok `Ulubione` nadal odświeża się po zmianie, a komunikat NVDA pada dopiero
po zakończeniu odświeżenia. Plik, którego naprawdę nie ma w Bibliotece,
otrzymuje jasny komunikat z poleceniem `Foldery Biblioteki, Ctrl+F5`; AMC nie
udaje wtedy powodzenia i nie importuje niejawnie całego folderu.

## Stan sprawdzenia

Testy bezpośrednie: 59 zaliczonych. Pełna regresja wxPython: 1953 zaliczone,
110 świadomie pominiętych i 11 podtestów zaliczonych. Wszystkie 26 zestawów
protokołu C# przeszło. Całe rozwiązanie Release zbudowało się bez ostrzeżeń i
błędów. Publiczna paczka `1555412f` ma 1075 kontrolowanych plików; zainstalowana
kopia przeszła pełną integralność i kontrolowany start. Publiczny `alpha.431`
został zainstalowany i uruchomiony z `D:\Projekty Codex\AMC Public`. Ręczny
odbiór mowy i fokusu NVDA pozostaje do wykonania.

Publiczny profil pozostaje kopią wspólnego kodu bez niedopracowanych modułów
TIDAL, Spotify i Frontier Smart. WiiM i Sonos pozostają dostępne.
Niczego nie opublikowano zdalnie.
