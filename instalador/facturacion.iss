[Setup]
AppName=FACDIN-Facturación
AppVersion=0.0.24
AppPublisher=Tu Negocio Software
DefaultDirName={autopf}\Facturacion
DefaultGroupName=Facturación
OutputDir=.
OutputBaseFilename=Facturacion-Setup-0.0.24
Compression=lzma2/max
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
SetupIconFile=..\icons\icono.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el escritorio"
Name: "autoiniciar"; Description: "Iniciar servidor al encender Windows"; GroupDescription: "Servidor:"; Flags: unchecked; Check: IsServidor

[Files]
Source: "..\dist\Facturacion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\icons\*.ico"; DestDir: "{app}\icons"; Flags: ignoreversion

[Icons]
Name: "{group}\Facturación"; Filename: "{app}\Facturacion.exe"; IconFilename: "{app}\icons\icono.ico"; Check: NotIsEstacion
Name: "{group}\Facturación Servidor (red)"; Filename: "{app}\Facturacion.exe"; Parameters: "--lan --sin-ventana"; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor
Name: "{group}\Facturación Estación"; Filename: "{app}\Facturacion.exe"; Parameters: "--conectar"; IconFilename: "{app}\icons\icono.ico"; Check: IsEstacion

Name: "{autodesktop}\Facturación"; Filename: "{app}\Facturacion.exe"; Tasks: desktopicon; IconFilename: "{app}\icons\icono.ico"; Check: NotIsEstacion
Name: "{autodesktop}\Facturación Servidor"; Filename: "{app}\Facturacion.exe"; Parameters: "--lan --sin-ventana"; Tasks: desktopicon; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor
Name: "{autodesktop}\Facturación Estación"; Filename: "{app}\Facturacion.exe"; Parameters: "--conectar"; Tasks: desktopicon; IconFilename: "{app}\icons\icono.ico"; Check: IsEstacion

Name: "{userstartup}\Facturación Servidor"; Filename: "{app}\Facturacion.exe"; Parameters: "--lan --sin-ventana"; Tasks: autoiniciar; IconFilename: "{app}\icons\icono_servidor.ico"; Check: IsServidor

[Run]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""Facturacion Web"" dir=in action=allow program=""{app}\Facturacion.exe"" enable=yes"; Flags: runhidden; Check: IsServidor
Filename: "{app}\Facturacion.exe"; Parameters: "--conectar"; Description: "Abrir Facturación Estación ahora"; Flags: nowait postinstall skipifsilent; Check: IsEstacion
Filename: "{app}\Facturacion.exe"; Description: "Abrir Facturación ahora"; Flags: nowait postinstall skipifsilent; Check: NotIsEstacion

[Code]
var
  RolPage: TInputOptionWizardPage;
  IpPage: TInputQueryWizardPage;
  RolSeleccionado: String;

procedure InitializeWizard();
begin
  RolPage := CreateInputOptionPage(wpSelectDir,
    'Tipo de instalación', '¿Cómo se usará esta PC?',
    'Seleccione el rol de esta computadora:',
    True, False);
  RolPage.Add('Servidor (PC principal con caja): hospedará la base de datos.');
  RolPage.Add('Estación de trabajo (caja adicional): se conectará al servidor por red.');
  RolPage.Add('Instalación individual: uso en una sola PC sin red.');
  RolPage.Values[0] := True;

  IpPage := CreateInputQueryPage(RolPage.ID,
    'Conexión con el servidor', 'Dirección IP del servidor',
    'Ingrese la IP de la PC donde está instalado el servidor (ej: 192.168.1.10).');
  IpPage.Add('IP del servidor:', False);
  IpPage.Values[0] := '';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = IpPage.ID then
    Result := (RolSeleccionado <> 'estacion');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = RolPage.ID then
  begin
    if RolPage.Values[0] then RolSeleccionado := 'servidor'
    else if RolPage.Values[1] then RolSeleccionado := 'estacion'
    else RolSeleccionado := 'individual';
  end;
  if CurPageID = IpPage.ID then
  begin
    if Trim(IpPage.Values[0]) = '' then
    begin
      MsgBox('Debe ingresar la IP del servidor para continuar.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function IsServidor: Boolean; begin Result := (RolSeleccionado = 'servidor'); end;
function IsEstacion: Boolean; begin Result := (RolSeleccionado = 'estacion'); end;
function NotIsEstacion: Boolean; begin Result := (RolSeleccionado <> 'estacion'); end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    SaveStringToFile(ExpandConstant('{app}\rol.txt'), RolSeleccionado, False);
    if RolSeleccionado = 'estacion' then
      SaveStringToFile(ExpandConstant('{app}\ip_servidor.txt'), Trim(IpPage.Values[0]), False);
  end;
end;
