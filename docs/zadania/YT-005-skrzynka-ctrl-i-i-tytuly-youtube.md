# YT-005 — skrzynka Ctrl+I i polskie tytuły YouTube

## Status

W trakcie. Kod i testy są przygotowywane w kanonicznym AMC wxPython.

## Zgłoszenie użytkownika

27 października 2026 użytkownik potwierdził, że porcje po 150 pozycji są
potrzebne, ale pierwsza porcja skrzynki obejmuje jedynie około pół dnia przy
dużej liczbie obserwowanych podcastów i kanałów YouTube. Poprosił, aby kolejne
naciśnięcia `Ctrl+I` doładowywały dalsze porcje po 150. Zgłosił też, że część
tytułów filmów YouTube ponownie jest wyświetlana po angielsku.

Ta korekta zastępuje wcześniejsze założenie z POD-003, że sam końcowy wiersz
**Załaduj więcej** wystarcza jako jedyna droga szybkiego doładowania skrzynki.

## Diagnoza

- Odczytowa kontrola prawdziwej bazy wykazała 27 862 pozycje w skrzynce, a
  pierwsze 150 obejmowało około 14 godzin. Dane użytkownika nie zostały
  zmienione.
- `Ctrl+I` ponownie otwierało ten sam widok, ale żądało poprzedniej liczby
  pozycji zamiast następnej porcji. Enter na wierszu doładowania działał.
- Argument kolekcji yt-dlp łączył `youtubetab:approximate_date` z pozbawionym
  nazwy ekstraktora `lang=pl`. Ustawienie języka nie trafiało więc do
  ekstraktora `youtube`. Kanałowy Atom poprawiał tytuły tylko dla niewielkiej
  liczby najnowszych materiałów, a starsze pozycje mogły zachować automatyczne
  tłumaczenie angielskie.
- Korekta z 27 października 2026 zastępuje wcześniejszy komentarz źródłowy z
  11 września 2026, według którego dwie opcje `--extractor-args` nie mogły
  działać razem. Oficjalny kontrakt yt-dlp pozwala powtórzyć opcję dla różnych
  ekstraktorów; średnik rozdziela argumenty tylko w obrębie jednego ekstraktora.

## Materiał do dokumentacji użytkownika

Pierwsze `Ctrl+I` otwiera **Nowe odcinki i materiały** i wczytuje 150 pozycji.
Kolejne `Ctrl+I`, gdy ta skrzynka jest otwarta, doładowuje następne 150 i
ustawia fokus na pierwszej nowej pozycji. Nadal można użyć Enter na końcowym
wierszu **Załaduj więcej**. `Ctrl+I` nie pobiera danych z sieci; pokazuje dane
już zapisane. Odświeżanie sieciowe uruchamia `F5` lub `Ctrl+F5` zgodnie z
kontekstem.

Po odświeżeniu kanału lub playlisty YouTube AMC prosi yt-dlp o polskie
metadane. Zapisane wcześniej tytuły zostaną zaktualizowane przy następnym
odświeżeniu źródła.

## Uzasadnienie i decyzje

- Rozmiar porcji pozostaje równy 150, aby bardzo duża skrzynka nie blokowała
  interfejsu ani czytnika ekranu.
- Powtórne `Ctrl+I` jest drugim wejściem do istniejącej operacji doładowania;
  nie tworzy osobnej listy i nie zmienia zachowania Escape.
- Nazwa, skrót i opis polecenia pochodzą ze wspólnego modelu używanego przez
  menu, paletę, pełną pomoc i Pomoc klawiatury.
- yt-dlp otrzymuje dwa jawne argumenty ekstraktorów: `youtubetab` dla dat
  oraz `youtube` dla języka metadanych. Jest to składnia udokumentowana przez
  dostawcę i sprawdzona z zainstalowanym komponentem.

## Testy i wynik

Do uzupełnienia po uruchomieniu regresji.

## Testy NVDA i klawiatury

Automatyczne testy sprawdzają pierwsze i ponowne `Ctrl+I`, niezmieniony punkt
powrotu Escape oraz zgodność menu, palety i obu rodzajów pomocy. Ręczny odbiór
NVDA nowej kompilacji pozostaje do wykonania po zbudowaniu i instalacji.

## Znane ograniczenia

- Poprawa już zapisanych tytułów wymaga odświeżenia odpowiedniego źródła.
- Źródło publiczne YouTube nadal ma bezpieczny limit 100 pozycji na jedno
  odświeżenie; limit 150 dotyczy wyłącznie liczby pozycji pokazanych naraz w
  zbiorczym widoku skrzynki.

## Wersja i commit

Wersja nie została jeszcze zbudowana ani zainstalowana. Commit: jeszcze nie
utworzono.
