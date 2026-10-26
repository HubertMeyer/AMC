# AMC06 — harmonogramy: data, czas i dzień tygodnia

Data przygotowania i zatwierdzenia zakresu: 18 października 2026 r.

Status: audyt i specyfikacja poziomu A zatwierdzone do późniejszego wdrożenia produkcyjnego. Zakres rozszerzono o pełny kontrakt klawiaturowego wpisywania daty, godziny rozpoczęcia i długości nagrania. Nie wykonano kompilacji ani uruchomienia AMC.

## Zgłoszone zachowanie

Przy tworzeniu harmonogramu dzień tygodnia ma wynikać z wybranej daty pierwszego nagrania, a nie z dnia, w którym harmonogram jest zapisywany. Data, godzina i dzień muszą pozostać zgodne po zapisaniu, edycji, powieleniu i ponownym otwarciu.

Edytor ma również odzyskać wygodę pól segmentowych znaną ze starego AMC: `lewo/prawo` wybiera część daty albo czasu, `góra/dół` zmienia wybraną część, a wpisywanie cyfr zastępuje bieżącą wartość i po ukończeniu części przechodzi dalej. Długość nagrania ma mieć jednoznaczne, osobne pola godzin i minut, przy czym puste godziny oznaczają zero.

## Wynik audytu źródłowego

1. Model zapisuje następny termin jako UTC w `NextStartUtcTicks` oraz osobno identyfikator strefy w `TimeZoneId`.
2. Edytor przelicza zapisany termin do strefy harmonogramu i pokazuje osobne kontrolki daty oraz godziny. Sekundy są świadomie zerowane.
3. W źródle istnieje już częściowa, jeszcze niezweryfikowana produkcyjnie ochrona zgłoszonego przypadku:
   - nowy plan początkowo zaznacza dzień tygodnia wybranej daty;
   - zmiana daty aktualizuje ten domyślny dzień;
   - pierwsza ręczna zmiana listy dni wyłącza dalsze automatyczne nadpisywanie;
   - edycja istniejącego planu zachowuje jego jawnie wybrane dni.
4. Istnieją testy źródłowe sprawdzające zmianę poniedziałku na wtorek oraz zachowanie ręcznego wyboru dni, lecz nie zostały uruchomione w ramach obecnej serii prac.
5. Kalkulator cyklicznego planu wyprowadza lokalną godzinę następnych wystąpień z ostatniego zapisanego terminu UTC. Przy nieistniejącej godzinie podczas wiosennej zmiany czasu przesuwa wystąpienie do pierwszej prawidłowej chwili. Następny cykl może jednak odziedziczyć tę przesuniętą godzinę i trwale zmienić porę planu.
6. Dla niejednoznacznej godziny podczas jesiennej zmiany czasu kod nie zapisuje jawnej decyzji, czy wybrać pierwsze, czy drugie wystąpienie tej samej godziny.
7. Bieżące źródło C# zawiera już częściowe przygotowanie oczekiwanego edytora:
   - datę jako pole segmentowe `dd.MM.yyyy` z przyciskami góra/dół;
   - godzinę rozpoczęcia jako pole segmentowe `HH:mm`;
   - własną obsługę cyfr z górnego rzędu i klawiatury numerycznej;
   - automatyczne przejście po dwóch cyfrach dnia, dwóch miesiąca, czterech roku, dwóch godziny i dwóch minut;
   - osobne pola długości w godzinach i minutach oraz próbę traktowania pustych godzin jako zera.
8. Samo istnienie tego kodu nie dowodzi zachowania wersji uruchamianej przez użytkownika. Nie sprawdzono jeszcze natywnego zaznaczania segmentu, mowy NVDA, utrzymania pustego pola godzin ani kolejności przejść po cyfrze, strzałkach i Tabie.

Wniosek: podstawowa korekta dnia jest już przygotowana w źródle, ale AMC06 nie może zostać uznane za gotowe bez sprawdzenia pełnego zapisu oraz bez ustabilizowania lokalnej godziny cyklicznego planu na granicach czasu letniego i zimowego.

