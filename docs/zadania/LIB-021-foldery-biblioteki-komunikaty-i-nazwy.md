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

- RED: nowy test i18n dla obu komunikatów konfliktu zwrócił `AssertionError` przed dodaniem wzorców angielskich.
- GREEN: uruchomiono `python -m compileall -q wxlite/amc_wx_lite/i18n.py wxlite/tests/test_i18n.py wxlite/tests/test_library_folder_issue21.py`, a następnie celowany headless runner sześciu testów: 5 z `test_library_folder_issue21` i `test_library_folder_conflicts_translate_full_unicode_paths_both_ways`; wszystkie przeszły.
- Test dialogu używa rzeczywistych metod `finish()` → `apply_payload()` → `set_status()` → `Announcer`, a jedynie kontrolki wx są stubami. Sprawdza osobno ADD, REFRESH z wyborem `source-refresh`, FAIL, fokus listy/pustej listy oraz brak czwartego powiadomienia dla nieaktywnego ownera. Osobny test prowadzi rzeczywisty callback `LiteFrame._show_library_folders()` przez `runner.submit()` do prawdziwego `finish()`.
- Test i18n przełącza PL → EN → PL w `try`/`finally`, z nazwą i ścieżką UNC zawierającymi spacje i znaki Unicode. Wzorce dodano do `en_legacy.json`, a `template.json` odtworzono przez `python wxlite/tools/export_translation_template.py --output wxlite/amc_wx_lite/locales/template.json`.
- Regresja helpera rozróżniania obejmuje UNC i korzeń dysku z końcowymi separatorami; kod produkcyjny helpera nie wymagał zmiany.

## Materiał użytkowy

Nie dodano skrótów. Zmiana dotyczy istniejącego dialogu „Foldery Biblioteki” i jego komunikatów.

## Ograniczenia

Test headless potwierdza owner/gating i wywołanie callbacku powiadomienia `Announcer`, ale nie zastępuje natywnego `NotifyWinEvent` ani żywego odbioru przez NVDA. Nie uruchamiano Core smoke, GUI, AV ani instalatora. `wxlite/run_tests.py` nie zapewnił selektywnego uruchomienia wskazanych modułów w tej konfiguracji i pełny przebieg zakończył się `FAIL`; nie porównywano go z baseline, więc nie klasyfikujemy tych błędów jako istniejących. Odbiór binarny/GUI i instalator są świadomie odłożone do następnego etapu. Stary instalator diagnostyczny `9739fe3` nie zawiera tej zmiany.

## Źródła

- GitHub issue #21, Hubert Meyer, 2026-11-17.
- `wxlite/amc_wx_lite/gui.py`, `library_db.py`.
- `src/AccessibleMediaController.Core/LocalMedia/LocalFolderLibraryManager.cs`.

## Status

Zmiana źródeł oraz sześć testów celowanych zaliczone; bez Core smoke i live NVDA.
