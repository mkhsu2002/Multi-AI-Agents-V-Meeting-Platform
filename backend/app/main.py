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

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="FlyPig AI Conference API",
    description="飛豬隊友AI虛擬會議系統的後端API",
    version="0.5.0"
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
        # 首先嘗試使用現代的 OpenAI 客戶端
        try:
            client = openai.OpenAI(api_key=openai_api_key)
            logger.info("成功創建現代 OpenAI 客戶端")
            return client
        except (TypeError, ValueError, ImportError) as e:
            logger.warning(f"使用現代客戶端失敗: {str(e)}，嘗試傳統方式")
            
        # 如果現代客戶端失敗，嘗試使用傳統全局配置
        try:
            # 為傳統方法設置 API 金鑰
            openai.api_key = openai_api_key
            
            # 檢查是否支持舊式 API
            if hasattr(openai, 'ChatCompletion') and callable(getattr(openai.ChatCompletion, 'create', None)):
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
        return None

# 數據模型
class Participant(BaseModel):
    id: str
    name: str
    title: str
    personality: str = ""  # 設為可選，默認為空字符串
    expertise: str = ""    # 設為可選，默認為空字符串
    isActive: bool = True
    
    class Config:
        # 允許額外的字段
        extra = "ignore"
    
class ConferenceConfig(BaseModel):
    topic: str
    participants: List[Participant]
    rounds: int = Field(ge=1, le=20, default=3)
    language: str = "繁體中文"
    conclusion: bool = True
    
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

# 角色提示詞
ROLE_PROMPTS = {
    "Pig Boss": "我是飛豬隊友 (FlyPig AI) 的領頭豬，我制定公司的宏偉藍圖，並帶領我們團隊一起翱翔。我的目標是團隊的成功，讓我們一起努力！我的命令就是方向。",
    "Brainy Pig": "我是飛豬隊友 (FlyPig AI) 行銷策略的智囊，我的豬腦袋裡充滿了各種新奇點子，旨在提升我們團隊的品牌影響力。一起集思廣益，讓我們的飛豬形象深入人心！",
    "Busy Pig": "我是飛豬隊友 (FlyPig AI) 業務拓展的先鋒，我的豬蹄將帶領我們團隊去開拓更廣闊的市場。團隊合作才能讓我們飛得更高更遠！讓我們一起努力拿下更多訂單！",
    "Professor Pig": "我是飛豬隊友 (FlyPig AI) 技術創新的領頭豬，我的豬腦袋裝滿了最新的技術知識，不斷鑽研，力求為我們的團隊開發出更領先的產品。 團隊的智慧是無窮的，一起來攻克技術難關吧！",
    "Calculator Pig": "我是飛豬隊友 (FlyPig AI) 的財政管家，我的豬算盤算得清清楚楚，確保我們團隊的每一分錢都用在刀刃上，為團隊的發展保駕護航。 團結一心，共同管理好我們的財富！",
    "Caregiver Pig": "我是飛豬隊友 (FlyPig AI) 團隊的後勤部長，關心每一位隊友的成長和福祉。營造一個充滿活力和團隊精神的工作氛圍是我的責任。 讓我們互助互愛，共同打造一個強大的飛豬團隊！",
    "Secretary Pig": "我是飛豬隊友 (FlyPig AI) 的會議記錄員，負責記錄會議的重點和決策，並整理會議總結，以便團隊成員更好地了解會議內容和行動方向。 團隊的溝通和效率，由我來記錄和整理！"
}

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
                
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
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
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
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
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
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

