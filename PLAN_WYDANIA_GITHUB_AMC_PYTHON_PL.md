# AMC Python — plan przed pierwszym wydaniem przez GitHub

Ten dokument zapisuje pierwotny plan przygotowany przed decyzją wydawniczą.
Korekta użytkownika z 26 października 2026 r. zastępuje wcześniejszy wymóg
osobnej zgody dla każdego stanu: każde faktyczne, zweryfikowane wydanie ma
trafić na GitHub. Bieżący model dwóch kanałów, kolejność migracji i bramki
bezpieczeństwa są nadrzędnie opisane w
`docs/zadania/REL-002-kanoniczne-wydania-test-public-github.md`.

## Cel

Każda wersja przekazywana użytkownikowi lub innym testerom ma pochodzić z
jednego oznaczonego commita i jednego wydania GitHub. Kod źródłowy, numer
wersji, manifest paczki, plik instalacyjny lub ZIP, informacje aktualizatora,
sumy kontrolne i dokumentacja zmian muszą wskazywać dokładnie tę samą wersję.
Nie wolno publikować paczki z lokalnymi poprawkami nieobecnymi w oznaczonym
commicie.

## Docelowe nazwy i profile produktu

- Stary program WPF z serii `alpha.4xx`, w tym wersja około `alpha.422`, jest
  historycznym AMC i nie uczestniczy w nowym procesie wydania.
- Obecny `AMC Python` jest jedyną rozwijaną bazą produktu. Przy wydaniu jego
  pełny profil zmieni nazwę na `AMC Test`.
- Publiczne `AMC` jest budowane z tej samej bazy kodu i tego samego oznaczonego
  commita co `AMC Test`, lecz z ograniczonym manifestem możliwości.
- Funkcje testowe nie mogą przypadkiem wrócić do publicznej paczki przez menu,
  pomoc, paletę, skrót, plik zależności ani pozostawiony adapter usługi.
- Dane, instalacja, blokada jednej instancji i kanały aktualizacji profili są
  rozdzielone. Kontrolowane przenoszenie zgodnych danych użytkowych wymaga
  osobnego, jawnego mechanizmu.

## 1. Model wersji i wydań GitHub

- Ustalić prostą numerację wersji oraz dwa kanały: testowy i stabilny, jeśli
  oba okażą się potrzebne. Nazwa okna może nadal podawać czytelną datę i
  godzinę, ale diagnostyka musi również znać jednoznaczny numer i commit.
- Dla każdej wersji utworzyć tag, GitHub Release, opis zmian, załącznik
  użytkowy, manifest plików oraz SHA-256 załącznika.
- Zbudować wydanie wyłącznie z czystego oznaczonego commita w powtarzalnym
  środowisku. Zachować rachunek budowy i wyniki testów.
- Przed pierwszą publikacją zdecydować o licencji repozytorium, licencjach
  dołączanych bibliotek oraz ewentualnym podpisie kodu. Brak podpisu trzeba
  jasno opisać testerom; nie wolno imitować zaufanego podpisu.
- Wykluczyć z repozytorium i paczki dane kont, tokeny, lokalne bazy, historię,
  nagrania, logi użytkownika, cache oraz prywatne ścieżki.

## 2. Kompletna paczka użytkowa i zależności

Przygotować wersjonowany spis wszystkich składników potrzebnych na komputerze
bez środowiska programistycznego. Dla każdego składnika zapisać wersję,
pochodzenie, licencję, sposób aktualizacji i sumę kontrolną, jeśli jest
dołączany lub pobierany przez AMC.

Spis ma objąć co najmniej:

- prywatny runtime Python, wxPython i pozostałe koła z przypiętymi wersjami;
- host .NET i wymagany runtime lub decyzję o paczce samowystarczalnej;
- natywne biblioteki audio i host Spotify/Librespot;
- FFmpeg i inne dekodery potrzebne do obsługiwanych formatów;
- `yt-dlp` oraz komponenty używane do odtwarzania, pobierania i wyszukiwania
  treści YouTube;
- WebView2 i moduły internetowe wykorzystywane przez TIDAL lub Spotify;
- wszystkie pliki licencji i informacji o autorach wymagane przy dystrybucji.

AMC nie może zależeć od przypadkowej globalnej instalacji Pythona, `yt-dlp`,
FFmpeg, Node, narzędzi deweloperskich ani cache Codex. Należy sprawdzić start,
odtwarzanie, pobieranie i wyszukiwanie na czystym koncie Windows.

## 3. Bezpieczne aktualizacje programu i komponentów

- Aktualizator programu pobiera informacje wyłącznie z ustalonego źródła
  GitHub Releases i rozróżnia kanał testowy od stabilnego.
- Przed instalacją weryfikuje wersję, zgodność formatu paczki, manifest i
  SHA-256. Aktualizacja ma być transakcyjna, zachowywać ustawienia i umożliwiać
  odzyskanie poprzedniej wersji po błędzie.
- Nadal obowiązuje bezpieczne zamknięcie: aktualizator nie może wymuszać
  zakończenia AMC podczas nagrywania ani pozostawiać częściowo podmienionej
  instalacji.
- Aktualizacje FFmpeg, `yt-dlp` i podobnych komponentów muszą używać osobnych,
  wersjonowanych manifestów, oficjalnych źródeł, sum kontrolnych i możliwości
  wycofania. Nie wolno po cichu pobierać „najnowszego” pliku bez ustalonej
  wersji i weryfikacji.
- Sprawdzić kolejno: świeżą instalację, aktualizację z poprzedniego wydania,
  brak sieci, uszkodzoną paczkę, przerwanie podmiany i powrót do działającej
  wersji.

## 4. Dostępne zgłaszanie błędów

- Dodać prosty moduł dostępny klawiaturą i poprawnie czytany przez NVDA.
- Raport ma automatycznie zawierać tylko bezpieczne dane techniczne: numer
  wersji, commit, wersje komponentów, system oraz wybrany przez użytkownika
  zakres diagnostyki.
- Przed dołączeniem logów pokazać, co zostanie wysłane, umożliwić podgląd i
  usunięcie danych. Domyślnie nie dołączać nazw plików prywatnych, adresów
  strumieni, historii, treści kont ani tokenów.
- Ustalić docelowy kanał: formularz tworzący zgłoszenie GitHub albo bezpieczne
  przygotowanie raportu do ręcznego wysłania. Program nie powinien publikować
  raportu bez jednoznacznego zatwierdzenia użytkownika.

Zatwierdzony kierunek opisuje zadanie `REL-001`: własna instancja
`michaldziwisz/sygnalista` na licencji MIT tworzy zwykłe GitHub Issues bez
wymagania konta GitHub od zgłaszającego. Pełny raport i opcjonalny log trafiają
do prywatnego repozytorium, a publiczne issue zawiera bezpieczne podsumowanie.
Log pozostaje domyślnie wyłączony i przed wysłaniem wymaga podglądu oraz
jednoznacznego zatwierdzenia.

GitHub Issues staje się kolejką zgłoszeń, nie automatycznym poleceniem zmiany
kodu. Po weryfikacji wybrane issue można powiązać z zadaniem w
`docs/zadania`; Codex albo Hermes rozpoczyna analizę dopiero na jawne polecenie
użytkownika.

## 4a. Licencje i dobrowolne wpłaty

Radio Browser zezwala na użycie danych i API w programach darmowych oraz
niedarmowych, więc katalog stacji nie blokuje sam w sobie PayPala ani GitHub
Sponsors. Osobną bramą jest dołączony BASS: jego bezpłatna licencja obejmuje
podmiot niekomercyjny, który nie zarabia na produkcie. Przed dodaniem wpłat
należy wykonać `LIC-001` i uzyskać pisemne potwierdzenie Un4seen, kupić
odpowiednią licencję albo usunąć BASS z profilu publicznego.

## 5. Dokumentacja przed testami

Przygotować i sprawdzić co najmniej:

- instrukcję instalacji, pierwszego uruchomienia, aktualizacji i odinstalowania;
- pełną listę skrótów klawiszowych według sesji i widoku;
- opis Biblioteki, odtwarzacza, pobierania, nagrywania i integracji sieciowych;
- instrukcję zgłaszania błędów i znajdowania numeru wersji;
- wymagania systemowe, zasady prywatności, listę komponentów i licencji;
- rozwiązywanie typowych problemów z NVDA, WebView2, urządzeniami audio,
  YouTube, Spotify, TIDAL, Sonos i WiiM.

Dokumentacja ma odpowiadać rzeczywistemu wydaniu. Skrótu lub funkcji, której
nie ma w paczce, nie wolno opisywać jako dostępnej.

## 6. Odbiór wydania

Przed każdym wydaniem testowym wykonać automatyczny pełny zestaw testów oraz
krótki odbiór ręczny z NVDA. Odbiór obejmuje co najmniej:

- instalację i aktualizację na czystym profilu oraz migrację istniejącego
  profilu bez utraty ustawień i kolekcji;
- wszystkie globalne skróty oraz skróty zależne od widoku;
- fokus początkowy, listy, pola kombi, dialogi, Save/Cancel i ponowne otwarcie;
- odtwarzanie obsługiwanych formatów, YouTube, radia, podcastów i usług;
- pobieranie, nagrywanie, operacje na plikach oraz zachowanie po błędzie;
- aktualizację komponentów i całej aplikacji, także przy braku sieci i
  odrzuconej sumie kontrolnej;
- brak technicznych identyfikatorów i reprezentacji obiektów w mowie NVDA.

Wydanie jest gotowe dopiero wtedy, gdy tag, załącznik GitHub, manifest, sumy,
opis zmian, dokumentacja i wynik testów zostały wzajemnie porównane. Po
publikacji należy pobrać załącznik tak, jak zrobi to tester, ponownie sprawdzić
sumę i wykonać próbę aktualizacji z poprzedniej publicznej wersji.
