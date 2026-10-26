# AMC16 — Spotify: jedno proste logowanie z Librespot

Data przygotowania zakresu: 18 października 2026 r.

Status: wykonano audyt istniejącej drogi logowania AMC, upstream Librespot i publicznie dostępnych informacji o programach Eltena. Zatwierdzono zachowanie Librespota oraz przygotowanie osobnego eksperymentu jednego logowania dla prawdziwego konta Premium wyłącznie w prywatnym profilu `AMC Test`. Publiczne `AMC` nie pokazuje Spotify w ogóle do czasu pełnej weryfikacji i osobnej decyzji wydawniczej. Nie zmieniono kodu produkcyjnego, nie użyto prawdziwego konta, nie kompilowano i nie uruchamiano AMC ani Eltena.

## Cel

Użytkownik profilu `AMC Test` ma włączyć Spotify i połączyć swoje prawdziwe konto Premium bez tworzenia aplikacji w Spotify for Developers, bez wpisywania Client ID i bez podawania hasła w AMC. Po jednym procesie AMC ma podać, które możliwości faktycznie działają: odtwarzanie, wyszukiwanie, biblioteka oraz playlisty.

To zadanie bada wykonalność i bezpieczeństwo tej drogi. Nie zakłada z góry, że jedno uwierzytelnienie będzie mogło zasilić wszystkie funkcje. Musi jednak objąć zakresy potrzebne AMC08, ponieważ użytkownik zatwierdził tworzenie i uzupełnianie natywnych playlist Spotify we własnym `AMC Test`.

## Stan obecny AMC

1. Odtwarzanie Librespot ma już prosty przepływ urządzenia. AMC pobiera jednorazowy kod, pokazuje adres Spotify, czeka na zgodę i zapisuje token w Menedżerze poświadczeń Windows.
2. Hasło jest wpisywane wyłącznie na stronie Spotify i nie trafia do AMC.
3. Przepływ urządzenia używa identyfikatora klienta Spotify Desktop znanego z upstream Librespot. Żądany jest obecnie wyłącznie zakres odtwarzania.
4. Katalog, wyszukiwanie, biblioteka i obecne funkcje kolekcji mają drugie logowanie Web API z własnym Client ID i lokalnym adresem powrotu.
5. Natywny host AMC steruje bezpośrednio `Player` Librespota. Został świadomie zbudowany bez discovery, Zeroconf i Spirc, dlatego nie pojawia się obecnie jako urządzenie do wybrania w oficjalnej aplikacji Spotify.
6. Dwa osobne okna konta są poprawne technicznie, ale nie są dobrym pierwszym uruchomieniem dla odbiorcy instalatora.

## Wniosek z porównania z Eltenem

- aktualne opisy użytkowe potwierdzają, że aplikacja Elten Link udostępniała wygodną obsługę Spotify dla kont Premium, z wyszukiwaniem i obsługą playlist;
- użytkownik pamięta, że aplikacja Elten Link pozwalała zalogować się zwykłym kontem i po zalogowaniu udostępniała zawartość Spotify bez samodzielnego tworzenia aplikacji deweloperskiej. To istotny wzorzec produktowy, ale na 18 października 2026 r. pozostaje obserwacją użytkową, a nie potwierdzeniem konkretnego protokołu lub bieżącego działania Elten Link;
- publiczne repozytoria `dawidpieper/elten2` i `dawidpieper/elten3` nie zawierają kodu nazwanego `spotify` ani `librespot`; programy Eltena mogą być dostarczane oddzielnie od rdzenia;
- nie ma więc podstaw, aby twierdzić, że Elten używa konkretnego Client ID, przepływu urządzenia, Zeroconf albo brokera;
- do AMC przenosimy wyłącznie wzorzec użytkowy: jedno proste połączenie i jasny stan funkcji. Nie instalujemy, nie debugujemy i nie kopiujemy programu Eltena. Kod Eltena jest GPLv3, a kod osobnego programu może mieć inne zasady.

## Uzupełnienie techniczne: jeden token jest realną hipotezą

- dokumentacja kodu upstream Librespot z 18 października 2026 r. wprost podaje, że token OAuth z odpowiednimi zakresami może służyć zarówno do Spotify Web API, jak i do utworzenia sesji Librespot;
- obecny AMC nie wykorzystuje tej możliwości: parowanie kodem prosi tylko o zakres `streaming`, a katalog, biblioteka i playlisty mają osobne logowanie Web API z własnym Client ID;
- dlatego najważniejsza próba AMC16 ma rozszerzyć wyłącznie kontrolowany prototyp parowania o dokładnie potrzebne zakresy biblioteki i playlist, a następnie sprawdzić na tym samym tokenie kolejno profil, wyszukiwanie, bibliotekę, własne playlisty, tworzenie playlisty i odtwarzanie;
- sukces techniczny nie rozstrzyga jeszcze publikacji. Spotify udostępnia przepływ urządzenia tylko wybranym identyfikatorom klienta, a używany identyfikator Spotify Desktop nie jest tożsamością AMC. Trzeba osobno ocenić trwałość, zgodność z zasadami i możliwość bezpiecznego wyłączenia funkcji;
- zwykłe oficjalne Web API pozostaje ograniczone: aplikacja w trybie deweloperskim obsługuje najwyżej pięciu wskazanych użytkowników, a rozszerzony dostęp dla szerokiej publiczności wymaga obecnie organizacji i spełnienia wysokich kryteriów Spotify. To wyjaśnia, dlaczego droga z własnym Client ID nie nadaje się na prosty instalator, mimo że Spotify jest usługą masową.

