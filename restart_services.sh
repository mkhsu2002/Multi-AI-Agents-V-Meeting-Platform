#!/bin/bash

# 設置顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 設置端口
FRONTEND_PORT=3000
BACKEND_PORT=8000

# 項目路徑
PROJECT_ROOT="$(dirname "$(realpath "$0")")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}飛豬隊友 AI 虛擬會議系統 - 服務重啟腳本${NC}"
echo -e "${GREEN}============================================${NC}"

# 檢查並關閉佔用前端端口的進程
check_and_kill_port() {
    local port=$1
    local service_name=$2
    
    echo -e "\n${YELLOW}正在檢查${service_name}端口 ${port}...${NC}"
    
    # 查找佔用指定端口的進程PID
    local pid=$(lsof -ti:$port)
    
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}發現佔用${service_name}端口 ${port} 的進程 (PID: $pid)${NC}"
        echo -e "${YELLOW}正在關閉進程...${NC}"
        kill -9 $pid
        echo -e "${GREEN}進程已關閉${NC}"
    else
        echo -e "${GREEN}${service_name}端口 ${port} 未被佔用${NC}"
    fi
}

# 啟動前端服務
start_frontend() {
    echo -e "\n${YELLOW}正在啟動前端服務...${NC}"
    cd "$FRONTEND_DIR" || { echo -e "${RED}無法進入前端目錄${NC}"; exit 1; }
    npm start &
    echo -e "${GREEN}前端服務啟動命令已發出 (http://localhost:${FRONTEND_PORT})${NC}"
}

# 啟動後端服務
start_backend() {
    echo -e "\n${YELLOW}正在啟動後端服務...${NC}"
    cd "$BACKEND_DIR" || { echo -e "${RED}無法進入後端目錄${NC}"; exit 1; }
    
    # 檢查虛擬環境
    if [ -d "venv" ]; then
        echo -e "${YELLOW}正在激活虛擬環境...${NC}"
        source venv/bin/activate || { echo -e "${RED}無法激活虛擬環境${NC}"; exit 1; }
    fi
    
    # 啟動後端
    python run.py &
    echo -e "${GREEN}後端服務啟動命令已發出 (http://localhost:${BACKEND_PORT})${NC}"
}

# 主程序
echo -e "${YELLOW}開始檢查並重啟服務...${NC}"

# 檢查並關閉佔用端口的進程
check_and_kill_port $FRONTEND_PORT "前端"
check_and_kill_port $BACKEND_PORT "後端"

# 等待一下確保端口被釋放
echo -e "\n${YELLOW}等待端口釋放 (2秒)...${NC}"
sleep 2

# 啟動服務
start_backend
start_frontend

echo -e "\n${GREEN}所有服務啟動命令已發出！${NC}"
echo -e "${GREEN}前端: http://localhost:${FRONTEND_PORT}${NC}"
echo -e "${GREEN}後端: http://localhost:${BACKEND_PORT}${NC}"
echo -e "${GREEN}API測試頁面: http://localhost:${BACKEND_PORT}/api-test${NC}"
echo -e "\n${YELLOW}注意: 服務啟動需要一點時間，請耐心等待。${NC}"
echo -e "${YELLOW}如需停止服務，請按 Ctrl+C 兩次${NC}"

# 保持腳本運行
wait 