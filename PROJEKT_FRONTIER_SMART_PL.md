# AMC — integracja urządzeń Frontier Smart przez FSAPI

Data ustalenia: 21 października 2026 r.  
Status: etap C — poprawiony przepływ wykrywania i zgodność starszego firmware'u; oczekuje na test prawdziwego radia  
AMC: `0.1.0-alpha.424`, lokalny commit bazowy `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`

## 1. Decyzja

Obsługę urządzeń opartych na Frontier Smart można dodać do AMC jako
eksperymentalny adapter sieci lokalnej bez dostępu do partnerskiego SDK
producenta. Pierwsza wersja nie wymaga analizy ani modyfikowania firmware'u.

To ustalenie zastępuje wcześniejszą decyzję w `MEDIA_CONTROLLER_PL.md`, według
której adapter Frontier Smart miał czekać na wspierane API. Nowe materiały
potwierdzają wystarczająco stabilny kontrakt społecznościowy:

- urządzenie przyjmuje lokalne żądania HTTP pod `/fsapi/...`;
- uwierzytelnienie odbywa się kodem PIN;
- wartości i wyniki są zwracane jako XML;
- dostępne są odczyt, zapis, listy, odczyt wielu pól i opcjonalne powiadomienia;
- urządzenia można wykrywać przez SSDP za pomocą typu
  `urn:schemas-frontier-silicon-com:fs_reference:fsapi:1`;
- lista węzłów obejmuje zasilanie, głośność, wyciszenie, tryb, transport,
  metadane, presety, korektor, wyłącznik czasowy i nawigację.

Adapter pozostaje oznaczony jako eksperymentalny, ponieważ dokumentacja nie
jest oficjalnym kontraktem producenta, a zestaw węzłów różni się między
modelami i wersjami firmware'u.

## 2. Materiały źródłowe

