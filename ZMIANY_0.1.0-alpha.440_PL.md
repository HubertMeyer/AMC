# AMC Public 0.1.0-alpha.440 — projekt opisu zmian

> Projekt do korekty i zatwierdzenia użytkownika. Nie jest automatycznie
> publikowaną instrukcją ani dowodem instalacji.

Ta aktualizacja koryguje profil usług opublikowanego `alpha.439`. AMC Public
udostępnia WiiM i Frontier Smart, natomiast nie udostępnia Sonosa, Spotify ani
TIDAL-a. Pozostałe funkcje najnowszej bazy AMC Test pozostają bez zmian.

## Zachowanie Public

- Menedżer sesji, menu Widok, pomoc kontekstowa i paleta poleceń pokazują
  Frontier Smart, a nie pokazują Sonosa.
- Pakiet zawiera moduł Frontier Smart i fizycznie nie zawiera modułu Sonosa.
- Aktualizacja z `alpha.439` usuwa pozostawiony moduł Sonosa z katalogu
  instalacji i przyjmuje jego starszy manifest jako bezpieczny stan wejściowy.
- WiiM pozostaje dostępny. Spotify i TIDAL pozostają wyłączone wewnątrz AMC,
  a rozpoznane utwory korzystają z publicznego wyszukiwania WWW.
- Logowanie Google do YouTube i konfiguracja OAuth Google nadal nie należą
  do profilu ani paczki Public.

## Stan techniczny

- wersja techniczna: `0.1.0-alpha.440`;
- testy celowane Pythona: 100/100 zaliczone;
- testy Launchera i aktualizatora: 38/38 zaliczone;
- paczka, instalator i publikacja: do uzupełnienia po wykonaniu;
- instalacja lokalna nie zostanie zmieniona bez osobnego, bezpiecznego
  przebiegu aktualizacji.
