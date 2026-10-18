# NVDA-001 — opóźnienie Ctrl+C z NVDAExtensionGlobalPlugin

- Status: `Oczekuje`
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

Do uzupełnienia po pracy:

- Data zakończenia:
- Wynik:
- Zmienione pliki:
- Commit bazowy i końcowy:
- Testy i rezultaty:
- Zbudowana lub zainstalowana wersja:
- Pozostałe ograniczenia:
