@echo off
title Gaming Python — Menu
echo.
echo  ================================================
echo    Gaming Python — Demarrage du menu Pygame
echo  ================================================
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

echo [+] Demarrage du menu...
python client/main.py

pause
