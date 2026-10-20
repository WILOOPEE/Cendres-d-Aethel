; Ouvrir avec Inno Setup sur Windows apres avoir construit le .exe
[Setup]
AppId={{B1C65A8E-28F2-48D2-90E7-AETHELCENDRES01}
AppName=Cendres d'Aethel
AppVersion=1.0
DefaultDirName={autopf}\Cendres d'Aethel
DefaultGroupName=Cendres d'Aethel
OutputDir=installateur
OutputBaseFilename=Setup_Cendres_d_Aethel
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\Cendres d'Aethel.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Cendres d'Aethel"; Filename: "{app}\Cendres d'Aethel.exe"
Name: "{autodesktop}\Cendres d'Aethel"; Filename: "{app}\Cendres d'Aethel.exe"

[Run]
Filename: "{app}\Cendres d'Aethel.exe"; Description: "Lancer Cendres d'Aethel"; Flags: postinstall nowait skipifsilent
