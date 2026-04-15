@echo off
title Gaming Python — Serveur API
echo.
echo  ================================================
echo    Gaming Python — Demarrage du serveur FastAPI
echo  ================================================
echo.
echo  > API disponible sur http://localhost:8000
echo  > Documentation : http://localhost:8000/docs
echo.

cd /d "%~dp0.."

if not exist venv (
    echo [!] Environnement virtuel introuvable. Creation...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo [+] Demarrage uvicorn...
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

pause
