@echo off
REM Setup script for AI Code Generation System with LangGraph (CMD version)

echo ========================================
echo AI Code Generation System - Setup
echo ========================================
echo.

REM Check Python version
python --version
echo.

REM Check if venv exists
if exist venv (
    echo Virtual environment already exists.
    echo Use: rmdir /s venv  to remove and recreate
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check .env file
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo Please edit .env and add your API keys!
    echo Minimum required: GEMINI_API_KEY or GROQ_API_KEY
) else (
    echo .env file exists
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env with your API keys:
echo    notepad .env
echo.
echo 2. Run tests:
echo    python test_system.py
echo.
echo 3. Execute project generation:
echo    python main_langgraph.py
echo.

REM Run tests
python test_system.py

pause