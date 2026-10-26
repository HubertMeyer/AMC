# AMC08 — tworzenie playlist Spotify i dodawanie do playlist

Data przygotowania zakresu: 18 października 2026 r.

Status: audyt źródłowy i specyfikacja poziomu A przygotowane. Użytkownik zatwierdził wdrożenie natywnych playlist Spotify we własnym profilu `AMC Test`; ukrycie Spotify w wydaniu publicznym nie anuluje ani nie ogranicza AMC08. Nie wykonano jeszcze operacji na prawdziwym koncie Spotify, nie zmieniono kodu produkcyjnego ani testów, nie kompilowano i nie uruchamiano AMC.

## Cel

`AMC Test` ma umożliwić utworzenie natywnej playlisty na koncie Spotify oraz dodanie do jednej lub wielu edytowalnych playlist Spotify zaznaczonych utworów albo odcinków. Zadanie nie obiecuje uruchamiania całej playlisty Spotify jako kontekstu odtwarzania.

Playlisty konta Spotify pozostają czymś innym niż lokalne playlisty AMC. Interfejs, skróty i komunikaty muszą zawsze mówić wprost, którego rodzaju playlisty dotyczą.

## Wynik audytu źródłowego

1. `SpotifyScopes.Requested` świadomie nie zawiera obecnie `playlist-modify-private` ani `playlist-modify-public`. Komentarze i testy wprost mówią, że zakresy mają zostać dodane dopiero razem z funkcją zmiany playlist.
2. `SpotifyIntegrationService` potrafi odczytywać bibliotekę, wyszukiwać i zmieniać przynależność do kolekcji konta, ale nie ma metod tworzenia playlist Spotify ani dodawania do nich pozycji.
3. Obecne polecenie tworzenia playlisty w sesji Spotify tworzy lokalną playlistę AMC przez `PlaylistIndex`. Nie wysyła niczego do Spotify.
4. `Ctrl+P` i `Ctrl+Shift+P` są wspólnymi skrótami playlist, ale ich cel jest rozstrzygany przez bieżącą sesję. W Mediach lokalnych prowadzą do playlist AMC, w TIDAL-u do playlist TIDAL, a w Spotify powinny prowadzić do natywnych playlist Spotify. Obecny routing sesji Spotify do lokalnych playlist AMC jest więc stanem przejściowym do skorygowania, a nie kontraktem do zachowania.
5. Synchronizacja Spotify pobiera playlisty konta przez `/me/playlists`, ale zwykły widok `Playlisty` w sesji Spotify nadal jest widokiem playlist AMC. Natywne playlisty Spotify są elementami zdalnej kolekcji i wymagają osobnego, jawnie nazwanego wejścia.
6. Model playlisty Spotify przechowuje nazwę i tekstową nazwę właściciela, lecz nie zachowuje identyfikatora właściciela, flagi współpracy, prywatności ani `snapshot_id`. Tekstowa nazwa właściciela nie wystarcza do rozstrzygnięcia prawa do edycji.
7. Odczyt zawartości używa obecnie przestarzałego `/playlists/{id}/tracks`. Dla aktualnego trybu deweloperskiego trzeba przejść na `/playlists/{id}/items` i parser pola `item`, zachowując kontrolowany fallback dla starszego kształtu `track` tam, gdzie Spotify nadal go zwraca.
8. `Ctrl+Shift+P` ma już utrwalone znaczenie użytkowe: `Dodaj do playlisty`. Okno tego polecenia może zarówno wybrać istniejącą playlistę bieżącej usługi, jak i utworzyć nową. Nie ma potrzeby wprowadzania osobnego `Alt+Shift+P` dla Spotify.
9. `Ctrl+N` pozostaje kontekstowym poleceniem „Nowy” dla innych sesji i nie jest wymagany do podstawowej obsługi playlist Spotify. Utworzenie playlisty Spotify bez wcześniejszego zaznaczenia może pozostać jawnym poleceniem menu i palety, bez nowego globalnego skrótu.

## Potwierdzony kontrakt Spotify Web API

