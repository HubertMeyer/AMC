# NAME-001 — widoczna nazwa AMC Test

## Status

W trakcie.

## Cel

Prywatna, pełna wersja rozwijana z AMC Python ma być widoczna dla użytkownika
i NVDA jako `AMC Test`. Przyszły profil publiczny będzie widoczny jako `AMC`.

## Zakres bieżącej zmiany

- tytuł głównego okna i nazwa aplikacji wx: `AMC Test`;
- komunikaty uruchamiania, diagnostyki, bezpiecznego zamykania i aktualizacji:
  `AMC Test`;
- launcher i aktualizator rozpoznają jednocześnie okna `AMC Test` oraz starsze
  `AMC Python`, aby pierwsza aktualizacja była bezpieczna;
- techniczny katalog `D:\Projekty Codex\AMC Python`, identyfikator jednej
  instancji, nazwy plików i wartość `application` w manifeście pozostają teraz
  bez zmian. Ich przemianowanie wymaga osobnej migracji instalatora i skrótów.

## Kryteria akceptacji

- NVDA po wejściu do głównego okna mówi `AMC Test`, nie `AMC Python`.
- Druga instancja nie uruchamia się obok pierwszej także w czasie przejścia ze
  starej nazwy.
- Aktualizator potrafi bezpiecznie poprosić o zamknięcie zarówno starego, jak i
  nowego tytułu i nadal respektuje blokadę podczas nagrywania.
- Testy Pythona i .NET obejmują obecną oraz starszą nazwę.

## Prace i weryfikacja

- Data rozpoczęcia: 18 października 2026
- Data zakończenia:
- Zmienione pliki:
- Testy:
- Commit:
- Zainstalowana kompilacja:
