@echo off
chcp 65001 >nul
:: 建立備份資料夾
set "backupdir=C:\RegistryBackup"
if not exist "%backupdir%" mkdir "%backupdir%"

:: 備份日期時間 (避免冒號導致檔名錯誤)
set "datetime=%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%"
set "datetime=%datetime: =0%"

echo 備份開始: %datetime%
echo.

:: 備份 UsbFlags (IgnoreHWSerNum)
reg export "HKLM\SYSTEM\CurrentControlSet\Control\UsbFlags" "%backupdir%\UsbFlags_%datetime%.reg"

:: 備份 Enum\USB (所有裝置識別)
reg export "HKLM\SYSTEM\CurrentControlSet\Enum\USB" "%backupdir%\Enum_USB_%datetime%.reg"

:: 備份 COM Name Arbiter (COM Port分配)
reg export "HKLM\SYSTEM\CurrentControlSet\Control\COM Name Arbiter" "%backupdir%\COMDB_%datetime%.reg"

echo.
echo 備份完成。
pause
