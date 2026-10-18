# LIC-001 — Radio Browser, BASS i dobrowolne wpłaty

- Status: `Oczekuje`
- Utworzono: 18 października 2026
- Obszar: licencje wydania i finansowanie projektu
- Polecenie uruchamiające: `Uruchom zadanie LIC-001`

## Cel

Rozstrzygnąć warunki, na jakich publiczne AMC Python może przyjmować
dobrowolne wpłaty, zanim w programie, dokumentacji albo na GitHubie pojawi się
PayPal, GitHub Sponsors lub podobny odnośnik.

## Potwierdzone ustalenia

- AMC korzysta bezpośrednio z publicznego API Radio Browser. Oficjalna
  dokumentacja pozwala używać API w oprogramowaniu darmowym i niedarmowym, a
  zebrane dane stacji są oznaczone jako public domain. Radio Browser nie jest
  więc sam w sobie zakazem sprzedaży ani dobrowolnych wpłat.
- Do pakietu AMC dołączony jest BASS. Dołączona licencja zezwala bezpłatnie na
  użycie niekomercyjne tylko wtedy, gdy twórca nie zarabia na produkcie przez
  sprzedaż, reklamy i podobne mechanizmy. Powiązana z AMC zbiórka wpłat może
  zostać uznana za zarabianie na produkcie; nie wolno zakładać, że słowo
  „dobrowolna” automatycznie omija ten warunek.
- Oficjalna odpowiedź autora BASS dotycząca donationware doprecyzowuje, że
  licencja jest wymagana, jeżeli prośba o wpłatę znajduje się w aplikacji albo
  wpłacający otrzymuje dodatkowe funkcje lub wsparcie. Sam odnośnik do wpłat na
  zewnętrznej stronie, bez korzyści dla wpłacającego i bez prośby w AMC, według
  tej odpowiedzi nie wymaga licencji BASS.
- Oficjalny cennik sprawdzony 18 października 2026 podaje dla jednej platformy:
  BASS Shareware 125 EUR, Single Commercial 950 EUR oraz Unlimited Commercial
  3450 EUR. Licencje są bez tantiem i obejmują przyszłe aktualizacje BASS.
  Najtańsza licencja Shareware jest przeznaczona dla indywidualnego autora,
  ale przed zakupem trzeba pisemnie potwierdzić z Un4seen, że dokładny model
  bezpłatnego AMC z dobrowolnymi wpłatami mieści się w jej warunkach.
- Bieżący kod AMC wywołuje `bass.dll` bezpośrednio przez deklaracje P/Invoke;
  nie korzysta z osobno licencjonowanej biblioteki BASS.NET. Na obecnym stanie
  nie doliczamy więc kosztu BASS.NET, ale audyt przed wydaniem ma to ponownie
  potwierdzić dla gotowej paczki.
- wxPython i większość wymienionych bibliotek otwartych nie wprowadzają
  analogicznego zakazu komercyjnego, ale pełny audyt wszystkich składników
  nadal jest obowiązkowy przed wydaniem.

## Decyzja do podjęcia

Przed włączeniem wpłat wybrać jedną z dróg:

1. uzyskać od Un4seen pisemne potwierdzenie, że planowany model wpłat mieści
   się w bezpłatnym użyciu; albo
2. kupić właściwą licencję BASS dla AMC i wskazanych platform; albo
3. usunąć BASS z publicznego profilu oraz zastąpić jego funkcje składnikami o
   licencji zgodnej z finansowaniem projektu.

Ogólny odnośnik do wsparcia autora poza programem również wymaga tej samej
ostrożności. Najbezpieczniejszy wariant bez zakupu to brak prośby o wpłaty w
samej aplikacji, brak funkcji lub uprzywilejowanego wsparcia dla wpłacających i
odnośnik dostępny wyłącznie na zewnętrznej stronie projektu. Ostateczną
interpretację konkretnego wariantu powinien potwierdzić właściciel BASS lub
prawnik; ten dokument nie jest poradą prawną.

## Kryteria akceptacji

1. Powstaje kompletna macierz składników publicznej paczki i ich licencji.
2. Dla BASS istnieje pisemna zgoda, zakupiona licencja albo potwierdzone
   usunięcie z publicznego pakietu.
3. Tekst wpłat nie sugeruje zakupu funkcji, pierwszeństwa w poprawkach ani
   gwarancji świadczenia usługi, jeżeli taki model nie został osobno przyjęty.
4. Dokumentacja podaje autorów i wymagane informacje licencyjne.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data zakończenia:
- Wybrany model finansowania:
- Decyzja dotycząca BASS:
- Zmienione składniki i dokumenty:
- Pozostałe ograniczenia:

