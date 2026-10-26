# AMC Test 0.1.0-alpha.425 — szkic zmian

To wydanie jest przeznaczone wyłącznie do lokalnej próby w AMC Test. Nie jest
wydaniem publicznym.

## Apple Music — prototyp do próby na prawdziwym koncie

- Nowa sesja Apple Music ma bibliotekę utworów, albumów i playlist,
  wyszukiwanie `Ctrl+F`, otwieranie albumów, wykonawców i powiązań strzałką w
  prawo oraz zgodne z możliwościami API dodawanie do Biblioteki i ulubionych.
- `Ctrl+F5` otwiera konto Apple Music. Developer token jest przechowywany w
  Menedżerze poświadczeń Windows, a użytkownik loguje się w oficjalnym oknie
  Apple Music.
- Enter na utworze korzysta z ukrytego MusicKit on the Web; transport AMC może
  sterować odtwarzaniem, głośnością, czasem i przejściem utworu.
- Usuwanie z biblioteki i ulubionych nie jest obiecywane, ponieważ publiczne
  Apple Music API nie udostępnia odpowiedniej operacji usuwania.

## YouTube i Google

- `Ctrl+F5` w sesji Podcasty i YouTube otwiera nowe konto YouTube.
- Oficjalne logowanie Google działa w zwykłej przeglądarce, przez PKCE, bez
  sekretu klienta. AMC prosi wyłącznie o odczyt danych YouTube.
- Można zaimportować subskrybowane kanały i własne playlisty do Biblioteki.
- Globalny skrót wtyczki NVDA `Ctrl+Windows+F5` i menu Plik nadal odświeżają
  wszystkie zapisane źródła.
- Logowanie do Data API nie jest przekazywane do `yt-dlp` i nie omija blokad
  wieku, regionu, prywatności ani innych zabezpieczeń odtwarzania.

## Odtwarzanie losowe

- W odtwarzaczu plików lokalnych, Podcastów i YouTube oraz Spotify klawisz `R`
  przełącza odtwarzanie losowe.
- Ta sama funkcja jest dostępna z menu Odtwarzanie i menu kontekstowego
  odtwarzacza, ze stanem odczytywanym przez NVDA.
- Element „Odtwarzaj jako następne” i kolejka zachowują pierwszeństwo przed
  losowaniem.

## Pozostałe składniki wspólnego pakietu testowego

Pakiet obejmuje także zgromadzone wcześniej i osobno sprawdzone poprawki:

- dodawanie kanałów, playlist i publicznych materiałów YouTube;
- obsługę dużych podcastów Spotify i ich odtwarzanie;
- ulepszoną sesję Frontier Smart, w tym wykrywanie oraz zgodność ze starszym
  firmware'em.

## Granice

- Apple Music wymaga gotowego developer tokenu oraz prawdziwego konta z aktywną
  subskrypcją. Zgodność DRM WebView2 pozostaje do ręcznej próby.
- Google/YouTube wymaga publicznego Client ID typu Aplikacja na komputer oraz
  włączonego YouTube Data API v3.
- TIDAL pozostaje przy dotychczasowym przekazywaniu do oryginalnej aplikacji;
  w tym wydaniu nie ma nowej obietnicy pełnego sterowania jej odtwarzaczem.

Dokument jest szkicem do korekty po próbie użytkownika.
