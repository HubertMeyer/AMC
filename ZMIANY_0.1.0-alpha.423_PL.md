# AMC 0.1.0-alpha.423 — edycja audio i uporządkowany odtwarzacz

## Wycinanie i dopisywanie fragmentów

Usuwanie zaznaczonego fragmentu z oryginału ma teraz osobne, modalne okno.
Początkowy fokus znajduje się na bezpiecznym przycisku **Anuluj**. Po
rozpoczęciu operacji przycisk zmienia się w **Przerwij**, postęp pozostaje w tym
samym oknie, a fokus nie wraca w trakcie pracy do przycisku **Wstrzymaj** ani do
kontrolek odtwarzacza. Przerwanie zatrzymuje FFmpeg i pozostawia oryginał bez
podmiany.

W oknie dopisywania jedynym polem edycyjnym jest ścieżka istniejącego pliku
docelowego. Zasady operacji są zwykłym opisem i tekstem pomocy przycisku
**Dopisz**. Postęp obejmuje przygotowanie fragmentu, łączenie lub ponowne
kodowanie oraz sprawdzenie gotowego pliku, więc nie zatrzymuje się pozornie na
70 procentach. Anulowanie i błędy nie mogą pozostawić połowy podmienionego
pliku. O zachowaniu pełnej kopii po udanej operacji nadal decyduje ustawienie
**Zachowuj kopie po edycji**.

## Dwa techniczne elementy w odtwarzaczu TIDAL

Pola odczytywane jako dwie niezrozumiałe wartości nie były dwoma ustawieniami
AMC. Oficjalna biblioteka TIDAL tworzy wewnątrz ukrytego WebView dwa elementy
`video-one` i `video-two`, aby przygotować następny materiał i odtwarzać bez
przerw. Te szczegóły biblioteki przedostawały się do nawigacji klawiaturą i
czytnika ekranu.

AMC usuwa teraz cały dokument silnika odtwarzania z dostępnego interfejsu,
wyłącza Tab dla elementów multimedialnych oraz elementów dodanych później przez
bibliotekę i odbiera im przypadkowo przejęty fokus. Zabezpieczenie obejmuje
silniki TIDAL i Spotify. Tab w widoku odtwarzacza porusza się wyłącznie po
rzeczywistych kontrolkach AMC i pozostaje w tym widoku; Escape wraca do listy.
Home przechodzi na początek, End na koniec materiału, a w Radiu End wraca do
transmisji na żywo.

Stan głośności jest widoczny jako **Głośność: 100%** i ma dla NVDA pełną nazwę
z jednostką „procent”. Przyciski **Ciszej** i **Głośniej** podają bieżącą
wartość oraz zmianę o 5 punktów procentowych. Prędkość `1,00 razy` jest opisana
jako **normalna prędkość**; wartości mniejsze i większe mówią odpowiednio
„wolniej niż normalnie” albo „szybciej niż normalnie”.

## Apple Podcasts

Do pola adresu źródła można wkleić publiczną stronę podcastu z
`podcasts.apple.com`. AMC odczytuje identyfikator podcastu, korzysta z
publicznego katalogu Apple i otwiera udostępniony kanał RSS lub Atom. Nie
loguje się do konta Apple i nie obiecuje dostępu do materiałów dostępnych
wyłącznie w płatnej subskrypcji.

## Zakres sprawdzenia

Automatyczny test uruchamia rzeczywisty lokalny WebView2 oraz prawdziwy moduł
TIDAL bez konta. Potwierdza obecność obu elementów `video-one` i `video-two`,
ich usunięcie z Tab i drzewa dostępności, ochronę elementu dodanego już po
wczytaniu strony oraz dalszy start dźwięku po poleceniu hosta. Osobny test WPF
sprawdza zamkniętą kolejność Tab, brak pól kombi w widoku odtwarzacza i pełne
etykiety głośności oraz prędkości.

Testy edycji tworzą własne krótkie pliki. Sprawdzają FLAC, MP3, M4A i Ogg,
przerwanie obu okien bez zmiany plików, zajęty i tylko do odczytu cel, równoległe
dopisywanie oraz dostępne błędy uszkodzonego pliku i FFmpeg. Nie używają
prywatnych nagrań ani kont użytkownika.

Nie wykonano jeszcze ręcznego odsłuchu tej wersji z żywym NVDA na własnym
nagraniu użytkownika. Taką próbę należy wykonać po instalacji alfa423; testy
automatyczne nie są deklaracją jakości każdego pliku i kodeka.
