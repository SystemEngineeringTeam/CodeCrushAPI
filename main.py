from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from src.WsManager import WsManager
from src.models import Crush,Player

app = FastAPI()
manager = WsManager()

# 部屋ごとのコード管理
roomId_code: Dict[str, Dict[str, str]] = {}

# CORS設定
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
async def codeCrushEndpoint(data: Crush, roomId: str):
    """
    破壊したコードを送るエンドポイント
    プレイヤー1とプレイヤー2でコードを交換する
    """
    if data.player not in ["player1", "player2"]:
        raise HTTPException(status_code=400, detail="Invalid player. Use 'player1' or 'player2'.")

    if roomId not in roomId_code:
        roomId_code[roomId] = {"player1": None, "player2": None}

    # コードを保存
    roomId_code[roomId][data.player ] = data.code
    print(f"roomId: {roomId}, {data.player } sent code: {data.code}")

    # もう一方のプレイヤーのコードを確認
    other_player = "player1" if data.player == "player2" else "player2"
    if roomId_code[roomId][other_player]:
        exchanged_code = roomId_code[roomId][other_player]
        print(f"Exchanging code with {other_player}: {exchanged_code}")
        return {"status": "exchanged", "code": exchanged_code}

    # もう一方のコードがまだない場合
    return {"status": "waiting"}

@app.post("/getCode/{roomId}")
async def getCodeEndpoint(data: Player, roomId: str):
    """
    プレイヤー1とプレイヤー2でコードを交換するエンドポイント
    """
    if data.player not in ["player1", "player2"]:
        raise HTTPException(status_code=400, detail="Invalid player. Use 'player1' or 'player2'.")
    # もう一方のプレイヤーのコードを確認
    other_player = "player1" if data.player == "player2" else "player2"
    if roomId_code[roomId][other_player]:
        exchanged_code = roomId_code[roomId][other_player]
        print(f"Exchanging code with {other_player}: {exchanged_code}")
        return {"status": "exchanged", "code": exchanged_code}

    # もう一方のコードがまだない場合
    return {"status": "waiting"}

@app.websocket("/ws/{roomId}")
async def websocket_endpoint(websocket: WebSocket, roomId: str):
    """
    WebSocketのエンドポイント
    """
    await manager.connect(websocket, roomId)
    try:
        while True:
            code = await websocket.receive_text()
            await websocket.send_text(json.dumps({"status": "received", "roomId": roomId,"code": code}))
    except WebSocketDisconnect:
        await manager.disconnect(websocket, roomId)
        print("WebSocket close")
        try:
            del roomId_code[roomId]
            print(f"remove roomId: {roomId}")
        except KeyError:
            pass
