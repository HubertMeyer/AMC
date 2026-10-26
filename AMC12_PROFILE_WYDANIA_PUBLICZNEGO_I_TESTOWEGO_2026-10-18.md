# AMC12 — profil wydania publicznego i testowego

> **Korekta użytkownika z 24 października 2026 r. — zastępuje wcześniejsze
> ustalenia o równoległych magazynach i niezależnej bazie publicznej.** Bieżące
> źródła `AMC Test` są zawsze jedyną bazą następnego instalatora publicznego.
> Instalator korzysta z istniejącego profilu użytkownika, żeby można go było
> od razu sprawdzić na rzeczywistych danych. Profil publiczny nie cofa kodu do
> dawnej wersji i nie tworzy drugiej linii rozwoju; jedynie ukrywa funkcje
> wskazane jako niegotowe dla danego wydania. Poniższe akapity o osobnych
> magazynach, osobnych instalacjach i migracji danych mają wyłącznie wartość
> historyczną i nie są już obowiązującą specyfikacją.

Data ustalenia: 18 października 2026 r.

Status: zatwierdzono model jednego kodu i dwóch profili wydania oraz bezpieczne utrzymywanie równoległych danych użytkowych. `AMC Test` jest domyślnym źródłem danych dla publicznego `AMC`, ale oba profile zachowują osobne magazyny. To specyfikacja poziomu A do wdrożenia razem z niezależnym instalatorem AMC12. Nie zmieniono instalatora ani kodu produkcyjnego, nie kompilowano i nie uruchamiano AMC.

## Nazwy użytkowe

- wydanie publiczne: `Accessible Multimedia Controller`, krótko `AMC`;
- prywatne wydanie testowe użytkownika: `Accessible Multimedia Controller — Test`, krótko `AMC Test`;
- numer wersji jest osobnym polem, na przykład `1.0.0`; nie dokładamy cyfry do nazwy produktu jako `AMC 1`;
- nie używamy nazwy `AMC Python`. Python jest szczegółem technicznym, a ten tekst ma zostać usunięty z przypadkowych komunikatów NVDA w AMC01.

Przykładowe nazwy plików instalatora: `AMC-1.0.0.exe` i `AMC-Test-1.0.0.exe`.

## Jeden kod, dwa profile

Nie tworzymy dwóch rozwijanych osobno kopii aplikacji. Ten sam kod jest budowany z jawnym manifestem możliwości wydania:

- profil `public`: tylko funkcje dopuszczone do stabilnego użycia przez odbiorców zewnętrznych;
- profil `test`: funkcje publiczne oraz świadomie włączone eksperymenty użytkownika.

Manifest jest częścią podpisanego lub weryfikowanego pakietu. Nie wolno wybierać profilu po nazwie konta Windows, obecności tokenu, ścieżce komputera ani ręcznej zmianie zwykłego ustawienia.

## Izolacja instalacji

Profile muszą mieć osobne:

- identyfikatory produktu i instalatora;
- foldery programu oraz skróty z jednoznacznymi nazwami;
- kanały i manifesty aktualizacji;
- ustawienia, pamięć podręczną, logi i pliki tymczasowe;
- przestrzenie nazw poświadczeń w Menedżerze poświadczeń Windows;
- identyfikację procesu przekazywaną mechanizmowi jednej instancji.

Dzięki temu `AMC` i `AMC Test` mogą istnieć obok siebie. Aktualizacja albo awaria wydania testowego nie zastępuje plików publicznych i nie uszkadza jego profilu.

Nie używamy wspólnego zapisu obu wydań do tych samych plików ani baz. Import początkowy pozostaje jawną operacją z kopią bezpieczeństwa, ale po nim dozwolone jest wielokrotne, kontrolowane odświeżanie zgodnych danych z `AMC Test` do publicznego `AMC`.

## Równoległe dane użytkownika

### Wynik audytu obecnego magazynu

Obecny AMC zapisuje zwarty stan ustawień w `state.json`, lokalną Bibliotekę w `library.db`, a Podcasty i YouTube w `podcasts.db`. Ten sam model stanu obejmuje też radio, harmonogramy, historię, zakładki oraz dane Spotify i TIDAL-u. Istniejący pełny eksport nie nadaje się więc do automatycznego kopiowania między profilami: przenosi zbyt szeroki zakres, a starsze wydanie odrzuca kopię utworzoną przez nowszy schemat.

AMC12 ma dodać osobny, wersjonowany format `migawki danych wspólnych`. Migawka nie jest kopią `state.json` ani plików SQLite. Powstaje przez jawny wybór obsługiwanych pól, jest zapisywana atomowo i ma własną wersję zgodności niezależną od wersji wewnętrznej bazy.

### Kierunek synchronizacji

- domyślnym źródłem jest `AMC Test`, ponieważ to ono będzie zwykle używane przez właściciela;
- publiczne `AMC` może mieć włączoną opcję `Odświeżaj dane z AMC Test przy uruchomieniu` oraz polecenie ręczne `Odśwież dane z AMC Test`;
- przed uruchomieniem publicznego AMC używana jest tylko ostatnia kompletna, poprawnie zweryfikowana migawka. Niedokończony albo uszkodzony eksport nie zastępuje wcześniejszych danych;
- gdy `AMC Test` działa, migawka powstaje z odłączonego, spójnego stanu po zakończeniu zapisu, a nie przez kopiowanie otwartej bazy SQLite;
- gdy publiczne AMC ma własne zmiany, automatyczne odświeżenie nie nadpisuje ich po cichu. Zatrzymuje się i podaje krótkie podsumowanie; użytkownik może przyjąć dane testowe albo zachować publiczne;
- pierwsza wersja nie wykonuje automatycznej synchronizacji z publicznego AMC z powrotem do `AMC Test`. Osobne polecenie `Przenieś zmiany do AMC Test` może zostać dodane później z podglądem konfliktów. Nie wolno tworzyć niejawnej synchronizacji dwukierunkowej;
- brak `AMC Test` na komputerze nie jest błędem publicznego wydania i nie pokazuje niepotrzebnych komunikatów zwykłemu użytkownikowi.

### Dane powielane

Migawka może przenosić tylko dane występujące i obsługiwane w obu profilach:

- źródła, kolejność, metadane i pozycje odtwarzania Biblioteki lokalnej;
- historię odtwarzania i wyszukiwania, zakładki nazwane, rozdziały użytkownika oraz lokalne playlisty AMC;
- stacje radiowe, Bibliotekę radia, ulubione, kolejkę i presety;
- subskrypcje Podcastów i YouTube, zapisane odcinki, stan `nowy`, `rozpoczęty`, `odtworzony`, pozycję i ścieżki pobranych plików;
- historię nagrywania i odwołania do istniejących plików nagrań;
- definicje harmonogramów wraz z ich trwałymi identyfikatorami;
- opcjonalnie wspólne ustawienia użytkowe, takie jak komunikaty, długości przewijania, foldery nagrań i pobierania oraz własne profile klawiatury, po odfiltrowaniu poleceń nieobecnych w wydaniu publicznym.

Fizyczne pliki audio, pobrania i nagrania nie są dublowane. Oba profile mogą wskazywać te same pliki użytkownika, a synchronizacja przenosi wyłącznie bezpieczne metadane i ścieżki.

### Dane zawsze osobne albo pomijane

- kanał aktualizacji, identyfikator produktu, manifest możliwości i wersja schematu wewnętrznego;
- ostatnia sesja, kolejność sesji oraz ustawienia funkcji, których profil docelowy nie zawiera;
- tokeny, kody logowania, hasła i wpisy Menedżera poświadczeń Windows;
- katalogi, playlisty i stan Spotify, TIDAL-u lub innej usługi nieobecnej publicznie;
- logi, pamięć podręczna, pliki tymczasowe, aktywne zadania, kolejki odpowiedzi sieciowych i stan trwającego nagrywania;
- fokus, otwarte okna i inne chwilowe dane interfejsu, które mogłyby przejąć kontekst drugiego profilu.

