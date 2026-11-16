# HUBERT-20261116 — zgłoszenia, powiadomienia i wspólne wydanie

Status: W trakcie.

## Polecenie i korekta użytkownika

16.11.2026 Michał polecił w swojej notatce „Hubert zgłoszenia 2026-11-16.md” wdrożyć #17 i #18, sprawdzić wcześniejsze #9–#11 i #14–#16, poprawić nadal występujące problemy, a pozostałe zamknąć po potwierdzeniu. Dopuszcza pytanie do zgłaszającego o aktualny stan. Osobnym wymaganiem są powiadomienia GitHub i Sygnalisty na bota AMC oraz publikacja aktualizacji Public i Test.

**Nowsza decyzja zastępująca wcześniejsze zgody instalacyjne:** użytkownik sam pobierze i zainstaluje aktualizacje na głównym komputerze. Nie zamykać tam AMC, nie instalować ani nie uruchamiać nowej wersji automatycznie. Instalacje testowe są dozwolone na komputerze Hermes. Informować o postępach. Test ma różnić się zakresem funkcjonalnym wyłącznie obecnością Apple Music; separacja danych, nazw i kanałów pozostaje zamierzona.

Użytkownik dodatkowo polecił rozbić zakres na osobne zadania. Nie zmieniać dostawcy na płatne API; bieżące wykonanie korzysta z openai-codex.

**Kontynuacja po zmianie sesji — późniejsza wyraźna dyspozycja Michała:** „Jak nowa sesja, to kontynuuj po prostu, nie muszę pisać”. Przy wznowieniu wykonania odczytać ten aktualny plan i nowsze korekty, sprawdzić stan Git i wykonawców, następnie kontynuować pierwszy niedokończony uzgodniony krok bez proszenia o dodatkową wiadomość „kontynuuj AMC”. Nowa sesja nie unieważnia zlecenia. Nie powtarzać odebranych etapów ani nie rozszerzać zakresu na inne zadania. Zapis tej zasady nie jest wdrożeniem automatu tworzącego sesję lub wybudzającego agenta; takiego mechanizmu nie deklarować bez rzeczywistego wdrożenia i próby.

**Doprecyzowanie 17.11.2026:** Michał potwierdził stałą zgodę na automatyczną kontynuację dużych zleconych prac. Dla tego zadania punktem końcowym są sprawdzone instalatory AMC Public i AMC Test opublikowane na GitHubie, wraz ze wszystkimi etapami rozpisanymi w tym pliku. Nie zatrzymywać się na odbiorze testu lub pojedynczej poprawki, nie czekać na kolejne „kontynuuj”. Zgłaszać rzeczywistą blokadę zamiast pomijać testy albo deklarować niezmierzone wyniki. Ograniczenia głównego komputera i płatnego API pozostają bez zmian.

## Stan wejściowy i bezpieczeństwo

- Repozytorium Hermes: `/home/michal/projekty/AMC`, gałąź `codex/amc-test-public-20261109`, baza `26950509629a2092b0cc4e7987e5a370d740db31`, zgodna z GitHub w odczycie przed rozpoczęciem.
- Pełne źródła i testy odtworzono z `git archive` dokładnego commita na głównym komputerze; 2982 pliki odpowiadają identyfikatorom blobów indeksu. Przed rozpoczęciem drzewo było czyste. Eksport Windows wymagał zweryfikowanej normalizacji wyłącznie CRLF→LF.
- Na głównym komputerze przeniesiono notatkę bez zmiany treści do `D:\Projekty Codex\AMC - notatki\Hubert zgłoszenia 2026-11-16.md`. Główny kod pozostaje w `D:\Projekty Codex\AMC - integracja wxPython`, instalacja Test w `D:\Projekty Codex\AMC Python`.
- Stara próba `Hermes\AMC-Python-proba-list-20261005` nie była repozytorium ani uruchomioną aplikacją. Usunięto ją dopiero po sprawdzeniu manifestu 1032 plików i zachowaniu pięciu materiałów (notatka Sonos, stan, manifest, opis i uruchamiacz) w `AMC - notatki\Archiwum proby 2026-10-07`. Dwa odsyłacze w dokumentacji głównego komputera poprawiono na archiwum; nie są to zmiany kodu ani instalacji.

## Podział i kryteria odbioru

1. **Aktualizacja i NVDA #17 + kontrola #14.** Osobny worktree `AMC-zadania/hubert17`. Żadnej instalacji niewybranego dodatku i żadnego wymuszonego restartu NVDA. Błąd dodatku nie może unieważniać poprawnej aktualizacji AMC. Przy starcie w trakcie instalacji: żadnej częściowej instalacji, sprawdzalna blokada i odtwarzanie poprzedniej całości po awarii. Testy RED/GREEN i kontrola toru rzeczywistego instalatora/updatera.
2. **Radio Archiwista #18.** Worktree `AMC-zadania/hubert18`. Dni tygodnia z uwzględnieniem języka interfejsu, stabilne identyfikatory i sortowanie, bez zmiany zapisanych dat/adresów. Ocena załączonej łatki, testy RED/GREEN i dokumentacja użytkowa.
3. **MP3 #15 i kolejka #16.** Worktree `AMC-zadania/hubert-audio-kolejka`. Weryfikacja już istniejących zmian względem pełnych zgłoszeń. MP3: rzeczywisty tor dekodowania i pomiar, nie sam opis. Kolejka: restart procesu, kolejność, trwałość i zachowanie po błędzie zapisu. Nie dublować poprawionego kodu; zgłosić granice dowodów.
4. **Spotify #9–#11.** Worktree `AMC-zadania/hubert-spotify`. Weryfikacja pełnych komentarzy i późniejszych korekt. Bieżący tor Web Playback SDK/Chrome oraz alternatywny Soloist wybierany po potwierdzeniu konfiguracji i sesji; Chrome pozostaje powrotem awaryjnym. Nie historyczny LibreSpot. Konto i katalog, trwała biblioteka, naturalny koniec i następny utwór w obu torach, wyjścia Chrome, 403 playlist oraz nieprawdziwe ostrzeżenie odświeżania. Prywatna kolejka AMC i kolejka Soloist/Spotify Connect są odrębne. Potrzebę żywego konta zgłosić zamiast fabrykować wyniki. Zgodnie z dodatkową dyspozycją Michała obserwować także zewnętrzne zgłoszenia kolejki Soloist; poniżej zapis świeżego odczytu.
5. **Historia #5 i PR #2 #3 #6 #7 #8.** Potwierdzić stan przyjęcia; nie otwierać ponownie zamkniętego zadania i nie kopiować drugi raz istniejących zmian.
6. **Powiadomienia.** Nowe i zmienione zgłoszenia/komentarze AMC i prywatnego intake, trwały kursor i deduplikacja publicznej zajawki Sygnalisty z prywatnym rekordem. Kanał AMC tego profilu; nie udostępniać prywatnych logów, poświadczeń ani załączników. Sprawdzić połączenie i rzeczywisty harmonogram.
7. **Profile i wydanie.** Kontrola parytetu wspólnych funkcji, celowane testy, niezależny przegląd, build obu profili, identyczność źródeł i tożsamość manifestów, odbiór instalatorów na Hermesie. Publikacja stabilna Public i prerelease Test, readback wszystkich zasobów i sum; zgodność metadanych aktualizatora. Na głównym komputerze wyłącznie ręczna aktualizacja użytkownika.

## Wykonanie

Etapy 1–4 zlecone do izolowanych worktree; integracja, zamykanie Issues i publikacja należą do prowadzącego. Żaden etap nie jest ukończony na podstawie samego raportu wykonawcy.

## Odbiór zmian z worktree

