# AMC Test 0.1.0-alpha.445 — projekt opisu zmian i odbioru

To wydanie przenosi do pełnego profilu AMC Test poprawki zweryfikowane w AMC
Public oraz wszystkie późniejsze zmiany wspólnej bazy kodu z 29 października
2026 r. Dokument jest projektem do korekty użytkownika po odbiorze.

## Najważniejsze zmiany

- Import playlist M3U zachowuje nazwy stacji z `#EXTINF` i `icy-name`, nie
  redukuje wielopozycyjnego pliku do jednego adresu oraz ma test regresji na
  pliku zawierającym wiele kanałów.
- Radio odczytuje tytuły bieżących audycji i utworów z metadanych ICY dla
  obsługiwanych strumieni MP3 i AAC. Tytuł głównego okna może zawierać nazwę
  stacji i bieżącego utworu, dzięki czemu informację odczytuje także `NVDA+T`.
- Stara, ostatnio użyta prędkość nie staje się automatycznie domyślną
  prędkością każdej sesji po migracji ustawień.
- Na karcie `Ustawienia > Aktualizacje` jest domyślnie włączone pole
  `Automatycznie sprawdzaj dostępność nowej wersji AMC po uruchomieniu programu`.
  Sprawdzenie odbywa się w tle; pobranie i instalacja nadal wymagają wybrania
  przycisku `Aktualizuj AMC`.
- Proces wydania odrzuca pliki spoza manifestu, w tym pamięć podręczną Pythona
  utworzoną podczas kontroli startu.

## Profil AMC Test

- Wydanie zachowuje pełny profil sesji używany w AMC Test: TIDAL, Spotify,
  Sonos, WiiM, Frontier Smart, Radio, Podcasty i pozostałe źródła Test.
- Sonos pozostaje funkcją eksperymentalną w dotychczasowym, niedziałającym
  stanie; wydanie nie przedstawia go jako naprawionego.
- Dane, konta, ustawienia, Biblioteka i nagrania nie są dołączane do paczki ani
  publikowane. Aktualizacja korzysta z istniejącego profilu AMC Test.

## Odbiór po aktualizacji

- Sprawdzić import przekazanej playlisty M3U i nazwy wszystkich stacji.
- Sprawdzić tytuł bieżącej audycji zwykłą nawigacją oraz `NVDA+T`.
- Otworzyć `Ustawienia > Aktualizacje`, sprawdzić nowe pole, zamknąć okno i
  otworzyć je ponownie.
- Potwierdzić obecność TIDAL-a, Spotify i Sonosa oraz zachowanie dotychczasowych
  kont i ustawień. Brak działania Sonosa pozostaje znanym ograniczeniem.

## Stan wytworzenia

- Kod wydania: commit `cbf71ad1ba86f2b2d638eb3128b26d5ff73456e1`.
- Testy bezokienne: 205 zaliczonych i 1 pominięty w Pythonie, 3/3 M3U/ICY
  oraz 38/38 launchera i aktualizatora.
- Paczka `e6945c5c` i instalator `AMC-Test-2026-10-29-2032.exe`: zbudowane i
  zweryfikowane. SHA-256 instalatora:
  `da28bcb96bc71262627bbc91d110295aa13d0a9f63cf28f29e860c0c1ef7624a`.
- Wydanie GitHub `test-2026.10.29.2032`: opublikowane jako prerelease kanału
  Test i odczytowo zweryfikowane.
- Instalacja oraz ręczny odbiór NVDA: niewykonane; działającej kopii programu
  nie zmieniono.