@app.post("/api/conference/start")
async def start_conference(config: ConferenceConfig, background_tasks: BackgroundTasks):
    try:
        # 記錄請求資料內容
        logger.info(f"接收到會議配置請求: {config.json()}")
        
        # 生成會議ID
        conference_id = str(uuid.uuid4())
        
        # 驗證配置
        active_participants = [p for p in config.participants if p.isActive]
        logger.info(f"活躍參與者數量: {len(active_participants)}")
        
        if len(active_participants) < 2:
            raise HTTPException(status_code=400, detail="至少需要2位參與者才能開始會議")
        
        if not config.topic:
            raise HTTPException(status_code=400, detail="會議主題不能為空")
        
        # 儲存會議配置
        active_conferences[conference_id] = {
            "id": conference_id,
            "config": config.dict(),
            "messages": [],
            "stage": "waiting",
            "current_round": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # 記錄儲存成功
        logger.info(f"成功創建會議 {conference_id}")
        
        # 在背景執行會議流程
        background_tasks.add_task(run_conference, conference_id)
        
        return {
            "success": True, 
            "conferenceId": conference_id,
            "message": "會議已開始初始化"
        }
    except ValidationError as ve:
        # 記錄 Pydantic 驗證錯誤
        logger.error(f"請求資料驗證失敗: {str(ve)}")
        return {
            "success": False,
            "conferenceId": "",
            "error": f"請求資料格式不正確: {str(ve)}"
        }
    except Exception as e:
        logger.error(f"啟動會議失敗: {str(e)}")
        return {
            "success": False,
            "conferenceId": "",
            "error": f"啟動會議失敗: {str(e)}"
        }

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
    conf = active_conferences[conference_id]
    config = conf["config"]
    
    # 更新狀態為介紹階段
    await update_conference_stage(conference_id, "introduction")
    
    # 生成並發送自我介紹
    await generate_introductions(conference_id)
    
    # 進入討論階段
    await update_conference_stage(conference_id, "discussion")
    
    # 進行多輪討論
    for round_num in range(1, config["rounds"] + 1):
        await run_discussion_round(conference_id, round_num)
    
    # 生成結論
    await update_conference_stage(conference_id, "conclusion")
    await generate_conclusion(conference_id)
    
    # 標記會議結束
    await update_conference_stage(conference_id, "ended")
    
    logger.info(f"Conference {conference_id} completed")

async def update_conference_stage(conference_id: str, stage: str):
    """更新會議階段並通知客戶端"""
    conf = active_conferences[conference_id]
    conf["stage"] = stage
    
    # 通過WebSocket通知客戶端
    await broadcast_message(conference_id, {"type": "stage_change", "stage": stage})
    logger.info(f"Conference {conference_id} stage changed to {stage}")

async def update_current_round(conference_id: str, round_num: int):
    """更新當前回合並通知客戶端"""
    conf = active_conferences[conference_id]
    conf["current_round"] = round_num
    
    # 通過WebSocket通知客戶端
    await broadcast_message(conference_id, {"type": "round_update", "round": round_num})

# MVP階段使用模擬的回應，實際環境中使用OpenAI API
async def generate_ai_response(prompt: str, participant_id: str, temperature: float = 0.7) -> str:
    """使用OpenAI生成回應"""
    try:
        # 檢查API密鑰是否已配置
        client = get_openai_client()
        if not client:
            logger.warning("未設置OpenAI API密鑰，使用預設回應")
            return f"這是一個預設回應，因為未配置OpenAI API。我是{participant_id}。"
        
        # 構建角色提示詞
        role_prompt = ROLE_PROMPTS.get(participant_id, "")
        
        try:
            # 嘗試使用新版API格式
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"你是一個名為{participant_id}的虛擬角色。{role_prompt}請用繁體中文回答，風格幽默生動。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            else:
                # 使用舊版API格式
                response = client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"你是一個名為{participant_id}的虛擬角色。{role_prompt}請用繁體中文回答，風格幽默生動。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
        except AttributeError as attr_err:
            # 處理可能的API結構差異
            logger.warning(f"嘗試調用OpenAI API時發生屬性錯誤: {str(attr_err)}")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"你是一個名為{participant_id}的虛擬角色。{role_prompt}請用繁體中文回答，風格幽默生動。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=300
            )
            
            if hasattr(response.choices[0], 'message'):
                return response.choices[0].message.content.strip()
            return response.choices[0]['message']['content'].strip()
            
    except Exception as e:
        logger.error(f"OpenAI API調用失敗: {str(e)}")
        return f"生成回應時發生錯誤。我是{participant_id}，我會繼續參與討論。錯誤訊息: {str(e)[:100]}"

async def generate_introductions(conference_id: str):
    """生成所有參與者的自我介紹"""
    conf = active_conferences[conference_id]
    config = conf["config"]
    topic = config["topic"]
    
    # 主持人介紹會議
    await add_message(
        conference_id,
        "moderator",
        f"大家好，歡迎參加今天的主題為「{topic}」的會議。現在我們將進行自我介紹，請各位簡單介紹自己並談談對今天主題的看法。"
    )
    
    # 等待1秒使界面顯示更自然
    await asyncio.sleep(1)
    
    # 參與者依次進行自我介紹
    for participant in config["participants"]:
        if not participant["isActive"]:
            continue
        
        # 構建提示
        prompt = f"你是{participant['name']}（{participant['title']}），請你用繁體中文做一個簡短的自我介紹，提到你的角色和職責。然後，針對會議主題「{topic}」，簡短表達你的第一印象或初步想法，不超過100字。"
        
        # 生成回應
        response = await generate_ai_response(prompt, participant["id"], participant.get("temperature", 0.7))
        
        # 添加消息並廣播
        await add_message(conference_id, participant["id"], response)
        
        # 模擬打字延遲
        await asyncio.sleep(3)
    
    # 主持人結束介紹階段
    await add_message(
        conference_id,
        "moderator",
        "謝謝大家的自我介紹。現在我們將進入正式討論階段，請各位就主題展開發言。"
    )
    
    await asyncio.sleep(1)

