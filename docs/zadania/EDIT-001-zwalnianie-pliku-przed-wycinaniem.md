# EDIT-001 — zwalnianie pliku przed wycinaniem

Status: **Zrobione**

## Zgłoszenie i zachowanie użytkowe

27.10.2026 użytkownik odtworzył z historii nagrywania plik MP3 trwający około
1 godziny 48 minut, a następnie dwukrotnie próbował usunąć z niego fragment.
AMC przez około 15 sekund czekał, po czym nie wykonywał cięcia. Log wykazał,
że własny odtwarzacz AMC nadal lub ponownie trzymał plik otwarty.

Po poprawce uruchomienie usuwania fragmentu zatrzymuje lokalne odtwarzanie,
czeka na faktyczne zamknięcie dekodera i dopiero potem uruchamia edycję.
Do końca operacji AMC odmawia ponownego otwarcia lokalnego pliku czytelnym
komunikatem. Radio i odtwarzanie zewnętrzne nie są blokowane.

## Materiał do dokumentacji użytkownika

- Podczas usuwania fragmentu AMC sam zatrzymuje odtwarzanie edytowanego pliku.
- Nie trzeba wcześniej zamykać odtwarzacza ani naciskać `Escape`.
- Ponowna próba odtworzenia lokalnego pliku przed końcem operacji zwraca
  komunikat: „Trwa usuwanie fragmentu. Poczekaj na zakończenie edycji przed
  ponownym odtworzeniem pliku.”
- Gdy dekoder nie zwolni pliku w wyznaczonym czasie, AMC nie zmienia oryginału
  i podaje jednoznaczny błąd.

## Uzasadnienie i decyzje

`WindowsMediaOutput.Stop()` natychmiast wyciszał dźwięk, ale kosztowne
zamknięcie WASAPI, dekodera i pliku wykonywał w zadaniu tła. Dotychczasowy
edytor jedynie ponawiał próbę wyłącznego otwarcia przez 15 sekund. W czasie
tego oczekiwania polecenie odtwarzania mogło ponownie otworzyć ten sam plik.

Poprawka zachowuje nieblokujące zatrzymanie odtwarzacza, lecz śledzi zadanie
domykające tor. Operacja wycinania jawnie czeka na jego zakończenie. Osobna
blokada w LiteHost serializuje wycinanie z uruchamianiem i wznawianiem plików,
sterowaniem kolejką oraz przełączaniem lokalnego urządzenia audio. Niezależna
kontrola wyłącznego dostępu w edytorze pozostaje ochroną przed innymi procesami.

## Testy i wynik

- `wxlite/tests/test_audio_clip_removal_playback_gate.py`: **3 zaliczone**.
- `AccessibleMediaController.LiteHost`, konfiguracja Release: **kompilacja
  zaliczona, 0 błędów, 0 ostrzeżeń**.
- `AccessibleMediaController.Windows.SmokeTests --audio-clip-original`:
  **zaliczony**; rzeczywiste wycinanie wszystkich testowanych formatów
  podmieniło pliki tymczasowe dopiero po weryfikacji i nie pozostawiło ogona.
- Testy były bezokienne. Nie uruchamiano ani nie instalowano aplikacji.

## Znane ograniczenia

- Poprawka nie zamyka uchwytów należących do obcych programów. W takim
  przypadku pozostaje bezpieczna odmowa bez zmiany oryginału.
- Nie wykonano jeszcze instalacji, publikacji GitHub ani ręcznego odbioru z
  NVDA; są to osobne etapy następnego wydania.

## Wersja i commit

- Gałąź robocza: `codex/konfigurowalne-skroty-20261026`.
- Commit: commit zawierający ten plik zadania.
- Pełny build paczki, instalacja i wydanie GitHub: jeszcze niewykonane.
