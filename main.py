from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import asyncio
import json

from src.WsManager import WsManager
from src.models import Crush,Code ,Player,Language

app = FastAPI()
manager = WsManager()

# グローバル変数
# ルームのステータスの管理
room_status = defaultdict(lambda: {
    "explanation": {"player1": False, "player2": False, "completed": False},
    "crush": {"player1": False, "player2": False, "completed": False},
    "fix": {"player1": False, "player2": False, "completed": False},
    "result": {"player1": False, "player2": False, "completed": False},
})
# 部屋ごとのコードを管理
roomId_code = defaultdict(lambda: {
    "player1": None,
    "player2": None,
    "code": None  # デフォルトのコード
})
lock = asyncio.Lock()

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
    return HTMLResponse("CodeCrushAPI Create By Ayuayuyu")


def validate_room_and_player(roomId: str, player: str):
    if player not in ["player1", "player2"]:
        raise HTTPException(status_code=400, detail="Invalid player. Use 'player1' or 'player2'.")
    
    
    
def compare_and_add_comment(old_code: str, new_code: str,language:str) -> str:
    """
    2つのコードを比較し、差分がある行に //del コメントを追加する。
    """
    # コードを行ごとに分割
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    # 結果を格納するリスト
    result = []
    
    def comment_select():
        if language == "c":
            return "//del"
        elif language == "python":
            return "#del"
    
    comment = comment_select()
    
    
    # 行ごとに比較
    for i, new_line in enumerate(new_lines):
        if i < len(old_lines):
            old_line = old_lines[i]
            # 変更されている場合
            if new_line != old_line:
                result.append(f"{new_line} {comment}")  # コメント追加
            else:
                result.append(new_line)  # 変更なし
        else:
            # 新しい行（旧コードに存在しない行）
            result.append(f"{new_line} {comment}")
    
    # 古いコードに存在し、新しいコードにない行は無視（削除された行）
    # 結果を結合して返す
    return "\n".join(result)


@app.post("/defalutCode/{roomId}")
async def defaultCode(code: Code,roomId: str):
    """
    元となるコードを受け取るエンドポイント
    """
    async with lock:
        roomId_code[roomId]["code"] = code.code

    return roomId_code[roomId]["code"]
    

@app.post("/status/{status_type}/{roomId}")
async def update_status(status_type: str, roomId: str, update: Player):
    """
    任意のステータスを更新するエンドポイント
    """
    async with lock:
        if status_type not in room_status[roomId]:
            return {"error": "Invalid status type"}

        if update.player in room_status[roomId][status_type]:
            room_status[roomId][status_type][update.player] = True

        if (
            room_status[roomId][status_type]["player1"]
            and room_status[roomId][status_type]["player2"]
        ):
            room_status[roomId][status_type]["completed"] = True

    return room_status[roomId][status_type]


@app.get("/status/{status_type}/{roomId}")
async def get_status(status_type: str, roomId: str):
    """
    任意のステータスを取得するエンドポイント
    """
    if roomId not in room_status or status_type not in room_status[roomId]:
        return {"error": "Room or status type not found"}

    if room_status[roomId][status_type]["completed"]:
        print(f"status: {status_type}")
        return {"status": status_type}
    else :
        print("status : waiting")
        return {"status": "waiting"}


@app.post("/codeCrush/{roomId}")
async def codeCrushEndpoint(data: Crush, roomId: str):
    """
    破壊したコードを送るエンドポイント
    """
    async with lock:
        validate_room_and_player(roomId, data.player)
        roomId_code[roomId][data.player] = data.code
        print(f"roomId: {roomId}, {data.player} sent code: {data.code}")

    return {"status": "sendCode"}


@app.post("/getCode/{roomId}")
async def getCodeEndpoint(data: Language, roomId: str):
    """
    プレイヤー1とプレイヤー2でコードを交換するエンドポイント
    """
    async with lock:
        validate_room_and_player(roomId, data.player)
        other_player = "player1" if data.player == "player2" else "player2"

        if roomId_code[roomId][other_player]:
            #比較してコメントの追加
            exchanged_code = compare_and_add_comment(roomId_code[roomId]["code"], roomId_code[roomId][other_player],data.language)
            print(f"Exchanging code with {other_player}: {exchanged_code}")
            return {"status": "exchanged", "code": exchanged_code}

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
            await manager.broadcast(roomId, json.dumps({"status": "received", "roomId": roomId, "code": code}))
    except WebSocketDisconnect:
        await manager.disconnect(websocket, roomId)
        print("WebSocket disconnected")
        async with lock:
            roomId_code.pop(roomId, None)
            print(f"Room {roomId} removed")
