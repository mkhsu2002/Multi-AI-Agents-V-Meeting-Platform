# 飛豬隊友 AI 虛擬會議系統 (v0.5)

基於 LLM 驅動的 Web 應用，允許多個智能體 AI Agents 進行互動式討論，模擬商務會議、創意腦力激盪或學術辯論場景。

## 版本說明

當前版本：v0.5
主要更新：
- 移除了 Socket.IO 依賴，統一使用原生 WebSocket 進行通信，避免路由衝突
- 增強了 WebSocket 連接的錯誤處理和日誌記錄
- 優化了 OpenAI API 的錯誤處理，支持新的 API 格式（sk-proj-*）
- 添加了 API 測試頁面，方便檢查 OpenAI 連接狀態

## 功能特點

- 智能體交互與個性化：AI 角色具備不同的個性、專業領域和發言風格
- 會議流程管理：支持自定義主題、多回合討論、角色分配
- 視覺化對話呈現：動態展示智能體對話，類似遊戲中 NPC 的互動場景
- 會議紀錄與結果分析：自動生成會議記錄，提供關鍵內容摘要
- 預設角色：包含總經理、行銷經理、業務經理等不同職能的"豬隊友"角色

## 技術架構

- **前端**：React + TailwindCSS
- **後端**：Python (FastAPI)
- **AI 引擎**：OpenAI API
- **即時通信**：Socket.IO

## 快速開始

### 前端設置

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 啟動開發服務器
npm start
```

### 後端設置

```bash
# 進入後端目錄
cd backend

# 創建並激活虛擬環境
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 文件，添加您的 OpenAI API 密鑰

# 啟動後端服務器
uvicorn app.main:app --reload
```

## 系統架構

```
/
├── frontend/                # React 前端
│   ├── public/              # 靜態文件
│   └── src/
│       ├── components/      # UI 組件
│       ├── contexts/        # React Context
│       ├── pages/           # 頁面組件
│       └── utils/           # 工具函數
├── backend/                 # Python 後端
│   ├── app/                 # 主應用
│   ├── models/              # 數據模型
│   └── utils/               # 工具函數
└── README.md                # 項目說明
```

## 使用說明

1. 打開應用後，您可以在設置面板中配置會議主題、回合數和參與者
2. 點擊"開始會議"按鈕後，系統將自動開始會議流程
3. 每位 AI 角色將依次進行自我介紹，然後進入討論階段
4. 會議結束後，秘書將總結會議重點
5. 您可以隨時導出會議記錄

## API 測試頁面

訪問 `http://localhost:8000/api-test` 可以打開 API 測試頁面，用於：
- 檢查 OpenAI API 連接狀態
- 更新 API 密鑰
- 測試與 LLM 的對話

## GitHub 上傳指南

若要將此項目上傳到 GitHub，請按照以下步驟操作：

1. 創建一個新的 GitHub 倉庫
   ```bash
   # 打開 GitHub 網站，登錄並創建一個新倉庫
   # 建議倉庫名稱：FlyPigAI 或 TinyPigTroupe
   ```

2. 初始化本地 Git 倉庫
   ```bash
   # 在項目根目錄中執行
   git init
   ```

3. 添加 .gitignore 文件
   ```bash
   # 在項目根目錄中創建 .gitignore 文件，內容如下：
   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   *.so
   .Python
   venv/
   ENV/
   
   # Node.js
   node_modules/
   npm-debug.log
   yarn-error.log
   
   # 環境變數
   .env
   
   # 系統文件
   .DS_Store
   Thumbs.db
   ```

4. 添加並提交文件
   ```bash
   git add .
   git commit -m "初始提交 v0.5：移除 Socket.IO，統一使用原生 WebSocket"
   ```

5. 添加遠程倉庫
   ```bash
   git remote add origin https://github.com/你的用戶名/你的倉庫名.git
   ```

6. 推送代碼
   ```bash
   git push -u origin main
   # 或者如果你的默認分支是 master
   # git push -u origin master
   ```

## 自定義與擴展

- 可以通過修改前端代碼添加新的 UI 元素或互動功能
- 通過後端代碼可以調整 AI 角色的生成邏輯和對話流程
- 如需添加新角色，可在 `App.js` 中的 `participants` 數組添加新的角色配置

## 貢獻

歡迎提交 Pull Request 或提出 Issue！

## 許可證

MIT 