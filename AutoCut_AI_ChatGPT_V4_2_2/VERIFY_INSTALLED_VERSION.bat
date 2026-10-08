@echo off
setlocal EnableExtensions
set "DST=%APPDATA%\Adobe\CEP\extensions\AutoCut_AI_ChatGPT"
echo === VERIFY AUTO CUT AI INSTALLED ===
if not exist "%DST%\VERSION.json" exit /b 1
type "%DST%\VERSION.json"
findstr /C:"\"version\":\"4.2.2\"" "%DST%\VERSION.json" >nul || exit /b 2
if not exist "%DST%\js\c1Builder.js" exit /b 3
findstr /C:"C1Builder.fromFile(timing.path)" "%DST%\js\main.js" >nul || exit /b 4
findstr /C:"ChatGPTDirect.stage1(" "%DST%\js\main.js" >nul && exit /b 5
echo [PASS] v4.2.2 installed files are correct.
pause
exit /b 0
