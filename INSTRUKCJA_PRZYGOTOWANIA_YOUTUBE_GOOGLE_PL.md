# Przygotowanie logowania Google/YouTube dla AMC Test

Ta instrukcja jest dla osoby, która ma dostęp do projektu w Google Cloud.
Nie musi znać kodu AMC. Użytkownik końcowy loguje się później własnym kontem
Google na oficjalnej stronie Google.

## Co trzeba przygotować

1. Otwórz projekt w Google Cloud Console albo utwórz osobny projekt dla AMC
   Test.
2. Włącz **YouTube Data API v3**.
3. W sekcji Google Auth Platform skonfiguruj ekran zgody OAuth.
4. Dodaj zakres tylko do odczytu:
   `https://www.googleapis.com/auth/youtube.readonly`.
5. Jeżeli aplikacja pozostaje w trybie testowym, dodaj konta osób testujących
   do listy użytkowników testowych. Token odświeżania aplikacji testowej może
   mieć ograniczoną trwałość, więc po pewnym czasie AMC może poprosić o ponowne
   logowanie.
6. Utwórz dane logowania OAuth typu **Desktop app**, czyli **Aplikacja na
   komputer**.
7. Skopiuj wartość **Client ID**. Zwykle kończy się ona na
   `.apps.googleusercontent.com`.

Oficjalna dokumentacja Google:

- <https://developers.google.com/identity/protocols/oauth2/native-app>
- <https://developers.google.com/youtube/v3/guides/auth/installed-apps>
- <https://developers.google.com/youtube/v3/docs/subscriptions/list>

## Co przekazać użytkownikowi AMC

Przekaż wyłącznie publiczny **Client ID**. Nie przekazuj i nie dodawaj do
repozytorium:

- sekretu klienta;
- pobranego pliku `client_secret*.json`;
- tokenu dostępu ani tokenu odświeżania;
- hasła do konta Google;
- ciasteczek przeglądarki.

AMC zapisuje Client ID i tokeny użytkownika w Menedżerze poświadczeń Windows.
Nie trafiają one do `state.json`, kopii konfiguracji ani dziennika.

## Pierwsze uruchomienie w AMC Test

1. Otwórz sesję **Podcasty i YouTube**.
2. Naciśnij `Ctrl+F5` albo wybierz w menu Plik **Konto YouTube i import z
   Google…**.
3. Wklej Client ID i wybierz **Zapisz Client ID**.
4. Wybierz **Zaloguj kontem Google**. AMC otworzy zwykłą domyślną
   przeglądarkę dopiero po tym jawnym poleceniu.
5. Na stronie Google zaloguj właściwe konto i zaakceptuj odczyt danych YouTube.
6. Wróć do AMC i wybierz **Importuj subskrypcje i playlisty**.

Import scala subskrybowane kanały i playlisty należące do konta z Biblioteką
sesji Podcasty i YouTube. Nie usuwa wcześniej zapisanych źródeł. Odświeżanie
wszystkich źródeł nadal działa z menu Plik oraz globalnym skrótem wtyczki NVDA
`Ctrl+Windows+F5`.

## Ograniczenia

Logowanie służy do odczytu biblioteki YouTube. Nie przekazuje tokenu Google do
`yt-dlp`, nie daje AMC ciasteczek przeglądarki i nie omija ograniczeń wieku,
regionu, prywatności ani zabezpieczeń materiału. Publiczne materiały są
odtwarzane dotychczasowym mechanizmem AMC. Playlista może zostać odczytana z
API, ale prywatny lub zablokowany film nadal może nie dać się odtworzyć.

Dla szerszego, publicznego udostępnienia aplikacji Google może wymagać
weryfikacji ekranu zgody i zakresu YouTube. Na etapie AMC Test wystarczy tryb
testowy z jawnie dodanymi użytkownikami testowymi.
