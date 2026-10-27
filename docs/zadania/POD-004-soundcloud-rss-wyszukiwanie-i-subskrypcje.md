# POD-004 — SoundCloud jako podcast RSS: wyszukiwanie i subskrypcje

- Status: `Gotowe w źródłach; bez instalacji w tym zadaniu`
- Utworzono: 27 października 2026
- Obszar: Podcasty i YouTube, RSS, pobieranie, dostępność

## Cel

AMC ma traktować publiczny podcast hostowany w SoundCloud jak zwykły podcast,
nie jak stronę internetową. Użytkownik może wyszukać go przez `Ctrl+F`,
lokalnie zasubskrybować przez `Ctrl+Shift+L` albo podać adres profilu lub RSS
w `Ctrl+N`. Odcinki mają zachować bezpośrednie adresy audio z elementów
`enclosure`, dlatego działają odtwarzanie, kolejka, `Ctrl+D` i `Ctrl+S`.

## Korekta użytkownika z 27 października 2026

Ta korekta zastępuje wcześniejszą decyzję POD-004 o wyborze Mixcloud i
otwieraniu audycji na stronie WWW. Mixcloud nie dostarczał AMC plików audio,
więc nie spełniał wymagania podcastu. Rozwiązaniem jest publiczny RSS
SoundCloud, który rzeczywiście zawiera odcinki audio.

## Zachowanie użytkowe

- `Ctrl+F` korzysta z obecnego publicznego katalogu Apple Podcasts. Wynik,
  którego kanał znajduje się w `feeds.soundcloud.com`, jest nazwany
  **podcast SoundCloud**.
- Enter na takim wyniku weryfikuje RSS, zapisuje lokalną subskrypcję i otwiera
  listę odcinków. `Ctrl+Shift+L` zapisuje ją w Bibliotece bez otwierania.
- `Ctrl+N` przyjmuje `https://soundcloud.com/NazwaProfilu` oraz bezpośredni
  `https://feeds.soundcloud.com/users/soundcloud:users:ID/sounds.rss`.
- Adres pojedynczego utworu, playlisty, wyszukiwania albo adres zawierający
  nazwę użytkownika i hasło jest odrzucany z komunikatem użytkowym.
- Profil jest pobierany bez logowania. AMC odczytuje wyłącznie publiczny rekord
  użytkownika osadzony przez SoundCloud i buduje z jego identyfikatora
  kanoniczny adres RSS.
- Zapisany kanał używa interwału RSS, może być eksportowany do OPML i jest
  odświeżany tą samą ograniczoną drogą co pozostałe podcasty.
- Odcinki SoundCloud są zwykłymi odcinkami podcastu. Nie mają blokad kolejki,
  pobierania ani `Zapisz jako`.

## Dostępność i powierzchnie poleceń

- Etykieta źródła brzmi **podcast SoundCloud**. Identyfikator użytkownika,
  nazwa klasy i surowy rekord JSON nie wchodzą do nazwy wiersza.
- Wspólna nazwa `Ctrl+N` w menu, palecie, `Ctrl+F1` i pełnej pomocy brzmi
  **Dodaj podcast, SoundCloud, kanał YouTube lub medium internetowe**.
- Formularz ma jawny opis, że profil SoundCloud stanie się podcastem z
  odtwarzalnymi i możliwymi do pobrania plikami audio.
- Enter i Escape korzystają z istniejącego kontraktu wyników podcastów;
  `Ctrl+Shift+L` używa tej samej lokalnej mutacji Biblioteki co RSS.

## Uzasadnienie

Oficjalne materiały SoundCloud opisują RSS jako sposób dostarczania podcastów.
Kanał obejmuje publiczne utwory wybrane przez autora do RSS. Wyszukiwanie AMC
nie używa prywatnego ani przejętego klucza aplikacji SoundCloud: rozpoznaje
publiczne kanały SoundCloud zwrócone przez katalog Apple Podcasts. Profil
podany w `Ctrl+N` służy wyłącznie do odkrycia publicznego adresu RSS.

## Testy i rzeczywiste wyniki

- Build LiteHost Debug: zaliczony, `0` ostrzeżeń i `0` błędów.
- Celowane testy wxPython: `117 passed`.
- Końcowa próba po korekcie etykiety i przekierowania: `42 passed`.
- Pełna regresja wxPython: `2101 passed, 113 skipped, 13 subtests passed`.
- Pełny program testów Core: zaliczony, kod wyjścia `0`.
- Kontrolowany test profilu i normalizacji SoundCloud: zaliczony.
- Żywa próba profilu `4thandlong`: RSS zwrócił `271` plików audio.
- Żywa próba pierwszego `enclosure`: HTTP `206`, `Content-Type: audio/mpeg`,
  pobrano jeden bajt.
- Żywe wyszukiwanie `4th and Long`: znaleziono `2` podcasty SoundCloud.

## Znane ograniczenia

- `Ctrl+F` znajduje podcasty SoundCloud obecne w publicznym katalogu Apple.
  Profil niezgłoszony do tego katalogu nadal można dodać przez `Ctrl+N`.
- Autor SoundCloud decyduje, które publiczne utwory umieszcza w swoim RSS.
  AMC nie obchodzi ustawień prywatności i nie zamienia dowolnej playlisty ani
  utworu SoundCloud w podcast.
- Zmiana układu publicznego rekordu profilu przez SoundCloud może wymagać
  aktualizacji resolvera; bezpiecznym rozwiązaniem awaryjnym pozostaje pełny
  adres RSS.

## Wersja, build, instalacja i publikacja

- Kod: gotowy w drzewie źródłowym.
- Testy: celowane, pełna regresja wxPython i pełne testy Core zaliczone.
- Build: LiteHost Debug zaliczony.
- Instalacja: niewykonana i poza zakresem tego zadania.
- Publikacja: niewykonana i poza zakresem tego zadania.
- Commit źródłowy: `ebf9c812` (`fix: use SoundCloud RSS for podcast subscriptions`).
