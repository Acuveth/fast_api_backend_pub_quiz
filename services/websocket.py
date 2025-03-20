from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections and websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
            # Remove empty rooms
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
    async def broadcast(self, message: str, room_id: str):
        """Broadcast a message to all connections in a room"""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Connection might be closed
                    pass
    
    async def broadcast_json(self, data: dict, room_id: str):
        """Broadcast a JSON message to all connections in a room"""
        await self.broadcast(json.dumps(data), room_id)