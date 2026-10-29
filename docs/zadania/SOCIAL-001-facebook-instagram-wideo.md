# SOCIAL-001 — publiczne filmy Facebooka i Instagrama

## Status

W trakcie. Kod obsługi pojedynczych filmów oraz eksperymentalne, ręcznie
odświeżane subskrypcje publicznych stron Facebooka są gotowe w źródłach.
Nie wykonano instalacji, testu NVDA ani odbioru użytkownika. Publiczne profile
osobiste i profile Instagrama nie są subskrybowane.

## Cel użytkownika

Najważniejsze jest zapisanie kilku publicznych profili lub stron Facebooka i ręczne sprawdzanie nowych filmów. Instagram jest drugim źródłem. Potrzebne są zwykłe, dłuższe filmy oraz rolki, odtwarzanie w AMC i pobieranie. Przykładowa strona do próby: `http://www.facebook.com/buremisie`.

## Ustalenia techniczne

- `Ctrl+I` otwiera zapisaną skrzynkę, a `F5` lub `Ctrl+F5` odświeża źródła według kontekstu.
- yt-dlp obsługuje pojedyncze filmy i rolki Facebooka oraz posty wideo i rolki
  Instagrama. Nie ma ekstraktora listy filmów z profilu Facebooka; ekstraktor
  profilu Instagrama oznaczono jako niedziałający.
- gallery-dl obsługuje pojedyncze filmy Facebooka, lecz jego ekstraktor profilu
  zbiera informacje i zdjęcia, a nie listę filmów. Obsługa Facebooka w tej
  bibliotece jest oznaczona jako wymagająca cookies.
- Odczyt `https://www.facebook.com/buremisie/videos/` bez logowania zwrócił
  HTTP 200, nazwę i opis strony oraz powłokę interfejsu; w HTML nie było
  `/videos/`, `/reel/` ani pól `video_id`. Nie wykazano odczytu listy filmów.
- Oficjalna funkcja Meta `Page Public Content Access` pozwala czytać publiczne
  posty cudzych stron, ale wymaga App Review i weryfikacji firmy. Dokument:
  `https://developers.facebook.com/documentation/development/features-reference/page-public-content-access/`.
- Publiczny film Facebooka z próby CNN zadziałał w yt-dlp 2026.10.26, lecz
  dwie inne publiczne próbki zakończyły się błędem parsowania. Instagramowa
  próbka z dźwiękiem zadziałała; inna próbka wymaga logowania.

## Materiał do dokumentacji użytkownika

W sesji **Podcasty i YouTube** `Ctrl+N` pozwala dodać link do jednego
publicznego filmu Facebooka albo postu wideo lub rolki Instagrama. Film trafia
do **Publicznych materiałów internetowych**. Enter odtwarza w AMC ścieżkę
dźwiękową, `Ctrl+Shift+D` pobiera wideo do ustawionego folderu, a `Ctrl+S`
otwiera **Zapisz jako** dla jednego filmu. Domyślny format MP4 lub najlepszy
dostępny format ustawia się w ustawieniach sesji. AMC nie pokazuje obrazu
podczas odtwarzania; pobrany plik wideo zawiera obraz.

W tym samym formularzu można dodać publiczną stronę Facebooka, na przykład
`https://www.facebook.com/buremisie/`. Każda z kilku stron jest osobnym
źródłem w Bibliotece. `F5` sprawdza wybraną stronę, `Ctrl+F5` wszystkie
źródła sesji, a `Ctrl+I` pokazuje nowo odkryte filmy w skrzynce. `Ctrl+D` na
filmie pobiera sam dźwięk jako MP3 do ustawionego folderu. `Ctrl+Shift+D`
pobiera wideo. Do pobrania MP3 są potrzebne składniki yt-dlp i FFmpeg.
Komunikaty używają nazwy strony i filmu, nie technicznego ID.
Pierwsze dodanie nie wypełnia skrzynki całym archiwum; po odświeżeniu nowo
odkryte filmy są oznaczane jako nowe. Strony Facebooka nie są sprawdzane
automatycznie, nawet przy włączonym automatycznym odświeżaniu podcastów.
Formularz uprzedza, że lista z Facebooka może być niepełna. Błąd odczytu
jest komunikowany, a nie zapisywany jako pusty kanał. Profile Instagrama nie
są jeszcze obsługiwane jako źródło. Pojedynczy film pozostaje pozycją, a nie
odświeżaną subskrypcją.

