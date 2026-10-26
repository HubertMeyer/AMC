# Weryfikacja Frontier Smart — AMC 0.1.0-alpha.424

Data: 22 października 2026 r.

Stan źródeł: niezatwierdzone zmiany w kanonicznym repozytorium
`D:\Projekty Codex\Accessible Multimedia Controller`, oparte na commicie
`16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`. Ten rekord nie jest dowodem
commita, instalacji ani wydania GitHub.

## Zachowanie widoczne dla użytkownika

- Nowa sesja Frontier Smart sama rozpoczyna SSDP, zanim użytkownik poda PIN.
- Wykryty adres pojawia się jako jednoznacznie opisany kandydat na liście.
- PIN potwierdza zaznaczone urządzenie w drugim kroku.
- Ręczny adres IP jest zwiniętą opcją awaryjną.
- Podczas pierwszego skanu fokus pozostaje na liście; nie przechodzi na
  przycisk zamknięcia.
- Po zapisaniu urządzenia `Ctrl+F5` otwiera listę bez automatycznego skanu.
- Osobny przycisk **Wykryj nowe urządzenia** uruchamia skan na żądanie.
- `F5` odświeża zapisane urządzenie, a na kandydacie lub pustej liście uruchamia
  wykrywanie.
- Starszy firmware bez działającego `GET_MULTIPLE` przechodzi na pojedyncze
  odczyty także wtedy, gdy błąd FSAPI jest zwrócony przy HTTP 200.

Przykładowe komunikaty dla NVDA:

- „Wykrywanie urządzeń Frontier Smart w sieci lokalnej…”;
- „Wykryto jedno urządzenie Frontier Smart. Wybierz je, wpisz PIN i użyj
  Połącz i dodaj.”;
- „Urządzenie odrzuciło PIN. Sprawdź go i spróbuj ponownie.”;
- „Nie wykryto urządzenia Frontier Smart. Możesz ponowić wykrywanie albo
  rozwinąć dodawanie ręczne po adresie IP.”

## Wykonane komendy i wyniki

1. `dotnet restore AccessibleMediaController.sln --runtime win-x64
   -p:NuGetAudit=false --disable-build-servers -m:1`
   — zaliczone dla sześciu projektów. Bez `-m:1` lokalny MSBuild kończył się
   kodem błędu przy 0 raportowanych błędach; skrypt `build.ps1` został
   ujednolicony z działającym przebiegiem.
2. `dotnet build AccessibleMediaController.sln --configuration Release
   --no-restore --disable-build-servers -m:1`
   — sukces, 0 ostrzeżeń, 0 błędów.
3. `AccessibleMediaController.FrontierSmart.SmokeTests`
   — 13/13 zaliczonych.
4. Celowa próba negatywna bez przejścia awaryjnego po błędzie FSAPI przy
   HTTP 200 — oczekiwane niepowodzenie 12/13; po przywróceniu kodu 13/13.
5. `AccessibleMediaController.FrontierSmart.Windows.SmokeTests`
   — 6/6 grup zaliczonych, w tym pierwsze automatyczne wykrywanie, brak
   ponownego skanu przy zapisanych urządzeniach, etykiety UI Automation i
   początkowy fokus.
6. Pełny `AccessibleMediaController.Core.SmokeTests` z `TEMP` i `TMP`
   skierowanymi do `wyniki-testow\temp-alpha424`
   — zaliczony, kod wyjścia 0.
7. Pełny `AccessibleMediaController.Windows.SmokeTests` w tym samym katalogu
   tymczasowym — brak końcowego wyniku. Przed przerwaniem zgłosił cztery
   timeouty lub brak oczekiwanego okna w starych testach UI Sonosa, jeden błąd
   dostępu w geście kopiowania Sonosa, a następnie nieobsłużony brak dostępu do
   schowka systemowego. Nie są to testy kodu Frontier Smart, ale pełnego
   przebiegu Windows nie uznaje się za zaliczony.
8. `dotnet publish` dla `win-x64`, self-contained i single-file
   — zaliczone. Skład pakietu sprawdzono względem listy `build.ps1`; suma
   natywnego hosta Librespot jest zgodna z wartością oczekiwaną.

## Gotowy pakiet

Katalog:

`D:\Projekty Codex\Accessible Multimedia Controller\publish\AccessibleMediaController-0.1.0-alpha.424`

Program:

`D:\Projekty Codex\Accessible Multimedia Controller\publish\AccessibleMediaController-0.1.0-alpha.424\AccessibleMediaController-0.1.0-alpha.424.exe`

- ProductVersion: `0.1.0-alpha.424`;
- rozmiar programu: 194 308 496 bajtów;
- pakiet: 216 590 396 bajtów i 1074 pliki;
- SHA-256 programu:
  `43F5FE3ED22F21256EB2D19A4653625F9A2E909711F3E46916E0E0A74DD4C40D`.

Na komputerze nie znaleziono `ISCC.exe`, dlatego nie zbudowano instalatora
Inno Setup. Pakiet nie został zainstalowany ani uruchomiony. Nie wykryto
działającego procesu AMC, ale nie wykonywano operacji zamykania ani podmiany
zainstalowanego programu.

## Pozostałe ograniczenia

- Syntetyczne SSDP i odpowiedzi HTTP nie potwierdzają wykrycia konkretnego
  radia w sieci użytkownika.
- Do próby sprzętowej pozostają: wykrycie, akceptacja PIN-u, odczyt stanu,
  transport, tryby i presety.
- Pasma 2,4 i 5 GHz mogą się widzieć przy wspólnym LAN; izolacja klientów,
  osobne VLAN-y albo filtrowanie multicastu mogą nadal zablokować SSDP.
- Nie usunięto katalogów kompilacji, stagingu ani wyników testowych przed
  akceptacją próby użytkownika.
