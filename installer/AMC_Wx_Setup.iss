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
  #define ShellProfileKey "Public"
  #define ShellApplicationName "Accessible Multimedia Controller"
  #define ShellOpenLabel "Otwórz w AMC"
  #define ShellQueueLabel "Dodaj do kolejki AMC"
#elif Profil == "test"
  #define Produkt "Accessible Multimedia Controller — Test"
  #define KrotkaNazwa "AMC Test"
  #define AppIdentity "{{0B807571-BDC5-4287-BD7C-4F4A7C71438F}"
  #define FolderProgramu "AMC Test"
  #define NazwaWyjscia "AMC-Test-" + Wersja + "-win-x64"
  #define AppPathName "AMC-Test.exe"
  #define LauncherMutex "Local\AccessibleMultimediaController.PythonLauncher.SingleInstance"
  #define ShellProfileKey "Test"
  #define ShellApplicationName "Accessible Multimedia Controller — Test"
  #define ShellOpenLabel "Otwórz w AMC Test"
  #define ShellQueueLabel "Dodaj do kolejki AMC Test"
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
ChangesAssociations=yes

; Instalator nigdy nie zamyka AMC przez Restart Manager. AppMutex zatrzymuje
; podmianę, gdy właściwy profil nadal działa. Użytkownik zamyka program zwykłą
; drogą, a ta droga odmawia zamknięcia podczas nagrywania lub finalizacji.
AppMutex={#LauncherMutex}
CloseApplications=no
RestartApplications=no

[Languages]
Name: "polski"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "shellcontext"; Description: "Dodaj polecenia Otwórz i Dodaj do kolejki w menu kontekstowym obsługiwanych plików"; \
    GroupDescription: "Integracja z Eksploratorem Windows:"; Flags: unchecked
Name: "shellopenwith"; Description: "Pokaż {#KrotkaNazwa} na liście Otwórz za pomocą i w ustawieniach aplikacji domyślnych"; \
    GroupDescription: "Integracja z Eksploratorem Windows:"; Flags: unchecked

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
const
  ShellExtensions = '.mp3|.m4a|.aac|.flac|.wav|.ogg|.oga|.opus|.wma|' +
    '.mp2|.wave|.rf64|.bwf|.adts|.asf|.aif|.aiff|.aifc|.mka|.ac3|' +
    '.eac3|.ec3|.amr|.mkv|.webm|.mp4|.m4v|.mov|.ogv|.avi|.wmv|' +
    '.mpeg|.mpg|.mpe|.ts|.mts|.m2ts|.vob|.flv|.3gp|.3g2|.3gp2|' +
    '.3gpp|.m3u|.m3u8|.pls|.xspf|.amc-partial';
  ShellClassesRoot = 'Software\Classes\';
  ShellCapabilitiesRoot = 'Software\AccessibleMultimediaController\{#ShellProfileKey}\Capabilities';
  ShellRegisteredApplication = '{#ShellApplicationName}';
  ShellClassPrefix = 'AccessibleMediaController.{#ShellProfileKey}.';
  ShellVerbPrefix = 'AccessibleMediaController.{#ShellProfileKey}.';

function PopShellExtension(var Values: string): string;
var
  Separator: Integer;
begin
  Separator := Pos('|', Values);
  if Separator = 0 then
  begin
    Result := Values;
    Values := '';
  end
  else
  begin
    Result := Copy(Values, 1, Separator - 1);
    Delete(Values, 1, Separator);
  end;
end;

function ShellClassFor(const Extension: string): string;
begin
  Result := ShellClassPrefix + Copy(Extension, 2, Length(Extension) - 1);
end;

procedure RemoveShellIntegration;
var
  Remaining, Extension, ClassName, AssociationRoot: string;
begin
  RegDeleteValue(HKA, 'Software\RegisteredApplications', ShellRegisteredApplication);
  RegDeleteKeyIncludingSubkeys(HKA, ShellCapabilitiesRoot);
  Remaining := ShellExtensions;
  while Remaining <> '' do
  begin
    Extension := PopShellExtension(Remaining);
    ClassName := ShellClassFor(Extension);
    AssociationRoot := ShellClassesRoot + 'SystemFileAssociations\' + Extension +
      '\shell\' + ShellVerbPrefix;
    RegDeleteKeyIncludingSubkeys(HKA, AssociationRoot + 'open');
    RegDeleteKeyIncludingSubkeys(HKA, AssociationRoot + 'queue');
    RegDeleteValue(
      HKA,
      ShellClassesRoot + Extension + '\OpenWithProgids',
      ClassName);
    RegDeleteKeyIncludingSubkeys(HKA, ShellClassesRoot + ClassName);
  end;
end;

procedure RegisterShellIntegration;
var
  Remaining, Extension, ClassName, ClassRoot, AssociationRoot,
    Executable, Command: string;
begin
  Executable := ExpandConstant('{app}\AMC.exe');
  Remaining := ShellExtensions;

  if WizardIsTaskSelected('shellopenwith') then
  begin
    RegWriteStringValue(
      HKA,
      'Software\RegisteredApplications',
      ShellRegisteredApplication,
      ShellCapabilitiesRoot);
    RegWriteStringValue(
      HKA,
      ShellCapabilitiesRoot,
      'ApplicationName',
      ShellRegisteredApplication);
    RegWriteStringValue(
      HKA,
      ShellCapabilitiesRoot,
      'ApplicationDescription',
      'Dostępny odtwarzacz i organizator multimediów');
  end;

  while Remaining <> '' do
  begin
    Extension := PopShellExtension(Remaining);
    ClassName := ShellClassFor(Extension);
    ClassRoot := ShellClassesRoot + ClassName;
    AssociationRoot := ShellClassesRoot + 'SystemFileAssociations\' + Extension +
      '\shell\' + ShellVerbPrefix;

    if WizardIsTaskSelected('shellcontext') then
    begin
      RegWriteStringValue(HKA, AssociationRoot + 'open', '', '{#ShellOpenLabel}');
      RegWriteStringValue(HKA, AssociationRoot + 'open', 'Icon', Executable + ',0');
      Command := '"' + Executable + '" "%1"';
      RegWriteStringValue(HKA, AssociationRoot + 'open\command', '', Command);
      RegWriteStringValue(HKA, AssociationRoot + 'queue', '', '{#ShellQueueLabel}');
      RegWriteStringValue(HKA, AssociationRoot + 'queue', 'Icon', Executable + ',0');
      Command := '"' + Executable + '" /kolejka "%1"';
      RegWriteStringValue(HKA, AssociationRoot + 'queue\command', '', Command);
    end;

    if WizardIsTaskSelected('shellopenwith') then
    begin
      RegWriteStringValue(
        HKA,
        ShellCapabilitiesRoot + '\FileAssociations',
        Extension,
        ClassName);
      RegWriteStringValue(HKA, ShellClassesRoot + Extension + '\OpenWithProgids', ClassName, '');
      RegWriteStringValue(HKA, ClassRoot, '', 'Plik ' + Uppercase(Copy(Extension, 2, Length(Extension) - 1)) + ' ({#KrotkaNazwa})');
      RegWriteStringValue(HKA, ClassRoot + '\DefaultIcon', '', Executable + ',0');
      RegWriteStringValue(HKA, ClassRoot + '\shell\open', '', '{#ShellOpenLabel}');
      Command := '"' + Executable + '" "%1"';
      RegWriteStringValue(HKA, ClassRoot + '\shell\open\command', '', Command);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    { Aktualizacja najpierw usuwa wpisy TEGO profilu. Odznaczenie zadania
      jest dzięki temu prawdziwym wyłączeniem, nie tylko brakiem nowych wpisów. }
    RemoveShellIntegration;
    RegisterShellIntegration;
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

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RemoveShellIntegration;
end;
