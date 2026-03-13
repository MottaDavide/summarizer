#define MyAppName "Summerizer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "d.motta"
#define MyAppExeName "Summerizer.exe"

[Setup]
AppId={{0DB392A6-5AE7-4B40-BE77-F32C34DBCBAB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=Summerizer-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\summerizer.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un'icona sul desktop"; GroupDescription: "Icone aggiuntive:"

[Files]
Source: "dist\Summerizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia {#MyAppName}"; Flags: nowait postinstall skipifsilent