- Utworzenie playlisty bieżącego użytkownika używa `POST /me/playlists`.
- Dodanie pozycji używa `POST /playlists/{playlist_id}/items`.
- Jedno żądanie dodania przyjmuje najwyżej 100 URI i zachowuje ich kolejność.
- Do playlist można dodawać URI utworów i odcinków.
- Odpowiedź dodania zawiera `snapshot_id`, który potwierdza nową wersję playlisty.
- Prywatne playlisty wymagają `playlist-modify-private`, a publiczne `playlist-modify-public`. Pełna obsługa obu rodzajów wymaga obu zakresów.
- Odczyt elementów przez `/playlists/{playlist_id}/items` jest obecnie ograniczony do playlist, których bieżący użytkownik jest właścicielem albo współtwórcą; obce playlisty mogą zwrócić 403.
- Aplikacja w trybie deweloperskim ma ograniczenia kont i zapytań. Nie wolno na tej podstawie obiecać publicznej funkcji Spotify dla wszystkich użytkowników AMC.

Źródła oficjalne:

- https://developer.spotify.com/documentation/web-api/reference/create-playlist
- https://developer.spotify.com/documentation/web-api/reference/add-items-to-playlist
- https://developer.spotify.com/documentation/web-api/reference/get-playlists-items
- https://developer.spotify.com/documentation/web-api/concepts/scopes
- https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide
- https://developer.spotify.com/documentation/web-api/concepts/quota-modes

## Zatwierdzona spójność playlist między sesjami

### Jedna intencja skrótów, cel zależny od sesji

- `Ctrl+P` otwiera playlisty właściwe dla bieżącej sesji: AMC w Mediach lokalnych, TIDAL w TIDAL-u i natywne playlisty konta Spotify w Spotify.
- `Ctrl+Shift+P` wszędzie zachowuje użytkowe znaczenie `Dodaj do playlisty`. W sesji Spotify dodaje do prawdziwej playlisty Spotify, a nie do lokalnej playlisty AMC.
- Okno `Ctrl+Shift+P` pozwala wybrać jedną lub kilka istniejących playlist bieżącej usługi oraz utworzyć nową playlistę, gdy użytkownik tego potrzebuje. Utworzenie nowej playlisty jest dostępne również wtedy, gdy lista jest pusta.
- Lokalne playlisty AMC pozostają lokalne i nie są automatycznie publikowane w Spotify. Jeżeli później potrzebne będzie dodawanie materiału Spotify do playlisty AMC, otrzyma jawne polecenie drugorzędne, a nie przejmie `Ctrl+Shift+P`.

### Playlisty Spotify — działanie w sesji Spotify

- `Ctrl+Shift+P`: `Dodaj do playlisty Spotify…` dla zaznaczonych zgodnych pozycji w sesji Spotify, również z odtwarzacza i wyników wyszukiwania.
- `Ctrl+P`: `Playlisty Spotify` — pokazuje natywne playlisty konta, które można potem udostępnić przez Spotify.
- W oknie dodawania znajduje się jawna opcja `Utwórz nową playlistę Spotify…`. Po utworzeniu nowa playlista zostaje wybrana jako cel i otrzymuje bieżące zaznaczenie.
- Osobne polecenie menu i palety `Utwórz pustą playlistę Spotify…` pozostaje dostępne bez obowiązkowego skrótu, gdy użytkownik nie chce od razu dodawać elementów.
- Wszystkie nazwy zawierają słowo `Spotify`; żadna etykieta nie może brzmieć jedynie `Playlista` albo `Zapisz`, gdy rezultat trafia do konta zewnętrznego.

## Tworzenie playlisty Spotify

