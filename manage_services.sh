#!/bin/bash

# 飛豬隊友 AI 虛擬會議系統服務管理腳本
# 功能: 啟動/停止前後端服務，釋放被佔用的端口

# 定義顏色
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 無顏色

# 定義端口
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 顯示標題
show_title() {
    echo -e "${BLUE}"
    echo "============================================"
    echo "   飛豬隊友 AI 虛擬會議系統 - 服務管理工具   "
    echo "============================================"
    echo -e "${NC}"
}

# 檢查端口是否被佔用
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        # macOS/Linux 使用 lsof
        lsof -i :$port -t &> /dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        # Windows 使用 netstat
        netstat -ano | grep ":$port " | grep "LISTENING" &> /dev/null
        return $?
    else
        echo -e "${RED}無法檢查端口，缺少必要的工具 (lsof 或 netstat)${NC}"
        return 1
    fi
}

# 釋放被佔用的端口
free_port() {
    local port=$1
    local processes
    
    echo -e "${YELLOW}檢查端口 $port 是否被佔用...${NC}"
    
    if check_port $port; then
        if command -v lsof &> /dev/null; then
            # macOS/Linux 使用 lsof
            processes=$(lsof -i :$port -t)
            if [ -n "$processes" ]; then
                echo -e "${YELLOW}端口 $port 被以下進程佔用: $processes${NC}"
                echo -e "${YELLOW}正在終止這些進程...${NC}"
                for pid in $processes; do
                    kill -9 $pid 2> /dev/null
                    if [ $? -eq 0 ]; then
                        echo -e "${GREEN}成功終止進程 $pid${NC}"
                    else
                        echo -e "${RED}無法終止進程 $pid${NC}"
                    fi
                done
            fi
        elif command -v netstat &> /dev/null && command -v taskkill &> /dev/null; then
            # Windows 使用 netstat 和 taskkill
            processes=$(netstat -ano | grep ":$port " | grep "LISTENING" | awk '{print $5}')
            if [ -n "$processes" ]; then
                echo -e "${YELLOW}端口 $port 被以下進程佔用: $processes${NC}"
                echo -e "${YELLOW}正在終止這些進程...${NC}"
                for pid in $processes; do
                    taskkill /F /PID $pid 2> /dev/null
                    if [ $? -eq 0 ]; then
                        echo -e "${GREEN}成功終止進程 $pid${NC}"
                    else
                        echo -e "${RED}無法終止進程 $pid${NC}"
                    fi
                done
            fi
        else
            echo -e "${RED}無法釋放端口，缺少必要的工具${NC}"
            return 1
        fi
        
        # 再次檢查端口是否被釋放
        if check_port $port; then
            echo -e "${RED}無法釋放端口 $port, 請手動關閉佔用該端口的應用${NC}"
            return 1
        else
            echo -e "${GREEN}端口 $port 已成功釋放${NC}"
            return 0
        fi
    else
        echo -e "${GREEN}端口 $port 未被佔用${NC}"
        return 0
    fi
}

# 啟動後端服務
start_backend() {
    echo -e "${YELLOW}正在啟動後端服務...${NC}"
    
    # 檢查後端端口
    if check_port $BACKEND_PORT; then
        echo -e "${RED}端口 $BACKEND_PORT 已被佔用，嘗試釋放...${NC}"
        free_port $BACKEND_PORT
        if [ $? -ne 0 ]; then
            echo -e "${RED}無法啟動後端服務，端口 $BACKEND_PORT 無法使用${NC}"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}啟動後端服務 (FastAPI)...${NC}"
    cd backend && python run.py &
    
    # 等待服務啟動
    echo -e "${YELLOW}等待後端服務啟動...${NC}"
    sleep 3
    
    # 檢查服務是否成功啟動
    if check_port $BACKEND_PORT; then
        echo -e "${GREEN}後端服務已成功啟動於端口 $BACKEND_PORT${NC}"
        return 0
    else
        echo -e "${RED}後端服務啟動失敗${NC}"
        return 1
    fi
}

# 啟動前端服務
start_frontend() {
    echo -e "${YELLOW}正在啟動前端服務...${NC}"
    
    # 檢查前端端口
    if check_port $FRONTEND_PORT; then
        echo -e "${RED}端口 $FRONTEND_PORT 已被佔用，嘗試釋放...${NC}"
        free_port $FRONTEND_PORT
        if [ $? -ne 0 ]; then
            echo -e "${RED}無法啟動前端服務，端口 $FRONTEND_PORT 無法使用${NC}"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}啟動前端服務 (React)...${NC}"
    cd frontend && npm start &
    
    # 等待服務啟動
    echo -e "${YELLOW}等待前端服務啟動...${NC}"
    sleep 5
    
    # 檢查服務是否成功啟動
    if check_port $FRONTEND_PORT; then
        echo -e "${GREEN}前端服務已成功啟動於端口 $FRONTEND_PORT${NC}"
        return 0
    else
        echo -e "${RED}前端服務啟動失敗${NC}"
        return 1
    fi
}

# 停止所有服務
stop_all() {
    echo -e "${YELLOW}正在停止所有服務...${NC}"
    
    # 釋放後端端口
    if check_port $BACKEND_PORT; then
        free_port $BACKEND_PORT
    else
        echo -e "${GREEN}後端服務已停止${NC}"
    fi
    
    # 釋放前端端口
    if check_port $FRONTEND_PORT; then
        free_port $FRONTEND_PORT
    else
        echo -e "${GREEN}前端服務已停止${NC}"
    fi
    
    echo -e "${GREEN}所有服務已停止${NC}"
}

# 顯示菜單
show_menu() {
    echo -e "${BLUE}請選擇操作:${NC}"
    echo -e "${BLUE}1) 釋放佔用的端口${NC}"
    echo -e "${BLUE}2) 啟動後端服務${NC}"
    echo -e "${BLUE}3) 啟動前端服務${NC}"
    echo -e "${BLUE}4) 啟動所有服務${NC}"
    echo -e "${BLUE}5) 停止所有服務${NC}"
    echo -e "${BLUE}0) 退出${NC}"
    
    read -p "請輸入選項 [0-5]: " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}釋放端口 $BACKEND_PORT 和 $FRONTEND_PORT...${NC}"
            free_port $BACKEND_PORT
            free_port $FRONTEND_PORT
            echo -e "${GREEN}端口釋放操作完成${NC}"
            ;;
        2)
            start_backend
            ;;
        3)
            start_frontend
            ;;
        4)
            echo -e "${YELLOW}啟動所有服務...${NC}"
            start_backend
            start_frontend
            echo -e "${GREEN}所有服務啟動操作完成${NC}"
            ;;
        5)
            stop_all
            ;;
        0)
            echo -e "${GREEN}感謝使用，再見！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}無效的選項，請重新選擇${NC}"
            ;;
    esac
}

# 主循環
main() {
    while true; do
        show_title
        show_menu
        echo ""
        read -p "按 Enter 繼續..." dummy
        clear
    done
}

# 執行主函數
main 