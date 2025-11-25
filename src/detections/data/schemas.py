from pydantic import BaseModel
from typing import List

class DetectionResult(BaseModel):
    cls: int
    conf: float

class InferenceResponse(BaseModel):
    prototype_id: str
    detections: List[DetectionResult]
    inference_time: float
    timestamp: str