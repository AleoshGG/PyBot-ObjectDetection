from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from src.detections.data.schemas import InferenceResponse, DetectionResult
from src.detections.services.inference_service import InferenceService
from src.detections.handler.websocket_handler import websocket_handler
import asyncio
import base64
import time
import uuid

router = APIRouter()

@router.post("/detect", response_model=InferenceResponse)
async def detect_objects(
    background_tasks: BackgroundTasks,
    prototype_id: str = Form(...),
    image: UploadFile = File(...),
    timestamp: str = Form(default=None)
):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        if timestamp is None:
            timestamp = str(time.time())
        
        # Leer imagen
        image_bytes = await image.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Imagen vacía")
        
        # Procesar inferencia
        result = await router.inference_service.process_request(image_bytes, request_id)
        
        # Preparar respuesta para Raspberry
        response_data = InferenceResponse(
            prototype_id=prototype_id,
            detections=result['detections'],
            inference_time=time.time() - start_time,
            timestamp=timestamp,
            request_id=request_id
        )
        
        # Enviar al WebSocket en segundo plano (no esperar)
        if result['processed_image']:
            background_tasks.add_task(
                broadcast_to_websocket,
                prototype_id,
                result['detections'],
                result['processed_image'],
                timestamp
            )
        
        return response_data
        
    except Exception as e:
        print(f"Error en request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

async def broadcast_to_websocket(prototype_id: str, detections: list, processed_image: bytes, timestamp: str):
    """Transmisión asíncrona al WebSocket"""
    try:
        encoded_image = base64.b64encode(processed_image).decode('utf-8')
        websocket_data = {
            "prototype_id": prototype_id,
            "detections": detections,
            "image": encoded_image,
            "timestamp": timestamp
        }
        
        await websocket_handler.broadcast_json(websocket_data)
    except Exception as e:
        print(f"Error en broadcast WebSocket: {e}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Conectar el cliente
    await websocket_handler.connect(websocket)
    
    try:
        # Mantener la conexión activa
        while True:
            # Recibir cualquier mensaje (puede ser un ping)
            data = await websocket.receive_text()
            # Opcional: puedes manejar mensajes del cliente aquí
            # Por ejemplo, si quieres que el cliente envíe comandos
            
    except WebSocketDisconnect:
        websocket_handler.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        websocket_handler.disconnect(websocket)
        
@router.get("/stats")
async def get_stats():
    """Endpoint para monitorear rendimiento"""
    return router.inference_service.get_stats()

# Inicializar el servicio después de definir el router
@router.on_event("startup")
async def startup_event():
    from app import thread_pool
    router.inference_service = InferenceService(thread_pool)