@echo off
REM This script starts the Flask app defined in controller.py and passes any arguments to Flask

REM Set the FLASK_APP environment variable to the controller.py file
set FLASK_APP=source/web_controller.py
set CHROMA_DATA=data/chroma

REM Start Chroma DB
start "Chroma DB" cmd /k "cd backend && call activate/Scripts/activate.bat && chroma run --path %CHROMA_DATA%"

REM Start Flask App
start "Flask App" cmd /k "cd backend && call activate/Scripts/activate.bat && flask --app %FLASK_APP% run %*"

REM Start Frontend App (example: React)
start "Frontend" cmd /k "cd frontend && npm run dev"

echo All services started.
pause
