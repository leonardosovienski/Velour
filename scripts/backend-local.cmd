@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
