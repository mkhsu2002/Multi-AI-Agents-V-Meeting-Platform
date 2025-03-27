@echo off
rem 飛豬隊友 AI 虛擬會議系統 Git 初始化腳本 (Windows版)

echo =======================================
echo 飛豬隊友 AI 虛擬會議系統 Git 初始化腳本
echo =======================================
echo.

rem 檢查 git 是否已安裝
git --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 錯誤: Git 未安裝。請先安裝 Git。
    exit /b 1
)

rem 檢查是否已經是 git 倉庫
if exist ".git" (
    echo 警告: 這個目錄已經是一個 Git 倉庫。
    echo 是否要繼續？這將重置現有的 Git 配置。
    set /p continue=繼續？(y/n): 
    if /i "%continue%" neq "y" (
        echo 已取消。
        exit /b 1
    )
    echo 繼續初始化...
)

rem 初始化 git 倉庫
echo 初始化 Git 倉庫...
git init

rem 讀取倉庫地址
echo.
echo 請輸入您的 GitHub 用戶名和倉庫名：
set /p github_username=GitHub 用戶名: 
set /p repo_name=倉庫名稱 (默認: TinyPigTroupe): 

if "%repo_name%"=="" (
    set repo_name=TinyPigTroupe
)

rem 添加文件到暫存區
echo.
echo 添加文件到暫存區...
git add .

rem 提交更改
echo.
echo 提交初始版本...
git commit -m "初始提交 v0.5.0：飛豬隊友 AI 虛擬會議系統"

rem 添加遠程倉庫
echo.
echo 添加遠程倉庫...
git remote add origin "https://github.com/%github_username%/%repo_name%.git"

rem 提示用戶推送到 GitHub
echo.
echo 初始化完成！
echo 現在您可以使用以下命令推送到 GitHub:
echo git push -u origin main
echo.
echo 如果您的默認分支是 'master'，請使用:
echo git push -u origin master
echo.
echo 是否立即推送到 GitHub？
set /p push_now=推送到 GitHub？(y/n): 

if /i "%push_now%"=="y" (
    rem 嘗試 main 分支
    git push -u origin main > nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo 成功推送到 GitHub!
    ) else (
        echo 嘗試推送到 master 分支...
        rem 如果失敗，嘗試 master 分支
        git push -u origin master > nul 2>&1
        if %ERRORLEVEL% equ 0 (
            echo 成功推送到 GitHub!
        ) else (
            echo 推送失敗。請手動推送。
            echo 可能需要先在 GitHub 上創建倉庫，或檢查您的 GitHub 認證。
        )
    )
) else (
    echo 跳過推送。您可以稍後手動推送。
)

echo.
echo 腳本執行完成！
echo 您的倉庫已準備好：https://github.com/%github_username%/%repo_name%
echo.

pause 