# AMC Test 23.10.2026, 22:20 — tempo Spotify i PIN Frontier Smart

Status: **Zainstalowane i uruchomione do ręcznego odbioru. Nieopublikowane.**

## Zachowanie użytkowe

- Spotify ma rzeczywistą regulację prędkości `0,50–2,00x` w wewnętrznym
  silniku. `Shift+,` zwalnia, `Shift+.` przyspiesza, a `Ctrl+.` przywraca
  normalne `1,00x`. Polecenia są wspólne dla skrótów, menu, pomocy
  kontekstowej, pełnej pomocy i palety.
- Odcinki Spotify używają silnika mowy, utwory silnika muzycznego; oba
  zachowują wysokość głosu i muzyki.
- Pole Frontier Smart nazywa kod jednoznacznie „PIN-em NetRemote urządzenia”.
  Po wykryciu Teufel RADIO 3SIXTY AMC podaje fabryczny kod `1234` oraz ścieżkę
  jego zmiany w radiu: `Ustawienia systemowe → Sieć → Ustawienia NetRemote
  PIN`.
- Natywne rozdziały Spotify nie są częścią tej instalacji i pozostają bez
  zmian. Zachowanie awaryjnego wyboru urządzenia audio po odłączeniu Denona
  nadal wymaga kontrolowanego testu.

## Testy i rzeczywiste wyniki

- Rust Release offline: 34/34 testy jednostkowe i 13/13 procesowych.
- wxPython, zestaw ukierunkowany: 204/204.
- LiteHost ProtocolTests: 27/27 zestawów; Core SmokeTests zakończone kodem 0;
  izolowany `--librespot-output-smoke` zaliczony.
- Pełna kompilacja Release rozwiązania: 0 ostrzeżeń, 0 błędów.
- Testy układu paczki: 31/31.
- Szeroki Windows SmokeTests przeszedł testy zmienionego Spotify, ale później
  zatrzymał się na zastanej kontroli nazwy instalatora i przejściowym błędzie
  `OpenClipboard`; tego przebiegu nie uznaje się za pełną zaliczoną regresję.
- Kandydat oraz stała instalacja przeszły kontrolę integralności i kontrolowany
  start interfejsu oraz hosta. Po instalacji potwierdzono odpowiadające okno
  „AMC Test — 23.10.2026, 22:20”, proces
  `D:\Projekty Codex\AMC Python\runtime\python.exe` i lokalny host audio.

## Wersja, instalacja i publikacja

- Rewizja źródłowa paczki:
  `591322e2f85c0a07634733c6164fa4cc6a336595`.
- Identyfikator pakietu: `53e3d987`.
- Pełna etykieta:
  `2026.10.23-591322e2f85c0a07634733c6164fa4cc6a336595-53e3d987`.
- Stała instalacja: `D:\Projekty Codex\AMC Python`.
- Host Librespot: 6 595 072 B, SHA-256
  `0fde62641c16de6e35ac25962b756f868dd7fd36643e71661f849c231d55c15a`.
- Testy promocji pominięto w samym skrypcie, ponieważ opisane wyżej bramki i
  kompilacje wykonano bezpośrednio przed promocją z tej samej czystej rewizji.
- AMC Public, instalator publiczny i GitHub pozostały bez zmian. Niczego nie
  opublikowano ani nie wypchnięto.

## Odbiór ręczny

1. Uruchomić krótki odcinek Spotify, sprawdzić kolejno `Shift+.`, `Shift+,`
   i `Ctrl+.` oraz komunikaty NVDA.
2. Powtórzyć na utworze muzycznym i ocenić wysokość dźwięku oraz przejścia po
   pauzie i przewinięciu.
3. Przy odłączonym Denonie uruchomić krótki, najlepiej już buforowany materiał
   i potwierdzić automatyczny wybór urządzenia domyślnego.
4. W Frontier Smart wybrać Teufel, wpisać `1234`, przejść klawiszem `Tab` do
   „Połącz i zapisz” i sprawdzić fokus po zamknięciu oraz ponownym otwarciu.

Ręczny odsłuch, połączenie z radiem i odbiór NVDA nie zostały jeszcze
wykonane; sama instalacja i automatyczne kontrole nie stanowią ich zastępstwa.