### Harmonogramy bez podwójnego nagrywania

Definicje harmonogramów mają być takie same i widoczne w obu profilach, ale globalny koordynator na komputerze przyznaje prawo wykonywania harmonogramów tylko jednemu profilowi naraz. Domyślnym wykonawcą jest `AMC Test`.

- publiczny wiersz może mówić na przykład `Włączony, wykonywany przez AMC Test`, bez technicznego identyfikatora blokady;
- polecenie `Przejmij wykonywanie harmonogramów w tym wydaniu` przenosi prawo atomowo i wymaga potwierdzenia;
- przejęcie jest zablokowane, gdy którekolwiek wydanie właśnie nagrywa albo finalizuje plik;
- uruchomienie obu programów nie może rozpocząć dwóch kopii tego samego wystąpienia;
- brak uruchomionego właściciela nie powoduje cichego przejęcia przez drugi profil. Program informuje o niewykonanym planie zamiast ryzykować podwójne nagranie;
- historia wykonania wraca w następnej migawce danych wspólnych, ale aktywny zapis i uchwyty pliku nigdy nie są synchronizowane.

### Dostępne polecenia

- `Odśwież dane z AMC Test`;
- `Stan synchronizacji danych`;
- `Przejmij wykonywanie harmonogramów w tym wydaniu`.

Polecenia pojawiają się w Ustawieniach, `Ctrl+F1` i palecie `Ctrl+Shift+K` tylko wtedy, gdy drugi profil jest zainstalowany albo istnieje poprawna migawka. Wynik ma podawać czas migawki oraz krótkie liczby przeniesionych kategorii, bez ścieżek baz, nazw klas i wersji technicznych.

## Publiczne integracje urządzeń i TIDAL

- WiiM należy do publicznego `AMC` jako opcjonalna, początkowo wyłączona sesja. Świeże uruchomienie nie skanuje sieci bez polecenia użytkownika;
- Sonos jest celem publicznym, ale profil wydania włącza go dopiero po wdrożeniu stabilnego publicznego brokera HTTPS i zaliczeniu pełnej próby na koncie spoza środowiska autora;
- jeżeli brama Sonosa nie jest zamknięta dla konkretnego wydania, Sonos pozostaje całkowicie ukryty zamiast pokazywania niedziałającej obietnicy;
- TIDAL występuje wyłącznie w `AMC Test`. Publiczne `AMC` nie pokazuje jego sesji, ustawień konta, pomocy, palety ani pozycji `Niedostępne`;
- użyteczne API katalogu, biblioteki i synchronizacji TIDAL-u pozostaje dostępne do prywatnego rozwijania. Nie jest ono jednak dowodem przewidywalnego pełnego odtwarzania ani gotowości publicznej.

## Spotify

Do osobnej decyzji po AMC16:

- Spotify występuje wyłącznie w `AMC Test`;
- `AMC Test` obejmuje zatwierdzone AMC08: `Ctrl+P` otwiera natywne playlisty konta Spotify, a `Ctrl+Shift+P` dodaje do istniejącej playlisty albo pozwala utworzyć nową prywatną lub publiczną playlistę Spotify;
- publiczne `AMC` nie pokazuje Spotify w Menedżerze sesji, wynikach wyszukiwania, menu, Ustawieniach, `Ctrl+F1`, palecie `Ctrl+Shift+K` ani ekranie pierwszego uruchomienia;
- publicznego Spotify nie można przywrócić edycją zwykłego pliku ustawień;
- publiczny pakiet pomija składniki używane wyłącznie przez Spotify, o ile nie są potrzebne innej funkcji; test integralności wykrywa zarówno zbędny składnik, jak i osierocone polecenie;
- istniejące poświadczenia `AMC Test` nie są usuwane podczas instalacji, aktualizacji ani deinstalacji publicznego `AMC`;
- pomyślny eksperyment jednego logowania nie włącza funkcji automatycznie w publicznym profilu. Powstaje raport i dopiero osobna decyzja zmienia manifest publiczny.