- Opcja `Utwórz nową playlistę Spotify…` w oknie `Ctrl+Shift+P` oraz osobne polecenie palety otwierają dostępne okno z polami `Nazwa playlisty Spotify` oraz `Widoczność playlisty`.
- Dostępne widoczności: `Prywatna — widoczna tylko zgodnie z ustawieniami konta` oraz `Publiczna — publikowana w profilu Spotify`. Model przechowuje wartość techniczną osobno od etykiety.
- Wartością początkową jest `Prywatna`.
- Pierwsza wersja nie tworzy playlist współtworzonych i nie ustawia automatycznego opisu ani grafiki.
- Nazwa jest wymagana, oczyszczona z przypadkowych znaków sterujących i ograniczona zgodnie z kontraktem API. AMC nie odrzuca drugiej playlisty o tej samej nazwie, ponieważ Spotify dopuszcza powtarzające się nazwy.
- Anuluj nie wysyła żądania. Zapisz blokuje ponowne zatwierdzenie do zakończenia operacji.
- Sukces HTTP 201 dodaje zwróconą playlistę do bieżącej kolekcji Spotify, ustawia fokus na niej, zachowuje użytkową nazwę i mówi `Utworzono playlistę Spotify: nazwa`.
- Błąd nie tworzy lokalnej atrapy. Fokus wraca do pola lub poprzedniego wiersza, a komunikat podaje krótką przyczynę.

## Dodawanie pozycji do playlist Spotify

- Polecenie przyjmuje wyłącznie pozycje z wiarygodnym URI `spotify:track:` albo `spotify:episode:`.
- Album, wykonawca, podcast jako kontener, playlista, kategoria, wiersz `Wczytaj więcej` i element z innej usługi nie są wysyłane jako pozycje playlisty.
- Gdy całe zaznaczenie jest niezgodne, AMC mówi `Do playlisty Spotify można dodać utwory i odcinki Spotify`.
- Przy zaznaczeniu mieszanym zgodne pozycje mogą zostać dodane, ale wynik musi podać liczbę pominiętych pozycji. Lista do wysłania jest niezmienną migawką z chwili zatwierdzenia.
- Okno celu pokazuje tylko playlisty, do których konto może próbować zapisu: własne oraz oznaczone jako współtworzone. Ostateczną decyzję nadal podejmuje API; odpowiedź 403 nie jest przedstawiana jako sukces.
- Każdy wiersz celu ma użytkową etykietę: nazwa, właściciel, prywatna lub publiczna, ewentualnie współtworzona. Identyfikatory konta, `snapshot_id`, typy modelu i URI nie trafiają do NVDA.
- Można zaznaczyć jedną albo kilka playlist. Spacja zmienia wybór i podaje jeden krótki komunikat. Enter lub przycisk `Dodaj` wykonuje operację.
- Przycisk `Utwórz nową playlistę Spotify…` jest zawsze dostępny w oknie, także przy pustej liście. Może mieć lokalny skrót okna, ustalony po audycie konfliktów, ale nie wprowadza nowego skrótu globalnego. Po utworzeniu okno wraca na nową playlistę i zaznacza ją jako cel.
- URI są deduplikowane w obrębie jednego zaznaczenia i wysyłane w widocznej kolejności, partiami do 100.
- AMC domyślnie nie tworzy drugiej kopii pozycji już obecnej na playliście. Używa aktualnej albo bezpiecznie odświeżonej zawartości edytowalnej playlisty do pominięcia identycznego URI i podaje liczbę pominiętych duplikatów. Świadome wielokrotne kopie mogą być osobną funkcją później.
- Każda potwierdzona partia zapisuje zwrócony `snapshot_id`. Błąd późniejszej partii daje wynik częściowy z dokładną liczbą pozycji potwierdzonych i niepotwierdzonych.
- Po sukcesie otwarta zawartość docelowej playlisty jest odświeżana, a fokus wraca na poprzedni wiersz albo pierwszy właśnie dodany element. Inny widok lub sesja wybrane podczas wolnej odpowiedzi nie są przełączane z opóźnieniem.
- Komunikat końcowy ma postać `Dodano do playlisty Spotify: nazwa` albo przy wielu celach `Dodano N pozycji do M playlist Spotify`. Ostrzeżenia o duplikatach i pominięciach są dodawane raz, po wyniku.

## Logowanie i zakresy

