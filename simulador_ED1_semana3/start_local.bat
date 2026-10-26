@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.11 -m venv .venv
    if errorlevel 1 (echo No se pudo crear el entorno. Revisa Python 3.11/3.12. & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 (echo Error instalando dependencias. & pause & exit /b 1)
echo Visita http://127.0.0.1:8001 en el navegador.
".venv\Scripts\python.exe" main.py
pause
