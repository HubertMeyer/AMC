# AMC05 — odtwarzany element na listach

- Status: **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA**
- Data realizacji w AMC Test: 2026-10-19
- Repozytorium wykonawcze: `D:\Projekty Codex\AMC - integracja wxPython`
- Materiał historyczny, tylko do odczytu:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC05_ODTWARZANY_ELEMENT_NA_LISTACH_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

Na właściwych listach Plików lokalnych, Podcastów i YouTube oraz Spotify
bieżący materiał otrzymuje na początku wiersza osobny stan „Odtwarzane” albo
„Wstrzymane”. Stan nie zastępuje tytułu ani pozostałych szczegółów wiersza.

Oznaczenie powstaje tylko wtedy, gdy AMC ma potwierdzoną sesję, stabilny
identyfikator materiału i bieżący stan odtwarzacza. Zatrzymanie, przejście z
materiału A do B albo awaria usuwa nieaktualne oznaczenie. Folder, playlista,
kanał, seria, zakładka i inny kontener nie są oznaczane jak odtwarzany utwór.

Wyniki wyszukiwania otrzymują ten sam stan wyłącznie wtedy, gdy wynik należy do
tej samej sesji i ma dokładnie ten sam identyfikator co odtwarzany materiał.
Odświeżenie napisu nie zmienia zaznaczenia ani położenia fokusu.

Sonos i WiiM nadal pokazują stan tylko na podstawie świeżej, wiarygodnej
migawki urządzenia. Brak świeżego stanu nie jest zastępowany zgadywaniem.

## Uzasadnienie i decyzje

- Stan odtwarzania jest osobnym polem modelu wiersza. Dzięki temu nie niszczy
  tytułu, szczegółów ani komunikatu o stanie elementu.
- Porównanie używa identyfikatora i sesji, a nie samej nazwy. Dwa utwory o tym
  samym tytule nie mogą zostać oznaczone jednocześnie.
- Odświeżenie aktywności aktualizuje jedynie tekst istniejących wierszy. Nie
  przebudowuje widoku, nie wybiera elementu i nie przenosi fokusu.
- TIDAL nie dostał pozornego oznaczenia, ponieważ obecny kontrakt nie dostarcza
  jeszcze równie pewnej tożsamości i stanu dla wszystkich widoków.
- Użyte słowa są celowo krótkie i użytkowe: „Odtwarzane” oraz „Wstrzymane”. Do
  nazw dostępnych nie trafiają nazwy klas, właściwości ani identyfikatory.

### Korekta użytkownika z 2026-10-18

Zastępuje wcześniejsze zachowanie ograniczone praktycznie do listy Radia.
Odtwarzany element ma być rozpoznawalny także na innych właściwych listach, ale
bez oznaczania kontenerów i bez utraty dotychczasowych szczegółów wiersza.

## Zmienione miejsca

- `wxlite/amc_wx_lite/playback_activity.py`
- `wxlite/amc_wx_lite/list_model.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/tests/test_playback_activity.py`

## Testy i wynik

- Ukierunkowane testy AMC05 i AMC13 oraz ich regresji: **224 zaliczone**.
- Pełna regresja wxPython po ostatecznej zmianie kodu: **1770 zaliczonych,
  110 pominiętych i 11 podtestów zaliczonych** w 82,91 s.
- Ponowna lekka kontrola po korekcie polskich znaków w pomocy wykonała
  wszystkie **10** nowych testów AMC05/AMC13 bez błędu ich asercji. Repozytoryjny
  uruchamiacz biblioteki standardowej zgłosił osobno cztery zastane moduły
  wymagające `pytest`; pełny zestaw z `pytest` był już wcześniej zielony.
- LiteHost w konfiguracji Release: kompilacja zaliczona, 0 ostrzeżeń i 0
  błędów.
- Pełne LiteHost ProtocolTests: **20 zestawów zaliczonych**.
- Core SmokeTests: zaliczone, kod wyjścia 0.
- `git diff --check`: bez błędów przed zatwierdzeniem źródeł.

Po commicie dokumentacji pełną regresję wxPython powtórzono: **1770
zaliczonych, 110 pominiętych i 11 podtestów zaliczonych** w 85,32 s. Procedura
promocji zbudowała 1660 plików, sprawdziła manifest i sumy SHA-256,
zainstalowała wersję i potwierdziła uruchomiony proces oraz tytuł „AMC Test”.
W samej procedurze testy oznaczono jako pominięte, ponieważ pełny zestaw został
wykonany bezpośrednio tuż przed promocją. Ręczny odbiór NVDA nadal pozostaje
osobnym etapem.

## Znane ograniczenia

- Ręczny odbiór NVDA pozostaje do wykonania po instalacji: początkowo
  zaznaczony element, przejście A → B, pauza i wznowienie, zatrzymanie,
  wyszukiwanie, powrót fokusu oraz ponowne otwarcie listy.
- Lista wyników wyszukiwania jest migawką i otrzymuje stan przy utworzeniu lub
  kontrolowanym odświeżeniu, bez samoczynnego przestawiania fokusu.
- Sonos i WiiM zależą od świeżości stanu adaptera. TIDAL celowo nie zgaduje
  aktywnego wiersza.

## Wersja i commit

- Implementacja i testy: `12b5856ee2f90be8b6d6b501c09ac27cf749085f` —
  `feat(amc05-amc13): oznacz odtwarzanie i napraw End radia`.
- Dokumentacja zadania: commit następujący po commicie implementacji.
- Kompilacja: Release — zaliczona.
- Instalacja: `2026.10.19-ca7dfa167728317728be534da7a71f8484ebe573-b9d47b3d`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonano; brak wysyłania do GitHuba i brak wydania publicznego.

