; CFS Designers Agent — Inno Setup script (compile when Inno is installed)
; 1. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
; 2. Open this file in Inno Compiler
; 3. Build → Output: packaging\Output\CFS-Designers-Agent-Setup.exe
;
; Before compile: copy a ready agent folder to packaging\agent-dist\
; (venv + config.example.json). Or adjust Source paths below.

#define MyAppName "CFS Designers Agent"
#define MyAppVersion "0.5.0"
#define MyAppPublisher "CFS Designers"

[Setup]
AppId={{A7C3E2F1-9B4D-4E8A-B2C1-CFS-DESIGNERS-AGENT}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\CFS Designers Agent
DefaultGroupName=CFS Designers
OutputDir=Output
OutputBaseFilename=CFS-Designers-Agent-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
; Place distributable agent files under packaging\agent-dist before building
Source: "agent-dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CFS Designers Agent"; Filename: "{app}\START-AGENT.bat"
Name: "{autodesktop}\CFS Designers Agent"; Filename: "{app}\START-AGENT.bat"

[Run]
Filename: "{app}\INSTALL-AGENT.bat"; Description: "Install autostart + enroll helper"; Flags: postinstall skipifsilent shellexec
