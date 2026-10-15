# AMC Python — przekazanie prac na wtorek

Ten plik jest krótkim punktem startowym po pracach zakończonych 14 października
2026 r. Szczegółowy stan pozostaje w `AMC_PYTHON_STAN_2026-10-10_PL.md`.

## Aktualizacja 15 października 2026, godz. 13:57

Etap drobnych poprawek przed Spotify został ukończony, przetestowany, zbudowany
i zainstalowany w kanonicznej instalacji `D:\Projekty Codex\AMC Python`.

- źródło instalacji: `80fb0792971d815498cbcdf9b7457e0a77de7c18`;
- kompilacja: `2026.10.15-80fb0792971d815498cbcdf9b7457e0a77de7c18-d8dc97e6`;
- tytuł uruchomionego okna: `AMC Python — 15.10.2026, 13:57`;
- manifest i instalacja: 603 pliki, zgodny commit i identyfikator zawartości;
- pełny zestaw głównej gałęzi: 1565 testów zaliczonych, 110 pominiętych
  historycznych, 11 podtestów zaliczonych, zero błędów;
- przed aktualizacją oraz po niej nie było procesu nagrywania ani żadnego
  pliku `.amc-partial`; odtwarzanie mogło zostać przerwane przez bezpieczny
  restart;
- repozytorium jest czyste poza zapleczem `.test-output` i `.test-tmp`.

Ukończone przyrosty:

1. `Shift+F2`: naprawiono rzeczywisty wyścig między zatwierdzeniem dialogu a
   Enterem wracającym do listy. Testy wykonują prawdziwą zmianę nazwy pliku
   tymczasowego, także w historii nagrywania, dla zmiany samej wielkości liter,
   blokady pliku oraz zachowania fokusu. Pozostaje krótki odbiór użytkownika
   z NVDA w zainstalowanej wersji.
2. WiiM i Sonos: wspólna lewa strzałka podaje dostępne parametry własnych
   strumieni i pozycje tylko do odczytu bez ujawniania identyfikatorów;
   `Ctrl+F` przeszukuje bieżące listy, a globalne wyniki zachowują stabilną
   tożsamość i nie zapisują niczego.
3. Skróty globalne: `Ctrl+H`, `Ctrl+L`, `Alt+R` i `Alt+Shift+R` dochodzą z
   list oraz odtwarzacza. Wspólna Historia zachowuje sesję, widok i fokus;
   poprawiono też utratę zapamiętanego folderu przy późniejszym `Ctrl+L`.
4. TIDAL: `Ctrl+F` korzysta z katalogu online, zachowuje typ i tożsamość
   wyniku; Enter na wykonawcy nie wybiera arbitralnego albumu. Prawa strzałka
   w wynikach wyszukiwania otwiera relacje, a wykonawca prowadzi do albumów,
   utworów i podobnych wykonawców. Samo wyszukanie i przeglądanie nie zapisuje
   elementu do kolekcji. Radio Browser także odtwarza wynik przejściowo bez
   automatycznego dopisania stacji.
5. Zależności: dodano `scripts\Prepare-AMCDevelopmentDependencies.ps1`,
   `scripts\Use-AMCDevelopmentEnvironment.ps1` i raport
   `ZALEZNOSCI_AMC_STAN_PL.md`. Trwały cache znajduje się w
   `D:\Projekty Codex\AMC - zależności`; Rust/MSVC, .NET, Node/pnpm,
   wxPython i pytest są sprawdzone także offline. Skrypt ustawia rzeczywistą
   ścieżkę Windowsowego `dotnet`, więc testy nie wracają do historycznej
   ścieżki `/home/michal/dotnet/dotnet`.

