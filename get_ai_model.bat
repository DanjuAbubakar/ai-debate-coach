@echo off
setlocal
cd /d "%~dp0"
title AI Debate Coach - Download AI model
echo.
echo  ==========================================
echo     Download the free AI model (one time)
echo  ==========================================
echo.

rem --- find Ollama ---
set "OLLAMA="
where ollama >nul 2>&1 && set "OLLAMA=ollama"
if not defined OLLAMA if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA goto noollama

rem --- choose a model that fits this laptop's memory ---
set "RAM=0"
for /f %%G in ('powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"') do set "RAM=%%G"
if %RAM% GEQ 8 (set "MODEL=llama3.2") else (set "MODEL=llama3.2:1b")
echo  Your laptop has about %RAM% GB of RAM, so we'll use: %MODEL%
echo.
echo  Downloading... (about 1.3 to 2 GB - keep this window open)
echo.
"%OLLAMA%" pull %MODEL%
if errorlevel 1 goto pullfail

echo.
echo  ==========================================
echo   DONE! The AI model is installed.
echo   1. Close the run_backend window if it's open
echo   2. Double-click run_backend.bat again
echo   3. Double-click run_frontend.bat
echo   The sidebar should now say "AI engine: Local LLM".
echo  ==========================================
goto end

:noollama
echo  [PROBLEM] Ollama isn't installed yet.
echo.
echo  1. Download it here: https://ollama.com/download/OllamaSetup.exe
echo  2. Install it like a normal program
echo  3. Double-click get_ai_model.bat again
echo.
echo  Opening the download page for you...
start "" "https://ollama.com/download/OllamaSetup.exe"
goto end

:pullfail
echo.
echo  [PROBLEM] The download didn't finish. Check your internet,
echo  make sure Ollama is running (llama icon near the clock),
echo  then double-click get_ai_model.bat again - it continues where it stopped.

:end
echo.
pause
