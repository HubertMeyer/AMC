# STR-001 — laboratorium TIDAL i Apple Music

- Status: `Oczekuje`
- Utworzono: 18 października 2026
- Obszar: usługi strumieniowe i profil testowy
- Polecenie uruchamiające: `Uruchom zadanie STR-001`

## Cel

Zbadać oficjalne możliwości TIDAL i Apple Music bez obiecywania użytkownikom
funkcji, których dostawcy nie pozwalają niezależnemu klientowi wykonać.
Najpierw powstaje raport i mały eksperyment w profilu testowym; dopiero potem
może zapaść osobna decyzja o wdrożeniu.

## TIDAL

- Ponownie sprawdzić aktualne Web API, SDK oraz warunki deweloperskie.
- Pełne odtwarzanie wolno realizować wyłącznie przez oficjalny, niezmieniony
  moduł Player udostępniony przez TIDAL; katalog, Biblioteka i playlisty nie są
  automatycznie dowodem możliwości odtwarzania.
- Zachować istniejące ustalenia i nie powtarzać identycznej próby logowania ani
  pytania do TIDAL bez nowego dowodu.

## Apple Music

- Sprawdzić Apple Music API, MusicKit on the Web i ewentualny natywny klient
  macOS oddzielnie.
- Apple wymaga identyfikatora MusicKit i podpisanego tokenu deweloperskiego;
  dane Biblioteki wymagają także zgody użytkownika i Music User Token.
- Odtwarzanie na Windows należy badać przez oficjalne MusicKit on the Web, a
  nie przez odtwarzanie przechwyconych adresów multimediów. Natywny macOS może
  korzystać z MusicKit dla Swift, ale jest to osobny adapter platformy.

## Organizacja pracy

- Badanie może zostać wykonane w osobnym zadaniu Codex albo przez Hermesa,
  kiedy użytkownik jawnie je uruchomi. Raport musi wrócić do tego pliku i
  zawierać źródła, datę, ograniczenia konta oraz rozdzielenie faktów od
  hipotez.
- Żadne zewnętrzne zadanie nie otrzymuje tokenów, danych kont ani prywatnego
  profilu AMC. Próby logowania i odtwarzania wykonuje się dopiero lokalnie, po
  osobnej zgodzie i w odizolowanym profilu testowym.
- TIDAL i Apple Music pozostają poza publicznym profilem do czasu osobnego
  odbioru prawnego, funkcjonalnego i dostępnościowego.

## Kryteria zakończenia badania

1. Macierz: katalog, wyszukiwanie, Biblioteka, playlisty, historia,
   odtwarzanie, sterowanie, pobieranie i ograniczenia terytorialne.
2. Opis oficjalnego logowania bez sekretu osadzonego w publicznym kliencie.
3. Prototyp nie zapisuje ani nie odtwarza chronionych adresów poza oficjalnym
   SDK.
4. Decyzja: odrzucić, pozostawić w laboratorium albo przygotować osobny plan
   wdrożenia testowego.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data zakończenia:
- Wersje API i warunków:
- Wynik TIDAL:
- Wynik Apple Music:
- Rekomendacja:

