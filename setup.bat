@echo off
setlocal
cd /d "%~dp0"
title AI Debate Coach - Setup
echo.
echo  ==========================================
echo     AI Debate Coach - one-time setup
echo  ==========================================
echo  Folder: %CD%
echo.

rem --- Problem 1: running from inside the zip file ---
echo %CD% | find /i "AppData\Local\Temp" >nul
if not errorlevel 1 goto inzip
if not exist requirements.txt goto inzip

rem --- Problem 2: Python missing or not on PATH ---
set "PY="
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY py --version >nul 2>&1
if not defined PY if not errorlevel 1 set "PY=py"
if not defined PY goto nopython

rem --- Problem 3: Python too old ---
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto oldpython

echo  Found:
%PY% --version
echo.
echo  [1/3] Creating virtual environment...
if not exist venv\Scripts\python.exe %PY% -m venv venv
if not exist venv\Scripts\python.exe goto venvfail

echo  [2/3] Updating pip...
venv\Scripts\python.exe -m pip install --upgrade pip --default-timeout=120 --retries 10

echo.
echo  [3/3] Installing packages. This can take 3 to 10 minutes - don't close this window...
venv\Scripts\python.exe -m pip install -r requirements.txt --default-timeout=120 --retries 10
if errorlevel 1 goto pipfail

echo.
echo  ==========================================
echo   SUCCESS! Setup is done.
echo   Next: double-click run_backend.bat
echo   Then: double-click run_frontend.bat
echo  ==========================================
goto end

:inzip
echo  [PROBLEM] You are running this from INSIDE the zip file.
echo.
echo  Fix: close this window, right-click ai-debate-coach.zip,
echo  choose "Extract All...", open the extracted folder,
echo  then double-click setup.bat again.
goto end

:nopython
echo  [PROBLEM] Python is not installed, or Windows can't find it.
echo.
echo  Fix:
echo   1. Go to https://www.python.org/downloads/ and download Python.
echo   2. When installing, TICK the box "Add python.exe to PATH" at the bottom.
echo   3. Restart your laptop, then double-click setup.bat again.
echo.
echo  Note: if typing python opens the Microsoft Store, open Windows Settings,
echo  search "Manage app execution aliases" and turn OFF the two Python entries.
goto end

:oldpython
echo  [PROBLEM] Your Python is too old. This project needs Python 3.10 or newer.
%PY% --version
echo  Fix: install the latest Python from https://www.python.org/downloads/
echo  - tick "Add python.exe to PATH" - then run setup.bat again.
goto end

:venvfail
echo  [PROBLEM] Couldn't create the virtual environment (venv folder).
echo  Fix: move the project to a simple folder like C:\Projects\ai-debate-coach
echo  - no OneDrive, no special characters - then run setup.bat again.
goto end

:pipfail
echo.
echo  [PROBLEM] Package download failed. This is almost always the internet connection.
echo  Fix: check your data or Wi-Fi, then just run setup.bat again -
echo  it continues from where it stopped.
goto end

:end
echo.
pause