Rozpoczęto pierwszy etap Spotify bez logowania i bez operacji na koncie.
Aktualny wx/LiteHost nie ma jeszcze sesji Spotify. W osobnych gałęziach są
przygotowywane: tylko-do-odczytu kontrakt LiteHost, model jednej sesji wx oraz
pakowanie istniejącego przypiętego hosta Librespot. Wzorzec interfejsu stanowi
nowy TIDAL po powyższych poprawkach; stary WPF pozostaje wyłącznie technicznym
źródłem wiedzy o Web API, OAuth i Librespot.

Najbliższy odbiór użytkownika obecnej kompilacji: `Shift+F2`, TIDAL po
wyszukaniu wykonawcy i prawa strzałka, `Ctrl+H`, WiiM/Sonos oraz `Ctrl+F`.
Nowy błąd z tego odbioru ma pierwszeństwo przed dalszą instalacją Spotify.

## Właściwy projekt i instalacja

- Aktywny projekt: `D:\Projekty Codex\AMC - integracja wxPython`.
- Użytkowa instalacja: `D:\Projekty Codex\AMC Python\AMC.exe`.
- Stary interfejs WPF w `D:\Projekty Codex\Accessible Multimedia Controller`
  jest wycofany z bieżących prac. Można go czytać jako materiał historyczny,
  ale nie należy w nim wdrażać poprawek ani go uruchamiać zamiast AMC Python.
- Zmiany pozostają lokalne. Nie wysyłać ich do GitHuba bez nowej, jednoznacznej
  decyzji użytkownika dotyczącej konkretnego stanu.

## Ostatnia odebrana technicznie wersja

- commit źródłowy: `375e5b0886e484832277cccf343f5f0d9a075bc2`;
- kompilacja: `2026.10.14-375e5b0886e484832277cccf343f5f0d9a075bc2-3a5e9a79`;
- tytuł uruchomionego okna: `AMC Python — 14.10.2026, 20:21`;
- pełny przebieg bazowy z wcześniejszej kompilacji: 1546 testów zaliczonych,
  110 pominiętych historycznych oraz 11 zaliczonych podtestów;
- po ostatniej zmianie odczytu strumieni: 49 ukierunkowanych testów WiiM i
  Sonos zaliczonych;
- osobny zestaw testów launchera i aktualizatora: 13 z 13 zaliczonych;
- rozwiązanie C#: 0 ostrzeżeń i 0 błędów;
- zweryfikowany pakiet: 602 pliki;
- uruchomione procesy pochodzą z `D:\Projekty Codex\AMC Python`; stary proces
  WPF nie był uruchomiony;
- katalog źródeł był czysty poza lokalnymi `.test-output` i `.test-tmp`.

Dokładny rachunek ostatniej instalacji zapisuje lokalny plik
`.test-output\LAST_TEST_BUILD.json`. Katalog `.test-output` jest zapleczem
testowym, a nie drugim sposobem uruchamiania programu.

## Nagrywanie zawsze ma pierwszeństwo

Niedzielne nagrania były powodem przesunięcia automatycznego startu na wtorek.
Niezależnie od dnia, dopóki nagrywanie trwa albo nie da się go pewnie
wykluczyć, wolno analizować i zmieniać kod,
tworzyć lokalne commity, wykonywać lekkie testy na plikach tymczasowych oraz
przygotowywać zależności, jeżeli nie dotyka to działającej instalacji i nie
grozi zakłóceniem nagrania.

W tym czasie nie wolno wykonywać pełnej kompilacji lub publikacji, zamykać ani
restartować AMC, podmieniać plików instalacji, uruchamiać instalatora ani
testować na żywej aplikacji lub plikach użytkownika. Przed każdą taką
czynnością trzeba sprawdzić stan nagrywania oraz przez odpowiedni odstęp
obserwować, czy rośnie którykolwiek plik `.amc-partial`. Brak widocznego okna
nie jest wystarczającym potwierdzeniem.

