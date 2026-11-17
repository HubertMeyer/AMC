# Odbiór follow-up Spotify — 17 listopada 2026

## Zakres i granice

Odbiór wykonano na `9b773694dba8e61ae527664ae195d194453ab211`, w izolowanym worktree `hubert-spotify-followup`. Nie użyto konta Spotify, tokenów użytkownika ani odtwarzania. Nie zmieniano detekcji końca utworu, kolejki AMC, adaptera Connect/Soloist ani kodu odtwarzania z #11.

Wprowadzono tylko doprecyzowanie komunikatu dla niedostępnej playlisty. Nie diagnozuje ono przyczyny pojedynczego braku dostępu: informuje o fakcie niedostępności dla bieżącego konta i o znanym ograniczeniu trybu deweloperskiego, które obejmuje między innymi playlisty innych osób.

## Uzasadniona zmiana

`LiteSpotifyCatalogContract.CreateContainerResult` zwraca dla niedostępnej playlisty:

> Spotify nie udostępnił zawartości tej playlisty temu kontu. W trybie deweloperskim dotyczy to między innymi playlist innych osób.

Pozostałe kontenery zachowują wcześniejszy ogólny komunikat. To nie przypisuje 403 wyłącznie cudzej playliście; ścieżka API łączyła już 403 i 404 w stan „zawartość niedostępna”.

## Dowody

### Nowy kontrakt komunikatu i rzeczywisty transport bez konta

1. RED: `AccessibleMediaController.LiteHost.ProtocolTests --spotify-catalog` zakończył się niepowodzeniem, ponieważ wymagany komunikat playlisty nie istniał.
2. GREEN: po minimalnej zmianie ten sam zestaw zakończył się `Wszystkie zestawy przeszly (1).`
3. Nowy `SpotifyPlaylistAccessMessageTests` uruchamia produkcyjny `SpotifyIntegrationService` i `SpotifyApiClient` przez `HttpClient` z lokalnym `HttpMessageHandler`. Atrapa odpowiada HTTP 403 wyłącznie na `GET /v1/playlists/playlist-other-user/items`; test potwierdza dokładnie jedno żądanie i bezpieczny wynik „zawartość nieudostępniona”. Nie kontaktuje Spotify ani magazynu poświadczeń.
4. Uruchomienie `AccessibleMediaController.Windows.SmokeTests --spotify-playlist-fresh-creation` (obejmuje także nowy pomiar 403) zakończyło się kodem 0.
5. Rzeczywisty konsument zmienionego kontraktu zbudowano w osobnym katalogu NTFS z SDK 8.0.423: `AccessibleMediaController.LiteHost` — 0 ostrzeżeń, 0 błędów.

### #9 — konfiguracja

Bieżące źródła mają pole Client ID, jawny adres powrotu i komunikat dla pustego identyfikatora przed próbą logowania. Zastany test wxLite obejmuje tę ścieżkę. Nie zmieniano kodu konfiguracji ani nie ponawiano szerszej walidacji GUI.

Próba selektywnego uruchomienia trzech testów wxLite w WSL została zablokowana przez brak modułu `wx` w dostępnym interpreterze (`ModuleNotFoundError: No module named 'wx'`). Nie instalowano ani nie uruchamiano GUI tylko po to, aby odtworzyć niezmieniony test. To nie podważa wyników C# powyżej.

### #10 — trwała biblioteka i pierwsze wejście w Playlisty

Nie dublowano już odebranego pakietu #10. Bieżąca rewizja zawiera poprawkę: trwały cache jest zapisywany wyłącznie po pełnym odczycie czterech podstawowych kategorii (utwory, albumy, wykonawcy, playlisty), a wejście najpierw w Playlisty nie oznacza pełnej kolekcji jako wczytanej. Pomocnik `SpotifyCollectionCompletion` jest jawnie linkowany do LiteHost i rzeczywisty LiteHost skompilował się w tym odbiorze.

## Granica dowodu #11

Nie ma nowych danych przyczynowych z protokołu Librespot ani z prawdziwego konta, które uzasadniałyby kolejną zmianę dla `trackUnavailable`. Nie dodano heurystyki EOS (`paused` i pozycja około zera) ani synchronizacji kolejki z Soloist/Connect.

Nadal wymagają rzeczywistego konta i odpowiedniego protokołu, więc nie były symulowane:

- znaczenie kodu/zdarzeń hosta Librespot dla konkretnego błędu klucza audio;
- zachowanie odtwarzania kolejnego utworu po naturalnym końcu;
- zachowanie SDK/Chrome po ponownym połączeniu oraz fizyczny wybór wyjścia;
- potwierdzenie, które playlisty Spotify udostępnia konkretnemu kontu poza testowanym HTTP 403.
