@echo off
cd /d "%~dp0.."
echo Requisitos: Windows 10/11 64-bit + Visual Studio C++ Desktop.
if not exist .venv\Scripts\flet.exe (
 echo Crea tu venv e instala: pip install "flet[all]==1.0.4"
 pause
 exit /b 1
)
.venv\Scripts\flet.exe build windows
pause
