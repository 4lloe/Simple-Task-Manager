@echo off
chcp 65001 >nul
title Simple Task Manager - Microservices Launcher
color 0A

echo ============================================================
echo   SIMPLE TASK MANAGER - MICROSERVICES
echo   Практична робота №4 - Малій Д.Д., КНТ-22-4
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] Запуск Service Registry (порт 8500)...
start "Service Registry [8500]" cmd /k "cd /d "%~dp0microservices\service_registry" && py app.py"
timeout /t 3 /nobreak >nul

echo [2/5] Запуск Task Service (порт 8001)...
start "Task Service [8001]" cmd /k "cd /d "%~dp0microservices\task_service" && py app.py"
timeout /t 2 /nobreak >nul

echo [3/5] Запуск Category Service (порт 8002)...
start "Category Service [8002]" cmd /k "cd /d "%~dp0microservices\category_service" && py app.py"
timeout /t 2 /nobreak >nul

echo [4/5] Запуск Notification Service (порт 8003)...
start "Notification Service [8003]" cmd /k "cd /d "%~dp0microservices\notification_service" && py app.py"
timeout /t 2 /nobreak >nul

echo [5/5] Запуск API Gateway (порт 8000)...
start "API Gateway [8000]" cmd /k "cd /d "%~dp0microservices\api_gateway" && py app.py"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo   ВСІ МІКРОСЕРВІСИ ЗАПУЩЕНО!
echo ============================================================
echo.
echo   Service Registry:     http://127.0.0.1:8500/docs
echo   API Gateway:          http://127.0.0.1:8000/docs
echo   Task Service:         http://127.0.0.1:8001/docs
echo   Category Service:     http://127.0.0.1:8002/docs
echo   Notification Service: http://127.0.0.1:8003/docs
echo.
echo   Frontend працює через: http://127.0.0.1:8000/api/*
echo.
echo   Для зупинки закрийте всі вікна терміналів
echo ============================================================
echo.
pause
