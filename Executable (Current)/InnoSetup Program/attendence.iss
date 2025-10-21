; ----------------------------
; Attendance System Installer
; ----------------------------
[Setup]
AppName=FRC-1164-Attendance-System-Installer
AppVersion=1.0
DefaultDirName={autopf}\FRC-1164-Attendance-System
DefaultGroupName=FRC-1164-Attendance-System
UninstallDisplayIcon={app}\FRC-1164-Attendance-System.exe
OutputBaseFilename=FRC-1164-Attendance-System
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; ----------------------------
; Files
; ----------------------------
[Files]
; Main executable
Source: "dist\FRC-1164-Attendance-System.exe"; DestDir: "{app}"; Flags: ignoreversion

; Assets (logo, gear, icon)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Data folder
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

; ----------------------------
; Shortcuts
; ----------------------------
[Icons]
; Start Menu shortcut
Name: "{group}\Attendance System"; Filename: "{app}\FRC-1164-Attendance-System.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"

; Desktop shortcut
Name: "{commondesktop}\Attendance System"; Filename: "{app}\FRC-1164-Attendance-System.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icon.ico"

; ----------------------------
; Run After Install
; ----------------------------
[Run]
Filename: "{app}\FRC-1164-Attendance-System.exe"; Description: "Launch Attendance System"; Flags: nowait postinstall skipifsilent