## Granice rozsądnego użycia

- wymagamy prawdziwego konta Spotify Premium;
- nie obchodzimy płatności, reklam, ograniczeń konta Free, blokad geograficznych, ochrony treści ani limitów równoczesnego odtwarzania;
- AMC nie pobiera plików Spotify i nie udostępnia nagrywania ani trwałego przechwytywania strumienia;
- użytkownik świadomie zatwierdza swoje konto i może je równie łatwo odłączyć;
- dane logowania pozostają w Menedżerze poświadczeń Windows, nie w zwykłym pliku ustawień ani kopii zapasowej;
- prawdziwe konto użytkownika nie rozwiązuje automatycznie kwestii tożsamości klienta. Spotify wymaga osobnego kodu klienta dla każdej aplikacji, a identyfikator Spotify Desktop nie jest identyfikatorem AMC;
- mechanizmu opartego na cudzym Client ID nie nazywamy oficjalnym i nie uznajemy automatycznie za właściwy dla stabilnego publicznego wydania tylko dlatego, że działa technicznie.

## Eksperyment A — obecny kod urządzenia

1. Na świeżym profilu AMC i testowym koncie Premium przejść pełny proces `spotify.com/pair`.
2. Sprawdzić anulowanie, wygaśnięcie kodu, odmowę zgody, zamknięcie okna, ponowne uruchomienie AMC, odświeżenie tokenu i odłączenie konta.
3. Sprawdzić, które zakresy faktycznie są przyznawane i czy bezpiecznie można użyć tego samego zatwierdzonego stanu do odczytu katalogu, biblioteki i playlist.
4. Nie poszerzać zakresów metodą prób i błędów na koncie użytkownika. Lista zakresów musi zostać ustalona przed testem i odpowiadać dokładnie funkcjom AMC.
5. Osobno sprawdzić tworzenie i edycję playlist z AMC08. Odczyt biblioteki nie stanowi dowodu prawa do jej zmiany.

## Eksperyment B — Spotify Connect przez sieć lokalną

1. W osobnej gałęzi prototypowej rozszerzyć natywny host o discovery Librespota.
2. Uruchomić czasowo urządzenie o dostępnej nazwie, na przykład `AMC — połącz konto`.
3. Użytkownik otwiera oficjalną aplikację Spotify na telefonie lub komputerze i wybiera AMC na liście urządzeń. Nie wpisuje hasła ani kodu w AMC.
4. Po otrzymaniu poświadczenia host kończy tryb wykrywania albo przechodzi do zwykłego odtwarzania. Lokalny serwer nie może pozostawać aktywny bez potrzeby.
5. Sprawdzić zaporę Windows, sieć publiczną i prywatną, wiele kart sieciowych, VPN, izolację klientów Wi-Fi, dwie równoczesne próby oraz zmianę użytkownika.
6. Sprawdzić, czy otrzymane poświadczenie można bezpiecznie zachować po restarcie i czy daje tylko odtwarzanie, czy również funkcje konta potrzebne AMC08.

## Porównanie dróg

| Droga | Wygoda użytkownika | Główne ograniczenie | Decyzja przed produkcją |
| --- | --- | --- | --- |
| Kod na `spotify.com/pair` | bardzo dobra; działa także z innym urządzeniem | używa klienta Spotify Desktop, a nie tożsamości AMC | ocena zgodności, trwałości i zakresów |
| Wybór AMC w Spotify Connect | bardzo dobra; brak kodu i hasła | wymaga tej samej sieci, discovery i reguł zapory | prototyp oraz test bezpieczeństwa lokalnego |
| Oficjalne Web API AMC | dobre po skonfigurowaniu aplikacji | publiczny limit i proces akceptacji Spotify | zachować jako drogę deweloperską lub przyszłą oficjalną |
| Spotify Soloist | potencjalnie najlepsza droga oficjalna | obecnie Linux, klucz użytkownika i zakaz redystrybucji binariów | obserwować obsługę Windows i zasady dystrybucji |

## Docelowy interfejs profilu testowego, jeżeli eksperyment się powiedzie

