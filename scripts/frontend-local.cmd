@echo off
cd /d "%~dp0..\frontend"
if exist "..\.tools\node.exe" (
 "..\.tools\node.exe" node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173 --strictPort
) else (
 node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173 --strictPort
)