Jeżeli nagrywanie jest aktywne lub stan pozostaje niepewny, należy pozostawić
bezpiecznie przygotowaną poprawkę w repozytorium i poczekać na wyraźnie
wskazane przez użytkownika okno. Pełna kompilacja, instalacja, aktualizacja na
żywo i odbiór z NVDA mogą ruszyć dopiero wtedy. Sam brak bezpiecznego okna do
instalacji nie blokuje pracy nad kodem i testami izolowanymi.

## PILNE: zacząć od niedziałającego Shift+F2

Po uruchomieniu kompilacji z godziny 20:21 użytkownik ponownie potwierdził, że
`Shift+F2` zamyka dialog, ale realna zmiana nazwy pliku nie dochodzi do skutku.
Poprzednie testy i komunikaty sukcesu nie są więc dowodem działania tej
funkcji. To jest pierwszy i blokujący punkt prac we wtorek, przed
przygotowaniem zależności oraz Spotify.

Należy zacząć od kontrolowanego odtworzenia na niepotrzebnym pliku w Plikach
lokalnych i Historii nagrywania. Po zatwierdzeniu trzeba sprawdzić bezpośrednio
na dysku, czy stara ścieżka zniknęła, nowa istnieje, a lista i historia mają
nową ścieżkę i zachowany fokus. Samo zamknięcie dialogu albo szybki powrót do
listy nie oznacza sukcesu.

Sprawdzić kolejno:

1. dojście skrótu `Shift+F2` do właściwej akcji i wybranego wiersza;
2. wartość odebraną z dialogu oraz to, czy Enter nie uruchamia równolegle
   odtwarzacza;
3. wywołanie hosta i właściwej operacji systemu plików, blokady pliku oraz
   rzeczywisty wynik na dysku;
4. aktualizację ścieżki w Bibliotece i Historii nagrywania dopiero po
   potwierdzonym powodzeniu;
5. zmianę tylko wielkości liter, ponowną zmianę nazwy i uczciwy komunikat
   błędu, gdy plik jest naprawdę zajęty;
6. hipotezę o brakującej zależności Pythona, ale bez jej zakładania. `Ctrl+X`
   działa, więc trzeba znaleźć rzeczywistą różnicę w przepływie operacji;
7. implementację starego AMC WPF wolno przeczytać jako porównanie, lecz
   poprawkę wdrażać wyłącznie w nowym AMC Python.

Test odbiorczy musi zmieniać nazwę prawdziwego pliku tymczasowego i sprawdzać
obie ścieżki na dysku. Nie instalować następnej wersji i nie przechodzić do
dalszych etapów, dopóki ten test oraz próba z NVDA nie potwierdzą działania.

## Drobny wspólny punkt WiiM i Sonosa: lewa strzałka

Po naprawieniu `Shift+F2`, a przed Spotify, należy ujednolicić odczyt
parametrów stacji i strumienia. `Lewa strzałka` w listach WiiM i Sonosa ma
działać tak jak w Radiu internetowym: podać raz dostępne, użytkowe parametry
bieżącej pozycji, w tym adres lub ścieżkę źródła, jeżeli API je zwraca.

Polecenie ma działać również dla ulubionych i innych pozycji tylko do odczytu,
których nie można zmienić ani usunąć. Uprawnienie do modyfikacji nie może
decydować o dostępności informacji. Gdy dostawca nie udostępnia adresu lub
innego parametru, nie wolno go zgadywać ani odczytywać w zamian identyfikatora
technicznego. Wspólne testy kontraktowe powinny objąć WiiM, Sonosa oraz
przyszłe adaptery, pojedynczy komunikat NVDA i niezmieniony fokus.

## Drobny punkt przekrojowy: Ctrl+H i skróty globalne

`Ctrl+H` obecnie nie otwiera Historii odtwarzania z widoków WiiM i Sonosa.
Trzeba sprawdzić także podcasty oraz inne główne widoki. Skrót ma być obsłużony
na wspólnym poziomie aplikacji, a nie kopiowany osobno do każdego adaptera:
powinien otworzyć jedną Historię odtwarzania niezależnie od bieżącej sesji, a
po jej zamknięciu przywrócić fokus do wcześniejszego elementu.

Przy tej poprawce należy przejrzeć routing pozostałych skrótów globalnych,
zwłaszcza `Alt+R`, `Alt+Shift+R` i `Ctrl+L`, aby nowy widok nie przejmował ich
bez działania. Dodać parametryzowany test wejścia z Radia internetowego,
podcastów, WiiM i Sonosa. Ten mały punkt można przygotować równolegle w osobnym
worktree po ustaleniu przyczyny blokującego problemu `Shift+F2`; nie może sam
instalować wydania ani dotykać działającej aplikacji.

## Drobny punkt przekrojowy: wyszukiwanie TIDAL, podcastów i radia

Użytkownik wyszukał w TIDAL-u wykonawcę, nacisnął Enter i zamiast świadomie
wybranego wyniku trafił na album, który był już zapisany w kolekcji. Trzeba
odtworzyć ten przypadek z wykonawcą mającym album zapisany i niezapisany oraz
sprawdzić mapowanie zaznaczonego wiersza, typu wyniku i akcji Enter. Enter na
wykonawcy ma otworzyć wykonawcę, a nie arbitralny album z biblioteki.

`Prawa strzałka` na wykonawcy powinna otworzyć jedno menu relacji zawierające
co najmniej albumy i utwory, jeżeli TIDAL je zwraca. Użytkownik ma móc
przejrzeć nowości i dopiero osobnym poleceniem dodać wybrany element do
biblioteki. Sprawdzić analogiczny routing typów i relacji w podcastach oraz
innych wyszukiwarkach.

W Radio Browserze oraz Radiu internetowym wyniki wyszukiwania nie mogą
automatycznie trafiać do biblioteki lub zapisanych stacji. W całym AMC samo
wyszukanie, Enter, prawa strzałka i przeglądanie muszą być bez zapisu. Test ma
porównać bibliotekę przed i po scenariuszu, sprawdzić zapisany i niezapisany
element, fokus, pojedynczą akcję Enter oraz właściwe menu prawej strzałki.

## Kolejny etap: Ctrl+F w usługach i lokalnych listach

`Ctrl+F` powinien działać spójnie także w WiiM i Sonosie. Nawet gdy oficjalne
API nie udostępnia pełnego katalogu do przeszukania, program może lokalnie
odnajdywać lub filtrować już wczytane strumienie, playlisty i inne nazwane
elementy. Gdy API oferuje wyszukiwanie globalne, należy je udostępnić w tym
samym wzorcu interfejsu, z jasno wypowiedzianym zakresem.

Najpierw zinwentaryzować obecne znaczenie `Ctrl+F` i rozdział wyszukiwania
lokalnego od globalnego w Radiu internetowym, podcastach i TIDAL-u. Następnie
dodać wspólny kontrakt dla WiiM, Sonosa oraz przyszłych adapterów: zachowanie
fokusu, Enter na właściwym wyniku, Escape do punktu wyjścia i brak zapisu do
biblioteki. Innowacje AMC, takie jak szybkie presety i lokalne filtrowanie, są
pożądane, jeżeli nie udają funkcji niedostępnej w API dostawcy.

## Późniejszy etap po Spotify: jednolite logowanie

Po zintegrowaniu Spotify trzeba zaprojektować pierwsze uruchomienie usług tak,
aby odbiorca nowego instalatora nie musiał ręcznie generować ani wpisywać
technicznych kodów aplikacji, identyfikatorów klienta lub sekretów, o ile
oficjalny model dostawcy pozwala użyć rejestracji AMC i publicznego przepływu
autoryzacji. Osobno sprawdzić aktualne wymagania Sonosa, WiiM, Spotify, TIDAL-u
i pozostałych usług; nie zakładać, że wszystkie używają tego samego protokołu.

