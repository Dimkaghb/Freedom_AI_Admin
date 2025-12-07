@echo off
echo.
echo =========================================
echo   RESTARTING BACKEND SERVER
echo =========================================
echo.

REM Kill existing process on port 8000
echo Stopping existing backend server on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo Starting backend server with new configuration...
echo.

REM Start the server
cd /d "%~dp0"
start "Freedom AI Backend" cmd /k "uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo =========================================
echo   Backend server is starting...
echo   Check the new window for logs
echo =========================================
echo.
pause