## Zatwierdzony kontrakt wpisywania daty i czasu

### Data pierwszego nagrania

- Jest jednym polem segmentowym w układzie `dzień.miesiąc.rok`; nie jest zwykłym polem tekstowym wymagającym ręcznego wpisania separatorów.
- `Strzałka w lewo/prawo` wybiera odpowiednio dzień, miesiąc albo rok i podaje nazwę wybranej części oraz jej wartość, na przykład `Miesiąc: październik`.
- `Strzałka w górę/dół` zmienia tylko wybraną część. Zmiana dnia przechodzi prawidłowo przez koniec miesiąca, zmiana miesiąca dopasowuje zbyt duży dzień do końca nowego miesiąca, a zmiana roku uwzględnia 29 lutego.
- Po każdej zmianie wartości NVDA podaje zwięzłą wynikową datę i dzień tygodnia. Nie odczytuje nazwy klasy kontrolki, wewnętrznego formatu ani daty UTC.
- Cyfry zastępują wybrany segment, a nie dopisują się do starej wartości. Dzień i miesiąc przyjmują po dwie cyfry, a rok cztery; zera wiodące są dozwolone.
- Po ukończeniu prawidłowego segmentu fokus wewnętrzny przechodzi dokładnie raz do następnego segmentu. Po ukończeniu roku pozostaje w polu daty; zwykły `Tab` przechodzi do godziny rozpoczęcia.
- Wartość nieprawidłowa, na przykład dzień 32 lub miesiąc 19, nie zmienia zapisanej daty, nie przeskakuje dalej i daje jeden krótki komunikat z prawidłowym zakresem.
- Rozpoczęty, ale nieukończony ciąg cyfr jest czyszczony po zmianie segmentu, użyciu góra/dół, Tabie, Shift+Tabie, Escape albo opuszczeniu pola. Nie może po kilku sekundach połączyć się z cyfrą wpisaną w innej części.

### Godzina rozpoczęcia

- Jest jednym polem segmentowym `godzina:minuty`, a nie swobodnym polem tekstowym.
- `Lewo/prawo` wybiera godzinę albo minuty; `góra/dół` zmienia wybraną część.
- Wpisanie czterech cyfr, na przykład `2310`, ustawia `23:10`: po dwóch prawidłowych cyfrach godziny wybór przechodzi do minut.
- Godzina przyjmuje `00–23`, a minuty `00–59`. Błędna część nie zmienia czasu i nie przesuwa wyboru.
- NVDA mówi `Godzina: 23` albo `Minuty: 10`, a po zakończeniu całego czasu może podać jedno krótkie podsumowanie `23:10`. Nie powtarza przy tym nazwy okna ani całej instrukcji.
- Godzina rozpoczęcia nie może być pusta, ponieważ harmonogram potrzebuje konkretnego terminu. Puste godziny opisane niżej dotyczą wyłącznie długości nagrania.
- Zmiana godziny w polu czasu nie zmienia wybranej daty, także przy przejściu z `23` na `00` albo odwrotnie.

### Wspólna obsługa klawiatury

- Cyfry z górnego rzędu oraz klawiatury numerycznej zachowują się jednakowo.
- Pierwsza cyfra po wejściu do segmentu rozpoczyna nową wartość; nie jest dopisywana do cyfry znajdującej się wcześniej w polu.
- Klawisze lewo/prawo nie przesuwają kursora po separatorach i nie przenoszą fokusa do innej kontrolki.
- Tab i Shift+Tab zawsze przechodzą między całymi kontrolkami. Escape anuluje okno bez zapisu, a Enter zapisuje dopiero po pełnej walidacji.
- Nie stosujemy automatycznego przeskoku opartego wyłącznie na opóźnionym timerze, ponieważ mógłby przenieść segment w trakcie odczytu NVDA. Przejście następuje po kompletnej liczbie cyfr albo świadomym klawiszu użytkownika.

## Zatwierdzony kontrakt długości nagrania

- Długość nagrania ma dwa osobne pola: `Długość nagrania, godziny` oraz `Długość nagrania, minuty`.
- Są to pola góra/dół. Strzałki zmieniają wartość, wpisanie cyfry zastępuje zaznaczoną wartość, a Tab przechodzi z godzin do minut.
- Pole godzin może pozostać wizualnie puste. Puste oznacza wewnętrznie zero godzin, ale nie jest samodzielnie błędem.
- Przy wejściu na puste pole NVDA ma podać `Długość nagrania, godziny, puste — zero godzin`, aby neutralna wartość nie była niejednoznaczna.
- Jeżeli użytkownik pozostawi godziny puste i wpisze `25` w minutach, wynik wynosi dokładnie `25 minut`.
- Po zapisaniu i ponownym otwarciu planu trwającego 25 minut pole godzin ponownie jest puste, a pole minut zawiera `25`; aplikacja nie zamienia pustego pola na mylące `0` tylko na ekranie.
- Minuty są dodatkową częścią długości i mają zakres `0–59`. Wartość 60 lub większa nie może zostać po cichu obcięta do 59; edytor pozostaje w polu i podaje, że należy użyć pola godzin.
- Jeżeli godziny są większe od zera, minuty mogą być puste i oznaczają zero minut. Puste oba pola albo łączne zero daje przy zapisie komunikat `Długość nagrania musi wynosić co najmniej jedną minutę` i fokus na polu minut.
- Godziny i minuty są łączone dopiero w modelu. NVDA oraz użytkownik nie muszą wpisywać liczby minut całkowitych, na przykład `85`, aby uzyskać godzinę i 25 minut.
- Pole `Długość jednej części w minutach` pozostaje osobnym polem minut całkowitych, ponieważ może przekraczać 59. Jego etykieta musi wyraźnie odróżniać je od minut będących częścią całej długości.

## Zatwierdzone zachowanie edytora

- Dla nowego planu domyślnie zaznaczony dzień tygodnia pochodzi z daty pierwszego nagrania wyświetlanej w edytorze.
- Dopóki użytkownik nie zmieni listy dni ręcznie, każda zmiana daty przenosi jedyne domyślne zaznaczenie na dzień tej daty.
- Po pierwszej ręcznej zmianie listy dni data pierwszego nagrania nie nadpisuje wyboru. Pozwala to rozpocząć plan w jednym dniu, ale ustawić późniejsze powtórzenia w innych dniach.
- Edycja istniejącego planu nigdy nie zastępuje zapisanych dni bieżącym dniem komputera ani dniem otwarcia edytora.
- `Jednorazowo` i `Codziennie` nie wymagają ręcznego wyboru dni. `W wybrane dni tygodnia` wymaga co najmniej jednego zaznaczenia.
- Zapisana godzina nie zawiera ukrytych sekund ani milisekund.
- Anuluj nie zmienia harmonogramu. Zapisz utrwala dokładnie dane widoczne w kontrolkach i przywraca fokus na właściwy wiersz menedżera.

## Zatwierdzone usprawnienia menedżera harmonogramów

Korekta użytkownika z 26 października 2026 r. zastępuje wcześniejszą decyzję
poniżej o przypisaniu części czasowej do prawej strzałki. Prawa strzałka ma
podawać zwięzłe parametry pliku wynikowego: bitrate albo rodzaj zapisu, nazwę
pliku oraz `folder domyślny` lub samą ścieżkę niestandardową. Komunikat nie
zaczyna się od słowa `Źródło` ani od nazwy lub adresu stacji. Rozbudowany opis
czasu pozostaje osobnym, niewdrożonym zakresem AMC06.

