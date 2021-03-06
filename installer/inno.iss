; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "OpenS3Box"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "jrobben"
#define MyAppURL "https://github.com/jrobben"
#define MyAppExeName "dist\opens3box.exe"
#define MyDevFolder ".."

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{89686C30-1510-4B97-A355-AAC75CDB275E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#MyDevFolder}\LICENSE
OutputDir={#MyDevFolder}\installer
OutputBaseFilename=opens3box-setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyDevFolder}\dist\opens3box.exe"; DestDir: "{app}\dist"; Flags: ignoreversion
Source: "{#MyDevFolder}\dist\*"; DestDir: "{app}\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyDevFolder}\resources\16x16\*"; DestDir: "{app}\resources\16x16"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyDevFolder}\opens3box.conf.in"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyDevFolder}\logging.conf"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

