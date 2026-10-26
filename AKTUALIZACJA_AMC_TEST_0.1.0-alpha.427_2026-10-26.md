# Aktualizacja AMC Test 0.1.0-alpha.427

Data: 26 października 2026 r.

## Zakres użytkowy

Aktualizacja łączy trzy wcześniej wykonane zadania:

1. interakcje z historią rozpoznanych utworów: krótkie i pełne menu działań,
   Spotify, TIDAL, publiczne łącza Apple Music, kopiowanie, otwieranie albumu,
   kolejność rekordów i fokus;
2. rozdzielenie informacji pod strzałkami w widoku `Nagrywane` oraz zwięzły
   opis pliku wynikowego pod prawą strzałką w Harmonogramie;
3. pobieranie wideo z YouTube przez `Ctrl+Shift+D` oraz zapis przez `Ctrl+S`,
   z wyborem MP4 albo najlepszego dostępnego formatu.

Źródłowe zapisy zachowania pozostają w:

- `AMC_ROZPOZNANE_UTWORY_INTERAKCJE_2026-10-26.md`;
- `AMC_NAGRYWANE_PRAWA_STRZALKA_2026-10-26.md`;
- `AMC_POBIERANIE_WIDEO_YOUTUBE_2026-10-25.md`.

## Źródła i wersja

- kanoniczne repozytorium:
  `D:\Projekty Codex\Accessible Multimedia Controller`;
- numer AMC Test: `0.1.0-alpha.427`;
- baza Git: `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`;
- zmiany pozostają w istniejącym, wcześniej brudnym katalogu roboczym;
- nie utworzono commita i nie wykonano publikacji zdalnej.

## Testy i kompilacja

- kompilacja całego rozwiązania w konfiguracji Release: powodzenie,
  0 ostrzeżeń i 0 błędów;
- test Core `--youtube-video-download`: powodzenie;
- test Windows `--youtube-video-download`: powodzenie;
- test Windows `--recognition-history-ui`: powodzenie;
- test Windows `--active-recording-output`: powodzenie;
- test Windows `--schedule-copy`: 9/9;
- przed budowaniem i ponownie przed instalacją nie działał żaden proces AMC,
  AMC Test, `ffmpeg` ani `yt-dlp`;
- nie wykonano ręcznego odsłuchu żywego NVDA ani rzeczywistego pobrania filmu
  z YouTube.

Nie uruchamiano pełnego monolitycznego zestawu Windows. Ma on wcześniej
zapisane, niezależne problemy aparatury WPF i schowka. Zamiast przedstawiać go
jako zielony przebieg, uruchomiono izolowane testy wszystkich trzech zakresów.

## Pierwszy pakiet, instalator i instalacja — stan historyczny, zastąpiony

- pakiet:
  `D:\Projekty Codex\Accessible Multimedia Controller\publish\AccessibleMediaController-0.1.0-alpha.427`;
- program w pakiecie:
  `AccessibleMediaController-0.1.0-alpha.427.exe`;
- program: 194582928 bajtów;
- SHA-256 programu:
  `73D2077EC5419828EC11902FE06D3CDB34B272F4A2DA61683D1F442E7E13FBB5`;
- instalator:
  `D:\Projekty Codex\Accessible Multimedia Controller\publish\AMC-Setup-0.1.0-alpha.427.exe`;
- instalator: 65482800 bajtów;
- SHA-256 instalatora:
  `46B6ADFA31727071810992B81C0F6E2C616AE89EE81DA706DC9645F65B5A6501`;
- kompilator instalatora: Inno Setup 6.7.3;
- cicha instalacja: kod zakończenia 0;
- zainstalowany program:
  `C:\Users\micha\AppData\Local\Programs\AMC\AccessibleMediaController.exe`;
- wersja zainstalowanego programu: `0.1.0-alpha.427`;
- suma zainstalowanego programu jest identyczna z sumą programu w pakiecie;
- wymagane moduły i katalogi zależności są obecne;
- po instalacji AMC Test pozostawiono zamknięty.

## Szkic zmian dla użytkownika

- Rozpoznane utwory otrzymały skróconą listę najważniejszych działań pod prawą
  strzałką oraz pełny zestaw usług, łączy i powiązań w menu kontekstowym.
- `Ctrl+Enter` pokazuje album w domyślnej usłudze AMC i ustawia fokus na
  rozpoznanym utworze; osobne pozycje otwierają aplikacje usług.
- W `Nagrywane` lewa strzałka opisuje strumień, a prawa parametry i miejsce
  zapisywanego pliku. Harmonogram używa tego samego krótkiego opisu.
- W sesji Podcasty i YouTube `Ctrl+Shift+D` pobiera wideo, a `Ctrl+S` otwiera
  zapis wideo pod wybraną nazwą. Domyślnym formatem jest MP4; ustawienia
  pozwalają zachować najlepszy format źródłowy.

Ten szkic nie został opublikowany i pozostaje do korekty użytkownika.

