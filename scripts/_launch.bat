@echo off
cd /d "%~dp0.."
call venv\Scripts\activate.bat
start "Gaming Python API" cmd /k "cd /d "%~dp0.." & call venv\Scripts\activate.bat & uvicorn server.main:app --reload --host 0.0.0.0 --port 8000"
ping 127.0.0.1 -n 3 > nul
python client/main.py
