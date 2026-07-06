@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Flask dashboard...
python app.py
if errorlevel 1 pause
