# AMC Test 23.10.2026, 15:42 — widoczne konto YouTube

- Status: `Zbudowane, atomowo zainstalowane i uruchomione; automatyczna
  weryfikacja zainstalowanego hosta oraz palety zaliczona, czeka na ręczne
  logowanie i odbiór NVDA`.
- Data instalacji: 23 października 2026
- Obszar: YT-001, zgodność protokołu C#–Python, zbiorczy AMC Test
- Instalacja: `D:\Projekty Codex\AMC Python`

## Zachowanie widoczne dla użytkownika

W sesji `Podcasty i YouTube` paleta `Ctrl+Shift+K`, menu Plik i pełna pomoc
korzystają z jednego modelu polecenia `Konto YouTube i synchronizacja
subskrypcji…`. Polecenie pojawia się dopiero po potwierdzeniu przez hosta, że
profil AMC Test ma poprawny publiczny identyfikator klienta Google. Sam start
programu nie otwiera przeglądarki i nie loguje konta.

Po uruchomieniu polecenia okno ma pozwalać rozpocząć logowanie w zwykłej
przeglądarce, anulować oczekiwanie, sprawdzić stan, podejrzeć niedestrukcyjny
plan synchronizacji oraz osobno zatwierdzić zapis kanałów w Bibliotece AMC.
Zakres Google pozostaje tylko do odczytu.

## Dokładne polecenia i lokalizacje

- Program: `D:\Projekty Codex\AMC Python\AMC.exe`.
- Zainstalowany host: `D:\Projekty Codex\AMC Python\host\amc_lite_host.exe`.
- Publiczny identyfikator klienta w paczce testowej:
  `D:\Projekty Codex\AMC Python\app\amc_wx_lite\youtube-oauth-client-id.txt`.
- Kandydat:
  `.test-output/AMC-Python-next-2026.10.23-589708e6f0ab6de4b4b6939c6278b70e0c14e110-d88713d0`.
- Polecenie użytkownika: w sesji `Podcasty i YouTube` nacisnąć
  `Ctrl+Shift+K`, wpisać `Konto YouTube` i nacisnąć Enter.

Nie zapisano sekretu klienta, tokenu użytkownika ani kodu autoryzacyjnego.
Nie uruchomiono przeglądarki ani żądania OAuth podczas budowania i kontroli.

## Komunikaty i zachowanie czytnika ekranu

Nazwa polecenia brzmi `Konto YouTube i synchronizacja subskrypcji…` i kończy
się prawidłowym znakiem `U+2026`. Okno używa nazw `Stan konta YouTube`,
`Kanały planowane do zapisania w Bibliotece AMC`, `Zaloguj konto YouTube przez
Google w przeglądarce`, `Anuluj oczekiwanie na logowanie YouTube` i `Zamknij
okno konta YouTube`. Odpowiedzi hosta są zamieniane wyłącznie na celowe
komunikaty użytkowe; reprezentacje obiektów, nazwy typów i identyfikatory nie
wchodzą do nazw dostępnych.

Automatycznie potwierdzono tekst i obecność wpisu w zainstalowanej paczce.
Rzeczywista mowa NVDA, fokus początkowy, Tab i Shift+Tab, powrót z
przeglądarki, anulowanie oraz odmowa Google wymagają ręcznego odbioru.

## Ważne różnice między trybami

- `AMC Test`: klient OAuth i polecenie są dołączone, a możliwość hosta ma
  wartość `available=true`.
- `AMC Public`: zasób klienta nie jest kopiowany, możliwość nie jest
  reklamowana i polecenie pozostaje niewidoczne.
- Projekt Google pozostaje w trybie Testing i obsługuje tylko dodanych
  użytkowników testowych.

## Uzasadnienie i poprawiona przyczyna

Wersja 15:14 zawierała konfigurację OAuth, lecz typowane rekordy C# wychodziły
z nazwami `Available`, `Connected` i `Message`; Python sprawdzał zapis
`available`, `connected` i `message`. Interfejs odczytywał więc istniejącą
możliwość jako niedostępną i ukrywał całe polecenie.

Serializer całego protokołu LiteHost wymusza teraz `camelCase`, rekordy konta
YouTube mają dodatkowo jawne nazwy przewodowe, a klient Python przejściowo
akceptuje także starszy zapis. Test między prawdziwym procesem C# i klientem
Python chroni granicę, której wcześniejsze atrapy nie mierzyły. Ten mechanizm
obejmuje przyszłe typowane odpowiedzi innych sesji, dlatego podobna cicha
rozbieżność wielkości liter nie powinna ponownie przejść testów.

