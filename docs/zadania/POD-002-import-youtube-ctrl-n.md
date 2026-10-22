# POD-002 — jednoetapowy import linków YouTube pod Ctrl+N

## Status

Poprawka w źródłach, zbudowana i zweryfikowana 2026-10-22; **niezainstalowana**.
Ręczny odbiór z prawdziwym adresem ujawnił błąd w zainstalowanym AMC Test:
`https://www.youtube.com/@WieniawskiSociety` kończył się komunikatem
„Nie można dodać źródła: Adres YouTube nie prowadzi do publicznego kanału ani
playlisty.” Zainstalowana wersja `AMC Test — 22.10.2026, 22:48` nadal zawiera
ten błąd, dopóki użytkownik osobno nie zleci przygotowania i instalacji nowej
kompilacji.

## Zachowanie widoczne dla użytkownika

W sesji **Podcasty i YouTube** `Ctrl+N` otwiera natywny formularz dodawania
źródła. Po wklejeniu publicznego adresu kanału, playlisty, filmu albo
transmisji jeden Enter uruchamia przycisk **Sprawdź i dodaj**. AMC najpierw
sprawdza adres, a po powodzeniu zapisuje źródło w Bibliotece. Nie trzeba
wykonywać osobno operacji „Sprawdź” i „Dodaj”.

Obsługiwany jest również zwykły adres kanału z uchwytem, na przykład
`https://www.youtube.com/@NazwaKanału`. Pomoc w formularzu podaje ten format
wprost.

Podczas operacji przycisk jest zablokowany, aby drugi Enter nie uruchomił
duplikatu. Błąd pozostawia formularz otwarty do poprawienia adresu. Sukces jest
potwierdzany komunikatem o dodaniu i zapisaniu źródła.

## Uzasadnienie i decyzje

- Zakończone 2026-10-22 zadanie historycznego interfejsu WPF potwierdziło, że
  tamten formularz wymagał ujednolicenia do jednego Entera.
- Bieżący AMC Test w wxPython już realizował docelowy jednoetapowy przebieg.
  Ręczny odbiór wykazał jednak, że samo okno działało, lecz LiteHost odrzucał
  poprawny kanał przed uruchomieniem `yt-dlp`.
- **Korekta użytkownika z 2026-10-22 zastępuje wcześniejszą ocenę, że
  zainstalowany przebieg jest zweryfikowany i czeka tylko na odbiór.** Pierwsza
  normalizacja poprawnie tworzyła adres
  `https://www.youtube.com/%40WieniawskiSociety/videos`. `FetchAsync`
  normalizował go ponownie, ale analizował nieodkodowany segment `%40…`, nie
  rozpoznawał początku `@` i zgłaszał błąd jeszcze przed wywołaniem `yt-dlp`.
- Segmenty ścieżki są teraz odkodowywane przed ścisłą walidacją. Normalizacja
  jest idempotentna: adres użytkownika i jego stabilna postać `%40…/videos`
  prowadzą do tego samego kanału. Odkodowane ukośniki i inne znaki spoza
  bezpiecznego alfabetu nadal są odrzucane.
- Polecenie, skrót i menu pozostają filtrowane przez sesję. `Ctrl+N` w innych
  sesjach może oznaczać inną, kontekstową czynność.

## Testy i wynik

- Dodano deterministyczną regresję dokładnego adresu
  `https://www.youtube.com/@WieniawskiSociety` oraz ponownej normalizacji
  `https://www.youtube.com/%40WieniawskiSociety/videos`.
- Ukierunkowana kompilacja testów C# Release: **0 ostrzeżeń, 0 błędów**.
- Ukierunkowany test `--youtube-collection-normalization`: **zaliczony**.
- Kompilacja LiteHost Release używanego przez AMC Test: **0 ostrzeżeń,
  0 błędów**.
- Testy formularza, skrótu, menu, klienta hosta i lokalnego RSS:
  **6 zaliczonych, 0 nieudanych, 1 prawidłowo pominięty test sieciowy**.
- Jawnie włączony test sieciowy rzeczywistego LiteHosta z tymczasową bazą:
  **2 zaliczone, 0 nieudanych, 0 pominiętych**. Kanał został rozpoznany jako
  `UCpFEKtbJxKnsOcraylnuNsA`, miał nazwę „Wieniawski Society - Videos” i został
  zapisany pod stabilnym adresem `%40…/videos`.
- Osobne odczytowe uruchomienie zarządzanego składnika `yt-dlp` na stabilnym
  adresie zwróciło materiał kanału. Potwierdza to, że wcześniejszy błąd
  występował przed uruchomieniem `yt-dlp`, a nie w odpowiedzi YouTube.

## Znane ograniczenia

- Poprawiona kompilacja nie została jeszcze zainstalowana ani odebrana ręcznie
  z NVDA. Dotychczasowy ręczny odbiór dotyczył wersji z błędem i jest dowodem
  regresji, nie zaliczeniem poprawki.
- Rzeczywisty import zależy od dostępności publicznego materiału i odpowiedzi
  YouTube oraz `yt-dlp`. Materiał prywatny albo wymagający logowania nie jest
  traktowany jako publiczne źródło.

## Wersja i commit

- Bazowy commit roboczego repozytorium podczas poprawki:
  `b94805a51dda69ec6bf52d5d776fa6d0693aa188`.
- Commit poprawki źródeł i testów:
  `7f4a7d156cc05d90005f78d613c224a21d663160`.
- Zainstalowany kandydat **niezawierający jeszcze tej poprawki**:
  `2026.10.22-6ce22410bb80ac867504d15d17d890e9774d929e-f3e80d2d`,
  1670 plików.
- Stała lokalizacja: `D:\Projekty Codex\AMC Python`.
- Potwierdzony tytuł: `AMC Test — 22.10.2026, 22:48`.
- AMC Public, instalator i publikacja: bez zmian.

## Materiał do dokumentacji użytkownika

W sesji **Podcasty i YouTube** naciśnij `Ctrl+N`, wpisz pełny publiczny adres,
na przykład `https://www.youtube.com/@NazwaKanału`, i naciśnij Enter na
przycisku **Sprawdź i dodaj**. AMC sam rozpoznaje kanał, uruchamia `yt-dlp`,
pobiera najwyżej 100 najnowszych materiałów i zapisuje kanał w Bibliotece.
Podczas operacji drugi Enter nie uruchamia duplikatu. Po powodzeniu NVDA podaje
rodzaj źródła, nazwę i liczbę pozycji. Błąd pozostawia formularz do poprawienia.
Funkcja działa bez logowania i bez cookies; kanały prywatne lub wymagające
logowania nie są obsługiwane.

## Roboczy wpis do changelogu

- Naprawiono import kanałów YouTube z adresów zawierających uchwyt `@` pod
  `Ctrl+N`. Stabilny, zakodowany adres `%40…/videos` może być ponownie
  sprawdzony bez błędnego odrzucenia kanału przed uruchomieniem `yt-dlp`.
