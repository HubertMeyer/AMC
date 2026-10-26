# YT-004 — pobieranie wideo z YouTube

- Status: **W trakcie; kod, testy, build i instalacja AMC Test są gotowe,
  pozostaje ręczny odbiór pobranego pliku i NVDA**.
- Data wdrożenia: 26.10.2026.
- Instalacja: `D:\Projekty Codex\AMC Python`.

## Zachowanie widoczne dla użytkownika

- Na jednym albo kilku zaznaczonych materiałach YouTube `Ctrl+Shift+D`
  pobiera pliki wideo do skonfigurowanego folderu pobierania.
- `Ctrl+S` na jednym materiale YouTube otwiera systemowe `Zapisz jako` i
  pozwala wybrać nazwę, położenie oraz format dla tej jednej operacji.
- W Ustawieniach sesji Podcasty i YouTube można wybrać domyślnie `MP4,
  domyślny i najbardziej zgodny` albo `Oryginalny lub najlepszy dostępny
  format, bez wymuszania MP4`.
- Na zwykłym odcinku podcastu `Ctrl+S` nadal zapisuje odcinek audio. Skrót jest
  rozstrzygany przez wspólny model według rodzaju zaznaczenia.
- Menu, menu kontekstowe, paleta, `Ctrl+F1` i pełna pomoc pokazują te same
  działania tylko tam, gdzie są dostępne.

Pobieranie używa zarządzanych przez AMC składników yt-dlp i FFmpeg. Plik
powstaje najpierw w katalogu roboczym, jest sprawdzany jako niepusty, a dopiero
potem atomowo publikowany pod nazwą docelową. Przerwanie nie pozostawia
gotowego pliku udającego sukces.

## Uzasadnienie i decyzje

- MP4 jest bezpiecznym ustawieniem domyślnym. Tryb oryginalny zachowuje
  najlepszy format dostarczony przez usługę i dopasowuje końcowe rozszerzenie.
- Identyfikatory i adresy YouTube pozostają w modelu i nie są czytane przez
  NVDA jako etykiety elementów.
- Pobieranie wideo i audio korzysta z jednej blokady operacji, aby dwa zapisy
  nie nadpisywały wspólnego stanu postępu.

## Testy i wynik

- Testy kontraktu obejmują oba skróty, rozpoznawanie elementów YouTube,
  domyślny i błędny format, menu oraz jawne operacje protokołu z formatem.
- Końcowy zestaw menu, skrótów i pomocy: **106/106**.
- Pełna regresja promocji: **2057 zaliczonych, 111 pominiętych, 13 podtestów
  zaliczonych**.
- LiteHost Release, serwer protokołu, launcher i aktualizator: zaliczone;
  launcher **30/30**, buildy **0 ostrzeżeń i 0 błędów**.
- Kandydat i instalacja przeszły kontrolę 1674 plików, sum, manifestu oraz
  izolowany start interfejsu i hosta.

## Znane ograniczenia i ręczny odbiór

- Rzeczywiste pobranie zależy od dostępności filmu, sieci oraz aktualnych
  składników yt-dlp i FFmpeg.
- Materiał chroniony, prywatny albo niedostępny regionalnie może zostać
  odrzucony przez YouTube.
- Do ręcznego odbioru pozostaje pobranie krótkiego filmu w obu trybach,
  sprawdzenie rzeczywistego rozszerzenia, anulowania `Zapisz jako`, komunikatów
  postępu, fokusu po zamknięciu i ponownego otwarcia ustawienia z NVDA.

## Materiał do dokumentacji użytkownika

> Zaznacz materiały YouTube i naciśnij Ctrl+Shift+D, aby pobrać je jako wideo
> do folderu pobierania. Dla jednego filmu Ctrl+S otwiera Zapisz jako. Domyślny
> format MP4 lub format oryginalny wybierzesz w Ustawieniach sesji Podcasty i
> YouTube.

## Projekt opisu zmian

> Dodano dostępne pobieranie filmów YouTube do MP4 lub najlepszego formatu,
> wielokrotny wybór pod Ctrl+Shift+D i bezpieczne Zapisz jako pod Ctrl+S.

## Wersja i commit

- Commit: `bba5e92d687ade1998e79c88656e1a5d545abcf2`.
- Pakiet: `39f0d3f2`.
- Okno: `AMC Test — 26.10.2026, 13:32`.
- Publikacja: nie wykonywano.