## Testy i rzeczywiste wyniki

- Celowane testy YouTube i rzeczywistej granicy C#–Python: 22/22 zaliczone.
- Pełna regresja Python/wx uruchomiona dwukrotnie: za każdym razem 2016
  zaliczonych, 111 kontrolowanie pominiętych i 11 podtestów zaliczonych.
- Protokół LiteHost: 27/27 zestawów, w tym siedem scenariuszy konta YouTube.
- Launcher i aktualizator: 30/30 testów, również ponownie w bramce promocji.
- Całe rozwiązanie: kompilacja Release bez ostrzeżeń i błędów.
- Kandydat: 1672 pliki; manifest, sumy i kontrolowany start zaliczone.
- Zainstalowana kopia: pełna integralność i kontrolowany start zaliczone.
- Rzeczywisty zainstalowany host odpowiedział na
  `youtube.accountCapabilities` polami `available`, `readOnly`,
  `separateProfileCredentials`, `message`, z `available=true` i bez nazw
  PascalCase.
- Zainstalowany runtime utworzył dokładnie jeden wpis konta YouTube w palecie.
- Uruchomione okno: `AMC Test — 23.10.2026, 15:42`.

## Zakres wcześniejszych poprawek w tej samej paczce

- Spotify: stronicowanie dużych zapisanych podcastów i odtwarzanie odcinków są
  obecne; użytkownik potwierdził 150 odcinków Tyflo Podcast i odtwarzanie.
- Parser Tyflo Podcast pomija puste rekordy Spotify; poprawka jest obecna.
- YouTube `Ctrl+N`, szybkie `Ctrl+V` i stabilizacja fokusu są obecne; użytkownik
  potwierdził poprawę.
- `Odtwarzaj losowo (R)` dla plików, podcastów i Spotify jest obecne w kodzie,
  menu kontekstowym, palecie i pomocy; czeka na ręczny odbiór.
- Kod korekt Frontier Smart jest obecny, ale ręczny test użytkownika nie
  wykazał poprawy, więc funkcja pozostaje otwarta.
- Automatyczny powrót Spotify z nieobecnego Denona USB do domyślnego wyjścia
  Windows ma kod i testy, lecz ręczny test użytkownika zakończył się porażką;
  nie jest uznany za naprawiony.
- Natywne rozdziały odcinków Spotify nie są wdrożone. Obecny mechanizm może
  korzystać tylko ze znaczników czasu znalezionych w opisie.

## Znane ograniczenia i migracja

Nie ma migracji profilu. Token powstanie dopiero po jawnym logowaniu i ma
pozostać w chronionym magazynie Windows. Tryb Google Testing może wymagać
ponownej zgody i nie jest gotowym modelem publicznej dystrybucji. AMC Public,
instalator publiczny i GitHub nie zostały zmienione.

Ręczny odbiór powinien objąć obecność polecenia, fokus okna, wybór konta,
zgodę, powrót do AMC, podgląd subskrypcji, zapis, wylogowanie i ponowne
otwarcie. Frontier, wyjście audio Spotify i rozdziały Spotify pozostają
odrębnymi, otwartymi usterkami.

## Materiał do instrukcji użytkownika

Otwórz `Podcasty i YouTube`, naciśnij `Ctrl+Shift+K`, wpisz `Konto YouTube` i
naciśnij Enter. Wybierz `Zaloguj konto YouTube przez Google w przeglądarce`.
AMC nie pyta o hasło i prosi tylko o odczyt subskrypcji. Po powrocie najpierw
sprawdź plan zmian; zapis kanałów do Biblioteki AMC jest osobnym poleceniem.

## Wersja i commit

- Rewizja źródła paczki: `589708e6f0ab6de4b4b6939c6278b70e0c14e110`.
- Identyfikator zawartości: `d88713d0`.
- Etykieta kompilacji:
  `2026.10.23-589708e6f0ab6de4b4b6939c6278b70e0c14e110-d88713d0`.
- Utworzenie paczki: 23.10.2026, 15:42:22 czasu lokalnego.
- Instalacja i uruchomienie: 23.10.2026, 15:43:42 czasu lokalnego.
- Niniejszy zapis odbioru powstał po instalacji i nie zmienia tożsamości
  zainstalowanej paczki.
