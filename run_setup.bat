@echo off
echo 🏦 NeoBank - Quick Setup and Run
echo ==================================

echo Activating virtual environment...
call .venv\Scripts\activate

echo Creating superuser and test data...
python quick_setup.py

echo.
echo Starting development server...
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver
