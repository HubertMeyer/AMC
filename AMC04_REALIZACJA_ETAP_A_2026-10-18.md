# AMC04 — realizacja, etap A: nazwane zakładki

Data: 18 października 2026 r.

Tryb pracy: poziom A, bez kompilacji i bez uruchamiania AMC.

## Ustalenie

- `Shift+Page Up/Down` przechodzi po wszystkich zakładkach bieżącego materiału.
- `Ctrl+Shift+Page Up/Down` przechodzi wyłącznie po zakładkach posiadających nazwę, tworzonych przez `Ctrl+Shift+B`.
- Nazwana zakładka nadal jest zakładką. Nie staje się rozdziałem.
- `Ctrl+Shift+strzałka w lewo/prawo` pozostaje nawigacją po rzeczywistych rozdziałach materiału.
- WiiM nie otrzymuje zakładek w tym etapie. Istniejący filtr poleceń WiiM odrzuca nowe polecenia tak samo jak pozostałe polecenia zakładek.

## Zmiany

1. `BookmarkIndex` otrzymał osobny widok nazwanych zakładek oraz osobne wyszukiwanie względne i sąsiednie. Filtr opiera się na nazwie użytkowej, nie na typie technicznym ani identyfikatorze.
2. Dodano pierwszoklasowe polecenia poprzedniej i następnej nazwanej zakładki. Dzięki temu paleta, pomoc i wykonanie nie udają nawigacji po rozdziałach.
3. Dodano jeden resolver klawiatury dla obu par zakładek:
   - `Shift+Page Up/Down` — wszystkie zakładki;
   - `Ctrl+Shift+Page Up/Down` — tylko nazwane.
4. Kursor powtarzanej nawigacji pamięta, czy użytkownik poruszał się po wszystkich, czy tylko po nazwanych zakładkach. Zmiana trybu rozpoczyna wyszukiwanie od bieżącej pozycji i nie kontynuuje od punktu z drugiego zbioru.
5. Dodano użytkowe etykiety do menu głównego i menu odtwarzacza. Żaden identyfikator polecenia ani nazwa klasy nie trafia do NVDA.
6. Uzupełniono:
   - pomoc kontekstową `Ctrl+F1`;
   - paletę poleceń `Ctrl+Shift+K`;
   - krótki tekst pomocy odtwarzacza;
   - komunikaty graniczne dla braku poprzedniej lub następnej nazwanej zakładki.

## Przygotowane testy

- filtrowanie zakładek bez nazwy;
- wyszukiwanie nazwanej zakładki względem bieżącego czasu;
- przejście sąsiednie tylko w zbiorze nazwanych zakładek;
- routing czterech skrótów i brak działania poza odtwarzaczem albo podczas obsługi menu;
- przekazanie nowych poleceń przez `CommandRouter`;
- obecność obu nowych skrótów w palecie poleceń.

Testów nie uruchomiono, ponieważ użytkownik polecił nie kompilować. Zostaną wykonane razem z pozostałymi zmianami AMC04/AMC05 przy Bramce 2, po sprawdzeniu, że AMC nie nagrywa.

## Poza zakresem

- Nie dodano rozpoznawania rozdziałów na podstawie ciszy ani innych cech nagrania.
- Nie zmieniano globalnych gestów dodatku NVDA.
- Nie dodawano zakładek do WiiM, TIDAL ani Sonos.
- Nie kompilowano, nie uruchamiano AMC, AMC Python ani NVDA.

## Migracja

Migracja danych nie jest potrzebna. Istniejące zakładki z niepustą nazwą automatycznie należą do zbioru nazwanych zakładek; szybkie zakładki bez nazwy pozostają widoczne tylko w nawigacji ogólnej.
