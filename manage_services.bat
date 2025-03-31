@echo off
setlocal enabledelayedexpansion
title 飛豬隊友 AI 虛擬會議系統 - 服務管理工具

REM 定義顏色
set GREEN=92m
set YELLOW=93m
set RED=91m
set BLUE=94m
set NC=0m

REM 定義端口
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

:main
cls
call :show_title
call :show_menu
echo.
pause
goto main

:show_title
echo ============================================
echo    飛豬隊友 AI 虛擬會議系統 - 服務管理工具   
echo ============================================
echo.
goto :eof

:show_menu
echo 請選擇操作:
echo 1) 釋放佔用的端口
echo 2) 啟動後端服務
echo 3) 啟動前端服務
echo 4) 啟動所有服務
echo 5) 停止所有服務
echo 0) 退出
echo.

set /p choice=請輸入選項 [0-5]: 

if "%choice%"=="1" call :free_ports
if "%choice%"=="2" call :start_backend
if "%choice%"=="3" call :start_frontend
if "%choice%"=="4" call :start_all
if "%choice%"=="5" call :stop_all
if "%choice%"=="0" exit /b

goto :eof

:free_ports
echo 釋放端口 %BACKEND_PORT% 和 %FRONTEND_PORT%...
call :free_port %BACKEND_PORT%
call :free_port %FRONTEND_PORT%
echo 端口釋放操作完成
goto :eof

:free_port
set port=%~1
echo 檢查端口 %port% 是否被佔用...

REM 檢查端口是否被佔用
netstat -ano | findstr ":%port% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%port% " ^| findstr "LISTENING"') do (
        set pid=%%a
        echo 端口 %port% 被進程 !pid! 佔用
        echo 正在終止這些進程...
        taskkill /F /PID !pid! > nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo 成功終止進程 !pid!
        ) else (
            echo 無法終止進程 !pid!
        )
    )
    
    REM 再次檢查端口是否被釋放
    netstat -ano | findstr ":%port% " | findstr "LISTENING" > nul
    if !ERRORLEVEL! EQU 0 (
        echo 無法釋放端口 %port%, 請手動關閉佔用該端口的應用
    ) else (
        echo 端口 %port% 已成功釋放
    )
) else (
    echo 端口 %port% 未被佔用
)
goto :eof

:start_backend
echo 正在啟動後端服務...

REM 檢查後端端口
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    echo 端口 %BACKEND_PORT% 已被佔用，嘗試釋放...
    call :free_port %BACKEND_PORT%
    
    REM 再次檢查端口
    netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" > nul
    if !ERRORLEVEL! EQU 0 (
        echo 無法啟動後端服務，端口 %BACKEND_PORT% 無法使用
        goto :eof
    )
)

echo 啟動後端服務 (FastAPI)...
start cmd /c "cd backend && python run.py"

REM 等待服務啟動
echo 等待後端服務啟動...
timeout /t 3 > nul

REM 檢查服務是否成功啟動
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    echo 後端服務已成功啟動於端口 %BACKEND_PORT%
) else (
    echo 後端服務啟動失敗
)
goto :eof

:start_frontend
echo 正在啟動前端服務...

REM 檢查前端端口
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    echo 端口 %FRONTEND_PORT% 已被佔用，嘗試釋放...
    call :free_port %FRONTEND_PORT%
    
    REM 再次檢查端口
    netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" > nul
    if !ERRORLEVEL! EQU 0 (
        echo 無法啟動前端服務，端口 %FRONTEND_PORT% 無法使用
        goto :eof
    )
)

echo 啟動前端服務 (React)...
start cmd /c "cd frontend && npm start"

REM 等待服務啟動
echo 等待前端服務啟動...
timeout /t 5 > nul

REM 檢查服務是否成功啟動
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    echo 前端服務已成功啟動於端口 %FRONTEND_PORT%
) else (
    echo 前端服務啟動失敗
)
goto :eof

:start_all
echo 啟動所有服務...
call :start_backend
call :start_frontend
echo 所有服務啟動操作完成
goto :eof

:stop_all
echo 正在停止所有服務...

REM 釋放後端端口
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    call :free_port %BACKEND_PORT%
) else (
    echo 後端服務已停止
)

REM 釋放前端端口
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" > nul
if %ERRORLEVEL% EQU 0 (
    call :free_port %FRONTEND_PORT%
) else (
    echo 前端服務已停止
)

echo 所有服務已停止
goto :eof 