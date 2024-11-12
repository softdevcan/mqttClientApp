from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..core.mqtt_manager import mqtt_manager
from ..models.mqtt_models import MQTTConnectionConfig, MQTTPublishMessage
from ..config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.APP_NAME}
    )

@router.get("/connect", response_class=HTMLResponse)
async def connect_page(request: Request):
    return templates.TemplateResponse(
        "connect.html",
        {
            "request": request,
            "default_host": settings.DEFAULT_HOST,
            "default_port": settings.DEFAULT_PORT
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )

@router.post("/api/connect")
async def connect(
    host: str = Form(...),
    port: int = Form(...),
    username: str = Form(None),
    password: str = Form(None)
):
    config = MQTTConnectionConfig(
        host=host,
        port=port,
        username=username,
        password=password
    )
    return await mqtt_manager.connect(config)

@router.post("/api/disconnect")
async def disconnect():
    return await mqtt_manager.disconnect()

@router.post("/api/subscribe")
async def subscribe(topic: str = Form(...), qos: int = Form(...)):
    return await mqtt_manager.subscribe(topic, qos)

@router.post("/api/unsubscribe")
async def unsubscribe(topic: str = Form(...)):
    return await mqtt_manager.unsubscribe(topic)

@router.post("/api/publish")
async def publish(
    topic: str = Form(...),
    message: str = Form(...),
    qos: int = Form(...),
    retain: bool = Form(...)
):
    return await mqtt_manager.publish(topic, message, qos, retain)

@router.get("/api/connection-status")
async def connection_status():
    """MQTT bağlantı durumunu kontrol et"""
    is_connected = mqtt_manager.connection.client is not None
    return {"status": "connected" if is_connected else "disconnected"}