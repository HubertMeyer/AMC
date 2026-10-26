# AMC — aktualizowanie programu i składników

> Projekt instrukcji i opisu zmian z 26 października 2026 r. Dokument wymaga
> korekty i akceptacji użytkownika przed publikacją.

## Aktualizacja całego AMC

1. Otwórz menu `Pomoc` i wybierz `Sprawdź aktualizację AMC…`.
2. AMC sprawdzi kanał przypisany do zainstalowanej wersji. AMC Test zawsze
   korzysta z kanału testowego, a AMC Public zawsze z kanału publicznego. Nie
   trzeba i nie można wybierać kanału ręcznie.
3. Fokus znajdzie się w polu `Informacje o aktualizacji AMC`. Pole podaje nową
   wersję oraz krótkie podsumowanie zmian. Można je czytać strzałkami jak
   zwykły tekst tylko do odczytu.
4. Jeżeli jest nowa wersja, przejdź Tabem do `Aktualizuj AMC` i naciśnij Enter.
   AMC pobierze i sprawdzi pełny instalator. Jeśli aktualizacji nie ma, okno
   zawiera tylko przycisk `Zamknij okno aktualizacji`.
5. Po poprawnej kontroli AMC zamknie się zwykłą bezpieczną drogą, zainstaluje
   nową wersję i ponownie się uruchomi. Ustawienia, Biblioteka, konta i
   wcześniejsze decyzje o skrótach oraz integracji Eksploratora pozostają w
   swoich profilach.

Jeżeli trwa nagrywanie albo któryś składnik AMC nie może się jeszcze zamknąć,
aktualizacja nie podmienia plików. Najpierw bezpiecznie zatrzymaj nagrywanie,
zamknij odpowiedni proces i ponów sprawdzenie. Błąd pobrania lub kontroli nie
instaluje częściowej wersji.

## Pierwsza instalacja na nowym komputerze

Pełny plik `AMC-Test-rrrr-mm-dd-ggmm.exe` albo
`AMC-Public-rrrr-mm-dd-ggmm.exe` zawiera program, prywatny runtime Python,
LiteHost, launcher i pomocnik aktualizacji. Użytkownik nie musi osobno
instalować Pythona ani .NET. Instalator tworzy wpis odinstalowania Windows i
pozwala wybrać opcjonalny skrót pulpitu oraz integrację obsługiwanych plików z
Eksploratorem.

## Aktualizacja FFmpeg i yt-dlp

Aktualizacja całego AMC i aktualizacja składników multimedialnych są osobnymi
czynnościami. Aby sprawdzić FFmpeg i yt-dlp, wybierz w menu `Pomoc` polecenie
`Sprawdź i zaktualizuj składniki: FFmpeg i yt-dlp`.

AMC pobiera składniki tylko ze wskazanych źródeł dostawców, porównuje SHA-256 i
uruchamia kontrolę wersji przed uaktywnieniem. Niepowodzenie pozostawia
poprzednią działającą kopię. Pierwszy rzeczywisty odbiór sieciowy tej funkcji
po nowym wydaniu należy wykonać ręcznie poza piaskownicą testową.

## Projekt listy zmian AMC Test 0.1.0-alpha.434

- Dodano `Pomoc > Sprawdź aktualizację AMC…`.
- Dodano dostępne pole informacji o nowej wersji i przycisk `Aktualizuj AMC`.
- Kanał jest przypisany do profilu: Test nie może pobrać Public, a Public nie
  może pobrać Test.
- Pobierany instalator jest sprawdzany według profilu, nazwy, rozmiaru i
  SHA-256 przed zamknięciem programu.
- Aktualizacja używa pełnego instalatora Windows, zachowuje stan deinstalatora
  oraz wcześniejsze zadania instalacji i po sukcesie ponownie uruchamia AMC.
- Komunikaty błędów aktualizacji programu i składników nie odczytują przez
  NVDA technicznych ścieżek ani surowych wyjątków.

## Procedura wydania dla opiekuna projektu

1. Zbudować profil `test` albo `public` z czystego, zapisanego commitu przez
   `wxlite/tools/Build-AMCBundle.ps1`.
2. Z tego samego commitu utworzyć pełny instalator przez
   `wxlite/tools/Build-AMCInstaller.ps1`.
3. Przygotować krótki plik podsumowania zmian i najpierw uruchomić
   `scripts/Publish-AMCRelease.ps1` bez `-Publish`. Sprawdzić powstałe pliki
   integralności, opisu, gotowości i `amc-update-<profil>.json`.
4. Po ręcznym odbiorze instalatora wykonać ten sam skrypt z `-Publish`.
   Skrypt wymaga obecności dokładnego commitu na GitHubie, nie zastępuje
   istniejącego wydania i po wysłaniu odczytuje stan załączników.
5. Na poprzedniej zainstalowanej wersji wykonać aktualizację z menu i
   potwierdzić nazwę okna, wersję, zachowane ustawienia, skróty, integrację
   powłoki oraz działanie deinstalatora.

Publikacja źródeł, udany build, lokalny instalator, instalacja na komputerze i
GitHub Release są pięcioma osobnymi wynikami i tak należy je raportować.
