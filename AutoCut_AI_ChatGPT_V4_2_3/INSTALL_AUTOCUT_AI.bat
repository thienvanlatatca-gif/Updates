@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "VER=4.2.3"
set "DST=%APPDATA%\Adobe\CEP\extensions\AutoCut_AI_ChatGPT"
if /I "%~1"=="--from-stage" goto FROM_STAGE
set "SRC=%~dp0"

set "PRRUN=0"
tasklist /FI "IMAGENAME eq Adobe Premiere Pro.exe" 2>nul | find /I "Adobe Premiere Pro.exe" >nul && set "PRRUN=1"
tasklist /FI "IMAGENAME eq PremierePro.exe" 2>nul | find /I "PremierePro.exe" >nul && set "PRRUN=1"
if "%PRRUN%"=="1" (echo [LOI] Tat hoan toan Premiere roi chay lai.& pause& exit /b 20)

if not exist "%SRC%CSXS\manifest.xml" exit /b 1
if not exist "%SRC%js\c1Builder.js" exit /b 2

set "STAGE=%TEMP%\AutoCut_AI_Stage_%VER%_%RANDOM%_%RANDOM%"
if exist "%STAGE%" rmdir /s /q "%STAGE%" >nul 2>nul
mkdir "%STAGE%" >nul 2>nul || exit /b 3
echo [1/5] Tao staging an toan...
xcopy "%SRC%*" "%STAGE%\" /E /I /H /Y /Q >nul
if errorlevel 2 (echo [LOI] Staging xcopy that bai.& pause& exit /b 4)
if not exist "%STAGE%\VERSION.json" exit /b 5
if not exist "%STAGE%\js\c1Builder.js" exit /b 6

call "%STAGE%\INSTALL_AUTOCUT_AI.bat" --from-stage "%DST%" "%STAGE%"
set "RC=%ERRORLEVEL%"
if exist "%STAGE%" rmdir /s /q "%STAGE%" >nul 2>nul
exit /b %RC%

:FROM_STAGE
set "SRC=%~dp0"
set "DST=%~2"
if not defined DST set "DST=%APPDATA%\Adobe\CEP\extensions\AutoCut_AI_ChatGPT"
echo [2/5] Xoa extension cu...
if exist "%DST%" rmdir /s /q "%DST%" >nul 2>nul
if exist "%DST%" (echo [LOI] Khong xoa duoc extension cu.& pause& exit /b 10)
mkdir "%DST%" >nul 2>nul || exit /b 11

echo [3/5] Copy v%VER% tu staging...
xcopy "%SRC%*" "%DST%\" /E /I /H /Y /Q >nul
if errorlevel 2 (echo [LOI] Copy vao CEP that bai.& pause& exit /b 12)

for %%V in (7 8 9 10 11 12 13 14) do reg add "HKCU\Software\Adobe\CSXS.%%V" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>nul

echo [4/5] Verify runtime...
if not exist "%DST%\VERSION.json" goto VERIFY_FAIL
if not exist "%DST%\js\c1Builder.js" goto VERIFY_FAIL
findstr /C:"\"version\":\"4.2.3\"" "%DST%\VERSION.json" >nul || goto VERIFY_FAIL
findstr /C:"C1Builder.fromFile(timing.path)" "%DST%\js\main.js" >nul || goto VERIFY_FAIL
findstr /C:"ChatGPTDirect.stage1(" "%DST%\js\main.js" >nul && goto STALE_FAIL
>"%DST%\INSTALLED_4.2.3_OK.txt" echo verified
echo [5/5] [OK] Auto Cut AI v4.2.3 da cai va verify dung.
pause
exit /b 0

:STALE_FAIL
echo [LOI] main.js van la logic cu.
pause
exit /b 13
:VERIFY_FAIL
echo [LOI] Verify v4.2.3 that bai.
pause
exit /b 14
