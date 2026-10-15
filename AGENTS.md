# AMC — ustalenia projektu

- Kanoniczne repozytorium bieżącego, nowego AMC Python:
  `D:\Projekty Codex\AMC - integracja wxPython`.
- `D:\Projekty Codex\Accessible Multimedia Controller` zawiera wycofany z
  bieżących prac stary interfejs WPF. Można go czytać jako materiał historyczny,
  ale nie należy tam wdrażać nowych poprawek ani budować użytkowej aktualizacji.
- Użytkownik 9 października
  2026 r. wyraził stałą zgodę na pracę w tym katalogu także po wznowieniu
  zadania; nie pytaj ponownie o wybór katalogu roboczego.
- Zmiany z aktywnego katalogu integracji wxPython pozostają lokalne. Nie
  wysyłaj ich do GitHuba bez osobnej, aktualnej zgody użytkownika na publikację.
- Historyczna zgoda z 9 września 2026 r. na publikowanie starego AMC nie jest
  bieżącą zgodą na publikację nowego AMC Python. Dla tego projektu zawsze
  wymagana jest osobna decyzja dotycząca konkretnego przygotowanego stanu.
- Przed publikacją sprawdzaj zakres zmian i zawartość pakietu. Nie publikuj
  poświadczeń, danych kont, lokalnych kolekcji, prywatnych nagrań ani logów
  użytkownika. Zgoda nie obejmuje innych repozytoriów ani kontaktowania
  zewnętrznych osób w imieniu użytkownika.
- Publikacja źródeł, publikacja ZIP w Releases i uruchomienie programu są
  osobnymi czynnościami. Raportuj ich rzeczywiste wyniki, także blokady.
  Nie zamykaj programu w trakcie nagrywania.
- Użytkownik 11 września 2026 r. zezwolił na przyszłe instalowanie aktualizacji
  dodatku AMC do NVDA oraz uruchamianie/restartowanie NVDA i AMC, z uprzednim
  zamknięciem poprzednich instancji. Przed takim działaniem sprawdź, czy AMC
  nie nagrywa (także w tle lub z harmonogramu). Gdy nie da się tego potwierdzić,
  nie zamykaj programów i zapytaj. Sama publikacja nie wymaga restartu.
- Po publikacji wydania usuń jego lokalny ZIP z `publish` dopiero po
  zweryfikowaniu, że odpowiadający mu załącznik GitHub Releases został
  skutecznie wysłany i jest dostępny (nazwa, rozmiar i, gdy dostępny, SHA-256).
  Sam push źródeł nie oznacza wysłania ZIP-a. Niewysłane i niezweryfikowane
  paczki pozostaw; nie usuwaj przy tym rozpakowanej bieżącej wersji programu.
- Priorytet TIDAL: zweryfikowane pełne odtwarzanie, nie deklarowanie próbek
  jako pełnych utworów. Ustalenia i granice: `PROJEKT_TIDAL_PL.md`.
- Wynik zwykłego logowania do Embed i analiza jego kodu:
  `TIDAL_WERYFIKACJA_PELNEGO_ODTWARZANIA_2026-09-09.md`. Nie prosić ponownie
  o identyczne logowanie bez nowego dowodu. Za osobną zgodą użytkownika pytanie
  wysłano do TIDAL: https://github.com/orgs/tidal-music/discussions/384.
  Nie dublować zgłoszenia. Zgoda nie obejmuje podłączania tożsamości Nostr.
- Testy muszą kończyć się niezerowym kodem i diagnostyką po niepowodzeniu,
  nie pozostawionym oknem awarii CLR. Test negatywny nie jest zaliczeniem
  funkcji. Profile WebView2 testów są odizolowane od konta i stanu AMC.
- Etykiety dostępności list, pól kombi i menu muszą być tekstem użytkowym,
  nigdy domyślną reprezentacją obiektu, enuma ani identyfikatorem komendy.
  Testuj początkowy fokus, strzałki, ponowne otwarcie i powrót po zamknięciu.

## Skróty globalne

- Widok sesji, urządzenia ani listy nie może przejmować skrótu globalnego i
  pozostawiać go bez działania. `Ctrl+H` otwiera Historię odtwarzania z każdego
  głównego miejsca programu, w szczególności z Radia internetowego, podcastów,
  WiiM i Sonosa. Po zamknięciu historii fokus wraca do elementu, z którego ją
  wywołano.
