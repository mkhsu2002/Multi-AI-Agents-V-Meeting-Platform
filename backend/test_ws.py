import asyncio
import websockets
import json
import traceback

async def test_ws_connection():
    # 使用我們剛剛創建的會議ID
    conference_id = "8e4b3aaf-088d-483c-a092-b57108eb8b0a"
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
            print("等待更多消息...")
            for _ in range(5):  # 最多接收5條消息
                try:
                    # 設置超時
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"收到新消息: {response}")
                except asyncio.TimeoutError:
                    print("等待超時，沒有收到新消息")
                    break
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"連接關閉: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
        print("詳細錯誤信息:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ws_connection()) 