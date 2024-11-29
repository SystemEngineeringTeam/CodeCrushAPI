from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from src.WsManager import WsManager
from src.models import Datas



app = FastAPI()
manager = WsManager()

#dictでroomIdとidを保存する
roomId_store = {}

class Counter():
    counter =  0
    
    def getCount(self):
        self.counter+=1
        return self.counter
    
counter = Counter()

# CORSの設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get():
    return HTMLResponse("code-read Create By Ayuayuyu")

@app.post("/codeCrush/{roomId}")
async def codeCrushEndpoint(code: str):
    """
    破壊したコードを送るエンドポイント
    """
    print(f"codeCrush: {code}")
    return {"status": "crush"}

@app.post("/codefix")
async def codeFixEndpoint(code: str):
    """
    修正したコードを送るエンドポイント
    """
    print(f"codeFix: {code}")
    return {"status": "fix"}
    

@app.websocket("/ws/{roomId}")
async def websocket_endpoint(websocket: WebSocket,roomId:str):
    """
    webSocketのエンドポイント
    """
    await manager.connect(websocket,roomId)
    try:
        while True:
            roomId = await websocket.receive_text()
            #roomIdだけ送られたとき
            roomId_store[roomId] = None
            await websocket.send_text(json.dumps({"status": roomId}))
    except WebSocketDisconnect:
        #接続が切れた場合は削除
        await manager.disconnect(roomId)
        print("WebSocket close")
        #roomIdの削除
        print(f"remove roomId: {roomId}")
        if roomId in roomId_store:
            del roomId_store[roomId]
            
    