Docelowo różne mechanizmy, takie jak OAuth z PKCE, kod urządzenia, dostęp
lokalny czy automatyczne wykrywanie urządzenia, mają dawać spójne doświadczenie
z NVDA: zrozumiałe rozpoczęcie, anulowanie, ponowienie i wylogowanie. Nie wolno
umieszczać sekretów, tokenów ani danych kont w instalatorze, repozytorium lub
logach. Jeżeli któraś usługa rzeczywiście wymaga własnej rejestracji
deweloperskiej użytkownika, trzeba przygotować dostępny kreator i uczciwie to
wyjaśnić zamiast obiecywać niemożliwe logowanie bez konfiguracji.

Odbiór tego etapu wykonać na czystym profilu lub maszynie, bez wcześniejszych
tokenów i narzędzi deweloperskich. Ten projekt jest późniejszy i nie blokuje
wtorkowych napraw, zależności ani podstawowej integracji Spotify.

## Co naprawiono 14 października

1. Edycja plików audio: wycinanie i dopisywanie korzystają z właściwego
   kontekstu pliku; poprawiono zakończenie operacji, postęp i obsługę końca
   materiału. Dodano testy dokładnego wycięcia końcówki WAV.
2. Odtwarzacz: uporządkowano osobne kontrolki głośności i tempa, ich etykiety
   dostępności oraz kierunek klawiszy strzałek, Home i End.
3. WiiM: przywrócono listę Biblioteki po wejściu do odtwarzacza i usunięto
   zbędnie czytane słowo „źródło” z kategorii.
4. `Alt+D`: opis podcastu zaczyna się od właściwej treści, bez odczytywania
   technicznego lub powtarzanego nagłówka dialogu.
5. Historia nagrywania: operacje na rzeczywistym pliku aktualizują ścieżkę lub
   usuwają ukończony wpis, jeżeli pliku już nie ma. Wpisy nieudane pozostają
   jako diagnostyka.
6. `Ctrl+Shift+C`: kopiuje adres własnego strumienia WiiM albo Sonos. Ulubione
   Sonos nie udają adresu strumienia, gdy API udostępnia tylko identyfikator.
7. `Shift+F2`: podjęta poprawka wyścigu nie rozwiązała problemu w próbie
   użytkownika. Punkt pozostaje otwarty i ma pierwszeństwo przed dalszymi
   pracami; obowiązuje sekcja „PILNE” powyżej.

Najważniejsze commity, od najnowszego:

- `375e5b08` — uproszczony odczyt nazw strumieni WiiM i Sonos;
- `c47d5e25` — aktualizator rozpoznaje uproszczony tytuł okna i potrafi
  bezpiecznie zamknąć bieżącą wersję przed podmianą;
- `4168946c` — trwały wybór urządzenia WiiM oraz dopuszczenie kopiowania
  adresu w sesjach WiiM i Sonos;
- `c525e8c0` — naprawa zmiany nazwy pliku po `Shift+F2`;
- `c843f6a5` — kopiowanie adresów strumieni WiiM i Sonos;
- `442bc858` — operacje na plikach historii nagrań;
- `4fdaae76` — Biblioteka WiiM i kierunki głośności;
- `d7506703` — edycja plików i dostępność odtwarzacza.

## Krótki odbiór na żywo przed Spotify

Testy automatyczne przeszły, ale we wtorek warto zacząć od krótkiego odbioru
z NVDA na niepotrzebnych plikach:

1. `Shift+F2` w Plikach lokalnych i Historii nagrywania: po Enter nazwa ma się
   rzeczywiście zmienić, lista ma zachować fokus, a odtwarzacz nie może się
   sam otworzyć.
2. `Shift+Delete`: plik ma trafić do Kosza, a ukończony wpis historii ma
   zniknąć po odświeżeniu. Nieudane nagrania mogą pozostać jako diagnostyka.
3. Wycięcie końca materiału: dla pliku 12-minutowego usunięcie zakresu
   9:00–12:00 ma pozostawić dokładnie około 9 minut, bez dopisanej końcówki.
