from src.detections.services.inference_service import InferenceService
from src.detections.controller.detections_controller import router
from src.detections.handler.websocket_handler import websocket_handler

from fastapi import FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="High Performance Object Detection Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global thread pool for CPU-intensive tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

# Services
inference_service = InferenceService(thread_pool)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "object_detection",
        "active_connections": len(websocket_handler.active_connections)
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=1200,
        workers=1,  # Usar 1 worker y manejar concurrencia internamente
        loop="asyncio"
    )