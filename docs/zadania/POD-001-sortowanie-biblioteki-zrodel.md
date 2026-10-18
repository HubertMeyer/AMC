# POD-001 — sortowanie Biblioteki podcastów i kanałów

## Status

Oczekuje.

## Stan obecny

Zbiorcza Biblioteka podcastów, kanałów YouTube, playlist YouTube i pozycji
`Media internetowe` jest czytana według trwałego pola `ordinal`. Jest to
kolejność własna odziedziczona z bazy, a nie porządek alfabetyczny ani według
daty dodania. Menu sortowania `Alt+1`, `Alt+2`, `Alt+3` działa obecnie tylko w
Skrzynce podcastów, nie na głównej liście źródeł.

## Cel

Dać użytkownikowi jawny wybór porządku głównej Biblioteki bez zmiany danych
współdzielonego profilu przez interfejs Python.

## Wstępna propozycja

- `Alt+1` — ostatnio dodane na początku;
- `Alt+2` — alfabetycznie;
- `Alt+3` — kolejność własna z bazy;
- wybrany tryb jest zapisany w prywatnych ustawieniach AMC Test;
- zmiana sortowania zachowuje zaznaczenie według stabilnego identyfikatora;
- pomoc `Ctrl+F1`, menu i paleta `Ctrl+Shift+K` opisują te same polecenia;
- tryb alfabetyczny używa polskiego porównania nazw, nie technicznych ID;
- sortowanie nie miesza podcastów, kanałów i `Media internetowe` z odcinkami.

Skróty oraz domyślny tryb wymagają potwierdzenia przed wdrożeniem. Zadanie nie
jest częścią poprawki `SEARCH-001` i nie powinno opóźniać widocznego zaznaczenia
elementu właśnie dodanego z wyszukiwarki.

## Kryteria akceptacji

- trzy tryby zwracają przewidywalną kolejność na tej samej bibliotece;
- nowe źródło jest widoczne i zaznaczone po dodaniu w każdym trybie;
- ponowne uruchomienie zachowuje wybór sortowania;
- NVDA mówi nazwę trybu, pozycję elementu i użytkową nazwę źródła;
- testy nie zapisują bezpośrednio do `podcasts.db` z warstwy Python.

## Prace i weryfikacja

- Data rozpoczęcia:
- Data zakończenia:
- Zmienione pliki:
- Testy:
- Commit:
- Zainstalowana kompilacja:
