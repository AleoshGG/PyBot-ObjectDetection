import os

class Settings:
    MODEL_PATH: str = os.path.join("model_ai", "best2.pt")
    WEBSOCKET_BROADCAST: str = "ws_broadcast"

settings = Settings()