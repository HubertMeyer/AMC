# Apple Music dla AMC Test — plik dla osoby z Apple Developer

## Kto może to przygotować

Potrzebna jest osoba należąca do Apple Developer Program z rolą Account Holder
albo Admin. Samo zwykłe konto Apple ID nie wystarczy.

Ta osoba nie loguje użytkownika końcowego i nie przekazuje swojego hasła.
Przygotowuje wyłącznie konfigurację aplikacji oraz podpisany developer token JWT.

## Co zrobić w Apple Developer

1. Utworzyć albo wybrać Media ID przeznaczone dla AMC Test.
2. Włączyć dla niego MusicKit.
3. Utworzyć klucz Media Services powiązany z tym Media ID.
4. Zapisać bezpiecznie:
   - Team ID,
   - Key ID,
   - pobrany prywatny klucz z rozszerzeniem `.p8`.
5. Klucza `.p8` nie dodawać do repozytorium, wiadomości, zgłoszenia błędu,
   instalatora ani ustawień AMC. Apple pozwala pobrać ten klucz tylko raz.

## Jak utworzyć gotowy token bez wysyłania klucza

W repozytorium AMC jest lokalny skrypt:

`D:\Projekty Codex\Accessible Multimedia Controller\narzedzia\apple-music\Utworz-DeveloperToken.ps1`

Uruchomić go w PowerShell 7 na komputerze, na którym bezpiecznie znajduje się
klucz `.p8`:

```powershell
pwsh -File "D:\Projekty Codex\Accessible Multimedia Controller\narzedzia\apple-music\Utworz-DeveloperToken.ps1" -TeamId TEAMID1234 -KeyId KEYID12345 -PrivateKeyPath "C:\bezpieczny-folder\AuthKey_KEYID12345.p8"
```

Skrypt domyślnie tworzy token ważny 90 dni i kopiuje wyłącznie gotowy JWT do
schowka. Nie kopiuje ani nie zmienia `.p8`. Dopuszczalny parametr
`-DaysValid` ma zakres od 1 do 180 dni.

## Co przekazać opiekunowi AMC

Przekazać bezpiecznym kanałem tylko:

- gotowy developer token JWT, czyli jeden długi tekst z trzema częściami
  rozdzielonymi kropkami;
- informację, że używanym katalogiem ma być `pl`, jeżeli test odbywa się na
  polskim koncie.

Nie przekazywać pliku `.p8`, Team ID, Key ID ani hasła do konta Apple.

## Co robi potem użytkownik AMC Test

1. Otwiera sesję Apple Music.
2. Naciska Ctrl+F5 i wybiera okno Konto Apple Music.
3. Wkleja gotowy developer token, wpisuje `pl` i wybiera
   „Zapisz i sprawdź token”.
4. Wybiera „Zaloguj kontem Apple”.
5. Loguje się wyłącznie w oficjalnym oknie Apple.
6. Wybiera „Pobierz bibliotekę”.

AMC zapisuje oba tokeny w Menedżerze poświadczeń Windows. Pełne odtwarzanie
wymaga aktywnej subskrypcji Apple Music. Pierwszy test ma także potwierdzić, czy
DRM MusicKit działa w używanej wersji WebView2.

## Czego nie robić

- Nie umieszczać gotowego JWT w repozytorium; wygasa, ale nadal jest
  poświadczeniem aplikacji.
- Nie wklejać zawartości `.p8` do okna AMC.
- Nie wysyłać klucza ani tokenu w publicznym Issue lub logu.
- Nie publikować jeszcze tej konfiguracji w wydaniu publicznym. Jest
  przeznaczona do AMC Test i weryfikacji na prawdziwym koncie.
