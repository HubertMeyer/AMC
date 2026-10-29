# AMC Test 0.1.0-alpha.444 — projekt opisu zmian i odbioru

To jest roboczy tekst do korekty i zatwierdzenia przez użytkownika. Wydanie
GitHub zawiera krótszy, faktyczny opis oraz sumę kontrolną instalatora.

## Zmiany

- W sesji Podcasty i YouTube można dodać kilka publicznych stron Facebooka
  przez `Ctrl+N`, odświeżyć wybraną przez `F5` albo wszystkie źródła przez
  `Ctrl+F5`. `Ctrl+I` otwiera skrzynkę nowo odkrytych filmów.
- Pojedyncze publiczne filmy Facebooka i Instagrama można dodać tym samym
  formularzem. Enter odtwarza dźwięk w AMC, `Ctrl+D` pobiera MP3,
  `Ctrl+Shift+D` pobiera wideo, a `Ctrl+S` otwiera Zapisz jako dla jednego filmu.
- Przełączenie języka z angielskiego na polski po zapisie Ustawień nie powinno
  przerywać przebudowy menu. Własne teksty komunikatów pozostają bez zmian.
  Przycisk Anuluj ma jawną polską etykietę i nazwę dostępności.

## Odbiór po aktualizacji

1. W Ustawieniach zmień język z angielskiego na polski i sprawdź z NVDA menu
   Pliki, przycisk Anuluj oraz zachowanie własnych tekstów komunikatów.
2. W Podcastach i YouTube dodaj `https://www.facebook.com/buremisie/`,
   wybierz tę stronę i naciśnij `F5`. Sprawdź listę filmów oraz `Ctrl+I`.
3. Jeśli film ma dźwięk i jest publicznie dostępny, sprawdź Enter oraz
   `Ctrl+D` po uprzednim sprawdzeniu składników FFmpeg i yt-dlp w Pomocy.

## Ograniczenia

Lista strony Facebooka pochodzi z nieudokumentowanego mechanizmu i może być
niepełna lub niedostępna. W teście na żywo sprawdzono jedną stronę i jeden
film. Profili osobistych Facebooka ani profili Instagrama nie można
subskrybować. Interfejs AMC odtwarza ścieżkę dźwiękową, bez obrazu. Nowe
wydanie opublikowano, lecz nie zainstalowano lokalnie i nie wykonano odbioru
NVDA ani rzeczywistego pobrania MP3.