- Zwykły wiersz zostaje skrócony do nazwy planu, stanu oraz najbliższego terminu. NVDA nie powinien przy każdej strzałce góra/dół powtarzać folderu, formatu, nazwy pliku i wszystkich pozostałych parametrów.
- `Strzałka w prawo` podaje bitrate albo rodzaj zapisu, przykładową nazwę pliku i miejsce zapisu bez powtarzania źródła.
- Szczegółowy opis czasu, długości, podziału na części i wybudzania pozostaje do wdrożenia w osobnym etapie; bieżąca korekta nie przypisuje mu nowego gestu.
- `Shift+Enter` otwiera historię nagrań wybranego planu. Wpis historii musi dostać trwały identyfikator harmonogramu; sama nazwa planu nie wystarcza po zmianie nazwy albo powieleniu.
- `Shift+Spacja` pomija najbliższe wystąpienie bez wyłączania całego planu. Ponowne użycie przed tym terminem przywraca wystąpienie.
- `F2` zmienia wyłącznie nazwę planu w krótkim, dostępnym oknie, bez otwierania całego edytora.
- `Alt+Enter` pokazuje pełne właściwości planu w sekcjach: Termin, Nagrywanie, Miejsce zapisu i Ostatni wynik.
- `Ctrl+C` kopiuje użytkowe podsumowanie wybranego planu, bez identyfikatorów technicznych.
- `Shift+F10` albo klawisz menu otwiera menu kontekstowe zawierające wszystkie działania dostępne dla zaznaczonego planu.
- Menedżer ostrzega o nakładających się harmonogramach oraz możliwej kolizji wynikowych nazw plików.
- Polecenie `Sprawdź plan`, dostępne z menu, weryfikuje stację, miejsce zapisu, format, wymagany koder i najbliższy termin bez rozpoczynania nagrania.
- Każde nowe działanie trafia do pomocy `Ctrl+F1`, menu kontekstowego oraz palety `Ctrl+Shift+K` tam, gdzie paleta ma jednoznaczny dostęp do wybranego planu.

### Świadomie nieprzypisany Ctrl+Enter

`Ctrl+Enter` nie otrzymuje w AMC06 żadnego nowego działania. W szczególności nie rozpoczyna jednorazowego nagrywania według planu. Ewentualne użycie `Ctrl+Enter` albo `Ctrl+Alt+Enter` do otwierania folderu będzie rozstrzygnięte dopiero w osobnym audycie integracji folderów i powłoki, opisanym w AMC14.

## Zatwierdzony model czasu

- Plan cykliczny przechowuje osobno zamierzoną lokalną godzinę ścienną, strefę czasową oraz najbliższe konkretne wystąpienie UTC.
- Przy migracji istniejących planów zamierzona lokalna godzina jest wyliczana z ich obecnego `NextStartUtcTicks` w zapisanej `TimeZoneId`. Migracja nie przesuwa najbliższego zapisanego nagrania.
- Zwykła zmiana czasu letniego lub zimowego nie zmienia zamierzonej lokalnej godziny kolejnych nagrań.
- Jeżeli wybrana godzina nie istnieje podczas wiosennego przestawienia zegara, tylko to jedno wystąpienie rozpoczyna się w pierwszej prawidłowej chwili po luce. Następne wystąpienie wraca do zapisanej godziny.
- Jeżeli wybrana godzina występuje dwukrotnie podczas jesiennego cofnięcia zegara, AMC uruchamia jedno nagranie przy pierwszym chronologicznym wystąpieniu tej godziny. Nie tworzy drugiego nagrania po cofnięciu zegara.
- Zmiana strefy systemu Windows nie zmienia strefy już zapisanego planu. Nowy plan używa strefy systemowej z chwili utworzenia.
- Lista harmonogramów i podgląd nazwy pliku pokazują datę i czas tego samego najbliższego wystąpienia w strefie planu.

## Powielanie i edycja

- Powielenie zachowuje datę, zamierzoną lokalną godzinę, strefę, cykl i niezależną kopię listy dni.
- Kopia pozostaje wyłączona i nie dziedziczy informacji o trwającym, zatrzymanym ani nieudanym wystąpieniu.
- Zmiana kopii nie może modyfikować oryginału.
- Edycja planu po przejściu na kolejne wystąpienie pokazuje rzeczywistą datę tego wystąpienia i pierwotnie zamierzoną godzinę lokalną, a nie godzinę chwilowo przesuniętą przez lukę czasu letniego.

