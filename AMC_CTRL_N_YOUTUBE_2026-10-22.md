# AMC Test — import kanału YouTube przez Ctrl+N

## Zakres i korekta kontekstu

- Data: 2026-10-22.
- Dotyczy wyłącznie głównego repozytorium i wariantu roboczego **AMC Test** w `D:\Projekty Codex\Accessible Multimedia Controller`.
- Korekta użytkownika z 2026-10-22 zastępuje wcześniejsze, błędne utożsamienie badanego programu z inną kompilacją lub wydaniem publicznym. W tym zadaniu nie instalowano ani nie uruchamiano innej wersji AMC.
- Późniejsza korekta użytkownika z 2026-10-22 zastępuje pierwszą decyzję o dwuetapowej obsłudze **Sprawdź → Dodaj**. Obowiązującym zachowaniem jest jedno **Dodaj**, które samo sprawdza adres i po powodzeniu kontynuuje import.
- Sprawdzony adres: `https://www.youtube.com/@WieniawskiSociety`.

## Stan przed zmianą i przyczyna

Polecenie **Plik → Dodaj podcast lub kanał YouTube**, skrót **Ctrl+N**, otwierało właściwe okno, a backend poprawnie rozpoznawał wskazany kanał YouTube. Problem leżał w obsłudze klawisza Enter:

- pierwotnie przycisk **Dodaj** był oznaczony jako domyślny, chociaż przed sprawdzeniem adresu pozostawał wyłączony;
- pierwotnie przycisk **Sprawdź** nie był przyciskiem domyślnym, więc Enter w polu adresu próbował uruchomić wyłączone **Dodaj** i nic nie robił;
- pierwsza poprawka rozdzieliła sprawdzanie i zatwierdzenie na dwa kolejne naciśnięcia Enter, lecz użytkownik słusznie wskazał, że sprawdzanie jest tylko techniczną częścią dodawania, a nie osobną decyzją;
- istniejące testy nie obejmowały pełnego przebiegu `adres → jeden Enter → sprawdzenie → dodanie → trwały zapis → ponowne otwarcie`;
- pomoc i paleta poleceń opisywały głównie RSS/Atom i nie wymieniały wprost kanału ani playlisty YouTube.

Kanał został poprawnie rozpoznany przez używany przez AMC mechanizm YouTube jako identyfikator `UCpFEKtbJxKnsOcraylnuNsA`, z adresem roboczym `https://www.youtube.com/%40WieniawskiSociety/videos`. W bazie użytkownika nie było jednak tego adresu, identyfikatora ani nazwy, co potwierdziło, że wcześniejsza próba nie została utrwalona.

## Zachowanie po zmianie

1. Po otwarciu okna fokus znajduje się w polu adresu.
2. W oknie jest jedno domyślne **Dodaj**; osobny przycisk **Sprawdź** został usunięty.
3. Enter uruchamia jednoetapową operację: AMC sprawdza adres, pobiera informacje i po powodzeniu zamyka okno z wynikiem gotowym do dodania.
4. Na czas oczekiwania **Dodaj**, pole adresu i pole nazwy są wyłączone, a przycisk przestaje być domyślny. Drugi Enter nie uruchamia drugiego importu.
5. Asertywny region stanu przekazuje NVDA komunikat `Sprawdzanie adresu i dodawanie źródła…`.
6. Nieprawidłowy adres albo błąd pobierania pozostawia okno otwarte, ponownie włącza **Dodaj**, przenosi fokus do pola adresu i zaznacza cały tekst do poprawienia.
7. Po dodaniu AMC czeka na rzeczywisty zapis kolejki stanu. Dopiero po jego zakończeniu ogłasza `Zapisano w Bibliotece`. W przypadku błędu lub przekroczenia limitu czasu informuje, że element jest widoczny tylko w bieżącej sesji i nie został zapisany trwale.
8. Wspólny katalog poleceń, pełna pomoc klawiatury i paleta poleceń używają opisu wymieniającego RSS/Atom oraz kanał lub playlistę YouTube.

## Zmienione pliki źródłowe

