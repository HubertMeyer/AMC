# AMC Python — przekazanie prac na niedzielę

Ten plik jest krótkim punktem startowym po pracach zakończonych 14 października
2026 r. Szczegółowy stan pozostaje w `AMC_PYTHON_STAN_2026-10-10_PL.md`.

## Właściwy projekt i instalacja

- Aktywny projekt: `D:\Projekty Codex\AMC - integracja wxPython`.
- Użytkowa instalacja: `D:\Projekty Codex\AMC Python\AMC.exe`.
- Stary interfejs WPF w `D:\Projekty Codex\Accessible Multimedia Controller`
  jest wycofany z bieżących prac. Można go czytać jako materiał historyczny,
  ale nie należy w nim wdrażać poprawek ani go uruchamiać zamiast AMC Python.
- Zmiany pozostają lokalne. Nie wysyłać ich do GitHuba bez nowej, jednoznacznej
  decyzji użytkownika dotyczącej konkretnego stanu.

## Ostatnia odebrana technicznie wersja

- commit źródłowy: `c47d5e250ed51527cf3645a6b0707c1fb7b499c9`;
- kompilacja: `2026.10.14-c47d5e250ed51527cf3645a6b0707c1fb7b499c9-3ee86c2b`;
- tytuł uruchomionego okna: `AMC Python — 14.10.2026, 20:09`;
- pełny przebieg: 1546 testów zaliczonych, 110 pominiętych historycznych oraz
  11 zaliczonych podtestów;
- osobny zestaw testów launchera i aktualizatora: 13 z 13 zaliczonych;
- rozwiązanie C#: 0 ostrzeżeń i 0 błędów;
- zweryfikowany pakiet: 602 pliki;
- uruchomione procesy pochodzą z `D:\Projekty Codex\AMC Python`; stary proces
  WPF nie był uruchomiony;
- katalog źródeł był czysty poza lokalnymi `.test-output` i `.test-tmp`.

Dokładny rachunek ostatniej instalacji zapisuje lokalny plik
`.test-output\LAST_TEST_BUILD.json`. Katalog `.test-output` jest zapleczem
testowym, a nie drugim sposobem uruchamiania programu.

## Co naprawiono 14 października

1. Edycja plików audio: wycinanie i dopisywanie korzystają z właściwego
   kontekstu pliku; poprawiono zakończenie operacji, postęp i obsługę końca
   materiału. Dodano testy dokładnego wycięcia końcówki WAV.
2. Odtwarzacz: uporządkowano osobne kontrolki głośności i tempa, ich etykiety
   dostępności oraz kierunek klawiszy strzałek, Home i End.
3. WiiM: przywrócono listę Biblioteki po wejściu do odtwarzacza i usunięto
   zbędnie czytane słowo „źródło” z kategorii.
4. `Alt+D`: opis podcastu zaczyna się od właściwej treści, bez odczytywania
   technicznego lub powtarzanego nagłówka dialogu.
5. Historia nagrywania: operacje na rzeczywistym pliku aktualizują ścieżkę lub
   usuwają ukończony wpis, jeżeli pliku już nie ma. Wpisy nieudane pozostają
   jako diagnostyka.
6. `Ctrl+Shift+C`: kopiuje adres własnego strumienia WiiM albo Sonos. Ulubione
   Sonos nie udają adresu strumienia, gdy API udostępnia tylko identyfikator.
7. `Shift+F2`: usunięto wyścig powodowany przez Enter zatwierdzający dialog.
   Ten sam Enter nie może już wejść do odtwarzacza i zająć pliku przed
   zakończeniem zmiany nazwy. Sukces jest zgłaszany dopiero po potwierdzeniu,
   że nowa ścieżka rzeczywiście istnieje. Test GUI zmienia nazwę prawdziwego
   pliku tymczasowego.

Najważniejsze commity, od najnowszego:

- `c47d5e25` — aktualizator rozpoznaje uproszczony tytuł okna i potrafi
  bezpiecznie zamknąć bieżącą wersję przed podmianą;
