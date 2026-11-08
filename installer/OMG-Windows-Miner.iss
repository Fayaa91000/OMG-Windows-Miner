#define MyAppName "OMG Windows Miner"
#define MyAppVersion "0.4.0"
#define MyAppExeName "OMG-Windows-Miner.exe"

[Setup]
AppId={{B91A2AC0-516F-40DC-BF32-BC96E602F514}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\OMG Windows Miner
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=OMG-Windows-Miner-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist\OMG-Windows-Miner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\third_party\xmrig\COPYING"; DestDir: "{app}\licenses\xmrig"; Flags: ignoreversion

[Icons]
Name: "{group}\OMG Windows Miner"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\OMG Windows Miner"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
; No automatic mining or application launch after installation.