- Źródło poświadczeń dla profilu `AMC Test` rozstrzyga AMC16. Implementacja playlist nie może utrwalić wymagania, aby użytkownik tworzył własną aplikację deweloperską Spotify.
- Do `SpotifyScopes` dochodzi osobna grupa `PlaylistWrite` zawierająca `playlist-modify-private` i `playlist-modify-public`.
- Istniejący token nie uzyska nowych zakresów podczas zwykłego odświeżenia. Konto wymaga świadomego ponownego logowania.
- Polecenie nie otwiera automatycznie przeglądarki i nie rozpoczyna OAuth bez decyzji użytkownika. Przy braku zakresu mówi: `Edycja playlist Spotify wymaga ponownego zalogowania. Otwórz Konto Spotify przez Ctrl+F5`.
- Okno konta przed logowaniem wyjaśnia użytkowo oba nowe uprawnienia: zarządzanie prywatnymi i publicznymi playlistami. Nie odczytuje technicznych nazw zakresów jako zwykłego opisu.
- Tokeny, zakresy, identyfikatory właściciela, URI pozycji i `snapshot_id` nie trafiają do komunikatów, schowka ani zwykłego logu.
- W pierwszym publicznym wydaniu Spotify jest całkowicie ukryte, ale `AMC Test` zachowuje i rozwija funkcję playlist. Eksperyment AMC16 rozstrzygnie model jednego logowania dla profilu testowego oraz przygotuje dowody potrzebne do ewentualnej, osobnej decyzji publicznej.

## Model danych

- Dane playlisty Spotify przechowują osobno użytkową nazwę właściciela oraz wewnętrzny identyfikator właściciela.
- Osobne pola opisują prywatność, współtworzenie, możliwość próby edycji i ostatni znany `snapshot_id`.
- Wewnętrzne pola nie są dołączane do `AccessibleLabel` ani `ToString()`.
- Parser akceptuje aktualne pole `item`; pole `track` może być wyłącznie kontrolowanym fallbackiem dla starszej odpowiedzi. Nie wolno podwajać tej samej pozycji, gdy odpowiedź zawiera oba pola.
- Nowo utworzona lub zmieniona playlista jest scalana z kolekcją po stabilnym identyfikatorze Spotify, nie po nazwie.

## Obsługa błędów i limitów

- 401: pojedyncze kontrolowane odświeżenie poświadczenia, potem prawdziwy błąd logowania.
- 403: rozróżnienie braku zakresu, braku prawa do tej playlisty oraz ograniczenia trybu deweloperskiego, o ile odpowiedź pozwala to wiarygodnie ustalić.
- 404: playlista została usunięta lub przestała być dostępna; odświeżyć listę bez tworzenia lokalnej kopii.
- 429: respektować `Retry-After`; `QUOTA_EXCEEDED` nie może uruchamiać pętli ponowień. Komunikat mówi o limicie Spotify, nie o awarii dźwięku.
- Przerwanie sieci przed potwierdzeniem nie ustawia optymistycznie sukcesu. Przy niepewnym wyniku należy odświeżyć playlistę przed kolejną próbą, aby ograniczyć duplikaty.
- Dwa szybkie polecenia są serializowane tą samą bramką operacji konta. Drugie nie może nadpisać nowszego `snapshot_id` starszą odpowiedzią.

## Dostępność NVDA

- Każdy nowy element listy ma jawne `AutomationProperties.Name`, `TextSearch.TextPath` i użytkowe `ToString()` tam, gdzie kontrolka wiąże całe obiekty.
- Test obejmuje początkowo zaznaczoną playlistę, rozwinięcie listy widoczności, strzałki, Spację, wielokrotny wybór, Zapisz, Anuluj i ponowne otwarcie.
- Po zakończeniu operacji NVDA słyszy jeden końcowy rezultat. Komunikat przygotowania nie może zagłuszyć sukcesu albo błędu.
- Nazwa klasy, rekord, enum widoczności, identyfikator konta, URI ani `snapshot_id` nie może zostać wypowiedziany.
- Po wolnej odpowiedzi sieci fokus wraca tylko wtedy, gdy użytkownik nadal jest w tym samym oknie i kontekście.

## Pomoc, paleta i menu