## Uzasadnienie i decyzje

Korekta z 2026-10-29: zastępuje wcześniejszą decyzję o wdrożeniu wyłącznie
pojedynczych linków. Po rzeczywistej próbie na stronie Burego Misia dodano
osobny rodzaj źródła `FacebookPage`, ręczne odświeżanie i rozpoznawanie
załączników wideo. Stabilny adres strony
jest zapisywany w Bibliotece, a adres strumienia jest pobierany ponownie przy
odtwarzaniu. Logowanie i cookies nie są pobierane z przeglądarki. Komunikat
o odmowie Facebooka nie udaje pustej listy. Komunikat o błędzie parsowania
pojedynczego filmu odróżnia się od materiału wymagającego logowania.
Użytkowy opis materiału w bazie wskazuje właściwego dostawcę.

## Testy i wynik

- `dotnet build src/AccessibleMediaController.LiteHost/AccessibleMediaController.LiteHost.csproj -c Release --no-restore --disable-build-servers -v:q`: **sukces, 0 błędów, 0 ostrzeżeń**. Nie jest to build instalatora.
- Siedem celowanych asercji Pythona z `test_youtube_video_download_contract.py` wykonano przypiętym runtime AMC bez `pytest`: **7 zaliczonych**. Runtime nie ma modułu pytest, więc nie przedstawiam tego jako przebiegu pytest.
- Parser JSON tłumaczeń oraz składnia zmienionych plików Python: **zaliczone**.
- `yt-dlp.exe` 2026.10.26 pobrano do katalogu zadania i zweryfikowano SHA-256 `f5389d3698ecde4ef06f4e6b1ce0294fe9ac1396228c8990b8d3416d6d177a7d`. Publiczny film CNN i rolka `CDUMkliABpa` zwróciły strumień audio oraz format MP4 w symulacji pobierania. Plików wideo nie pobierano.
- Próba dwóch innych filmów Facebooka skończyła się błędem `Cannot parse data`; nie zostały zaliczone. Inny film Instagram TV zwrócił komunikat o braku anonimowego dostępu.
- Nie uruchomiono GUI, testu NVDA, instalatora ani nowej wersji użytkowej.
- Po dodaniu subskrypcji: kompilacja LiteHosta bez błędów i ostrzeżeń;
  celowany zestaw `--facebook-page` zaliczony (adresy, parser, dwie osobne
  strony w bazie, odświeżanie wyłącznie ręczne, przekazanie filmu do pobierania
  i proponowana nazwa MP3); celowany
  `--facebook-live` zaliczony na `buremisie`, jeden film. Testy funkcji
  Pythona z `test_youtube_video_download_contract.py`: 8 zaliczonych.
  Składnia zmienionych plików Pythona i JSON tłumaczeń: zaliczone.
  yt-dlp w symulacji wybrał dla filmu `4170870626378494` ścieżkę audio
  `m4a`, kodek `mp4a.40.5`, czas 3840,237 s. Nie pobrano MP3.

## Znane ograniczenia

Nie ma potwierdzenia, że mechanizm odczytu wpisów z dowolnej publicznej strony
Facebooka działa stabilnie. Próbę na jednej stronie opisano poniżej. Metoda
korzysta z nieudokumentowanego zapytania Facebooka i może wymagać aktualizacji.
Obecnie pobiera tylko bieżące okno najnowszych wpisów, nie całe archiwum;
częste publikowanie pomiędzy ręcznymi odświeżeniami może pominąć filmy.
Nie przeprowadzono próby na kilku stronach ani na profilu osobistym.
Publiczne pojedyncze filmy działają tylko wtedy,
gdy bieżąca wersja yt-dlp potrafi je odczytać. Część Instagrama odmawia
anonimowego dostępu. Materiały bez ścieżki dźwiękowej nie przechodzą obecnie
importu, chociaż sam plik wideo mógłby być możliwy do pobrania. Rzeczywisty
odczyt i pobranie MP3 z interfejsu AMC wymagają osobnego odbioru.

## Dalsza analiza: 2026-10-29

Koryguje wcześniejsze ustalenie „brak potwierdzonego mechanizmu odczytu listy”.
Sprawdzono trzy warianty na publicznej stronie `buremisie`, bez logowania:

- `mbasic.facebook.com/buremisie/videos/` i `m.facebook.com/buremisie/videos/`
  zwróciły pusty wątek. Pełna wersja nadal zwróciła powłokę bez odnośników do filmów.
- RSSHub ma aktualną trasę `/facebook/page/:id` dla stron i publicznych profili.
  Jej kod używa nieudokumentowanego zapytania Facebook GraphQL, dopuszcza pracę
  bez cookies i rozpoznaje załączniki wideo. Publiczna instancja `rsshub.app`
  zwróciła HTTP 403, inna instancja HTTP 503. Nie potwierdzono działającego
  publicznego kanału RSS. Kod trasy:
  `https://github.com/DIYgod/RSSHub/blob/master/lib/routes/facebook/page.ts`;
  kod odczytu: `https://github.com/DIYgod/RSSHub/blob/master/lib/routes/facebook/utils.ts`.
- Jedno anonimowe zapytanie tą metodą dla ID strony `100064737484510`
  zwróciło wpis z filmem z 25.10.2026:
  `https://www.facebook.com/buremisie/videos/4170870626378494/`.
  yt-dlp 2026.10.26 rozpoznał ten film i czas 3840,237 s w symulacji, bez
  pobierania. To jest dowód wykonalności na tej stronie w tym dniu, a nie
  gwarancja kompletności ani trwałości listy. W odpowiedzi znaleziono jeden
  wpis pomimo żądania pięciu, więc przed wdrożeniem subskrypcji trzeba zbadać
  stronicowanie i rozróżnianie filmów od pozostałych wpisów.

Dokumentacja `/{page-id}/videos` w Graph API v26.0 mówi, że odczyt tego
konkretnego endpointu nie jest dostępny. Oficjalny `/{page-id}/feed` pozwala
czytać posty, a dla cudzej strony wymaga funkcji Page Public Content Access;
obiekt posta ma `attachments` i `permalink_url`. Wymagania funkcji obejmują
App Review i weryfikację firmy. Dokumenty:
`https://developers.facebook.com/docs/graph-api/reference/page/videos/`,
`https://developers.facebook.com/docs/graph-api/reference/page/feed/`,
`https://developers.facebook.com/docs/graph-api/reference/post/`.

Wniosek projektowy: próbny, ręcznie odświeżany odczyt publicznych stron bez
logowania jest możliwy, ale jego zawodność trzeba wyraźnie pokazać w AMC.
Nie wpisywać publicznego RSSHuba jako gwarantowanego źródła i nie zapisywać
tymczasowych adresów strumienia. Stabilna ścieżka oficjalna wymaga
zatwierdzonej aplikacji Meta i zaplecza na token; nie jest gotowym rozwiązaniem
dla samodzielnej aplikacji lokalnej.

## Wersja i commit

Źródła zmieniono na bieżącej gałęzi `codex/konfigurowalne-skroty-20261026`.
Zmiany obejmują resolver, import, odtwarzanie audio, pobieranie wideo, nazwy
użytkowe, subskrypcje stron Facebooka, menu, pomoc, tłumaczenia i celowane testy. Kompilacja LiteHosta jest
zaliczona. Brak nowej instalacji, wydania i commitu.

Nowy etap zmienił `AppSettings.cs`, `PodcastLibraryDatabase.cs`,
`LitePodcastAddCoordinator.cs`, `LitePodcastRefreshCoordinator.cs`,
`AccessibleMediaController.LiteHost.csproj`, `gui.py`, `podcast_source.py`,
`menu_model.py`, `shortcuts.py`, `i18n.py`, `en_legacy.json`, test kontraktowy
Pythona i pliki projektu oraz uruchamiania testów LiteHosta. Dodał
`FacebookPublicPageClient.cs` i `FacebookPageTests.cs`. Wcześniejsze zmiany
obsługi pojedynczych filmów w pozostałych plikach zachowano.
