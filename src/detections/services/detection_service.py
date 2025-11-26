import cv2
import numpy as np

# ------------------------------------------------------------
# 🔧 PARCHE para evitar:
# AttributeError: Can't get attribute 'C3k2'
# ------------------------------------------------------------
try:
    import ultralytics.nn.modules.block as block_mod
    # Si el checkpoint espera la clase "C3k2" pero no existe en la versión instalada
    if not hasattr(block_mod, "C3k2"):
        from ultralytics.nn.modules.block import C3
        block_mod.C3k2 = C3     # Alias estable para checkpoints YOLO antiguos
except Exception as e:
    print(f"Advertencia: no se pudo aplicar el parche C3k2: {e}")

# ------------------------------------------------------------

from ultralytics import YOLO
from src.config.config import settings


class DetectionService:
    def __init__(self):
        print("Cargando modelo YOLO...")

        # Carga del modelo YA con el parche aplicado
        self.model = YOLO(settings.MODEL_PATH)
        self.model.fuse()

        # Warm-up
        self._warm_up_model()
        print("Modelo YOLO cargado y listo")

    def _warm_up_model(self):
        """Warm up del modelo para la primera inferencia rápida"""
        dummy_input = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        _ = self.model(dummy_input)

    def process_image(self, image_bytes: bytes) -> tuple:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if original_img is None:
                return [], b''

            inference_size = 320
            h, w = original_img.shape[:2]
            scale = inference_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)

            inference_img = cv2.resize(original_img, (new_w, new_h))

            # Inferencia optimizada
            results = self.model(
                inference_img,
                imgsz=inference_size,
                conf=0.25,
                iou=0.45,
                max_det=10,
                verbose=False
            )

            # Procesar detecciones
            detections = []
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "cls": int(box.cls[0]),
                        "conf": float(box.conf[0])
                    })

            # Imagen anotada solo si hay detecciones
            if detections:
                annotated_frame = results[0].plot()
                display_frame = cv2.resize(annotated_frame, (w, h))
            else:
                display_frame = original_img

            # Codificación ligera
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
            _, encoded_img = cv2.imencode('.jpg', display_frame, encode_params)

            return detections, encoded_img.tobytes()

        except Exception as e:
            print(f"Error en procesamiento de imagen: {e}")
            return [], b''
