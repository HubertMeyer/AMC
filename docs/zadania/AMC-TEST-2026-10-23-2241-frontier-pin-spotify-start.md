# AMC Test 23.10.2026, 22:41 — bezpieczne usuwanie PIN-u i informacja Spotify

- Status: **zbudowane, atomowo zainstalowane i uruchomione; automatyczne
  bramki zaliczone, czeka na ręczny odbiór NVDA, Spotify i Teufela**.
- Instalacja: `D:\Projekty Codex\AMC Python`.
- Profil: wyłącznie AMC Test. AMC Public, instalator publiczny i GitHub nie
  zostały zmienione.

## Zachowanie widoczne dla użytkownika

- Po naciśnięciu Enter na materiale Spotify AMC od razu mówi
  `Przygotowywanie odtwarzania Spotify`. Nie jest to przedwczesne potwierdzenie
  dźwięku: właściwy stan nadal zatwierdza dopiero zdarzenie rozpoczęcia.
- Usuwanie urządzenia Frontier Smart nie ogłasza już sukcesu, jeżeli Windows
  odmówi usunięcia jego PIN-u z Menedżera poświadczeń. Brak już istniejącego
  poświadczenia jest bezpiecznie traktowany jak wykonane usunięcie.
- PIN Teufela jest lokalnym PIN-em NetRemote, nie hasłem Wi-Fi. Dla Teufel
  RADIO 3SIXTY wartość fabryczna to `1234`; radio pokazuje ją w `Ustawienia
  systemowe → Sieć → Ustawienia NetRemote PIN`.

## Dostępność i powierzchnie poleceń

Nie dodano nowego polecenia ani skrótu, dlatego menu, pełna pomoc, `Ctrl+F1` i
paleta `Ctrl+Shift+K` nie wymagają nowych pozycji. Komunikat Spotify jest
zamierzonym, użytkowym tekstem NVDA. Techniczny kod błędu Windows, nazwa klasy,
identyfikator urządzenia, adres i PIN nie są nazwą elementu listy ani zwykłym
komunikatem sukcesu.

## Testy i rzeczywiste wyniki

- Ukierunkowany zestaw kontraktu Frontier Smart: **1/1 zaliczony**. Sprawdza
  powodzenie, bezpieczne tolerowanie braku poświadczenia i odmowę każdego
  innego błędu Windows.
- Testy interfejsu Spotify: **33/33 zaliczone**; obejmują przekazanie Play bez
  przedwczesnego zatwierdzenia oraz nowy komunikat przygotowania.
- Kompilacja `AccessibleMediaController.LiteHost` Release: **0 ostrzeżeń,
  0 błędów**.
- Paragon pełnej promocji podaje `tests=zaliczone`. Kandydat i stała instalacja
  mają tę samą tożsamość; pakiet zawiera **1674 pliki**. Skrypt promocji
  wykonał kontrolę manifestu, sum, odizolowany start kandydata, atomową
  instalację i ponowny kontrolowany start zainstalowanej kopii.
- Potwierdzone okno po promocji: `AMC Test — 23.10.2026, 22:41`; proces PID
  6676 pochodził z `D:\Projekty Codex\AMC Python\runtime\python.exe`.

## Znane ograniczenia i ręczny odbiór

- Trzeba ręcznie sprawdzić z NVDA poprawny i błędny PIN, zapis urządzenia,
  usunięcie, powrót fokusu oraz ponowne otwarcie listy. Rzadkiej odmowy
  Menedżera poświadczeń nie należy sztucznie wywoływać na profilu użytkownika.
- Trzeba odsłuchać fizyczne Spotify: pierwsze Play bez Denona, zmianę tempa,
  pauzę, wznowienie i przewijanie. Automatyczne testy nie zastępują odsłuchu.
- Rozdziały Spotify pozostają bez zmian: AMC rozpoznaje je tylko z co najmniej
  dwóch znaczników czasu w opisie. Użyty katalog i silnik nie dostarczają
  natywnej listy rozdziałów.
- TIDAL nie został zmieniony. Sonos i Apple Music pozostają osobnymi zadaniami.

## Wersja i commity

- Kod: `9e8d3eab643b579215719bc52ac77b215f0c6fea` —
  `fix(amc-test): dopracuj PIN Frontier i start Spotify`.
- Pakiet: `ce7898a4`.
- Etykieta: `2026.10.23-9e8d3eab643b579215719bc52ac77b215f0c6fea-ce7898a4`.
- Promocja zakończona 23.10.2026 o 22:42:51 czasu lokalnego.
