# AMC03 — audyt skrótów rozdziałów, zakładek i historii

Data audytu: 18 października 2026 r.

Rodzaj etapu: obserwacja i projekt zachowania. Tabela została zatwierdzona 18 października 2026 r. z korektą dotyczącą nazwanych zakładek; wykonanie tej korekty rozpoczęto w AMC04 bez kompilacji i bez uruchamiania aplikacji.

## Zakres i źródła

Porównano tylko funkcje objęte AMC03:

- zakładki użytkownika;
- rozdziały dostawcy, osadzone i tworzone przez użytkownika;
- historię widoków;
- historię odtwarzania;
- kolizje między klawiaturą okna, dodatkiem NVDA i warstwą Python.

Źródła:

1. Kanoniczny projekt pełnego AMC/WPF: `D:\Projekty Codex\Accessible Multimedia Controller`, gałąź `main`, odczytany stan bazowy `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc` wraz z bieżącymi zmianami roboczymi.
2. Zainstalowana równoległa implementacja: `D:\Projekty Codex\AMC Python`, pakiet utworzony 16 października 2026 r., etykieta `2026.10.16-02fd6da80044715cc756c97c2243181196f9e158-4871c17d`.
3. Dodatek NVDA z kanonicznego projektu, wersja `0.3.3`.

AMC Python był w tym etapie wyłącznie źródłem porównania. Nie uruchamiano go, nie testowano na żywo i nie zmieniano jego plików.

## Rozstrzygnięcia pojęć

- **Zakładka** to punkt czasu utworzony przez użytkownika. Szybka zakładka nie ma nazwy, nazwana zakładka ma opis. Zakładka nie dzieli materiału na zakresy, a nadanie jej nazwy nie zmienia jej w rozdział.
- **Rozdział** to początek nazwanego zakresu pochodzącego od dostawcy, innej aplikacji albo z metadanych pliku. Ewentualne przyszłe rozpoznawanie rozdziałów przez AMC, na przykład na podstawie ciszy, jest osobną funkcją i nie należy do obecnego etapu.
- **Historia widoków** to stos otwieranych list i poziomów bieżącej sesji.
- **Historia odtwarzania** to lista wcześniej uruchomionych materiałów bieżącej sesji.
- **Kolejka** to bieżąca kolejność odtwarzania. Nie jest historią.

Najważniejsze rozstrzygnięcie: `Ctrl+Shift+B` tworzy **nazwaną zakładkę**, nie rozdział. Skróty nawigacji po nazwanych zakładkach i po rzeczywistych rozdziałach są rozłączne.

## Tabela docelowa skrótów okna AMC

