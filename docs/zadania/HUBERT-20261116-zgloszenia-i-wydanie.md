# HUBERT-20261116 — zgłoszenia, powiadomienia i wspólne wydanie

Status: W trakcie — rozwój i testy źródeł są kontynuowane; publikacja i uruchamianie objętych blokadą kandydatów pozostają wstrzymane.

## Korekta zakresu blokady — 17.11.2026

Użytkownik wyraźnie wymaga dalszej pracy nad działającą aplikacją przez Codex.
Alarm Defendera nie jest powodem zatrzymania rozwoju źródeł, przeglądu kodu
ani izolowanych testów z nieszkodliwymi procesami i danymi fixture. Wstrzymane
pozostają wykonanie i instalacja dotkniętych kandydatów, ponawianie dotkniętego
toru kompilacji/pakowania oraz publikacja; nie wyłączać ochrony ani nie
obchodzić wykrycia. Zachować wcześniejsze ważne testy zamiast powtarzać całość.

Uruchomiono dwie niezależne prace przez podagentów bieżącego dostawcy
openai-codex (bez odrębnie płatnego API): przegląd faktycznie niedokończonych
zachowań aplikacji oraz diagnozę wrappera instalatora na podstawie istniejących
logów. Poprawkę wolno wprowadzić po dowodzie błędu i proporcjonalnym teście;
nie zgadywać przyczyny `ISCC exit 2` ani nie przedstawiać samych nowych logów
jako usunięcia alarmu. Brak standalone Codex CLI na Hermesie nie jest brakiem
dostępu do bieżącego providera Codex. Raporty prac muszą rozdzielać poprawki
źródeł, testy, żywy odbiór i gotowość do wydania.

Przegląd aplikacji wskazał konkretny, wcześniej zgłoszony błąd z
`AMC-TEST-ZAWIESZENIE-20261110.md`, punkt 4. Prowadzący niezależnie odczytał
`gui.py`: `_menu_native_label` przekazuje przetłumaczone `strzałka w prawo`
po tabulatorze również przy `accelerator=True`, choć wx oczekuje technicznej
nazwy klawisza. Poprawka z behawioralnym RED/GREEN jest w osobnej delegacji;
ma zachować przypisania, flagi, opisy niebędące akceleratorami i obsługę pól
edycji. Nie przypisywać temu błędowi przyczyny wielogodzinnego zawieszenia.
Przegląd wskazał też starszy dług katalogu angielskiego; nie rozszerzono teraz
zakresu na hurtowe tłumaczenie.

Pierwsza poprawka menu `deleg_9a6ab2aa` ma `39 passed`, lecz **nie została
scalona**: niezależny przegląd wykazał regresję pomijaną przez test. Surowe
`Ctrl+Prior` i `Ctrl+Next` z rzeczywistych pozycji zmiany sesji nie są poprawną
składnią parsera wx. Prowadzący sprawdził przypięty `wxPython==4.3.1` i jego
submoduł wxWidgets `670835aec7e54b9e9d5a50d6a1aea1e8ba0bcdb2`, plik
`src/common/accelcmn.cpp`: zwykłe klawisze wymagają aliasów `PageUp`/`PageDown`
lub pozostałych jawnie rozpoznawanych nazw; `KP_Prior` dotyczy innego klawisza.
Do jednej ograniczonej korekty `deleg_ec0f1deb` przekazano minimalną konwersję
aliasów i testy AKTUALNYCH wpisów rejestru, w tym `Shift+Right`, `Ctrl+Right`,
`Alt+Right`, `Ctrl+Prior`, `Ctrl+Next`. Nie zmieniać przypisań ani flag.
Wcześniejsze wymaganie bezwarunkowego przekazywania surowego skrótu zostaje
skorygowane: celem jest składnia rozpoznawana przez wx, nie literalna kopia
wewnętrznego aliasu. To nadal kontrola kodu/formattera, nie żywy odbiór wx/NVDA.

Korekta `deleg_ec0f1deb` została odebrana i zintegrowana do kanonicznych źródeł.
Testy badają osiem rzeczywistych pozycji rejestru. Prowadzący dodał i naprawił
mały przypadek brzegowy nowego helpera (sam znak `+` nie może znikać); po
integracji ograniczony zestaw menu i historii zakończył się **41 passed in
3.02s**. Zachowano przypisania, flagi, `label_override` i czytelne podpisy bez
akceleratora; `git diff --check` przeszedł. Nie ma nowego pakietu, instalacji ani
żywego odbioru. Szczegóły: `AMC-TEST-ZAWIESZENIE-20261110.md`, punkt 4.

## Diagnoza wrappera i poprawa dowodów wykonania — 17.11.2026

