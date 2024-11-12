from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.routes import router
from .api.websocket import websocket_endpoint
from .config import settings
from pathlib import Path
import logging

from .core.mqtt_manager import mqtt_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG_MODE)

# CORS ayarlarını ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Güvenlik için spesifik origin'leri belirtebilirsiniz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyalar için dizin
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True)

# Static dosyaları mount et
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Router'ı ekle
app.include_router(router)

# WebSocket endpoint'ini direkt olarak tanımla
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    print(f"New WebSocket connection attempt from {websocket.client}")  # Debug için
    try:
        await websocket.accept()
        await websocket_endpoint(websocket, mqtt_manager)
    except Exception as e:
        print(f"WebSocket error: {e}")  # Debug için
        raise