## Uzupełnienie z 26 października 2026 r. — nazwy stacji z prostych M3U

Do bieżących źródeł **AMC Test** dodano uzupełnianie brakujących nazw stacji z
ograniczonych czasowo nagłówków Icecast/Shoutcast. Nazwa zapisana w playliście
ma pierwszeństwo, a brak nazwy serwera pozostawia krótką nazwę hosta zamiast
pełnego adresu URL. Zmiana nie dodaje nowego polecenia ani skrótu.

Korekta użytkownika z tego samego dnia zastępuje wcześniejszą, błędną decyzję
asystenta o oznaczeniu tej zmiany numerem `0.1.0-alpha.428`. Profil pozostaje
**AMC Test**, a numer źródeł pozostaje `0.1.0-alpha.427`; nie utworzono nowego
wydania publicznego.

Izolowana kompilacja i test importu zakończyły się powodzeniem. Na przekazanej
playliście przyjęto 17 unikalnych stacji: 14 nazw pochodziło z serwerów, a 3
pozycje zachowały nazwę zastępczą hosta. Szczegółowy zapis znajduje się w
`AMC_IMPORT_NAZW_ICY_2026-10-26.md`.

Zainstalowany wcześniej program `0.1.0-alpha.427` o sumie zapisanej w sekcji
„Pakiet, instalator i instalacja” jeszcze nie zawiera tego uzupełnienia. W tym
zadaniu nie zbudowano nowego instalatora i nie ponowiono instalacji AMC Test.

Powyższe dwa zdania opisują stan po samym zadaniu importu. Zostały zastąpione
przez późniejsze scalenie wszystkich funkcji opisane niżej.

## Uzupełnienie końcowe z 26 października 2026 r. — kompletny AMC Test

Na polecenie użytkownika połączono w jednej bieżącej kopii **AMC Test**:

1. historię rozpoznanych utworów i wszystkie działania pod `Ctrl+Alt+S`;
2. poprawione fizyczne rozpoznawanie `Ctrl+Alt+S` także z głównej listy Radia;
3. opis strumienia i pliku wynikowego w `Nagrywane` oraz Harmonogramie;
4. pobieranie wideo z YouTube przez `Ctrl+Shift+D` i kontekstowe
   **Zapisz wideo jako** przez `Ctrl+S`;
5. uzupełnianie nazw stacji podczas importu prostych playlist M3U.

WPF przekazuje literę w skrócie zawierającym Alt jako `Key.System` i umieszcza
właściwy klawisz w `SystemKey`. Odtwarzacz normalizował to wcześniej, ale
handler głównej listy porównywał surowe `e.Key` z `S`. Skróty `S`, `Shift+S`,
`Ctrl+Alt+S` i `Ctrl+Alt+Shift+S` korzystają teraz z jednego routera używanego
przez listę, odtwarzacz i pomoc klawiatury. `Ctrl+Alt+S` działa w Radiu także
poza odtwarzaczem; nie przejmuje skrótu w innych sesjach.

### Weryfikacja scalonego zakresu

- pełna kompilacja rozwiązania Release: powodzenie, 0 ostrzeżeń i 0 błędów;
- `--recognition-history-ui`: powodzenie, w tym wspólny routing skrótów;
- Windows `--youtube-video-download`: powodzenie;
- Core `--youtube-video-download`: powodzenie;
- `--active-recording-output`: powodzenie;
- `--schedule-copy`: 9/9;
- `--radio-playlist-import`: powodzenie;
- ręczny test żywego NVDA i rzeczywiste pobranie wideo: niewykonane.

### Bieżący pakiet i instalacja

- numer techniczny pozostaje `0.1.0-alpha.427`; nie utworzono `alpha.428`;
- pakiet:
  `D:\Projekty Codex\Accessible Multimedia Controller\publish\AccessibleMediaController-0.1.0-alpha.427`;
- program: 194591120 bajtów;
- SHA-256 programu:
  `AF37288D7F1355A5E499B94B21D7199E8309C86C5C667369A4B327843A12567F`;
- instalator:
  `D:\Projekty Codex\Accessible Multimedia Controller\publish\AMC-Setup-0.1.0-alpha.427.exe`;
- instalator: 65507701 bajtów;
- SHA-256 instalatora:
  `543C2FCB59BAF77FC6F6561FB7E55278743D6232829F30D50AE137039068BAB6`;
- kompilator instalatora: Inno Setup 6.7.3;
- cicha instalacja: kod zakończenia 0;
- zainstalowany program:
  `C:\Users\micha\AppData\Local\Programs\AMC\AccessibleMediaController.exe`;
- `ProductVersion` zainstalowanego programu: `0.1.0-alpha.427`;
- suma zainstalowanego programu jest identyczna z sumą programu w pakiecie;
- wymagane moduły są obecne;
- AMC Test po instalacji pozostawiono zamknięty.

Pierwszy pakiet `alpha.427` zachowano tymczasowo w `publish` pod ukrytą nazwą
z prefiksem `.previous-` do czasu odbioru przez użytkownika.
