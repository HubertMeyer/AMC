# POD-004 — SoundCloud jako podcast RSS: wyszukiwanie i subskrypcje

- Status: `Wydanie alpha.436 istnieje; poprawa polskiego Ctrl+F zapisana w commicie 11ba6271, bez nowej instalacji i publikacji`
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

## Korekta wyszukiwania z 27 października 2026

Użytkownik potwierdził, że `Ctrl+F` zwraca głównie zagraniczne wyniki i nie
znajduje polskich profili dominikańskich. Diagnoza wykazała, że wcześniejsza
wersja nie przeszukiwała SoundCloud bezpośrednio: rozpoznawała wyłącznie kanały
SoundCloud obecne w Apple Podcasts. Zapytania o Freta, Służew i Rzeszów nie
zwracały tam żadnego takiego kanału, mimo że ich publiczne RSS-y zawierają
odpowiednio 254, 500 i 35 odcinków.

Ta korekta dodaje wydzielony, przeszukiwalny katalog zweryfikowanych profili z
niepustym RSS. Nie korzysta z konta, sekretu aplikacji ani wewnętrznego klucza
strony WWW. Profil Jarosław istnieje, lecz jego RSS jest obecnie pusty, dlatego
nie jest reklamowany jako działający podcast.

Późniejsze doprecyzowanie użytkownika z tego samego dnia potwierdziło, że
globalne `Ctrl+Shift+F` ma honorować tę samą poprawkę. W wxPython oba skróty
korzystają ze wspólnej funkcji wyszukiwania, a zakres globalny obejmuje sesję
Podcasty i YouTube niezależnie od sesji początkowej. Dodany test regresyjny
utrwala ten kontrakt zamiast tworzyć drugi, rozbieżny adapter SoundCloud.

## Zachowanie użytkowe

- `Ctrl+F` przeszukuje w pierwszej kolejności zweryfikowany katalog SoundCloud,
  a następnie pozostałe publiczne katalogi. Pierwsze wpisy to Freta10,
  Dominikanie Służew i Dominikanie – Rzeszów.
- `Ctrl+Shift+F` korzysta z tego samego katalogu SoundCloud w wyszukiwaniu
  wszystkich usług, również gdy okno otwarto z innej sesji niż Podcasty i
  YouTube.
- Każdy wynik, którego kanał znajduje się w `feeds.soundcloud.com`, jest
  nazwany **podcast SoundCloud**. Zweryfikowane wyniki SoundCloud są ustawiane
  przed ogólnymi wynikami katalogowymi.
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
nie używa prywatnego ani przejętego klucza aplikacji SoundCloud: łączy
zweryfikowany katalog adresów RSS z publicznymi kanałami zwróconymi przez Apple
Podcasts. Profil podany w `Ctrl+N` służy wyłącznie do odkrycia publicznego
adresu RSS.

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
- Diagnoza polskich wyników Apple: Freta `0`, Służew `0`, Rzeszów `0`;
  Jarosław `2` ogólne wyniki, ale `0` kanałów SoundCloud.
- Żywe RSS-y: Freta10 `254`, Służew `500`, Rzeszów `35`, Jarosław `0`
  odcinków audio.
- Kontrolowany test nowego katalogu: zaliczony; polskie znaki i warianty bez
  znaków działają, a identyfikatory nie wchodzą do etykiety NVDA.
- Celowany test Windows po korekcie (`--soundcloud-podcast-client`): oba
  przypadki zaliczone — resolver publicznego profilu oraz wyszukiwanie polskich
  kanałów przez `Ctrl+F` bez konta.
- Test parytetu wyszukiwania globalnego potwierdza, że `Ctrl+Shift+F` wywołuje
  ten sam katalog i zwraca `Freta10` jako **podcast SoundCloud** z użytkową
  nazwą sesji, bez technicznego identyfikatora w etykiecie NVDA.
- Powiązany zestaw wyszukiwania, nawigacji, skrótów i palety poleceń po dodaniu
  testu parytetu: `116 passed`.
- Żywa próba całej drogi wyszukiwania dla `Dominikanie Freta`: źródło
  SoundCloud zwróciło `1` wynik w `0,0 s`, a `Freta10` było pierwszą pozycją z
  prawidłowym RSS-em i adresem profilu.
- Celowane testy wxPython związane z wyszukiwaniem, nawigacją, dodawaniem
  podcastu i paletą poleceń: `94 passed`.
- Pełna regresja wxPython po korekcie: `2102 passed, 113 skipped, 13 subtests
  passed`.
- Pełna regresja Windows nie jest oznaczona jako zaliczona. Pierwszy przebieg
  zatrzymał test schowka z powodu braku dostępu piaskownicy; sam ten test po
  uruchomieniu z dostępem do schowka przeszedł. Powtórzenie poza piaskownicą
  ujawniło niezależne, niestabilne przypadki czasowe WPF/Sonos oraz błąd
  serializacji schowka. Celowany test SoundCloud pozostaje zielony.
- Samowystarczalna paczka AMC Test: `2136` kontrolowanych plików, pełna
  integralność i odizolowany start interfejsu oraz hosta zaliczone.
- Instalator `AMC-Test-2026-10-27-0233.exe`: zbudowany, skan sekretów zaliczony,
  Quick App Switcher `0.1.6` potwierdzony w pliku integralności.
- GitHub prerelease `test-2026.10.27.0233`: opublikowany i niezależnie
  zweryfikowany wraz z trzema załącznikami oraz ich sumami SHA-256.

## Znane ograniczenia

- `Ctrl+F` nie przeszukuje całej platformy SoundCloud. Obejmuje publiczne wpisy
  Apple oraz jawny katalog profili zweryfikowanych przez projekt. Pozostały
  profil można dodać przez `Ctrl+N`, jeśli udostępnia niepusty RSS.
- Autor SoundCloud decyduje, które publiczne utwory umieszcza w swoim RSS.
  AMC nie obchodzi ustawień prywatności i nie zamienia dowolnej playlisty ani
  utworu SoundCloud w podcast.
- Zmiana układu publicznego rekordu profilu przez SoundCloud może wymagać
  aktualizacji resolvera; bezpiecznym rozwiązaniem awaryjnym pozostaje pełny
  adres RSS.

## Wersja, build, instalacja i publikacja

- Kod wydania alpha.436: gotowy i opublikowany na GitHubie.
- Korekta polskiego wyszukiwania: zapisana w commicie `11ba6271`; bez nowej
  instalacji i publikacji.
- Testy korekty: celowany zestaw SoundCloud, rzeczywista droga LiteHost oraz
  pełna regresja wxPython zaliczone. Pełna regresja Windows ma niezależne błędy
  środowiskowe i czasowe opisane wyżej, dlatego nie jest przedstawiana jako
  zielona.
- Build: LiteHost Debug oraz pełna samowystarczalna paczka Test zaliczone.
- Instalator: `AMC-Test-2026-10-27-0233.exe`, 134290393 bajty, SHA-256
  `1d4fd2ecabe4d358246ae094ebfefdbc19dde7ceade018e6f13bcb5c61beb36a`.
- Instalacja: świadomie niewykonana; użytkownik sprawdzi aktualizację ręcznie.
- Publikacja: prerelease `test-2026.10.27.0233`, commit wydania `abfee285`.
- Commit źródłowy: `ebf9c812` (`fix: use SoundCloud RSS for podcast subscriptions`).
- Commit korekty wyszukiwania: `11ba6271`
  (`fix: find verified Polish SoundCloud podcasts`).
