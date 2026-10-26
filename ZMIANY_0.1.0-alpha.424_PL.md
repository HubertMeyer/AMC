# AMC 0.1.0-alpha.424 — Frontier Smart gotowy do próby z radiem

## Pierwsze uruchomienie

Nową sesję **Frontier Smart** tworzy się w istniejącym Menedżerze sesji,
otwieranym przez `Ctrl+Shift+S` lub `Ctrl+0`. Po wybraniu **Nowa sesja Frontier
Smart…** AMC sam rozpoczyna wykrywanie urządzeń w sieci lokalnej. Nie trzeba
naciskać `Ctrl+F5`, wpisywać adresu IP ani podawać PIN-u przed skanem.

Wykryte radio pojawia się najpierw na liście. Dopiero po jego wybraniu należy
wpisać PIN urządzenia i użyć **Połącz i dodaj**. Ręczny adres IP pozostaje
opcją awaryjną w zwiniętej sekcji. Fokus podczas skanowania pozostaje na
liście, a nie na przycisku zamknięcia.

## Ponowne otwieranie listy

Gdy urządzenie zostało już dodane, `Ctrl+F5` pokazuje zapisaną listę i pozwala
wybrać urządzenie aktywne, odświeżyć je albo usunąć z AMC. Okno nie rozpoczyna
wtedy kolejnego skanu. Służy do tego osobny przycisk **Wykryj nowe
urządzenia**.

## Zgodność ze starszym firmware'em

AMC pokazuje odpowiedź SSDP przed uwierzytelnieniem i odpytuje wszystkie
aktywne interfejsy IPv4. Awaria jednej karty sieciowej nie przerywa całego
skanu. Po podaniu PIN-u najpierw sprawdzana jest minimalna tożsamość urządzenia,
a pełny stan jest pobierany osobno. Gdy starszy firmware nie obsługuje
`GET_MULTIPLE`, AMC przechodzi na pojedyncze odczyty również wtedy, gdy radio
zwróci błąd FSAPI w odpowiedzi HTTP 200.

## Zakres sprawdzenia

- testy protokołu Frontier Smart: 13/13;
- testy okien Frontier Smart: 6/6;
- pełne testy Core: zaliczone po użyciu projektowego katalogu tymczasowego;
- celowa próba negatywna potwierdziła, że test wykrywa brak obsługi odpowiedzi
  starszego firmware'u;
- pełne testy Windows nie zakończyły całego przebiegu z powodu pięciu
  istniejących problemów aparatury Sonosa oraz odmowy dostępu do schowka;
- rzeczywiste wykrywanie, PIN, transport, tryby i presety wymagają jeszcze
  sprawdzenia przez użytkownika na radiu.

To jest szkic informacji o zmianach do akceptacji po próbie sprzętowej. Nie
jest opublikowanym wydaniem GitHub.
