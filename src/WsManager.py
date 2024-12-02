from typing import List, Dict
from fastapi import WebSocket
from collections import defaultdict

class WsManager:
    def __init__(self):
        # 複数の部屋を管理するために辞書を使用する
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: str):
        try:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:  # リストが空なら部屋を削除
                del self.active_connections[room_id]
        except ValueError:
            print(f"Error: {ValueError}")

    async def broadcast(self, message: str, room_id: str):
        to_remove = []
        for connection in self.active_connections.get(room_id, []):
            try:
                await connection.send_text(message)
            except:
                to_remove.append(connection)

        for connection in to_remove:
            self.active_connections[room_id].remove(connection)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]
