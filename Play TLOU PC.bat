@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python not found. Install from python.org and check "Add to PATH". & pause & exit /b 1)
python "launcher\tlou_launcher.py"