Przegląd `deleg_6743783f` zakończony; prowadzący odczytał ponownie logi
`build-test-installer-alpha511-17e01.log`, `...-retry1.log` oraz
`build-test-installer-direct-verified.log`. Oba kanoniczne przebiegi kończą się
komunikatem wrappera o kodzie `2`; retry usunął pusty output, ale nie usunął
błędu. Zachowane transkrypty nie zawierają argv ISCC ani jego stdout/stderr.
Nie ustalono przyczyny różnicy i nie przypisano jej błędowi cytowania.

Potwierdzono lukę diagnostyczną. Wykonawca przygotował minimalną zmianę trzech
plików: `Start-ArgumentListSafeProcess.ps1`, `Build-AMCInstaller.ps1` oraz
`test_installer_argumentlist_compat.py`. Projekt zapisuje ścieżki EXE i źródła
(nie ich hashe), argv, cwd, stan oraz exit code; brak możliwości zapisania
dowodu przed startem ma zatrzymać proces. Nie przechwytuje stdout/stderr.
Kod z tego worktree został po review `deleg_af10f3ab` zintegrowany do
kanonicznych źródeł `/home/michal/projekty/AMC`, włączonych do zatwierdzenia
tego etapu w historii Git; bez publikacji nowego wydania.
Prowadzący przed integracją potwierdził niezmieniony zakres docelowy, wykonał
`git apply --check` i porównał SHA-256 wszystkich trzech skopiowanych plików
z zaakceptowanym worktree. `git diff --check` przeszedł.

Niezależny reviewer sprawdził na Windows PowerShell `5.1.26100.9711` fixture z
kodem `23`, niezapisywalny cel (proces nie ruszył), brak EXE (`launch-failed`)
i parser obu skryptów. Po integracji prowadzący dodatkowo uruchomił parsery
oraz krytyczną ścieżkę `launch-failed` na rzeczywistym PS 5.1: wynik `pass`,
exit `0`, dokładny JSON odczytany ponownie. Dowód prowadzącego:
`/home/michal/.hermes/profiles/amc/cache/scratch/installer-launch-failed-78b583f63dcd486b96502a5b0c9f08cc.json`.
Pierwsze uruchomienie sondy bez standardowego przełącznika procesu PS zostało
zatrzymane przez politykę wykonywania skryptów; właściwa próba użyła istniejącego
w testach `-ExecutionPolicy Bypass` tylko dla tego procesu, bez zmiany polityk
systemowych i bez zmiany ochrony Defendera.

Moduł pytest pod WSL zwrócił `3 skipped`, nie zaliczenie funkcji Windows.
Nie znaleziono natywnego Pythona przez PATH, PEP514 ani typowe katalogi
systemowe; alias Microsoft Store nie jest użytym interpreterem. Nie używano
runtime'u kandydatów objętych blokadą. Nie uruchomiono ISCC, AMC ani instalatora.
Przyjęta poprawa diagnostyki nie oznacza rozwiązania kodu `2`, wyjaśnienia
Defendera ani zgody na ponowną kompilację.

### Materiał do dokumentacji użytkownika

Ta zmiana nie dodaje polecenia, skrótu ani elementu interfejsu. Przy przyszłym,
dozwolonym przygotowywaniu instalatora nieudana kompilacja pozostawi dokładny
zapis uruchomienia, a komunikat poda jego miejsce. Nie trzeba zmieniać ustawień
AMC ani wyłączać ochrony. Nie ma nowego pakietu, instalacji ani wydania.

## Bieżąca blokada wydania — 17.11.2026, po instalacjach alpha.511

Oba bundle z zamrożonej rewizji `17e01e44b137b9dd3002444efcb8d17443ba956c`
(`sourceDirty=false`) istnieją. Bezokienne instalacje do osobnych prywatnych
celów Hermesa zakończyły setup, pełną integralność i kontrolowany start kodem
`0` dla obu profili. Prowadzący niezależnie odczytał dokładny zbiór plików obu
instalacji oraz pięć krytycznych hashy każdego profilu.

- Public: 2662 pliki payloadu, bundle ID `e15e7587`, instalator
  `AMC-Public-2026-11-17-0532.exe`, 133481669 B, SHA-256
  `031834372748c196f5abc79b2552da0fedeac62f7bda394c3713fa0768c5140c`.
- Test: 3647 plików payloadu, bundle ID `2214575e`, kandydat instalatora
  `AMC-Test-2026-11-17-0535.exe`, 214371611 B, SHA-256
  `6133f8bda266bff45f99e08e333a8f1d63e28e5321932a9cf8f5c5de46983b77`.
