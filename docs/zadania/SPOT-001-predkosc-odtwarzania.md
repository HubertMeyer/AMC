# SPOT-001 — prędkość odtwarzania Spotify

Status: **W trakcie — kod, testy natywnego silnika, testy interfejsu, pełna
kompilacja Release, atomowa instalacja i uruchomienie AMC Test są zaliczone.
Pozostał ręczny odsłuch Spotify oraz odbiór komunikatów NVDA.**

Data rozpoczęcia: 2026-10-23

## Polecenie użytkownika

Spotify ma udostępniać prawdziwą zmianę prędkości odtwarzania tak jak Pliki,
Podcasty i Time Shift. Polecenia nie mogą być widoczną atrapą: mają docierać do
wewnętrznego silnika Librespot, działać podczas odtwarzania utworów i odcinków,
zachowywać wysokość głosu oraz być dostępne spójnie w odtwarzaczu, menu,
pomocy `Ctrl+F1`, pełnej pomocy i palecie `Ctrl+Shift+K`.

## Materiał do dokumentacji użytkownika

W sesji Spotify prędkość można zmieniać z odtwarzacza i z menu Odtwarzanie:

- `Shift+,` — wolniej;
- `Shift+.` — szybciej;
- `Ctrl+.` — prędkość normalna.

Dostępne stopnie to `0,50x`, `0,75x`, `1,00x`, `1,25x`, `1,50x`, `1,75x` i
`2,00x`. Pole wyboru wyjaśnia znaczenie każdej liczby: `1,00x` to normalna
prędkość, wartości niższe są wolniejsze, a wyższe szybsze. Po zmianie NVDA
ogłasza na przykład `Prędkość 1,25 razy`; po przywróceniu wartości neutralnej
ogłasza `Prędkość normalna`.

Ustawienie domyślne sesji Spotify jest dostępne w Opcjach sesji. Wybrane tempo
jest przekazywane przed rozpoczęciem nowego materiału, zachowywane przy
wznowieniu i po przełączeniu lokalnego wyjścia audio. Zmiana podczas
odtwarzania jest wysyłana od razu do tego samego wewnętrznego silnika.

Odcinki Spotify korzystają z silnika mowy Speedy/Sonic, a utwory z silnika
muzycznego Signalsmith Stretch. Oba zmieniają czas trwania bez prostego
przestrojenia próbek, więc wysokość głosu i muzyki pozostaje bez zmian.

Funkcja należy obecnie do profilu AMC Test razem z całą sesją Spotify. Nie
została dodana do AMC Public.

## Uzasadnienie i decyzje

- Sam Librespot 0.8.0 nie udostępnia gotowej regulacji tempa. PCM jest więc
  kierowany przez te same przypięte silniki `AmcTempoEngines.dll`, z których
  korzystają pozostałe lokalne sesje AMC.
- Zakres `0,5–2,0x` jest walidowany w Pythonie, protokole LiteHost, kliencie C#
  i natywnym hoście. Nieprawidłowa wartość nie jest po cichu przycinana przez
  proces Librespot.
- Rodzaj materiału pochodzi z rzeczywistego URI `spotify:episode:` albo
  `spotify:track:`. Nie zgadujemy go po tytule.
- Powrót do `1,0x` omija przetwarzanie przy nowym strumieniu. Przewinięcie,
  zatrzymanie i nowy materiał zerują stan procesora, żeby nie domieszać próbek
  z poprzedniego miejsca lub utworu.
- Korekta użytkownika z 23.10.2026: niedziałające natywne rozdziały Spotify
  pozostają poza tym zadaniem i nie są przedstawiane jako wdrożone.

## Testy i wynik

- Rust Release, offline: **34/34 testy jednostkowe oraz 13/13 testów
  procesowych zaliczone**. Test z prawdziwym przypiętym
  `AmcTempoEngines.dll` sprawdza ABI i potwierdza, że oba silniki przy `1,5x`
  rzeczywiście zwracają krótszy sygnał stereo bez zmiany częstotliwości
  próbkowania.
- wxPython: **204/204 testy zaliczone**. Obejmują przekazanie wartości przy
  Play, wykonanie bieżącej zmiany dla sesji Spotify, widoczność w menu,
  wspólnym katalogu poleceń, pomocy i palecie oraz etykiety opcji sesji.