- [Opis protokołu FSAPI](https://github.com/flammy/fsapi/blob/master/FSAPI.md)
- [Implementacja i narzędzia fsapi-tools](https://github.com/MatrixEditor/fsapi-tools)
- [Dokumentacja narzędzi FSAPI](https://matrixeditor.github.io/fsapi-tools/fsapi-tools.html)
- [Analiza firmware'u](https://matrixeditor.github.io/fsapi-tools/firmware-analysis.html)
- [Archiwum znanych firmware'ów](https://github.com/cweiske/frontier-silicon-firmwares)

Kod AMC nie powinien kopiować implementacji PHP ani Pythona. Protokół jest na
tyle prosty, że adapter można napisać w C# przy użyciu `HttpClient`, bez nowej
zależności uruchomieniowej. `fsapi-tools` ma licencję MIT i pozostaje dobrym
źródłem porównawczym dla nazw węzłów oraz odpowiedzi urządzeń.

## 3. Zakres pierwszej wersji

Pierwszy pionowy etap udostępnia osobną sesję „Frontier Smart” i
następujące funkcje:

1. Automatyczne wykrywanie SSDP oraz ręczne dodanie lokalnego adresu IP.
2. Wprowadzenie PIN-u urządzenia i sprawdzenie połączenia.
3. Zapamiętanie urządzenia oraz wybór aktywnego urządzenia.
4. Odczyt nazwy, identyfikatora radia, wersji firmware'u, zasilania, bieżącego
   trybu, głośności, wyciszenia i informacji „teraz odtwarzane”.
5. Sterowanie zasilaniem, głośnością, wyciszeniem, odtwarzaniem lub pauzą,
   następnym i poprzednim elementem.
6. Lista rzeczywiście dostępnych trybów urządzenia i przełączanie tylko na
   tryby oznaczone przez urządzenie jako wybieralne.
7. Lista presetów bieżącego trybu i ich uruchamianie.
8. Odświeżanie ręczne klawiszem `F5`; kontekstowe `Ctrl+F5` otwiera zarządzanie
   urządzeniami, zgodnie z istniejącą semantyką sesji WiiM i Sonos.

Drugi etap może dodać przeglądanie drzewa `netRemote.nav.list`, wyszukiwanie,
korektor, losowanie, powtarzanie, timer uśpienia, pozycję oraz powiadomienia.
Pełna nawigacja wymaga osobnego kontraktu powrotu, oczekiwania na stan gotowy i
przywracania fokusu; nie powinna być dopisywana jako nieprzetestowany skrót.

## 4. Kontrakt protokołu

Podstawowe wywołania mają postać:

```text
GET /fsapi/GET/<węzeł>?pin=<PIN>
GET /fsapi/SET/<węzeł>?pin=<PIN>&value=<wartość>
GET /fsapi/LIST_GET_NEXT/<węzeł>/-1?pin=<PIN>&maxItems=<liczba>
```

Minimalny zestaw węzłów:

| Funkcja | Węzeł FSAPI |
|---|---|
| Nazwa urządzenia | `netRemote.sys.info.friendlyName` |
| Stabilna tożsamość | `netRemote.sys.info.radioId` |
| Wersja firmware'u | `netRemote.sys.info.version` |
| Zasilanie | `netRemote.sys.power` |
| Głośność | `netRemote.sys.audio.volume` |
| Liczba kroków głośności | `netRemote.sys.caps.volumeSteps` |
| Wyciszenie | `netRemote.sys.audio.mute` |
| Bieżący tryb | `netRemote.sys.mode` |
| Dostępne tryby | `netRemote.sys.caps.validModes` |
| Transport | `netRemote.play.control` |
| Nazwa i opis | `netRemote.play.info.name`, `netRemote.play.info.text` |
| Wykonawca i album | `netRemote.play.info.artist`, `netRemote.play.info.album` |
| Czas i pozycja | `netRemote.play.info.duration`, `netRemote.play.position` |
| Presety trybu | `netRemote.nav.presets` |
| Wybór presetu | `netRemote.nav.action.selectPreset` |

Wartości `netRemote.play.control` udokumentowano jako: 1 — odtwarzaj,
2 — pauza, 3 — następny, 4 — poprzedni. Głośność nie może być przeliczana przy
założeniu stałej skali 0–20; maksymalną liczbę kroków należy odczytać z
`netRemote.sys.caps.volumeSteps` i dopiero wtedy przedstawić procent.

## 5. Sesje i współpraca z UNDOK

Urządzenie obsługuje tylko jedną sesję FSAPI naraz. Utworzenie nowej sesji może
unieważnić sesję innej aplikacji. Dlatego pierwsza wersja AMC powinna wysyłać
zwykłe żądania z PIN-em, bez `CREATE_SESSION` i `GET_NOTIFIES`. Stan można
odświeżać po poleceniu, przy wejściu do sesji i na jawne `F5`.

Opcjonalne powiadomienia długiego odpytywania można dodać później jako
świadomie włączaną funkcję, po sprawdzeniu zachowania z UNDOK i aplikacjami
producentów. AMC nie może po cichu zrywać sterowania w innej aplikacji.

## 6. Architektura AMC

Nowy adapter powinien pozostać oddzielony od WiiM, mimo podobnej roli:

```text
Core/Devices/FrontierSmart/
  FrontierSmartClient.cs
  FrontierSmartModels.cs
  FrontierSmartXmlParser.cs
  FrontierSmartDiscoveryService.cs

Windows/
  FrontierSmartDevicesWindow.xaml
  FrontierSmartDevicesWindow.xaml.cs
  FrontierSmartChoiceWindow.xaml
  FrontierSmartChoiceWindow.xaml.cs
  MainWindow.FrontierSmart.cs
  Services/FrontierSmartPinStore.cs
```

Warstwa klienta odpowiada za ograniczone żądania HTTP, kodowanie parametrów,
XML i statusy `FS_*`. Warstwa sesji AMC odpowiada za polecenia, komunikaty,
fokus, cache bieżącego obrazu urządzenia i mapowanie głośności. Brak węzła
oznacza brak funkcji tego konkretnego urządzenia, a nie awarię całej sesji.

Możliwości należy sondować i przechowywać w pamięci osobno dla każdego
urządzenia oraz wersji firmware'u. Interfejs pokazuje wyłącznie funkcje
potwierdzone przez urządzenie.

## 7. Dostępność i polecenia

- Jedna definicja polecenia musi zasilać menu, skróty, pomoc kontekstową,
  pełną pomoc i paletę poleceń.
- `Ctrl+F5` w sesji Frontier Smart ma znaczyć „Urządzenia Frontier Smart”, a
  `F5` — „Odśwież urządzenie Frontier Smart”. Poza tą sesją polecenia nie są
  reklamowane.
- Każdy wiersz urządzenia otrzymuje jawny tekst użytkowy, na przykład:
  „Radio w kuchni, aktywne, dostępne, DAB, Polskie Radio Dwójka”.
- Listy urządzeń, trybów i presetów muszą mieć jednocześnie jawne
  `AutomationProperties.Name`, `TextSearch.TextPath`, szablon tekstowy i
  użytkowe `ToString()`. NVDA nie może usłyszeć nazwy klasy, rekordu, enumu,
  identyfikatora trybu ani surowego węzła FSAPI.
- Głośność ma być mówiona jako procent oraz, w szczegółach technicznych, jako
  krok, np. „40 procent, krok 8 z 20”. Sama liczba 8 jest niejednoznaczna.
- Po zapisaniu lub anulowaniu fokus wraca do elementu, z którego otwarto okno.
  Ponowne otwarcie wybiera ostatnio potwierdzone urządzenie, tryb lub preset.
- PIN nie może pojawiać się w komunikatach, historii dostępności ani logach.

## 8. Bezpieczeństwo

- Akceptować wyłącznie literalny lokalny adres IPv4 lub IPv6; bez nazw DNS,
  informacji użytkownika w URI i bez przekierowań HTTP.
- Ograniczyć czas połączenia, czas całego żądania i rozmiar odpowiedzi.
- Parametry kodować, a XML czytać bez DTD i bez rozwiązywania zasobów
  zewnętrznych.
- Nie logować pełnego URI, ponieważ zawiera PIN.
- Nie przechowywać PIN-u jako zwykłego pola konfiguracji. Zapamiętany PIN jest
  przechowywany osobno dla urządzenia w Menedżerze poświadczeń Windows.
- Nie wysyłać poleceń zmiany sieci Wi-Fi, PIN-u, aktualizacji ani fabrycznego
  resetu w pierwszej wersji.

## 9. Firmware

Repozytoria firmware'u służą do rozpoznawania modeli, wersji i różnic węzłów.
Nie należy automatycznie pobierać ani instalować firmware'u z AMC. Materiały
opisują różne formaty (`.isu.bin`, `.sap.bin`, `.ota.bin`), różne nagłówki,
szyfrowane obrazy i procedury awaryjnego flashowania. Błędny plik może
unieruchomić radio.

Bezpieczny późniejszy zakres to tylko:

- odczyt aktualnej wersji z urządzenia;
- pokazanie informacji, że w archiwum istnieje znana wersja;
- bez automatycznej oceny zgodności i bez przycisku instalacji.

## 10. Testy wymagane przed wydaniem

1. Parser wartości XML: tekst, liczby ze znakiem i bez znaku, puste wartości,
   listy, `listend`, brak węzła i każdy obsługiwany status `FS_*`.
2. Klient HTTP: poprawne kodowanie PIN-u i wartości, brak przekierowań,
   ograniczenie rozmiaru, anulowanie, timeout, 403, 404 oraz odpowiedź 200 z
   błędem FSAPI.
3. SSDP: odpowiedź poprawna, zduplikowana, bez `LOCATION`, z obcym typem
   usługi i z nielokalnym adresem.
4. Głośność: różne `volumeSteps`, zaokrąglenie procentu i brak dzielenia przez
   zero.
5. Możliwości: brak pojedynczego węzła usuwa tylko odpowiadające mu polecenie.
6. Parzystość poleceń: nazwa, skrót, opis, widoczność, stan włączony i wykonana
   akcja są zgodne w menu, palecie i obu rodzajach pomocy.
7. Test NVDA: początkowy fokus, strzałki, Enter, Escape, Save, Cancel, powrót
   fokusu i ponowne otwarcie dla urządzeń, trybów i presetów.
8. Test na prawdziwym radiu: wykrycie, błędny PIN, wyłączone radio, zmiana
   trybu, preset, głośność, transport oraz równoległe użycie UNDOK.

## 11. Stan wykonania z 21 października 2026 r.

### Zachowanie użytkowe

- Istniejące okno otwierane przez `Ctrl+Shift+S` i `Ctrl+0` nosi nazwę
  **Menedżer sesji**. Dodano do niego przycisk **Nowa sesja Frontier Smart…**;
  nie powstał drugi, konkurencyjny menedżer.
- Kreator wymaga potwierdzonego urządzenia. Pozwala wykryć radio przez SSDP albo
  podać lokalny adres IP, podać PIN, sprawdzić połączenie, wybrać aktywne radio
  i dopiero wtedy utworzyć sesję.
- Utworzona sesja otrzymuje pierwszy wolny skrót `Ctrl+cyfra`, zaczynając od
  `Ctrl+9`. Po ponownym uruchomieniu wraca tylko sesja wcześniej utworzona przez
  użytkownika; sama obecność kodu adaptera nie dodaje jej automatycznie.
- `Ctrl+F5` otwiera urządzenia Frontier Smart, `F5` odświeża stan,
  `Ctrl+Alt+P` otwiera presety bieżącego trybu, a menu Widok udostępnia tryby.
  Standardowe polecenia AMC obsługują zasilanie, głośność, wyciszenie,
  odtwarzanie lub pauzę, następny i poprzedni element oraz informację o czasie.
- Bezpośrednie skróty presetów używają tej samej numeracji co inne sesje, ale
  uruchamiają sprzętowy preset bieżącego trybu. Frontier Smart nie pokazuje
  polecenia przypisywania lokalnego presetu AMC jako presetu urządzenia.
- PIN nie trafia do stanu JSON, kopii konfiguracji ani komunikatów. Jest
  przechowywany w Menedżerze poświadczeń Windows pod kluczem zależnym od
  stabilnego identyfikatora urządzenia.

### Zmienione miejsca

- Rdzeń protokołu: `src/AccessibleMediaController.Core/Devices/FrontierSmart`.
- Stan i zapis: `AppSettings.cs` oraz `ConfigurationStore.cs`.
- Wspólny model poleceń, paleta i pomoc: `CommandIds.cs`, `CommandCatalog.cs`
  oraz `CommandPaletteSearch.cs`.
- Menedżer sesji i okna urządzeń, trybów oraz presetów:
  `SessionSelectionWindow`, `FrontierSmartDevicesWindow` i
  `FrontierSmartChoiceWindow`.
- Integracja sesji i odtwarzacza: `MainWindow.FrontierSmart.cs` oraz istniejące
  menu i router wejścia w `MainWindow`.

### Sprawdzenia i ich rzeczywiste wyniki

- `AccessibleMediaController.FrontierSmart.SmokeTests`: **13/13 zaliczonych**.
  Obejmuje parser XML, URI, głośność, SSDP, żądania z PIN-em, brak identyfikatora
  sesji, minimalne sprawdzenie tożsamości oraz zgodność ze starszym firmware'em
  bez `GET_MULTIPLE` albo z błędem FSAPI zwróconym przy HTTP 200.
- `AccessibleMediaController.FrontierSmart.Windows.SmokeTests`: **6/6
  zaliczonych**. Obejmuje wspólny katalog poleceń, dynamiczny slot sesji,
  użytkowe etykiety wierszy, początkowy fokus i ponowne otwarcie Menedżera
  sesji, kreatora urządzeń oraz listy trybów i presetów.
- Pełny `AccessibleMediaController.Core.SmokeTests`: **zaliczony, kod wyjścia
  0**. Test wykrył wcześniej brak sekcji `FrontierSmart` w kopii stanu; błąd
  poprawiono i ponowne uruchomienie potwierdziło, że zapis nie wymazuje sekcji.
- Pełny `AccessibleMediaController.Windows.SmokeTests`: **191 z 197 grup
  zaliczonych**. Sześć niezaliczonych grup dotyczy aparatury testowej Sonosa
  (stan modyfikatorów klawiatury, fokus, bariera czasowa i współdzielony
  schowek) oraz testowego procesu instalatora bez polecenia `Get-FileHash`.
  Nie są to testy Frontier Smart; pozostają jawnie zapisanym ograniczeniem
  pełnej walidacji Windows, a nie wynikiem zaliczonym.
- Końcowy build `AccessibleMediaController.Windows.csproj` w konfiguracji
  Release: **sukces, 0 ostrzeżeń, 0 błędów**.

### Stan dostarczenia

- Źródła: zmienione w kanonicznym repozytorium
  `D:\Projekty Codex\Accessible Multimedia Controller`, nadal jako
  niezatwierdzone zmiany drzewa roboczego opartego na commicie
  `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`.
- Build: rozwiązanie `alpha.424` skompilowane pomyślnie lokalnie, 0 ostrzeżeń
  i 0 błędów.
- Pakiet przenośny: utworzony i sprawdzony w
  `publish\AccessibleMediaController-0.1.0-alpha.424`.
- Instalacja: jeszcze niewykonana.
- Wydanie GitHub: nieutworzone i nieopublikowane.
- Test sprzętowy: niewykonany; to następny wymagany krok.

## 12. Instrukcja pierwszego testu sprzętowego

1. Radio i komputer muszą być w tej samej sieci lokalnej. Przygotuj PIN FSAPI
   urządzenia; często jest to `1234`, ale AMC niczego nie zakłada. Pasma 2,4 i
   5 GHz nie przeszkadzają, jeżeli router naprawdę łączy je w jeden segment bez
   izolacji klientów.
2. Otwórz **Menedżer sesji** przez `Ctrl+Shift+S` albo `Ctrl+0`.
3. Użyj **Nowa sesja Frontier Smart…**. Skan rozpoczyna się sam, a fokus
   pozostaje na liście urządzeń. Nie trzeba naciskać `Ctrl+F5` ani otwierać
   ręcznego formularza.
4. Po wykryciu wybierz radio, wpisz PIN i użyj **Połącz i dodaj**. Gdy SSDP nie
   znajdzie radia, rozwiń **Dodawanie ręczne po adresie IP**, wpisz jego lokalny
   adres i użyj **Dodaj i sprawdź**.
5. Po potwierdzeniu połączenia użyj **Utwórz sesję**. Menedżer
   ogłosi przypisany skrót `Ctrl+cyfra` i pozostawi fokus na nowym wierszu.
6. W sesji sprawdź kolejno `F5`, Spację, strzałki głośności, `Ctrl+M`,
   Page Up/Page Down, tryby z menu Widok oraz presety pod `Ctrl+Alt+P`.
7. W razie błędu podaj dokładny komunikat AMC, model radia i wersję firmware'u.
   Nie podawaj PIN-u.

## 13. Znane ograniczenia przed testem radia

- Nie ma jeszcze potwierdzenia, które węzły udostępnia konkretny model i jego
  firmware. Brak funkcji ma wyłączyć tylko tę funkcję, nie całą sesję.
- Presety FSAPI zależą od bieżącego trybu urządzenia; ten sam numer może znaczyć
  co innego w DAB, FM i radiu internetowym.
- Pierwsza wersja nie przegląda pełnego drzewa `netRemote.nav.list`, nie zmienia
  PIN-u ani sieci, nie aktualizuje firmware'u i nie używa długiego odpytywania.
- AMC celowo nie tworzy sesji FSAPI na urządzeniu, aby nie unieważniać sesji
  aplikacji UNDOK. Stan jest odczytywany przy wejściu, po poleceniu i na `F5`.

## 14. Szkic changelogu do akceptacji

> Dodano eksperymentalną sesję Frontier Smart dla odbiorników zgodnych z
> lokalnym FSAPI. Nową sesję tworzy się w istniejącym Menedżerze sesji przez
> wykrywanie SSDP albo ręczny adres IP i PIN. Dostępne są stan urządzenia,
> zasilanie, głośność, wyciszenie, podstawowy transport, tryby i sprzętowe
> presety bieżącego trybu. PIN jest przechowywany w Menedżerze poświadczeń
> Windows. Zakres funkcji zależy od modelu i firmware'u; integracja wymaga
> jeszcze potwierdzenia na prawdziwym radiu.

Ten tekst jest szkicem. Nie został dodany do opublikowanych informacji o
wydaniu i wymaga akceptacji po teście sprzętowym.

## 15. Korekta z 22 października 2026 r. — pierwsze wykrywanie

Ta korekta zastępuje wcześniejszą decyzję z 21 października, według której
początkowy fokus kreatora trafiał do PIN-u, a użytkownik sam uruchamiał
wykrywanie. Po próbie na rzeczywistym radiu ustalono następujący kontrakt:

- utworzenie pierwszej sesji rozpoczyna wykrywanie automatycznie;
- samo SSDP nie wymaga PIN-u i od razu zapełnia listę kandydatów;
- PIN jest drugim krokiem, służącym do potwierdzenia zaznaczonego urządzenia;
- ręczny adres IP jest opcją awaryjną w zwiniętej sekcji;
- podczas skanu fokus pozostaje na liście, nigdy na przycisku zamknięcia;
- po zapisaniu urządzenia `Ctrl+F5` otwiera gotową listę bez automatycznego
  ponawiania skanu; nowego urządzenia szuka jawny przycisk;
- wykryte adresy są pamiętane w RAM przy ponownym otwarciu okna, ale bez
  poprawnego PIN-u nie trafiają do konfiguracji ani sesji.

### Przyczyny poprawki źródłowej

Pierwsza implementacja łączyła trzy osobne kroki: SSDP, sprawdzenie PIN-u i
pełny odczyt stanu. W efekcie urządzenie poprawnie odpowiadające na SSDP mogło
nie pojawić się na liście, gdy starszy firmware inaczej obsługiwał
`GET_MULTIPLE` albo nie miał jednego z opcjonalnych węzłów. Dodatkowo błąd
multicastu na jednej aktywnej karcie sieciowej przerywał cały przebieg.

Nowy kod pokazuje odpowiedź SSDP przed uwierzytelnieniem, izoluje błędy kart,
powtarza zapytania usługi i `ssdp:all`, a po PIN-ie najpierw czyta minimalną
tożsamość. Pełny stan jest kolejnym, nieblokującym krokiem. Starsze firmware'y,
które zwracają brak `GET_MULTIPLE` jako HTTP 404 albo jako zwykły XML FSAPI z
HTTP 200, przechodzą na pojedyncze odczyty.

### Stan weryfikacji po korekcie

- testy protokołu Frontier Smart: **13/13 zaliczonych**;
- testy okien Frontier Smart: **6/6 grup zaliczonych**;
- oba projekty testowe są częścią rozwiązania i pełnego `build.ps1`;
- build całej aplikacji zakończył się wynikiem 0 ostrzeżeń i 0 błędów;
- pakiet `alpha.424` został utworzony i ma właściwą wersję pliku;
- pełne testy Core przeszły po skierowaniu ich własnych plików tymczasowych do
  katalogu testowego na D:;
- pełne testy Windows nie doszły do końcowego podsumowania: pięć starych
  scenariuszy Sonosa nie przeszło z powodu timeoutu lub ograniczeń pulpitu, a
  kolejny test zakończył proces na braku dostępu do schowka; dedykowane testy
  Frontier Smart pozostały zaliczone 6/6;
- wykrycie, PIN, stan, presety i transport prawdziwego radia nadal wymagają
  próby użytkownika; test syntetyczny nie jest dowodem łączności sprzętowej.

## 16. Rekord pakietu testowego alpha.424

Pełny, datowany zapis komend, wyników, komunikatów NVDA, ograniczeń i sumy
kontrolnej znajduje się w
`wyniki-testow/WERYFIKACJA_FRONTIER_SMART_424_2026-10-22.md`. Zmiany są nadal
niezatwierdzonym stanem roboczym opartym na commicie
`16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`; nie utworzono wydania GitHub.