Wykonawcy oddali lokalne commity. Po przeglądzie i rzeczywistych testach do gałęzi wydania scalono #17, bezpieczną część #10 oraz poprawione #18. Pierwotne propozycje #18 i EOS Spotify zostały zatrzymane do korekty; regresję #18 poprawiono, odrzucony EOS usunięto z kandydata. Nie zamknięto zgłoszeń i nie opublikowano pakietów. Prowadzący sprawdził bezpośrednio stan Git i diffy.

- **#17:** kandydat `b51e21248844f5a1292ed4e8c54768e8ba3b14cb` (kod `1f53cb61726619763e56585d9e2f060bf2a35fda`) przeszedł niezależny przegląd bez konkretnej usterki. Zintegrowany jako `f136cf6` i `c8c0c7f`; testy ponowione w gałęzi wydania: **34 passed in 0.22s**. Pierwsza próba po cherry-pick nie znalazła plików, bo początkowy sparse checkout nadal był włączony; wyłączono go i dopiero wtedy wykonano testy. Zachowano dwa wcześniejsze własne pliki dokumentacyjne. Nie zalicza to rzeczywistej instalacji Windows ani całego #14.
- **#18:** pierwotny kandydat `6a9e7db7d0626fd3287f91b95448914421b588de` zatrzymano po review starej etykiety otwartej listy. Poprawiony `5e82f5b4611ce991f0fd37db436f2f43c5548fc9` przeszedł ponowione przez prowadzącego 44 testy źródła, ustawień PL→EN→PL i celowanego i18n. Lokalnie zintegrowano kod i dokumentację jako `c665022`, `a89f62d`, `b85fb7142d31788ee11e674e689d9e42a1650a5a`. Po integracji testy #18 wraz z profilami, helperem dodatku #17 i wpięciem #10: **90 passed in 1.72s**. Wybrany RowID, kolejność i breadcrumb zostają, bez ponownego wywołania źródła. Nadal brak żywego odbioru NVDA i instalatora.
- **#9–#11:** pierwotny kandydat `c48081fe9ca51a01832bb332ca205877e53a94dd` odrzucono z powodu heurystyki EOS. Bezpieczny `b51d2b494d11ed6666cfa72398e9f89264ec7432` zachowuje wyłącznie korektę oceny kompletności #10 i prawidłowe wpięcie helpera; zintegrowano lokalnie jako `fb98ac29b2bbff76643102e0f73fde8e43b464bf`. Prowadzący wyeksportował dokładny kandydat na osobny NTFS (2986 plików, 0 brakujących), zbudował ProtocolTests i rzeczywisty LiteHost (oba kod 0, 0 błędów i ostrzeżeń), uruchomił zestaw kompletności (1 zestaw PASS) i regresję catalog/profile (2 zestawy PASS). XML wiring ponowiono po integracji: 1 test OK. Drzewa C# źródeł i ProtocolTests identyczne po integracji. Nie zalicza to OAuth/NVDA #9, synchronizacji żywego konta i cache #10 ani rzeczywistego EOS #11; zgłoszenia pozostają otwarte. Notatka jest teraz w `docs/zadania/HUBERT-SPOTIFY-20261116.md`.
- **#15/#16:** dokumentacyjny wynik `f218f5d4e6498f498c74b83db931630f06a54bc4` nie zawiera nowej poprawki. Istniejący limiter MP3 i własny magazyn kolejki są widoczne w kodzie; nie zastępuje to pomiaru aktualnego dekodera ani restartu osobnego procesu. Pozostają otwarte wymagane próby.
- **Narzędzia:** początkowy brak SDK na Windowsie Hermesa odblokowano prywatną kopią istniejącego SDK z głównego komputera (sam odczyt, bez zmiany tej maszyny). Niekompletnego pobrania Linux nie użyto. Rzeczywiste buildy/testy C# opisano poniżej; host produkcyjny kompiluje się, ale nie jest to jeszcze gotowa paczka ani odbiór odtwarzania.
- **Powiadomienia AMC/Sygnalisty:** odebrano skrypt `scripts/amc_issue_watch.py` w profilu AMC; prowadzący odtworzył i usunął błąd/dublowanie pary pojawiającej się w dwóch kolejnych odczytach. Po własnych korektach sam AMC ma 9 testów; łącznie z niezmienionym Soloist **12 passed in 0.63s**. Rzeczywisty odczyt API był cichy, kod 0; 11 publicznych rekordów, jedna skorelowana para formularza. Cron `0764fb911f0d` działa co 5 godzin zgodnie z wyraźną korektą Michała (zastępuje początkowe 30 minut), `no_agent=true`, `deliver=origin`; odczyt listy potwierdził włączony harmonogram i rzeczywistą próbę przez scheduler: `last_status=ok`, bez błędu. Bez prywatnych treści i bez adresów w zbiorczej wiadomości, wyłącznie numer i neutralny typ zmiany. Szczegóły w `docs/szkic-amc-issue-watch.md` profilu. Cotygodniowy monitor Soloist pozostaje bez zmian.

