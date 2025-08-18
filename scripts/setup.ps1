# Sample OpenRouter Backend Setup Script for Windows PowerShell
# This script helps set up and run the application

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Sample OpenRouter Backend Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy env.example to .env and configure your settings:" -ForegroundColor Yellow
    Write-Host "  Copy-Item env.example .env" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Required settings:" -ForegroundColor Yellow
    Write-Host "  - OPENROUTER_API_KEY" -ForegroundColor Cyan
    Write-Host "  - SECRET_KEY" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Run the application:" -ForegroundColor Cyan
Write-Host "   python app\main.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Run with uvicorn:" -ForegroundColor Cyan
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080" -ForegroundColor White
Write-Host ""
Write-Host "3. Generate access token:" -ForegroundColor Cyan
Write-Host "   python scripts\generate_token.py --user-id your_user_id" -ForegroundColor White
Write-Host ""
Write-Host "4. Run with Docker:" -ForegroundColor Cyan
Write-Host "   docker-compose up --build" -ForegroundColor White
Write-Host ""
Write-Host "The application will be available at: http://localhost:8080" -ForegroundColor Green
Write-Host "API documentation: http://localhost:8080/docs" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to continue"
