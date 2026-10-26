# AMC13 — regresja End w Time Shifcie radia

Data audytu: 18 października 2026 r.

Tryb pracy: poziom A. Nie kompilowano i nie uruchamiano AMC.

## Zgłoszone zachowanie

- `Home` przechodzi do początku dostępnego Time Shiftu.
- przewijanie strzałkami i zmiana tempa działają;
- `End` nie wraca na żywo i pojawia się komunikat związany z nieznanym czasem odtwarzania;
- najważniejszy błąd: w otwartym odtwarzaczu radia `End` nie wraca z Time Shiftu na żywo;
- procentowa nawigacja i zapisywanie fragmentów są osobnymi pomysłami rozwojowymi, nie częścią tej regresji.

## Ustalenia ze źródła

### End

W bieżącym źródle istnieje właściwe polecenie `RadioJumpLive`. Jego wykonanie:

1. wywołuje `RadioMediaOutput.JumpToLive()`;
2. ustawia odczyt blisko końca pierścienia z małym zapasem bezpieczeństwa;
3. przywraca tempo `1,00x`;
4. oznajmia „Na żywo”;
5. nie korzysta z czasu trwania stacji.

Obsługa klawiatury ma też specjalny warunek `End` w odtwarzaczu radia przed ogólnym `TrackEnd`. Zgłoszony wynik przeczy więc zamierzonej drodze źródłowej. Najbardziej prawdopodobne są dwie klasy przyczyn:

- uruchomiona kompilacja nie odpowiada bieżącemu źródłu;
- określony stan fokusa albo inna warstwa wejścia omija specjalną drogę i uruchamia ogólne polecenie końca materiału.

W ramach etapu A przygotowano test, który wysyła `End` przez rzeczywiste `MainWindow`, sprawdza obsłużone zdarzenie, końcowe `BehindLive` i powrót do tempa `1,00x`. Ta sama próba sprawdza, że `NVDA+End` pozostaje nieobsłużone przez AMC i nie zmienia pozycji Time Shiftu. Test nie został jeszcze uruchomiony.

### Osobny pomysł: skok procentowy

W źródle cyfry `0–9` mają wybierać `0–90%` aktualnego okna bufora. Ta funkcja istnieje wraz z testami pierścienia, zawinięcia, pauzy i tempa. Trzeba ją później zweryfikować w tej samej próbie na żywo, ale nie mieszać z naprawą `End`.

`Ctrl+Shift+J` jest ogólnym oknem „Skocz do procentu” dla zwykłych materiałów. Został błędnie włączony do pierwszej interpretacji zgłoszenia i nie należy do zakresu AMC13.

### Zaznaczanie i zapis fragmentu

Obecny edytor fragmentów działa tylko na lokalnym pliku lub pobranym odcinku. Wymaga stabilnej ścieżki, znanej długości i pliku wejściowego dla FFmpeg.

Time Shift przechowuje natomiast zdekodowane audio PCM w pierścieniu pamięciowym albo w pliku mapowanym, który:

- nie jest samodzielnym plikiem multimedialnym;
- może zawinąć się i nadpisać najstarsze dane;
- jest nadal zapisywany podczas eksportu;
- znika po zamknięciu toru radia.

Dlatego funkcji nie należy dopinać do obecnego `TryGetLocalClipContext`. Potrzebny jest osobny kontekst fragmentu Time Shiftu oparty na niezmiennych pozycjach pierścienia oraz identyfikatorze generacji stacji. Eksport powinien atomowo skopiować zaznaczony zakres do migawki, a dopiero potem zakodować go do wybranego formatu. Operacja „usuń fragment z oryginału” nie ma tu sensu i pozostanie niedostępna.

## Plan naprawy regresji

1. Dodać jeden resolver `Home`/`End` dla Time Shiftu wywoływany na poziomie okna, przed ogólnym transportem.
2. Dodać test pełnej drogi `End` dla kilku stanów fokusa oraz ochrony `NVDA+End`.
3. Potwierdzić, że wykonanie `RadioJumpLive` nie korzysta z długości stacji, przywraca tempo `1,00x` i oznajmia „Na żywo”.
4. Ujednolicić pomoc `Ctrl+F1`, paletę i menu.

## Osobny przyszły etap — zaznaczenie i zapis kopii fragmentu Time Shiftu

To nie jest „wycinanie na żywo” ani usuwanie czegokolwiek z odbieranej transmisji. Użytkownik zaznacza początek i koniec materiału, który nadal istnieje w buforze Time Shiftu, a AMC zapisuje kopię tego zakresu do nowego, zwykłego pliku. Odbiór stacji i pierścień Time Shiftu działają dalej bez zmian.

1. Dodać migawkę dowolnego zakresu pierścienia bez zatrzymywania odbioru.
2. Przechowywać początek i koniec wraz z generacją stacji oraz sprawdzać, czy dane nie zostały nadpisane.
3. Użyć `I` i `O` do granic, `Shift+I/O` oraz `Alt+Page Up/Down` do nawigacji po granicach.
4. Zapisywać kopię fragmentu do nowego pliku przez istniejący bezpieczny mechanizm kodera i pliku tymczasowego.
5. Nie oferować usunięcia fragmentu z bufora, przesuwania materiału, dopisywania do transmisji ani innej destrukcyjnej edycji. Time Shift pozostaje źródłem tylko do odczytu.

## Testy wymagane przed odbiorem

- bufor częściowo wypełniony i zawinięty;
- `Home` i `End` w otwartym odtwarzaczu radia;
- tempo `0,75x`, `1,00x`, `1,25x` i `1,50x` oraz pauza;
- fokus na przycisku, panelu, oknie, menu i powrót po Anuluj;
- `NVDA+End` pozostawione czytnikowi ekranu;
- zmiana stacji podczas zaznaczenia i eksportu;
- nadpisanie początku zaznaczenia przez pierścień;
- poprawna długość i integralność gotowego pliku;
- brak zatrzymania odbioru i brak uszkodzonego pliku po błędzie kodera.

## Stan

Zakres skorygowano: AMC13 dotyczy `End` w otwartym odtwarzaczu radia. Audyt źródłowy zakończony i przygotowano test regresji `End`/`NVDA+End` w pełnej drodze okna. Nie zmieniano jeszcze wykonania Time Shiftu; testu ani aplikacji nie uruchamiano.
