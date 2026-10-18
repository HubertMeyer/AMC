# ARC-001 — wspólny rdzeń poleceń, CLI i lokalne sterowanie AI

- Status: `Oczekuje`
- Utworzono: 18 października 2026
- Obszar: architektura aplikacji, automatyzacja i bezpieczeństwo
- Polecenie uruchamiające: `Uruchom zadanie ARC-001`
- Horyzont: przygotowywać granice przy bieżących zmianach; pełny serwer dopiero
  po ustabilizowaniu publicznego AMC

## Trwała decyzja architektoniczna

Funkcja programu i sposób jej wywołania są osobnymi warstwami. Skrót klawiszowy,
menu, paleta poleceń, dodatek NVDA, przyszły wiersz poleceń i lokalny serwer dla
sztucznej inteligencji nie mogą zawierać własnej kopii logiki funkcji ani
sterować AMC przez sztuczne naciskanie klawiszy. Każdy adapter tworzy jawne,
wersjonowane polecenie, które wykonuje wspólna warstwa aplikacyjna i zwraca
ustrukturyzowany wynik.

Istniejący wersjonowany potok dodatku NVDA i lista dozwolonych komend stanowią
dobry punkt wyjścia, ale nie są jeszcze pełnym publicznym API automatyzacji.

## Docelowy układ

1. Wspólny katalog poleceń i zapytań z argumentami, wynikami oraz błędami.
2. Jedna implementacja przypadku użycia niezależna od wxPython.
3. Cienkie adaptery: GUI, skróty, paleta, NVDA, CLI oraz lokalny serwer AI.
4. Osobne operacje tylko do odczytu i operacje zmieniające stan.
5. Profil możliwości odróżniający AMC Test od publicznego AMC.
6. Dane maszynowe są oddzielone od celowych, dostępnych etykiet dla NVDA.

## Zasady bezpieczeństwa

- Serwer domyślnie działa tylko lokalnie; nie jest wystawiany do Internetu.
- Obowiązuje jawna lista poleceń, wersjonowanie protokołu i kontrola klienta.
- Usuwanie, nadpisywanie, zatrzymywanie nagrania i inne działania ryzykowne
  wymagają potwierdzenia lub krótkotrwałego tokenu zgody.
- Działania automatyczne mają dziennik audytowy bez sekretów i danych kont.
- Polecenia otwierające okna nie mogą bez potrzeby przejmować fokusu.
- Wywołania dotyczące GUI są bezpiecznie przekazywane do wątku wxPython.

## Etapy przyszłego wdrożenia

1. Ujednolicić istniejące akcje i odłączyć ich logikę od procedur zdarzeń GUI.
2. Dodać prosty klient CLI do odczytu stanu i podstawowego transportu.
3. Rozszerzyć polecenia o sesje, wyszukiwanie, kolejkę i bibliotekę.
4. Dopiero później wystawić ograniczony lokalny serwer, np. adapter MCP, dla AI.
5. Osobno dopuścić harmonogramy, playlisty i operacje destrukcyjne po testach
   autoryzacji, potwierdzeń, współbieżności i dostępności.

## Poza zakresem pierwszego etapu

- Zdalne sterowanie przez Internet.
- Automatyzowanie interfejsu przez symulowanie klawiatury lub myszy.
- Pełny dostęp AI do systemu plików, haseł albo tokenów usług.
- Implementacja serwera przed ustabilizowaniem bieżących funkcji AMC.

## Kryteria akceptacji przyszłego wdrożenia

1. Ta sama funkcja przechodzi przez jeden przypadek użycia z GUI, CLI i testu.
2. Adapter nie zawiera logiki domenowej i nie emituje sztucznych klawiszy.
3. Odpowiedzi mają stabilny format, a komunikaty dostępności nie ujawniają nazw
   klas, identyfikatorów ani technicznych reprezentacji obiektów.
4. Nieuprawnione, nieznane i niedostępne w profilu polecenia są odrzucane.
5. Testy obejmują nagrywanie, dialog modalny, zajęty interfejs, utratę klienta,
   podwójne wysłanie polecenia i zachowanie fokusu.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data rozpoczęcia i zakończenia:
- Zakres wdrożonego etapu:
- Protokół i wersja:
- Adaptery:
- Testy i ich wyniki:
- Ograniczenia:
