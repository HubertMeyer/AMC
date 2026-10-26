# REC-002 — prawa strzałka w nagrywanych plikach

- Status: **Zrobione; kod, testy, build i instalacja AMC Test są zaliczone**.
- Data wdrożenia: 26.10.2026.
- Instalacja: `D:\Projekty Codex\AMC Python`.

## Zachowanie widoczne dla użytkownika

W widoku aktualnie nagrywanych plików `Strzałka w prawo` podaje format,
rzeczywistą nazwę tworzonego pliku i folder. Dla folderu domyślnego mówi
`folder domyślny`; dla własnego położenia podaje ścieżkę. Nie powtarza nazwy
stacji ani adresu strumienia.

Ta sama zasada działa w oknie harmonogramów nagrywania. Gdy plik nie został
jeszcze utworzony, NVDA otrzymuje uczciwy tekst `plik przygotowywany`.
Polecenie istnieje również w menu Radia, pomocy kontekstowej, pełnej pomocy i
palecie pod użytkową nazwą `Ustawienia pliku nagrania`.

## Uzasadnienie i decyzje

- Zadanie zostało wcześniej przygotowane, a 26.10.2026 użytkownik polecił
  jawnie dołączyć je do bieżącej wersji AMC Test.
- Prawa strzałka zmienia znaczenie tylko w widoku `Nagrywane`; na zwykłej
  liście Radia pozostaje natywną nawigacją.
- Model i mowa nie ujawniają technicznego stanu nagrania ani identyfikatora.

## Testy i wynik

- Testy celowane sprawdzają aktywne nagranie, harmonogram, folder domyślny i
  własny, brak nazwy stacji i URL oraz ograniczenie skrótu do widoku
  `Nagrywane`.
- Końcowy zestaw poleceń i menu: **106/106**.
- Pełna regresja promocji: **2057 zaliczonych, 111 pominiętych, 13 podtestów
  zaliczonych**.
- LiteHost Release i serwer protokołu: **0 ostrzeżeń, 0 błędów**.

## Znane ograniczenia

Ręczny odbiór z NVDA powinien jeszcze potwierdzić zwięzłość mowy w prawdziwym
nagraniu i harmonogramie oraz brak utraty fokusu po ponownym otwarciu.

## Materiał do dokumentacji użytkownika

> W widoku Nagrywane albo w harmonogramie naciśnij prawą strzałkę, aby usłyszeć
> format, nazwę przygotowywanego pliku i folder zapisu. To samo polecenie jest
> dostępne jako Ustawienia pliku nagrania w menu Radia.

## Projekt opisu zmian

> Prawa strzałka w aktywnych nagraniach i harmonogramach podaje teraz format,
> nazwę pliku oraz folder zapisu bez powtarzania stacji i adresu.

## Wersja i commit

- Commit: `bba5e92d687ade1998e79c88656e1a5d545abcf2`.
- Pakiet: `39f0d3f2`.
- Okno: `AMC Test — 26.10.2026, 13:32`.
- Publikacja: nie wykonywano.
