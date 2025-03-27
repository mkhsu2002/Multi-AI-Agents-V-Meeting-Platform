#!/bin/bash

# 顯示啟動訊息
echo "===== 啟動飛豬隊友 AI 虛擬會議系統 ====="
echo "正在檢查服務狀態..."

# 檢查端口是否被占用
if lsof -ti:8000 > /dev/null; then
    echo "端口 8000 已被占用，嘗試關閉現有進程..."
    kill -9 $(lsof -ti:8000)
    sleep 1
fi

# 進入專案根目錄（若有需要可自行調整）
cd "$(dirname "$0")"

# 啟動後端服務
echo "正在啟動後端服務..."
cd backend
echo "進入虛擬環境..."
# 如果使用虛擬環境，取消下面註釋並修改路徑
source venv/bin/activate

# 啟動後端服務（在背景運行）
python run.py &
BACKEND_PID=$!
echo "後端服務已啟動，PID: $BACKEND_PID"

# 等待後端啟動完成
echo "等待後端服務初始化..."
sleep 3

# 檢查後端是否成功啟動
if ! curl -s http://localhost:8000/api/test > /dev/null; then
    echo "後端服務啟動失敗，請檢查錯誤訊息"
    exit 1
fi

echo "後端服務已成功啟動"

# 啟動前端服務
echo "正在啟動前端服務..."
cd ../frontend

# 檢查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "安裝前端依賴..."
    npm install
fi

# 啟動前端服務
npm start &
FRONTEND_PID=$!
echo "前端服務已啟動，PID: $FRONTEND_PID"

echo "===== 飛豬隊友 AI 虛擬會議系統已啟動 ====="
echo "前端地址: http://localhost:3000"
echo "後端地址: http://localhost:8000"
echo "API 測試: http://localhost:8000/api/test"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 等待用戶按Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; echo '系統已關閉'; exit" INT
wait 