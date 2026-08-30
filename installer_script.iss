; MAXXX OS - Inno Setup Script
; Creates a professional Windows installer

#define MyAppName "MAXXX OS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MAXXX OS"
#define MyAppURL "https://github.com/maxxx-os/maxxx-os"
#define MyAppExeName "MaxxxOS.exe"

[Setup]
AppId={{B1E23C80-4A5F-4E8D-9C2B-7F6E8D9A1B3C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=MaxxxOS_Setup
SetupIconFile=maxxx_os_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "installollama"; Description: "Install Ollama (Local AI Engine)"; GroupDescription: "Dependencies:"; Flags: checkedonce

[Files]
Source: "dist\MaxxxOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "vault\*"; DestDir: "{app}\vault"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function IsOllamaInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd', '/c ollama --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if (CurStep = ssPostInstall) and IsTaskSelected('installollama') then
  begin
    if not IsOllamaInstalled then
    begin
      MsgBox('Ollama will now be installed. This may take a few minutes.', mbInformation, MB_OK);
      Exec('powershell', '-Command "Invoke-WebRequest -Uri https://ollama.com/download/OllamaSetup.exe -OutFile OllamaSetup.exe; Start-Process OllamaSetup.exe -ArgumentList ''/VERYSILENT'' -Wait"', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      Exec('powershell', '-Command "ollama pull qwen2.5:7b"', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
