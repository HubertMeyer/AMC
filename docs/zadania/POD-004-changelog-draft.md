# Projekt changelogu — POD-004 Mixcloud

Status: projekt do korekty i zatwierdzenia użytkownika. Nie opisuje jeszcze
zainstalowanego ani opublikowanego wydania.

- Dodano publiczne wyszukiwanie profili i audycji Mixcloud w `Ctrl+F` sesji
  Podcasty i YouTube, bez konta i bez klucza API.
- Dodano lokalne subskrypcje profili Mixcloud przez `Ctrl+Shift+L` oraz
  bezpośrednie dodawanie profilu lub audycji przez `Ctrl+N`.
- Zapisane profile można otwierać i odświeżać; poznane wcześniej audycje nie są
  usuwane tylko dlatego, że wypadły z aktualnego okna publicznego API.
- Enter na audycji otwiera oficjalną stronę Mixcloud bez niejawnego dodawania
  wyniku do Biblioteki.
- Menu, paleta poleceń, pełna pomoc i `Ctrl+F1` używają wspólnego modelu
  dostępności. Pobieranie, zapis pliku i kolejka są ukryte dla audycji
  Mixcloud, ponieważ publiczne API nie udostępnia strumienia audio.
- SoundCloud pozostaje przy publicznym RSS. Nie dodano płatnej rejestracji API,
  sekretu klienta ani parsowania stron.
