# AMC Test — diagnoza sekretu YouTube i wyboru Frontier

- Status: `Źródło i testy gotowe; brak nowej paczki oraz instalacji`.
- Data: 23 października 2026
- Commit źródła: `3e57b68656ee06c1742a3775bac3d810f792646f`
- Instalacja nadal używana przez użytkownika: `AMC Test — 23.10.2026, 16:30`
- Repozytorium: `D:\Projekty Codex\AMC - integracja wxPython`
- Instalacja testowa: `D:\Projekty Codex\AMC Python`

## Zachowanie widoczne dla użytkownika

Po przyszłej instalacji konto YouTube będzie dostępne tylko wtedy, gdy pakiet
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
- Brakujący sekret ma zostać zapisany jako jeden wiersz, bez cudzysłowów, w
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

## Ograniczenia i następny krok

Na komputerze nie znaleziono pobranego pliku JSON klienta ani lokalnego pliku
sekretu. Bez tej wartości nie zbudowano kandydata i nie zmieniono działającej
instalacji 16:30. Następny krok wymaga odczytania `Client secret` dokładnie z
tego samego klienta typu Aplikacja komputerowa w projekcie
`amc-test-youtube`, zapisania go we wskazanym pliku, a następnie pełnej budowy,
kontroli nagrań, atomowej instalacji i odbioru NVDA.

Nie wykonano publikacji, instalatora AMC Public ani wysłania do GitHuba.
