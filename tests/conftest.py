import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, create_autospec
import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.mqtt_manager import MQTTManager
from app.models.mqtt_models import MQTTConnection


@pytest.fixture
def test_client():
    """Create a test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client"""
    mock_client = create_autospec(mqtt.Client)
    mock_client.is_connected.return_value = True

    mock_client.connect = MagicMock()
    mock_client.disconnect = MagicMock()
    mock_client.subscribe = MagicMock()
    mock_client.unsubscribe = MagicMock()
    mock_client.publish = MagicMock()
    mock_client.loop_start = MagicMock()
    mock_client.loop_stop = MagicMock()
    mock_client.username_pw_set = MagicMock()

    return mock_client


class AsyncWebSocketMock:
    def __init__(self):
        self.sent_messages = []
        self.receive_queue = asyncio.Queue()

    async def send_text(self, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        self.sent_messages.append(message)

    async def receive_json(self):
        return await self.receive_queue.get()

    def put_message(self, message):
        self.receive_queue.put_nowait(message)


@pytest.fixture
def mqtt_test_manager(mock_mqtt_client):
    """Test MQTT manager"""
    manager = MQTTManager()
    manager.connection = MQTTConnection()
    manager.connection.client = mock_mqtt_client
    manager.connection.subscriptions = set()
    manager.connection.websocket = AsyncWebSocketMock()

    # Mock methods
    async def mock_connect(config):
        try:
            if hasattr(config, 'username') and config.username:
                manager.connection.client.username_pw_set(config.username, config.password)
            manager.connection.client.connect(config.host, config.port)
            manager.connection.client.loop_start()
            return {"status": "success", "message": f"Connected to {config.host}:{config.port}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def mock_disconnect():
        manager.connection.client.disconnect()
        manager.connection.client.loop_stop()
        return {"status": "success", "message": "Disconnected from broker"}

    async def mock_subscribe(topic, qos):
        manager.connection.client.subscribe(topic, qos)
        manager.connection.subscriptions.add(topic)
        return {"status": "success", "message": f"Subscribed to {topic}"}

    async def mock_unsubscribe(topic):
        manager.connection.client.unsubscribe(topic)
        if topic in manager.connection.subscriptions:
            manager.connection.subscriptions.remove(topic)
        return {"status": "success", "message": f"Unsubscribed from {topic}"}

    async def mock_publish(topic, message, qos=0, retain=False):
        manager.connection.client.publish(topic, message, qos, retain)
        return {"status": "success", "message": f"Message published to {topic}"}

    # WebSocket Methods
    async def mock_send_ws_message(message):
        """Asynchronous WebSocket message sender"""
        if hasattr(manager.connection, 'websocket'):
            ws = manager.connection.websocket
            if hasattr(ws, 'send_text'):
                try:
                    if isinstance(message, dict):
                        message = json.dumps(message)
                    await ws.send_text(message)
                    return True
                except Exception as e:
                    print(f"WebSocket send error: {str(e)}")
        return False

    async def mock_handle_message(client, userdata, message):
        """Asynchronous message handler"""
        if hasattr(manager.connection, 'websocket'):
            await mock_send_ws_message({
                'type': 'message',
                'topic': message.topic,
                'payload': message.payload.decode()
            })

    async def mock_handle_connect(client, userdata, flags, rc):
        """Asynchronous connect handler"""
        if hasattr(manager.connection, 'websocket'):
            await mock_send_ws_message({
                'type': 'status',
                'message': 'WebSocket connected successfully'
            })

    # Replace methods
    manager.connect = mock_connect
    manager.disconnect = mock_disconnect
    manager.subscribe = mock_subscribe
    manager.unsubscribe = mock_unsubscribe
    manager.publish = mock_publish

    manager._async_send_ws_message = mock_send_ws_message
    manager._handle_message = mock_handle_message
    manager._handle_connect = mock_handle_connect

    return manager


@pytest.fixture(autouse=True)
def mock_mqtt_dependencies(mqtt_test_manager, monkeypatch):
    """Replace the global MQTT manager with test version"""
    monkeypatch.setattr('app.api.routes.mqtt_manager', mqtt_test_manager)
    monkeypatch.setattr('app.api.websocket.mqtt_manager', mqtt_test_manager)


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )