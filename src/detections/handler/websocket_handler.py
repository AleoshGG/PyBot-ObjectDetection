import asyncio
import json
from fastapi import WebSocket

class WebSocketHandler:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast_json(self, data: dict):
        if self.active_connections:
            message = json.dumps(data)
            tasks = [asyncio.create_task(conn.send_text(message)) 
                    for conn in self.active_connections]
            await asyncio.gather(*tasks, return_exceptions=True)

websocket_handler = WebSocketHandler()