async def run_discussion_round(conference_id: str, round_num: int):
    """執行一個討論回合"""
    conf = active_conferences[conference_id]
    config = conf["config"]
    topic = config["topic"]
    
    # 更新當前回合
    await update_current_round(conference_id, round_num)
    
    # 設置默認主持人 (使用第一位參與者或創建一個虛擬主持人)
    # 獲取主席信息
    chair = None
    if "chair" in config:
        chair = next((p for p in config["participants"] if p["id"] == config["chair"]), None)
    
    if not chair:
        # 使用會議主持人作為默認主席
        chair = {
            "id": "moderator",
            "name": "會議主持人",
            "title": "AI會議助手",
            "temperature": 0.7
        }
    
    # 生成回合主題
    round_topic = get_round_topic(round_num, topic)
    
    # 主席開場白
    chair_prompt = f"你是會議主席{chair['name']}（{chair['title']}）。現在是第{round_num}輪討論，主題是「{topic}」。請你用繁體中文給出本輪討論的開場白，說明本輪將討論的內容：{round_topic}，並邀請下一位參與者發言，不超過100字。"
    chair_response = await generate_ai_response(chair_prompt, chair["id"], chair.get("temperature", 0.7))
    
    chair_message = {
        "id": f"{conference_id}_round{round_num}_chair",
        "speakerId": chair["id"],
        "speakerName": chair["name"],
        "speakerTitle": chair["title"],
        "text": chair_response,
        "timestamp": datetime.now().isoformat()
    }
    
    # 儲存消息
    conf["messages"].append(chair_message)
    
    # 通過WebSocket發送消息
    await broadcast_message(conference_id, {
        "type": "new_message",
        "message": chair_message,
        "current_speaker": chair["id"]
    })
    
    # 模擬打字延遲
    await asyncio.sleep(3)
    
    # 獲取所有活躍參與者，並排除主席
    chair_id = chair["id"]
    active_participants = [p for p in config["participants"] if p["isActive"] and p["id"] != chair_id]
    
    for idx, participant in enumerate(active_participants):
        # 收集之前的消息作為上下文
        previous_messages = [m["text"] for m in conf["messages"][-min(5, len(conf["messages"])):]]
        context = "\n".join(previous_messages)
        
        # 構建提示
        prompt = f"""
        你是{participant['name']}（{participant['title']}）。
        當前會議主題是「{topic}」，當前討論的重點是：{round_topic}
        
        以下是之前的對話：
        {context}
        
        請你根據自己的角色和專業領域，用繁體中文對當前討論主題發表看法，並可回應之前其他人的意見。回答不超過150字。
        """
        
        # 生成回應
        response = await generate_ai_response(prompt, participant["id"], participant.get("temperature", 0.7))
        
        # 建立消息物件
        message = {
            "id": f"{conference_id}_round{round_num}_{participant['id']}",
            "speakerId": participant["id"],
            "speakerName": participant["name"],
            "speakerTitle": participant["title"],
            "text": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # 儲存消息
        conf["messages"].append(message)
        
        # 通過WebSocket發送消息
        await broadcast_message(conference_id, {
            "type": "new_message",
            "message": message,
            "current_speaker": participant["id"]
        })
        
        # 模擬打字延遲
        await asyncio.sleep(4)

async def generate_conclusion(conference_id: str):
    """生成會議結論"""
    conf = active_conferences[conference_id]
    config = conf["config"]
    topic = config["topic"]
    
    # 嘗試尋找秘書參與者，如果沒有則使用默認秘書
    secretary = next((p for p in config["participants"] if p.get("id") == "Secretary Pig" and p.get("isActive", True)), None)
    
    if not secretary:
        # 創建一個默認的秘書
        secretary = {
            "id": "conclusion_bot",
            "name": "會議小結機器人",
            "title": "AI總結助手",
            "temperature": 0.5
        }
    
    # 收集所有消息作為上下文
    all_messages = [f"{m.get('speakerName', 'Unknown')} ({m.get('speakerTitle', 'Unknown')}): {m.get('text', '')}" for m in conf.get("messages", [])]
    context = "\n".join(all_messages[-20:])  # 最後20條消息
    
    # 構建提示
    prompt = f"""
    你是會議秘書{secretary['name']}。會議主題是「{topic}」，經過了{config.get("rounds", 3)}輪討論。
    
    以下是會議中的部分發言摘要：
    {context}
    
    請你用繁體中文總結整場會議的重點，並提出5點關鍵結論或行動項目。格式為帶編號的列表，總字數不超過300字。
    """
    
    try:
        # 生成總結
        client = get_openai_client()
        
        if not client:
            # 如果API客戶端不可用，返回一個通用結論
            conclusion = f"由於技術原因，無法連接到AI服務生成完整的會議結論。這裡是一個簡單的總結：{topic}的會議已結束，感謝所有與會者的寶貴意見。"
        else:
            try:
                # 嘗試使用新版API
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "你是一位專業的會議秘書，負責總結會議要點和提出建議。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,
                        max_tokens=350
                    )
                    conclusion = response.choices[0].message.content.strip()
                else:
                    # 嘗試使用舊版API
                    response = client.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "你是一位專業的會議秘書，負責總結會議要點和提出建議。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,
                        max_tokens=350
                    )
                    conclusion = response.choices[0].message.content.strip()
            except AttributeError:
                # 嘗試使用全局API方法
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一位專業的會議秘書，負責總結會議要點和提出建議。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=350
                )
                if hasattr(response.choices[0], 'message'):
                    conclusion = response.choices[0].message.content.strip()
                else:
                    conclusion = response.choices[0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"生成會議結論時出錯: {str(e)}")
        conclusion = f"由於技術原因，無法生成完整會議結論。請檢查API設置。錯誤信息: {str(e)[:100]}"
    
    # 建立消息物件
    message = {
        "id": f"{conference_id}_conclusion",
        "speakerId": secretary["id"],
        "speakerName": secretary["name"],
        "speakerTitle": secretary["title"],
        "text": conclusion,
        "timestamp": datetime.now().isoformat()
    }
    
    # 儲存消息
    conf["messages"].append(message)
    conf["conclusion"] = conclusion
    
    # 通過WebSocket發送消息
    await broadcast_message(conference_id, {
        "type": "new_message",
        "message": message,
        "current_speaker": secretary["id"]
    })
    await broadcast_message(conference_id, {"type": "conclusion", "text": conclusion})

