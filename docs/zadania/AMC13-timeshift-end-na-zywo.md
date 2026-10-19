# AMC13 — End w Time Shifcie Radia wraca na żywo

- Status: **Wdrożone i zainstalowane w AMC Test; czeka na ręczny odbiór NVDA**
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

## Uzasadnienie i decyzje

- Time Shift zna koniec transmisji jako osobną operację hosta
  `radio.jumpLive`; nie próbuje wyliczać nieznanej długości pliku radiowego.
- Powrót na żywo zeruje wcześniejsze przyspieszenie, ponieważ użytkownik
  oczekuje prawdziwego bieżącego strumienia, a nie dalszego nadrabiania.
- Jedno polecenie i ten sam warunek dostępności zasilają wykonanie, menu,
  `Ctrl+F1`, pełną pomoc oraz paletę. Niedostępna funkcja nie jest reklamowana.
- Regresję naprawiono wąsko. Skok procentowy i zapis zaznaczonego fragmentu
  Time Shiftu nie zostały dołączone do tej zmiany.

### Korekta użytkownika z 2026-10-18

Ta decyzja zastępuje omyłkowe odniesienie do `Ctrl+Shift+J`. Problem dotyczy
wyłącznie klawisza `End` w już otwartym odtwarzaczu Time Shiftu: ma on wracać
do transmisji na żywo.

Ta sama korekta doprecyzowuje późniejszy zapis fragmentu: nie chodzi o
wycinanie żywego źródła, lecz o zaznaczenie zakresu istniejącego bufora i zapis
do nowego pliku. Funkcja ta pozostaje poza AMC13.

## Zmienione miejsca

- `src/AccessibleMediaController.LiteHost/LiteEngineHandlers.cs`
- `wxlite/amc_wx_lite/host_client.py`
- `wxlite/amc_wx_lite/shortcuts.py`
- `wxlite/amc_wx_lite/menu_model.py`
- `wxlite/amc_wx_lite/gui.py`
- `wxlite/tests/test_radio_jump_live.py`

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

## Znane ograniczenia

- Nie dodano skoku procentowego w Time Shifcie.
- Nie dodano zaznaczania ani eksportu fragmentu bufora do nowego pliku.
- Ręcznie po instalacji trzeba sprawdzić `Home`, przewijanie, zmianę tempa,
  `End`, `NVDA+End`, menu, `Ctrl+F1`, `Ctrl+Shift+K` i powrót fokusu.

## Wersja i commit

- Implementacja i testy: `12b5856ee2f90be8b6d6b501c09ac27cf749085f` —
  `feat(amc05-amc13): oznacz odtwarzanie i napraw End radia`.
- Dokumentacja zadania: commit następujący po commicie implementacji.
- Kompilacja: Release — zaliczona.
- Instalacja: `2026.10.19-ca7dfa167728317728be534da7a71f8484ebe573-b9d47b3d`,
  manifest, sumy i uruchomienie zweryfikowane 19 października 2026.
- Publikacja: nie wykonano; brak wysyłania do GitHuba i brak wydania publicznego.

