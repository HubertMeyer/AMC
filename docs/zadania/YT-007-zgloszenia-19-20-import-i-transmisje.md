# YT-007 — zgłoszenia Huberta #19 i #20: import i transmisje

- Status: `W trakcie — rozwój źródeł i testy bez interfejsu; wydanie wstrzymane bramką bezpieczeństwa alpha.511`.
- Rozpoczęcie: 17 listopada 2026.
- Polecenie użytkownika: „To Hubert znowu? Sprawdź oba zgłoszenia, wdrożyc je”.
- Repozytorium: `michalkasperczak/AMC`, gałąź `codex/amc-test-public-20261109`.
- Baza: `cbad568eaabcea7f733dcb1e62e43ed232b1afcb`; przed pracą lokalny i zdalny HEAD zgodne, drzewo czyste.

## Źródła i stan zastany

Pełne zgłoszenia i komentarze odczytano przez GitHub. Oba zgłoszenia napisał `HubertMeyer`.

- #19: import Google Takeout (ZIP i CSV), NewPipe i FreeTube; właściwe typowanie kanałów/playlist YouTube w OPML; propozycja nieoficjalnego logowania kodem; komentarze dodają publiczną listę live/upcoming bez konta.
- #20: zgłoszony brak `was_live` w zlokalizowanych wynikach yt-dlp oraz odrzucanie publicznych archiwów kanału Trójki `UC22dMuSZ7XTCkEY72rodgIA`. Opis autora nie jest jeszcze niezależną reprodukcją AMC.
- YT-001 zawiera wcześniejszą decyzję o własnym kliencie AMC, oficjalnym OAuth i zakazie używania cudzych danych klienta TV; brak konfiguracji nie jest powodem do dołączania sekretów do paczki.
- YT-002 zawiera istniejące Ctrl+T i Ctrl+Shift+I, limit 20 jawnie wybranych kanałów, brak monitoringu wszystkich subskrypcji i brak osobnego archiwum zauważonych transmisji.

## Zakres i kryteria odbioru

1. Import plików bez logowania: CSV/ZIP Takeout, JSON NewPipe i plik FreeTube zgodny z eksportem AMC. Wybór i potwierdzenie przed zapisem, idempotencja po stabilnym ID, zachowanie nazw i danych istniejących źródeł; bez setek natychmiastowych pobrań na wątku GUI.
2. OPML: adresy kanałów i playlist YouTube otrzymują rzeczywisty typ; RSS pozostaje RSS. Okrągły eksport/import AMC nie degraduje YouTube.
3. Bezpieczny parser plików: ograniczenia rozmiaru/liczby wpisów, brak rozpakowywania ZIP na dysk, brak wykonywania HTML i brak importu historii oglądania/kont/poświadczeń.
4. #20: najpierw rzeczywista próba na publicznym kanale i test RED. Minimalna poprawka zachowuje polskie tytuły i daty oraz nie wpuszcza trwających/zaplanowanych transmisji do archiwum. Nie zakładać, że czas trwania sam dowodzi zakończenia.
5. Lista live/upcoming bez konta: wykorzystać istniejący publiczny tor yt-dlp i kontrakt widoku zamiast nowego klienta prywatnego API; zachować pełną listę kanału, częściowe błędy, cache/F5, limit wybranych kanałów i brak automatycznego OAuth. Oficjalne API, jeśli dostępne, pozostaje opcją.
6. Działające polecenia muszą zachować wspólny model menu, palety, Ctrl+F1, pełnej pomocy, metadanych i instrukcji; bez zmiany istniejących przypisań skrótów.
7. Celowane testy RED/GREEN oraz niezależny ograniczony przegląd zmian. Testy Core/protokołu na nieszkodliwych danych, bez uruchamiania AMC, instalatora, ISCC, dotkniętych kandydatów i bez zmiany ochrony.

## Uzasadnienie i decyzje

Nieoficjalne logowanie cudzym klientem TV nie zostaje włączone w tym etapie: jest sprzeczne z jawną decyzją YT-001 i nie jest niezbędne do importu ani publicznych transmisji. Ten fragment #19 pozostaje rozstrzygnięciem zakresu, nie ukończoną funkcją. Nie ukrywać go w raporcie ani zamykać całego #19 jako wykonanego.

Publiczne transmisje mają najpierw użyć już obecnego narzędzia yt-dlp; nie wdrażać osobnego masowego skanera Innertube ani zmieniać limitu 20 kanałów na podstawie pomiarów zgłaszającego.

## Podział pracy

- Izolowany worktree `amc-yt-imports-cbad568`: importer Core + koordynator OPML/protokół i testy; GUI importu integruje koordynator główny.
- Izolowany worktree `amc-yt-archive-cbad568`: reprodukcja i poprawka #20 w YouTubeCollectionClient oraz testy kolekcji.
- Izolowany worktree `amc-yt-live-cbad568`: publiczny dostawca transmisji i host, Python/GUI dla list transmisji; nie zmieniać importu OPML ani klienta kolekcji.
- Koordynator główny: formularz importu, parytet pomocy/palety/metadanych, integracja, celowany odbiór i rejestr.

## Materiał do dokumentacji użytkownika

Projekt do uzupełnienia po testach: import kanałów z pliku nie wymaga konta Google; źródła będą dodawane bez natychmiastowego pobierania wszystkich materiałów. Zakończone transmisje pozostają w zwykłej liście kanału, a Ctrl+T i Ctrl+Shift+I dotyczą wyłącznie pozycji trwających i zaplanowanych. Nie powstaje osobna historia.

## Testy i wynik

Odczytano pełne zgłoszenia, decyzje YT-001/YT-002, instrukcje repozytorium i zgodność GitHub; autor obu: `HubertMeyer`.

Interfejs importu zachowuje `Action.IMPORT_PODCAST_OPML`, Ctrl+O i istniejący protokół `podcast.opml.inspect/import`, rozszerza filtr plików i tekst wyboru źródeł oraz wspólne menu/pomoc/paletę i angielskie etykiety. Backend w izolowanym worktree pozostaje w toku — samo okno nie jest dowodem obsługi formatu.

- RED interfejsu: `2 failed, 2 passed` — brak CSV w filtrze i brak YouTube w etykiecie istniejącego polecenia.
- RED tłumaczenia nowego okna: `1 failed, 4 passed` — brak angielskiego tytułu.
- GREEN ograniczonej grupy interfejsu i sąsiednich kontraktów: `83 passed, 1 skipped, 4 deselected`; raport `state/youtube-issues-19-20/import-ui-tests.xml` w profilu AMC. Obejmuje rzeczywiste wywołanie metody importu z atrapą transportu, wybór jednego źródła, anulowanie obu okien i identyczność polecenia menu/palety/pomocy/Ctrl+O. Nie dowodzi natywnej dostępności wx/NVDA.
- Cztery wyłączone testy są potwierdzonymi osobno awariami bazy `cbad568`: dwa testy klawiszy dostępu menu (brak `&` przy kopiowaniu nazwy pobranego pliku), dwa testy ogólnej kompletności tłumaczeń (starsze kontrolki/napisy poza importem). Nie oznaczono pełnej regresji jako zielonej ani nie zmieniano zakresu zadania, by naprawiać te braki.
- Szablon tłumaczeń odtworzono istniejącym generatorem; test jego zgodności przechodzi po dodaniu nowych etykiet. `git diff --check` bez błędów.
- Ograniczony niezależny przegląd interfejsu wskazał brak jawnego tłumaczenia selektora pliku i dynamicznych stanów wyboru. Potwierdzono nowym testem RED (`1 failed, 5 deselected`). Dodano jawne `i18n.ui_text` dla tytułu/kontrolek/selekcji i selektora pliku oraz angielskie stany; `9 passed, 15 deselected` w grupie korekty i zgodności szablonu, raport `state/youtube-issues-19-20/import-ui-review-correction.xml`. Istniejący ogólny handler `_on_init_dialog` dodatkowo lokalizuje drzewo okna, ale sam nie dowodzi tłumaczenia natywnego filtra plików ani odświeżanych wierszy.
- Testy backendu/importowanych danych, kolekcji i transmisji zostaną dopisane dopiero po rzeczywistym zakończeniu prac wykonawczych.

## Znane ograniczenia

Nadal obowiązuje hold bezpieczeństwa po nierozstrzygniętych detekcjach RCX. Nie budować nowego instalatora ani paczki aplikacji, nie instalować i nie uruchamiać AMC lub dotkniętych kandydatów. Odbiór żywego Windows/NVDA jest osobną, wstrzymaną bramką. Główny komputer użytkownik aktualizuje sam.

## Wersja i commit

Brak nowego wydania, instalacji i publikacji binariów. Nowe commity źródeł zostaną zapisane dopiero po testach i przeglądzie.

## Następny krok

Wykonać trzy odizolowane zakresy źródłowe z testami RED/GREEN, następnie zintegrować tylko zaakceptowane zmiany i zapisać rzeczywisty wynik każdego kryterium.