| Skrót i kontekst | Pełny AMC/WPF — stan odczytany | AMC Python — stan odczytany | Działanie docelowe | Sesje i warunki | Komunikat NVDA |
|---|---|---|---|---|---|
| `B`, odtwarzacz | Dodaje szybką zakładkę. W Radiu podczas nagrywania dodaje punkt do zapisywanego pliku. | Tak samo, ale zwykłe zakładki są ograniczone do plików lokalnych; Radio ma osobną drogę nagrania. | Dodaj szybką zakładkę w bieżącym miejscu. | Materiał o znanym czasie w odtwarzaczu AMC; w Radiu wyłącznie trwające nagranie. | `Dodano zakładkę: czas` albo krótki powód niedostępności. |
| `Ctrl+Shift+B`, odtwarzacz | Dodaje nazwaną zakładkę. Na liście dochodzi do tej samej komendy, która odpowiada, że wymagany jest odtwarzacz. | W odtwarzaczu dodaje nazwaną zakładkę, ale na liście otwiera zakładki zaznaczonego pliku. | Jedno znaczenie: dodaj nazwaną zakładkę; funkcja działa tylko w odtwarzaczu. Usunąć inne znaczenie tego gestu z listy Python. | Jak dla `B`. | `Dodano zakładkę nazwa: czas`; po Anuluj bez dodatkowej mowy. |
| `Ctrl+B`, lista lub odtwarzacz | Otwiera wspólny widok Zakładek; bieżący materiał jest porządkowany na początku. | Otwiera wszystkie zakładki, ale w sesji Podcasty jest obecnie blokowany jako funkcja Biblioteki plików. | Otwórz Zakładki wszystkich obsługiwanych sesji, z bieżącym materiałem na początku i możliwością filtrowania. | Wszystkie sesje posiadające trwałe zakładki; samo otwarcie listy nie wymaga odtwarzacza. | Nagłówek `Zakładki`, potem zwykły wiersz i pozycja. |
| `Shift+Page Up`, odtwarzacz | Poprzednia zakładka bieżącego materiału. | Jest przypisany, lecz wykonanie działa tylko dla plików lokalnych. | Poprzednia zakładka użytkownika. | Wewnętrznie odtwarzany, przewijalny materiał ze stabilnym identyfikatorem. | `nazwa, czas` albo `Brak poprzedniej zakładki w tym materiale`. |
| `Shift+Page Down`, odtwarzacz | Następna zakładka bieżącego materiału. | Jest przypisany, lecz wykonanie działa tylko dla plików lokalnych. | Następna zakładka użytkownika. | Jak wyżej. | `nazwa, czas` albo `Brak następnej zakładki w tym materiale`. |
| `Ctrl+Shift+Page Up`, odtwarzacz | Brak osobnego filtrowania. | Brak osobnego filtrowania. | Poprzednia **nazwana zakładka** utworzona przez `Ctrl+Shift+B`; pomija szybkie zakładki bez nazwy. | Jak dla pozostałych zakładek. W pierwszym wdrożeniu bez WiiM. | `nazwa, czas` albo `Brak poprzedniej nazwanej zakładki w tym materiale`. |
| `Ctrl+Shift+Page Down`, odtwarzacz | Brak osobnego filtrowania. | Brak osobnego filtrowania. | Następna **nazwana zakładka** utworzona przez `Ctrl+Shift+B`; pomija szybkie zakładki bez nazwy. | Jak wyżej. | `nazwa, czas` albo `Brak następnej nazwanej zakładki w tym materiale`. |
| `Ctrl+Alt+B`, lista lub odtwarzacz | Otwiera rozdziały wybranego albo bieżącego materiału. | Brak funkcji; most dodatku NVDA jawnie odpowiada, że nie jest zaimplementowana. | Otwórz jedną listę rozdziałów dostawcy, osadzonych i użytkownika. | Materiał typu utwór lub odcinek o znanym czasie; na liście może być wybrany bez uruchamiania. | `Rozdziały`, potem nazwa rozdziału, zakres i pozycja. |
| `Ctrl+Alt+Shift+B`, odtwarzacz | Dodaje nazwany rozdział użytkownika. | Brak akcji. | Dodaj nazwany rozdział w bieżącym miejscu. | Wewnętrznie odtwarzany materiał o znanym czasie, poza samym końcem. | `Dodano rozdział nazwa: czas`. |
| `Ctrl+Shift+strzałka w lewo`, odtwarzacz | Poprzedni rozdział. Po więcej niż 3 sekundach od początku najpierw wraca do początku bieżącego rozdziału. | Brak akcji. | Główny skrót poprzedniego rozdziału. | Materiał z rozdziałami i obsługiwanym skokiem do czasu. | `nazwa rozdziału, czas` albo `Brak poprzedniego rozdziału`. |
| `Ctrl+Shift+strzałka w prawo`, odtwarzacz | Następny rozdział. | Brak akcji. | Główny skrót następnego rozdziału. | Jak wyżej. | `nazwa rozdziału, czas` albo `Brak następnego rozdziału`. |
| `Ctrl+Alt+Page Up/Down`, odtwarzacz | Drugi skrót do poprzedniego lub następnego rozdziału. | Brak akcji. | Zachować jako zgodnościowy alias rozdziałów i jawnie opisać jako skrót alternatywny. `Ctrl+Shift+Page Up/Down` ma odrębne znaczenie: nazwane zakładki. | Jak dla rozdziałów. | Ten sam komunikat co dla głównego skrótu rozdziału. |
| `Alt+strzałka w lewo/prawo`, lista | Poprzedni lub następny widok bieżącej sesji. W odtwarzaczu `Alt+lewo` wraca do listy, a `Alt+prawo` niczego nie zmienia. | Brak mapowania historii widoków. | Historia widoków na listach. W odtwarzaczu zachować powrót `Alt+lewo`; podstawowymi drogami wyjścia pozostają `Escape` i `F6`. | Wszystkie sesje mające listy. | Po zmianie od razu nagłówek i zaznaczony wiersz; na granicy `Brak poprzedniego/następnego widoku w sesji …`. |
| `Ctrl+H`, lista lub odtwarzacz | Otwiera Historię odtwarzania bieżącej sesji. WiiM zapisuje migawki historii, lecz filtr poleceń blokuje mu otwarcie widoku. | Ma osobne widoki dla Plików, Radia, Podcastów, Spotify, WiiM i Sonos; TIDAL wpada obecnie do historii plików lokalnych. | Otwórz historię dokładnie aktywnej sesji. Wpis tylko informacyjny może pozostać na liście bez możliwości ponownego uruchomienia. | Wszystkie sesje, które rejestrują historię; brak wpisów daje pusty widok, nie przełącza do innej sesji. | `Historia odtwarzania`, potem tytuł i pozycja. Dla wpisu tylko informacyjnego: `Tego wpisu nie można ponownie uruchomić z AMC`. |
| `Alt+strzałka w dół`, odtwarzacz | Uruchamia starszy, możliwy do powtórzenia element Historii odtwarzania. | Brak mapowania; `Alt+Down` na listach służy do zmiany kolejności. | Starszy odtwarzany element historii. | Odtwarzacz; sesja z historią i przynajmniej jednym wpisem możliwym do powtórzenia. | Sam tytuł albo `Brak starszego elementu w historii`. |
| `Alt+strzałka w górę`, odtwarzacz | Uruchamia nowszy, możliwy do powtórzenia element Historii odtwarzania. | Brak mapowania; `Alt+Up` na listach służy do zmiany kolejności. | Nowszy odtwarzany element historii. | Jak wyżej. | Sam tytuł albo `Brak nowszego elementu w historii`. |
| `Alt+strzałka w górę/dół`, lista z ręczną kolejnością | Przenosi zaznaczony element lub blok o jedną pozycję. | Działa na obsługiwanych listach i playlistach. | Zachować. Kontekst listy nie może uruchamiać historii odtwarzania. | Tylko kolejność własna, kolejka lub playlista obsługująca ręczne przestawianie. | `Przeniesiono w górę/dół…` albo komunikat granicy. |
| `Page Up/Down`, odtwarzacz | Poprzedni lub następny element kolejki/kontekstu odtwarzania. | Tak samo. | Zachować jako nawigację po elementach, nie po zakładkach i nie po rozdziałach. | Sesje obsługujące zmianę elementu. | Tytuł nowego elementu zgodnie z ustawieniami komunikatów. |
| `Alt+Page Up/Down`, odtwarzacz | Poprzednia lub następna granica zaznaczonego fragmentu; WiiM używa tej pary kontekstowo do swoich źródeł/presetów. | Granice fragmentu, a w WiiM źródła. | Zachować znaczenie kontekstowe. Nie przypisywać tej pary do zakładek ani rozdziałów. | Pliki/Podcasty z fragmentem; WiiM według jego własnej warstwy. | Nazwa granicy i czas albo właściwa nazwa źródła WiiM. |

