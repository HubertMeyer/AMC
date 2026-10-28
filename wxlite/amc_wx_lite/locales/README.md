# Katalogi tłumaczeń AMC wxPython

Plik `template.json` jest szablonem nowego języka. Klucze są trwałe i nie są
tekstami pokazywanymi użytkownikowi. Nie wolno zmieniać nazw kluczy ani
placeholderów zapisanych w nawiasach klamrowych.

Pełny szablon wraz z bieżącą listą poleceń tworzy:

```powershell
python wxlite\tools\export_translation_template.py --output wxlite\amc_wx_lite\locales\template.json
```

Bez `--output` narzędzie wypisuje JSON na standardowe wyjście. Sekcja `ui`
zawiera stabilne klucze nowych powierzchni, `commands` stabilne identyfikatory
poleceń, a `legacyUi` i `legacyTemplates` pełny zinwentaryzowany interfejs
wxPython zachowany podczas migracji. Wartości profilu, kont, ścieżki, stacje,
tytuły i urządzenia nie są częścią katalogu.

Tłumacz powinien wypełnić wszystkie wartości, zachować UTF-8, nie zmieniać
placeholderów `{argN}` i uruchomić test `test_i18n.py`. Dodanie kompletnego
katalogu wymaga też jawnego dopisania jego kodu do `SUPPORTED_LANGUAGES` oraz
użytkowej nazwy do wyboru języka. `en_legacy.json` jest angielskim katalogiem
zgodności; jego metadane zapisują zakres i źródło roboczego tłumaczenia.
