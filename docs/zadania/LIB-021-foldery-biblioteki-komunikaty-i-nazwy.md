# LIB-021 — Foldery Biblioteki: komunikaty i jednoznaczne nazwy

## Cel

Naprawić zgłoszenie #21 Huberta: po dodaniu, odświeżeniu albo odmowie Folderu Biblioteki wynik ma być pojedynczo ogłoszony przez aktywny modalny dialog. W widoku korzeni lokalnych foldery o identycznej nazwie mają być rozróżnialne bez zmiany ich ścieżek, ID ani danych na dysku.

## Przyczyna

`LibraryFoldersDialog.finish()` i `fail()` aktualizowały tylko widoczny status oraz fokus listy. Nie wywoływały live regionu. Komunikat od hosta przy konflikcie zawierał wyłącznie nazwę istniejącego źródła. Korzenie widoku lokalnego wyświetlały sam `display_name`, więc różne ścieżki kończące się tą samą nazwą były nierozróżnialne.

## Zmiana

- Dialog ma własny `Announcer` oparty o jego `status`; `Announcer` ustala owner jako top-level parent pola statusu, więc przy aktywnym modalu ogłasza właśnie dialog, a nie nieaktywną ramkę.
- `finish()` i `fail()` przekazują wynik do tego announcera raz; fokus po operacji pozostaje zgodny z dotychczasowym zachowaniem.
- Konflikt hosta podaje także pełną ścieżkę istniejącego Folderu Biblioteki.
- Tylko powtarzające się bez rozróżnienia wielkości liter nazwy korzeni dostają dopisek rodzica, np. `cd (X:\a)` i `CD (X:\b)`; unikalne nazwy pozostają krótkie.

## Akceptacja

- Sukces dodania/odświeżenia i błąd są pojedynczo wysyłane do live regionu aktywnego dialogu.
- Nieaktywny owner blokuje natywne powiadomienie zgodnie z istniejącą bramką `Announcer`; modalny status ma owner dialogu.
- Odmowa zagnieżdżonego/nakładającego się źródła podaje ścieżkę konfliktującego źródła.
- Rozróżnienie jest wyłącznie prezentacyjne; ID, ścieżki, import i zapis nie zmieniają się.

## Testy RED → GREEN

- Python: `wxlite/tests/test_library_folder_issue21.py` sprawdza case-insensitive rozróżnienie nazw i faktyczny łańcuch `finish`/`fail` → `set_status` → `Announcer`, wraz z ownerem aktywnym i nieaktywnym.
- Core smoke test sprawdza, że odmowa dodania zagnieżdżonego folderu zawiera ścieżkę istniejącego źródła.

## Materiał użytkowy

Nie dodano skrótów. Zmiana dotyczy istniejącego dialogu „Foldery Biblioteki” i jego komunikatów.

## Ograniczenia

Test headless potwierdza owner/gating oraz wywołanie `NotifyWinEvent`, ale nie zastępuje żywego odbioru przez NVDA. Odbiór binarny/GUI i instalator są świadomie odłożone do następnego etapu. Stary instalator diagnostyczny `9739fe3` nie zawiera tej zmiany.

## Źródła

- GitHub issue #21, Hubert Meyer, 2026-11-17.
- `wxlite/amc_wx_lite/gui.py`, `library_db.py`.
- `src/AccessibleMediaController.Core/LocalMedia/LocalFolderLibraryManager.cs`.

## Status

Zmiana źródeł oraz testy celowane zaliczone; bez live NVDA.