1. W Menedżerze sesji użytkownik włącza `Spotify` i wybiera `Konfiguruj…`.
2. Otwiera się jedno okno `Połącz Spotify`, bez pól technicznych.
3. Okno proponuje tylko drogi zaliczone w eksperymencie: `Połącz kodem na stronie Spotify` i ewentualnie `Połącz przez aplikację Spotify na tym samym Wi-Fi`.
4. Adres oraz kod są zwykłymi polami możliwymi do odczytania i skopiowania. Przeglądarka nie otwiera się bez jawnego polecenia.
5. Po sukcesie AMC mówi jedno podsumowanie, na przykład: `Połączono Spotify. Odtwarzanie, wyszukiwanie i biblioteka są gotowe. Edycja playlist wymaga ponownej zgody`.
6. Gdy działa tylko odtwarzanie, AMC mówi to wprost i nie pokazuje pustej biblioteki jako awarii.
7. `Odłącz Spotify…` zatrzymuje wewnętrzne odtwarzanie, usuwa właściwe poświadczenia i nie pozostawia starego procesu, urządzenia sieciowego ani tokenu.
8. Spotify pozostaje wyłącznie w `AMC Test`, dopóki nie ma stabilnej, udokumentowanej drogi dostawcy, pełnych testów i osobnej decyzji o przeniesieniu do publicznego `AMC`.

## Pomoc i paleta

- `Ctrl+F1` opisuje wyłącznie drogę dostępną w danym wydaniu oraz wymóg konta Premium;
- `Ctrl+Shift+K` zawiera `Połącz Spotify`, `Stan Spotify` i `Odłącz Spotify`, gdy są właściwe dla bieżącego stanu;
- zwykły komunikat nie używa nazw `OAuth`, `Zeroconf`, `Spirc`, `scope`, `token`, `Client ID` ani nazw klas;
- raport techniczny może podać użyty wariant logowania i etap błędu, ale nie może zawierać tokenu, kodu urządzenia ani danych konta.

## Kryteria zaliczenia

1. Nowy użytkownik nie zakłada aplikacji deweloperskiej i nie wpisuje Client ID.
2. Hasło nigdy nie przechodzi przez AMC.
3. Po jednym procesie wiadomo dokładnie, które funkcje działają.
4. Ponowne uruchomienie nie wymaga logowania, dopóki Spotify nie unieważni dostępu.
5. Anulowanie i odłączenie nie pozwalają spóźnionej odpowiedzi ponownie zapisać konta.
6. Wykrywanie sieciowe, jeżeli zostanie wybrane, działa tylko przez czas niezbędny do połączenia i nie wystawia sekretów.
7. NVDA poprawnie odczytuje początkowy fokus, kod, adres, stan oczekiwania, sukces, błąd, Anuluj oraz ponowne otwarcie.
8. Testy obejmują brak Premium, brak sieci, blokadę zapory, wygaśnięcie kodu, zmianę konta oraz utratę ważności tokenu.
9. Funkcje playlist przechodzą osobne testy AMC08; samo odtwarzanie nie zalicza tworzenia ani modyfikowania playlist.
10. Publiczny profil kompilacji całkowicie pomija Spotify, łącznie z sesją, poleceniami, pomocą, paletą i składnikami zależnymi, bez usuwania prywatnych ustawień użytkownika profilu `AMC Test`.

## Poza zakresem

- instalowanie, uruchamianie, debugowanie albo utrzymywanie programu Spotify dla Eltena;
- kopiowanie kodu Eltena lub niepublicznego programu;
- Spotify Free bez reklam, pobieranie utworów, zapisywanie strumienia, modyfikowanie treści i obchodzenie ograniczeń regionalnych;
- deklarowanie partnerstwa lub oficjalnego wsparcia Spotify;
- publiczne wdrożenie przed wykonaniem eksperymentów, pełnej weryfikacji i osobną decyzją użytkownika.

## Źródła z dnia audytu

- https://github.com/librespot-org/librespot/blob/dev/oauth/src/lib.rs
- https://github.com/librespot-org/librespot/blob/dev/docs/device-authorization.md
- https://github.com/librespot-org/librespot/blob/dev/docs/authentication.md
- https://developer.spotify.com/documentation/web-api/concepts/quota-modes
- https://developer.spotify.com/terms
- https://developer.spotify.com/documentation/soloist/tutorials/getting-started
- https://github.com/dawidpieper/elten3
- https://elten.link/pl/forum/thread/28097

## Zasoby

- poziom A: wykonany audyt i plan eksperymentów;
- poziom B: test istniejącego kodu urządzenia na świadomie wskazanym koncie Premium;
- poziom C: prototyp discovery/Zeroconf, test integracyjny i test NVDA w `AMC Test`; wynik przygotowuje, lecz nie zastępuje osobnej decyzji wydawniczej;
- kompilacja i uruchomienie dopiero we wspólnej bramce uzgodnionej z użytkownikiem, gdy nie trwa nagrywanie.
