@echo off
echo ========================================
echo Crypto Backtesting System - Setup
echo ========================================
echo.
echo Installing required packages...
echo.
pip install -r requirements.txt
echo.
echo ========================================
echo Installation complete!
echo Starting application...
echo ========================================
echo.
python run.py
pause
