# AMC Test — instalacja zbiorcza 23.10.2026, 11:24

## Status

Zainstalowano i uruchomiono wyłącznie profil `test` w stałym katalogu
`D:\Projekty Codex\AMC Python`. AMC Public, jego instalator i GitHub pozostały
bez zmian. Ręczny odbiór nowych funkcji z NVDA pozostaje do wykonania.

## Zawartość użytkowa

- poprawione dodawanie źródeł YouTube przez `Ctrl+N`, ze stabilnym fokusem i
  bez ujawniania technicznych okien procesów;
- gotowy interfejs konta Google/YouTube i bezpieczny OAuth; prawdziwe logowanie
  wymaga jeszcze publicznego identyfikatora klienta Google dla AMC;
- czwarta korekta wykrywania i konfiguracji Frontier Smart;
- pełne, stronicowane odświeżanie bardzo dużych kanałów podcastów;
- pełne odświeżanie zapisanych podcastów i odcinków Spotify oraz uczciwe
  rozdziały Spotify wyłącznie ze znaczników czasu obecnych w opisie;
- `Odtwarzaj losowo (R)` w odtwarzaczu Plików, Podcastów i Spotify, także w
  menu kontekstowym, menu Odtwarzanie, palecie poleceń i pomocy;
- scalone poprawki stabilności oraz dokumentacja rozróżniająca kontrolowaną
  promocję od awarii okna.

Apple Music nie jest częścią tej paczki wxPython. Historyczny prototyp WPF nie
jest źródłem bieżącego AMC Test.

## Przebieg instalacji i bezpieczeństwo

- Pierwsza próba została zatrzymana przed podmianą, ponieważ AMC wykrył aktywne
  nagranie `Poznań`, rozpoczęte o 11:06:14. Nie wymuszano zakończenia procesu.
- Po zakończeniu nagrania potwierdzono brak działających składników starej
  instalacji i zastosowano wcześniej zweryfikowanego kandydata.
- Pierwsza próba testu startu stałej instalacji była przedwczesna: pomocniczy
  proces atomowego aktualizatora nadal pracował. Po jego naturalnym zakończeniu
  integralność i kontrolowany start zostały powtórzone z wynikiem pozytywnym.
- Widoczne okno uruchomiono ze stałego katalogu D. Utworzono skróty `AMC Test`
  na pulpicie i w menu Start; istniejących skrótów `AMC` nie zmieniono.

## Testy i rzeczywiste wyniki

- testy nowego losowania: 6 zaliczonych;
- rozszerzona regresja poleceń i transportu: 205 zaliczonych;
- regresja menu kontekstowego: 86 zaliczonych;
- poprawione przypadki pełnej kopii, atrap GUI i Radia: 8 zaliczonych;
- pełna regresja wxPython przed commitem i ponownie podczas promocji:
  **2010 zaliczonych, 111 pominiętych, 11 podtestów zaliczonych**;
- testy launchera i aktualizatora: **30 zaliczonych**;
- kompilacje .NET Release: 0 ostrzeżeń i 0 błędów w raportowanych etapach;
- integralność 1671 plików kandydata oraz zainstalowanej kopii: zaliczona;
- kontrolowany start interfejsu i hosta z kandydata i po instalacji: zaliczony;
- widoczne uruchomienie: `AMC Test — 23.10.2026, 11:24`, proces interfejsu
  `D:\Projekty Codex\AMC Python\runtime\python.exe`.

## Wersja i commit

- rewizja źródłowa: `12747221ba764681b15e93257b14f9d6d712a6b8`;
- identyfikator zawartości: `95c15869`;
- etykieta:
  `2026.10.23-12747221ba764681b15e93257b14f9d6d712a6b8-95c15869`;
- czas utworzenia paczki: 23.10.2026, 11:24:17 czasu polskiego;
- profil manifestu: `test`;
- stała instalacja: `D:\Projekty Codex\AMC Python\AMC.exe`.

## Znane ograniczenia i dalszy odbiór

- Nowe funkcje wymagają ręcznego przejścia z NVDA na prawdziwych danych i,
  odpowiednio, prawdziwym koncie Spotify, urządzeniu Frontier Smart i koncie
  Google/YouTube.
- Do logowania Google/YouTube potrzebna jest konfiguracja publicznego klienta
  OAuth AMC; nie należy przekazywać do repozytorium hasła, tokenu użytkownika
  ani prywatnego Apple ID.
- Apple Music pozostaje osobnym zadaniem diagnostyczno-implementacyjnym.

