from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any, Union
import os
from dotenv import load_dotenv
import logging
import asyncio
import openai
from datetime import datetime
import json
import uuid
import time
from starlette.websockets import WebSocketDisconnect
from app.config import ROLE_PROMPTS, MODERATOR_CONFIG, AI_CONFIG, PROMPT_TEMPLATES, ROUND_TOPICS, MESSAGE_TYPES, SCENARIO_INFO, DEFAULT_SCENARIO
# 引入情境模組配置
from app.config_scenarios import DISCUSSION_SCENARIOS, SCENARIO_SELECTION_GUIDE

# 載入環境變數
load_dotenv()

# 配置日誌
log_level_str = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "app/logs/app.log")

# 將字符串日誌級別轉換為對應的logging級別
log_level = getattr(logging, log_level_str.upper(), logging.INFO)

# 確保日誌目錄存在
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# 設置日誌配置
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日誌級別設置為 {log_level_str}，日誌文件路徑為 {log_file}")

# 創建FastAPI應用
app = FastAPI(
    title="FlyPig AI Conference API",
    description="飛豬隊友AI虛擬會議系統的後端API",
    version="2.1.0"  # 更新版本號
)

# 創建靜態文件目錄
os.makedirs("app/static", exist_ok=True)

# 添加靜態文件支持
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS設定
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY環境變量未設置。LLM功能將不可用。")
else:
    # 新版OpenAI API不再使用全局設置
    # 我們將在每次調用時創建客戶端並提供API密鑰
    logger.info("OpenAI API密鑰已設置")

# 創建OpenAI客戶端實例的函數
def get_openai_client():
    """
    根據 API 金鑰創建 OpenAI 客戶端
    支持新舊版本 SDK 和不同格式的 API 金鑰
    """
    global openai_api_key
    
    if not openai_api_key:
        logger.warning("未設置 OpenAI API 金鑰，無法創建客戶端")
        return None
    
    # 掩蔽 API 金鑰用於日誌
    masked_key = (openai_api_key[:5] + "..." + openai_api_key[-5:]) if len(openai_api_key) > 10 else "***"
    logger.info(f"正在使用 API 金鑰創建客戶端 (已遮蔽: {masked_key})")
    
    try:
        # 首先檢查OpenAI版本
        openai_version = getattr(openai, "__version__", "未知")
        logger.info(f"OpenAI庫版本: {openai_version}")
        
        # 首先嘗試使用現代的 OpenAI 客戶端
        try:
            logger.info("嘗試創建現代 OpenAI 客戶端")
            client = openai.OpenAI(api_key=openai_api_key)
            
            # 驗證客戶端可用性
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                logger.info("成功創建現代 OpenAI 客戶端")
                return client
            else:
                logger.warning("現代客戶端創建成功但結構不符合預期")
        except (TypeError, ValueError, ImportError, AttributeError) as e:
            logger.warning(f"使用現代客戶端失敗: {str(e)}，嘗試傳統方式")
            
        # 如果現代客戶端失敗，嘗試使用傳統全局配置
        try:
            # 為傳統方法設置 API 金鑰
            logger.info("嘗試設置全局 API 金鑰")
            openai.api_key = openai_api_key
            
            # 檢查是否支持舊式 API
            if hasattr(openai, 'ChatCompletion'):
                # 測試客戶端有效性
                logger.info("使用傳統 OpenAI 客戶端 (全局配置)")
                return openai
            else:
                logger.warning("傳統 API 端點不可用，無法創建客戶端")
                return None
                
        except Exception as legacy_err:
            logger.error(f"傳統方式配置失敗: {str(legacy_err)}")
            return None
            
    except Exception as e:
        logger.error(f"創建 OpenAI 客戶端時發生未預期的錯誤: {str(e)}")
        logger.exception("OpenAI客戶端創建過程中發生異常")
        return None

# 數據模型
class Participant(BaseModel):
    id: str
    name: str
    title: str
    personality: str = ""  # 設為可選，默認為空字符串
    expertise: str = ""    # 設為可選，默認為空字符串
    isActive: bool = True
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0) # 新增：溫度，給定合理範圍
    rolePrompt: Optional[str] = None # 新增：角色提示詞
    
    class Config:
        # 允許額外的字段
        extra = "ignore"
    
class ConferenceConfig(BaseModel):
    topic: str
    participants: List[Participant]
    rounds: int = Field(ge=1, le=20, default=3)
    language: str = "繁體中文"
    conclusion: bool = True
    scenario: Optional[str] = DEFAULT_SCENARIO  # 新增：研討情境類型，預設為商務會議
    additional_notes: Optional[str] = ""  # 新增：附註補充資料
    
    class Config:
        # 允許額外的字段
        extra = "ignore"

class Message(BaseModel):
    id: str
    speakerId: str
    speakerName: str
    speakerTitle: str
    text: str
    timestamp: str

# 內存存儲（在實際生產環境中應使用數據庫）
active_conferences = {}
connected_clients = {}

# API路由
@app.get("/")
def read_root():
    return {"message": "歡迎使用飛豬隊友AI虛擬會議系統API"}

