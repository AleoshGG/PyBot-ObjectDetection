from fastapi import FastAPI, UploadFile, File, WebSocket, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import base64
from typing import List, Dict, Any
import json

from src.detections.controller.detections_controller import router
from src.detections.handler.websocket_handler import websocket_handler

app = FastAPI(title="Object Detection Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Object Detection Service Running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "object_detection"}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1
    )