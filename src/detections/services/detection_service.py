import cv2
import numpy as np
from ultralytics import YOLO
from src.config.config import settings

class DetectionService:
    def __init__(self):
        self.model = YOLO(settings.MODEL_PATH)
        self.model.fuse()
    
    def process_image(self, image_bytes: bytes) -> tuple:
        # Convertir bytes a numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if original_img is None:
            raise ValueError("No se pudo decodificar la imagen")
        
        # Redimensionar para inferencia (como en tu código original)
        inference_img = cv2.resize(original_img, (256, 256))
        
        # Ejecutar inferencia
        results = self.model(inference_img)
        
        # Extraer detecciones en formato cls/conf
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    "cls": int(box.cls[0]),
                    "conf": float(box.conf[0])
                })
        
        # Crear imagen anotada (igual que tu código original)
        annotated_frame = results[0].plot()  # Esto dibuja las bounding boxes
        
        # Redimensionar para visualización (320x240 como en tu código)
        display_frame = cv2.resize(annotated_frame, (320, 240))
        
        # Codificar imagen a JPEG
        _, encoded_img = cv2.imencode('.jpg', display_frame)
        return detections, encoded_img.tobytes()