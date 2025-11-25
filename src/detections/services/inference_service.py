import time
import cv2
import numpy as np
from src.detections.services.detection_service import DetectionService

class InferenceService:
    def __init__(self):
        self.detector = DetectionService()
    
    async def process_request(self, image_bytes: bytes):
        start_time = time.time()
        
        # El detector ahora retorna detecciones en formato cls/conf
        detections, processed_image = self.detector.process_image(image_bytes)
        
        inference_time = time.time() - start_time
        
        return {
            'detections': detections,  # Formato: [{"cls": 0, "conf": 0.85}, ...]
            'inference_time': inference_time,
            'processed_image': processed_image  # Imagen con bounding boxes
        }