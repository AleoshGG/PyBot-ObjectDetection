from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket
from src.detections.data.schemas import InferenceResponse, DetectionResult
from src.detections.services.inference_service import InferenceService
from src.detections.handler.websocket_handler import websocket_handler
import asyncio
import base64
import time
import json

router = APIRouter()
inference_service = InferenceService()

@router.post("/detect", response_model=InferenceResponse)
async def detect_objects(
    prototype_id: str = Form(...),
    image: UploadFile = File(...),  # Ahora recibimos el archivo directamente
    timestamp: str = Form(default=None)
):
    try:
        if timestamp is None:
            timestamp = str(time.time())
        
        # Leer la imagen directamente como bytes
        image_bytes = await image.read()
        
        # Procesar inferencia
        result = await inference_service.process_request(image_bytes)
        
        # Codificar la imagen procesada con las bounding boxes
        encoded_processed_image = base64.b64encode(result['processed_image']).decode('utf-8')
        
        # Preparar datos para WebSocket (igual que tu formato original)
        websocket_data = {
            "prototype_id": prototype_id,
            "detections": result['detections'],  # Ya en formato cls, conf
            "image": encoded_processed_image,
            "timestamp": timestamp
        }
        
        # Broadcast via WebSocket
        asyncio.create_task(
            websocket_handler.broadcast_json(websocket_data)
        )
        
        # Responder al cliente (Raspberry) solo con los resultados de inferencia
        return InferenceResponse(
            prototype_id=prototype_id,
            detections=result['detections'],
            inference_time=result['inference_time'],
            timestamp=timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler.connect(websocket)
    try:
        while True:
            # Mantener conexión activa
            await websocket.receive_text()
    except Exception as e:
        websocket_handler.disconnect(websocket)