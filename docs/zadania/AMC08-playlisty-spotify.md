# AMC08 — natywne playlisty Spotify

Status: **Korekta pamięci podręcznej i ostatniego celu wdrożona w źródłach i
testach; czeka na pełną regresję, instalację oraz świadomą próbę z NVDA na
koncie Spotify**.

Źródło decyzji: zatwierdzona analiza historyczna tylko do odczytu
`D:\Projekty Codex\Accessible Multimedia Controller\AMC08_PLAYLISTY_SPOTIFY_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

- W sesji Spotify `Ctrl+P` otwiera listę natywnych playlist konta Spotify.
  Samo wejście na listę nie obiecuje odtwarzania całej playlisty.
- Na zaznaczonym utworze albo odcinku `Ctrl+Shift+P` otwiera okno „Dodaj do
  playlist Spotify”. Strzałki wybierają playlistę, a Spacja zaznacza lub
  odznacza wiele playlist. Enter wykonuje operację, Escape ją anuluje.
- Przycisk „Nowa playlista…” pyta o nazwę i widoczność: domyślnie prywatną
  albo jawnie publiczną. Nowa playlista jest od razu zaznaczona jako cel.
- Przy pierwszym `Ctrl+Shift+P` w danym uruchomieniu AMC mówi „Pobieram
  playlisty Spotify”. Kolejne otwarcia korzystają z pamięci podręcznej i nie
  pobierają tej samej listy ponownie. Po zapisie AMC mówi, ile pozycji dodano,
  które były już obecne oraz czy wynik jest częściowy.
- Playlista utworzona w oknie od razu trafia do listy bieżącego uruchomienia.
  Przy następnym `Ctrl+Shift+P` jest widoczna, a ostatnio użyte playlisty są
  zaznaczone. Ich wybór jest zapisany w prywatnych ustawieniach AMC Test.
- Starsze logowanie Spotify nie zawiera zgód na zmianę playlist. AMC nie
  otwiera wtedy przeglądarki samoczynnie, tylko kieruje do `Ctrl+F5`, aby
  użytkownik świadomie zalogował konto ponownie.
- Lista odczytywana przez NVDA zawiera tylko nazwę, widoczność, informację o
  współdzieleniu i właścicielu oraz stan zaznaczenia. Identyfikatory playlist,
  adresy i `snapshot_id` pozostają niewidocznymi danymi modelu.
- `Ctrl+F1`, pełna pomoc, menu i paleta `Ctrl+Shift+K` używają tego samego
  polecenia. W Spotify brzmi ono „Dodaj do playlist Spotify lub utwórz
  playlistę”; w Plikach, Radiu i Podcastach zachowuje lokalne znaczenie
  „Przynależność do playlist”.

## Uzasadnienie i decyzje

- **Korekta użytkownika z 18 października 2026:** `Ctrl+Shift+P` zastępuje
  wcześniejszy pomysł osobnego `Alt+Shift+P`.
- **Korekta użytkownika z 18 października 2026:** tworzone są prawdziwe
  playlisty Spotify, które można udostępnić. Funkcja nie obiecuje odtwarzania
  całych playlist przez Librespot.
- Używane są ścieżki `/me/playlists` i `/playlists/{id}/items`. Odczyt
  zawartości przyjmuje pole `item`, a `track` wyłącznie jako kontrolowany
  fallback zgodności.
- Wejściowe utwory i odcinki są odduplikowane. Przed zapisem klient odczytuje
  istniejącą zawartość każdej playlisty, więc ponowienie nie dopisuje drugiego
  wystąpienia tej samej pozycji.
- Jedno żądanie zawiera najwyżej 100 pozycji. Każda przyjęta partia zapisuje
  zwrócony `snapshot_id`; awaria późniejszej partii zachowuje i raportuje
  wcześniejszy sukces.
- Identyfikatory playlist z wxPython są ponownie rozwiązywane na świeżej liście
  edytowalnych playlist wewnątrz C#. Interfejs nie może nadać sobie prawa do
  cudzej playlisty przez podmianę danych żądania.
- OAuth prosi jawnie o `playlist-modify-private` oraz
  `playlist-modify-public`. Bez obecności użytkownika nie jest rozpoczynane
  ponowne logowanie i żaden test nie zapisuje danych na prawdziwym koncie.
- **Korekta użytkownika z 19 października 2026 zastępuje wcześniejsze
  pobieranie listy przy każdym `Ctrl+Shift+P`.** Lista jest pobierana raz na
  proces, ale samo dodanie nadal przechodzi przez świeżą weryfikację hosta.
  Potwierdzona nowa playlista jest dopisywana do pamięci, zamiast czekać na
  późniejsze odświeżenie katalogu Spotify.

## Testy i wynik

- 19 października 2026, przed 02:00: `py_compile` zmienionych modułów —
  zaliczony.
- 19 października 2026, odizolowane testy Pythona: parser etykiet, przepływ
  tworzenia i dodawania, fokus po dialogu, klient hosta, skróty, menu,
  `Ctrl+F1` i paleta `Ctrl+Shift+K` — **101 zaliczonych**.
- Po wzmocnieniu obsługi niepotwierdzonego utworzenia playlisty ponowiono
  ukierunkowany zestaw — **63 zaliczone**.
- Pełna odizolowana regresja wxPython po ostatecznej zmianie — **1754
  zaliczone, 110 pominiętych, 11 podtestów zaliczonych** w 91,86 s.
- Testy atrap C# obejmują zakresy OAuth, listę edytowalnych playlist,
  prywatne i publiczne tworzenie, partie 100, idempotencję, `snapshot_id`,
  endpoint `/items` i wynik częściowy. Ukierunkowane zestawy playlist i
  istniejącej zmiany Biblioteki Spotify zaliczone; pełne Core SmokeTests
  zakończone kodem 0.
- Ukierunkowany kontrakt protokołu playlist zaliczony **1/1**, a pełna regresja
  LiteHost ProtocolTests — **20/20 zestawów**.
- Kompilacja Release Core SmokeTests, LiteHost ProtocolTests i właściwego
  LiteHost zakończona powodzeniem, bez ostrzeżeń i błędów.
- Bramkę bezpieczeństwa po 02:00 zaliczono: żaden harmonogram nie pozostawał
  w aktywnym oknie, przez 10 sekund nie rósł żaden plik `.amc-partial`, a żaden
  z zachowanych plików odzyskiwania nie był zablokowany przez proces.
- Nie wykonano odbioru sieciowego ani zapisu na koncie Spotify.
- Procedura promocji ponownie zaliczyła pełne **1754** testy wxPython,
  zbudowała paczkę 1659 plików, sprawdziła jej manifest i sumy SHA-256,
  zainstalowała ją oraz potwierdziła uruchomienie właściwego procesu i tytułu.
- 19 października 2026 po zgłoszeniu z prawdziwego użycia: bramka obejmująca
  cache, nową playlistę, zapamiętanie celów, magazyn ustawień, menu,
  nagrywanie i harmonogramy — **204 zaliczone**. Atrapa potwierdza, że dwa
  kolejne wywołania pobierają katalog tylko raz, nowa publiczna playlista jest
  widoczna za drugim razem, oba ostatnie cele są zaznaczone, a wybór przeżywa
  zapis ustawień. Korekta nie została jeszcze zainstalowana ani odebrana w
  sieci na prawdziwym koncie.
- Szeroki audyt menu, skrótów i sesji: **403 zaliczone i 5 podtestów**.
  Pełna regresja wxPython po połączeniu korekt: **1837 zaliczonych, 110
  pominiętych i 11 podtestów zaliczonych**.

## Znane ograniczenia

- Odtwarzanie całej playlisty Spotify przez AMC nadal nie jest obiecywane.
- Zewnętrzny odbiór na prawdziwym koncie, w tym ponowne OAuth z nowymi
  zakresami, pozostaje zadaniem ręcznym.
- Ręczny test NVDA i prawdziwego konta Spotify nie został wykonany. Sama
  poprawna instalacja nie potwierdza jeszcze odbioru mowy ani operacji
  sieciowej na koncie.
- Pamięć katalogu obowiązuje do zamknięcia AMC Test. Playlista utworzona w
  AMC trafia do niej natychmiast; zmiana wykonana równolegle w innej aplikacji
  Spotify będzie widoczna po ponownym uruchomieniu AMC Test. Dodawanie nie
  ufa cache — host ponownie sprawdza uprawnienia i istnienie wskazanego celu.

## Wersja i commit

- Profil docelowy: bieżący AMC Test.
- Kod źródłowy: commit `697d1a73fd66c12bfa061f4d5f55a93ddaa36e85`.
- Kompilacja: Release, zaliczona 19 października 2026 po bezpiecznej bramce
  nagrywania; nie jest to jeszcze paczka instalacyjna.
- Instalacja: `2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonywać w tym etapie.
- Korekta cache i ostatniego celu: bieżący lokalny etap, commit zostanie
  wpisany po zapisie; kompilacja i instalacja jeszcze niewykonane.