- Przy dodawaniu nowego widoku lub integracji sprawdź wspólną tablicę skrótów,
  co najmniej `Ctrl+H`, `Alt+R`, `Alt+Shift+R` i `Ctrl+L`. Dodawaj testy
  parametryzowane dla reprezentatywnych widoków zamiast osobnych, rozbieżnych
  obsług klawiszy.

## Edycja plików audio

- Polecenie wycięcia „do końca pliku” oznacza koniec rzeczywistej osi ramek
  odczytanej przez FFmpeg, a nie zaniżony czas z nagłówka, odtwarzacza albo
  ostatniej pozycji odsłuchu. Ręcznie ustawiona granica wcześniejsza niż koniec
  nadal pozostaje granicą ręczną.
- Każda zmiana destrukcyjnej edycji audio wymaga parametryzowanego testu całej
  listy formatów audio deklarowanej przez `LocalAudioFileDiscovery`, w tym
  aliasów rozszerzeń. Test ma przygotować prawdziwy plik danego kodeka,
  zasymulować zaniżony czas odtwarzacza, wyciąć ogon, sprawdzić rzeczywistą
  długość wyniku i brak plików roboczych. Kontenery wideo pozostają jawnie
  odrzucone, dopóki nie powstanie osobny, równie pełny kontrakt ich edycji.
- Nie uznawaj samego kodu wyjścia FFmpeg za dowód poprawności. Oryginał wolno
  zastąpić dopiero po odczytaniu wyniku i porównaniu jego osi czasu z
  oczekiwanym skutkiem operacji.

## Wyszukiwanie, relacje i biblioteka

- Wynik wyszukiwania zachowuje swój rzeczywisty typ i tożsamość. Enter na
  wykonawcy otwiera wykonawcę, na albumie album, na utworze utwór, a w
  podcastach odpowiednio podcast lub odcinek. Nie wolno podmieniać zaznaczenia
  na podobny albo wcześniej zapisany element z biblioteki.
- `Prawa strzałka` na wyniku otwiera jedno użytkowe menu relacji właściwe dla
  typu elementu. Dla wykonawcy obejmuje co najmniej albumy i utwory, jeżeli
  usługa je udostępnia. Relacje mają służyć przeglądaniu katalogu przed
  świadomym dodaniem czegokolwiek do biblioteki.
- Wyszukiwanie, Enter, prawa strzałka i samo przeglądanie nigdy nie zmieniają
  biblioteki ani ulubionych. Dodanie wymaga osobnego, jawnego polecenia
  użytkownika. Zasada obowiązuje TIDAL, Radio Browser, podcasty, przyszłe
  Spotify i inne katalogi.
- Test wyszukiwania porównuje bibliotekę przed i po przeglądaniu, obejmuje
  element już zapisany oraz niezapisany, sprawdza typ zaznaczenia, fokus,
  pojedynczą reakcję Enter i menu prawej strzałki. Nie wolno uznać samego
  poprawnego tekstu wyniku za dowód prawidłowego routingu.
- `Ctrl+F` działa w każdym sensownie przeszukiwalnym widoku, również w WiiM i
  Sonosie. Wyszukiwanie lokalne filtruje lub odnajduje elementy już wczytanej
  listy, na przykład strumienie i playlisty. Wyszukiwanie globalne korzysta z
  katalogu usługi tylko wtedy, gdy oficjalne API udostępnia taką możliwość.
  Interfejs zawsze jasno podaje zakres i nie przełącza go po cichu.
- Lokalne i globalne wyszukiwanie używają wspólnego zachowania klawiatury:
  przewidywalny fokus, Enter na rzeczywistym wyniku, Escape do poprzedniego
  miejsca i brak automatycznego zapisu. Adapter dostawcy dostarcza dane oraz
  możliwości, ale nie tworzy osobnego, rozbieżnego interfejsu wyszukiwarki.

## Wspólny kontrakt interfejsu źródeł

- Zachowanie, które użytkownik odebrał i jednoznacznie potwierdził jako dobre,
  staje się wzorcem akceptacyjnym dla równoważnych funkcji w innych źródłach.
  Nie projektuj ponownie bez wskazanej potrzeby. Przenoś ten sam układ skrótów,
  nawigację, kolejność komunikatów, fokus, powrót i znaczenie Entera oraz
  strzałek wszędzie, gdzie możliwości usługi na to pozwalają.
- Dopracowany TIDAL jest wzorcem funkcjonalnym interfejsu Spotify: wejście do
  biblioteki, wyszukiwanie lokalne i globalne, rzeczywista tożsamość wyniku,
  relacje wykonawca–album–utwór, przeglądanie przed zapisem, odtwarzanie,
  dodawanie i usuwanie, sortowanie, historia, Escape i przywracanie fokusu.
  Stare AMC i librespot mogą dostarczyć rozwiązania techniczne, lecz nie są
  wzorcem zachowania interfejsu.
- Jawny wyjątek potwierdzony przez użytkownika: działające `Shift+F2` ze
  starego AMC jest wzorcem funkcjonalnym zmiany nazwy pliku w AMC Python.
  Zachowaj nazwę bez rozszerzenia w dialogu, niezmienne rozszerzenie, brak
  nadpisywania, zatrzymanie aktualnie wczytanego pliku z zachowaniem pozycji,
  zmianę fizycznej nazwy na dysku, stabilną tożsamość rekordu, aktualizację
  Biblioteki, historii i zakładek oraz powrót fokusu. Sukces wolno ogłosić
  dopiero po potwierdzeniu nowej ścieżki. Operację plikową wykonuje host C#;
  wxPython prowadzi dialog i odświeża interfejs, więc sama technologia Python
  nie jest powodem różnicy w zachowaniu.
- Nie kopiuj osobnych przepływów ekran po ekranie. Utrzymuj wspólny model
  elementu, nawigacji i możliwości oraz wspólną warstwę poleceń; adapter
  dostawcy ma jedynie pobierać dane, mapować tożsamość i jawnie zgłaszać
  obsługiwane możliwości. Dzięki temu poprawka wspólnej funkcji obejmuje
  wszystkie porównywalne usługi zamiast rozchodzić się na rozbieżne wersje.
- Kontekst nawigacji obejmuje co najmniej źródło i sesję, zakres wyszukiwania,
  zapytanie, rzeczywisty typ i identyfikator zaznaczenia, stos powrotu,
  sortowanie oraz bieżące urządzenie, jeśli dotyczy. Wynik asynchroniczny musi
  należeć do aktualnej generacji żądania; spóźniona odpowiedź nie może
  podmienić nowszego widoku, zaznaczenia ani źródła.
- Każda nowa funkcja współdzielona dostaje test kontraktowy uruchamiany dla
  wszystkich odpowiednich adapterów. Test obejmuje nie tylko tekst listy, ale
  też tożsamość elementu, brak niejawnego zapisu, fokus początkowy i powrotny,
  Enter, Escape, lewą i prawą strzałkę, skróty oraz odpowiedź spóźnionego
  żądania. Po teście automatycznym wykonaj próbę z NVDA.
- Ograniczenia API są dozwoloną różnicą, lecz mają być reprezentowane jako
  brak możliwości z jasnym komunikatem. Nie zgaduj brakujących relacji, nie
  podstawiaj podobnego elementu z biblioteki i nie pokazuj technicznego
  identyfikatora w miejsce danych, których dostawca nie udostępnia.

## Pierwsze uruchomienie i logowanie do usług

- Docelowy instalator prowadzi zwykłego użytkownika przez dostępny, oficjalny
  przepływ logowania. Nie powinien żądać ręcznego tworzenia aplikacji
  deweloperskiej, wyszukiwania identyfikatora klienta ani przepisywania
  technicznych wartości, jeżeli regulamin i API pozwalają użyć rejestracji AMC
  oraz publicznego przepływu autoryzacji.
- Dla każdej usługi osobno wybierz najprostszy bezpieczny mechanizm wspierany
  przez dostawcę, na przykład OAuth z PKCE, kod urządzenia, dostęp lokalny lub
  wykrywanie urządzenia. Nie ujednolicaj protokołów pozornie; ujednolicaj
  doświadczenie użytkownika, komunikaty, anulowanie, ponawianie i wylogowanie.
