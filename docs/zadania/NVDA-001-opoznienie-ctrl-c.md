# NVDA-001 — opóźnienie Ctrl+C z NVDAExtensionGlobalPlugin

- Status: `W trakcie — poprawka zastosowana, NVDA zrestartowane; czeka na ręczny odbiór mowy i schowka`
- Utworzono: 17 października 2026
- Obszar: NVDA, schowek i skróty AMC
- Polecenie uruchamiające: `Uruchom zadanie NVDA-001`

## Cel

Usunąć zauważalne opóźnienie reakcji na `Ctrl+C` w AMC podczas pracy z
NVDAExtensionGlobalPlugin, bez przywracania angielskiego komunikatu `copy`, bez
podwójnego komunikatu i bez pogorszenia działania kopiowania w innych
aplikacjach.

## Potwierdzona diagnoza

- Z uruchomionym NVDA bez dodatków opóźnienie znika całkowicie.
- Po ponownym włączeniu NVDAExtensionGlobalPlugin opóźnienie wraca. Użytkownik
  potwierdził ten związek w bezpośredniej próbie 17 października 2026 r.
- Dodatek przechwytuje `Ctrl+C` w pliku
  `%APPDATA%\nvda\addons\NVDAExtensionGlobalPlugin\globalPlugins\NVDAExtensionGlobalPlugin\clipboardCommandAnnouncement\__init__.py`.
- Zaobserwowany kod odkłada przekazanie gestu przez
  `delayScriptTaskWithDelay(80, callback)`, następnie wywołuje
  `gesture.send()`, czeka przez `time.sleep(0.1)` i dopiero sprawdza zmianę
  schowka oraz przygotowuje komunikat. Łącznie daje to zauważalną zwłokę.
- `Ctrl+Shift+C` w AMC reaguje szybciej, ponieważ nie przechodzi przez dokładnie
  ten sam mechanizm dodatku.
- AMC nie ma już własnej sztucznej pauzy przed kopiowaniem. Zmiana
  `02fd6da8` (`Przyspiesz kopiowanie nazwy`) usunęła wcześniejsze odroczenie
  180 ms i przywróciła synchroniczny zapis do schowka. Zestaw 96 testów
  skrótów, wyszukiwania i dialogów przeszedł po tej zmianie. Próba użytkownika
  wykazała jednak, że odczuwalna zwłoka pozostaje wyłącznie z aktywnym
  NVDAExtensionGlobalPlugin.

## Zakres

- Ustalić bezpieczny sposób współpracy dodatku z AMC.
- Preferować wyjątek dla AMC albo nieblokujące obserwowanie schowka, które nie
  wstrzymuje przekazania `Ctrl+C` do aplikacji.
- Rozpoznać AMC na podstawie stabilnej tożsamości aplikacji, a nie samego tytułu
  okna. Instalacja AMC Python używa własnego runtime'u, dlatego nie wolno bez
  sprawdzenia zakładać, że ogólny proces `python.exe` jednoznacznie oznacza AMC.
- Zachować natychmiastowy polski komunikat AMC i brak angielskiego `copy`.
- Sprawdzić zachowanie dodatku w co najmniej jednej zwykłej aplikacji, aby
  wyjątek dla AMC nie wyłączył globalnej funkcji kopiowania gdzie indziej.

## Poza zakresem

- Ponowne dodawanie opóźnienia po stronie AMC.
- Wyłączanie całego NVDAExtensionGlobalPlugin jako rozwiązanie docelowe.
- Zmiana pozostałych funkcji dodatku bez związku ze schowkiem.
- Publikacja AMC albo dodatku bez osobnej, aktualnej zgody użytkownika.

## Kryteria akceptacji

1. Z włączonym NVDAExtensionGlobalPlugin `Ctrl+C` w AMC reaguje bez zauważalnej
   sztucznej pauzy i nie jest wolniejszy w sposób odczuwalny od
   `Ctrl+Shift+C`.
2. NVDA wypowiada dokładnie jeden krótki polski komunikat AMC i nie mówi
   angielskiego `copy`.
3. Do schowka trafia prawidłowa nazwa, również przy szybkim powtarzaniu skrótu.
4. Zachowanie jest poprawne po ponownym uruchomieniu AMC i NVDA.
5. NVDA uruchomione bez dodatków nadal działa prawidłowo z AMC.
6. Reprezentatywne kopiowanie w innej aplikacji zachowuje zamierzone działanie
   NVDAExtensionGlobalPlugin.
7. Próba nie wymaga globalnego wyłączenia dodatku ani opóźniania skrótu w AMC.

## Bezpieczeństwo wykonania

- Nie edytuj na ślepo plików aktywnego dodatku w `%APPDATA%`. Najpierw ustal
  źródło, sposób pakowania, możliwość wycofania zmiany i metodę testu.
- Przed restartem NVDA albo AMC sprawdź, czy AMC nie nagrywa. Jeżeli nie można
  tego potwierdzić, zapytaj użytkownika.