- `src/AccessibleMediaController.Windows/PodcastSourceWindow.xaml`
- `src/AccessibleMediaController.Windows/PodcastSourceWindow.xaml.cs`
- `src/AccessibleMediaController.Windows/MainWindow.xaml.cs`
- `src/AccessibleMediaController.Core/Commands/CommandCatalog.cs`
- `tests/AccessibleMediaController.Windows.SmokeTests/PodcastSourceWindowTests.cs`
- `tests/AccessibleMediaController.Windows.SmokeTests/Program.cs`

## Test dostępności i trwałości

Nowy test WPF działa na wątku STA i sprawdza:

- początkowy fokus, jedno domyślne **Dodaj**, brak osobnego **Sprawdź** oraz asertywny region stanu;
- błąd składni adresu i błąd sieci: komunikat, zaznaczenie adresu, zachowany fokus i gotowość do ponownej próby;
- blokadę pól i przycisku podczas oczekiwania oraz ochronę przed drugim importem po ponownym Enter;
- jednoetapowe sprawdzenie i zatwierdzenie poprawnego kanału YouTube;
- ponowne otwarcie czystego okna;
- zapis do odizolowanej, tymczasowej bazy i odczyt po ponownym utworzeniu magazynu konfiguracji;
- zgodność nazwy i skrótu Ctrl+N w katalogu poleceń, pomocy i palecie poleceń.

Test nie modyfikuje biblioteki użytkownika. Tymczasowy katalog testowy został usunięty po zakończeniu.

## Rzeczywiste wyniki

- Kompilacja ukierunkowanego projektu testowego w konfiguracji Release: **sukces, 0 ostrzeżeń, 0 błędów**.
- Końcowy test ukierunkowany `--podcast-source-window`: **sukces** — `OK: Ctrl+N Podcasty i YouTube — jeden Enter sprawdza, dodaje i zapisuje`.
- Pełne `build.ps1`, uruchomione przed późniejszym uproszczeniem przycisku: kompilacja całego rozwiązania zakończona powodzeniem, a ówczesna wersja testu importu przeszła również w pełnym zestawie. Po końcowym uproszczeniu ponownie zbudowano projekt Windows i uruchomiono test ukierunkowany.
- Pełna bramka testowa: **nie jest zielona** — 7 z 198 innych testów nie przeszło. Dotyczyły: trzech scenariuszy Sonos, Schowka, cyfr TimeShift, F11 oraz środowiska testu instalatora (`Get-FileHash` niedostępne w uruchomionym procesie). Te awarie nie wystąpiły w kodzie importu podcastów/YouTube i nie zostały w tym zadaniu naprawione.

## Ograniczenia i stan wydania

- Zmiany są obecne w źródłach AMC Test i w lokalnej kompilacji Release.
- Nie wykonano instalacji, publikacji wydania ani podmiany uruchomionej aplikacji.
- Nie wykonywano ręcznego odsłuchu prawdziwym NVDA; zachowanie UI Automation, fokusa, przycisków domyślnych i regionu komunikatów sprawdził automatyczny test WPF.
- Bazowy commit repozytorium podczas pracy: `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`.
- Zmiany z tego zadania są niezatwierdzone. Repozytorium zawierało wcześniej liczne inne, niezwiązane zmiany i pliki robocze; nie zostały nadpisane ani usunięte.

## Robocza instrukcja dla użytkownika

1. W sesji **Podcasty i YouTube** wybierz **Plik → Dodaj podcast lub kanał YouTube** albo naciśnij **Ctrl+N**.
2. Wpisz lub wklej pełny adres. Opcjonalnie podaj własną nazwę.
3. Naciśnij Enter. AMC sam sprawdzi adres i doda źródło; nie trzeba wybierać osobnego **Sprawdź**.
4. Poczekaj na komunikat `Zapisano w Bibliotece`. Dopiero on potwierdza trwały zapis.
5. Jeśli adres jest niepoprawny albo źródło jest niedostępne, popraw zaznaczony adres i ponownie naciśnij Enter.

## Roboczy wpis do changelogu

- Uproszczono import podcastów oraz kanałów i playlist YouTube przez Ctrl+N: jedno naciśnięcie Enter sprawdza adres, dodaje źródło i potwierdza trwały zapis. Usunięto zbędny osobny krok **Sprawdź**, dodano ochronę przed podwójnym Enter oraz dostępne komunikaty i powrót fokusa po błędzie.

