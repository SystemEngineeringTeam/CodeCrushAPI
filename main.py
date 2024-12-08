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
    "read": {"player1": False, "player2": False, "completed": False},
    "delete": {"player1": False, "player2": False, "completed": False},
    "fix": {"player1": False, "player2": False, "completed": False},
    "answer": {"player1": False, "player2": False, "completed": False},
})
room_getStatus = defaultdict(lambda: {
    "status": None
})
# 部屋ごとのコードを管理
roomId_code = defaultdict(lambda: {
    "player1": None,
    "player2": None,
    "code": None  # デフォルトのコード
})

player = defaultdict(lambda: {
    "player1": False,
    "player2": False,
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
    
    
    
def compare_and_add_comment(old_code: str, new_code: str, language: str) -> str:
    """
    2つのコードを比較し、内容が変更された行に //delete または #delete コメントを追加する。
    また、旧コードに存在し新コードにない行を出力する。
    """
    # コードを行ごとに分割
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()

    # 結果を格納するリスト
    result = []

    # 削除された行を格納するリスト
    deleted_lines = []

    def comment_select():
        if language == "c":
            return "//delete"
        elif language == "python":
            return "#delete"

    comment = comment_select()

    max_lines = max(len(old_lines), len(new_lines))

    for i in range(max_lines):
        old_line = old_lines[i] if i < len(old_lines) else None
        new_line = new_lines[i] if i < len(new_lines) else None

        # 両方の行が存在する場合
        if old_line is not None and new_line is not None:
            # 内容が変更されている場合
            if old_line.strip() != new_line.strip():
                # ただし、空白やインデントの変更だけの場合は変更なしとして扱う
                if old_line.strip() == new_line.strip():
                    result.append(new_line)  # そのまま追加
                else:
                    result.append(f"{new_line} {comment}")  # コメント追加
            else:
                result.append(new_line)  # そのまま追加
        # 新しいコードに存在しない場合（削除された行）
        elif old_line is not None:
            deleted_lines.append(old_line)  # 削除された行として記録
        # 新しいコードにのみ存在する場合
        elif new_line is not None:
            result.append(f"{new_line} {comment}")


    # 結果を結合して返す
    return "\n".join(result)




@app.post("/player/{roomId}")
async def playerendpoint(data: Player,roomId: str):
    if data.player == "player1":
        print(f"player1: {player[roomId]['player1']},player2: {player[roomId]['player2']}")
        if player[roomId]["player1"] == False:
            player[roomId]["player1"] = True
            print("player1: false")
            return {"player": "false"}
        elif player[roomId]["player1"] == True:
            print("player1: true")
            return {"player": "true"}
    elif data.player == "player2":
        if player[roomId]["player2"] == False:
            player[roomId]["player2"] = True
            print("player2: false")
            return {"player": "false"}
        elif player[roomId]["player2"] == True:
            print("player2: true")
            return {"player": "true"}



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
            room_getStatus[roomId] = status_type

    return room_status[roomId][status_type]


@app.get("/status/{roomId}")
async def get_status(roomId: str):
    """
    任意のステータスを取得するエンドポイント
    """
    if roomId in room_getStatus[roomId]:
        return {"error": "Room or status type not found"}

    if (room_getStatus[roomId]!= None):
        print(f"status: {room_getStatus[roomId]}")
        return {"status": room_getStatus[roomId]}
    else :
        print("status : waiting")
        return {"status": "waiting"}


@app.post("/deleteCode/{roomId}")
async def codeCrushEndpoint(data: Crush, roomId: str):
    """
    破壊したコードを送るエンドポイント
    """
    async with lock:
        validate_room_and_player(roomId, data.player)
        roomId_code[roomId][data.player] = data.code
        print(f"roomId: {roomId}, {data.player} sent code: {data.code}")

    return {"status": "sendCode"}


@app.post("/fixCode/{roomId}")
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