- Zachowaj kopię albo odtwarzalny pakiet poprzedniej wersji dodatku przed próbą
  instalacji zmienionej wersji.

## Wynik wykonania

- Data zastosowania: 19 października 2026, po potwierdzonym zakończeniu
  nagrywania.
- Wynik: lokalna poprawka jest obecna dokładnie raz, oryginał zachowany obok
  pliku, a NVDA uruchomiono ponownie jego własnym przełącznikiem `-r`.
- Zmieniony plik instalacji dodatku:
  `%APPDATA%\nvda\addons\NVDAExtensionGlobalPlugin\globalPlugins\NVDAExtensionGlobalPlugin\clipboardCommandAnnouncement\__init__.py`.
- Kopia do wycofania:
  `__init__.py.amc-original-f4ecf28d9df2` w tym samym folderze.
- Commit narzędzia: `1169e6aa17414c0d30c7cf4d3c40e530463ea317`;
  poprawka zgodności CRLF: `df2f8fe6`.
- Pozostałe ograniczenie: wynik mowy, zawartość schowka i zachowanie zwykłej
  aplikacji muszą zostać potwierdzone ręcznie przez użytkownika.

## Materiał do dokumentacji użytkownika

W AMC Test `Ctrl+C` kopiuje nazwę natychmiast i podaje jeden polski komunikat
„Skopiowano nazwę”. Lokalna poprawka zgodności powoduje, że funkcja
„ogłaszanie poleceń schowka” dodatku NVDAExtensionGlobalPlugin nie przechwytuje
`Ctrl+C` wyłącznie w zainstalowanym AMC. W innych programach dodatek zachowuje
swoje dotychczasowe działanie. Rozpoznanie AMC korzysta ze ścieżki procesu oraz
rozpoznanego układu instalacji (`runtime`, launcher i manifest), a nie z tytułu
okna ani ogólnej nazwy `python.exe`.

## Uzasadnienie i decyzje

- Nie przywrócono opóźnienia po stronie AMC: zapis do schowka pozostaje
  synchroniczny.
- Nie dodano AppModule ani natywnego gestu `Ctrl+C` do dodatku AMC dla NVDA,
  ponieważ odebrałoby to zwykłe polecenie czytnikowi i złamało dotychczasowy
  kontrakt gestów `Ctrl+Windows`.
- Przygotowano odwracalne narzędzie zgodności dla konkretnej funkcji zewnętrznego
  dodatku. Tworzy kopię oryginału, odrzuca nieznany układ źródła i zapisuje
  zmianę atomowo. Samo narzędzie nie restartuje NVDA.
- Korekta z 19 października 2026 zastępuje wcześniejszy pomysł opóźnienia
  zapisu AMC o 180 ms. Opóźnienie zostało usunięte już w `02fd6da8`, a obecna
  poprawka omija źródłowe opóźnienie dodatku tylko dla rozpoznanej instalacji
  AMC.

## Testy i wynik

- Sucha walidacja na rzeczywistym pliku NVDAExtensionGlobalPlugin 14.1.2:
  poprawkę można zastosować, a wygenerowany kod przechodzi kompilację składni.
- `wxlite/tests/test_nvda_extension_clipboard_compat.py`: początkowo `3
  passed`; po wykryciu instalacyjnego układu CRLF dodano przypadek regresyjny
  i uzyskano `4 passed`.
- Łączna izolowana regresja SEARCH-001/NVDA-001, Spotify, TIDAL, menu i
  schowka: `154 passed`.
- Po 02:00 potwierdzono brak aktywnego harmonogramu, brak wzrostu plików
  `.amc-partial` i brak blokady tych plików. Poprawkę zastosowano atomowo,
  sucha kontrola po zapisie rozpoznała ją jako obecną, a proces NVDA został
  ponownie uruchomiony.

## Znane ograniczenia

- Aktualizacja NVDAExtensionGlobalPlugin może nadpisać lokalną poprawkę; po
  aktualizacji trzeba najpierw ponownie wykonać suchą walidację nowego układu.
- Status pozostaje „W trakcie” wyłącznie do ręcznej próby `Ctrl+C` w AMC oraz
  w zwykłej aplikacji.
- Kopia oryginału musi zostać zachowana do ręcznego odbioru użytkownika.

## Wersja i commit

- Źródło narzędzia i testy: commit
  `1169e6aa17414c0d30c7cf4d3c40e530463ea317`.
- Zmienione pliki repozytorium:
  `tools/nvda_extension_clipboard_compat.py` oraz
  `wxlite/tests/test_nvda_extension_clipboard_compat.py`.
- Kompilacja i instalacja AMC Test:
  `2026.10.19-e0f97512d1eee067d225d7b8c73b808ff3f3e561-c0e62181`.
- Instalacja poprawki dodatku NVDA: wykonana; poprawka obecna dokładnie raz,
  kopia oryginału zachowana, NVDA zrestartowane.
- Publikacja: niewykonana i niedozwolona w nocnym etapie.
