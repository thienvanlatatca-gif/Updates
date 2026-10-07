@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "SRC=%~dp0PremiereCEP"
set "DST=%APPDATA%\Adobe\CEP\extensions\PR_Auto_Bridge_2021_Plus"

echo === PR AUTO - CAI CEP PLUGIN CHO PREMIERE 2021+ ===
if not exist "%SRC%\CSXS\manifest.xml" (
  echo [LOI] Khong tim thay %SRC%\CSXS\manifest.xml
  if /I not "%~1"=="/silent" pause
  exit /b 1
)

if exist "%DST%" rmdir /s /q "%DST%"
mkdir "%DST%" >nul 2>nul
xcopy "%SRC%\*" "%DST%\" /E /I /Y /Q >nul
if errorlevel 1 (
  echo [LOI] Khong copy duoc CEP extension.
  if /I not "%~1"=="/silent" pause
  exit /b 1
)

for %%V in (8 9 10 11 12 13 14) do (
  reg add "HKCU\Software\Adobe\CSXS.%%V" /v PlayerDebugMode /t REG_SZ /d 1 /f >nul 2>nul
)

echo [OK] Da cai vao:
echo %DST%
echo.
echo Premiere Pro 2021: mo Window ^> Extensions ^> PR Auto Bridge 2021+
echo Premiere moi hon: co the nam trong Window ^> Extensions ^(Legacy^).
echo Neu Premiere dang mo, hay tat va mo lai Premiere.
if /I not "%~1"=="/silent" pause
exit /b 0