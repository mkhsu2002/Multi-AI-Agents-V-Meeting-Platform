#!/bin/bash

# 顯示啟動訊息
echo "===== 啟動飛豬隊友 AI 虛擬會議系統 ====="
echo "正在檢查服務狀態..."

# 檢查端口是否被占用
check_and_kill_port() {
  local port=$1
  if lsof -ti:$port > /dev/null; then
    echo "端口 $port 已被占用，嘗試關閉現有進程..."
    kill -9 $(lsof -ti:$port)
    sleep 1
    if lsof -ti:$port > /dev/null; then
       echo "關閉端口 $port 失敗，請手動檢查。"
       exit 1
    fi
    echo "端口 $port 已清理。"
  else
    echo "端口 $port 未被占用。"
  fi
}

check_and_kill_port 8000 # 檢查後端端口
check_and_kill_port 3000 # 檢查前端端口 (如果需要)

# 進入專案根目錄
cd "$(dirname "$0")"
echo "當前目錄: $(pwd)"

# 啟動後端服務
echo "--- 正在設定後端服務 ---"
cd backend
echo "進入後端目錄: $(pwd)"

# 檢查並創建虛擬環境 (如果不存在)
if [ ! -d "venv" ]; then
    echo "找不到虛擬環境 'venv'，正在創建..."
    # 確保使用 python3 (或您系統上的 Python 3 可執行檔名)
    if command -v python3 &> /dev/null; then
        python3 -m venv venv
    elif command -v python &> /dev/null; then
        python -m venv venv
    else
        echo "錯誤：找不到 Python 3 解釋器，無法創建虛擬環境。"
        exit 1
    fi

    if [ $? -ne 0 ]; then
        echo "創建虛擬環境失敗。"
        exit 1
    fi
    echo "虛擬環境 'venv' 已創建。"
fi

# 啟用虛擬環境
echo "正在啟用虛擬環境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "啟用虛擬環境失敗。請檢查 venv 目錄是否正確。"
    exit 1
fi
echo "虛擬環境已啟用。"

# 在虛擬環境中安裝/更新依賴
echo "正在安裝/更新後端依賴 (請稍候)..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "安裝後端依賴失敗。"
    # 停用虛擬環境 (可選)
    # deactivate
    exit 1
fi
echo "後端依賴已安裝/更新。"

# 啟動後端服務（在背景運行）
echo "正在啟動後端服務 (使用 run.py)..."
python run.py &
BACKEND_PID=$!
echo "後端服務已啟動，PID: $BACKEND_PID"

# 等待後端啟動完成 (增加等待時間並改進檢查方式)
echo "等待後端服務初始化 (最多等待 15 秒)..."
backend_ready=0
for i in {1..15}; do
    if curl -s --fail http://localhost:8000/api/test > /dev/null; then
        echo "後端服務已就緒。"
        backend_ready=1
        break
    fi
    echo -n "." # 顯示進度
    sleep 1
done
echo "" # 換行

if [ $backend_ready -eq 0 ]; then
    echo "後端服務在 15 秒內未能成功啟動，請檢查 run.py 的日誌或後端輸出。"
    # 停用虛擬環境 (可選)
    # deactivate
    # 嘗試停止已啟動的後端進程
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 啟動前端服務
echo "--- 正在設定前端服務 ---"
cd ../frontend
echo "進入前端目錄: $(pwd)"

# 檢查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "找不到 node_modules，正在安裝前端依賴 (可能需要一些時間)..."
    npm install
    if [ $? -ne 0 ]; then
        echo "安裝前端依賴失敗。"
        # 停用虛擬環境 (可選)
        # deactivate
        # 停止後端服務
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    echo "前端依賴已安裝。"
fi

# 啟動前端服務
echo "正在啟動前端服務 (npm start)..."
npm start &
FRONTEND_PID=$!
echo "前端服務已啟動，PID: $FRONTEND_PID"

echo ""
echo "===== 飛豬隊友 AI 虛擬會議系統已啟動 ====="
echo "前端地址: http://localhost:3000"
echo "後端地址: http://localhost:8000"
echo "API 測試: http://localhost:8000/api/test"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 清理函數
cleanup() {
    echo ""
    echo "正在停止服務..."
    # 停止前端
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "正在停止前端服務 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    # 停止後端
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "正在停止後端服務 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    # 停用虛擬環境 (如果已啟用)
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "正在停用虛擬環境..."
        deactivate
    fi
    echo "系統已關閉。"
    exit 0
}

# 設置 trap
trap cleanup INT TERM

# 等待後台進程結束 (或者用戶按 Ctrl+C)
wait $BACKEND_PID $FRONTEND_PID 