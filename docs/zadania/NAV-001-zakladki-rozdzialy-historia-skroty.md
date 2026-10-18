# NAV-001 — zakładki, rozdziały i historia nawigacji

## Status

Oczekuje.

## Cel

Ujednolicić klawiszową nawigację w otwartym odtwarzaczu i jednoznacznie
oddzielić cztery różne pojęcia: szybkie zakładki użytkownika, nazwane zakładki
użytkownika, rozdziały dostawcy lub pliku oraz historię nawigacji. Zachowanie ma
być wspólne dla sesji wszędzie tam, gdzie dany rodzaj danych rzeczywiście
istnieje, bez udawania rozdziałów lub zakładek w usłudze, która ich nie zwraca.

## Ustalony kontrakt skrótów

- `B` dodaje szybką, nienazwaną zakładkę w bieżącej pozycji.
- `Ctrl+Shift+B` w odtwarzaczu dodaje zakładkę z nazwą. Na liście pozostaje
  istniejącym wejściem do zakładek zaznaczonego materiału; kontekst ma być
  jawny w pomocy i palecie.
- `Shift+Page Up` i `Shift+Page Down` przechodzą do poprzedniej i następnej
  zakładki użytkownika, niezależnie od tego, czy zakładka ma nazwę.
- `Ctrl+Shift+Page Up` i `Ctrl+Shift+Page Down` przechodzą wyłącznie po
  nazwanych zakładkach utworzonych przez użytkownika. Nie są skrótami
  rozdziałów.
- `Ctrl+Shift+strzałka w lewo` i `Ctrl+Shift+strzałka w prawo` przechodzą po
  rzeczywistych rozdziałach dostarczonych przez plik, podcast albo usługę.
  Nazwana zakładka nie staje się rozdziałem tylko dlatego, że ma tekstową
  nazwę.
- `Alt+strzałka w lewo` i `Alt+strzałka w prawo` służą do cofania i ponawiania
  nawigacji po widokach lub elementach, zgodnie ze sprawdzonym zachowaniem
  historycznego AMC. Nie zmieniają pozycji czasu w materiale.
- Znaczenie `Alt+strzałka w górę` i `Alt+strzałka w dół` trzeba najpierw
  odtworzyć w historycznym AMC i w bieżącej mapie skrótów. Nie wolno przypisać
  im nowego działania na podstawie przypuszczenia ani kolidować z porządkiem
  sesji, list i urządzeń.

## Zakres sesji

- Pliki lokalne: szybkie i nazwane zakładki; rozdziały tylko wtedy, gdy plik
  albo parser je udostępnia.
- Podcasty i YouTube: rozdziały dostawcy, jeżeli są dostępne; zakładki
  użytkownika tylko po potwierdzeniu trwałej tożsamości materiału i pozycji.
- Spotify i inne sesje z wewnętrznym odtwarzaczem: zakładki mogą być
  dostępne, jeśli AMC zna stabilny identyfikator i pozycję; nie obiecujemy
  rozdziałów bez danych dostawcy.
- Radio i Time Shift: zakładki dotyczą osi bieżącego bufora lub nagrania
  wyłącznie wtedy, gdy można je później bezpiecznie odtworzyć. Nie zapisujemy
  pozornej zakładki prowadzącej do utraconego fragmentu.
- WiiM, Sonos i odtwarzacze zewnętrzne: brak funkcji ma zostać krótko
  oznajmiony, jeżeli urządzenie nie zwraca wystarczającej pozycji lub danych.

## Zasady mowy i dostępności

- Skok mówi krótko rodzaj, nazwę, jeśli istnieje, pozycję czasu i numer, na
  przykład „Zakładka, 12 minut 30 sekund, 2 z 5” albo „Rozdział: Wywiad,
  3 z 8”.
- Brak poprzedniego lub następnego elementu jest komunikatem użytkowym, bez
  sygnału systemowego i bez technicznych identyfikatorów.
- Fokus pozostaje w odtwarzaczu. Jeden gest powoduje jedną zmianę pozycji i
  jeden końcowy komunikat.
- Pomoc `Ctrl+F1`, menu odtwarzacza i paleta `Ctrl+Shift+K` opisują dokładnie
  te same znaczenia i warunki dostępności.

## Weryfikacja

1. Najpierw porównać działanie historycznego AMC i bieżącej implementacji,
   szczególnie `Alt+strzałka w górę/dół`, bez modyfikowania starego programu.
2. Rozdzielić w warstwie hosta filtry: wszystkie zakładki użytkownika, tylko
   nazwane zakładki i rozdziały dostawcy. Wpis mający jednocześnie bity
   zakładki i rozdziału może uczestniczyć w obu odpowiednich przebiegach, ale
   nie wolno zmieniać jego znaczenia ani usuwać niewłaściwego bitu.
3. Testy obejmują początek, środek i koniec listy, jeden element, brak danych,
   powtarzające się pozycje, zakładkę nazwaną i nienazwaną, rozdział dostawcy,
   zmianę materiału, ponowne otwarcie oraz odpowiedź spóźnioną.
4. Odbiór NVDA obejmuje wszystkie skróty, powrót fokusu, pomoc i paletę.

## Poza zakresem

- Automatyczne wykrywanie ciszy i tworzenie rozdziałów przez AMC.
- Edytor rozdziałów oraz eksport rozdziałów do pliku.
- Wymyślanie rozdziałów na podstawie nazwanych zakładek użytkownika.

## Prace i weryfikacja

- Data rozpoczęcia:
- Data zakończenia:
- Zmienione pliki:
- Testy:
- Commit:
- Zainstalowana kompilacja:
