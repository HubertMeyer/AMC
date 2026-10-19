# AMC13 — End w Time Shifcie Radia wraca na żywo

- Status: **Rozszerzenie skoków procentowych gotowe w źródłach i testach;
  instalacja nadal zawiera wcześniejszą poprawkę End**
- Data realizacji w AMC Test: 2026-10-19
- Repozytorium wykonawcze: `D:\Projekty Codex\AMC - integracja wxPython`
- Materiał historyczny, tylko do odczytu:
  `D:\Projekty Codex\Accessible Multimedia Controller\AMC13_TIMESHIFT_RADIA_2026-10-18.md`.

## Materiał do dokumentacji użytkownika

W otwartym odtwarzaczu Radia klawisz `End` wraca z bufora Time Shiftu do
transmisji na żywo. Jednocześnie przywraca normalne tempo `1,00x` i AMC mówi
„Na żywo”. `Home` nadal przechodzi na początek dostępnego bufora.

Polecenie „Wróć do transmisji na żywo” jest widoczne w menu, pomocy
`Ctrl+F1`, pełnej pomocy klawiatury i palecie `Ctrl+Shift+K` tylko w sesji
Radia, w odtwarzaczu i przy aktywnym strumieniu. `NVDA+End` pozostaje
poleceniem czytnika ekranu i nie jest przechwytywane przez AMC.

Na zwykłym pliku, podcaście lub filmie `End` zachowuje dotychczasowe znaczenie
końca materiału. Na liście pozostaje zwykłym klawiszem listy.

W odtwarzaczu Radia cyfry `0`–`9` przechodzą odpowiednio do 0–90% aktualnego
bufora Time Shift. Procent jest liczony od najstarszego dostępnego miejsca do
bieżącego końca bufora, również po zawinięciu jego okna. AMC mówi na przykład
„50% bufora”; przy ustawionym komunikacie procentu i czasu może powiedzieć
„50% bufora, 2:00”. Te same cyfry w pozostałych odtwarzaczach nadal odnoszą
się do długości materiału.

## Uzasadnienie i decyzje

- Time Shift zna koniec transmisji jako osobną operację hosta
  `radio.jumpLive`; nie próbuje wyliczać nieznanej długości pliku radiowego.
- Powrót na żywo zeruje wcześniejsze przyspieszenie, ponieważ użytkownik
  oczekuje prawdziwego bieżącego strumienia, a nie dalszego nadrabiania.
- Jedno polecenie i ten sam warunek dostępności zasilają wykonanie, menu,
  `Ctrl+F1`, pełną pomoc oraz paletę. Niedostępna funkcja nie jest reklamowana.
- Skok procentowy ma osobną operację hosta, ponieważ zwykła długość strumienia
  radiowego jest nieznana, a po zawinięciu bufora jego początek nie jest zerem
  czasu całej transmisji.
- Zapis zaznaczonego fragmentu Time Shiftu pozostaje osobnym, późniejszym
  etapem.

### Korekta użytkownika z 2026-10-18

Ta decyzja zastępuje omyłkowe odniesienie do `Ctrl+Shift+J`. Problem dotyczy
wyłącznie klawisza `End` w już otwartym odtwarzaczu Time Shiftu: ma on wracać
do transmisji na żywo.

Ta sama korekta doprecyzowuje późniejszy zapis fragmentu: nie chodzi o
wycinanie żywego źródła, lecz o zaznaczenie zakresu istniejącego bufora i zapis
do nowego pliku. Funkcja ta pozostaje poza AMC13.

### Korekta użytkownika z 2026-10-19

Ta decyzja zastępuje wcześniejsze odłożenie wszystkich skoków procentowych.
Same skoki cyframi `0`–`9` zostały dołączone do AMC13 jako małe rozszerzenie.
Zaznaczanie zakresu i zapis fragmentu nadal pozostają poza tym etapem.

## Zmienione miejsca

- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/amc_wx_lite/transport_parity.py`
- `wxlite/tests/test_radio_jump_live.py`
- `wxlite/tests/test_transport_parity_gui_wiring.py`

## Testy i wynik

- Nowe testy potwierdzają osobne znaczenie `End` dla Radia, niezmienione
  znaczenie w pozostałych odtwarzaczach, warunki menu i pomocy, dedykowaną
  operację hosta oraz komunikat i widoczne tempo `1,00x`.
- Wspólna ukierunkowana regresja AMC05/AMC13: **224 zaliczone**.
- Pełna regresja wxPython: **1770 zaliczonych, 110 pominiętych i 11 podtestów
  zaliczonych** w 82,91 s.
- LiteHost Release: kompilacja zaliczona, 0 ostrzeżeń i 0 błędów.
- Pełne LiteHost ProtocolTests: **20 zestawów zaliczonych**.
- Core SmokeTests: zaliczone, kod wyjścia 0.
- Bramkę bezpieczeństwa przed pełną kompilacją zaliczono 19 października 2026:
  0 aktywnych harmonogramów, 0 plików `.amc-partial` w folderze nagrań i 0
  rosnących plików.

Tuż przed promocją pełną regresję wxPython powtórzono: **1770 zaliczonych,
110 pominiętych i 11 podtestów zaliczonych** w 85,32 s. Procedura promocji
zbudowała 1660 plików, zweryfikowała manifest i sumy SHA-256, zainstalowała
wersję oraz potwierdziła uruchomiony proces i tytuł „AMC Test”. Ręczna próba
klawiatury i NVDA pozostaje osobnym etapem.

Po rozszerzeniu o skoki procentowe ukierunkowana regresja Python skoków,
komunikatów i pomocy ma wynik **79 zaliczonych**. Odizolowany test rzeczywistego
bufora C# zaliczył **20 pozycji i próbek**: częściowy bufor, zawinięcie, tempo,
pauzę, odmowy i pomoc. LiteHost Debug skompilował się z 0 ostrzeżeń i 0 błędów.
Przed kompilacją pięciosekundowy pomiar wykazał 0 plików `.amc-partial` i 0
plików rosnących. Nie zamykano ani nie podmieniano działającej aplikacji.
Osobna regresja wspólnego katalogu skrótów, `Ctrl+F1`, palety `Ctrl+Shift+K`
i menu ma wynik **138 zaliczonych**.

## Znane ograniczenia

- Nie dodano zaznaczania ani eksportu fragmentu bufora do nowego pliku.
- Ręcznie po instalacji trzeba sprawdzić `Home`, przewijanie, zmianę tempa,
  `End`, `NVDA+End`, menu, `Ctrl+F1`, `Ctrl+Shift+K` i powrót fokusu.
- Rozszerzenie skoków procentowych nie zostało jeszcze zbudowane do paczki,
  zainstalowane ani odebrane z NVDA w bieżącej instalacji.

## Wersja i commit

- Implementacja i testy: `12b5856ee2f90be8b6d6b501c09ac27cf749085f` —
  `feat(amc05-amc13): oznacz odtwarzanie i napraw End radia`.
- Rozszerzenie skoków procentowych: commit następujący po tym zapisie.
- Dokumentacja zadania: commit następujący po commicie implementacji.
- Kompilacja: Release — zaliczona.
- Instalacja: `2026.10.19-ca7dfa167728317728be534da7a71f8484ebe573-b9d47b3d`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonano; brak wysyłania do GitHuba i brak wydania publicznego.

