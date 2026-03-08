; Chess Diagram Creator - Inno Setup Script

[Setup]
AppName=Chess Diagram Creator
AppVersion=1.2.1
AppPublisher=Chess Diagram Creator
DefaultDirName={autopf}\ChessDiagramCreator
DefaultGroupName=Chess Diagram Creator
OutputBaseFilename=ChessDiagramCreator_Setup_v1.2.1
Compression=lzma2
SolidCompression=yes
OutputDir=..\dist
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\ChessDiagramCreator\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Chess Diagram Creator"; Filename: "{app}\ChessDiagramCreator.exe"
Name: "{autodesktop}\Chess Diagram Creator"; Filename: "{app}\ChessDiagramCreator.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\ChessDiagramCreator.exe"; Description: "Launch Chess Diagram Creator"; Flags: nowait postinstall skipifsilent
