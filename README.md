# 飛豬隊友 AI 虛擬會議系統 (v1.0)

基於 LLM 驅動的 Web 應用，允許多個智能體 AI Agents 進行互動式討論，模擬商務會議、創意腦力激盪或學術辯論場景。

## 版本說明

當前版本：v1.0
主要更新：
- 穩定版本首次發布
- 完整支持 WebSocket 通信機制
- 優化智能體對話流程與回應速度
- 支持最新版 OpenAI API 格式（sk-proj-*）
- 增強用戶界面，提供更直觀的操作體驗

## 功能特點

- **智能體交互與個性化**：每一位AI角色均由LLM驅動，具備不同的個性、專業領域和發言風格
- **會議流程管理**：支持自定義主題、多回合討論、角色分配
- **視覺化對話呈現**：動態展示智能體對話，類似於真實會議場景
- **會議紀錄與結果分析**：自動生成會議記錄，提供關鍵內容摘要
- **預設角色系統**：包含總經理、行銷經理、業務經理等不同職能的"豬隊友"角色
- **即時互動**：通過 WebSocket 技術，確保對話流程的即時性和連貫性
- **會議階段控制**：包括介紹階段、討論階段和結論階段，模擬真實會議流程
- **多輪討論支持**：可配置多輪討論，每輪討論都有明確的主題和目標
- **會議記錄導出**：支持將整個會議過程導出為Markdown格式，方便保存和分享

## 技術架構

- **前端**：React + TailwindCSS
- **後端**：Python (FastAPI)
- **AI 引擎**：OpenAI API
- **即時通信**：WebSocket
- **數據存儲**：暫時使用內存存儲，未來規劃支持數據庫

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
4. 會議結束後，主持人將總結會議重點
5. 您可以隨時導出會議記錄

## API 測試頁面

訪問 `http://localhost:8000/api-test` 可以打開 API 測試頁面，用於：
- 檢查 OpenAI API 連接狀態
- 更新 API 密鑰
- 測試與 LLM 的對話

## 安裝說明

### 系統需求
- Node.js v14+ 
- Python 3.8+
- npm 或 yarn
- 有效的 OpenAI API 金鑰

### 完整安裝步驟

1. 克隆倉庫
   ```bash
   git clone https://github.com/您的用戶名/TinyPigTroupe.git
   cd TinyPigTroupe
   ```

2. 安裝並啟動後端
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # 記得編輯 .env 文件添加您的 API 密鑰
   python run.py  # 或使用 uvicorn app.main:app --reload
   ```

3. 安裝並啟動前端
   ```bash
   cd ../frontend
   npm install
   npm start
   ```

4. 訪問應用
   - 前端: http://localhost:3000
   - 後端: http://localhost:8000
   - API測試頁面: http://localhost:8000/api-test

## 自定義與擴展

- 可以通過修改前端代碼添加新的 UI 元素或互動功能
- 通過後端代碼可以調整 AI 角色的生成邏輯和對話流程
- 如需添加新角色，可在 `frontend/src/config/agents.js` 中添加新的角色配置

## 未來規劃

- **優化會議流程**：讓討論更加緊湊有序，增強角色間的互動
- **智能體管理編輯介面**：提供直觀的UI介面進行角色編輯和管理
- **多國語言支持**：除繁體中文外，支持英文、日文等多種語言
- **多 LLM API支持**：除OpenAI外，支持Anthropic Claude、Google Gemini等多種LLM服務
- **不同情境會議模板**：預設不同會議情境的模板，如產品規劃、市場分析、創意激發等
- **數據庫整合**：從內存存儲轉向持久化存儲，支持會議記錄查詢
- **用戶認證系統**：添加登錄功能，支持多用戶環境
- **會議分析工具**：提供更深入的會議內容分析

## 致謝

感謝 [Microsoft TinyTroupe](https://github.com/microsoft/TinyTroupe/)！本項目在概念上受到微軟 TinyTroupe 的啟發，但由於既有架構未能完全滿足我們想要實現的效果，我們毅然決定從頭開始重新構建。我們的目標是創建一個每一位智能體均由LLM驅動的虛擬會議系統，並提供視覺化的會議呈現效果，讓使用者能直觀地感受AI智能體之間的互動和對話。

## 貢獻

我們熱切歡迎各領域的專家和開發者加入本項目！無論您擅長前端開發、後端架構、UI設計、提示詞工程或是LLM應用，都能在這裡發揮您的才能。如果您有任何想法或建議，請隨時提交 Pull Request 或提出 Issue。

## 許可證

MIT 