### Wynik niezależnego przeglądu i korekta zakresu

- **#18 regresja usunięta i kod scalony:** test prawdziwej ścieżki zapisu ustawień wykazał stare etykiety po PL→EN; po zmianie korzysta ona ze wspólnego `ListModel.replace()` dla istniejących identyfikatorów dni. Test PL→EN→PL potwierdza etykiety, RowID, kolejność, breadcrumb, niezmieniony model Plików i brak wywołania źródła. Rzeczywisty odczyt NVDA pozostaje osobną bramką.
- **#11 propozycja odrzucona i wycofana:** stan „gra blisko końca → wstrzymane przy 0” może oznaczać zewnętrzną pauzę i przewinięcie; dla utworu ≤3 s heurystyka działa już od początku. Fałszywy `PlaybackEnded` dochodziłby do frontendu i uruchamiał następny lokalny element. W bezpiecznym kandydacie oba adaptery są identyczne z bazą; brak detektora, testu i rejestracji odrzuconego EOS. Prowadzący potwierdził pusty diff adapterów. Istniejącego problemu EOS to nie rozwiązuje; #11 pozostaje otwarte.
- **#10 bramka kompilacyjna zaliczona:** brakujący link helpera do rzeczywistego LiteHost poprawiono po RED→GREEN statycznego testu XML. Prowadzący wykonał później prawdziwe testy C# i build konsumenta z wynikiem opisanym wyżej. Wynik nie obejmuje żywego konta i cache.
- **Profile (wstępnie):** celowane testy `test_release_profile.py`, instalatora i helpera dodatku po integracji #17: **45 passed in 1.08s**. Nie jest to jeszcze porównanie gotowych paczek Public/Test.

### Odblokowanie rzeczywistych testów C# na Hermesie

Pobieranie Linux SDK zakończyło się błędem odczytu sieciowego; nie użyto tej niekompletnej paczki. Alternatywnie skopiowano istniejący katalog .NET z głównego komputera przez odczyt SSH/tar bez zapisu, instalacji ani uruchamiania AMC na tym komputerze. Prywatny SDK działa na Windowsie Hermesa pod `C:\Users\Michal\AppData\Local\AMC-BuildTools\dotnet`; `--list-sdks` zawiera wymagany 8.0.423.

Źródła dokładnego `c8c0c7f3992462ed9a86898c87f3f182cbc2ff34` rozpakowano na NTFS: `C:\Users\Michal\AppData\Local\AMC-Hermes-Build\c8c0c7f39924`, 2984 pliki, brakujących 0. Rzeczywisty build `AccessibleMediaController.LiteHost.ProtocolTests` Release przeszedł (0 błędów, 0 ostrzeżeń). Runner uruchomiony z `--persistence --spotify-catalog --spotify-profile` zakończył się kodem 0: `QueuePersistenceTests: OK`, wszystkie trzy zestawy zaliczone. Następnie rzeczywisty host produkcyjny `AccessibleMediaController.LiteHost` również zbudował się Release (0 błędów, 0 ostrzeżeń, 8.29 s). To testy i build na bazie + #17, nie odbiór proponowanej #10 ani żywego konta; test magazynu nadal nie zastępuje restartu dwóch osobnych procesów hosta.