- LiteHost ProtocolTests: **27/27 zestawów zaliczonych**; Core SmokeTests
  zakończyły się kodem 0. Izolowany Windows SmokeTest
  `--librespot-output-smoke` jest zaliczony.
- Całe rozwiązanie `AccessibleMediaController.sln` zbudowano w Release:
  **0 ostrzeżeń, 0 błędów**. Cel MSBuild zaakceptował nową przypiętą sumę
  hosta.
- Kandydat i stała instalacja przeszły kontrolę integralności oraz kontrolowany
  start interfejsu i hosta. Zainstalowana kopia ma rewizję `591322e2`, pakiet
  `53e3d987` i działa z `D:\Projekty Codex\AMC Python`; potwierdzony proces
  interfejsu to `runtime\python.exe`, a okno „AMC Test — 23.10.2026, 22:20”
  odpowiada.
- Szeroki Windows SmokeTests przeszedł przez zmienione testy Spotify, lecz
  później zatrzymał się na dwóch zastanych problemach niezwiązanych z tym
  zadaniem: kontroli rozdzielenia nazw instalatora AMC/AMC Test oraz chwilowej
  odmowie `OpenClipboard`. Tego przebiegu nie zapisujemy jako pełnej regresji.

## Znane ograniczenia

- Nie wykonano jeszcze ręcznego odsłuchu na prawdziwym koncie Spotify ani
  kontroli mowy NVDA w zainstalowanym AMC Test.
- Zatrzymanie i pauza domykają bufor procesora, a wznowienie zaczyna nowy
  strumień DSP. Automatyczne testy pilnują danych i kolejności poleceń, ale
  ewentualne krótkie przejście dźwięku wymaga odbioru słuchowego.
- Rozdziały Spotify pozostają bez zmian. Obecny kod nadal potrafi utworzyć
  rozdziały tylko ze znaczników czasu w opisie, nie z natywnego katalogu
  rozdziałów dostawcy.

## Korekta informacji podczas pierwszego odtwarzania — 23.10.2026

Po Enter AMC od razu ogłasza `Przygotowywanie odtwarzania Spotify`, zanim
asynchronicznie uruchomi lub przygotuje wewnętrzny silnik. Komunikat nie
twierdzi jeszcze, że dźwięk działa; właściwy stan odtwarzania nadal zatwierdza
dopiero zdarzenie `playback.started`. Dzięki temu kilkusekundowe pobieranie i
rozruch nie wyglądają dla użytkownika NVDA jak zawieszenie programu.

Ukierunkowane testy interfejsu Spotify przeszły **33/33**. Korekta jest w
commicie `9e8d3eab643b579215719bc52ac77b215f0c6fea`. Późniejsza promocja tego
samego dnia zbudowała i atomowo zainstalowała dokładnie ten commit jako AMC
Test 22:41; integralność oraz kontrolowany start zostały zaliczone.

Rozdziałów nie rozszerzono. Obiekt odcinka używany przez bieżący katalog i
przypięty silnik nie dostarczają natywnej listy rozdziałów. AMC nadal może je
utworzyć tylko wtedy, gdy opis zawiera co najmniej dwa rozpoznawalne znaczniki
czasu. Dodanie samego komunikatu diagnostycznego wymagałoby osobnej zmiany
kontraktu i nie odzyskałoby brakujących danych.

## Wersja i commit

- Kod źródłowy: `4505f325d5eec7df6f520ee156ee79214882df38` —
  `feat(spotify): dodaj sterowanie prędkością Librespot`.
- Przypięcie zbudowanego hosta i kontraktu paczki:
  `591322e2f85c0a07634733c6164fa4cc6a336595` —
  `build(spotify): przypnij host z obsługą tempa`.
- Komunikat przygotowania pierwszego odtwarzania:
  `9e8d3eab643b579215719bc52ac77b215f0c6fea` —
  `fix(amc-test): dopracuj PIN Frontier i start Spotify`.
- Lokalny host Release AMC Test: 6 595 072 B, SHA-256
  `0fde62641c16de6e35ac25962b756f868dd7fd36643e71661f849c231d55c15a`.
- Zainstalowany pakiet AMC Test:
  `2026.10.23-9e8d3eab643b579215719bc52ac77b215f0c6fea-ce7898a4`.
- AMC Public i GitHub: bez zmian; niczego nie opublikowano.
