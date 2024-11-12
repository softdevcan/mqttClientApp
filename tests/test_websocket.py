import json
from unittest.mock import MagicMock

import pytest

@pytest.mark.asyncio
async def test_websocket_connection(test_client):
    """Test WebSocket connection"""
    with test_client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "status"
        assert "WebSocket connected successfully" in data["message"]


@pytest.mark.asyncio
async def test_websocket_mqtt_message(mqtt_test_manager):
    """Test MQTT message received through WebSocket"""
    mock_message = MagicMock()
    mock_message.topic = 'test/topic'
    mock_message.payload = b'test message'

    await mqtt_test_manager._handle_message(None, None, mock_message)

    ws = mqtt_test_manager.connection.websocket
    assert len(ws.sent_messages) > 0
    sent_message = json.loads(ws.sent_messages[-1])
    assert sent_message["type"] == "message"
    assert sent_message["topic"] == "test/topic"
    assert sent_message["payload"] == "test message"


@pytest.mark.asyncio
async def test_websocket_status_message(mqtt_test_manager):
    """Test status message received through WebSocket"""
    await mqtt_test_manager._handle_connect(None, None, None, 0)

    ws = mqtt_test_manager.connection.websocket
    assert len(ws.sent_messages) > 0
    sent_message = json.loads(ws.sent_messages[-1])
    assert sent_message["type"] == "status"
    assert "connected" in sent_message["message"].lower()  # Case-insensitive check for any form of "connected"