## Stara alfa i migracja

Nie opieramy trwałego podziału kanałów na obecnej nazwie starej alfy ani na tym, że znajduje się już na komputerze. Przed jej późniejszym usunięciem instalator ma:

1. rozpoznać dokładną wersję i miejsce danych;
2. zaproponować import do `AMC Test` albo publicznego `AMC`, zależnie od rodzaju danych;
3. nie kopiować tokenów ani ustawień usług do profilu publicznego, jeżeli dana usługa jest tam nieobecna;
4. wykonać kopię i podać użytkowy wynik migracji;
5. usuwać starą instalację dopiero po sprawdzeniu uruchomienia właściwego nowego profilu.

## Aktualizacje

- `AMC` otrzymuje wyłącznie stabilne wydania publiczne;
- `AMC Test` otrzymuje wydania testowe i może być aktualizowane częściej;
- jeden kanał nie proponuje pakietu drugiego kanału;
- aktualizacja nie zamyka żadnego profilu podczas nagrywania;
- wersja, rozmiar i SHA-256 są sprawdzane przed zastąpieniem plików;
- wycofanie wadliwej wersji testowej nie zmienia publicznego `AMC`.

### Ochrona nagrywania przed instalatorem

Istniejący skrypt Inno Setup ma `CloseApplications=force`. To było użyteczne dla dawnych cichych aktualizacji, ale nie spełnia docelowej bramy publicznego wydania: instalator uruchomiony ręcznie albo przez zewnętrzny mechanizm nie może wymusić zamknięcia AMC podczas nagrywania.

Docelowy kontrakt:

- instalator i aktualizator najpierw pytają działającą instancję właściwego profilu o stan bezpiecznego zamknięcia;
- jeśli trwa nagrywanie lub finalizacja pliku, instalacja nie zamyka programu, nie zastępuje żadnego pliku i zapisuje aktualizację jako oczekującą;
- użytkownik otrzymuje krótki wynik `Aktualizacja poczeka na zakończenie nagrywania`, bez konieczności odpowiadania na kilka okien;
- gdy nie trwa nagrywanie, AMC wykonuje zapis stanu, kończy proces kontrolowanie, a pomocnik dopiero potem uruchamia instalator;
- brak odpowiedzi działającej instancji nie jest zgodą na wymuszone zamknięcie. Instalator odmawia podmiany i podaje, że AMC trzeba zamknąć świadomie;
- zasada obowiązuje ręczne uruchomienie instalatora, aktualizację w tle, naprawę i przejście między wersjami;
- osobne profile mają osobne kanały uzgodnienia. Aktualizacja `AMC` nie pyta `AMC Test` o zamknięcie i odwrotnie, chyba że operacja dotyczy wspólnego składnika, którego nie wolno wymienić podczas nagrywania w żadnym profilu;
- parametr Inno Setup pozwalający zamykać aplikacje może pozostać wyłącznie jako awaryjna, świadoma operacja serwisowa, nie jako domyślna droga publicznego instalatora.

## Wersja Portable

Wersja Portable ma sens jako dodatkowy sposób uruchamiania AMC bez instalacji, szczególnie do prób, komputerów bez uprawnień instalacyjnych i świadomego używania z dysku zewnętrznego. Została jednak świadomie odłożona poza obecny etap AMC11–AMC14. Nie zastępuje instalatora i nie blokuje pierwszego wydania publicznego.

Pierwszy zakres Portable:

- osobne archiwum `AMC-Portable-<wersja>-win-x64.zip`, przygotowane z tego samego profilu publicznego i tych samych zweryfikowanych plików co instalator;
- jawny znacznik trybu Portable obok programu, a nie rozpoznawanie trybu po przypadkowej nazwie folderu;
- ustawienia, bazy, pamięć podręczna, logi, komponenty FFmpeg i `yt-dlp` oraz pliki tymczasowe pod wersjonowanym katalogiem `Data` obok programu;
- osobna tożsamość jednej instancji, aby Portable nie przywoływało zainstalowanego AMC ani nie przekazywało mu plików;
- brak automatycznej rejestracji rozszerzeń, `Otwórz za pomocą`, skrótów i autostartu, ponieważ ścieżka wersji Portable może się zmienić albo zniknąć po odłączeniu dysku;
- pierwsza wersja może jedynie sprawdzać dostępność aktualizacji i pobierać nowe archiwum. Samodzielna podmiana działającego katalogu Portable wymaga osobnej, bezpiecznej implementacji;
- poświadczenia nie są zwykłymi plikami do przenoszenia. Jeżeli zostaną zapisane w katalogu Portable z ochroną konta Windows, kopia na inny komputer nie może ich odszyfrować i wymaga ponownego logowania;
- program sprawdza możliwość zapisu w swoim katalogu przed uruchomieniem. Tryb Portable w `Program Files`, na nośniku tylko do odczytu albo w katalogu synchronizowanym nie może cicho przejść na magazyny instalowanej wersji;
- usunięcie katalogu Portable usuwa program i jego zwykłe dane, ale instrukcja musi wcześniej wskazać eksport ustawień i plików użytkownika znajdujących się poza tym katalogiem.

Portable jest zadaniem średnim: samo spakowanie istniejącego publikowania jest proste, lecz trzeba prawidłowo przekierować wszystkie magazyny, aktualizator, komponenty, blokadę jednej instancji i poświadczenia. Rekomendacja: najpierw stabilny instalator x64, potem Portable x64 jako osobny etap odbioru, bez opóźniania pierwszego wydania.

## Windows na ARM

Rozróżniamy dwie różne obietnice:

1. `AMC x64 działa na Windows 11 ARM przez emulację` — to pierwszy, znacznie mniejszy etap.
2. `AMC ma natywny pakiet ARM64` — to osobne, większe zadanie wydawnicze.

Obecny łańcuch jest związany z `win-x64`: skrypt przywracania i publikowania, pakiet samowystarczalny, instalator oraz sumy kontrolne używają x64. Repozytorium zawiera też natywne lub architekturowe składniki:

- `bass.dll` wyłącznie z katalogu `third_party/BASS/win-x64`;
- host Librespot wyłącznie jako `win-x64`;
- zarządzany komponent FFmpeg pobierający pakiet Windows x64;
- składniki SoundTouch, SQLite i WebView2 wymagające potwierdzenia właściwych zasobów ARM64;
- testy i kontrolę integralności zakładające konkretne pliki oraz sumy x64.

Dlatego samo `dotnet publish -r win-arm64` nie tworzy działającego wydania AMC. Kod .NET można opublikować dla ARM64, ale wszystkie biblioteki ładowane do procesu muszą mieć zgodną architekturę. Osobne narzędzia x64 mogą ewentualnie działać jako procesy emulowane, lecz wymaga to jawnej decyzji, osobnych manifestów i prób.

Zalecana kolejność:

1. Po ukończeniu instalatora x64 sprawdzić zwykły pakiet x64 na prawdziwym komputerze z Windows 11 ARM: start, NVDA, audio, nagrywanie, Time Shift, FFmpeg, `yt-dlp`, aktualizacja i instalator.
2. Jeśli emulowane x64 działa poprawnie, opisać je uczciwie jako zgodność przez emulację i nie obiecywać natywnego ARM64.
3. Dopiero przy realnym zapotrzebowaniu przygotować macierz zależności ARM64 i usunąć albo zastąpić każdy blokujący składnik ładowany do procesu.
4. Zbudować osobne artefakty, manifesty, sumy i kanały `win-arm64`; aktualizator i instalator muszą wybierać architekturę bez możliwości podania pakietu x64 jako natywnego ARM64.
5. Odbiór natywnego wydania wykonać na prawdziwym urządzeniu ARM64 z NVDA. Test samej kompilacji na komputerze x64 nie wystarcza.

