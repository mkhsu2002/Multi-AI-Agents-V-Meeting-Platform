import uvicorn
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    print(f"啟動飛豬隊友 AI 虛擬會議系統後端服務")
    print(f"監聽端口: {port}")
    print(f"調試模式: {'開啟' if debug else '關閉'}")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未設置 OPENAI_API_KEY 環境變數，LLM 功能將不可用")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug
    ) 