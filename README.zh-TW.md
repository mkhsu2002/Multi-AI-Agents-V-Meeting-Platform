# 多智能體 AI 虛擬會議平台 (MAAVMPv0.2)

[![YouTube 影片演示](https://img.youtube.com/vi/GujQzX5TVqE/0.jpg)](https://www.youtube.com/watch?v=GujQzX5TVqE)

*[English Version README](README.md)*

多智能體 AI 虛擬會議平台是一個由 LLM 驅動的多 AI 智能體群組會議平台，允許多個 AI 智能體進行互動式討論，模擬商務會議、創意腦力激盪或學術辯論。它具有開創性的基於 Web 的整個會議過程實時可視化。 

## 主要功能

- **AI 智能體管理**：完整的界面，用於創建、編輯和管理具有自訂個性的 AI 智能體
- **AI 智能體互動與個性化**：每個 AI 角色都由 LLM 驅動，具有獨特的個性、專業領域和說話風格
- **會議流程管理**：支持自訂主題、多輪討論和角色分配
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
2. 若要管理 AI 智能體，請導航至「智能體管理」頁面，在此您可以創建、編輯或刪除智能體
3. 點擊"開始會議"按鈕後，系統將自動開始會議流程
4. 每位 AI 角色將依次進行自我介紹，然後進入討論階段
5. 會議結束後，主持人將總結會議重點
6. 您可以隨時導出會議記錄

## API 測試頁面

訪問 `http://localhost:8000/api-test` 可以打開 API 測試頁面，用於：
- 檢查 OpenAI API 連接狀態
- 臨時更新 API 金鑰以供測試
- 使用後端邏輯直接測試與 LLM 的對話

## 安裝說明

### 系統需求
- Node.js v14+
- Python 3.8+
- npm 或 yarn
- 有效的 OpenAI API 金鑰 (建議使用 v1.x+ 版本以獲得最新客戶端庫功能的完全兼容性)

### 完整安裝步驟

1. 克隆倉庫
   ```bash
   git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   cd Multi-AI-Agents-V-Meeting-Platform
   ```

2. 安裝並啟動後端
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
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

### Docker 安裝（本地）

1. 在您的機器上安裝 Docker 和 Docker Compose
   - 對於 Windows 和 macOS，安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - 對於 Linux，請按照 [Docker 引擎安裝指南](https://docs.docker.com/engine/install/)

2. 克隆倉庫並導航到項目目錄
   ```bash
   git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   cd Multi-AI-Agents-V-Meeting-Platform
   ```

3. 為後端創建 .env 文件並添加您的 OpenAI API 密鑰
   ```bash
   cp backend/.env.example backend/.env
   # 編輯 .env 文件並添加您的 OpenAI API 密鑰
   ```

4. 構建並啟動容器
   ```bash
   docker-compose up -d --build
   ```

5. 訪問應用
   - 前端: http://localhost:3000
   - 後端: http://localhost:8000
   - API測試頁面: http://localhost:8000/api-test

6. 完成後停止容器
   ```bash
   docker-compose down
   ```

### Google Colab 設置

1. 打開一個新的 [Google Colab 筆記本](https://colab.research.google.com/)

2. 克隆倉庫並設置後端
   ```python
   !git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   %cd Multi-AI-Agents-V-Meeting-Platform/backend
   !pip install -r requirements.txt
   
   # 創建包含 OpenAI API 密鑰的 .env 文件
   %%writefile .env
   OPENAI_API_KEY=您的API密鑰
   ```

3. 安裝並配置 ngrok 來暴露後端服務器
   ```python
   !pip install pyngrok
   !ngrok authtoken 您的NGROK令牌  # 從 https://dashboard.ngrok.com/ 獲取
   
   from pyngrok import ngrok
   # 在後台啟動後端服務器
   !nohup python run.py &
   
   # 為後端服務器創建隧道
   public_url = ngrok.connect(8000)
   print(f"後端可通過以下地址訪問: {public_url}")
   ```

4. 更新前端 API 配置以使用 ngrok URL
   ```python
   %cd ../frontend
   
   # 在 Colab 中安裝 Node.js 包（可能需要幾分鐘）
   !npm install
   
   # 在前端更新 API 端點以使用 ngrok URL
   # 這是一個簡化的例子 - 您可能需要修改特定文件
   !sed -i "s|http://localhost:8000|{public_url}|g" src/utils/api.js
   
   # 啟動前端（這將提供一個訪問鏈接）
   !npm start
   ```

5. 通過 Colab 輸出中提供的鏈接訪問應用

## 自定義與擴展

- 可以通過修改前端代碼添加新的 UI 元素或互動功能
- 通過後端代碼可以調整 AI 角色的生成邏輯和對話流程
- 如需添加或編輯 AI 角色，請使用智能體管理介面 http://localhost:3000/agents
- 您也可以導出自定義的智能體並與他人分享

## 未來規劃

- **優化會議流程**：讓會議流程合乎邏輯，確保會議結論有效益。
- **多國語言支持**：除繁體中文外，可延伸英文、日文等多種語言
- **多 LLM API支持**：除OpenAI外，可延伸支持Anthropic Claude、Google Gemini及 本地Ollama 等多種 LLM API
- **不同情境會議模板**：根據不同會議情境，如集體創作、市場分析、創意激發等，建立豬隊友智能體提示詞模板
- **數據庫整合**：從內存存儲轉向持久化存儲，支持會議記錄查詢
- **用戶認證系統**：添加登錄功能，支持多用戶環境
- **會議分析工具**：提供更深入的會議內容分析
- **介面美觀優化**：智能體頭像生成，對話視窗情緒化識別
- **社群分享功能**：會議直播功能、會議錄影下載

## 致謝

感謝 [Microsoft TinyTroupe](https://github.com/microsoft/TinyTroupe/)！本項目在概念上受到微軟 TinyTroupe 的啟發，但由於既有架構未能完全滿足我們想要實現的效果，我們毅然決定從頭開始重新構建。我們的目標是創建一個每一位智能體均由LLM驅動的虛擬會議系統，並提供視覺化的會議呈現效果，讓使用者能直觀地感受AI智能體之間的互動和對話。

## 貢獻

我們熱切歡迎各領域的專家和開發者加入本項目！無論您擅長前端開發、後端架構、UI設計、提示詞工程或是LLM應用，都能在這裡發揮您的才能。如果您有任何想法或建議，請隨時提交 Pull Request 或提出 Issue。

## 支持我們

如果您覺得這個項目有幫助，可以請我們喝杯咖啡來支持我們的開發工作！

<a href="https://buymeacoffee.com/mkhsu2002w" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

您的捐贈將用於：
- 持續開發與功能增強
- API費用支付
- 系統優化與維護
- 社群建設與支持

## 許可證: MIT License

附加條款：為了尊重本專案的原始貢獻者，我們要求所有基於本專案的改版或衍生作品，在其文件或程式碼註解中明確標記 FlyPig AI。例如：

* 本專案基於 FlyPig AI 的 TinyPigTroupe 開源專案進行修改。
* 此改版由 [您的名稱/公司名稱] 維護，基於 FlyPig AI 的貢獻。

此要求旨在確保原始貢獻得到適當的認可，並促進開源社群的良好合作。 
