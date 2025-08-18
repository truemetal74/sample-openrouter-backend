@echo off
REM Sample OpenRouter Backend Setup Script for Windows
REM This script helps set up and run the application

echo.
echo ========================================
echo   Sample OpenRouter Backend Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy env.example to .env and configure your settings:
    echo   copy env.example .env
    echo.
    echo Required settings:
    echo   - OPENROUTER_API_KEY
    echo   - SECRET_KEY
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Available commands:
echo.
echo 1. Run the application:
echo    python app\main.py
echo.
echo 2. Run with uvicorn:
echo    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
echo.
echo 3. Generate access token:
echo    python scripts\generate_token.py --user-id your_user_id
echo.
echo 4. Run with Docker:
echo    docker-compose up --build
echo.
echo The application will be available at: http://localhost:8080
echo API documentation: http://localhost:8080/docs
echo.
pause
