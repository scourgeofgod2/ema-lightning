@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam yok. Once kurulum yapin:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python -m pip install -e ".[dev]" --extra-index-url https://download.pytorch.org/whl/cpu
    pause
    exit /b 1
)

if /i "%~1"=="browser" goto browser

echo EMA Lightning basliyor: http://127.0.0.1:8000
echo Ilk seferde model inecegi icin biraz surebilir. Durdurmak icin Ctrl+C.
echo.
start "EMA tarayici" /min cmd /c ""%~f0" browser"
.venv\Scripts\python.exe web\server.py
exit /b

:browser
set /a n=0
:loop
set /a n+=1
if %n% gtr 180 exit /b 1
timeout /t 1 /nobreak >nul
curl -sf -o nul http://127.0.0.1:8000
if errorlevel 1 goto loop
start "" http://127.0.0.1:8000