@app.get("/api-test", response_class=HTMLResponse)
async def api_test_page():
    """OpenAI API 測試頁面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenAI API 連接測試</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .container {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .api-status {
                margin: 20px 0;
                padding: 15px;
                border-radius: 5px;
            }
            .success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .warning {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
            }
            input, textarea {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            button:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
            }
            .response {
                margin-top: 20px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
                white-space: pre-wrap;
                max-height: 300px;
                overflow-y: auto;
            }
            .loading {
                text-align: center;
                margin: 10px 0;
                display: none;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 2s linear infinite;
                display: inline-block;
                margin-right: 10px;
                vertical-align: middle;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <h1>OpenAI API 連接測試</h1>
        
        <div class="container">
            <h2>API 狀態</h2>
            <div id="apiStatus" class="api-status warning">
                檢查中...
            </div>
            
            <h2>API 金鑰設定</h2>
            <div>
                <label for="apiKey">OpenAI API 金鑰</label>
                <input type="text" id="apiKey" placeholder="輸入你的 API Key (只會暫時使用，不會儲存)" />
                <button id="updateApiKey">更新 API 金鑰</button>
            </div>
            
            <h2>即時對話測試</h2>
            <div>
                <label for="message">輸入訊息</label>
                <textarea id="message" rows="4" placeholder="輸入想問 AI 的內容..."></textarea>
                <button id="sendMessage">發送訊息</button>
                
                <div class="loading" id="loading">
                    <span class="spinner"></span> 正在處理請求...
                </div>
                
                <h3>回應</h3>
                <div class="response" id="response">
                    尚未有對話...
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // 初始檢查 API 狀態
                checkApiStatus();
                
                // 綁定按鈕事件
                document.getElementById('updateApiKey').addEventListener('click', updateApiKey);
                document.getElementById('sendMessage').addEventListener('click', sendMessage);
            });
            
            // 檢查 API 狀態
            async function checkApiStatus() {
                const statusElement = document.getElementById('apiStatus');
                try {
                    const response = await fetch('/api/test');
                    const data = await response.json();
                    
                    if (data.openai && data.openai.connected) {
                        statusElement.className = 'api-status success';
                        statusElement.innerHTML = `<strong>成功!</strong> API 連接正常。<br>回應: ${data.openai.response || ''}`;
                    } else {
                        statusElement.className = 'api-status error';
                        statusElement.innerHTML = `<strong>錯誤!</strong> API 連接失敗。<br>原因: ${data.openai?.reason || '未知錯誤'}`;
                    }
                } catch (error) {
                    statusElement.className = 'api-status error';
                    statusElement.innerHTML = `<strong>錯誤!</strong> 無法檢查 API 狀態。<br>錯誤信息: ${error.message}`;
                }
            }
            
            // 更新 API 金鑰
            async function updateApiKey() {
                const apiKey = document.getElementById('apiKey').value.trim();
                if (!apiKey) {
                    alert('請輸入有效的 API 金鑰');
                    return;
                }
                
                const statusElement = document.getElementById('apiStatus');
                statusElement.className = 'api-status warning';
                statusElement.textContent = '正在更新 API 金鑰...';
                
                try {
                    const response = await fetch('/api/update-api-key', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ api_key: apiKey }),
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        statusElement.className = 'api-status success';
                        statusElement.textContent = '成功! API 金鑰已更新。正在重新檢查連接...';
                        setTimeout(checkApiStatus, 1000);
                    } else {
                        statusElement.className = 'api-status error';
                        statusElement.textContent = `錯誤! 無法更新 API 金鑰。原因: ${data.error || '未知錯誤'}`;
                    }
                } catch (error) {
                    statusElement.className = 'api-status error';
                    statusElement.textContent = `錯誤! 無法更新 API 金鑰。錯誤信息: ${error.message}`;
                }
            }
            
            // 發送測試訊息
            async function sendMessage() {
                const message = document.getElementById('message').value.trim();
                if (!message) {
                    alert('請輸入訊息');
                    return;
                }
                
                const loadingElement = document.getElementById('loading');
                const responseElement = document.getElementById('response');
                const sendButton = document.getElementById('sendMessage');
                
                loadingElement.style.display = 'block';
                sendButton.disabled = true;
                
                try {
                    const response = await fetch('/api/test/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message, topic: '測試對話' }),
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        responseElement.textContent = data.message || '無回應內容';
                    } else {
                        responseElement.textContent = `錯誤! ${data.error || '未知錯誤'}`;
                    }
                } catch (error) {
                    responseElement.textContent = `錯誤! 無法發送訊息。錯誤信息: ${error.message}`;
                } finally {
                    loadingElement.style.display = 'none';
                    sendButton.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/test")
async def test_api():
    """測試 API 連接和 OpenAI 配置狀態"""
    try:
        # 準備回應資料
        response_data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "api_key_set": bool(openai_api_key),
            "openai": {
                "connected": False,
                "reason": "尚未測試"
            }
        }
        
        # 如果 API 金鑰設置，檢查格式
        if openai_api_key:
            is_new_format = openai_api_key.startswith("sk-proj-")
            masked_key = openai_api_key[:5] + "..." + openai_api_key[-5:] if len(openai_api_key) > 10 else "***"
            response_data["api_key"] = {
                "format": "新格式 (sk-proj-*)" if is_new_format else "標準格式 (sk-*)",
                "masked": masked_key
            }
            logger.info(f"API 測試 - 使用 {response_data['api_key']['format']} 的 API 金鑰")
        
        # 獲取 OpenAI 庫版本
        try:
            response_data["openai_version"] = openai.__version__
        except (AttributeError, ImportError):
            response_data["openai_version"] = "未知"
        
        # 測試 OpenAI 連接
        client = get_openai_client()
        if client:
            try:
                # 簡單測試調用
                logger.info("執行 OpenAI API 連接測試")
                
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions') and callable(getattr(client.chat.completions, 'create', None)):
                    # 使用新版 API
                    logger.info("使用新版 API 格式進行測試調用")
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "簡短的測試回應"}],
                        max_tokens=5
                    )
                    resp_text = response.choices[0].message.content.strip()
                    response_data["openai"]["api_type"] = "新版 OpenAI 客戶端"
                else:
                    # 使用舊版 API
                    logger.info("使用舊版 API 格式進行測試調用")
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "簡短的測試回應"}],
                        max_tokens=5
                    )
                    if hasattr(response.choices[0], 'message'):
                        resp_text = response.choices[0].message.content.strip()
                    else:
                        resp_text = response.choices[0]['message']['content'].strip()
                    response_data["openai"]["api_type"] = "傳統 OpenAI API"
                
                response_data["openai"] = {
                    "connected": True,
                    "response": resp_text,
                    "model": "gpt-3.5-turbo",
                    "api_type": response_data["openai"].get("api_type", "未知"),
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"OpenAI API 測試成功: {resp_text}")
                
            except Exception as api_err:
                logger.error(f"OpenAI API 調用測試失敗: {str(api_err)}")
                
                # 獲取詳細錯誤信息
                error_details = {}
                try:
                    if hasattr(api_err, 'json'):
                        error_details = api_err.json()
                    elif hasattr(api_err, 'response') and hasattr(api_err.response, 'json'):
                        error_details = api_err.response.json()
                except:
                    pass
                
                response_data["openai"] = {
                    "connected": False, 
                    "reason": str(api_err)[:200],
                    "error_type": type(api_err).__name__,
                    "details": error_details,
                    "timestamp": datetime.now().isoformat()
                }
        else:
            logger.warning("API 金鑰未設置或客戶端創建失敗")
            response_data["openai"] = {
                "connected": False, 
                "reason": "API 金鑰未設置或客戶端創建失敗",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"OpenAI API 測試失敗: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "api_key_set": bool(openai_api_key),
            "error": str(e)[:200],
            "error_type": type(e).__name__
        }
    
    return response_data

# 測試消息請求數據模型
class TestMessageRequest(BaseModel):
    message: str
    topic: str = "測試主題"

class ApiKeyUpdateRequest(BaseModel):
    api_key: str

@app.post("/api/update-api-key")
async def update_api_key(request: ApiKeyUpdateRequest):
    """臨時更新 OpenAI API 金鑰（僅用於當前會話）"""
    try:
        # 記錄請求（不記錄完整 API Key）
        masked_key = request.api_key[:5] + "..." + request.api_key[-5:] if len(request.api_key) > 10 else "***"
        logger.info(f"收到更新 API 金鑰請求 (已遮蔽: {masked_key})")
        
        # 檢查金鑰格式
        is_new_format = request.api_key.startswith("sk-proj-")
        logger.info(f"API 金鑰格式檢查: {'新格式 (sk-proj-*)' if is_new_format else '標準格式 (sk-*)'}")
        
        # 更新全局變量中的 API Key
        global openai_api_key
        old_key = openai_api_key
        openai_api_key = request.api_key
        
        # 嘗試創建 OpenAI 客戶端以測試金鑰
        client = get_openai_client()
        if not client:
            # 如果創建失敗，恢復舊金鑰
            logger.error("無法使用新 API 金鑰創建客戶端，恢復原金鑰")
            openai_api_key = old_key
            return {
                "success": False,
                "error": "無法使用提供的 API 金鑰創建 OpenAI 客戶端",
                "details": "客戶端創建失敗",
                "api_format": "新格式 (sk-proj-*)" if is_new_format else "標準格式 (sk-*)"
            }
            
        # 嘗試簡單調用以確認金鑰有效
        logger.info("測試新 API 金鑰與 OpenAI 服務的連線")
        try:
            # 檢查客戶端類型並使用適當的 API 調用
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions') and callable(getattr(client.chat.completions, 'create', None)):
                # 使用新版 API
                logger.info("使用新版 API 格式進行測試調用")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "API 金鑰測試"}],
                    max_tokens=5
                )
                resp_text = response.choices[0].message.content.strip()
            else:
                # 使用舊版 API
                logger.info("使用舊版 API 格式進行測試調用")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "API 金鑰測試"}],
                    max_tokens=5
                )
                if hasattr(response.choices[0], 'message'):
                    resp_text = response.choices[0].message.content.strip()
                else:
                    resp_text = response.choices[0]['message']['content'].strip()
            
            logger.info(f"API 金鑰測試成功，回應: {resp_text}")
            return {
                "success": True,
                "message": "API 金鑰已更新並通過測試",
                "response": resp_text,
                "api_format": "新格式 (sk-proj-*)" if is_new_format else "標準格式 (sk-*)",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as api_err:
            # 如果 API 調用失敗，嘗試獲取詳細錯誤信息
            error_details = {}
            try:
                if hasattr(api_err, 'json'):
                    error_details = api_err.json()
                elif hasattr(api_err, 'response') and hasattr(api_err.response, 'json'):
                    error_details = api_err.response.json()
            except:
                error_details = {"error": str(api_err)[:200]}
            
            # 恢復舊金鑰
            logger.error(f"API 金鑰測試失敗: {str(api_err)}")
            openai_api_key = old_key
            
            return {
                "success": False,
                "error": f"API 金鑰無效或不兼容: {str(api_err)[:200]}",
                "error_type": type(api_err).__name__,
                "details": error_details,
                "api_format": "新格式 (sk-proj-*)" if is_new_format else "標準格式 (sk-*)",
                "timestamp": datetime.now().isoformat()
            }
                
    except Exception as e:
        logger.error(f"更新 API 金鑰時出錯: {str(e)}")
        return {
            "success": False,
            "error": f"更新 API 金鑰處理失敗: {str(e)[:200]}",
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/test/message")
async def test_message(request: TestMessageRequest):
    """處理測試頁面發送的消息請求"""
    try:
        # 記錄請求
        logger.info(f"收到測試消息請求: {request.json()}")
        
        # 獲取OpenAI客戶端
        client = get_openai_client()
        if not client:
            logger.warning("未設置OpenAI API密鑰或客戶端創建失敗，無法處理請求")
            return {
                "success": False,
                "message": "未配置OpenAI API或客戶端創建失敗，無法處理請求",
                "timestamp": datetime.now().isoformat()
            }
        
        # 構建提示詞
        system_message = f"你是會議助手，正在參與一個關於「{request.topic}」的討論。請用繁體中文回應，風格專業但友善。"
        user_message = request.message
        
        logger.info(f"準備發送到OpenAI的提示詞: {system_message}")
        logger.info(f"使用者訊息: {user_message}")
        
        # 檢查API金鑰格式
        is_new_format = openai_api_key.startswith("sk-proj-") if openai_api_key else False
        logger.info(f"使用的 API 金鑰格式: {'sk-proj-* (新格式)' if is_new_format else '標準格式'}")
        
        # 調用OpenAI API
        try:
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions') and callable(getattr(client.chat.completions, 'create', None)):
                # 嘗試新版 API
                logger.info("使用新版 API 格式發送請求")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                ai_response = response.choices[0].message.content.strip()
            else:
                # 嘗試舊版 API
                logger.info("使用舊版 API 格式發送請求")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                if hasattr(response.choices[0], 'message'):
                    ai_response = response.choices[0].message.content.strip()
                else:
                    ai_response = response.choices[0]['message']['content'].strip()
            
            logger.info(f"OpenAI API 回應: {ai_response}")
            
            return {
                "success": True,
                "message": ai_response,
                "timestamp": datetime.now().isoformat(),
                "topic": request.topic
            }
            
        except Exception as api_err:
            logger.error(f"OpenAI API 調用失敗: {str(api_err)}")
            
            # 獲取更詳細的錯誤信息
            error_details = {}
            try:
                if hasattr(api_err, 'json'):
                    error_details = api_err.json()
                elif hasattr(api_err, 'response') and hasattr(api_err.response, 'json'):
                    error_details = api_err.response.json()
            except:
                pass
            
            return {
                "success": False,
                "error": f"OpenAI API 調用失敗: {str(api_err)[:200]}",
                "error_type": type(api_err).__name__,
                "details": error_details,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"處理測試消息請求失敗: {str(e)}")
        return {
            "success": False,
            "error": f"處理請求失敗: {str(e)[:200]}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/scenarios")
def get_scenarios():
    """獲取可用的研討情境模組列表"""
    return {
        "scenarios": SCENARIO_INFO,
        "default": DEFAULT_SCENARIO,
        "selection_guide": SCENARIO_SELECTION_GUIDE
    }

@app.post("/api/conference/start")
async def start_conference(config: ConferenceConfig, background_tasks: BackgroundTasks):
    """開始一個新的會議"""
    conference_id = str(uuid.uuid4())
    
    # 驗證情境模組
    if config.scenario and config.scenario not in DISCUSSION_SCENARIOS:
        # 如果指定的情境不存在，使用預設情境
        logger.warning(f"指定的情境模組 '{config.scenario}' 不存在，使用預設情境 '{DEFAULT_SCENARIO}'")
        config.scenario = DEFAULT_SCENARIO
    
    # 初始化會議狀態
    active_conferences[conference_id] = {
        "id": conference_id,
        "topic": config.topic,
        "participants": {p.id: p.dict() for p in config.participants},
        "messages": [],
        "stage": "waiting",  # 初始階段：等待
        "rounds": config.rounds,
        "current_round": 0,
        "language": config.language,
        "conclusion": config.conclusion,
        "scenario": config.scenario,  # 新增：記錄使用的情境模組
        "additional_notes": config.additional_notes,  # 新增：附註補充資料
        "start_time": datetime.now().isoformat(),
        "connected_clients": [],  # 修改為列表而非字典
        "config": {  # 存儲完整配置
            "topic": config.topic,
            "participants": [p.dict() for p in config.participants],
            "rounds": config.rounds,
            "language": config.language,
            "conclusion": config.conclusion,
            "scenario": config.scenario,
            "additional_notes": config.additional_notes  # 新增：附註補充資料
        }
    }
    
    # 添加主持人（秘書）
    active_conferences[conference_id]["participants"][MODERATOR_CONFIG["id"]] = MODERATOR_CONFIG
    
    # 創建WebSocket連接管理器
    connected_clients[conference_id] = []
    
    # 在背景任務中啟動會議
    background_tasks.add_task(run_conference, conference_id)
    
    # 返回結果，增加success字段以兼容前端
    return {"conference_id": conference_id, "status": "created", "success": True}

@app.get("/api/conference/{conference_id}")
def get_conference(conference_id: str):
    if conference_id not in active_conferences:
        raise HTTPException(status_code=404, detail="找不到指定的會議")
    
    return active_conferences[conference_id]

@app.get("/api/conference/{conference_id}/messages")
def get_conference_messages(conference_id: str, limit: int = 50, offset: int = 0):
    if conference_id not in active_conferences:
        raise HTTPException(status_code=404, detail="找不到指定的會議")
    
    messages = active_conferences[conference_id]["messages"]
    return {
        "total": len(messages),
        "messages": messages[offset:offset+limit]
    }

# 會議執行邏輯
async def run_conference(conference_id: str):
    """執行會議的主要邏輯"""
    try:
        logger.info(f"開始執行會議 {conference_id} 的主要邏輯")
        
        if conference_id not in active_conferences:
            logger.error(f"無法執行不存在的會議: {conference_id}")
            return
            
        conf = active_conferences[conference_id]
        config = conf["config"]
        
        # 更新狀態為介紹階段
        await update_conference_stage(conference_id, "introduction")
        
        # 生成並發送自我介紹
        try:
            await generate_introductions(conference_id)
        except Exception as e:
            logger.error(f"生成自我介紹時出錯: {str(e)}")
            logger.exception("生成自我介紹過程中發生異常")
        
        # 進入討論階段
        await update_conference_stage(conference_id, "discussion")
        
        # 進行多輪討論
        for round_num in range(1, config["rounds"] + 1):
            try:
                await run_discussion_round(conference_id, round_num)
            except Exception as e:
                logger.error(f"執行第{round_num}輪討論時出錯: {str(e)}")
                logger.exception(f"執行第{round_num}輪討論過程中發生異常")
        
        # 生成結論
        await update_conference_stage(conference_id, "conclusion")
        try:
            await generate_conclusion(conference_id)
        except Exception as e:
            logger.error(f"生成會議結論時出錯: {str(e)}")
            logger.exception("生成會議結論過程中發生異常")
        
        # 標記會議結束
        await update_conference_stage(conference_id, "ended")
        
        logger.info(f"會議 {conference_id} 已成功完成")
    except Exception as e:
        logger.error(f"執行會議 {conference_id} 過程中發生錯誤: {str(e)}")
        logger.exception(f"執行會議過程中發生未捕獲的異常")
        
        # 嘗試將會議標記為錯誤狀態
        try:
            if conference_id in active_conferences:
                active_conferences[conference_id]["stage"] = "error"
                await broadcast_message(conference_id, {
                    "type": MESSAGE_TYPES["error"],
                    "message": "會議執行過程中發生錯誤，請重新創建會議。"
                })
        except:
            pass

async def update_conference_stage(conference_id: str, stage: str):
    """更新會議階段並通知客戶端"""
    conf = active_conferences[conference_id]
    conf["stage"] = stage
    
    # 通過WebSocket通知客戶端
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["stage_change"],
        "stage": stage
    })
    logger.info(f"Conference {conference_id} stage changed to {stage}")

async def update_current_round(conference_id: str, round_num: int):
    """更新當前回合並通知客戶端"""
    conf = active_conferences[conference_id]
    conf["current_round"] = round_num
    
    # 通過WebSocket通知客戶端
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["round_update"],
        "round": round_num
    })

# MVP階段使用模擬的回應，實際環境中使用OpenAI API
async def generate_ai_response(prompt: str, participant_id: str, conference_id: str = None, temperature: Optional[float] = None) -> str:
    """生成AI回應"""
    try:
        client = get_openai_client()
        if not client:
            logger.error("未能獲取OpenAI客戶端，無法生成回應")
            return "很抱歉，AI服務當前不可用。請檢查API金鑰設置。"
        
        # 獲取會議和參與者數據
        participant_data = None
        scenario_prompt = ""
        final_temperature = AI_CONFIG["default_temperature"] # 從通用配置獲取預設溫度
        role_prompt = ROLE_PROMPTS.get(participant_id, "") # 預設從 config.py 獲取

        if conference_id and conference_id in active_conferences:
            conference = active_conferences[conference_id]
            # 從會議儲存的參與者字典中獲取數據
            participant_data = conference.get("participants", {}).get(participant_id)

            if participant_data:
                 # 優先使用參與者自訂的 Role Prompt (如果存在且非空)
                custom_role_prompt = participant_data.get("rolePrompt")
                if custom_role_prompt and custom_role_prompt.strip():
                    role_prompt = custom_role_prompt
                    logger.debug(f"使用參與者 {participant_id} 的自訂 Role Prompt")
                else:
                     logger.debug(f"參與者 {participant_id} 未提供自訂 Role Prompt，使用預設")

                # 獲取情境相關系統提示詞
                scenario_id = conference.get("scenario")
                if scenario_id and scenario_id in DISCUSSION_SCENARIOS:
                    scenario_prompt = DISCUSSION_SCENARIOS[scenario_id].get("system_prompt", "")

                # 確定溫度：優先使用函數參數，其次是參與者數據，最後是全局預設
                if temperature is not None:
                     final_temperature = temperature
                     logger.debug(f"使用函數傳入的溫度: {final_temperature} for {participant_id}")
                elif participant_data.get("temperature") is not None:
                    final_temperature = participant_data["temperature"]
                    logger.debug(f"使用參與者 {participant_id} 的自訂溫度: {final_temperature}")
                else:
                    logger.debug(f"參與者 {participant_id} 未提供溫度，使用預設: {final_temperature}")
            else:
                 logger.warning(f"無法在會議 {conference_id} 中找到參與者 {participant_id} 的詳細數據")

        else:
             # 如果沒有會議上下文，則使用全局預設溫度
             logger.debug(f"無會議上下文，為 {participant_id} 使用預設溫度: {final_temperature}")
             # 如果函數直接傳入了溫度，則使用它
             if temperature is not None:
                 final_temperature = temperature


        # 組合系統提示詞
        system_message = AI_CONFIG["system_message_template"].format(
            participant_id=participant_id,
            role_prompt=role_prompt # 使用已確定的 role_prompt
        )

        # 如果有情境系統提示詞，附加到系統消息中
        if scenario_prompt:
            system_message += f"\n\n{scenario_prompt}"

        # 準備消息
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        logger.info(f"嘗試生成AI回應，參與者ID: {participant_id}, 最終溫度: {final_temperature}") # 使用 final_temperature

        # 檢查客戶端類型
        if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
            # 使用現代OpenAI客戶端
            logger.info("使用現代OpenAI客戶端API調用")
            try:
                response = client.chat.completions.create(
                    model=AI_CONFIG["default_model"],
                    messages=messages,
                    temperature=final_temperature, # 使用 final_temperature
                    max_tokens=AI_CONFIG["max_tokens"]
                )
                return response.choices[0].message.content.strip()
            except AttributeError as ae:
                logger.error(f"現代客戶端API屬性錯誤: {str(ae)}")
                # 嘗試備用方法
                if hasattr(client.chat.completions, 'create'):
                    response = client.chat.completions.create(
                        model=AI_CONFIG["default_model"],
                        messages=messages,
                        temperature=final_temperature, # 使用 final_temperature
                        max_tokens=AI_CONFIG["max_tokens"]
                    )
                    return response.choices[0].message.content.strip()
                raise

        # 使用傳統OpenAI客戶端
        elif hasattr(client, 'ChatCompletion'):
            logger.info("使用傳統OpenAI客戶端API調用")
            response = client.ChatCompletion.create(
                model=AI_CONFIG["default_model"],
                messages=messages,
                temperature=final_temperature, # 使用 final_temperature
                max_tokens=AI_CONFIG["max_tokens"]
            )
            return response['choices'][0]['message']['content'].strip()

        else:
            logger.error(f"無法識別的OpenAI客戶端類型: {type(client).__name__}")
            return "很抱歉，AI服務當前遇到技術問題。無法識別API客戶端類型。"

    except Exception as e:
        logger.error(f"生成AI回應時發生錯誤: {str(e)}")
        logger.exception("AI回應生成過程中發生異常")
        return f"很抱歉，AI生成過程中發生錯誤。錯誤詳情: {str(e)[:100]}"

# =============================================
# 新增：檢查暫停狀態的輔助函數
# =============================================
async def check_pause(conference_id: str):
    """檢查會議是否暫停，如果暫停則異步等待"""
    while conference_id in active_conferences and active_conferences[conference_id].get("stage") == "paused":
        logger.debug(f"會議 {conference_id} 已暫停，等待恢復...")
        await asyncio.sleep(1) # 每秒檢查一次

async def generate_introductions(conference_id: str):
    """生成所有參與者的自我介紹"""
    await check_pause(conference_id) # <--- 在函數開頭檢查
    conf = active_conferences[conference_id]
    config = conf["config"]
    topic = config["topic"]
    
    # 豬秘書(作為主持人)介紹會議
    additional_notes = conf.get("additional_notes", "")
    intro_message = f"大家好，我是{MODERATOR_CONFIG['name']}，擔任今天會議的秘書。歡迎參加主題為「{topic}」的會議。"
    
    # 如果有附註資料，加入開場白
    if additional_notes and additional_notes.strip():
        intro_message += f"\n\n會議補充資料：{additional_notes}\n\n"
    
    intro_message += "現在我們將進行自我介紹，請各位簡單介紹自己並談談對今天主題的看法。自我介紹完成後，我們將由主席引導進入正式討論階段。"
    
    await check_pause(conference_id) # <--- 添加消息前檢查
    await add_message(
        conference_id,
        MODERATOR_CONFIG["id"],
        intro_message
    )
    
    # 等待1秒使界面顯示更自然
    await asyncio.sleep(1)
    
    # 參與者依次進行自我介紹
    for participant in config["participants"]:
        await check_pause(conference_id) # <--- 每個參與者循環開始時檢查
        if not participant["isActive"]:
            continue
        
        # 跳過主持人(豬秘書)，因為已經在開場白中介紹過自己
        if participant["id"] == MODERATOR_CONFIG["id"]:
            continue
            
        # 構建一般參與者的提示
        intro_prompt = PROMPT_TEMPLATES["introduction"].format(
            name=participant['name'],
            title=participant['title'],
            topic=topic
        )
        
        # 如果有附註資料，加入提示詞
        # additional_notes = conf.get("additional_notes", "") # 已在函數開頭獲取
        if additional_notes and additional_notes.strip():
            intro_prompt += f"\n\n補充資料：{additional_notes}"
        
        # 生成回應
        response = await generate_ai_response(intro_prompt, participant["id"], conference_id)
        
        await check_pause(conference_id) # <--- 添加消息前檢查
        # 添加消息並廣播
        await add_message(conference_id, participant["id"], response)
        
        # 模擬打字延遲
        await asyncio.sleep(3)
    
    # 注意：此處不再添加主持人的結束語，將直接由主席在第一輪討論中開場

async def run_discussion_round(conference_id: str, round_num: int):
    """執行一輪討論"""
    await check_pause(conference_id) # <--- 在函數開頭檢查
    if conference_id not in active_conferences:
        logger.error(f"找不到會議 {conference_id}")
        return
    
    conference = active_conferences[conference_id]
    main_topic = conference["topic"]
    
    # 更新當前輪次
    await update_current_round(conference_id, round_num)
    
    # 獲取輪次主題
    round_topic = get_round_topic(round_num, main_topic, conference_id)
    
    # 主席（秘書）開場
    chair_id = MODERATOR_CONFIG["id"]
    chair_name = MODERATOR_CONFIG["name"]
    chair_title = MODERATOR_CONFIG["title"]
    
    # 主席開場白提示詞
    chair_prompt = PROMPT_TEMPLATES["chair_opening"].format(
        name=chair_name,
        title=chair_title,
        round_num=round_num,
        topic=main_topic,
        round_topic=round_topic
    )
    
    # 如果有附註資料，加入提示詞
    additional_notes = conference.get("additional_notes", "")
    if additional_notes and additional_notes.strip():
        chair_prompt += f"\n\n補充資料：{additional_notes}"
    
    await check_pause(conference_id) # <--- 生成回應前檢查
    # 生成主席開場白
    chair_text = await generate_ai_response(chair_prompt, chair_id, conference_id)
    await check_pause(conference_id) # <--- 添加消息前檢查
    await add_message(conference_id, chair_id, chair_text)
    
    # 等待一下，讓客戶端有時間處理主席的消息
    await asyncio.sleep(2)
    
    # 獲取參與者列表（排除主席秘書）
    participants = [p for p_id, p in conference["participants"].items() if p_id != chair_id and p.get("isActive", True)]
    
    # 獲取上一輪最後發言的參與者ID
    last_speakers = []
    if round_num > 1:
        # 檢查上一輪的最後幾個發言者
        messages = conference.get("messages", [])
        if messages:
            # 從後往前找最多3個不同的發言者
            speaker_count = 0
            for msg in reversed(messages):
                speaker_id = msg.get("speakerId")
                if speaker_id != chair_id and speaker_id not in last_speakers:
                    last_speakers.append(speaker_id)
                    speaker_count += 1
                    if speaker_count >= 3:
                        break
    
    logger.info(f"上一輪最後發言者: {last_speakers}")
    
    # 如果使用情境模組，應用角色權重
    weights = {}
    scenario_id = conference.get("scenario")
    if scenario_id and scenario_id in DISCUSSION_SCENARIOS:
        role_emphasis = DISCUSSION_SCENARIOS[scenario_id].get("role_emphasis", {})
        for p in participants:
            p_id = p["id"]
            # 如果角色在權重表中，使用定義的權重；否則使用預設權重1.0
            base_weight = role_emphasis.get(p_id, 1.0)
            
            # 如果是上一輪最後發言的參與者，降低權重
            if p_id in last_speakers:
                # 上一輪最後發言者的權重降低，越近發言的權重越低
                position = last_speakers.index(p_id)
                penalty = 0.5 - (position * 0.1)  # 最後發言者降低50%，倒數第二降低40%，倒數第三降低30%
                weights[p_id] = base_weight * (1 - penalty)
                logger.info(f"參與者 {p_id} 是上一輪發言者，權重從 {base_weight} 降低至 {weights[p_id]}")
            else:
                weights[p_id] = base_weight
    
    # 根據權重排序參與者（權重高的更有可能先發言）
    # 如果沒有權重，則使用原始順序
    if weights:
        # 對權重進行輕微隨機化，避免完全固定的發言順序
        import random
        for p_id in weights:
            weights[p_id] *= random.uniform(0.9, 1.1)
        
        participants.sort(key=lambda p: weights.get(p["id"], 1.0), reverse=True)
    else:
        # 沒有權重時，將上一輪最後發言的參與者排到後面
        if last_speakers:
            def get_participant_order(p):
                if p["id"] in last_speakers:
                    return last_speakers.index(p["id"]) - len(last_speakers)  # 負值，越靠後的發言者順序越小
                return 0  # 非上一輪發言者
            
            participants.sort(key=get_participant_order, reverse=True)
    
    # 記錄本輪發言順序
    speaker_order = [p["id"] for p in participants]
    logger.info(f"輪次 {round_num} 發言順序: {speaker_order}")
    
    # 獲取之前的對話上下文（最後N條消息）
    context_messages = conference["messages"][-10:]  # 取最後10條消息作為上下文
    context = "\n".join([f"{msg['speakerName']}：{msg['text']}" for msg in context_messages])
    
    # 每位參與者依次發言
    for participant in participants:
        await check_pause(conference_id) # <--- 每個參與者循環開始時檢查
        p_id = participant["id"]
        p_name = participant["name"]
        p_title = participant["title"]
        
        # 討論提示詞
        # additional_notes = conference.get("additional_notes", "") # 已在函數開頭獲取
        discussion_prompt = PROMPT_TEMPLATES["discussion"].format(
            name=p_name,
            title=p_title,
            topic=main_topic,
            round_topic=round_topic,
            context=context
        )
        
        # 如果有附註資料，加入提示詞
        if additional_notes and additional_notes.strip():
            discussion_prompt += f"\n\n補充資料：{additional_notes}"
        
        await check_pause(conference_id) # <--- 生成回應前檢查
        # 生成參與者發言
        response_text = await generate_ai_response(discussion_prompt, p_id, conference_id)
        await check_pause(conference_id) # <--- 添加消息前檢查
        await add_message(conference_id, p_id, response_text)
        
        # 更新上下文
        context_messages = conference["messages"][-10:]
        context = "\n".join([f"{msg['speakerName']}：{msg['text']}" for msg in context_messages])
        
        # 間隔一段時間，避免消息發送過快
        await asyncio.sleep(2)

    await check_pause(conference_id) # <--- 廣播完成前檢查
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["round_completed"],
        "round": round_num
    })

async def generate_conclusion(conference_id: str):
    """生成會議結論"""
    await check_pause(conference_id) # <--- 在函數開頭檢查
    conf = active_conferences[conference_id]
    config = conf["config"]
    topic = config["topic"]
    
    # 獲取主席
    chair = None
    # 從會議配置中獲取指定的主席 ID
    designated_chair_id = conf.get("config", {}).get("chair")
    if designated_chair_id and designated_chair_id in conf.get("participants", {}):
        chair_participant_data = conf["participants"][designated_chair_id]
        if chair_participant_data.get("isActive", True):
             chair = chair_participant_data # 使用 Participant 字典

    # 如果沒有指定或指定的主席無效，則使用第一個活躍非秘書參與者作為主席
    if not chair:
        for p_id, p_data in conf.get("participants", {}).items():
             if p_id != MODERATOR_CONFIG["id"] and p_data.get("isActive", True):
                 chair = p_data
                 break

    # 主席引導結論階段的文本
    chair_intro_text = f"感謝各位的精彩討論。我們已經完成了所有討論回合，現在進入會議的總結階段。讓我們請{MODERATOR_CONFIG['name']}為我們整理今天會議的重點內容。"
    # 秘書自己引導結論階段的文本
    secretary_intro_text = f"感謝各位的精彩討論。我們已經完成了所有討論回合，現在進入會議的總結階段。作為會議秘書，我將為大家總結今天的會議要點。"

    # 添加引導消息
    intro_speaker_id = chair["id"] if chair else MODERATOR_CONFIG["id"]
    intro_text = chair_intro_text if chair else secretary_intro_text
    await check_pause(conference_id) # <--- 添加消息前檢查
    await add_message(conference_id, intro_speaker_id, intro_text)
    
    await asyncio.sleep(2)
    
    # 收集所有消息作為上下文
    all_messages = [f"{m.get('speakerName', 'Unknown')} ({m.get('speakerTitle', 'Unknown')}): {m.get('text', '')}" for m in conf.get("messages", [])]
    context = "\n".join(all_messages[-30:])  # 最後30條消息，增加上下文範圍
    
    # 獲取附註補充資料
    additional_notes = conf.get("additional_notes", "")
    
    # 構建特殊的秘書結論提示
    secretary_prompt = """
    你是{name}（{title}），負責整理會議記錄並提出總結。
    
    會議主題是「{topic}」，經過了多輪討論。
    """.format(
        name=MODERATOR_CONFIG['name'],
        title=MODERATOR_CONFIG['title'],
        topic=topic
    )
    
    # 如果有附註資料，加入提示詞
    if additional_notes and additional_notes.strip():
        secretary_prompt += f"""
    
    會議補充資料：
    {additional_notes}
    """
    
    secretary_prompt += """
    
    以下是會議中的發言摘要：
    {context}
    
    請你用繁體中文進行以下工作：
    1. 簡短回應主席（如果有的話）或直接開始，表示你將進行會議總結
    2. 總結整場會議的討論重點和主要觀點
    3. 條理清晰地列出5-7點關鍵結論或行動項目
    4. 提出1-2個後續可能需要關注的方向
    
    格式為：先有一段回應/開頭，然後是總結內容，最後是帶編號的結論列表。總字數控制在400字以內。
    """.format(context=context)
    
    conclusion_text = "".strip() # 初始化結論文本
    try:
        await check_pause(conference_id) # <--- 生成結論前檢查
        # 生成總結
        client = get_openai_client()
        
        if not client:
            # 如果API客戶端不可用，返回一個通用結論
            conclusion_text = f"謝謝{'主席' if chair else ''}。作為會議秘書，我整理了關於「{topic}」的討論要點。由於技術原因，無法生成完整的分析，但仍感謝各位的積極參與和寶貴意見。"
        else:
            try:
                # 修改API調用，不使用await (OpenAI V1.x client is synchronous)
                response = client.chat.completions.create(
                    model=AI_CONFIG["default_model"],
                    temperature=0.5,  # 使用較低的溫度確保結論更加連貫和精確
                    messages=[
                        {"role": "system", "content": f"你是會議秘書{MODERATOR_CONFIG['name']}。你的工作是整理和總結會議內容，提供清晰的結論和後續行動項目。"},
                        {"role": "user", "content": secretary_prompt}
                    ],
                    max_tokens=800
                )
                conclusion_text = response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"生成結論時發生錯誤: {str(e)}")
                conclusion_text = f"謝謝{'主席' if chair else ''}。作為會議秘書，我想總結一下今天關於「{topic}」的討論，但在生成過程中遇到了一些技術問題。根據我記錄的內容，我們討論了這個主題的多個方面，並達成了一些共識。感謝各位的參與和寶貴意見。"
        
        await check_pause(conference_id) # <--- 添加總結消息前檢查
        # 添加豬秘書的總結消息
        await add_message(
            conference_id,
            MODERATOR_CONFIG["id"],
            conclusion_text
        )
        
        await asyncio.sleep(3)
        
        await check_pause(conference_id) # <--- 會議結束語前檢查
        # 會議結束語
        chair_end_text = f"感謝{MODERATOR_CONFIG['name']}的精彩總結，也感謝各位的積極參與。今天的會議到此結束，祝大家工作順利！"
        secretary_end_text = f"以上就是今天會議的總結。感謝各位的積極參與。今天的會議到此結束，祝大家工作順利！"
        
        end_speaker_id = chair["id"] if chair else MODERATOR_CONFIG["id"]
        end_text = chair_end_text if chair else secretary_end_text
            
        await check_pause(conference_id) # <--- 添加結束消息前檢查
        await add_message(conference_id, end_speaker_id, end_text)
            
    except Exception as e:
        logger.error(f"生成結論過程中發生錯誤: {str(e)}")
        await check_pause(conference_id) # <--- 即使出錯也要檢查
        await add_message(
            conference_id,
            MODERATOR_CONFIG["id"],
            f"感謝各位的參與。由於技術原因，我無法生成完整的會議總結。今天關於「{topic}」的會議到此結束，謝謝大家！"
        )

def get_round_topic(round_num: int, main_topic: str, conference_id: str = None) -> str:
    """根據輪次和主題獲取輪次子主題"""
    # 檢查是否有特定情境的輪次結構
    if conference_id and conference_id in active_conferences:
        scenario_id = active_conferences[conference_id].get("scenario")
        if scenario_id and scenario_id in DISCUSSION_SCENARIOS:
            scenario_rounds = DISCUSSION_SCENARIOS[scenario_id].get("round_structure", {})
            if round_num in scenario_rounds:
                return scenario_rounds[round_num]
    
    # 回退到預設輪次主題
    return ROUND_TOPICS.get(round_num, ROUND_TOPICS[1]).format(topic=main_topic)

# 原生WebSocket端點保持不變
@app.websocket("/ws/conference/{conference_id}")
async def websocket_endpoint(websocket: WebSocket, conference_id: str):
    try:
        await websocket.accept()
        
        client_info = f"{websocket.client.host}:{websocket.client.port}"
        logger.info(f"WebSocket連接已建立 - 客戶端: {client_info}，會議ID: {conference_id}")
        
        if conference_id not in active_conferences:
            logger.warning(f"客戶端嘗試連接不存在的會議 {conference_id}")
            await websocket.send_json({
                "type": MESSAGE_TYPES["error"],
                "message": "會議不存在"
            })
            await websocket.close()
            return
        
        if conference_id not in connected_clients:
            connected_clients[conference_id] = []
        
        connected_clients[conference_id].append(websocket)
        logger.info(f"客戶端已連接到會議 {conference_id}, 當前連接數: {len(connected_clients[conference_id])}")
        
        # 發送現有消息和狀態
        conference = active_conferences[conference_id]
        init_data = {
            "type": MESSAGE_TYPES["init"],
            "messages": conference.get("messages", []),
            "stage": conference.get("stage", "waiting"),
            "current_round": conference.get("current_round", 0),
            "conclusion": conference.get("conclusion")
        }
        logger.info(f"向客戶端發送初始化數據 - 會議ID: {conference_id}, 階段: {conference.get('stage', 'waiting')}")
        await websocket.send_json(init_data)
        
        # 如果是第一個客戶端連接，開始自我介紹
        if len(connected_clients[conference_id]) == 1 and conference["stage"] == "waiting":
            logger.info(f"首位客戶端已連接，開始會議 {conference_id} 的自我介紹階段")
            # 直接使用asyncio.create_task代替BackgroundTasks
            asyncio.create_task(process_introductions(conference_id))
        
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"收到來自客戶端的消息: {data}")
                await process_client_message(conference_id, data)
        except WebSocketDisconnect:
            logger.info(f"客戶端正常斷開連接，會議 {conference_id}，客戶端: {client_info}")
        except Exception as e:
            logger.error(f"處理WebSocket消息時出錯: {str(e)}")
        finally:
            # 確保清理資源
            if conference_id in connected_clients and websocket in connected_clients[conference_id]:
                connected_clients[conference_id].remove(websocket)
                logger.info(f"客戶端已從會議中移除，會議 {conference_id}，當前連接數: {len(connected_clients[conference_id])}")
    except Exception as e:
        logger.error(f"WebSocket連接初始化錯誤: {str(e)}")
        logger.exception("WebSocket初始化時發生異常")
        try:
            await websocket.close(code=1011, reason=f"伺服器內部錯誤: {str(e)[:50]}")
        except:
            pass

async def process_client_message(conference_id: str, data: str):
    """處理從客戶端收到的消息"""
    try:
        message = json.loads(data)
        message_type = message.get("type", "")
        logger.info(f"處理客戶端消息，類型: {message_type}")
        
        if message_type == "next_round":
            await process_next_round(conference_id)
        elif message_type == "end_conference":
            await end_conference(conference_id)
        elif message_type == "pause_conference":
            await pause_conference(conference_id)
        elif message_type == "resume_conference":
            await resume_conference(conference_id)
    except json.JSONDecodeError:
        logger.error(f"無法解析客戶端消息: {data}")
    except Exception as e:
        logger.error(f"處理客戶端消息時出錯: {str(e)}")

async def broadcast_message(conference_id: str, message: dict):
    """向會議中的所有客戶端廣播消息"""
    if conference_id not in connected_clients:
        logger.warning(f"嘗試向不存在的會議 {conference_id} 廣播消息")
        return
    
    clients_count = len(connected_clients[conference_id])
    if clients_count == 0:
        logger.warning(f"會議 {conference_id} 沒有連接的客戶端，無法廣播消息")
        return
        
    logger.info(f"正在向會議 {conference_id} 的 {clients_count} 個客戶端廣播消息，類型: {message.get('type', 'unknown')}")
    
    success_count = 0
    for client in connected_clients[conference_id]:
        try:
            await client.send_json(message)
            success_count += 1
        except Exception as e:
            logger.error(f"向客戶端廣播消息失敗: {str(e)}")
    
    logger.info(f"廣播完成 - 成功: {success_count}/{clients_count}")

async def add_message(conference_id: str, speaker_id: str, text: str):
    """添加消息並廣播給所有客戶端"""
    conference = active_conferences.get(conference_id)
    if not conference:
        logger.error(f"嘗試添加消息到不存在的會議: {conference_id}")
        return
    
    participant = None
    for p in conference["config"]["participants"]:
        if p["id"] == speaker_id:
            participant = p
            break
    
    if not participant:
        if speaker_id == "moderator":
            participant = {
                "id": MODERATOR_CONFIG["id"],
                "name": MODERATOR_CONFIG["name"],
                "title": MODERATOR_CONFIG["title"]
            }
        else:
            logger.error(f"找不到ID為 {speaker_id} 的參與者")
            return
    
    message = {
        "id": str(uuid.uuid4()),
        "speakerId": speaker_id,
        "speakerName": participant.get("name", "未知"),
        "speakerTitle": participant.get("title", "未知"),
        "text": text,
        "timestamp": datetime.now().isoformat()
    }
    
    if "messages" not in conference:
        conference["messages"] = []
    
    conference["messages"].append(message)
    
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["new_message"],
        "message": message,
        "current_speaker": speaker_id
    })
    
    # 添加短暫延遲，使對話更自然
    await asyncio.sleep(0.5)

async def process_next_round(conference_id: str):
    """進入下一輪討論"""
    conference = active_conferences.get(conference_id)
    if not conference or conference["stage"] != "discussion":
        return
    
    current_round = conference.get("current_round", 0)
    total_rounds = conference["config"].get("rounds", 3)
    
    if current_round < total_rounds:
        await update_current_round(conference_id, current_round + 1)
        await run_discussion_round(conference_id, current_round + 1)
    else:
        # 已經是最後一輪
        await process_conclusion(conference_id)

async def end_conference(conference_id: str):
    """結束會議"""
    logger.info(f"收到結束會議請求: {conference_id}")
    if conference_id not in active_conferences:
        logger.warning(f"嘗試結束不存在的會議: {conference_id}")
        return

    conference = active_conferences[conference_id]
    current_stage = conference.get("stage")
    logger.info(f"會議 {conference_id} 當前階段: {current_stage}")
    
    # 如果會議正在進行中 (非結束/錯誤/等待/暫停狀態)
    if current_stage not in ["ended", "error", "waiting"]:
        conference["stage"] = "ending" # 設置一個臨時狀態防止重入
        # 如果會議還沒自然結束（結論階段未完成），先嘗試處理結論
        if current_stage != "conclusion":
            try:
                logger.info(f"會議 {conference_id} 被手動結束，嘗試生成結論...")
                await generate_conclusion(conference_id) # 確保結論流程執行
            except Exception as e:
                 logger.error(f"手動結束會議 {conference_id} 時生成結論失敗: {str(e)}")
                 # 即使結論失敗，也要繼續結束流程
        
        # 在 generate_conclusion 後，狀態應該已變為 ended，但為確保安全，再次檢查和設置
        if active_conferences.get(conference_id, {}).get("stage") != "ended":
             logger.info(f"設置會議 {conference_id} 狀態為 ended")
             await update_conference_stage(conference_id, "ended")
        else:
             logger.info(f"會議 {conference_id} 狀態已為 ended，確保廣播")
             # 確保前端收到最終的 ended 狀態
             await broadcast_message(conference_id, {
                 "type": MESSAGE_TYPES["stage_change"],
                 "stage": "ended"
             })
    elif current_stage == "paused":
         # 如果是暫停狀態被要求結束，直接標記為 ended
         logger.info(f"會議 {conference_id} 在暫停狀態下被結束，直接設置為 ended")
         await update_conference_stage(conference_id, "ended")
    else:
         # 如果已經是 ended 或 error 或 waiting，記錄一下即可
         logger.info(f"會議 {conference_id} 狀態為 {current_stage}，無需再次結束流程，僅清理連接。")

    logger.info(f"會議 {conference_id} 已結束。")

    # 清理WebSocket連接
    if conference_id in connected_clients:
        clients_to_close = list(connected_clients[conference_id]) # 創建副本以安全迭代
        logger.info(f"正在關閉會議 {conference_id} 的 {len(clients_to_close)} 個WebSocket連接...")
        closed_count = 0
        for client in clients_to_close:
            try:
                await client.close(code=1000, reason="Conference ended") # 使用標準關閉碼
                closed_count += 1
            except Exception as e:
                logger.warning(f"關閉客戶端 {client} 連接時出錯: {str(e)}")
        
        # 清空連接列表
        if conference_id in connected_clients: # 再次檢查以防萬一
             # 等待一小段時間確保客戶端有機會收到關閉幀
            await asyncio.sleep(0.1)
            connected_clients[conference_id] = []
            logger.info(f"會議 {conference_id} 的 {closed_count}/{len(clients_to_close)} 個客戶端連接已關閉並移除。")

async def process_introductions(conference_id: str):
    """處理會議的自我介紹階段"""
    try:
        logger.info(f"開始處理會議 {conference_id} 的自我介紹階段")
        
        if conference_id not in active_conferences:
            logger.error(f"嘗試處理不存在的會議: {conference_id}")
            return
        
        conference = active_conferences[conference_id]
        
        # 檢查是否有客戶端連接
        if conference_id not in connected_clients or len(connected_clients[conference_id]) == 0:
            logger.warning(f"會議 {conference_id} 沒有客戶端連接，但嘗試進行自我介紹")
            # 我們仍然繼續處理，以便稍後客戶端連接時可以看到介紹
        
        # 更新會議階段為「介紹」
        await update_conference_stage(conference_id, "introduction")
        
        # 生成並發送自我介紹
        await generate_introductions(conference_id)
        
        # 進入討論階段
        await update_conference_stage(conference_id, "discussion")
        
        # 開始第一輪討論
        await run_discussion_round(conference_id, 1)
    except Exception as e:
        logger.error(f"處理自我介紹階段時出錯: {str(e)}")
        logger.exception("處理自我介紹階段時發生異常")
        
        # 嘗試將會議設置為錯誤狀態
        try:
            if conference_id in active_conferences:
                active_conferences[conference_id]["stage"] = "error"
                await broadcast_message(conference_id, {
                    "type": MESSAGE_TYPES["error"],
                    "message": f"處理自我介紹階段時出錯: {str(e)[:100]}"
                })
        except:
            pass

async def process_conclusion(conference_id: str):
    """處理會議的結論階段"""
    logger.info(f"開始處理會議 {conference_id} 的結論階段")
    
    if conference_id not in active_conferences:
        logger.error(f"嘗試處理不存在的會議: {conference_id}")
        return
    
    # 更新會議階段為「結論」
    await update_conference_stage(conference_id, "conclusion")
    
    # 生成會議結論
    await generate_conclusion(conference_id)
    
    # 標記會議結束
    await update_conference_stage(conference_id, "ended")
    
    logger.info(f"會議 {conference_id} 已完成")

# 添加全局異常處理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 記錄詳細的請求驗證錯誤
    error_detail = str(exc)
    logger.error(f"請求資料驗證失敗: {error_detail}")
    logger.error(f"請求路徑: {request.url.path}")
    
    try:
        body = await request.json()
        logger.error(f"請求體: {json.dumps(body, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"無法解析請求體: {str(e)}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "請求資料格式不正確，請檢查會議設定",
            "detail": [{"loc": err["loc"], "msg": err["msg"]} for err in exc.errors()]
        },
    )

# 添加暫停會議和恢復會議的功能
async def pause_conference(conference_id: str):
    """暫停會議進行"""
    if conference_id not in active_conferences:
        logger.error(f"嘗試暫停不存在的會議: {conference_id}")
        return
    
    # 更新會議狀態
    conference = active_conferences[conference_id]
    previous_stage = conference.get("stage", "waiting")
    conference["previous_stage"] = previous_stage
    conference["stage"] = "paused"
    
    # 通知所有客戶端
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["stage_change"],
        "stage": "paused",
        "previous_stage": previous_stage
    })
    
    logger.info(f"會議 {conference_id} 已暫停，之前階段: {previous_stage}")

async def resume_conference(conference_id: str):
    """恢復暫停的會議"""
    if conference_id not in active_conferences:
        logger.error(f"嘗試恢復不存在的會議: {conference_id}")
        return
    
    # 復原會議狀態
    conference = active_conferences[conference_id]
    previous_stage = conference.get("previous_stage", "discussion")
    
    # 如果沒有記錄之前的狀態，預設為討論階段
    if previous_stage == "paused" or not previous_stage:
        previous_stage = "discussion"
    
    conference["stage"] = previous_stage
    
    # 通知所有客戶端
    await broadcast_message(conference_id, {
        "type": MESSAGE_TYPES["stage_change"],
        "stage": previous_stage
    })
    
    logger.info(f"會議 {conference_id} 已恢復到階段: {previous_stage}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 