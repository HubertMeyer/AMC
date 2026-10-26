# AMC Test — projekt informacji o zmianach z 26 października 2026 r.

Ten tekst jest projektem do sprawdzenia i zatwierdzenia przez użytkownika; nie
został opublikowany.

## Rozpoznawanie i historia utworów

- `Ctrl+Alt+S` otwiera historię rozpoznań zarówno z głównej listy Radia, jak i
  z odtwarzacza.
- Historia ma krótką listę działań pod prawą strzałką oraz pełne menu usług,
  łączy, kopiowania, eksportu, usuwania i zmiany kolejności.
- Spotify i TIDAL można pokazać w AMC albo otworzyć w oryginalnej aplikacji;
  Apple Music korzysta z publicznych łączy bez logowania.

## Nagrywanie

- W `Nagrywane` lewa strzałka opisuje odbierany strumień, a prawa parametry,
  nazwę i folder pliku wynikowego.
- Harmonogram używa tego samego krótkiego opisu pliku bez powtarzania źródła.

## Wideo z YouTube

- `Ctrl+Shift+D` pobiera jeden albo kilka materiałów wideo do folderu pobrań.
- `Ctrl+S` otwiera kontekstowe **Zapisz wideo jako** z wyborem MP4 albo
  najlepszego dostępnego formatu. Dotychczasowe pobieranie audio pozostaje bez
  zmian.

## Nazwy stacji w prostych playlistach M3U

- AMC potrafi teraz odczytać nazwę stacji z nagłówka Icecast/Shoutcast, gdy
  playlista zawiera sam adres bez `#EXTINF`.
- Nazwa zapisana w playliście zawsze ma pierwszeństwo.
- Odczyt obejmuje tylko nagłówki, ma ograniczenia czasu i liczby równoległych
  połączeń oraz nie uruchamia odtwarzania.
- Jeśli serwer nie poda nazwy, lista zachowuje krótką nazwę hosta zamiast
  pełnego adresu URL.
- NVDA informuje o odczytywaniu nazw oraz podaje liczbę nazw odczytanych i
  zastępczych po zakończeniu importu.

Na przekazanej playliście Foobara AMC przyjął 17 unikalnych stacji i uzyskał
14 nazw z serwerów. Trzy serwery nie podały użytecznej nazwy.

