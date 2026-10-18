# REL-001 — GitHub Releases, aktualizacje i Sygnalista

- Status: `Oczekuje — fundament klienta dopuszczony po lokalnym instalatorze`
- Utworzono: 18 października 2026
- Obszar: wydania, aktualizator i dostępne zgłoszenia
- Polecenie uruchamiające: `Uruchom zadanie REL-001`

## Cel

Po przygotowaniu pierwszego publicznego instalatora połączyć jeden kontrolowany
proces: oznaczony kod w GitHubie, wydanie GitHub Releases, manifest aktualizacji
oraz dostępne zgłaszanie błędów bez wymagania konta GitHub od użytkownika.

## Zatwierdzony kierunek

- GitHub jest źródłem kodu, tagów, opisów zmian i gotowych wydań.
- `AMC-Python-Updater.exe` pozostaje wykonawcą transakcyjnej podmiany. Moduł
  internetowy jedynie sprawdza podpisany lub jednoznacznie zweryfikowany
  manifest, pobiera właściwy pakiet i przekazuje go aktualizatorowi.
- Kanał testowy i publiczny mają osobne manifesty. Aktualizacja nigdy nie
  zamyka AMC podczas nagrywania i nie instaluje niesprawdzonego pliku.
- Formularz `Zgłoś błąd lub sugestię` korzysta z idei Sygnalisty Michała
  Dziwisza: aplikacja wysyła zatwierdzony raport do Cloudflare Workera, a
  Worker tworzy issue w repozytorium AMC. Użytkownik nie potrzebuje konta
  GitHub.

## Wynik porównania zewnętrznego projektu

Sprawdzono projekt `michaldziwisz/sygnalista` z 18 października 2026:

- licencja MIT pozwala użyć i zmodyfikować kod z zachowaniem informacji
  licencyjnej;
- endpoint `POST /v1/report` przyjmuje rodzaj, tytuł, opis, wersję, kanał,
  diagnostykę oraz opcjonalny skompresowany log;
- pełny raport i log mogą trafić do prywatnego repozytorium `support-intake`,
  a publiczne issue dostaje etykietę `bug` lub `enhancement` oraz `from-app`;
- mapowanie aplikacji, token aplikacji, limity rozmiaru i tempo żądań są
  konfigurowane w Workerze;
- rozwiązanie jest wzorcem i możliwym składnikiem, ale AMC potrzebuje własnej
  polityki prywatności, filtrowania danych i testów nadużyć.

## Zakres formularza AMC

- Typ: błąd albo sugestia.
- Krótki tytuł, opis i opcjonalne kroki odtworzenia.
- Automatycznie: wersja AMC, commit, kanał wydania, wersja Windows, rodzaj
  aktywnej sesji i wersje składników — bez nazw prywatnych plików i bez danych
  kont.
- Log jest domyślnie wyłączony. Przed wysłaniem użytkownik może zobaczyć
  dokładny raport, usunąć log i zatwierdzić operację.
- Po powodzeniu aplikacja podaje numer zgłoszenia i umożliwia skopiowanie
  adresu. Nie otwiera wbudowanej przeglądarki.

## Przejście zgłoszeń do pracy

Sygnalista już tworzy zwykłe GitHub Issues, więc dalszy proces może być
automatyzowany bez przepisywania danych:

1. etykiety `bug`, `enhancement` i `from-app` rozdzielają kolejkę;
2. dodatkowe etykiety AMC określają sesję i wydanie testowe lub publiczne;
3. po weryfikacji zgłoszenia tworzymy albo wskazujemy zadanie w
   `docs/zadania`, zachowując numer issue;
4. Codex lub Hermes może później analizować wybrane issue wyłącznie na jawne
   polecenie użytkownika; samo nadejście raportu nie uruchamia zmian kodu.

## Kolejność wdrożenia

1. Repozytorium i model wersji.
2. Powtarzalne wydanie GitHub Releases z manifestem i sumą SHA-256.
3. Internetowe sprawdzanie aktualizacji oraz bezpieczne przekazanie paczki do
   istniejącego aktualizatora.
4. Własna instancja Workera Sygnalisty i prywatne repo raportów.
5. Dostępny formularz AMC, filtrowanie danych, testy NVDA, brak sieci,
   ponowienie, limit i odrzucenie zbyt dużego logu.

## Podział umożliwiający wcześniejszą pracę

Po przygotowaniu lokalnego instalatora wolno wdrożyć bez połączenia z usługą:

- dostępny formularz błędu lub sugestii;
- jawny podgląd całego raportu i domyślnie wyłączony log;
- filtrowanie ścieżek, nazw prywatnych plików, adresów, tokenów i danych kont;
- wspólny kontrakt transportu z atrapą sukcesu, błędu, braku sieci, limitu i
  zbyt dużego raportu;
- możliwość skopiowania albo zapisania zatwierdzonego raportu lokalnie, gdy
  prawdziwy serwer nie jest jeszcze skonfigurowany;
- testy NVDA fokusa, ponownego otwarcia, podglądu, Anuluj i Wyślij.

Nie wolno przed etapem GitHub uznawać wysyłania za działające, osadzać tokenu,
stawiać publicznego Workera ani tworzyć prawdziwych Issues. Wdrożenie Workera,
prywatnego repozytorium raportów, mapowania etykiet i końcowego endpointu
pozostaje częścią tego samego REL-001, wykonywaną razem z zatwierdzonym
repozytorium, kanałami wydań i polityką prywatności.

## Poza zakresem

- Publikacja obecnego stanu bez osobnej decyzji użytkownika.
- Wysyłanie logów, adresów stacji, historii lub danych kont bez podglądu i
  zgody.
- Automatyczne wdrażanie poprawek na podstawie samego zgłoszenia.
- Instalowanie lub utrzymywanie zewnętrznej aplikacji Michała Dziwisza.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data zakończenia:
- Repozytorium i kanały:
- Adres i wersja kontraktu Workera:
- Testy aktualizacji:
- Testy prywatności i NVDA:
- Wydanie:

