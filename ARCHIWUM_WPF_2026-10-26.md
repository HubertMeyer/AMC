# Archiwum AMC WPF z 26.10.2026

## Status

Ten snapshot jest historycznym archiwum dawnej aplikacji AMC WPF. Nie jest
bieżącą linią rozwoju, źródłem następnego instalatora ani wersją przeznaczoną
do dalszego zwykłego rozwijania.

Bieżące AMC Test i przyszłe AMC Public powstają z jednej wspólnej linii
aplikacji Python. Wariant publiczny ma być budowany później z dopracowanej
wersji AMC Test przez profil wydania i uzgodnione wyłączenia funkcji, a nie z
tego archiwum.

## Zakres archiwum

- gałąź: `archive/wpf-final-20261026`;
- baza lokalna przed snapshotem: `16dce37b1094a0a03e7a8ff7dbe0965e80b915fc`;
- snapshot zachowuje ostatnie lokalne źródła, testy i dokumentację WPF;
- pliki kompilacji, profile testowe, poświadczenia, dane kont, biblioteki,
  nagrania i inne dane użytkownika nie należą do archiwum.

## Weryfikacja

Przed utworzeniem snapshotu:

- porównano stan z `origin/main`;
- sklasyfikowano 84 zmodyfikowane i 96 nowych ścieżek;
- sprawdzono nazwy i treść planowanych plików pod kątem kluczy prywatnych,
  tokenów, haseł oraz plików poświadczeń;
- potwierdzono, że wzorce `.p8`, `.jwt` i `client_secret*.json` są ignorowane;
- nie wykryto nowego sekretu przeznaczonego do publikacji.

Kontrola `git diff --cached --check` zgłosiła dziewięć historycznych uwag
dotyczących końcowych pustych wierszy lub odstępów użytych w Markdown. Nie są
to błędy źródeł; pozostawiono je bez mechanicznego przepisywania archiwum.

Nie wykonano nowej kompilacji ani regresji WPF. Snapshot potwierdza zachowanie
źródeł, a nie działającą, zbudowaną lub zainstalowaną wersję programu.

## Odzyskanie

W razie wyjątkowej potrzeby kod można odczytać przez przełączenie na gałąź
`archive/wpf-final-20261026`. Ewentualne rozwiązanie należy najpierw porównać z
bieżącą implementacją Python i przenieść wybiórczo; nie należy wznawiać dawnej
linii WPF jako równoległego produktu.