- `4168946c` — trwały wybór urządzenia WiiM oraz dopuszczenie kopiowania
  adresu w sesjach WiiM i Sonos;
- `c525e8c0` — naprawa zmiany nazwy pliku po `Shift+F2`;
- `c843f6a5` — kopiowanie adresów strumieni WiiM i Sonos;
- `442bc858` — operacje na plikach historii nagrań;
- `4fdaae76` — Biblioteka WiiM i kierunki głośności;
- `d7506703` — edycja plików i dostępność odtwarzacza.

## Krótki odbiór na żywo przed Spotify

Testy automatyczne przeszły, ale w niedzielę warto zacząć od krótkiego odbioru
z NVDA na niepotrzebnych plikach:

1. `Shift+F2` w Plikach lokalnych i Historii nagrywania: po Enter nazwa ma się
   rzeczywiście zmienić, lista ma zachować fokus, a odtwarzacz nie może się
   sam otworzyć.
2. `Shift+Delete`: plik ma trafić do Kosza, a ukończony wpis historii ma
   zniknąć po odświeżeniu. Nieudane nagrania mogą pozostać jako diagnostyka.
3. Wycięcie końca materiału: dla pliku 12-minutowego usunięcie zakresu
   9:00–12:00 ma pozostawić dokładnie około 9 minut, bez dopisanej końcówki.
4. Dopisanie fragmentu do pliku: operacja ma się zakończyć, a okno postępu ma
   zniknąć; nie może pozostać bez końca.
5. Pierwsze wczytanie własnych strumieni WiiM i Sonos: sprawdzić kolejność
   przed użyciem `Alt+3` i po ponownym otwarciu.
6. Sprawdzić z kilku widoków globalne `Alt+R` i `Alt+Shift+R`.

Przed zamknięciem lub aktualizacją AMC nadal trzeba potwierdzić, że nie rośnie
żaden plik `.amc-partial` i że nie trwa nagrywanie.

## Następny główny blok: Spotify

Przed równoległymi pracami wykonać jako pierwsze zadanie
`ZADANIE_NIEDZIELA_PRZYGOTOWANIE_ZALEZNOSCI_PL.md`. Audyt z 14 października
potwierdził .NET, Python, Node, pnpm i WebView2, ale wykazał brak lokalnego
toolchainu Rust i narzędzi MSVC potrzebnych do przebudowania hosta Librespot.
Zadanie przygotuje trwały wspólny cache na dysku D i próbę pracy bez sieci.

Po przygotowaniu zależności i powyższym krótkim odbiorze wracamy do Spotify
w nowym AMC Python. Nie przenosimy funkcji do starego WPF. Pierwszy etap
powinien być inwentaryzacją
bez zapisu: przeczytać ten plik, `AMC_PYTHON_STAN_2026-10-10_PL.md` oraz
`SPOTIFY-LOSSLESS-I-MONITORING.md`, sprawdzić istniejące adaptery i testy, a
następnie ustalić zakres sesji Spotify oraz kryteria odbioru z NVDA.

Zakres należy rozdzielić co najmniej na: logowanie i stan konta, katalog i
bibliotekę, wyszukiwanie, przekazanie odtwarzania do właściwego silnika lub
oficjalnego klienta, sortowanie i nawigację kontekstową oraz dostępne etykiety
wszystkich list i pól kombi. Nie wykonywać logowania ani zmian na koncie bez
bieżącej, świadomej czynności użytkownika.

### Wzorzec interfejsu Spotify

Logikę widoków i obsługi klawiatury Spotify należy budować na rozwiązaniach,
które działają już w sesji TIDAL nowego AMC Python: wspólnym modelu list,
Biblioteki, wyszukiwania, sortowania, relacji, kolejki, presetów i odtwarzacza.
Stare AMC WPF oraz jego Librespot są wyłącznie materiałem technicznym dla API,
autoryzacji, silnika audio i istniejących ograniczeń. Nie przenosić z niego
zachowania interfejsu.

