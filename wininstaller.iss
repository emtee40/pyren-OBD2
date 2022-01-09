[Setup]
AppName=PyRen
AppVersion=0.9.r
DefaultDirName={pf}\PyRen
DefaultGroupName=Pyren
SetupIconFile=icons\obd.ico
OutputBaseFilename=Pyren_Setup
UsePreviousPrivileges=True

[Files]
Source: "README.md"; DestDir: "{app}"
Source: "*.py"; DestDir: "{app}"
Source: "\Python27\*"; DestDir: "{app}\Python27"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc"
Source: "BVMEXTRACTION\*"; DestDir: "{app}\BVMEXTRACTION"; Flags: ignoreversion recursesubdirs
Source: "EcuDacia\*"; DestDir: "{app}\EcuDacia"; Flags: ignoreversion recursesubdirs
Source: "EcuRenault\*"; DestDir: "{app}\EcuRenault"; Flags: ignoreversion recursesubdirs
Source: "EcuRsm\*"; DestDir: "{app}\EcuRsm"; Flags: ignoreversion recursesubdirs
Source: "Location\*"; DestDir: "{app}\Location"; Flags: ignoreversion recursesubdirs
Source: "MTCSAVE\*"; DestDir: "{app}\MTCSAVE"; Flags: ignoreversion recursesubdirs onlyifdoesntexist skipifsourcedoesntexist
Source: "NML\*"; DestDir: "{app}\NML"; Flags: ignoreversion recursesubdirs
Source: "Params\*"; DestDir: "{app}\Params"; Flags: ignoreversion recursesubdirs
Source: "pyren\*"; DestDir: "{app}\pyren"; Flags: ignoreversion recursesubdirs
Source: "Vehicles\*"; DestDir: "{app}\Vehicles"; Flags: ignoreversion recursesubdirs
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\importlib"
Type: filesandordirs; Name: "{app}\Python38"

[Code]
procedure AfterMyProgInstall;
begin
    MsgBox(ExpandConstant('{cm:AfterMyProgInstall} {app}'), mbInformation, MB_OK);
end;

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{app}\MTCSAVE"; Permissions: users-full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}";GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{group}\PyRen"; Filename: "{app}\Python27\python.exe"; Parameters: """{app}\_pyren_launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"
Name: "{userdesktop}\PyRen"; Filename: "{app}\Python27\python.exe"; Parameters: """{app}\_pyren_launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\icons\obd.ico"; Tasks: desktopicon

[CustomMessages]
en.AfterMyProgInstall=Can-Clip 212 and DTT2000data 2021-6-16 included, remember to keep them up to date. 
no.AfterMyProgInstall=Can-Clip 212 og DTT2000data 2021-6-16 inkludert, husk å holde dem oppdatert. 
de.AfterMyProgInstall=Can-Clip 212 und DTT2000data 2021-6-16 enthalten, denken Sie daran, sie auf dem neuesten Stand zu halten.
fr.AfterMyProgInstall=Can-Clip 212 et DTT2000data 2021-6-16 inclus, pensez a les tenir à jour.
es.AfterMyProgInstall=Can-Clip 212 y DTT2000data 2021-6-16 incluidos, recuerde mantenerlos actualizados.
it.AfterMyProgInstall=Can-Clip 212 e DTT2000data 2021-6-16 inclusi, ricordati di tenerli aggiornati.
nl.AfterMyProgInstall=Can-Clip 212 en DTT2000data 2021-6-16 inbegrepen, vergeet niet om ze up-to-date te houden.
pl.AfterMyProgInstall=W zestawie Can-Clip 212 i DTT2000data 2021-6-16, pamiętaj o ich aktualizacji.
ptbr.AfterMyProgInstall=Can-Clip 212 e DTT2000data 2021-6-16 incluídos, lembre-se de mantê-los atualizados.
pt.AfterMyProgInstall=Can-Clip 212 e DTT2000data 2021-6-16 incluídos, lembre-se de mantê-los atualizados.
ru.AfterMyProgInstall=Can-Clip 212 и DTT2000data 2021-6-16 включены, не забывайте обновлять их.
am.AfterMyProgInstall=Can-Clip 212 և DTT2000data 2021-6-16 ներառված են, հիշեք, որ դրանք թարմացվեն:
bg.AfterMyProgInstall=Включени са Can-Clip 212 и DTT2000data 2021-6-16, не забравяйте да ги поддържате актуални.
tr.AfterMyProgInstall=Can-Clip 212 ve DTT2000data 2021-6-16 dahildir, güncel tutmayı unutmayın.
ua.AfterMyProgInstall=Can-Clip 212 і DTT2000data 2021-6-16 включені, не забувайте оновлювати їх.

[Languages]
Name: "en"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Default.isl"
Name: "no"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Norwegian.isl"
Name: "de"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\German.isl"
Name: "fr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\French.isl"
Name: "es"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Spanish.isl"
Name: "it"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Italian.isl"
Name: "nl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Dutch.isl"
Name: "pl"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Polish.isl"
Name: "ptbr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\BrazilianPortuguese.isl"
Name: "pt"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Portuguese.isl"
Name: "ru"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Russian.isl"
Name: "am"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Armenian.isl"
Name: "bg"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Bulgarian.isl"
Name: "tr"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Turkish.isl"
Name: "ua"; MessagesFile: "C:\Program Files (x86)\Inno Setup 6\Languages\Ukrainian.isl"
