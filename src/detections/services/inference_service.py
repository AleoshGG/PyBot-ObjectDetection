import time
import asyncio
import cv2
import numpy as np
from src.detections.services.detection_service import DetectionService
from concurrent.futures import ThreadPoolExecutor

class InferenceService:
    def __init__(self, thread_pool: ThreadPoolExecutor):
        self.detector = DetectionService()
        self.thread_pool = thread_pool
        self.processing_times = []
        
    async def process_request(self, image_bytes: bytes, request_id: str):
        """Procesa la inferencia en un thread separado para no bloquear el event loop"""
        try:
            # Ejecutar en thread pool para no bloquear el event loop
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            result = await loop.run_in_executor(
                self.thread_pool, 
                self._process_image_sync, 
                image_bytes, 
                request_id
            )
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Mantener solo los últimos 100 tiempos
            if len(self.processing_times) > 100:
                self.processing_times.pop(0)
                
            return result
            
        except Exception as e:
            print(f"Error en inferencia {request_id}: {e}")
            raise e
    
    def _process_image_sync(self, image_bytes: bytes, request_id: str):
        """Procesamiento síncrono en el thread pool"""
        detections, processed_image = self.detector.process_image(image_bytes)
        
        return {
            'detections': detections,
            'processed_image': processed_image,
            'request_id': request_id
        }
    
    def get_stats(self):
        """Estadísticas de rendimiento"""
        if not self.processing_times:
            return {"avg_time": 0, "min_time": 0, "max_time": 0}
        
        return {
            "avg_time": sum(self.processing_times) / len(self.processing_times),
            "min_time": min(self.processing_times),
            "max_time": max(self.processing_times),
            "total_processed": len(self.processing_times)
        }