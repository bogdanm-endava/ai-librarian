@echo off
REM This script starts the Flask app defined in controller.py and passes any arguments to Flask

REM Set the FLASK_APP environment variable to the controller.py file
set FLASK_APP=source/web_controller.py

REM Call flask run with any arguments passed to this script
flask run %*
