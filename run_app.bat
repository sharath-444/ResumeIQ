@echo off
setlocal

:: Check if virtual environment exists
if not exist venv (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

:: Ask user which version they want to run
echo.
echo ==========================================
echo       ResumeIQ - Startup Menu
echo ==========================================
echo 1. Run as Web App (Open in Browser)
echo 2. Run as Desktop App (Requires pywebview)
echo 3. Exit
echo ==========================================
echo.

set /p choice="Enter choice [1-3]: "

if "%choice%"=="1" (
    echo Starting Web App...
    python app.py
) else if "%choice%"=="2" (
    echo Checking for pywebview...
    pip install pywebview
    echo Starting Desktop App...
    python desktop_app.py
) else (
    echo Exiting.
)

pause