### Odbiór aparatury #14 zaliczony; rzeczywista aktualizacja nadal otwarta

Rzeczywisty runner `AccessibleMediaController.PythonLauncher.Tests` na Windowsie Hermesa zakończył się kodem 1: jedno niepowodzenie z 46, `aktualizator wykrywa żywy proces z instalacji`. Zatrzymano wniosek o gotowości aktualizatora. Powtórzenia samego `UpdaterFindsRunningInstalledProcess` potwierdziły błąd; pomiar wykazał, że użyty przez fixture skopiowany `cmd.exe` z poleceniem `ping -n 30` kończy się przed ponownym skanem. Odtworzenie z `ping -n 300` i `ping.exe -n 300` też kończy proces po około 0.8 s, exit 1, stderr `Serwer DNS nieautorytatywny dla strefy.`

Kontrola z bezwzględną ścieżką `C:\WINDOWS\system32\ping.exe` utrzymała proces żywy, a niezmieniony guard wykrył go w trzech skanach. System32 jest w PATH, PATHEXT zawiera EXE, a `where.exe ping` znajduje systemowy plik; nie ustalono jeszcze przyczyny różnicy, więc NIE przypisywać jej brakowi PATH ani uprawnieniom. Delegacja `deleg_0497ff6f` zatrzymała się bez zmian na niepotrzebnie wymaganym standalone Codex CLI. Wznowiona `deleg_591dabbb` używa narzędzi bieżącego openai-codex, bez instalacji CLI, nowego OAuth i płatnego API; jej zakres to wyłącznie aparat testu w osobnym worktree `hubert14-fixture`. Produkcyjny guard nie został zmieniony; żadnego AMC nie zamknięto. Skrypt sondy jest w scratch profilu AMC: `amc-guard-probe-20261116.py`.

Wynik wznowionej delegacji: `dbfa07e38123b43a2989ec58e232ea3f3a183ac6` zastępuje proces `cmd/ping` własnym runnerem testów, handshake `READY` i oczekiwaniem na stdin. Zachowano asercje dokładnie jednego blokera, jego PID i ścieżki wewnątrz instalacji; produkcyjny guard i całe `src` w kandydacie bez zmian. Wykonawca zmierzył na czystej bazie RED **45/46** i po zmianie GREEN **46/46**, następnie trzy kolejne poprawne pełne przebiegi bez pozostawionych procesów.

Prowadzący niezależnie przejrzał diff i SHA-256 plików, utworzył własny staging dokładnego kandydata `hubert14-parent-dbfa07e38123` (2985 plików, 0 brakujących i 0 rozbieżnych hashy), wymusił Release rebuild (0 błędów/ostrzeżeń) i uruchomił rzeczywisty Windows runner: **46/46**, kod 0, brak pozostałych procesów próbnych. Zintegrowano lokalnie jako `d52fa980c0db6d8cf9bd876c14d6d8da1351fe3d`. Wszystkie pliki projektu i linkowane źródła po integracji identyczne z odebranym kandydatem. Dokumentacja: `HUBERT-14-fixture-20261116.md`; log scratch profilu: `amc-hubert14-parent-acceptance.log`. Odbiór aparatury zakończony; #14 nie zamknięto, aktualizacji/instalatora nie odebrano i niczego nie publikowano.

### Kontrola błędów pełnego i18n przy odbiorze #18

