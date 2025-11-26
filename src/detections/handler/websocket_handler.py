import asyncio
import json
from fastapi import WebSocket
from typing import List

class WebSocketHandler:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        # Aceptar la conexión sin restricciones
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Cliente WebSocket conectado. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 Cliente WebSocket desconectado. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_json(self, data: dict):
        if not self.active_connections:
            return
            
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error enviando a cliente: {e}")
                disconnected.append(connection)
        
        # Limpiar conexiones desconectadas
        for connection in disconnected:
            self.disconnect(connection)

websocket_handler = WebSocketHandler()