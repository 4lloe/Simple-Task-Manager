@echo off
chcp 65001 >nul
title Simple Task Manager - Stop All Services
color 0C

echo ============================================================
echo   SIMPLE TASK MANAGER - ЗУПИНКА ВСІХ СЕРВІСІВ
echo   Практична робота №4 - Малій Д.Д., КНТ-22-4
echo ============================================================
echo.

echo [1/6] Зупинка процесів Python на порту 8500 (Service Registry)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8500 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [2/6] Зупинка процесів Python на порту 8000 (API Gateway)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [3/6] Зупинка процесів Python на порту 8001 (Task Service)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [4/6] Зупинка процесів Python на порту 8002 (Category Service)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [5/6] Зупинка процесів Python на порту 8003 (Notification Service)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [6/6] Зупинка Frontend (порт 8080)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo.
echo Закриття вікон терміналів...
taskkill /FI "WINDOWTITLE eq Service Registry*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Task Service*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Category Service*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Notification Service*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq API Gateway*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F >nul 2>&1

echo.
echo ============================================================
echo   ВСІ СЕРВІСИ ЗУПИНЕНО!
echo ============================================================
echo.
pause