def get_round_topic(round_num: int, main_topic: str) -> str:
    """獲取每輪討論的具體主題"""
    topics = {
        1: f"{main_topic}的主要優勢和機會",
        2: f"{main_topic}可能面臨的挑戰和風險",
        3: f"{main_topic}的市場潛力和客戶需求",
        4: f"{main_topic}所需的資源和預算",
        5: f"實施{main_topic}的時間表和里程碑",
        6: f"{main_topic}的具體行動計劃"
    }
    
    return topics.get(round_num, f"{main_topic}的進一步討論要點")

# 原生WebSocket端點保持不變
@app.websocket("/ws/conference/{conference_id}")
async def websocket_endpoint(websocket: WebSocket, conference_id: str):
    await websocket.accept()
    
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"WebSocket連接已建立 - 客戶端: {client_info}，會議ID: {conference_id}")
    
    if conference_id not in active_conferences:
        logger.warning(f"客戶端嘗試連接不存在的會議 {conference_id}")
        await websocket.send_json({"type": "error", "message": "會議不存在"})
        await websocket.close()
        return
    
    if conference_id not in connected_clients:
        connected_clients[conference_id] = []
    
    connected_clients[conference_id].append(websocket)
    logger.info(f"客戶端已連接到會議 {conference_id}, 當前連接數: {len(connected_clients[conference_id])}")
    
    # 發送現有消息和狀態
    conference = active_conferences[conference_id]
    init_data = {
        "type": "init",
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
        await process_introductions(conference_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"收到來自客戶端的消息: {data}")
            await process_client_message(conference_id, data)
    except WebSocketDisconnect:
        connected_clients[conference_id].remove(websocket)
        logger.info(f"客戶端已斷開連接，會議 {conference_id}，剩餘連接: {len(connected_clients[conference_id])}")
    except Exception as e:
        logger.error(f"WebSocket連接錯誤: {str(e)}")
        try:
            connected_clients[conference_id].remove(websocket)
        except ValueError:
            pass
        logger.exception("WebSocket處理過程中發生異常")

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
                "id": "moderator",
                "name": "會議主持人",
                "title": "AI會議助手"
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
        "type": "new_message",
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
    if conference_id not in active_conferences:
        return
    
    # 處理會議結束
    conference = active_conferences[conference_id]
    
    if conference["stage"] not in ["conclusion", "ended"]:
        await process_conclusion(conference_id)
    
    # 清理資源
    # 我們保留會議數據一段時間供查詢，但可以清理不必要的連接
    if conference_id in connected_clients:
        for client in connected_clients[conference_id]:
            try:
                await client.close()
            except:
                pass
        connected_clients[conference_id] = []

async def process_introductions(conference_id: str):
    """處理會議的自我介紹階段"""
    logger.info(f"開始處理會議 {conference_id} 的自我介紹階段")
    
    if conference_id not in active_conferences:
        logger.error(f"嘗試處理不存在的會議: {conference_id}")
        return
    
    conference = active_conferences[conference_id]
    
    # 更新會議階段為「介紹」
    await update_conference_stage(conference_id, "introduction")
    
    # 生成並發送自我介紹
    await generate_introductions(conference_id)
    
    # 進入討論階段
    await update_conference_stage(conference_id, "discussion")
    
    # 開始第一輪討論
    await run_discussion_round(conference_id, 1)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 