- Root dowodów i prywatnych celów `installed/Public`, `installed/Test`:
  `C:\Users\Michal\AppData\Local\AMC-Hermes-Build\hubert-final-511-pipefix`.
- NVDA zachował PID `4960`; Test zaktualizował dodatek AMC na dysku
  `0.3.3` → `0.4.2`. Zachowano kopię odzyskiwania. Bez restartu ani reloadu;
  nie jest to dowód załadowania nowego dodatku lub odbioru żywego czytnika.

**HOLD BEZPIECZEŃSTWA.** Defender trzykrotnie zablokował tymczasowe
`installers/Test/RCX*.tmp` podczas kompilacji jako `Worm:Win32/Mofksys!pz`,
ThreatID `2147890643`. Źródłowy odczyt wykazuje `ActionSuccess=true`,
`DidThreatExecute=false`, `IsActive=false`; nie dowodzi to czystości maszyny
ani fałszywego alarmu. Skan końcowych EXE przez `Start-MpScan` nie dodał
wykrycia i pozostawił identyczne hashe. Ochrona jest włączona, bez wyjątków.
Dowód: `logs/parent-defender-scan.json` pod powyższym rootem.

Standardowy wrapper Test zwrócił `ISCC exit 2`. Wykonawca uzyskał jeden EXE
przez bezpośrednią kompilację diagnostyczną, skopiował go do finalnego katalogu
i ręcznie wygenerował sidecar. Zgodność hashy i udana instalacja nie zastępują
wyjaśnienia alarmu ani dowodu kanonicznego toru budowy. Kandydat Test **nie ma
odbioru do publikacji**. Nie obchodzić blokady zmianą katalogu, przywracaniem
kwarantanny ani osłabianiem ochrony.

Odczytowy przegląd `deleg_51725a3c` zakończony: zdarzenia Defendera 1116/1117
potwierdzają proces `ISCC.exe` i skuteczną kwarantannę trzech `RCX*.tmp`.
Raport: `logs/security-review.md`. Brak pełnego argv udanej kompilacji
przekłada się na niezamkniętą bramkę pochodzenia instalatora Test.

Prowadzący dodatkowo niezależnie zweryfikował ECDSA-P256/SHA-256 czterech
podpisów `.issig`: `Setup.e32`, `SetupLdr.e32`, `ISCmplr.dll`, `ISPP.dll`.
Klucz publiczny `def02` pobrany z serwera producenta i wersjonowanego tagu
`is-6_7_3` był zgodny; potwierdzono też jego identyfikator, podpisaną nazwę,
rozmiar i SHA plików. Cztery kontrolne modyfikacje podpisywanej wiadomości
zostały odrzucone. Bez uruchamiania kompilatora lub kodu producenta i bez
zmiany badanych plików. Dowód: `logs/parent-vendor-signatures.json`.
To domyka lukę w weryfikacji bieżących składników kompilatora opisaną
w raporcie pomocnika, ale **nie** dowodzi fałszywego alarmu dla `RCX*.tmp`.

Blokada pozostaje. **17.11.2026 użytkownik wyraził zgodę na przekazanie
Microsoftowi podejrzanych plików budowy do analizy, bez profili AMC, ustawień
i danych logowania.** Nie rozszerza to zgody na wyłączenie ochrony, wyjątki,
przywrócenie plików do produkcyjnego katalogu ani uruchamianie próbek.
Zgłoszenia jeszcze nie wysłano. **Aktualizacja po zgodzie użytkownika:
standardowe `Start-Process -Verb RunAs` zadziałało**, proces potwierdził
`elevated=true` na Hermesie. Brak administratora nie jest już blokadą.
`MpCmdRun -Restore -ListAll` zwraca teraz `No quarantined items.`; magazyn
Quarantine ma zero plików. Próby eksportu dokładnie trzech RCX do osobnego
katalogu przez `-Restore -FilePath ... -Path ...` nie zwróciły żadnej próbki;
oryginałów w katalogu budowy również nie ma. Nie ustalono przyczyny ich braku.
Zdarzenia kwarantanny 1117 pozostają w historii, ale nie dowodzą dostępności
próbek obecnie. W MPLog odczytano SHA-256 **jednego** RCXCA4F.tmp:
`05a161266787453c1ba5d4a3c5ce8b41b005fbb38e03a4228205e875106bb501`.
**Aktualizacja po jednoznacznej zgodzie użytkownika na OAuth:** zatwierdzono
na `account.live.com/Consent/Update` aplikację „Windows Defender Security
Intelligence” (profil podstawowy, e-mail, zachowanie dostępu). Portal rozpoznaje
konto; logowanie i dodatkowa zgoda nie są już blokadami. Nie zbierano haseł
ani kodów. Przejściowa odmowa 403 pod adresem zaplecza Azure nie utrzymała się
przy ponownym wejściu przez oficjalny frontend po zwykłym wyborze persony
Software developer. Nie obchodzono kontroli dostępu.

