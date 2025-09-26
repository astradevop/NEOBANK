@echo off
echo 🏦 NeoBank Setup - Activating Virtual Environment
echo ================================================

:: Activate virtual environment
call .venv\Scripts\activate

:: Run setup script
python setup_neobank.py

:: Keep window open
echo.
echo Press any key to start the development server...
pause > nul

:: Start development server
python manage.py runserver
