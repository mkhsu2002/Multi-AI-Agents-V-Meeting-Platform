@echo off
:: 設置編碼為UTF-8
chcp 65001 > nul

:: 顯示啟動訊息
echo ===== 啟動飛豬隊友 AI 虛擬會議系統 =====
echo 正在檢查服務狀態...

:: 檢查端口是否被占用
netstat -ano | find ":8000" > nul
if %ERRORLEVEL% EQU 0 (
    echo 端口 8000 已被占用，嘗試關閉現有進程...
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000"') do (
        taskkill /f /pid %%a
    )
    timeout /t 1 > nul
)

:: 進入專案根目錄（若有需要可自行調整）
cd /d %~dp0

:: 啟動後端服務
echo 正在啟動後端服務...
cd backend
echo 進入虛擬環境...
:: 如果使用虛擬環境，取消下面註釋並修改路徑
:: call venv\Scripts\activate.bat

:: 啟動後端服務（在新窗口中運行）
start "飛豬隊友後端服務" cmd /c "python run.py & pause"

:: 等待後端啟動完成
echo 等待後端服務初始化...
timeout /t 5 > nul

:: 不檢查後端是否成功啟動（Windows下curl可能不可用）
echo 後端服務已啟動

:: 啟動前端服務
echo 正在啟動前端服務...
cd ..\frontend

:: 檢查node_modules是否存在
if not exist node_modules (
    echo 安裝前端依賴...
    call npm install
)

:: 啟動前端服務（在新窗口中運行）
start "飛豬隊友前端服務" cmd /c "npm start & pause"

echo ===== 飛豬隊友 AI 虛擬會議系統已啟動 =====
echo 前端地址: http://localhost:3000
echo 後端地址: http://localhost:8000
echo API 測試: http://localhost:8000/api/test
echo.
echo 關閉命令窗口以停止服務

:: 等待用戶按任意鍵
pause 