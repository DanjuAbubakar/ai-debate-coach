@echo off
cd /d "%~dp0"
title AI Debate Coach - App
if not exist venv\Scripts\python.exe (
  echo Setup hasn't been done yet. Double-click setup.bat first.
  pause
  exit /b
)
cd frontend
echo.
echo  Opening the app in your browser at http://localhost:8501
echo  KEEP THIS WINDOW OPEN while you use the app.
echo.
..\venv\Scripts\python.exe -m streamlit run app.py --browser.gatherUsageStats false
pause
