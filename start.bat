@echo off
echo ========================================
echo  Simple Task Manager - Запуск системи
echo  ПЗ-5: Комплексування компонентів
echo ========================================
echo.

echo [1/2] Запуск Backend (FastAPI, порт 8000)...
start "Backend - FastAPI" cmd /k "cd /d %~dp0back && python app.py"

timeout /t 3 /nobreak > nul

echo [2/2] Запуск Frontend (Vite, порт 8080)...
start "Frontend - Vite" cmd /k "cd /d %~dp0front && npm run dev"

echo.
echo ========================================
echo  Система запущена!
echo  Backend:  http://127.0.0.1:8000
echo  Frontend: http://localhost:8080
echo  API Docs: http://127.0.0.1:8000/docs
echo ========================================
echo.
pause
