@echo off
echo [%date% %time%] Starting enum_auto_run.exe >> C:\Nelson\Dev\GitHub\Enum_Guardian\EnumGuardian.log
C:\Nelson\Dev\GitHub\Enum_Guardian\enum_auto_run.exe >> C:\Nelson\Dev\GitHub\Enum_Guardian\EnumGuardian.log 2>&1
echo [%date% %time%] Ended >> C:\Nelson\Dev\GitHub\Enum_Guardian\EnumGuardian.log