## Dostępność NVDA

- Kontrolki mają użytkowe nazwy: `Data pierwszego nagrania`, `Godzina rozpoczęcia`, `Powtarzanie nagrania` oraz `Dni tygodnia`.
- Po zmianie daty strzałką lub wpisaniu cyfr komunikat zawiera wybraną datę i jej dzień tygodnia.
- Wiersze dni mają jawne etykiety w rodzaju `Wtorek, zaznaczony`; NVDA nie może wypowiadać `DayOfWeek`, nazwy klasy ani reprezentacji obiektu.
- Strzałki tylko wybierają dzień, a Spacja zmienia jego zaznaczenie i podaje jeden krótki wynik.
- Test ręczny obejmuje początkową wartość, wpisywanie cyfr, strzałki, Tab i Shift+Tab, Zapisz, Anuluj, powrót fokusa oraz ponowne otwarcie.
- Odczyt segmentu ma zawsze postać użytkową: `Dzień`, `Miesiąc`, `Rok`, `Godzina` albo `Minuty`. NVDA nie może ograniczać się do samej liczby bez informacji, którą część zmieniamy.
- Długie instrukcje klawiaturowe są dostępne jako opis kontrolki i w pomocy, ale nie są powtarzane po każdej strzałce.
- Pole puste nie może być ogłaszane jako nazwa typu kontrolki ani jako brak wartości bez znaczenia. Dla długości godzin oznacza jawnie `puste — zero godzin`.

## Testy do wykonania przy wdrożeniu

1. Utworzenie planu w dniu innym niż data nagrania zaznacza dzień daty nagrania, nie dzień zapisu.
2. Zmiana daty przez granicę miesiąca i roku oraz wybór 29 lutego podają i zapisują prawidłowy dzień tygodnia.
3. Kolejne zmiany daty aktualizują domyślny dzień do chwili pierwszej ręcznej zmiany listy dni.
4. Po ręcznym zaznaczeniu kilku dni dalsza zmiana daty nie usuwa wyboru.
5. Zapis, zamknięcie i ponowne otwarcie odtwarzają tę samą datę, godzinę, strefę, cykl i dni.
6. Anulowanie nowego planu i anulowanie edycji nie zmieniają zapisanych danych.
7. Powielenie tworzy wyłączoną, niezależną kopię z tą samą datą, godziną, strefą i dniami.
8. Plan codzienny o 02:30 przechodzący przez wiosenną lukę uruchamia wystąpienie graniczne zgodnie z przyjętą regułą, a następnego dnia ponownie ma 02:30.
9. Plan w dwukrotnie występującej godzinie jesiennej uruchamia dokładnie jedno wystąpienie.
10. Zmiana bieżącej strefy Windows nie przesuwa istniejącego planu zapisanego w innej strefie.
11. Termin jednorazowy w przeszłości jest odrzucany; cykliczny w przeszłości wyznacza pierwsze prawidłowe przyszłe wystąpienie.
12. Wszystkie listy wyboru i lista dni przechodzą kontrolę etykiet dostępności bez technicznych nazw.
13. Zwykły wiersz pozostaje krótki, a boczne strzałki podają dwie różne, niepowtarzające się grupy informacji.
14. `Shift+Spacja` pomija i przywraca dokładnie jedno najbliższe wystąpienie bez wyłączenia planu.
15. `Shift+Enter` filtruje historię po trwałym identyfikatorze planu także po zmianie jego nazwy i utworzeniu kopii.
16. `F2`, `Alt+Enter`, `Ctrl+C` i menu kontekstowe zachowują zaznaczenie oraz przywracają fokus na ten sam wiersz.
17. `Ctrl+Enter` pozostaje bez nowego działania w menedżerze harmonogramów.
18. Po zainstalowaniu `AMC` i `AMC Test` oba profile pokazują te same zsynchronizowane definicje planów, lecz dokładnie jeden profil ma prawo wykonać dane wystąpienie.
19. Przeniesienie prawa wykonywania harmonogramów jest atomowe, niemożliwe podczas nagrywania i nie uruchamia ponownie już obsłużonego wystąpienia.
20. Lewo/prawo przechodzi kolejno przez dzień, miesiąc i rok oraz przez godzinę i minuty, a NVDA za każdym razem podaje nazwę właściwego segmentu.
21. Góra/dół zmienia wyłącznie wybrany segment; data poprawnie przechodzi przez koniec miesiąca, rok i 29 lutego, a czas nie zmienia daty przy przejściu `23` ↔ `00`.
22. Wpisanie `15042027` w polu daty daje `15.04.2027`, a `2310` w polu czasu daje `23:10`, z pojedynczym przejściem między segmentami.
23. Nieprawidłowe `32`, `19`, `29` jako godzina i `75` jako minuty czasu nie zmieniają poprzedniej wartości, nie przeskakują dalej i dają jeden komunikat.
24. Cyfry z głównej klawiatury i klawiatury numerycznej dają identyczny wynik, także po ponownym otwarciu okna.
25. Puste godziny długości plus `25` minut zapisują dokładnie 25 minut i po ponownym otwarciu zachowują puste godziny oraz `25` minut.
26. `1` godzina i `25` minut zapisują 85 minut, a `1` godzina i puste minuty zapisują 60 minut.
27. Puste oba pola długości, `0` i `0` oraz wpisanie minut poza zakresem nie są po cichu poprawiane na inną długość.
28. Pierwsza cyfra zastępuje poprzednią zawartość pola liczbowego; nie powstają przypadkowe wartości przez dopisywanie do wartości domyślnej.
29. Szybka seria cyfr, wolne wpisywanie, zmiana segmentu w połowie, Tab, Shift+Tab, Zapisz, Anuluj i ponowne otwarcie nie pozostawiają ukrytego bufora cyfr.
30. NVDA wypowiada jeden użytkowy komunikat na zmianę i nie dubluje jednocześnie natywnej wartości kontrolki oraz tekstu statusu.

