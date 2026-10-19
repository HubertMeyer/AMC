; Instalator bieżącego AMC z interfejsem wxPython.
; Źródłem jest kompletny folder z bundle-manifest.json, zweryfikowany przed
; kompilacją przez Build-AMCInstaller.ps1. Profil jest zamkniętym wyborem:
; public albo test. Oba warianty mają inne AppId, foldery, skróty i muteksy.

#ifndef Wersja
  #define Wersja "0.0.0"
#endif
#ifndef Zrodlo
  #error "Podaj /DZrodlo=<zweryfikowany folder paczki>"
#endif
#ifndef Wyjscie
  #define Wyjscie ".\output"
#endif
#ifndef Profil
  #define Profil "public"
#endif

#if Profil == "public"
  #define Produkt "Accessible Multimedia Controller"
  #define KrotkaNazwa "AMC"
  #define AppIdentity "{{1E437448-30B4-4E4A-BCA1-CDA114B096A9}"
  #define FolderProgramu "AMC"
  #define NazwaWyjscia "AMC-" + Wersja + "-win-x64"
  #define AppPathName "AMC.exe"
  #define LauncherMutex "Local\AccessibleMultimediaController.PythonLauncher.Public.SingleInstance"
#elif Profil == "test"
  #define Produkt "Accessible Multimedia Controller — Test"
  #define KrotkaNazwa "AMC Test"
  #define AppIdentity "{{0B807571-BDC5-4287-BD7C-4F4A7C71438F}"
  #define FolderProgramu "AMC Test"
  #define NazwaWyjscia "AMC-Test-" + Wersja + "-win-x64"
  #define AppPathName "AMC-Test.exe"
  #define LauncherMutex "Local\AccessibleMultimediaController.PythonLauncher.SingleInstance"
#else
  #error "Nieznany profil. Dozwolone sa tylko public i test."
#endif

[Setup]
AppId={#AppIdentity}
AppName={#Produkt}
AppVersion={#Wersja}
AppVerName={#Produkt} {#Wersja}
AppPublisher=Michał Kasperczak
DefaultDirName={localappdata}\Programs\{#FolderProgramu}
DefaultGroupName={#KrotkaNazwa}
UninstallDisplayName={#Produkt}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
Compression=lzma2/max
SolidCompression=yes
OutputBaseFilename={#NazwaWyjscia}
OutputDir={#Wyjscie}
SourceDir={#Zrodlo}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
DisableStartupPrompt=yes
DisableWelcomePage=no
DisableReadyPage=no
Uninstallable=yes
SetupLogging=yes
WizardStyle=classic

; Instalator nigdy nie zamyka AMC przez Restart Manager. AppMutex zatrzymuje
; podmianę, gdy właściwy profil nadal działa. Użytkownik zamyka program zwykłą
; drogą, a ta droga odmawia zamknięcia podczas nagrywania lub finalizacji.
AppMutex={#LauncherMutex}
CloseApplications=no
RestartApplications=no

[Languages]
Name: "polski"; MessagesFile: "compiler:Languages\Polish.isl"

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#KrotkaNazwa}"; Filename: "{app}\AMC.exe"; WorkingDir: "{app}"
Name: "{group}\Odinstaluj {#KrotkaNazwa}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#KrotkaNazwa}"; Filename: "{app}\AMC.exe"; WorkingDir: "{app}"; \
    Comment: "Uruchom lub przywołaj {#KrotkaNazwa}"

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#AppPathName}"; \
    ValueType: string; ValueName: ""; ValueData: "{app}\AMC.exe"; Flags: uninsdeletekey

[Run]
Filename: "{app}\AMC.exe"; Description: "Uruchom {#KrotkaNazwa} teraz"; \
    Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if (not Exec(
          ExpandConstant('{app}\AMC.exe'),
          '--sprawdz-pakiet-pelny-cicho',
          ExpandConstant('{app}'),
          SW_HIDE,
          ewWaitUntilTerminated,
          ResultCode)) or (ResultCode <> 0) then
    begin
      RaiseException(
        'Pełna kontrola integralności zainstalowanego pakietu nie powiodła się. ' +
        'Instalacja nie może zostać uznana za zakończoną.');
    end;
  end;
end;