4. Dopisanie fragmentu do pliku: operacja ma się zakończyć, a okno postępu ma
   zniknąć; nie może pozostać bez końca.
5. Pierwsze wczytanie własnych strumieni WiiM i Sonos: sprawdzić kolejność
   przed użyciem `Alt+3` i po ponownym otwarciu.
6. Sprawdzić z kilku widoków globalne `Alt+R` i `Alt+Shift+R`.
7. W zapisanych strumieniach i pozycjach tylko do odczytu WiiM oraz Sonosa
   nacisnąć lewą strzałkę: ma podać raz dostępne parametry jak Radio
   internetowe, bez identyfikatorów technicznych i bez zmiany fokusu.
8. Z Radia internetowego, podcastów, WiiM i Sonosa nacisnąć `Ctrl+H`: Historia
   odtwarzania ma otworzyć się raz, a po jej zamknięciu fokus ma wrócić do
   wcześniejszego elementu.
9. Wyszukać wykonawcę w TIDAL-u, wejść Enterem i użyć prawej strzałki: ma
   pozostać właściwy typ wyniku, a relacje mają prowadzić do albumów i utworów.
   Następnie wykonać podobną próbę w podcastach i Radio Browserze oraz
   potwierdzić, że biblioteka nie zmieniła się bez jawnego polecenia dodania.
10. Użyć `Ctrl+F` na listach Radia internetowego, podcastów, TIDAL-u, WiiM i
    Sonosa. Lokalny zakres ma odnajdywać wczytane elementy, a globalny korzystać
    z katalogu tylko tam, gdzie API go udostępnia; zakres musi być jednoznaczny.

Przed zamknięciem lub aktualizacją AMC nadal trzeba potwierdzić, że nie rośnie
żaden plik `.amc-partial` i że nie trwa nagrywanie.

## Następny główny blok: Spotify

Po rzeczywistym naprawieniu i odebraniu `Shift+F2`, przed równoległymi pracami
wykonać `ZADANIE_WTOREK_PRZYGOTOWANIE_ZALEZNOSCI_PL.md`. Audyt z 14 października
potwierdził .NET, Python, Node, pnpm i WebView2, ale wykazał brak lokalnego
toolchainu Rust i narzędzi MSVC potrzebnych do przebudowania hosta Librespot.
Zadanie przygotuje trwały wspólny cache na dysku D i próbę pracy bez sieci.

Po przygotowaniu zależności i powyższym krótkim odbiorze wracamy do Spotify
w nowym AMC Python. Nie przenosimy funkcji do starego WPF. Pierwszy etap
powinien być inwentaryzacją
bez zapisu: przeczytać ten plik, `AMC_PYTHON_STAN_2026-10-10_PL.md` oraz
`SPOTIFY-LOSSLESS-I-MONITORING.md`, sprawdzić istniejące adaptery i testy, a
następnie ustalić zakres sesji Spotify oraz kryteria odbioru z NVDA.

Zakres należy rozdzielić co najmniej na: logowanie i stan konta, katalog i
bibliotekę, wyszukiwanie, przekazanie odtwarzania do właściwego silnika lub
oficjalnego klienta, sortowanie i nawigację kontekstową oraz dostępne etykiety
wszystkich list i pól kombi. Nie wykonywać logowania ani zmian na koncie bez
bieżącej, świadomej czynności użytkownika.

### Wzorzec interfejsu Spotify

Logikę widoków i obsługi klawiatury Spotify należy budować na rozwiązaniach,
które działają już w sesji TIDAL nowego AMC Python: wspólnym modelu list,
Biblioteki, wyszukiwania, sortowania, relacji, kolejki, presetów i odtwarzacza.
Stare AMC WPF oraz jego Librespot są wyłącznie materiałem technicznym dla API,
autoryzacji, silnika audio i istniejących ograniczeń. Nie przenosić z niego
zachowania interfejsu.

