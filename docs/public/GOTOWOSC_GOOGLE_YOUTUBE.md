# Gotowość dokumentów i przepływu Google/YouTube dla AMC Public

Stan na 27 października 2026 r. Dokument roboczy; nie potwierdza publikacji,
instalacji ani akceptacji Google.

## Gotowe

- Projekt polityki prywatności obejmuje cały publiczny AMC oraz szczegółowy
  przepływ Google/YouTube.
- Projekt warunków korzystania zawiera wymagane odwołanie do Warunków
  korzystania z YouTube.
- Polityka opisuje zakres `youtube.readonly`, dane odczytywane przez AMC,
  lokalny zapis, broker OAuth, odbiorców, usuwanie i cofnięcie dostępu.
- Kod Public oddziela identyfikator klienta i broker od prywatnej konfiguracji
  AMC Test; sekret nie trafia do instalatora.
- AMC Public pozostaje prawidłową paczką bez publicznego identyfikatora i
  brokera. W takim wydaniu host nie dostaje argumentów OAuth, a konto Google
  nie jest pokazywane w menu, palecie ani pomocy.
- Profil Public cofa refresh token w oficjalnym punkcie Google, a dopiero po
  potwierdzeniu usuwa lokalne poświadczenie i oznaczone dane konta. Awaria
  zdalna zachowuje poświadczenie, aby można było bezpiecznie ponowić operację.
- Kanały i playlisty pochodzące z autoryzowanego konta mają jawne pochodzenie
  i datę odświeżenia. Publiczne źródła, których synchronizacja konta nie
  utworzyła ani nie zaktualizowała, pozostają rozdzielone.
- Przy uruchomieniu klienta Public dane konta starsze niż 30 dni są usuwane.
  Cofnięcie w AMC usuwa wszystkie oznaczone dane konta natychmiast w tej samej
  operacji lokalnej.
- Broker ma przypięte zależności, audyt bez znanych podatności i 5 z 5
  zaliczonych testów.

## Decyzja o niewdrażaniu

Korekta użytkownika z 27 października 2026 r.: domena `stareaudycje.pl` nie
będzie używana dla strony AMC, dokumentów Google ani brokera OAuth. Nie wybrano
innej domeny i nie planuje się jej kupować wyłącznie dla tej funkcji.

Kod klienta i brokera pozostaje przygotowany, ale niewdrożony. Dopóki nie
powstanie osobna, świadomie wybrana domena i kompletna konfiguracja
produkcyjna, AMC Public ma być budowane bez zasobów OAuth Google i bez
widocznego polecenia konta. Nie blokuje to publicznych funkcji YouTube, które
nie wymagają zalogowanego konta. Decyzja może zostać zmieniona później bez
przenoszenia prywatnego sekretu do aplikacji.

## Blokery przed publikacją

1. Uzupełnić adres korespondencyjny administratora i okres retencji zgłoszeń.
   Przed publikacją zdecydować, czy podany adres Gmail pozostaje publicznym
   kontaktem, czy zastępuje go inny dedykowany adres.
2. Poddać podstawy prawne, transfery międzynarodowe i dane administratora
   krótkiej kontroli prawnej właściwej dla sposobu dystrybucji AMC.
3. Jeżeli logowanie Google ma wejść do wydania Public, najpierw wybrać domenę
   inną niż `stareaudycje.pl`, a następnie udostępnić stronę programu, politykę
   i warunki pod stałymi publicznymi adresami HTTPS. Strona programu musi
   opisywać funkcje AMC i prowadzić do polityki.
4. Dodać do aplikacji zawsze dostępną pozycję otwierającą politykę oraz warunki
   i objąć ją wspólnym modelem menu, palety, pomocy, wykonania i testów NVDA.
5. Przed pierwszym użyciem funkcji YouTube uzyskać od użytkownika jawne
   potwierdzenie polityki i warunków; zapisać wersję zaakceptowanego dokumentu
   osobno w profilu Public. Odmowa ma pozostawić konto niepołączone.
6. W Google Cloud podać zgodne: nazwę aplikacji, stronę główną, politykę,
   warunki, adres pomocy i autoryzowaną domenę. W Search Console potwierdzić
   własność domeny.
7. Wdrożyć broker pod docelowym adresem HTTPS, ustawić sekret wyłącznie po
   stronie serwera i przeprowadzić rzeczywiste logowanie, odświeżenie tokenu,
   wylogowanie, cofnięcie dostępu w Google i kontrolę braku trwałych logów.
8. Przeprowadzić odbiór NVDA: początkowy fokus, czytanie dokumentów, linki,
   zgoda i odmowa, powrót fokusu, ponowne otwarcie oraz brak technicznych nazw.

## Źródła wymagań

- YouTube API Services Developer Policies:
  <https://developers.google.com/youtube/terms/developer-policies>
- Google — wymagania weryfikacji marki i polityki prywatności:
  <https://developers.google.com/identity/verification/authentication-verification>
- Google — zgodność OAuth i własna zweryfikowana domena:
  <https://developers.google.com/identity/verification/authentication-policy-compliance>
- RODO, w szczególności art. 13:
  <https://eur-lex.europa.eu/eli/reg/2016/679/oj>
- Urząd Ochrony Danych Osobowych — prawa osoby:
  <https://uodo.gov.pl/pl/493/4098>