## Macierz możliwości sesji

| Sesja | Zakładki użytkownika | Rozdziały | `Ctrl+H` | `Alt+góra/dół` w odtwarzaczu |
|---|---|---|---|---|
| Pliki lokalne, także wideo | Tak, gdy czas jest znany | Rozdziały osadzone i użytkownika | Tak | Tak |
| Podcasty RSS | Tak, także dla strumienia, gdy AMC zna czas i pozycję | Dostawca Podcasting 2.0, osadzone, strona odcinka i użytkownika | Tak | Tak |
| YouTube w sesji Podcasty | Tak, gdy materiał jest odtwarzany i przewijalny w AMC | Rozdziały odczytane z dostępnych danych oraz użytkownika | Tak | Tak |
| Spotify odtwarzane wewnątrz AMC | Tak, gdy jest stabilny identyfikator, czas i skok | Rozdziały użytkownika; rozdziały dostawcy dopiero po udokumentowanym źródle | Tak | Tak dla wpisów możliwych do ponownego uruchomienia |
| Radio na żywo | Nie dla samej transmisji; tak dla zapisywanego pliku podczas nagrywania | Nie | Tak, historia stacji | Tak, przejście między stacjami z historii |
| TIDAL sterowany w oryginalnej aplikacji | Nie, dopóki AMC nie ma wiarygodnej pozycji i własnego odtwarzacza | Nie | Tak, jeśli AMC zarejestrował wpisy; wpis może być tylko informacyjny | Tylko dla wpisów, które AMC potrafi ponownie uruchomić |
| WiiM | Nie w pierwszym wdrożeniu AMC04 | Nie w pierwszym wdrożeniu AMC04 | Tak; obecna blokada widoku jest błędem, bo migawki są już zapisywane | Tylko dla zapisanych strumieni lub presetów możliwych do ponownego uruchomienia |
| Sonos | Nie w pierwszym wdrożeniu AMC04 | Nie w pierwszym wdrożeniu AMC04 | Tak po podłączeniu zapisu migawek historii | Tylko dla wpisów możliwych do ponownego uruchomienia |

Reguła wspólna: sama obecność tytułu i czasu trwania nie wystarcza. Zakładki i rozdziały są dostępne dopiero wtedy, gdy AMC ma stabilny identyfikator materiału, aktualną pozycję oraz potrafi wykonać skok do podanego czasu.

## Konflikty i luki znalezione w audycie

1. **Dwa znaczenia `Ctrl+Shift+B` w AMC Python.** Na liście otwiera zakładki zaznaczonego pliku, a w odtwarzaczu tworzy nazwaną zakładkę. Docelowo gest ma jedno znaczenie; filtrowanie konkretnego materiału powinno być funkcją listy otwartej przez `Ctrl+B`.
2. **Brak rozdziałów w AMC Python.** Nie ma akcji okna, a most NVDA zalicza `previousChapter`, `nextChapter` i `showChapters` do znanych, lecz niezaimplementowanych poleceń.
3. **Zakładki Python tylko dla plików lokalnych.** Skróty są widoczne w odtwarzaczu, lecz wykonanie odmawia w Podcastach, YouTube i Spotify niezależnie od rzeczywistych możliwości materiału.
4. **Brak historii widoków oraz szybkiej historii odtwarzania w Python.** `Alt+lewo/prawo` nie są przypisane. `Alt+góra/dół` istnieją tylko do przestawiania listy.
5. **Niespójny `Ctrl+H` w obu implementacjach.** Pełny AMC zapisuje historię WiiM, ale blokuje polecenie otwarcia. AMC Python ma historię wielu usług, lecz TIDAL kieruje obecnie do Plików lokalnych.
6. **Pomoc pełnego AMC nie jest kompletna.** `Ctrl+F1` potrafi opisać bezpośrednie `Alt+góra/dół` w odtwarzaczu, ale ogólna pomoc odtwarzacza pomija rozdziały i historię. Paleta zawiera zakładki i rozdziały, lecz nie ma osobnych poleceń „starszy/nowszy element historii odtwarzania”.
7. **Alias rozdziałów jest ukryty.** `Ctrl+Alt+Page Up/Down` działa w WPF, ale paleta pokazuje tylko `Ctrl+Shift+lewo/prawo`. Alias trzeba jawnie opisać albo usunąć; rekomendacja to zachować go dla pamięci mięśniowej i oznaczyć jako alternatywny.
8. **Różne możliwości urządzeń są kodowane wyjątkami.** WiiM ma jawny filtr poleceń, Sonos i pozostałe sesje przechodzą innymi drogami. To sprzyja sytuacjom, w których menu ukrywa funkcję, ale skrót nadal do niej dochodzi.
9. **Dodatek NVDA i AMC Python nie mają parytetu.** Dodatek wystawia globalne polecenia rozdziałów, pełny AMC je wykonuje, a Python jawnie odmawia. Użytkownik słyszy więc inną odpowiedź zależnie od uruchomionego interfejsu.

## Polecenia globalnego dodatku NVDA

Globalne gesty dodatku pozostają osobną warstwą i nie powinny kopiować skrótów okna jeden do jednego:

- `Ctrl+Windows+B` — szybka zakładka;
- `Ctrl+Windows+Shift+Page Up/Down` — poprzednia/następna zakładka;
- `Ctrl+Windows+Alt+Shift+Page Up/Down` — poprzedni/następny rozdział;
- `Ctrl+Windows+Alt+B` — lista Zakładek;
- `Ctrl+Windows+Alt+C` — lista Rozdziałów;
- `Ctrl+Windows+H` — Historia odtwarzania aktywnej sesji.

Gesty z `Windows` nie kolidują ze skrótami okna. W AMC04 trzeba zachować te same nazwy poleceń i te same komunikaty o możliwościach sesji po obu stronach mostu.

## Wymagania dla AMC04

1. Wprowadzić jeden model możliwości dla zakładek, rozdziałów, historii odtwarzania i ponownego uruchamiania wpisu. Menu, skrót, paleta, `Ctrl+F1` i most NVDA muszą pytać ten sam model.
2. Dodać pierwszoklasowe polecenia „starszy element historii” i „nowszy element historii”, aby `Alt+góra/dół` nie były ukrytą logiką klawisza i mogły trafić do palety.
3. Utrzymać rozdział zakładek od rozdziałów także w danych i etykietach dostępności. Osobno filtrować nazwane zakładki dla `Ctrl+Shift+Page Up/Down`. W zwykłym wierszu nie wolno wypowiadać identyfikatora, typu obiektu ani technicznej nazwy pochodzenia.
4. Uzupełnić `Ctrl+F1`, paletę `Ctrl+Shift+K`, menu i instrukcję w tym samym etapie co implementacja skrótów.
5. Dodać testy resolverów klawiszy dla listy i odtwarzacza, testy macierzy sesji oraz testy odpowiedzi mostu NVDA. Testy muszą obejmować brak materiału, nieznany czas, pierwszy/ostatni punkt, wpis tylko informacyjny i zmianę sesji.
6. W próbie ręcznej NVDA sprawdzić początkowy fokus, powtarzanie skrótu, powrót po Anuluj, ponowne otwarcie listy oraz brak podwójnej mowy UIA i komunikatu aplikacji.

## Poza zakresem AMC03

- Nie zmieniano żadnego skrótu ani kodu wykonawczego.
- Nie rozstrzygano nowego skrótu do filtrowania Zakładek wyłącznie dla jednego materiału; najpierw wystarczy wybór i filtr we wspólnym widoku `Ctrl+B`.
- Nie dodawano zakładek do TIDAL, WiiM ani Sonos bez wiarygodnego kontraktu pozycji i przewijania.
- Nie uruchamiano kompilacji, AMC, AMC Python ani NVDA.

## Wynik etapu

Tabela została zatwierdzona z korektą: `Ctrl+Shift+Page Up/Down` nawiguje wyłącznie po nazwanych zakładkach z `Ctrl+Shift+B`, a `Ctrl+Shift+lewo/prawo` pozostaje nawigacją po rzeczywistych rozdziałach. AMC04 może wdrażać ten model bez ponownego zgadywania znaczenia skrótów.
