@echo off
REM WWF API Local Server Startup Script
REM This script starts the FastAPI server for local testing with Postman

echo ============================================
echo WWF Learning Content Generator API
echo Starting Local Development Server...
echo ============================================
echo.

REM Navigate to src directory
cd /d "%~dp0src"

REM Check if virtual environment exists
if exist "..\rag\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\rag\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found at ..\rag\Scripts\activate.bat
    echo Continuing with system Python...
)

echo.
echo Starting server on http://localhost:8000
echo.
echo Available endpoints:
echo   GET  http://localhost:8000/           - API Documentation
echo   GET  http://localhost:8000/health     - Health Check
echo   POST http://localhost:8000/generate-mcqs-quickbase
echo   POST http://localhost:8000/generate-microlearning-quickbase
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

REM Start the FastAPI server
python main.py

pause