- Sekretu klienta, tokenu odświeżania ani danych konta nie wolno osadzać w
  publicznym instalatorze, repozytorium, logu ani nazwie kontrolki. Dane sesji
  przechowuj mechanizmem chronionym systemu operacyjnego. Sam publiczny
  identyfikator aplikacji można dołączyć wyłącznie zgodnie z modelem i
  regulaminem konkretnego dostawcy.
- Jeżeli dostawca naprawdę wymaga od każdego użytkownika własnej rejestracji
  deweloperskiej, nie ukrywaj tego obejściem. Przygotuj dostępny kreator z
  jasnym wyjaśnieniem i minimalną liczbą kroków. Ostateczny projekt tego etapu
  powstaje po integracji Spotify i po ponownej weryfikacji aktualnych wymagań
  Sonosa, WiiM, Spotify i pozostałych usług.
- Odbiór wykonuj na czystym profilu lub maszynie: od pierwszego uruchomienia do
  gotowej sesji, z NVDA, bez wcześniej zapisanych tokenów i bez narzędzi
  deweloperskich. Test obejmuje anulowanie, wygaśnięcie kodu, odmowę dostępu,
  ponowienie, wylogowanie i aktualizację programu bez utraty ważnej sesji.

## Równoległe integracje systemów głośnikowych

- WiiM i Sonos są wzorcem wspólnego kontraktu dla przyszłych systemów
  głośnikowych z otwartym API. Nowa integracja ma używać wspólnego modelu
  możliwości i zachowania interfejsu wszędzie tam, gdzie urządzenia oferują
  równoważne funkcje; różnice producenta należy izolować w adapterze API.
- Każda poprawka dotycząca jednego systemu wymaga przeglądu wszystkich
  równoległych integracji. Nie kończ zadania po naprawieniu tylko zgłoszonej
  marki, jeżeli ten sam wzorzec listy, skrótu, fokusa, transportu lub błędu
  występuje także w pozostałych adapterach.
- Jednorodna lista zapisanych strumieni przekazuje NVDA nazwę strumienia i
  natywną informację o pozycji na liście. Nie dopisuj do każdego wiersza
  stałych tekstów „stacja zapisana w AMC”, „strumień sieciowy”, nazwy źródła
  ani marki urządzenia. Adres pozostaje danymi modelu i jest odczytywany lub
  kopiowany wyłącznie na jawne polecenie użytkownika.
- `Lewa strzałka` jest wspólnym, jawnym poleceniem odczytu parametrów stacji
  lub strumienia. W WiiM, Sonosie i przyszłych integracjach ma podawać te same
  użytkowe dane, które są dostępne w Radiu internetowym, w tym adres lub
  ścieżkę źródła, jeżeli adapter rzeczywiście je udostępnia. Działanie nie
  zależy od prawa do edycji albo usunięcia pozycji: obejmuje także ulubione i
  inne listy tylko do odczytu. Gdy API nie zwraca danego parametru, nie wolno
  go zgadywać ani zastępować identyfikatorem technicznym.
- Dla każdej integracji zachowaj ten sam kontrakt klawiatury i fokusa, o ile
  API wspiera daną funkcję: wybór ostatnio używanego urządzenia, wejście i
  powrót z Biblioteki, `Ctrl+Shift+C`, transport, kierunki regulacji głośności,
  komunikaty ładowania, pustej listy i błędu. Brak możliwości API ma być
  uczciwie zakomunikowany, a nie zastąpiony zachowaniem pozornym.
- Identyfikatory urządzeń, grup, strumieni i wartości protokołu pozostają w
  modelu. Nazwy dostępne, kolumny i komunikaty muszą być złożone wyłącznie z
  zamierzonych tekstów użytkowych.
- Dodawaj wspólne lub parametryzowane testy kontraktowe, które uruchamiają ten
  sam scenariusz dla WiiM, Sonos i każdego nowego adaptera. Test ma sprawdzać
  rzeczywisty tekst wszystkich kolumn listy, początkowy i przywrócony fokus,
  Enter, Escape, strzałki, kopiowanie adresu oraz ponowne otwarcie. Zmiana
  adaptera wymaga też krótkiej próby z NVDA; sam poprawny tekst wizualny nie
  jest wystarczający.
