# AMC14 — foldery i integracja z powłoką Windows

Status: **W trakcie**

Źródło zatwierdzonego zakresu:
`D:\Projekty Codex\Accessible Multimedia Controller\AMC14_FOLDERY_I_INTEGRACJA_POWLOKI_2026-10-18.md`.
Historyczny projekt służy wyłącznie jako materiał do odczytu. Wdrożenie jest
prowadzone w bieżącym AMC Test.

## Zakres

- aplikacyjne polecenie otwarcia folderu lokalnego elementu i zaznaczenia
  istniejącego pliku;
- odbieranie pliku przekazanego przy uruchomieniu oraz bezpieczne przekazanie
  go do już działającej instancji tego samego profilu;
- jawne dodawanie pliku do kolejki przez parametr `/kolejka`, bez usuwania
  istniejącej pozycji;
- całkowite rozdzielenie kanałów AMC Test i publicznego AMC;
- dopiero po odbiorze warstwy aplikacyjnej: opcjonalne i odwracalne wpisy
  instalatora w powłoce Windows.

Nie przypisujemy obecnie `Ctrl+Enter` ani innego nowego skrótu. Integracja nie
ustawia AMC domyślnym programem bez decyzji użytkownika.

## Materiał do dokumentacji użytkownika

### Etap A — folder zawierający

W menu **Pliki** oraz w palecie poleceń `Ctrl+Shift+K` jest polecenie
**Otwórz folder zawierający**. Działa dla lokalnego pliku lub folderu
zaznaczonego na liście, a w widoku odtwarzacza — dla rzeczywiście odtwarzanego
lokalnego pliku. Dla pliku Eksplorator otwiera folder i zaznacza ten plik; dla
folderu otwiera sam folder.

Polecenie celowo nie ma jeszcze skrótu. Pełna pomoc `F1` podaje je jako
**Bez skrótu — Otwórz folder zawierający**. `Ctrl+F1` nadal opisuje wyłącznie
rzeczywiście naciśnięty gest i nie udaje nieistniejącego skrótu.

Jeżeli element internetowy nie ma lokalnej kopii, AMC mówi:
**Ten element nie ma lokalnego pliku**. Jeżeli zapamiętana ścieżka już nie
istnieje, mówi: **Nie znaleziono lokalnego pliku**. Adres internetowy nie jest
otwierany jako folder.

## Uzasadnienie i decyzje

- 2026-10-19: etap aplikacyjny powstaje przed rejestracją powłoki i przed
  instalatorem. Pozwala to sprawdzić zachowanie bez zmiany skojarzeń Windows.
- Polecenie jest jedną akcją wspólną dla wykonania, menu, pełnej pomocy i
  palety. Dostępność wynika z bieżącej sesji oraz z lokalnej ścieżki elementu.
- Ścieżka jest przekazywana Eksploratorowi jako osobna lista argumentów, bez
  `shell=True` i bez składania tekstowej komendy. Nazwy ze spacjami, przecinkami,
  średnikami i polskimi znakami nie zmieniają znaczenia polecenia.
- Sprawdzenie istnienia następuje dopiero po wykonaniu polecenia. Dzięki temu
  odświeżanie menu nie blokuje interfejsu przy niedostępnym dysku sieciowym.
- Internetowy element bez pobranej kopii otrzymuje krótką odmowę; jego adres
  nie trafia do komunikatu NVDA.

## Testy i wynik

2026-10-19, etap A:

- `python wxlite/run_tests.py shell_paths_and_folder_command` — wszystkie 7
  testów AMC14 przeszły;
- sprawdzono rozpoznawanie ścieżki dyskowej i UNC oraz odrzucanie `https:` i
  identyfikatora usługi;
- sprawdzono osobne argumenty Eksploratora dla folderu i zaznaczanego pliku,
  także dla spacji, przecinka, średnika, nawiasu i polskich znaków;
- sprawdzono wspólną nazwę i dostępność w menu, pełnej pomocy oraz palecie dla
  sesji Pliki i Podcasty i YouTube oraz brak polecenia w Radiu;
- sprawdzono lokalny wiersz oraz krótką odmowę dla elementu internetowego.

Uruchamiacz testów zgłosił dodatkowo cztery zastane błędy importu innych
modułów testowych wymagających nieobecnego pakietu `pytest`. Nie są to
niepowodzenia testów AMC14; wszystkie siedem uruchomionych prób tego etapu
zakończyło się wynikiem `OK`.

## Znane ograniczenia

- Etap A jest zmianą źródłową i testową. Nie zbudowano ani nie zainstalowano
  nowej wersji, nie otwierano też prawdziwego Eksploratora w teście.
- Przekazywanie argumentu pliku do działającej instancji oraz kolejka
  `/kolejka` są następną częścią bieżącego zadania.
- Rejestracja typów plików, menu kontekstowego i ustawień domyślnych aplikacji
  nie została jeszcze wykonana.

## Wersja i commit

- Profil: źródła wspólne AMC Test i publicznego AMC, z późniejszym rozdzieleniem
  kanału przekazywania żądań według profilu.
- Instalacja: bez zmian.
- Commit etapu A: do uzupełnienia po zatwierdzeniu testów w repozytorium.
