<#
.SYNOPSIS
    Setup script for AI Code Generation System with LangGraph
.DESCRIPTION
    Creates virtual environment, installs dependencies, and configures the project
#>

param(
    [switch]$ForceRecreate,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Code Generation System - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Green

if ($pythonVersion -notmatch "3\.(11|12|13)") {
    Write-Warning "Recommended Python 3.11+, found: $pythonVersion"
}

# Check if venv exists
$venvPath = ".\venv"
if (Test-Path $venvPath) {
    if ($ForceRecreate) {
        Write-Host "Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    } else {
        Write-Host "Virtual environment already exists. Use -ForceRecreate to rebuild." -ForegroundColor Yellow
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "$venvPath\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env and add your API keys!" -ForegroundColor Red
    Write-Host "Minimum required: GEMINI_API_KEY or GROQ_API_KEY" -ForegroundColor Red
} else {
    Write-Host ".env file exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env with your API keys:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run tests:" -ForegroundColor White
Write-Host "   python test_system.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Execute project generation:" -ForegroundColor White
Write-Host "   python main_langgraph.py" -ForegroundColor Gray
Write-Host ""

if (-not $SkipTests) {
    Write-Host "Running tests..." -ForegroundColor Cyan
    python test_system.py
}