Publiczny profil ARM64 jest prostszy niż `AMC Test`, ponieważ publiczne AMC nie zawiera obecnie Spotify ani TIDAL-u. Mimo tego Radio, BASS, SoundTouch, FFmpeg, SQLite, WebView2, powłoka i aktualizator nadal wymagają oddzielnej weryfikacji.

Natywne ARM64 nie należy do pierwszego wydania instalatora i zostało świadomie odłożone. Najpierw wydajemy i stabilizujemy x64. Próba x64 pod emulacją na Windows 11 ARM oraz ewentualna osobna produkcja ARM64 nastąpią dopiero po późniejszej decyzji i nie wchodzą do bieżącej Bramy 5.

## Dostępność

- nazwa okna, informacje o wersji i wpis menu Start jednoznacznie rozróżniają `AMC` od `AMC Test`;
- zwykłe kontrolki nie wypowiadają nazwy profilu przy każdym ruchu, jeśli nie jest to potrzebne;
- listy i pola wyboru otrzymują jawne etykiety użytkowe, bez identyfikatorów manifestu i nazw wewnętrznych;
- pomoc i paleta są generowane z tego samego manifestu możliwości co interfejs, więc nie reklamują ukrytych Spotify, TIDAL-u ani niegotowego Sonosa;
- test NVDA obejmuje pierwsze uruchomienie obu profili, aktualizację, import, ponowne otwarcie i powrót fokusa po anulowaniu.
- test NVDA obejmuje też ręczne odświeżenie danych, ostrzeżenie o konflikcie, stan ostatniej migawki i przejęcie wykonywania harmonogramów.

## Kryteria odbioru

1. Oba profile można zainstalować obok siebie i uruchomić niezależnie.
2. Każdy profil aktualizuje wyłącznie siebie i ma jednoznaczną nazwę użytkową.
3. Publiczne `AMC` nie zawiera żadnej dostępnej drogi do Spotify ani osieroconego komunikatu na jego temat.
4. Publiczne `AMC` zawiera WiiM, zawiera Sonosa dopiero po jego bramie wydawniczej i nie zawiera żadnej dostępnej drogi do TIDAL-u.
5. `AMC Test` zachowuje istniejące prywatne funkcje i poświadczenia bez ujawnienia ich profilowi publicznemu.
6. Instalacja, aktualizacja, naprawa i deinstalacja jednego profilu nie uszkadzają drugiego.
7. Import starej alfy jest jawny, odwracalny przez kopię i nie miesza danych kanałów.
8. Po odświeżeniu publiczne AMC pokazuje te same zgodne stacje, podcasty, historię, zakładki, pliki i harmonogramy co źródłowe `AMC Test`, ale zachowuje własne ustawienia profilu.
9. Nowsza, uszkodzona albo przerwana migawka nie uszkadza ostatniego poprawnego stanu publicznego AMC.
10. Równoczesne uruchomienie obu profili nie wykonuje dwukrotnie tego samego harmonogramu.
11. Synchronizacja nie kopiuje Spotify, TIDAL-u, poświadczeń, logów ani aktywnego stanu nagrywania do profilu publicznego.
12. Wszystkie pakiety przechodzą test integralności, wersji, SHA-256, jednej instancji i ochrony aktywnego nagrywania.
13. Portable korzysta wyłącznie z własnego katalogu `Data`, nie rejestruje powłoki i nie miesza jednej instancji ani aktualizacji z wydaniem instalowanym.
14. Usunięcie lub przeniesienie Portable nie zostawia aktywnych skojarzeń prowadzących do nieistniejącego pliku.
15. Pakiet x64 na Windows 11 ARM jest opisany jako emulowany i przechodzi próbę na prawdziwym urządzeniu; natywne ARM64 nie jest deklarowane bez osobnego artefaktu i pełnego odbioru zależności.
16. Instalator uruchomiony podczas nagrywania kończy się bez zamykania AMC i bez podmiany plików, a aktualizacja pozostaje bezpiecznie oczekująca.