Odczytano kartę **jednego** RCX pod dokładnym SHA-256 powyżej: rozmiar
4427264 B, SHA-1 `5cebeb5381123ac17e8627f3fca0c5187cfcc553`, MD5
`ac211c951be5398a57c5c359f1c44e2d`; nazwa `NULL`, typ `N/A`.
Sekcja certyfikatu pokazuje `Invalid Certificate`; nie jest to werdykt malware
ani dowód fałszywego alarmu. Rozmiar jest równy podpisanemu `Setup.e32`, ale
SHA-256 jest inny — nie są to identyczne bajty. Sam rekord nie dowodzi,
że Microsoft nadal przechowuje bajty próbki.

Dla zweryfikowanego hasha **jednokrotnie wywołano `Rescan File`**. Po odświeżeniu
odczytano ponownie tę samą kartę, bez werdyktu lub potwierdzenia przyjęcia
operacji. Historia po operacji pokazuje `Showing 0 of 0 entries`, bez numeru
zgłoszenia. Nie uznawać kliknięcia za potwierdzone zlecenie analizy; pusta
historia również nie dowodzi odrzucenia samego ponownego skanu. Nie dublować
operacji automatycznie. Zwykły formularz programisty wymaga pliku i Company
Name (limit wyświetlany: 500 MB); nie wysłano go bez brakujących oryginałów,
nie zastąpiono ich raportem, instalatorem ani odtworzonym plikiem.
Dowód: `logs/microsoft-portal-status-20261117.json`, odczyt końcowy
17.11.2026 12:28:13 UTC. **Nie ma potwierdzonej analizy ani submission ID;
bramka bezpieczeństwa i niekanoniczny Test pozostają otwarte.**
Nie wyłączano ochrony, nie dodawano wyjątków, nie wykonywano próbek ani nowych
kompilacji. Dowody: `logs/admin-quarantine-access.json`,
`logs/admin-quarantine-details.json`, `logs/admin-targeted-rcx-export.json`,
`logs/admin-quarantine-resolution.md`. Wcześniejsza odmowa `0x80070005`
dotyczyła wyłącznie niepodniesionego procesu i jest historią.

Porównanie dostępnych danych z najnowszymi wydaniami GitHub zakończono:
Test `test-2026.11.15.2036`, Public `public-2026.11.15.2040`, oba ze źródła
`2b6b061db22523ed9cfb66d26e2808b3d7bf00a7`. Pobrano oryginalne instalatory;
prowadzący niezależnie przeliczył ich SHA i odczytał PE, potwierdzając zgodność
z digestami GitHub i sidecarami. Wszystkie cztery stare/nowe EXE mają wspólny
marker formatu Inno `6.7.0`, PE32/i386 i 11 sekcji — nie dowodzi to identycznej
wersji kompilatora ani payloadu. Nowe instalatory są mniejsze: Public o
3068989 B, Test o 4160320 B. W źródłach zmieniono m.in. obsługę dodatku NVDA
i uruchamianie kompilatora pod PS 5.1, ale brak dowodu związku z detekcją.
**Porównanie nie obejmuje pełnego payloadu poprzedniego wydania:** innoextract
1.9 i 7zip 26.00 nie odczytały użytego formatu. Nie wyodrębniono starego
manifestu; nie traktować tego jako zgodnego lub pustego zestawu plików.
Nie da się też ustalić dokładnego etapu powstania wykrytych RCX z zachowanych
logów. Raporty `logs/github-baseline-comparison.json` i `.md`; w JSON prowadzący
skorygował liczniki kandydackich `fileHashes`/`fileSizes` na rzeczywiste
2662/2662 i 3647/3647. Wykonawca `deleg_ac95fb71` zakończony.
Klasyfikacja Defendera nadal nierozstrzygnięta, publikacja wstrzymana.

Po wyjaśnieniu bezpieczeństwa i toru wydania nadal pozostają celowane odbiory
#14, #17 i #18 przez Windows/NVDA oraz publikacja. Nie publikowano,
nie zamykano Issues i nie dotykano głównego PC.
Poniższe opisy dawnych blokad PS 5.1 i starszych paczek są historią,
nie najnowszym stanem artefaktów.

## Polecenie i korekta użytkownika

