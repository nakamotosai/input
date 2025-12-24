; 脚本生成向导 - 中日说全功能正式版 (CNJP Input)
#define MyAppName "中日说"
#define MyAppEnglishName "cnjp input"
#define MyJapaneseName "日中インプット"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "nakamotosai"
#define MyAppURL "https://github.com/nakamotosai/input"
#define MyAppExeName "CNJP_Input.exe"
#define MyIconName "logo.ico"

[Setup]
; (中日说专用：请将此 ID 视为软件的终身身份证，后续升级请勿更改)
AppId={{B5A8E2D1-C9F3-4B9A-9D8F-A16A5E7B2C4D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; 互斥量，防止安装时程序正在运行
AppMutex=CNJP_Input_Server_Mutex
; 默认安装文件夹
DefaultDirName={autopf}\cnjp_input
DisableProgramGroupPage=yes
DisableDirPage=no
; 输出文件名
OutputBaseFilename=cnjp_input_setup_v{#MyAppVersion}
; 仅允许 64 位系统 (AI 库必需)
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; 安装程序图标
SetupIconFile={#MyIconName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; 需要管理员权限 (用于安装字体和写入 Program Files)
PrivilegesRequired=admin
; 自动关闭正在运行的实例
CloseApplications=yes

[Languages]
; 安装界面支持中日双语，自动识别
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; === 核心打包文件 (来自 PyInstaller dist 目录) ===
Source: "dist\CNJP_Input\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyIconName}"; DestDir: "{app}"; Flags: ignoreversion

; === 字体安装 ===
Source: "fonts\NotoSansSC-Regular.otf"; DestDir: "{autofonts}"; FontInstall: "Noto Sans SC"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "fonts\NotoSerifSC-Regular.otf"; DestDir: "{autofonts}"; FontInstall: "Noto Serif SC"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
; 开始菜单与桌面快捷方式
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyIconName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyIconName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时清理用户目录下的残留配置文件和临时文件
Type: filesandordirs; Name: "{localappdata}\CNJP_Input"

[Messages]
; 针对不同语言的欢迎语微调
chinesesimplified.WelcomeLabel2=欢迎安装 {#MyAppName}。{#13}{#13}本软件将为您提供极致流畅的离线中日翻译与语音输入体验。
japanese.WelcomeLabel1=欢迎使用 {#MyJapaneseName} 安装向导
japanese.WelcomeLabel2=このウィザードは、{#MyJapaneseName} をコンピューターにインストールします。{#13}{#13}高度なオフライン翻訳技術により、スムーズな入力をサポートします。
