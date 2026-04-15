@echo off
title Gaming Python — Tout lancer
echo.
echo  ================================================
echo    Gaming Python — Lancement complet
echo  ================================================
echo.
echo  [1] Serveur FastAPI dans une nouvelle fenetre
echo  [2] Menu Pygame dans cette fenetre
echo.

cd /d "%~dp0.."

if not exist venv (
    echo [!] Environnement virtuel introuvable. Installation...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo [+] Demarrage du serveur FastAPI...
start "Gaming Python — API" cmd /k "cd /d %cd% && venv\Scripts\activate.bat && uvicorn server.main:app --reload --host 0.0.0.0 --port 8000"

echo [+] Attente 2 secondes...
timeout /t 2 /nobreak >nul

echo [+] Demarrage du menu Pygame...
python client/main.py

pause