16.11.2026 Michał polecił w swojej notatce „Hubert zgłoszenia 2026-11-16.md” wdrożyć #17 i #18, sprawdzić wcześniejsze #9–#11 i #14–#16, poprawić nadal występujące problemy, a pozostałe zamknąć po potwierdzeniu. Dopuszcza pytanie do zgłaszającego o aktualny stan. Osobnym wymaganiem są powiadomienia GitHub i Sygnalisty na bota AMC oraz publikacja aktualizacji Public i Test.

**Nowsza decyzja zastępująca wcześniejsze zgody instalacyjne:** użytkownik sam pobierze i zainstaluje aktualizacje na głównym komputerze. Nie zamykać tam AMC, nie instalować ani nie uruchamiać nowej wersji automatycznie. Instalacje testowe są dozwolone na komputerze Hermes. Informować o postępach. Test ma różnić się zakresem funkcjonalnym wyłącznie obecnością Apple Music; separacja danych, nazw i kanałów pozostaje zamierzona.

Użytkownik dodatkowo polecił rozbić zakres na osobne zadania. Nie zmieniać dostawcy na płatne API; bieżące wykonanie korzysta z openai-codex.

**Kontynuacja po zmianie sesji — późniejsza wyraźna dyspozycja Michała:** „Jak nowa sesja, to kontynuuj po prostu, nie muszę pisać”. Przy wznowieniu wykonania odczytać ten aktualny plan i nowsze korekty, sprawdzić stan Git i wykonawców, następnie kontynuować pierwszy niedokończony uzgodniony krok bez proszenia o dodatkową wiadomość „kontynuuj AMC”. Nowa sesja nie unieważnia zlecenia. Nie powtarzać odebranych etapów ani nie rozszerzać zakresu na inne zadania. Zapis tej zasady nie jest wdrożeniem automatu tworzącego sesję lub wybudzającego agenta; takiego mechanizmu nie deklarować bez rzeczywistego wdrożenia i próby.

**Doprecyzowanie 17.11.2026:** Michał potwierdził stałą zgodę na automatyczną kontynuację dużych zleconych prac. Dla tego zadania punktem końcowym są sprawdzone instalatory AMC Public i AMC Test opublikowane na GitHubie, wraz ze wszystkimi etapami rozpisanymi w tym pliku. Nie zatrzymywać się na odbiorze testu lub pojedynczej poprawki, nie czekać na kolejne „kontynuuj”. Zgłaszać rzeczywistą blokadę zamiast pomijać testy albo deklarować niezmierzone wyniki. Ograniczenia głównego komputera i płatnego API pozostają bez zmian.

## Zasada odbioru — dokładnie, ale proporcjonalnie

Późniejsza korekta Michała: mocne i dokładne testy, z pełną troską o dostępność i klawiaturę, ale bez wielokrotnych rozległych audytów. Przed próbą określić sprawdzany kontrakt, konieczne sąsiednie regresje i warunek zakończenia. Jeden spójny odbiór niezmienionego kandydata; ponowienie tylko części dotkniętej zmianą lub rzeczywistym błędem/niestabilnością. Wykorzystać nadal ważne dowody, zamiast mechanicznie odtwarzać cały zestaw wykonawcy w przeglądzie prowadzącego.

Błąd zapisu raportu, eksportu lub pojedynczego logu nie uzasadnia ponownej walidacji całej aplikacji. Naprawić zapis lub dozbierać brakujący scenariusz. Żywy NVDA ma obejmować zmienione kontrolki, fokus, komunikaty i klawiaturę; nie pełny audyt wszystkich ekranów przy każdej poprawce. Kolejne szerokie przebiegi wymagają konkretnego uzasadnienia. Nie uruchamiać setek powtórzeń domyślnie.

Wspólne zachowania Public/Test badać raz tam, gdzie rzeczywiście są identyczne, a różnice profili i instalację/start sprawdzić dla obu gotowych artefaktów. Nie pomijać integralności paczek, tożsamości wersji, bezpieczeństwa nagrywania ani odczytu publikacji GitHub. Po spełnieniu kryteriów przejść dalej; rzeczywistą blokadę opisać, nie rozbudowywać bez końca aparatury. Korektę skierowano do trzech aktywnych wykonawców `deleg_f9478710`.

**Doprecyzowanie priorytetu klawiatury:** zachować dopracowaną według Michała, lekką obsługę — bez przebudowy „na zapas”. Krótki kontrakt regresji obejmuje wejście do menu, wyjście Escape i powrót fokusu do właściwej kontrolki/wiersza oraz spójne działanie strzałki w lewo w typach sesji AMC, w których służy nawigacji. W polu edycji pozostawić zwykły ruch kursora. Pokryć odrębne ścieżki obsługi sesji, nie każdą kombinację treści na listach. Dla zmienianych skrótów/dodatku sprawdzić właściwy kontekst i celowane przypadki negatywne: edycja, menu/dialog, a gdy zmienia się zasięg działania — własne neutralne okno kontrolne. Współpracę z rzeczywiście załadowanym dodatkiem NVDA odróżniać od testu bez dodatku. Nie przejmować standardowych klawiszy Windows/NVDA ani klawiszy poza właściwym kontekstem; nie uruchamiać destrukcyjnych skrótów systemowych jako sond. Potencjalne konflikty nie są zgłoszeniem potwierdzonego nowego błędu. Włączyć te kontrole do jednego proporcjonalnego odbioru, bez kolejnej pełnej kampanii audytowej; nie deklarować zaliczenia nieuruchomionych sesji/gestów.

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

### Public zbudowany; bezokienny pomocnik Test poprawiony dla PS 5.1

`deleg_e5860624` odebrał cachefix i z czystego zwykłego checkoutu `s511` wybudował Public z `1b4c397`. Prowadzący sprawdził fizyczny instalator: `AMC-Public-2026-11-17-0502.exe`, 133 479 035 B, SHA-256 `e48cab05eb0918ec8a25bbc931d2dc0af8997cab3bb61a0c1f3cc9eafb53bf76`. Odczytano surowy `alpha511-public-audit.json`: 2662 zadeklarowane pliki i 2662 fizyczne pliki poza manifestem, zgodne hashe/rozmiary, zero cache/Apple/Playwright, rzeczywisty natywny Git i potomny Python wskazują ten sam czysty commit. Kontrolowany bezokienny start zaliczony. Nie wykonano instalacji ani publikacji. Po poprawce poniżej ten instalator zachowuje wartość dowodową, ale nie będzie finalną parą ze starszego commita.

Test zatrzymał się na nieobsługiwanym `ProcessStartInfo.ArgumentList` w `Test-AppleMusicWebPipe.ps1`; parser tego skryptu był poprawny, ale wcześniejsza próba parsowania nie dowodziła działania API. Prowadzący utworzył test rzeczywistego potoku na zachowanym, rzeczywiście zbudowanym `amc_apple_music_web_host.exe`: **RED 1 failed** na dokładnie tej właściwości. Minimalna zmiana ustawia pojedynczy stały przełącznik ASCII przez `ProcessStartInfo.Arguments`; nie wymaga dynamicznego cytowania, zachowuje przekierowane stdin/stdout oraz limit czasu. **GREEN 80 passed**, w tym rzeczywiste `ping → pong` i zakończenie procesu bez GUI, konta ani odtwarzania. Test opcjonalnego artefaktu ma standardowy SKIP bez jawnego `AMC_APPLE_MUSIC_WEB_HOST`; nie przedstawiać wtedy go jako wykonanego.

Oddzielny błąd sprzątania Public pojawił się dopiero po udanym przeniesieniu zweryfikowanej paczki: PowerShell 5.1 nie usunął długiej ścieżki wygenerowanego `.editorconfig` w prywatnym `artifacts-launcher`. Nie zmieniono w tym celu produktu, nie usuwano prawidłowych plików paczki ani nie pomijano kontroli. Zachować diagnostykę i oddzielać wynik sprzątania od pełnej integralności i startu pakietu; przy następnym przebiegu potwierdzić to rozróżnienie w surowym logu. Dla zachowania jednej zamrożonej bazy obu finalnych artefaktów zbudować oba profile z następnego wspólnego commita zawierającego poprawkę pomocnika. Bez ponawiania MP3, kolejki, Spotify i całego GUI.

### Budowa ac68396 zatrzymana; pamięć podręczna wyłączona u źródła

`deleg_a2212b80` potwierdził czyste źródła i poprawny parser PS 5.1, ale kanoniczna budowa Public zatrzymała się przed startem i instalatorem. `copy_runtime` próbował skopiować zbędny `pyatv/.../__pycache__/RegisterForGameControllerEventsMessage_pb2.cpython-314.pyc` do 262-znakowej ścieżki Windows (`WinError 3`). Nie powstały finalne bundle/setupy Public ani Test. Zachowano log i niepełny kandydat w `hubert-final-511`; nie są wydaniem. Dodatek AMC 0.4.2 został jedynie zbudowany, nie zainstalowany.

Prowadzący dodał najpierw cztery przypadki regresji: świeży runtime i trzy tory kopiowania zależności. RED: **4 failed** przez obecność cache. Minimalna wspólna reguła ignoruje `__pycache__`, `*.pyc`, `*.pyo` już podczas przechodzenia i kopiowania źródła, a nie po skopiowaniu. Nie zmienia wejściowych zależności, nie skraca ścieżki, nie używa junctionów i nie omija manifestu. Zachowuje zwykłe moduły, natywne rozszerzenia, metadane i zamknięty `python314.zip`. Nie zmienia historycznej gałęzi odświeżenia runtime na miejscu.

