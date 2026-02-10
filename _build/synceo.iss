[Setup]
AppName=Synceo
AppVersion=1.3.1
DefaultDirName={userappdata}\Synceo
DefaultGroupName=Synceo
UninstallDisplayIcon={app}\synceo.exe
OutputBaseFilename=SynceoSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=icons\synceo.ico
PrivilegesRequired=lowest
;Informations du fichier apparaissant dans Propriété/Détails
VersionInfoCompany=Esshom
VersionInfoDescription=Synceo Server Installer
VersionInfoVersion=1.3.1.0
VersionInfoCopyright=Copyright (C) 2026 Esshom, Essteam Dev
VersionInfoProductName=Synceo Server


[Files]
Source: "dist\synceo.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: desktopicon; Description: Créer une icône sur le bureau; GroupDescription: Options supplémentaires:
Name: startup; Description: Démarrer Synceo avec Windows; GroupDescription: Démarrage:

[Icons]
Name: "{group}\Synceo"; Filename: "{app}\synceo.exe"
Name: "{userdesktop}\Synceo"; Filename: "{app}\synceo.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
ValueType: string; ValueName: "Synceo"; ValueData: """{app}\synceo.exe"""; \
Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\synceo.exe"; Description: Lancer Synceo; Flags: nowait postinstall skipifsilent
