#!/bin/bash
# 飛豬隊友 AI 虛擬會議系統 Git 初始化腳本

# 顯示彩色輸出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}飛豬隊友 AI 虛擬會議系統 Git 初始化腳本${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# 檢查 git 是否已安裝
if ! command -v git &> /dev/null; then
    echo -e "${RED}錯誤: Git 未安裝。請先安裝 Git。${NC}"
    exit 1
fi

# 檢查是否已經是 git 倉庫
if [ -d ".git" ]; then
    echo -e "${RED}警告: 這個目錄已經是一個 Git 倉庫。${NC}"
    echo "是否要繼續？這將重置現有的 Git 配置。"
    read -p "繼續？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 1
    fi
    echo "繼續初始化..."
fi

# 初始化 git 倉庫
echo -e "${GREEN}初始化 Git 倉庫...${NC}"
git init

# 讀取倉庫地址
echo ""
echo "請輸入您的 GitHub 用戶名和倉庫名："
read -p "GitHub 用戶名: " github_username
read -p "倉庫名稱 (默認: TinyPigTroupe): " repo_name
repo_name=${repo_name:-TinyPigTroupe}

# 添加文件到暫存區
echo ""
echo -e "${GREEN}添加文件到暫存區...${NC}"
git add .

# 提交更改
echo ""
echo -e "${GREEN}提交初始版本...${NC}"
git commit -m "初始提交 v0.5.0：飛豬隊友 AI 虛擬會議系統"

# 添加遠程倉庫
echo ""
echo -e "${GREEN}添加遠程倉庫...${NC}"
git remote add origin "https://github.com/${github_username}/${repo_name}.git"

# 提示用戶推送到 GitHub
echo ""
echo -e "${GREEN}初始化完成！${NC}"
echo -e "現在您可以使用以下命令推送到 GitHub:"
echo -e "${BLUE}git push -u origin main${NC}"
echo ""
echo "如果您的默認分支是 'master'，請使用:"
echo -e "${BLUE}git push -u origin master${NC}"
echo ""
echo "是否立即推送到 GitHub？"
read -p "推送到 GitHub？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 嘗試 main 分支
    if git push -u origin main; then
        echo -e "${GREEN}成功推送到 GitHub!${NC}"
    else
        echo -e "${BLUE}嘗試推送到 master 分支...${NC}"
        # 如果失敗，嘗試 master 分支
        if git push -u origin master; then
            echo -e "${GREEN}成功推送到 GitHub!${NC}"
        else
            echo -e "${RED}推送失敗。請手動推送。${NC}"
            echo "可能需要先在 GitHub 上創建倉庫，或檢查您的 GitHub 認證。"
        fi
    fi
else
    echo "跳過推送。您可以稍後手動推送。"
fi

echo ""
echo -e "${GREEN}腳本執行完成！${NC}"
echo -e "您的倉庫已準備好：https://github.com/${github_username}/${repo_name}"
echo "" 