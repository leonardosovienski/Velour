@echo off
echo Iniciando Velour...

echo [1/2] Subindo backend Python (porta 8000)...
start "Velour — Backend FastAPI" cmd /k ".venv\Scripts\activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Subindo frontend React (porta 5173)...
start "Velour — Frontend React" cmd /k "cd frontend && npm run dev"

echo.
echo Ambos os servicos iniciados.
echo   Backend:  http://127.0.0.1:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo Use a conta criada no cadastro ou com python bootstrap_admin.py.
echo Este atalho e exclusivo para desenvolvimento, apos instalar e migrar o banco.
echo.
echo Feche as janelas dos terminais para encerrar.
