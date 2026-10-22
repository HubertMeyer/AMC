# POD-002 — jednoetapowy import linków YouTube pod Ctrl+N

## Status

W trakcie — zachowanie jest zweryfikowane automatycznie, zainstalowane i
uruchomione w AMC Test 2026-10-22. Pozostaje ręczny odbiór NVDA z prawdziwym
publicznym adresem YouTube.

## Zachowanie widoczne dla użytkownika

W sesji **Podcasty i YouTube** `Ctrl+N` otwiera natywny formularz dodawania
źródła. Po wklejeniu publicznego adresu kanału, playlisty, filmu albo
transmisji jeden Enter uruchamia przycisk **Sprawdź i dodaj**. AMC najpierw
sprawdza adres, a po powodzeniu zapisuje źródło w Bibliotece. Nie trzeba
wykonywać osobno operacji „Sprawdź” i „Dodaj”.

Podczas operacji przycisk jest zablokowany, aby drugi Enter nie uruchomił
duplikatu. Błąd pozostawia formularz otwarty do poprawienia adresu. Sukces jest
potwierdzany komunikatem o dodaniu i zapisaniu źródła.

## Uzasadnienie i decyzje

- Zakończone 2026-10-22 zadanie historycznego interfejsu WPF potwierdziło, że
  tamten formularz wymagał ujednolicenia do jednego Entera.
- Bieżący AMC Test w wxPython już realizował docelowy jednoetapowy przebieg.
  Nie kopiowano kodu z archiwalnej aplikacji WPF; sprawdzono i zachowano
  implementację głównej wersji AMC Test.
- Polecenie, skrót i menu pozostają filtrowane przez sesję. `Ctrl+N` w innych
  sesjach może oznaczać inną, kontekstową czynność.

## Testy i wynik

- Testy przebiegu dodawania źródła znajdują się w
  `wxlite/tests/test_podcast_add.py` i były częścią pełnej regresji:
  **1978 zaliczonych, 110 pominiętych i 11 podtestów zaliczonych**.
- Testy launchera i aktualizatora: **30 z 30 zaliczonych**.
- Pełna kompilacja Release: 0 ostrzeżeń i 0 błędów.
- Integralność zainstalowanej kopii zwróciła kod 0. Kontrolowany start
  interfejsu i hosta został zaliczony.

## Znane ograniczenia

- Automatyczny test nie zastępuje ręcznego sprawdzenia mowy NVDA, fokusu,
  anulowania i powrotu fokusu po błędzie.
- Rzeczywisty import zależy od dostępności publicznego materiału i odpowiedzi
  YouTube oraz `yt-dlp`. Materiał prywatny albo wymagający logowania nie jest
  traktowany jako publiczne źródło.

## Wersja i commit

- Jednoetapowy przebieg istniał już w bieżącym AMC Test; zadanie z 2026-10-22
  potwierdziło zgodność zamiast przenosić zmianę z archiwalnego WPF.
- Zainstalowany kandydat zawierający zweryfikowane zachowanie:
  `2026.10.22-6ce22410bb80ac867504d15d17d890e9774d929e-f3e80d2d`,
  1670 plików.
- Stała lokalizacja: `D:\Projekty Codex\AMC Python`.
- Potwierdzony tytuł: `AMC Test — 22.10.2026, 22:48`.
- AMC Public, instalator i publikacja: bez zmian.
