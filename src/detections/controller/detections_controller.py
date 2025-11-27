import json
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from src.detections.services.rabbitmq_service import RabbitMQService
from src.detections.data.schemas import InferenceResponse, DetectionResult
from src.detections.services.inference_service import InferenceService
from src.detections.handler.websocket_handler import websocket_handler
import asyncio
import base64
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
# Instancia global del servicio RabbitMQ
rabbitmq_service = RabbitMQService()

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
        
        # Enviar a RabbitMQ en segundo plano (no esperar)
        if result['processed_image']:
            background_tasks.add_task(
                send_to_rabbitmq,
                prototype_id,
                result['detections'],
                result['processed_image'],
                timestamp
            )
        
        return response_data
        
    except Exception as e:
        print(f"Error en request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

async def send_to_rabbitmq(prototype_id: str, detections: list, processed_image: bytes, timestamp: str):
    """Enviar datos CAM a RabbitMQ de forma asíncrona"""
    try:
        # Convertir detections a string JSON
        detections_str = json.dumps(detections)
        
        # Codificar imagen a base64
        encoded_image = base64.b64encode(processed_image).decode('utf-8')
        
        # Crear estructura CAM
        cam_data = {
            "prototype_id": prototype_id,
            "detections": detections_str,  # Serializado como string JSON
            "image": encoded_image
        }
        
        # Enviar a RabbitMQ
        await rabbitmq_service.send_cam_data(cam_data)
        
    except Exception as e:
        print(f"Error enviando a RabbitMQ: {e}")

@router.get("/stats")
async def get_stats():
    """Endpoint para monitorear rendimiento"""
    return router.inference_service.get_stats()

# Inicializar servicios después de definir el router
@router.on_event("startup")
async def startup_event():
    from app import thread_pool
    router.inference_service = InferenceService(thread_pool)
    
    # Conectar a RabbitMQ
    try:
        # Obtener URL de RabbitMQ desde variables de entorno o configuración
        rabbitmq_url = os.getenv("URL_RABBIT")  # Reemplazar con tu URL real
        
        await rabbitmq_service.connect(rabbitmq_url)
        print("Servicio RabbitMQ inicializado exitosamente")
        
    except Exception as e:
        print(f"Error inicializando RabbitMQ: {e}")

@router.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    await rabbitmq_service.close()
    print("Conexión RabbitMQ cerrada")