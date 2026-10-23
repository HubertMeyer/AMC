# AMC Test — diagnoza sekretu YouTube i wyboru Frontier

- Status: `Paczka zbudowana, zainstalowana i uruchomiona; oczekuje na ręczny odbiór YouTube oraz Frontier z NVDA`.
- Data: 23 października 2026
- Commit funkcji: `3e57b68656ee06c1742a3775bac3d810f792646f`
- Commit zbudowanego źródła: `b162b4d113acd3de7c6ad7370428e16d80a972f0`
- Zainstalowana wersja: `AMC Test — 23.10.2026, 19:28`
- Repozytorium: `D:\Projekty Codex\AMC - integracja wxPython`
- Instalacja testowa: `D:\Projekty Codex\AMC Python`

## Zachowanie widoczne dla użytkownika

Konto YouTube jest dostępne tylko wtedy, gdy pakiet
zawiera kompletną parę klienta Google. Wymiana kodu i późniejsze odświeżenie
wyślą wymagany sekret do oficjalnego punktu tokenów. Sam sekret nie pojawi się
w adresie logowania, wierszu poleceń, logu ani nazwie kontrolki. Po błędzie
przycisk logowania poda NVDA bezpieczny ostatni wynik, a ten sam wynik zostanie
zapisany w prywatnym `frontend.log` do dalszej diagnozy.

Frontier Smart po automatycznym albo ręcznym skanowaniu zawsze pokaże listę
wykrytych urządzeń, także gdy radio jest tylko jedno. Enter lub OK przejdzie do
PIN-u; Escape wróci do przycisku wyszukiwania bez pokazania pola PIN.

## Dokładne lokalizacje i konfiguracja

- Publiczny identyfikator testowego klienta pozostaje w ignorowanym pliku
  `wxlite\amc_wx_lite\youtube-oauth-client-id.txt`.
- Sekret zapisano jako jeden wiersz, bez cudzysłowów, w
  ignorowanym pliku
  `wxlite\amc_wx_lite\youtube-oauth-client-secret.txt`.
- Builder dołącza oba zasoby wyłącznie do AMC Test. Przy braku jednego z nich
  usuwa oba z paczki, aby nie wystawić pozornie działającego logowania.
- AMC Public nie odczytuje i nie dołącza żadnego z tych zasobów.

## Obsługa NVDA i fokus

- Wynik błędu logowania jest celowym tekstem użytkowym, nie surową odpowiedzią
  Google ani reprezentacją obiektu.
- Powrót fokusu na przycisk logowania zachowuje bezpieczny ostatni wynik w jego
  nazwie dostępnościowej.
- Lista Frontier ma nazwę `Wykryte urządzenia Frontier Smart`, pierwszy element
  jest zaznaczony, a anulowanie wraca do `Szukaj nowych urządzeń`.
- Pole PIN pozostaje ukryte do jawnego zatwierdzenia urządzenia.

## Rzeczywiste testy

- 12 ukierunkowanych testów Python: zaliczone.
- Fundament OAuth YouTube: 11/11 scenariuszy zaliczonych.
- Koordynator konta YouTube: 5/5 scenariuszy zaliczonych.
- Protokoły LiteHost: zestaw konta YouTube i zestaw Frontier Smart zaliczone;
  kompilacja LiteHosta zakończona powodzeniem.
- Pierwszy równoległy start dwóch testów Core zderzył się o wspólny plik
  `obj\Release`; ten sam zestaw uruchomiony sekwencyjnie przeszedł. Nie był to
  błąd źródła ani produktu.
- Po zapisaniu rzeczywistej pary klienta: 37/37 testów konfiguracji YouTube i
  pakowania zaliczone.
- Promocja instalacji: 30/30 testów launchera i aktualizatora zaliczone;
  projekty C# zbudowane bez ostrzeżeń i błędów.
- Pełna regresja wxPython: 2019 zaliczonych, 111 kontrolowanie pominiętych i
  11 zaliczonych podtestów w 143,34 s.
- Kandydat zawierał 1673 pliki. Kontrolowany start kandydata i zainstalowanej
  kopii zakończył się powodzeniem.

## Ograniczenia i następny krok

Google nie pozwala już pobrać ani ponownie wyświetlić wcześniej utworzonego
sekretu. Po potwierdzeniu użytkownika utworzono drugi sekret w tym samym
kliencie typu Aplikacja komputerowa i pobrano JSON. Identyfikator w JSON został
porównany z konfiguracją AMC, a sekret zapisano w ignorowanym pliku. Wartość
nie trafiła do Git, dokumentacji ani zwykłych logów.

Chrome ma niestandardowy katalog pobierania w synchronizowanym folderze
iCloud; pozostały tam dwie kopie pobranego JSON-u po dwóch próbach. Nie zostały
usunięte przed prawdziwym odbiorem, zgodnie z zasadą zachowania jedynej kopii
poświadczenia do czasu potwierdzenia działania. Po udanym logowaniu można je
usunąć, a stary sekret zakończony w konsoli Google na `xIO3` wyłączyć i usunąć
osobną, potwierdzoną czynnością.

Przed instalacją wykryto aktywne nagranie `Trochę Kultury TVP Info`. Budowę i
podmianę odłożono do jego naturalnego zakończenia o 19:25; plik został zapisany.
Następnie aktualizator atomowo zainstalował i uruchomił AMC Test 19:28 z
rewizji `b162b4d1`, identyfikator paczki `892705d2`. W instalacji potwierdzono
obecność kompletnej pary klienta YouTube. Publikacji nie wykonywano.

Następny krok to ręczne zalogowanie w nowej wersji. O powodzeniu rozstrzyga
stan `YouTube: zalogowano` w AMC, nie sama strona powrotu w przeglądarce.
Potem należy sprawdzić podgląd i zapis subskrypcji oraz ręcznie odebrać z NVDA
listę wyboru pojedynczego urządzenia Frontier, Enter, Escape i powrót fokusu.

Nie wykonano publikacji, instalatora AMC Public ani wysłania do GitHuba.