GREEN: **79 passed** (nowe przypadki, cały `test_bundle_layout.py`, profile instalatora i parser dwóch wejść). Osobny rzeczywisty Windows Python z tych samych przygotowanych zależności odtworzył przed zmianą `WinError 3` na dokładnie 262 znakach, a po zmianie skopiował ten sam moduł bajt w bajt bez cache, przy niezmienionych wejściach. Dowód: `hubert-final-511/logs/python-cache-native-probe.json`. To odbiór poprawki kopiowania, nie gotowej paczki. Wersja techniczna pozostaje `.511`, bo żaden nowy instalator nie powstał ani nie został opublikowany. Zamrożony commit poprawki: `1b4c397c53b1df25169dea3e99239d8bb4ac881b`. Niezależny przegląd i budowę obu profili zlecono `deleg_e5860624`. Wciąż brak instalacji/NVDA i publikacji.

**Późniejsza kontrola wejść i decyzja o katalogu budowy:** pełne wyliczenie plików bez cache wskazało 2056 plików Public (maksymalna docelowa ścieżka 254 znaki) i 2561 Test (maksymalnie 261), w tym prawidłowy dokument Playwright `gallery-spec.md`. Nie usuwać prawidłowego pliku. Zastąpiono wcześniejszy nadmierny zakaz wyboru krótszego katalogu źródeł: wykonawca ma przygotować zwykły pełny checkout tego samego `1b4c397` pod `C:\Users\Michal\AppData\Local\AMC-Hermes-Build\s511`. To jawny wybór położenia źródeł dla niezmienionych kanonicznych skryptów, bez junctiona, shima, edycji stagingu albo ominięcia kontroli. Wymagane natywne Windows Git HEAD/status rzeczywistego nowego checkoutu i pełna kontrola długości docelowych ścieżek. Artefakty i logi pozostają pod `hubert-final-511`. Ta aktualizacja planu następuje po zamrożeniu źródeł pakietu i nie zmienia kodu kandydata.

### Warunki instalatora odblokowane; zamrożenie następnego kandydata

Odebrano `deleg_fb8f5bf8`, sprawdzono na Hermesie 17 920 bajtów i SHA oryginalnego Quick App Switcher 0.1.6 z kanonicznej specyfikacji. Zintegrowano `b350d24` jako `6cefb31`: bezpieczne uruchomienie ISCC także w PowerShell 5.1, bez prywatnego zmieniania stagingu. Pięć rzeczywistych argumentów fixture (Unicode, spacje, cudzysłów, końcowy backslash, pusty argument) zgadza się z zachowanym dowodem `argvExact=true`.

Przed budową prowadzący znalazł tę samą, potwierdzoną przyczynę w dwóch kolejnych wejściach: Windows PS 5.1 nie parsował `Build-AMCBundle.ps1` i `Test-AMCBundleStartup.ps1` zapisanych UTF-8 bez BOM. Nowe testy rzeczywistego parsera dały RED 2/2; dodanie wyłącznie BOM dało GREEN. Celowany zestaw: **31 passed, 1 skipped**; pominięty fixture EXE wymaga natywnego Windows Python i nie jest zaliczany jako test wykonany w WSL. Samo znalezienie `powershell.exe` w WSL nie zapewnia obsługi POSIX-owego katalogu tymczasowego przez kompilator Windows. To korekta aparatury, nie funkcji AMC.

Natywny Git for Windows 2.54.0 uruchomiono na **HERMES** z prywatnej kopii `cmd` i `mingw64/bin` istniejącego narzędzia (167 plików, odczyt głównego komputera bez zmian). Hash `cmd/git.exe` `81ef35ae005ca9318018d18e3327578ce939fb99feaad6b2d7c8ab15f3de8db5` zgadza się ze źródłem. Nie kopiowano całego profilu/deweloperskich danych ani repozytorium głównego PC; nie używać shimów. Nowy techniczny numer wspólnego kandydata: `0.1.0-alpha.511`. Zbudować go z czystego, zamrożonego checkoutu NTFS, potwierdzić prawdziwe Windows Git HEAD/status, następnie oba setupy i ich osobny odbiór na Hermesie. Nadal bez publikacji i bez instalacji głównego komputera na tym etapie.

### Odebrany wynik kolejnego etapu — 17.11.2026

`deleg_f9478710` zakończony. Prowadzący odczytał rzeczywiste logi obu procesów kolejki oraz sprawdził ich SHA względem raportu: drugi proces przywrócił 3 wpisy `fixture:C,B,A`, flagę play-next, bieżące `fixture:B`, `restoredRows=3`, bez odtwarzania. Nie powtarzano całej baterii. Dokument odebrano lokalnie jako `6a6957d`.

