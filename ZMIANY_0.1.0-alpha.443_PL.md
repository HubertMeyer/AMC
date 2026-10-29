# AMC Public 0.1.0-alpha.443 — szkic zmian i odbioru

To jest roboczy opis stabilnego wydania Public do sprawdzenia przez
użytkownika.

## Najważniejsze zmiany

- Wydanie powstaje z tej samej bazy kodu co najnowszy AMC Test
  `0.1.0-alpha.442`.
- Menedżer sesji `Ctrl+Shift+S` udostępnia osobną czynność **Ustawienia
  sesji…**. Dla obsługiwanych sesji można zdecydować, czy Enter otwiera
  odtwarzacz, czy pozostawia użytkownika na liście.
- Język polski, angielski oraz wybór zgodny z systemem są dostępne w
  Ustawieniach. Zapis zmienia język otwartego interfejsu bez restartu.
- Poprawiono rozpoznawanie polskiego języka Windows oraz mieszany odczyt nazwy
  listy **Ulubione** w angielskim interfejsie.

## Zakres profilu Public

- Dostępne są: Pliki lokalne, Radio, Podcasty i YouTube, WiiM oraz Frontier
  Smart.
- Sonos, Spotify i TIDAL nie są dostępne w menu, Menedżerze sesji, pomocy,
  palecie poleceń ani w fizycznej zawartości pakietu.
- Public nie zawiera logowania Google do YouTube, prywatnych tokenów ani
  konfiguracji OAuth Google.
- Rozpoznane utwory mogą korzystać z publicznych stron usług, ale nie otwierają
  nieobecnych sesji Spotify lub TIDAL wewnątrz AMC.

## Sposób odbioru

1. Zainstaluj lub zaktualizuj AMC Public z kanału stabilnego.
2. Otwórz Menedżer sesji skrótem `Ctrl+Shift+S` i sprawdź, czy widoczne są
   WiiM oraz Frontier Smart, a nie ma Sonosa, Spotify ani TIDAL-a.
3. Otwórz **Ustawienia programu**, karta **Ogólne**, i sprawdź zmianę języka
   polskiego, angielskiego oraz zgodnego z systemem.
4. Dla obsługiwanej sesji otwórz **Ustawienia sesji…** i sprawdź zachowanie
   Entera oraz powrót fokusu po zapisie i anulowaniu.

## Ważne ograniczenia

- Automatyczne testy nie zastępują ręcznego odsłuchu interfejsu z NVDA.
- Instalator nie jest podpisany cyfrowo; Windows może pokazać ostrzeżenie
  reputacyjne. Integralność jest weryfikowana sumą SHA-256.
- Sama publikacja nie instaluje ani nie uruchamia nowej wersji na tym
  komputerze.

## Stan wydania

- Celowane testy bez widocznego interfejsu: 231/231 zaliczonych.
- Testy Launchera i aktualizatora: 38/38 zaliczonych.
- Paczka Public `89473955`: integralność i kontrolowany start zaliczone.
- Instalator `AMC-Public-2026-10-29-0136.exe`: zbudowany, przeskanowany i
  opublikowany w stabilnym wydaniu `public-2026.10.29.0136`.
- Instalatora nie uruchamiano ani nie instalowano na tym komputerze.
