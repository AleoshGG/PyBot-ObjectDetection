import cv2
import numpy as np
from ultralytics import YOLO
from src.config.config import settings

class DetectionService:
    def __init__(self):
        print("Cargando modelo YOLO...")
        self.model = YOLO(settings.MODEL_PATH)
        self.model.fuse()
        # Warm up del modelo
        self._warm_up_model()
        print("Modelo YOLO cargado y listo")
    
    def _warm_up_model(self):
        """Warm up del modelo para la primera inferencia rápida"""
        dummy_input = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        _ = self.model(dummy_input)
    
    def process_image(self, image_bytes: bytes) -> tuple:
        try:
            # Decodificar imagen más rápido
            nparr = np.frombuffer(image_bytes, np.uint8)
            original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if original_img is None:
                return [], b''
            
            # Redimensionar para inferencia (mantener relación de aspecto)
            inference_size = 320  # Reducir tamaño para más velocidad
            h, w = original_img.shape[:2]
            scale = inference_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            
            inference_img = cv2.resize(original_img, (new_w, new_h))
            
            # Inferencia con parámetros optimizados
            results = self.model(
                inference_img, 
                imgsz=inference_size,
                conf=0.25,  # Confianza mínima reducida
                iou=0.45,   # NMS IOU threshold
                max_det=10,  # Máximo número de detecciones
                verbose=False  # Silenciar logs
            )
            
            # Procesar detecciones
            detections = []
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "cls": int(box.cls[0]),
                        "conf": float(box.conf[0])
                    })
            
            # Crear imagen anotada solo si hay detecciones
            if detections:
                annotated_frame = results[0].plot()
                # Redimensionar al tamaño original para display
                display_frame = cv2.resize(annotated_frame, (w, h))
            else:
                display_frame = original_img
            
            # Codificar con calidad reducida para WebSocket
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]  # Calidad reducida
            _, encoded_img = cv2.imencode('.jpg', display_frame, encode_params)
            
            return detections, encoded_img.tobytes()
            
        except Exception as e:
            print(f"Error en procesamiento de imagen: {e}")
            return [], b''