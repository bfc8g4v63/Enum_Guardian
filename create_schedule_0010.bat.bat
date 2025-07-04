:: 建立每天00:10執行排程
schtasks /create ^
 /tn "EnumGuardianAuto" ^
 /tr "C:\EnumGuardian\enum_auto_run.exe" ^
 /sc daily ^
 /st 00:10 ^
 /ru SYSTEM ^
 /rl HIGHEST ^
 /f
pause