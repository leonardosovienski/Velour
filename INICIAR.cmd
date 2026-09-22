@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Instale as dependencias conforme README.md.
 pause
 exit /b 1
)
if not exist ".env" (
 echo Configure .env conforme README.md.
 pause
 exit /b 1
)
start "Velour Backend" cmd /k "call scripts\backend-local.cmd"
start "Velour Frontend" cmd /k "call scripts\frontend-local.cmd"
echo Abra http://127.0.0.1:5173 quando os terminais estiverem prontos.
echo Feche os dois terminais para encerrar o Velour.
