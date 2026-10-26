# AMC Test 0.1.0-alpha.425 — co sprawdzić

## Najpierw zwykłe uruchomienie

1. Uruchom AMC Test ze skrótu **Accessible Multimedia Controller**.
2. Otwórz Menedżer sesji przez `Ctrl+Shift+S` lub `Ctrl+0`.
3. Upewnij się, że dotychczasowe sesje i kolejność są zachowane.

## Odtwarzanie losowe

1. W Plikach lokalnych uruchom album lub listę z kilkoma utworami.
2. W odtwarzaczu naciśnij `R`. NVDA powinien powiedzieć, że odtwarzanie losowe
   jest włączone.
3. Sprawdź następny utwór, potem wyłącz losowanie ponownym `R`.
4. Powtórz na podcaście lub materiale YouTube i w Spotify.
5. Sprawdź tę samą opcję w menu Odtwarzanie oraz menu kontekstowym odtwarzacza.

## YouTube — konto Google

Do próby potrzebny jest Client ID przygotowany według
`INSTRUKCJA_PRZYGOTOWANIA_YOUTUBE_GOOGLE_PL.md`.

1. Wejdź do sesji Podcasty i YouTube i naciśnij `Ctrl+F5`.
2. Wklej Client ID, zapisz go i wybierz **Zaloguj kontem Google**.
3. Po powrocie wybierz **Importuj subskrypcje i playlisty**.
4. Sprawdź Bibliotekę przez `Ctrl+L`, otwieranie kanału lub playlisty Enterem i
   odtwarzanie publicznego materiału.
5. `F5` nadal odświeża bieżące źródło, a menu Plik ma osobne **Odśwież
   wszystkie źródła**.

## Apple Music — prototyp

Do próby potrzebny jest gotowy JWT przygotowany według
`INSTRUKCJA_PRZYGOTOWANIA_APPLE_MUSIC_PL.md`. Nie przekazuj pliku `.p8`.

1. Wejdź do sesji Apple Music i naciśnij `Ctrl+F5`.
2. Wklej developer token, wybierz katalog `pl`, zapisz i sprawdź token.
3. Wybierz **Zaloguj kontem Apple**, a następnie **Pobierz bibliotekę**.
4. Sprawdź `Ctrl+L`, `Ctrl+P`, `Ctrl+F`, Enter na albumie i utworze oraz
   strzałkę w prawo na albumie i wykonawcy.
5. Sprawdź Spację, Page Up, Page Down, strzałki czasu i głośność w odtwarzaczu.
6. Sprawdź dodanie do Biblioteki `Ctrl+Shift+L` i ulubionych `Ctrl+Shift+U`.

## Zgłaszanie wyniku

Podaj dokładny komunikat NVDA, nazwę sesji, użyty skrót i to, czy problem
pojawił się na liście czy w odtwarzaczu. Nie przesyłaj tokenów, haseł, plików
`.p8`, plików `client_secret*.json` ani danych logowania.

To instrukcja lokalnej próby AMC Test, nie publicznego wydania.