- `Ctrl+F1` opisuje `Ctrl+P — playlisty Spotify` i `Ctrl+Shift+P — dodaj zaznaczone utwory lub odcinki do playlisty Spotify`, wyłącznie w sesji Spotify.
- Pomoc wyjaśnia, że w oknie `Ctrl+Shift+P` można wybrać istniejącą playlistę albo utworzyć nową natywną playlistę Spotify.
- Paleta `Ctrl+Shift+K` zawiera trzy jawne polecenia: tworzenie, dodawanie i pokazanie playlist konta Spotify.
- Menu główne, kontekstowe listy, wyniki wyszukiwania i odtwarzacz pokazują nowe polecenia tylko w zgodnym kontekście Spotify.
- Istniejące pozycje playlist AMC w sesji Spotify zostają doprecyzowane słowem `AMC`, bez zmiany ich skrótów.

## Testy do przygotowania przy wdrożeniu

1. `Ctrl+P` i `Ctrl+Shift+P` zachowują tę samą intencję użytkową we wszystkich sesjach, ale wybierają typ playlisty właściwy dla sesji; Spotify nigdy nie zapisuje tym skrótem do lokalnej playlisty AMC.
2. `Ctrl+Shift+P` w Spotify pokazuje istniejące edytowalne playlisty Spotify oraz zawsze dostępną możliwość utworzenia nowej; przy pustej liście nie pozostawia użytkownika bez dalszej czynności.
3. Tworzenie prywatnej i publicznej playlisty wysyła `POST /me/playlists` z prawidłową nazwą i widocznością oraz przyjmuje 201.
4. Anulowanie nie wysyła HTTP; podwójny Enter nie tworzy dwóch playlist.
5. Nowa playlista jest scalana po identyfikatorze i otrzymuje fokus mimo powtarzającej się nazwy.
6. Dodawanie wysyła `POST /playlists/{id}/items`, partie najwyżej po 100 URI, we właściwej kolejności.
7. Utwory i odcinki są przyjmowane, pozostałe rodzaje są pomijane albo prawidłowo odrzucane.
8. Własna, współtworzona i obca playlista są poprawnie rozróżnione bez porównywania nazw właścicieli.
9. Brak każdego z nowych zakresów daje konkretną instrukcję ponownego logowania, bez otwierania przeglądarki.
10. Aktualny `/items` i starszy fallback `track` są parsowane bez dublowania pozycji; stary endpoint `/tracks` nie jest wysyłany.
11. Odpowiedzi 401, 403, 404 i oba rodzaje 429 przechodzą testy na atrapach HTTP bez ujawnienia tokenu lub danych technicznych.
12. Częściowa awaria drugiej partii zachowuje potwierdzony wynik pierwszej i podaje prawdziwe liczby.
13. Szybka zmiana sesji lub widoku przed odpowiedzią nie kradnie fokusa i nie otwiera z opóźnieniem playlisty.
14. Etykiety listy celów przechodzą test NVDA dla początkowego fokusa, strzałek, Spacji, zapisu, anulowania i ponownego otwarcia.
15. Test na prawdziwym koncie jest oddzielny i wymaga świadomej zgody na utworzenie danych. Używa wyraźnie nazwanej playlisty testowej; nie usuwa ani nie zmienia istniejących playlist użytkownika.

## Świadomie poza zakresem

- uruchamianie całej playlisty Spotify albo zmiana kontekstu Page Up/Page Down na playlistę;
- usuwanie pozycji, zmiana kolejności, zmiana nazwy, opisu, widoczności lub grafiki istniejącej playlisty;
- tworzenie playlist współtworzonych;
- kopiowanie lokalnej playlisty AMC do Spotify jednym poleceniem;
- przenoszenie playlist między kontami lub usługami;
- automatyczne usuwanie playlisty testowej bez osobnej zgody użytkownika.

## Bramka

- Poziom A: implementacja klienta, modeli, routingu, okien, pomocy i testów z atrapami HTTP bez kontaktu z kontem.
- Poziom B: kompilacja i testy automatyczne razem z pozostałymi zmianami Spotify.
- Poziom C: ręczna próba NVDA i świadoma próba na koncie testowym albo na koncie użytkownika po jego zgodzie.
- AMC08 pozostaje częścią Bramy 4 z AMC09 i AMC10 i ma zostać ukończone dla `AMC Test`; publiczny profil nadal pomija całe Spotify. Sama próba konta może odbyć się oddzielnie.
- Przed kompilacją albo uruchomieniem AMC nadal trzeba potwierdzić, że nie trwa nagrywanie.
