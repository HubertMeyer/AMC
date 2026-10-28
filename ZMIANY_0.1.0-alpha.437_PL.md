# AMC Test 0.1.0-alpha.437 — szkic zmian i odbioru

To jest roboczy opis wydania testowego do sprawdzenia przez użytkownika.

## Najważniejsze zmiany

- SoundCloud: `Ctrl+F` uwzględnia zweryfikowane polskie podcasty Freta,
  Dominikanie Służew i Dominikanie Rzeszów. Te same wyniki są dostępne w
  globalnym wyszukiwaniu `Ctrl+Shift+F`, bez ujawniania technicznych
  identyfikatorów w etykietach NVDA.
- YouTube: poprawiono obsługę konta, odświeżania tokenu, atomowej synchronizacji
  subskrypcji i playlist oraz zachowanie polskich danych użytkowych. Testowy
  profil zachowuje uproszczone logowanie sprawdzone wcześniej przez
  użytkownika. Przygotowanie wariantu publicznego nie uruchamia jeszcze
  publicznego logowania ani żadnego zdalnego brokera.
- Ustawienia: karty mają kolejność `Ogólne`, `Radio i nagrywanie`, `Podcasty i
  YouTube`, `Dostępność i komunikaty`, `Klawiatura`, `Aktualizacje`,
  `Integracja z Windows`. Ustawienia zapisu Radia i Podcastów znajdują się na
  początku odpowiednich kart, a własne komunikaty są ostatnią sekcją karty
  dostępności.
- Rozpoznane utwory: historia jest związana z właściwą sesją, zachowuje
  poprawny powrót po `Escape`, a kopiowanie tytułu i wykonawcy ma krótkie
  polskie potwierdzenia.
- Edycja klipów: AMC czeka na rzeczywiste zwolnienie dekodera pliku przed
  wycinaniem, co usuwa wyścig powodujący sporadyczne niedokończenie operacji.
- Aktualizator: po powodzeniu nie pokazuje zbędnego okna z przyciskiem `OK`,
  próbuje przywrócić AMC na pierwszy plan i zachowuje najwyżej dwie najnowsze
  kopie ratunkowe aktualizacji.

## Sposób odbioru

1. W zainstalowanym AMC Test wybierz `Pomoc` i `Sprawdź aktualizację AMC…`.
2. Sprawdź opis wersji i uruchom aktualizację ręcznie.
3. Po instalacji AMC powinien uruchomić się bez dodatkowego komunikatu o
   powodzeniu i spróbować pokazać główne okno na pierwszym planie.
4. Sprawdź z NVDA kolejność kart ustawień, polskie wyniki SoundCloud,
   wyszukiwanie globalne oraz powrót z historii rozpoznanych utworów.

## Ważne ograniczenia

- To wydanie kanału Test. Nie jest stabilnym wydaniem AMC Public.
- Pakiet językowy i pełna wielojęzyczność nie należą do tego wydania; zostaną
  przygotowane i opublikowane w następnym etapie.
- Codex nie instaluje tej aktualizacji lokalnie. Ręczne uruchomienie
  aktualizacji pozostaje po stronie użytkownika.
