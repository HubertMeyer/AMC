# AMC 0.1.0-alpha.425 — roboczy opis pierwszego wydania publicznego

> Projekt do korekty użytkownika. Nie jest opublikowanym opisem wydania.
> Numer wersji zostanie potwierdzony dopiero po zbudowaniu i ręcznym odbiorze
> dokładnie tego instalatora.

## Co zawiera publiczny AMC

- sesje `Pliki lokalne`, `Radio`, `Podcasty i YouTube` oraz `WiiM`;
- klawiaturowy Menedżer sesji pod `Ctrl+Shift+S`, zwarta numeracja sesji
  `Ctrl+1–9` i wspólne nazwy poleceń w menu, pomocy `Ctrl+F1`, pełnej pomocy
  klawiatury oraz palecie `Ctrl+Shift+K`;
- dostępne listy, menu kontekstowe i komunikaty NVDA bez technicznych nazw klas,
  identyfikatorów i surowych wartości modelu;
- lokalne pliki, kolejkę, playlisty AMC, zakładki szybkie i nazwane, rozdziały
  z plików oraz historię nawigacji;
- radio internetowe, nagrywanie ręczne i harmonogramowe, krótkie listy
  `Alt+R` i `Alt+Shift+R` oraz szczegóły pliku pod lewą strzałką;
- Time Shift radia: `Home` przechodzi na początek bufora, `End` wraca do
  transmisji na żywo i normalnego tempa, a cyfry `0–9` przechodzą do 0–90%
  aktualnego bufora;
- Podcasty i YouTube z Biblioteką, wyszukiwaniem, sortowaniem źródeł i
  pobieraniem obsługiwanych materiałów;
- sterowanie WiiM bez wymagania aplikacji producenta;
- kontekstowe `Ctrl+F5`: Foldery Biblioteki w Plikach lokalnych, odświeżenie
  stacji w Radiu, odświeżenie Podcastów i YouTube oraz urządzeń WiiM;
- poprawne rozróżnienie `Ctrl+0` i presetu `Ctrl+Shift+0` także na natywnych
  listach Windows;
- opcjonalne i odwracalne skróty instalatora oraz polecenia powłoki, bez
  samoczynnego przejmowania domyślnych aplikacji;
- formularz `Zgłoś błąd lub sugestię…` z pełnym podglądem, domyślnie
  wyłączonym logiem, redakcją prywatnych danych oraz lokalnym kopiowaniem i
  zapisem raportu.

## Oddzielenie od AMC Test

Publiczny AMC i prywatny AMC Test mają osobne instalacje, procesy, kanały
aktualizacji, ustawienia interfejsu, pamięć podręczną, logi i poświadczenia.
Mogą działać równolegle. Publiczna instalacja nie korzysta z żywych baz ani
tokenów AMC Test. Dane wspólne można przenieść wyłącznie kontrolowaną,
wersjonowaną migawką AMC Test → AMC; nie obejmuje ona nagrywania w toku ani
poświadczeń usług.

## Czego ta wersja publiczna nie zawiera

- Spotify, TIDAL ani Sonosa — ich moduły interfejsu i prywatny host Spotify nie
  znajdują się w paczce publicznej;
- logowania do konta YouTube ani synchronizacji subskrypcji;
- Portable i ARM64;
- automatycznego wyświetlania wideo ani pełnoekranowego odtwarzacza wideo;
- eksportu zaznaczonego fragmentu Time Shiftu;
- działającej wysyłki Sygnalisty do GitHuba, dopóki końcowy Worker HTTPS nie
  zostanie wdrożony i odebrany. Bez endpointu formularz uczciwie pozostaje
  lokalny i nie pokazuje przycisku wysyłania.

## Instalacja i bezpieczeństwo

- Instalator jest przeznaczony dla Windows x64.
- Przed podmianą sprawdzany jest profil paczki, kompletność manifestu i SHA-256
  każdego kontrolowanego pliku.
- Instalator nie wymusza zamknięcia AMC podczas nagrywania. Aktualizację należy
  wykonywać dopiero po zakończeniu nagrywania ręcznego i harmonogramowego.
- Pierwsze wydanie może nie mieć podpisu cyfrowego, dlatego Windows może
  pokazać ostrzeżenie reputacyjne. SHA-256 instalatora będzie podane w opisie
  GitHub Release i w osobnym pliku integralności.

## Status odbioru

- Kod, testy, kompilacja, instalacja, ręczny test NVDA i publikacja są osobnymi
  etapami.
- Opis wolno opublikować dopiero po zbudowaniu końcowego kandydata, bezpiecznej
  instalacji obok AMC Test, potwierdzeniu dwóch niezależnych hostów i ogólnym
  teście użytkownika.
- GitHub Release musi po wysłaniu zwrócić właściwy tag, nazwę, rozmiar i stan
  instalatora, a jego opis musi zawierać zgodną sumę SHA-256.
