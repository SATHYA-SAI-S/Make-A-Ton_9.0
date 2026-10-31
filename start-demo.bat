@echo off
title SubscriptIQ Full Stack Launcher
color 0A

echo ==========================================================
echo        SubscriptIQ Subscription Management System
echo            Person 1 - Core Management Module
echo ==========================================================
echo.

:: 1. Verify and Start Mailpit Local SMTP Service
echo [1/3] Checking Mailpit local email service...
netstat -ano | findstr ":1025" >nul
if %errorlevel% equ 0 (
    echo [OK] Mailpit is already running on ports 1025 (SMTP) and 8025 (Web UI).
) else (
    if exist ".tools\mailpit\mailpit.exe" (
        echo Starting Mailpit background process...
        start "SubscriptIQ Mailpit" /min ".tools\mailpit\mailpit.exe"
        timeout /t 2 >nul
        echo [OK] Mailpit started successfully.
    ) else (
        echo [WARN] Mailpit executable not found in .tools\mailpit\.
        echo Please ensure Mailpit is installed or run in mock mode.
    )
)

:: 2. Start Backend FastAPI Server
echo.
echo [2/3] Checking Backend API Server...
netstat -ano | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo [OK] Backend server is already running on port 8000.
) else (
    echo Starting FastAPI backend on http://127.0.0.1:8000...
    start "SubscriptIQ Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    timeout /t 3 >nul
    echo [OK] Backend launched.
)

:: 3. Start Frontend Vite Development Server
echo.
echo [3/3] Checking Frontend Dev Server...
netstat -ano | findstr ":5173" >nul
if %errorlevel% equ 0 (
    echo [OK] Frontend is already running on port 5173.
) else (
    echo Starting React frontend on http://127.0.0.1:5173...
    start "SubscriptIQ Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0 --port 5173"
    timeout /t 3 >nul
    echo [OK] Frontend launched.
)

echo.
echo ==========================================================
echo   SubscriptIQ Services are Active and Ready!
echo ==========================================================
echo   * Web Application:  http://127.0.0.1:5173/
echo   * Mailpit Inbox:    http://127.0.0.1:8025/
echo   * Backend Swagger:  http://127.0.0.1:8000/docs
echo   * Internal Health:  http://127.0.0.1:8000/api/v1/health
echo ==========================================================
echo.
echo Pre-seeded Demo Logins:
echo   - Admin:    admin@example.com    / Admin@Secure123!
echo   - Staff:    staff@example.com    / Staff@Secure123!
echo   - Customer: acme@example.com     / Customer@Secure123!
echo.
echo Press any key to exit this launcher window (services keep running).
pause >nul