## Zależności i bramka

- AMC11 dostarcza oddzielne kanały aktualizacji i manifesty;
- AMC09 używa profilu możliwości w Menedżerze sesji;
- AMC10 dostarcza publiczne WiiM oraz warunkowo publicznego Sonosa;
- AMC06 nadaje harmonogramom trwałe identyfikatory i współpracuje z pojedynczym właścicielem ich wykonywania;
- AMC08 dostarcza w `AMC Test` natywne tworzenie i uzupełnianie playlist Spotify;
- AMC16 rozwija jedno logowanie Spotify wyłącznie w `AMC Test` do czasu osobnej decyzji;
- pełne wdrożenie i próba należą do Bramy 5 AMC12, gdy użytkownik nie nagrywa.
- Przed instalatorem AMC12 część aplikacyjna AMC14 dostarcza działające otwieranie plików, kolejkę i przekazanie do jednej instancji. AMC12 dopiero rejestruje ten kontrakt w powłoce Windows i sprawdza aktualizację oraz deinstalację.
- Portable x64, próba zgodności x64 na Windows 11 ARM i ewentualne natywne ARM64 są późniejszymi, niezależnymi etapami wydawniczymi poza bieżącą Bramą 5.

## Zasada architektoniczna i przyszła przenośność

Wybór .NET jako technologii rdzenia pozostaje właściwy. Model danych, harmonogramy, historia, Biblioteka, zakładki, obliczenia czasu, klienci HTTP i znaczna część logiki sesji mogą pozostać w `AccessibleMediaController.Core` bez zależności od interfejsu konkretnego systemu.

Nie oznacza to jednak, że dzisiejsza aplikacja jest automatycznie wieloplatformowa. Warstwa `AccessibleMediaController.Windows` używa WPF, Windows Forms, UI Automation, WASAPI/NAudio, rejestru, DPAPI, powłoki Windows, WebView2, Windows Media Control i współpracy z NVDA. Ewentualny port wymagałby nowego interfejsu oraz adapterów systemowych dla macOS albo Linux, przy zachowaniu wspólnego rdzenia.

Zasady na przyszłość:

- nowa logika domenowa trafia do Core, jeżeli nie potrzebuje API Windows;
- odczyt urządzeń, dźwięk, poświadczenia, powłoka, instalacja i dostępność pozostają za interfejsami implementowanymi przez warstwę systemową;
- Python pozostaje właściwy dla dodatku NVDA, narzędzi i cienkich integracji, ale nie przejmuje modelu danych ani głównej logiki AMC;
- Rust może być użyty w odizolowanym komponencie natywnym, jeżeli daje konkretną korzyść, tak jak osobny host Librespot, lecz nie ma powodu przepisywać w nim działającego rdzenia;
- nie rozpoczynamy portu na inny system bez realnej grupy użytkowników, sprzętu, czytnika ekranu i możliwości wykonania pełnych testów audio oraz dostępności.

## Źródła platformowe

- publikowanie samowystarczalnych pakietów .NET dla konkretnego RID: https://learn.microsoft.com/en-us/dotnet/articles/core/deploying/
- dodawanie obsługi Windows na ARM i znaczenie zależności: https://learn.microsoft.com/en-us/windows/arm/add-arm-support
- emulacja aplikacji x64 w Windows 11 ARM: https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation
- wymagania NVDA, w tym Windows 11 ARM64: https://api.nvaccess.org/documentation/userGuide.html
- obsługa architektur przez Inno Setup: https://jrsoftware.org/ishelp/topic_64bit.htm
