@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "SRC=%~dp0"
set "DST=%APPDATA%\Adobe\CEP\extensions\AutoCut_AI_ChatGPT"
set "VER=4.2.2"

echo =======================================================
echo   AUTO CUT AI v%VER% - HARD INSTALL / VERIFY
echo   Premiere Pro 2021 / 2022 / 2023+
echo =======================================================
echo.

set "PRRUN=0"
tasklist /FI "IMAGENAME eq Adobe Premiere Pro.exe" 2>nul | find /I "Adobe Premiere Pro.exe" >nul && set "PRRUN=1"
tasklist /FI "IMAGENAME eq PremierePro.exe" 2>nul | find /I "PremierePro.exe" >nul && set "PRRUN=1"
if "%PRRUN%"=="1" (
  echo [LOI] Premiere dang mo.
  echo Hay TAT HOAN TOAN Premiere, sau do chay lai installer nay.
  echo Neu cai khi Premiere dang mo, CEP co the tiep tuc dung main.js v4.2.0 cu.
  pause
  exit /b 20
)

if not exist "%SRC%CSXS\manifest.xml" exit /b 1
if not exist "%SRC%js\c1Builder.js" exit /b 2

if exist "%DST%" rmdir /s /q "%DST%" 2>nul
if exist "%DST%" (
  echo [LOI] Khong xoa duoc extension cu.
  pause
  exit /b 3
)

mkdir "%DST%" >nul 2>nul
robocopy "%SRC%" "%DST%" /MIR /NFL /NDL /NJH /NJS /NP >nul
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 exit /b 5

for %%V in (7 8 9 10 11 12 13 14) do (
  reg add "HKCU\Software\Adobe\CSXS.%%V" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>nul
)

if not exist "%DST%\VERSION.json" goto VERIFY_FAIL
if not exist "%DST%\js\c1Builder.js" goto VERIFY_FAIL
findstr /C:"\"version\":\"4.2.2\"" "%DST%\VERSION.json" >nul || goto VERIFY_FAIL
findstr /C:"C1Builder.fromFile(timing.path)" "%DST%\js\main.js" >nul || goto VERIFY_FAIL
findstr /C:"ChatGPTDirect.stage1(" "%DST%\js\main.js" >nul && goto STALE_FAIL
findstr /C:"Auto Cut AI v4.2.2" "%DST%\index.html" >nul || goto VERIFY_FAIL
findstr /C:"version: \"4.2.2\"" "%DST%\jsx\host.jsx" >nul || goto VERIFY_FAIL

>"%DST%\INSTALLED_4.2.2_OK.txt" echo Auto Cut AI v4.2.2 verified install %DATE% %TIME%
echo [OK] Auto Cut AI v4.2.2 da duoc cai va VERIFY thanh cong.
pause
exit /b 0

:STALE_FAIL
echo [LOI] main.js van con logic v4.2.0 ChatGPTDirect.stage1.
pause
exit /b 7

:VERIFY_FAIL
echo [LOI] Verify v4.2.2 that bai.
pause
exit /b 6
