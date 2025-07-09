:: 建立每天10:12執行排程
schtasks /create ^
 /tn "EnumGuardianAuto" ^
 /tr "C:\Nelson\Dev\GitHub\Enum_Guardian\enum_auto_run.exe" ^
 /sc daily ^
 /st 10:12 ^
 /ru SYSTEM ^
 /rl HIGHEST ^
 /f
pause