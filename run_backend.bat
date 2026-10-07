@echo off
cd /d "%~dp0"
title AI Debate Coach - Backend
if not exist venv\Scripts\python.exe (
  echo Setup hasn't been done yet. Double-click setup.bat first.
  pause
  exit /b
)
cd backend
echo.
echo  Backend running at http://localhost:8000
echo  API docs:          http://localhost:8000/docs
echo  KEEP THIS WINDOW OPEN while you use the app.
echo.
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
pause