Bezgłośny test MP3 doprowadzono do końca jedną celowaną próbą `--mp3-peaks-only`: kod 0, zaliczone progi surowego/ograniczonego szczytu i seeku w produkcyjnym torze. Wyjaśniono błędne utożsamienie lokalnej ścieżki komponentu FFmpeg na **HERMES** z głównym komputerem. Użyto istniejącej zależności odczytowo, z wersją i SHA przed/po, bez kolejnego pobierania, bez modyfikacji profilu i urządzenia audio. Szczegóły i zakres dowodu w `HUBERT-AUDIO-ODBIOR-20261117.md`; historyczna blokada „brak własnego dekodera” nie jest już aktualna.

Bezpieczne doprecyzowanie komunikatu niedostępnej playlisty z `cf19cf9` sprawdzono względem aktualnej dokumentacji Spotify o trybie deweloperskim i zintegrowano jako `d978877`. Prowadzący sprawdził zgodność zmienionych źródeł stagingu z repo i uruchomił celowany zestaw `--spotify-catalog`: `Wszystkie zestawy przeszly (1).`, kod 0. Początkowe nieudane uruchomienia były błędem odnalezienia runnera (faktyczne AssemblyName `amc_lite_protocol_tests`, konfiguracja Debug), nie testem produktu. Nie zmieniano EOS ani korzystano z konta Spotify; ograniczenia #9–#11 z pełnego raportu pozostają jawne.

Przygotowano prywatne ZIP-y obu profili i instalator Public z **poprzedniej** bazy `9b77369`; po nowej zmianie C# nie są finalnymi artefaktami tego wydania. Instalator Test zatrzymany przed kompilacją przez brak zaufanej paczki Quick App Switcher. Nie przyjęto na wiarę `sourceDirty=false`: osobno zlecono wąskie wyjaśnienie użytych shimów Git i prywatnej kompatybilności PowerShell 5.1 oraz odszukanie oryginalnej paczki dodatku (`deleg_fb8f5bf8`, `hubert-installer-prereqs`). Bez ponownego budowania bundle na tym etapie, instalacji i publikacji. Po rozwiązaniu tej zależności: zamrozić nowy wspólny commit, zbudować odpowiadające mu artefakty i wykonać proporcjonalny rzeczywisty odbiór instalacji/NVDA na Hermesie. Nie instalować na głównym komputerze.

### Wznowienie całego zakresu — 17.11.2026

Po doprecyzowaniu Michała uruchomiono `deleg_f9478710`: trzy równoległe, izolowane kontynuacje z dokładnej bazy `9b773694dba8e61ae527664ae195d194453ab211`:

- `hubert-audio-acceptance`: realny dekoder/limiter MP3 bez emisji dźwięku oraz zachowanie kolejki po zakończeniu i uruchomieniu dwóch osobnych procesów LiteHost, nie tylko test klasy magazynu; wykonawca `sa-0-3ba45d41`.
- `hubert-package-candidate`: rzeczywiste prywatne ZIP-y i instalatory Public/Test, czyste zależności, pełne manifesty i parytet profili; bez instalowania/publikowania przez wykonawcę `sa-1-5a2bc352`. Ewentualna późniejsza zmiana kodu wymaga aktualizacji kandydatów, nie wolno wydać ich jako odpowiadających innemu commitowi.
- `hubert-spotify-followup`: dalsza weryfikacja konfiguracji, komunikatów i trwałej biblioteki #9–#11 bez żywego konta, tokenów i odtwarzania; bez odrzuconej heurystyki EOS; wykonawca `sa-2-ddcabe71`.

Prowadzący zachowuje review, integrację, odbiór instalacji na Hermesie, pomiary NVDA i publikację z odczytem GitHub. Odczyt GitHub potwierdził ostatnie wydania `public-2026.11.15.2040` (stable) i `test-2026.11.15.2036` (prerelease); fetch nie wykazał nowych zmian zdalnej gałęzi. Wyniki dzieci nadejdą asynchronicznie, nie zakładać ich powodzenia.

Odczyt procesów komputera **HERMES** o 00:58:43 wykazał tylko `nvda.exe` PID 4960 w sesji 1 wśród nazw AMC/amc_/pythonw/NVDA; mostek NVDA odpowiedział `status=ok`, wersja 1.0. Nie uruchamiano aplikacji, instalatora ani GUI. To historyczna kontrola przygotowania, nie świeży guard nagrywania na przyszłą instalację i nie dowód dostępności nowej paczki.

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
