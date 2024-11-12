from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from ..core.mqtt_manager import MQTTManager
import logging
import json

logger = logging.getLogger("websocket")


async def websocket_endpoint(websocket: WebSocket, mqtt_manager: MQTTManager):
    """
    WebSocket endpoint for handling MQTT message streaming
    """
    if websocket.client_state == WebSocketState.DISCONNECTED:
        return

    try:
        # WebSocket bağlantısını kabul et
        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.accept()

        logger.info("WebSocket connection established")

        # Önceki bağlantıyı temizle
        if hasattr(mqtt_manager.connection, 'websocket'):
            old_ws = mqtt_manager.connection.websocket
            if old_ws != websocket and hasattr(old_ws, 'close'):
                try:
                    await old_ws.close()
                except Exception as e:
                    logger.error(f"Error closing old websocket: {e}")

        # Yeni bağlantıyı ayarla
        mqtt_manager.connection.websocket = websocket

        # Cache'i temizle
        if hasattr(mqtt_manager, '_message_cache'):
            mqtt_manager._message_cache.clear()

        # Bağlantıyı açık tut ve mesajları dinle
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

    finally:
        # Cleanup
        logger.info("Cleaning up WebSocket connection")
        if hasattr(mqtt_manager.connection, 'websocket'):
            try:
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
            except Exception as e:
                logger.error(f"Error during websocket cleanup: {e}")
            finally:
                delattr(mqtt_manager.connection, 'websocket')

        if hasattr(mqtt_manager, '_message_cache'):
            mqtt_manager._message_cache.clear()