Prowadzący utworzył czysty detached worktree bazy `2695050` w scratch profilu i uruchomił pełny `test_i18n.py` oddzielnie na nim oraz na kandydacie `5e82f5b`. Oba wyniki: **2 failed, 13 passed, 1 skipped**; padają te same dwie inwentaryzacje tłumaczeń. Porównanie samych skróconych repr zbiorów było nieważnym komparatorem (kolejność haszowania); zastąpiono je pomiarem pełnych, posortowanych różnic na liniach rzeczywistych asercji. Różnice obu drzew są identyczne: 161 braków dokładnych tekstów, 12 tekstów ustawień, 55 różnic szablonów. Są to błędy potwierdzone pomiarem na bazie, nie nowe regresje #18; nie raportować całego i18n jako zielonego. Logi scratch: `amc-i18n-base-vs-18.json`, `amc-i18n-canonical-differences.json`.

### Starsze #5 i propozycje #2, #3, #6, #7, #8

Ponowny odczyt GitHub potwierdził: #5 i wszystkie pięć PR-ów są zamknięte. PR-y mają `merged_at=null`: nie przedstawiać ich jako scalonych przez mechanizm GitHub. Komentarze Huberta wyjaśniają ręczne uwzględnienie zmian w innych commitach i jego odbiór:

- #2: wskazał `239c7e8`, `32fb6c0`, `f1c0934` i Public 29.10, 19:24.
- #3: wskazał `c36c833`, poprawkę kopii `5428b27` i to samo wydanie Public.
- #6, #7, #8: każdy ma potwierdzenie obecności w Public 30.10, 20:03, alpha.448, `5e474b9`.
- #5: Hubert potwierdził rozwiązanie na 42 866 utworach w Test 31.10, 13:35, alpha.455 i zamknął zgłoszenie. Wyraźnie napisał, że zawieszenie usunęła lista wirtualna bez jego alternatywnej wskazówki pozostawiania widocznej listy przy odtwarzaczu. Nie wdrażać tej historycznej alternatywy ani nie otwierać zgłoszenia ponownie bez nowej reprodukcji. To odczyt istniejącego odbioru zgłaszającego, nie nowy pomiar NVDA w tej sesji.

## Materiał do dokumentacji użytkownika

Szkic: aktualizator respektuje wybór dodatku NVDA, a Radio Archiwista dopowiada dzień tygodnia przy dacie. To wymagania do wdrożenia, nie potwierdzenie działania ani wydania. Pełny tekst do korekty powstanie z wyników zadań.

## Uzasadnienie i decyzje

Najnowsze decyzje w notatce użytkownika mają pierwszeństwo przed historycznymi rekordami. Status otwartego Issue nie dowodzi braku poprawki; zapis w rejestrze i test na atrapie nie dowodzą działania na żywym koncie lub urządzeniu. Publikacja ma czekać na weryfikację, a nie kończyć się samą zmianą źródeł.

## Monitoring kolejki Soloist — uzupełnienie 16.11.2026

Michał polecił obserwować zgłoszenia Soloist, o których Codex wspominał tego dnia. Świeży odczyt GitHub API wraz z komentarzami potwierdził dwa nowe, otwarte wątki:

- `spotify/soloist#37`: żądanie przejścia do istniejącej pozycji kolejki po UID bez utraty kontekstu. Dzisiejsze `play` pojedynczego URI zastępuje kontekst i opróżnia dotychczasową kolejkę; późniejsze `skip_next` może tworzyć inną kolejkę autoplay. Proponowana nazwa komendy jest ilustracją autora, nie istniejącą funkcją.
- `spotify/soloist#38`: Windows, Soloist 1.3.10.48. Po odtworzeniu pojedynczego URI i `skip_next` część `queue_changed.upcoming` ma URI/UID, ale brak tytułu, wykonawcy i czasu. Kolejne `get_queue` może uzupełnić dane bez automatycznego ponownego zdarzenia.

