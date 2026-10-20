@echo off
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  .venv\Scripts\python.exe -m pip install "flet[all]==1.0.4" pytest
)
.venv\Scripts\python.exe main.py
pause