## Dokumentacja i bramka

- AMC06 nie dodaje nowego skrótu ani polecenia, dlatego nie wymaga nowej pozycji w `Ctrl+F1` ani `Ctrl+Shift+K`.
- Pomoc i instrukcja użytkownika powinny wyjaśnić automatyczne dopasowanie dnia, moment przejścia na wybór ręczny, zachowanie przy zmianie czasu, segmentową obsługę daty i godziny oraz znaczenie pustych godzin długości.
- Implementacja, testy automatyczne i próba NVDA tworzą samodzielną Bramkę 3. Obsługa obrazu została przeniesiona do długoterminowego AMC15 i nie blokuje harmonogramów.
- Równoległe dane dwóch instalacji i globalne prawo wykonywania harmonogramów należą do AMC12. AMC06 dostarcza trwałe identyfikatory i reguły czasu, których ta koordynacja wymaga.
- Przed kompilacją i uruchomieniem w Bramce 3 trzeba ponownie potwierdzić, że AMC nie nagrywa.

## Stan prac

- Nie zmieniono kodu produkcyjnego ani testów w ramach przygotowania AMC06.
- Nie kompilowano i nie uruchamiano AMC.
- Istniejące fragmenty kodu i testy dotyczące dopasowania dnia, segmentów daty/czasu oraz rozdzielonej długości pozostają materiałem wejściowym do późniejszego wdrożenia i weryfikacji, a nie dowodem przejścia testów.
- Do poprawienia lub potwierdzenia w kodzie pozostają zwłaszcza: trwałe zachowanie pustego pola godzin, brak cichego obcinania minut, czyszczenie nieukończonego bufora cyfr przy każdej zmianie kontekstu oraz brak podwójnej mowy natywnej kontrolki i pola statusu.
