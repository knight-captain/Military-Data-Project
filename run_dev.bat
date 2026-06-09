@echo off
cd /d "%~dp0"

echo Pulling latest changes from Git...
git pull
if errorlevel 1 (
    echo.
    echo WARNING: git pull failed. You may have uncommitted changes or no internet.
    echo Continuing anyway...
    echo.
)

start "" "C:\Users\mckay\OneDrive\Documents\Code\Military Data Project"

call venv\Scripts\activate

echo Opening VS Code...
start "" code .