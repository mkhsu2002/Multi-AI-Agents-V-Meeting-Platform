import asyncio
import websockets
import json
import requests
import traceback
import time

async def test_conference():
    try:
        # 1. 創建會議
        print("步驟1: 創建會議")
        conference_data = {
            "topic": "測試主題",
            "participants": [
                {"id": "test1", "name": "測試用戶1", "title": "測試角色1", "isActive": True},
                {"id": "test2", "name": "測試用戶2", "title": "測試角色2", "isActive": True}
            ],
            "rounds": 1
        }
        
        response = requests.post(
            "http://localhost:8000/api/conference/start",
            headers={"Content-Type": "application/json"},
            json=conference_data
        )
        
        if not response.ok:
            print(f"創建會議失敗，狀態碼: {response.status_code}")
            print(f"響應內容: {response.text}")
            return
            
        conference_info = response.json()
        if not conference_info.get("success"):
            print(f"創建會議失敗: {conference_info}")
            return
            
        conference_id = conference_info["conferenceId"]
        print(f"會議創建成功，ID: {conference_id}")
        
        # 2. 建立WebSocket連接
        print("\n步驟2: 建立WebSocket連接")
        await test_ws_connection(conference_id)
        
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        print("詳細錯誤信息:")
        traceback.print_exc()

async def test_ws_connection(conference_id):
    uri = f"ws://localhost:8000/ws/conference/{conference_id}"
    
    try:
        print(f"嘗試連接: {uri}")
        async with websockets.connect(uri) as websocket:
            print(f"WebSocket連接已建立: {uri}")
            
            # 接收初始消息
            response = await websocket.recv()
            print(f"收到初始消息: {response}")
            
            # 解析JSON響應
            data = json.loads(response)
            print(f"會議階段: {data.get('stage')}")
            print(f"訊息數量: {len(data.get('messages', []))}")
            
            # 等待更多消息
            print("\n等待更多消息...")
            for i in range(10):  # 最多接收10條消息
                try:
                    # 設置超時
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"收到新消息 #{i+1}: {response}")
                    
                    # 如果收到新消息，解析並打印
                    data = json.loads(response)
                    msg_type = data.get("type")
                    print(f"消息類型: {msg_type}")
                    
                    if msg_type == "new_message":
                        speaker = data.get("message", {}).get("speakerName")
                        text = data.get("message", {}).get("text")
                        print(f"說話者: {speaker}")
                        print(f"內容: {text[:100]}..." if len(text) > 100 else f"內容: {text}")
                    
                except asyncio.TimeoutError:
                    print(f"等待超時 #{i+1}，沒有收到新消息")
                    break
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"連接關閉: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
        print("詳細錯誤信息:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conference()) 