Minimalny kontrakt odbioru Spotify:

- Enter wykonuje jedno działanie po jednym naciśnięciu; nie wymaga drugiego
  Entera i nie przepuszcza klawisza do nowo otwartego widoku;
- lewa strzałka podaje raz zwięzłą, prawidłową informację o bieżącym elemencie
  lub odtwarzaniu, bez dwóch komunikatów i danych technicznych;
- prawa strzałka otwiera właściwe menu relacji lub czynności kontekstowych
  zgodne z nowym TIDAL-em i nie odczytuje równolegle starego opisu;
- fokus po Enter, Escape, zapisaniu i anulowaniu wraca do zamierzonego wiersza;
- każda lista i pole kombi ma jawny tekst użytkowy dla NVDA; identyfikatory,
  rekordy i wartości modelu nie mogą być wypowiadane;
- odtwarzacz Spotify ma używać wspólnych, już uporządkowanych kontrolek tempa,
  głośności i transportu AMC Python.

Użytkownik będzie jeszcze obserwował bieżącą wersję w czwartek, piątek i
sobotę pod kątem samoczynnie pojawiających się okien. Nowe zgłoszenie w tej
sprawie ma pierwszeństwo przed instalacją kolejnego wydania, ale nie blokuje
przygotowania zależności i analizy Spotify.

## Etap przed udostępnieniem programu testerom

Po ukończeniu głównych funkcji, przed pierwszym wydaniem dla innych testerów,
wykonać osobny plan `PLAN_WYDANIA_GITHUB_AMC_PYTHON_PL.md`. Obejmuje on jeden
spójny proces wydań GitHub, aktualizator i moduł zgłaszania błędów, zamknięty
zestaw zależności użytkowych, dokumentację, skróty klawiszowe oraz odbiór na
czystej maszynie. To jest późniejszy etap; obecna zgoda użytkownika nie
obejmuje jeszcze publikacji repozytorium ani wydania na GitHubie.

## Jak bezpiecznie prowadzić kilka zadań równolegle

Równoległość jest bezpieczna, jeżeli każde zadanie zmieniające kod ma osobny
worktree i własną gałąź. Jedno zadanie integracyjne jest właścicielem głównego
katalogu, instalacji `D:\Projekty Codex\AMC Python` i końcowego wydania.

- Równolegle wykonywać analizę, testy i niezależne moduły.
- Zmiany w tych samych plikach, szczególnie głównym oknie, skrótach i protokole
  hosta, wykonywać kolejno albo po wcześniejszym podziale odpowiedzialności.
- Zadania robocze mają kończyć się lokalnym commitem, podaniem hasha i wyników
  testów. Nie powinny same instalować, uruchamiać aktualizatora ani publikować.
- Zadanie integracyjne przegląda i scala commity po kolei, rozwiązuje konflikty,
  uruchamia pełny zestaw testów, sprawdza nagrywanie i tylko raz buduje oraz
  instaluje nową wersję.
- Praktycznie najlepiej prowadzić jednocześnie dwa lub trzy niezależne zadania,
  nie kilka implementacji dotykających wspólnego interfejsu.

Przykładowe polecenie dla zadania roboczego:

> Pracuj wyłącznie w nowym AMC Python, w osobnym worktree i osobnej gałęzi.
> Nie modyfikuj starego WPF, nie instaluj programu i nie publikuj. Zakończ
> lokalnym commitem oraz raportem: zmienione pliki, testy, ryzyka i hash.

Przykładowy podział pierwszego dnia Spotify:

1. najpierw jedno zadanie przygotowania zależności, nie równolegle z kodem;
2. zadanie tylko do odczytu: inwentaryzacja obecnego kodu i braków Spotify;
3. osobne zadanie: kontrakt dostępności i scenariusze testów NVDA;
4. implementacja dopiero po uzgodnieniu wyników punktów 2–3;
5. na końcu jedno zadanie integracyjne i jedna instalacja.
