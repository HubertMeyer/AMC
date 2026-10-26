# REL-003 — usunięcie starego WPF i stan synchronizacji YouTube

- Data decyzji użytkownika: 26 października 2026
- Repozytorium kanoniczne: `D:\Projekty Codex\AMC - integracja wxPython`
- Worktree wykonawczy: `D:\Projekty Codex\AMC worktrees\sonos-broker-handoff-20261024`
- Status: stara instalacja WPF usunięta; źródła historyczne zachowane do archiwizacji

## Decyzja użytkownika

Użytkownik potwierdził, że bieżący AMC Test w Pythonie jest jedyną rozwijaną
wersją testową. Nie chce obecnie nadinstalowywać jej instalatorem systemowym.
Stara aplikacja WPF oraz jej lokalne artefakty mogą zostać usunięte, ale
niezweryfikowane źródła i historia mają zostać zachowane do czasu bezpiecznej
archiwizacji.

Ta decyzja uzupełnia REL-002. Nie zmienia rozdzielenia kanałów Test i Public.

## Bieżący AMC Test

Po równoległym wdrożeniu z 26 października potwierdzono:

- instalacja: `D:\Projekty Codex\AMC Python`;
- rewizja źródłowa paczki: `4c8fceda738afd0163040a400150007d16f8409c`;
- identyfikator paczki: `faef4e7f`;
- etykieta użytkowa: `26.10.2026, 14:01`;
- profil: `test`;
- kanał aktualizacji: `test`;
- paczka miała `sourceDirty=false`;
- po zakończeniu aktualizatora uruchomiło się okno `AMC Test — 26.10.2026, 14:01`.

Nie budowano ani nie instalowano systemowego instalatora AMC Test w ramach
REL-003.

## Usunięta instalacja WPF

Usunięto wyłącznie starą instalację WPF:

- katalog: `C:\Users\micha\AppData\Local\Programs\AMC`;
- początkowy rozmiar: 278 563 974 bajty;
- deinstalator zakończył się kodem `0`;
- po deinstalatorze usunięto 47 565 480 bajtów pozostawionych bibliotek i cache;
- usunięto stary skrót `C:\Users\micha\Desktop\AMC.lnk`;
- usunięto stare menu Start `...\Programs\AMC`;
- zachowano skróty pulpitu i menu Start `AMC Test`;
- natychmiast po operacji AMC Test nadal działał.

Usunięcie jest trwałe. Profil użytkownika, bazy biblioteki, poświadczenia oraz
instalacja `D:\Projekty Codex\AMC Python` nie były celem operacji.

## Oczyszczenie artefaktów starego repozytorium

W katalogu `D:\Projekty Codex\Accessible Multimedia Controller` usunięto 13
odtwarzalnych katalogów `bin`, `obj` i `wyniki-testow\temp-alpha424`.

- odzyskano 822 774 251 bajtów;
- zachowano źródła i katalog `.git`;
- zachowano katalog `publish` o rozmiarze 1 783 765 696 bajtów, ponieważ zawiera
  jedyne lokalne instalatory 425–427, a ich archiwum zdalne nie zostało jeszcze
  potwierdzone;
- usuniętych katalogów kompilacji i testów nie można odzyskać, ale można je
  odtworzyć ze źródeł.

Nie usunięto całego starego repozytorium. Kontrola wykazała:

- jeden lokalny commit przed `origin/main`;
- 231 zmienionych lub nieśledzonych ścieżek;
- tylko 1 plik identyczny z bieżącym worktree;
- 87 plików o innej treści;
- 143 pliki bez odpowiednika w bieżącym worktree.

Przed usunięciem repozytorium potrzebna jest jawna archiwizacja lub
udokumentowane odrzucenie tych różnic. Nie wolno usuwać ich zbiorczo jako
„już przepisanych”, dopóki nie zostanie to udowodnione dla każdej grupy.

## YouTube bez ponownego logowania Google

W kodzie istnieją dwa niezależne mechanizmy:

1. Konto Google odczytuje listę subskrypcji i playlist z YouTube. Synchronizacja
   jest jednokierunkowa `YouTube -> AMC`, najpierw pokazuje plan, a zapis do
   Biblioteki wymaga osobnego działania użytkownika. Nie usuwa dotychczasowych
   źródeł i niczego nie wysyła do YouTube.
2. Kanał zapisany już w Bibliotece jest zwykłym publicznym źródłem AMC.
   Odświeżanie korzysta z publicznego adresu kanału, `yt-dlp` i publicznego
   feedu; nie wymaga tokenu Google, ciasteczek przeglądarki ani logowania konta.

Stan rzeczywistej bazy `podcasts.db` sprawdzono wyłącznie zbiorczo, bez
odczytywania nazw kanałów i bez dostępu do poświadczeń:

- 287 aktywnych zapisanych kanałów YouTube;
- 284 mają zapis co najmniej jednego wcześniejszego odświeżenia;
- odstęp automatycznego odświeżania YouTube: 60 minut;
- maksymalnie 5 należnych źródeł w jednym przebiegu;
- interfejs co minutę zleca hostowi sprawdzenie, które źródła są należne.

Wniosek: użytkownik nie musi teraz ponownie logować się do Google, aby AMC
odświeżał już zapisane kanały. Bez logowania AMC nie odczyta nowych subskrypcji
dodanych później na koncie YouTube. Nowe logowanie publicznego klienta z PKCE
pozostaje osobnym przyszłym zadaniem.

## Następny bezpieczny etap

1. Sporządzić dokładną listę lokalnych i zdalnych gałęzi WPF.
2. Oddzielić źródła warte archiwizacji od tymczasowych wyników.
3. Przeskanować planowaną paczkę archiwalną pod kątem sekretów i danych
   użytkownika.
4. Utworzyć i zweryfikować archiwalny punkt na GitHubie.
5. Dopiero po weryfikacji nazwy, rozmiaru i sum kontrolnych archiwum usunąć
   lokalne instalatory oraz repozytorium WPF.

