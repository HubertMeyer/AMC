# AMC14 — foldery lokalne i integracja z powłoką Windows

Data utworzenia zadania: 18 października 2026 r.

Status: wykonano wstępny audyt istniejącego źródła. Fundament integracji z powłoką jest częściowo przygotowany, ale nie jest spięty w działającą całość i nie został uruchomiony. Nie ustalono jeszcze skrótów. Nie zmieniono kodu, instalatora ani konfiguracji systemu.

## Cel

Zapewnić jeden spójny i dostępny sposób przechodzenia z elementu AMC do jego rzeczywistego miejsca w systemie Windows oraz przygotować bezpieczną integrację instalatora z obsługiwanymi typami plików.

## Wynik wstępnego audytu źródłowego

To zadanie nie zaczyna się od zera. W repozytorium istnieją już:

- użytkowo nazwane grupy rozszerzeń audio, wideo, playlist i niedokończonych nagrań AMC;
- reguły poleceń `Otwórz w AMC` oraz `Dodaj do kolejki AMC`;
- parser argumentów wiersza poleceń i format przekazania żądania między instancjami;
- kod rejestracji per użytkownik w `HKEY_CURRENT_USER`, zgłoszenia w `Otwórz za pomocą` i Ustawieniach aplikacji domyślnych;
- ochrona przed wymuszaniem AMC jako domyślnego programu bez decyzji użytkownika.

Brakujące spięcie jest jednak istotne:

- kod rejestracji nie ma znalezionego wywołania w zwykłym interfejsie ani instalatorze;
- start aplikacji nie odczytuje jeszcze plików z argumentów;
- druga instancja jedynie przywołuje istniejące okno, ale nie przekazuje mu pliku ani polecenia kolejki;
- instalator rejestruje tylko `App Paths`, bez wyboru grup rozszerzeń i bez kontroli ich stanu;
- nie ma testów pełnej drogi: Eksplorator → druga instancja → działające AMC → właściwa lista lub kolejka;
- nazwy mutexu i zdarzenia są obecnie wspólne, więc wymagają rozdzielenia dla `AMC`, `AMC Test` i Portable.

Wniosek: powłoka jest zadaniem średnim, nie dużą implementacją od zera. Najwięcej pracy wymaga bezpieczne przekazanie plików do działającej instancji, integracja profili wydania oraz odbiór instalacji, aktualizacji i deinstalacji.

## Zakres poleceń folderów

- Otwórz folder i zaznacz lokalny plik wybrany w Bibliotece.
- Otwórz folder i zaznacz plik z Historii nagrywania albo listy nagranych plików.
- Otwórz folder i zaznacz pobrany odcinek podcastu lub pobrany materiał YouTube.
- Otwórz folder bieżącego lokalnego materiału z odtwarzacza.
- Otwórz folder źródłowy zaznaczonego folderu Biblioteki.
- Otwórz domyślny folder nagrań Radia oraz domyślny folder pobierania Podcastów z odpowiednich ustawień lub menu.
- Dla elementu internetowego, który nie ma lokalnego pliku, podać krótki komunikat `Ten element nie ma lokalnego pliku` i nie otwierać przypadkowego folderu.

## Zasady działania

- Gdy istnieje konkretny plik, Eksplorator Windows otwiera jego folder i zaznacza ten plik.
- Gdy wskazany jest folder źródłowy albo domyślny, Eksplorator otwiera sam folder.
- Ścieżka jest ustalana z modelu AMC, nie z tekstu dostępnościowego ani tytułu elementu.
- Polecenie nie pobiera pliku z internetu i nie uruchamia odtwarzania.
- Brak pliku, niedostępny dysk, brak uprawnień i element tylko w chmurze otrzymują osobne, użytkowe komunikaty.
- Wywołanie powłoki używa bezpiecznych argumentów i nie skleja polecenia tekstowego ze ścieżką.
- Polecenia są dostępne w menu kontekstowym, pomocy `Ctrl+F1` oraz palecie `Ctrl+Shift+K`, jeśli kontekst jednoznacznie wskazuje plik albo folder.

## Skróty — decyzja odłożona

- `Ctrl+Enter` i `Ctrl+Alt+Enter` są jedynie kandydatami do późniejszego porównania z istniejącą mapą klawiszy.
- Żaden z tych skrótów nie jest obecnie zatwierdzony ani rezerwowany.
- Audyt musi objąć zwykłe listy, odtwarzacz, okno harmonogramów, dodatek NVDA i skróty systemowe.
- Do czasu rozstrzygnięcia funkcja może być projektowana jako polecenie menu bez domyślnego skrótu.

## Integracja instalatora i rozszerzeń

- Ustalić listę faktycznie obsługiwanych rozszerzeń audio, wideo, playlist i plików projektu AMC.
- Instalator może proponować opcjonalne dodanie AMC do `Otwórz za pomocą`, ale nie może bez świadomego wyboru przejmować domyślnych skojarzeń użytkownika.
- Aktualizacja oraz naprawa instalacji muszą zachować dokonany wybór, a deinstalacja usuwać wyłącznie wpisy należące do AMC.
- Uruchomienie pliku z Eksploratora ma przekazać go do istniejącej instancji AMC, nie tworzyć drugiego programu i nie przerywać nagrywania.
- Ścieżki zawierające spacje, polskie znaki, znaki specjalne i nazwy sieciowe wymagają osobnych testów.
- Integracja nie może ujawniać prywatnych ścieżek w komunikatach NVDA, chyba że użytkownik świadomie wybierze informacje szczegółowe.
- Wersja Portable nie rejestruje rozszerzeń ani menu powłoki, ponieważ po przeniesieniu katalogu wpisy prowadziłyby do nieistniejącej ścieżki.
- `AMC`, `AMC Test` i późniejsze pakiety architekturowe muszą mieć rozdzielone klasy, możliwości oraz polecenia, aby deinstalacja jednego profilu nie usuwała wpisów drugiego.

## Zależności

- Część aplikacyjna AMC14 powstaje przed instalatorem AMC12. Najpierw AMC musi poprawnie przyjmować argumenty plików, przekazywać je do działającej instancji, otwierać materiał albo dodawać go do kolejki i bezpiecznie przechowywać wybór grup rozszerzeń.
- AMC12 nie projektuje tych zachowań od nowa. Instalator korzysta z gotowego, przetestowanego kontraktu AMC14 i dopiero wtedy rejestruje opcjonalne rozszerzenia, menu kontekstowe oraz pozycję `Otwórz za pomocą`.
- Końcowy odbiór rejestru, aktualizacji, naprawy i deinstalacji nadal odbywa się razem z instalatorem AMC12, ponieważ dopiero zainstalowany produkt ma stabilną ścieżkę programu.
- AMC02 dostarcza prawidłowe powiązanie nagrania z lokalnym plikiem.
- Moduł Podcastów musi rozróżniać materiał strumieniowany od rzeczywiście pobranego pliku.

## Kolejność wdrożenia

### AMC14A — kontrakt aplikacji, bez instalatora

1. Odczyt plików i przełącznika kolejki z argumentów pierwszej instancji.
2. Bezpieczne przekazanie tego samego żądania do już działającej instancji zamiast samego przywołania okna.
3. Walidacja lokalnej ścieżki i rozpoznanego rozszerzenia przed zmianą Biblioteki albo kolejki.
4. Otwieranie pliku lub dodawanie do kolejki bez przerywania nagrywania i bez zmiany niepowiązanej sesji.
5. Testy nazw ze spacjami, polskimi znakami, przecinkami, średnikami, znakami specjalnymi i ścieżkami sieciowymi.

### AMC14B — interfejs i ustawienia

1. Dostępny wybór grup rozszerzeń oraz polecenia `Otwórz w AMC` i `Dodaj do kolejki AMC`.
2. Informacja, że AMC zgłasza się jako możliwość, ale nie wymusza programu domyślnego.
3. Integracja z menu, pomocą `Ctrl+F1` i paletą `Ctrl+Shift+K`.
4. Osobne tożsamości i kanały przekazania dla `AMC` oraz `AMC Test`.

### AMC14C — instalator i Windows

Ten etap następuje dopiero w AMC12:

1. instalator rejestruje wyłącznie zatwierdzone grupy i stabilną ścieżkę właściwego profilu;
2. aktualizacja zachowuje wybór, naprawa go odtwarza, a deinstalacja usuwa tylko własne wpisy;
3. pełna próba Eksplorator → AMC obejmuje pierwszą i działającą instancję oraz aktywne nagrywanie;
4. Portable pozostaje bez rejestracji powłoki.

## Kryteria późniejszego odbioru

1. Każdy obsługiwany kontekst otwiera właściwy folder, a przy konkretnym pliku zaznacza właściwy plik.
2. Element bez lokalnej ścieżki nie otwiera folderu zastępczego.
3. Skojarzenia rozszerzeń są opcjonalne, odwracalne i nie zmieniają się samoczynnie po aktualizacji.
4. Plik uruchomiony z Eksploratora trafia do jednej istniejącej instancji AMC.
5. Trwające nagrywanie nie jest przerywane przez otwarcie pliku ani aktualizację integracji.
6. NVDA otrzymuje wyłącznie etykiety użytkowe, a fokus po powrocie do AMC zachowuje logiczny kontekst.
7. Argument pliku przekazany drugiej instancji nie ginie: działające AMC otwiera go albo dodaje do kolejki zgodnie z jawnym poleceniem.
8. `AMC`, `AMC Test` i Portable nie przywołują niewłaściwego procesu ani nie współdzielą przypadkowo blokady jednej instancji.

## Stan prac

- Nie przypisano skrótu.
- Potwierdzono istnienie częściowego kodu reguł i rejestracji, ale nie jest on dowodem działającej integracji.
- Nie zmieniono rejestru, instalatora ani skojarzeń plików.
- Nie otwierano Eksploratora Windows.
- Nie kompilowano i nie uruchamiano AMC.
