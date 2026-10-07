@echo off
cd /d "%~dp0"
title AI Debate Coach - Tests
if not exist venv\Scripts\python.exe (
  echo Setup hasn't been done yet. Double-click setup.bat first.
  pause
  exit /b
)
venv\Scripts\python.exe -m pytest -v
pause