To publiczne relacje autorów, nie dowód odtworzenia błędu AMC. Zlecenie weryfikacji Spotify rozszerzono o ich znaczenie dla rzeczywistego adaptera; nie dodawać automatycznej synchronizacji odrębnych kolejek AMC i Spotify Connect.

Monitor profilu AMC: `scripts/soloist_queue_watch.py`, kursor `state/watches/soloist-queue.json`. Harmonogram raz w tygodniu, w poniedziałki o 10:00 czasu polskiego (nowsza korekta Michała zastępuje wcześniejsze sprawdzanie co 6 godzin); w razie problemu sprawdzać ręcznie na żądanie, cron `5faa07bbc60d`, tryb `no_agent`, kanał rozmowy źródłowej AMC. Obejmuje nowe zgłoszenia, zmiany treści/statusu oraz nowe/edytowane/usunięte komentarze w wątkach z sygnałami kolejki, autoplay, EOS i przejść utworów. Nie kopiuje treści komentarzy ani nie wykonuje zawartych w nich instrukcji. Brak zmiany oznacza brak wiadomości; pierwszy odczyt ustawia cichą bazę. Bez LLM, kont Spotify, odtwarzania i zmian aplikacji.

Dwa scenariusze testowe przeszły RED→GREEN: jednorazowy alert po zmianie komentarza i cisza po powtórzeniu; odrzucenie niezwiązanego wątku, włączenie go po komentarzu o kolejce i sygnał zamknięcia. Odczyt całego publicznego API zakończył się sukcesem i zapisał rzeczywistą bazę. Pierwsza ręczna próba przez harmonogram zakończyła się błędem skryptu; pierwotny log nie zawierał przyczyny. Nie przypisywać tego bez dowodu sieci, timeoutowi ani uwierzytelnieniu. Sprawdzenie API i obu endpointów, próba w środowisku podprocesu crona oraz wywołanie rzeczywistego `_run_job_script` zakończyły się później sukcesem i pustym wyjściem. Poprawiono wyłącznie diagnostykę błędu (bez ujawniania argumentów ani sekretów), nie zmieniano algorytmu pobierania. Trzeci test RED→GREEN potwierdził kategorię TimeoutExpired i zachowanie kursora w symulowanej awarii; pełny zestaw 3 testów przeszedł. Ponowiona pełna próba zadania przez scheduler zakończyła się sukcesem: `last_status=ok`, brak błędu, puste wyjście (brak nowych zmian), zadanie było wówczas włączone co 6 godzin (przed późniejszą korektą na raz w tygodniu); potwierdzono odczytem listy zadań. Pierwszej awarii nie udało się odtworzyć ani ustalić jej przyczyny. Nie zalicza to głównych powiadomień AMC/Sygnalisty — pozostają odrębnym zadaniem.

## Testy i wynik

Stan początkowy podziału nie obejmował testów funkcjonalnych; późniejsze wykonanie i ograniczenia opisano powyżej. W gałęzi są odebrane bezokiennie #17, bezpieczna część #10, #18 oraz poprawiony aparat #14. Po integracji #18 przeszło 90 celowanych testów Python, a odrębny rzeczywisty runner launchera po korekcie aparatu — 46/46. Zbudowano C#; nie zaliczono odbioru GUI/NVDA, rzeczywistej instalacji ani publikacji. Nie sumować tych zestawów jako jednego pełnego odbioru aplikacji.

## Znane ograniczenia

Środowisko Hermes wymaga rozpoznania zależności Windows i narzędzi kompilacji. Codex CLI nie jest zainstalowany w lokalnym WSL; zadania wykonują narzędziowi podwykonawcy z bieżącym dostawcą openai-codex, bez przełączania na API. Katalog głównego komputera z pustym dawnym folderem notatki może być trzymany przez edytor; nie zamykano edytora ani nie przerywano pracy.

## Wersja i commit

Baza: `26950509629a2092b0cc4e7987e5a370d740db31`. Brak nowej wersji i wydania na etapie rozpoczęcia.
