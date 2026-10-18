# MAC-001 — ocena portu AMC Python na macOS

- Status: `Oczekuje`
- Utworzono: 18 października 2026
- Obszar: wxPython, LiteHost, VoiceOver i macOS
- Polecenie uruchamiające: `Uruchom zadanie MAC-001`
- Priorytet: odłożone bez terminu, nie przed pierwszym publicznym wydaniem
  Windows i nie bez nowej jawnej decyzji użytkownika

## Decyzja produktowa z 18 października 2026

Windows pozostaje jedynym planowanym i wspieranym systemem pierwszego wydania.
Port na macOS lub Linux jest technicznie możliwy, ale kosztowny, długotrwały i
zasobożerny; nie jest bieżącym celem AMC. Nie prowadzimy prac portowych tylko po
to, by utrzymywać teoretyczną wieloplatformowość. Zachowujemy czytelne granice
modułów i dokumentację, aby w przyszłości zainteresowany współtwórca mógł
przygotować niezależny port. Poniższy plan jest materiałem na taką przyszłą
ocenę, a nie aktywnym zobowiązaniem.

## Cel

Przygotować mały, nieprodukcyjny prototyp odpowiedzi na pytanie, ile z AMC
Python można rzeczywiście przenieść na macOS bez przepisywania programu oraz
czy podstawowy interfejs jest używalny z VoiceOver.

## Potwierdzony punkt wyjścia

- Produktem docelowym jest AMC Python z interfejsem wxPython, nie historyczne
  okno WPF.
- Aktualny interfejs używa wxPython 4.3.1 i natywnych kontrolek. Dla tej wersji
  istnieją paczki macOS dla Apple Silicon i komputerów Intel.
- wxPython pomaga przenieść układ okien, zdarzenia i dużą część logiki
  interfejsu, ale nie gwarantuje dostępności VoiceOver. Rozszerzalna klasa
  `wx.Accessible` jest opisana jako mechanizm MSW; na macOS trzeba polegać na
  dostępności natywnych kontrolek wxOSX i sprawdzić każdą z nich w praktyce.
- LiteHost jest obecnie produktem Windows: używa `net8.0-windows`, NAudio,
  WASAPI, Media Foundation, DPAPI, SMTC, rejestru i natywnych bibliotek
  `win-x64`. Samo uruchomienie tego hosta na macOS nie jest możliwe.

## Zakres pierwszego badania

1. Uruchomić odizolowany prototyp wxPython na prawdziwym Macu, bez audio i bez
   danych użytkownika.
2. Sprawdzić z VoiceOver: menu, `wx.ListCtrl`, pola edycji, pola wyboru,
   zakładki ustawień, dialogi, fokus, skróty oraz powrót po zamknięciu.
3. Wyodrębnić listę importów i fragmentów GUI zależnych od Win32, NVDA,
   globalnych skrótów oraz ścieżek Windows.
4. Zaprojektować adapter hosta macOS dla audio, urządzeń, poświadczeń,
   zasilania i integracji systemowej, bez zmiany wersjonowanego protokołu
   JSON-lines, jeżeli to możliwe.
5. Osobno sklasyfikować funkcje: możliwe od razu, wymagające adaptera,
   niedostępne u dostawcy i wymagające innego interfejsu natywnego.

## Poza zakresem

- Budowanie pełnego wydania macOS teraz.
- Udawanie, że zgodność wxPython oznacza zgodność VoiceOver.
- Przepisywanie działającej wersji Windows przed wynikiem prototypu.
- Publikacja w Mac App Store, podpisywanie i notaryzacja.

## Kryteria decyzji

Port jest uzasadniony dopiero wtedy, gdy prosty prototyp przechodzi na
prawdziwym Macu test VoiceOver i istnieje realna grupa użytkowników do dalszego
odbioru. Jeżeli podstawowa lista, dialogi albo fokus nie są stabilne, należy
porównać cienki natywny interfejs Swift/SwiftUI korzystający z tego samego
protokołu zamiast rozbudowywać obejścia wxPython.

## Wynik wykonania

Do uzupełnienia po pracy:

- Data zakończenia:
- Sprzęt i wersja macOS:
- Wersja VoiceOver i wxPython:
- Wynik prototypu:
- Macierz funkcji:
- Rekomendacja:

