# AMC Test 0.1.0-alpha.425 — zapis weryfikacji

## Nowe testy uruchomione 23 października 2026

- Kompilacja Windows Debug po integracji YouTube: zaliczona, 0 ostrzeżeń i 0
  błędów.
- `--youtube-google-ui`: zaliczony. Zakres: PKCE, brak sekretu, zakres tylko do
  odczytu, stronicowanie API, token w nagłówku, Ctrl+F5, menu, paleta, pomoc i
  etykiety NVDA.
- `--apple-music-prototype`: zaliczony po paginacji biblioteki i obsłudze
  prywatnych kontenerów.
- `--apple-music-ui`: zaliczony. Zakres: granice tokenu, Ctrl+F5, ukryty
  MusicKit i etykiety NVDA.
- Test generatora Apple JWT: zaliczony na jednorazowym kluczu testowym; pliki
  testowe zostały usunięte.
- `--playback-shuffle` oraz `--playback-shuffle-ui`: zaliczone podczas zadania
  odtwarzania losowego.
- Pełna kompilacja rozwiązania Release: zaliczona, 0 ostrzeżeń i 0 błędów.
- Pełny zestaw Core Release: zaliczony. Był jednym wspólnym przebiegiem
  integracyjnym przed instalacją.
- Izolowane zestawy Windows Release `--youtube-google-ui`,
  `--apple-music-ui` i `--playback-shuffle-ui`: zaliczone.
- Końcowa kontrola `git diff --check` z poprawną obsługą CRLF: zaliczona.
- Końcowy skan źródeł: brak plików `.p8`, JWT i `client_secret*.json` oraz brak
  twardo wpisanych tokenów lub kluczy. Po korekcie kontrolnej ponownie zaliczono
  `--apple-music-ui` w Release.

## Zestawy wcześniejsze

Osobne zadania miały już zaliczone testy dodawania źródeł YouTube, dużych
podcastów Spotify i odtwarzania oraz Frontier Smart 13/13. Nie uruchamiano ich
ponownie bez powodu w trakcie dodawania logowania Google.

## Czego test automatyczny nie potwierdza

- prawdziwego ekranu zgody i importu z konta Google;
- prawdziwego logowania Apple, aktywnej subskrypcji i zgodności DRM WebView2;
- rzeczywistego radia Frontier Smart w sieci użytkownika;
- ręcznego przejścia interfejsu z NVDA po instalacji.

## Pakiet i instalacja

- Program samowystarczalny: zbudowany jako `0.1.0-alpha.425`.
- Instalator:
  `D:\Projekty Codex\Accessible Multimedia Controller\publish\AMC-Setup-0.1.0-alpha.425.exe`.
- Rozmiar instalatora: 65 472 632 bajty.
- SHA-256 instalatora:
  `695a16e598765ce7a6b0c681c9dc46841247f23136aa176d82abeb383b444f0b`.
- Cicha instalacja: kod 0.
- Zainstalowany program:
  `C:\Users\micha\AppData\Local\Programs\AMC\AccessibleMediaController.exe`.
- ProductVersion zainstalowanego programu: `0.1.0-alpha.425`.
- SHA-256 zainstalowanego programu i programu w pakiecie:
  `4c9a29c7a48743532e036ac0dbc3a3a17f3abcef376357f241e0a448b1e80e82`.
- W instalacji potwierdzono hosty Apple Music, Spotify, TIDAL i Librespot.
- Programu po instalacji nie uruchamiano automatycznie.

Ten zapis odróżnia zmianę źródła, test, kompilację, instalację i publikację.
Publicznego wydania nie wykonano.
