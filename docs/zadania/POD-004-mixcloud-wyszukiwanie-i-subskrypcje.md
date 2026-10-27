# POD-004 — Mixcloud w Podcastach: wyszukiwanie i subskrypcje

- Status: `Kod i testy gotowe; przed promocją do AMC Test`
- Utworzono: 27 października 2026
- Obszar: Podcasty i YouTube, publiczne katalogi, dostępność
- Polecenie użytkownika: dodać SoundCloud albo Mixcloud do `Ctrl+N`,
  `Ctrl+F` i `Ctrl+Shift+L`, bez problematycznego logowania.

## Cel

AMC Test ma traktować publiczne kanały Mixcloud jako odświeżalne źródła w
sesji Podcasty i YouTube. Użytkownik ma móc wyszukać kanał lub audycję przez
`Ctrl+F`, dodać kanał do Biblioteki przez `Ctrl+Shift+L`, wkleić publiczny
adres Mixcloud w `Ctrl+N`, otworzyć kanał i przeglądać jego audycje.

## Korekta i decyzja z 27 października 2026

Ta decyzja zastępuje wcześniejsze pozostawienie SoundCloud jako wyłącznie
publicznego RSS bez adaptera katalogowego. Nie wprowadzamy logowania ani
wyszukiwania SoundCloud: aktualna oficjalna rejestracja aplikacji wymaga
płatnego konta Artist Pro i sekretu klienta, którego nie wolno umieszczać w
desktopowym AMC. Nie zastępujemy API parsowaniem stron ani prywatnym kluczem.

Wybieramy Mixcloud, ponieważ oficjalne API pozwala bez konta odczytywać i
wyszukiwać publiczne profile oraz audycje. `Ctrl+Shift+L` zapisuje źródło w
lokalnej Bibliotece AMC; nie zmienia konta Mixcloud i nie jest przedstawiane
jako obserwowanie w serwisie.

## Zakres etapu

- Publiczne wyszukiwanie profili i audycji Mixcloud w istniejącym oknie
  `Ctrl+F`, równolegle z Apple Podcasts, Spreakerem i YouTube.
- Jawne etykiety `profil Mixcloud` i `audycja Mixcloud`, bez odczytu kluczy API,
  nazw klas ani surowych rekordów.
- `Ctrl+N` przyjmujący publiczny adres profilu Mixcloud oraz publiczny adres
  pojedynczej audycji.
- Lokalna subskrypcja profilu przez `Ctrl+Shift+L`, trwałe odświeżanie jego
  publicznej listy i zachowanie odcinków nieobecnych w aktualnym oknie API.
- Enter na audycji używa jawnego, oficjalnego sposobu odtwarzania Mixcloud albo
  podaje uczciwe ograniczenie. API Mixcloud nie zwraca bezpośrednich strumieni
  audio i zabrania udawania ich zwykłym adresem odcinka.
- Ten sam katalog poleceń zasila skrót, menu, `Ctrl+F1`, pełną pomoc i paletę.

## Materiał do dokumentacji użytkownika

Zweryfikowane zachowanie: w sesji
`Podcasty i YouTube` naciśnij `Ctrl+F`, wpisz nazwę i wybierz wynik opisany jako
`profil Mixcloud` albo `audycja Mixcloud`. `Ctrl+Shift+L` na profilu doda go do
lokalnej Biblioteki AMC. `Ctrl+N` przyjmie również pełny publiczny adres
Mixcloud. Żadne konto Mixcloud ani Google nie jest potrzebne.

## Uzasadnienie i decyzje

- Źródłem danych jest wyłącznie udokumentowane API `https://api.mixcloud.com/`.
- Odczyt publicznych danych nie wymaga uwierzytelnienia; OAuth nie jest częścią
  tego etapu.
- Nie zapisujemy tokenów, nie wysyłamy historii odsłuchu i nie zmieniamy
  obserwowanych profili na koncie Mixcloud.
- SoundCloud pozostaje obsługiwany jako bezpośredni publiczny RSS, gdy
  użytkownik ma właściwy adres kanału.

## Testy i wynik

- Pełna regresja wxPython: `2105 passed, 113 skipped, 13 subtests passed`.
- Celowane testy nowych przepływów wxPython: `115 passed`.
- Test klienta Mixcloud z kontrolowanymi odpowiedziami HTTP: zaliczony.
- Próba rzeczywistego publicznego API Mixcloud: zaliczona; wyszukiwanie,
  odczyt profilu i odczyt audycji zwróciły poprawne dane bez logowania.
- Test domyślnego interwału odświeżania źródła Mixcloud: zaliczony.
- Build `AccessibleMediaController.LiteHost` w konfiguracji Debug: zaliczony,
  `0` ostrzeżeń i `0` błędów.
- `git diff --check` z regułą `cr-at-eol`: zaliczony.
- Kontrola działającego AMC Test przed promocją: widok `Nagrywane` pokazał
  `zero elementów`; wcześniejszy widok Radia i fokus zostały przywrócone.

## Znane ograniczenia

- Mixcloud nie udostępnia strumieni audio przez REST API. Oficjalnym sposobem
  odtwarzania jest widżet Mixcloud; nie wolno podstawiać adresu strony jako
  bezpośredniego pliku audio.
- Publiczne API dokumentuje profile i audycje, ale nie katalog playlist
  użytkownika równoważny playlistom YouTube. Interfejs nie będzie obiecywał
  funkcji, której API nie udostępnia.

## Wersja i commit

- Kod: gotowy w drzewie źródłowym.
- Testy: zaliczone; szczegóły powyżej.
- Build: build LiteHost Debug zaliczony; kandydat instalacyjny jeszcze
  niewykonany.
- Instalacja: niewykonana.
- Publikacja: niewykonana.
- Commit: do nadania przed promocją.
