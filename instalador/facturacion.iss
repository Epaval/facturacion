[Setup]
AppName=APP-FACTURACIÓN
AppVersion=0.0.20
AppPublisher=FACDIN/SOFTWARE
DefaultDirName={autopf}\Facturacion
DefaultGroupName=Facturación
OutputDir=.
OutputBaseFilename=Facturacion-Setup-0.0.20
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
SetupIconFile=..\icons\icono.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el escritorio"
Name: "autoiniciar"; Description: "Iniciar servidor al encender Windows"; GroupDescription: "Servidor:"; Flags: unchecked

[Files]
Source: "..\dist\Facturacion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\icons\*.ico"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\Facturación"; Filename: "{app}\Facturacion.exe"; IconFilename: "{app}\icons\icono.ico"
Name: "{group}\Facturación (servicio sin ventana)"; Filename: "{app}\Facturacion.exe"; Parameters: "--sin-ventana"; IconFilename: "{app}\icons\icono_servidor.ico"
Name: "{autodesktop}\Facturación"; Filename: "{app}\Facturacion.exe"; Tasks: desktopicon; IconFilename: "{app}\icons\icono.ico"
Name: "{userstartup}\Facturación Servidor"; Filename: "{app}\Facturacion.exe"; Parameters: "--sin-ventana"; Tasks: autoiniciar; IconFilename: "{app}\icons\icono_servidor.ico"

[Run]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""Facturacion Web"" dir=in action=allow program=""{app}\Facturacion.exe"" enable=yes"; Flags: runhidden
Filename: "{app}\Facturacion.exe"; Description: "Abrir Facturación ahora"; Flags: nowait postinstall skipifsilent