Minimalny kontrakt odbioru Spotify:

- Enter wykonuje jedno działanie po jednym naciśnięciu; nie wymaga drugiego
  Entera i nie przepuszcza klawisza do nowo otwartego widoku;
- lewa strzałka podaje raz zwięzłą, prawidłową informację o bieżącym elemencie
  lub odtwarzaniu, bez dwóch komunikatów i danych technicznych;
- prawa strzałka otwiera właściwe menu relacji lub czynności kontekstowych
  zgodne z nowym TIDAL-em i nie odczytuje równolegle starego opisu;
- fokus po Enter, Escape, zapisaniu i anulowaniu wraca do zamierzonego wiersza;
- każda lista i pole kombi ma jawny tekst użytkowy dla NVDA; identyfikatory,
  rekordy i wartości modelu nie mogą być wypowiadane;
- odtwarzacz Spotify ma używać wspólnych, już uporządkowanych kontrolek tempa,
  głośności i transportu AMC Python.

Użytkownik będzie jeszcze obserwował bieżącą wersję w czwartek, piątek i
sobotę pod kątem samoczynnie pojawiających się okien. Nowe zgłoszenie w tej
sprawie ma pierwszeństwo przed instalacją kolejnego wydania, ale nie blokuje
przygotowania zależności i analizy Spotify.

## Etap przed udostępnieniem programu testerom

Po ukończeniu głównych funkcji, przed pierwszym wydaniem dla innych testerów,
wykonać osobny plan `PLAN_WYDANIA_GITHUB_AMC_PYTHON_PL.md`. Obejmuje on jeden
spójny proces wydań GitHub, aktualizator i moduł zgłaszania błędów, zamknięty
zestaw zależności użytkowych, dokumentację, skróty klawiszowe oraz odbiór na
czystej maszynie. To jest późniejszy etap; obecna zgoda użytkownika nie
obejmuje jeszcze publikacji repozytorium ani wydania na GitHubie.

## Jak bezpiecznie prowadzić kilka zadań równolegle

Równoległość jest bezpieczna, jeżeli każde zadanie zmieniające kod ma osobny
worktree i własną gałąź. Jedno zadanie integracyjne jest właścicielem głównego
katalogu, instalacji `D:\Projekty Codex\AMC Python` i końcowego wydania.

- Równolegle wykonywać analizę, testy i niezależne moduły.
- Zmiany w tych samych plikach, szczególnie głównym oknie, skrótach i protokole
  hosta, wykonywać kolejno albo po wcześniejszym podziale odpowiedzialności.
- Zadania robocze mają kończyć się lokalnym commitem, podaniem hasha i wyników
  testów. Nie powinny same instalować, uruchamiać aktualizatora ani publikować.
- Zadanie integracyjne przegląda i scala commity po kolei, rozwiązuje konflikty,
  uruchamia pełny zestaw testów, sprawdza nagrywanie i tylko raz buduje oraz
  instaluje nową wersję.
- Praktycznie najlepiej prowadzić jednocześnie dwa lub trzy niezależne zadania,
  nie kilka implementacji dotykających wspólnego interfejsu.

Przykładowe polecenie dla zadania roboczego:

> Pracuj wyłącznie w nowym AMC Python, w osobnym worktree i osobnej gałęzi.
> Nie modyfikuj starego WPF, nie instaluj programu i nie publikuj. Zakończ
> lokalnym commitem oraz raportem: zmienione pliki, testy, ryzyka i hash.

Przykładowy podział pierwszego dnia Spotify:

1. najpierw jedno zadanie przygotowania zależności, nie równolegle z kodem;
2. zadanie tylko do odczytu: inwentaryzacja obecnego kodu i braków Spotify;
3. osobne zadanie: kontrakt dostępności i scenariusze testów NVDA;
4. implementacja dopiero po uzgodnieniu wyników punktów 2–3;
5. na końcu jedno zadanie integracyjne i jedna instalacja.
