import pytest
from app.models.mqtt_models import MQTTConnectionConfig

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_connect_success(mqtt_test_manager, mock_mqtt_client):
    """Test successful MQTT connection"""
    test_host = "test.mosquitto.org"
    test_port = 1883

    config = MQTTConnectionConfig(
        host=test_host,
        port=test_port
    )

    result = await mqtt_test_manager.connect(config)

    assert result["status"] == "success"
    assert f"Connected to {test_host}:{test_port}" in result["message"]
    mock_mqtt_client.connect.assert_called_once_with(test_host, test_port)
    mock_mqtt_client.loop_start.assert_called_once()


@pytest.mark.asyncio
async def test_connect_with_auth(mqtt_test_manager, mock_mqtt_client):
    """Test MQTT connection with authentication"""
    test_host = "test.mosquitto.org"
    test_port = 1883
    test_username = "testuser"
    test_password = "testpass"

    config = MQTTConnectionConfig(
        host=test_host,
        port=test_port,
        username=test_username,
        password=test_password
    )

    result = await mqtt_test_manager.connect(config)

    assert result["status"] == "success"
    mock_mqtt_client.username_pw_set.assert_called_once_with(test_username, test_password)
    mock_mqtt_client.connect.assert_called_once_with(test_host, test_port)


@pytest.mark.asyncio
async def test_connect_failure(mqtt_test_manager, mock_mqtt_client):
    """Test MQTT connection failure"""
    test_error = "Connection failed"
    mock_mqtt_client.connect.side_effect = Exception(test_error)

    config = MQTTConnectionConfig(
        host="invalid.host",
        port=1883
    )

    result = await mqtt_test_manager.connect(config)

    assert result["status"] == "error"
    assert test_error in str(result["message"])


@pytest.mark.asyncio
async def test_disconnect_success(mqtt_test_manager, mock_mqtt_client):
    """Test successful MQTT disconnection"""
    result = await mqtt_test_manager.disconnect()

    assert result["status"] == "success"
    assert "Disconnected from broker" in result["message"]
    mock_mqtt_client.disconnect.assert_called_once()
    mock_mqtt_client.loop_stop.assert_called_once()


@pytest.mark.asyncio
async def test_subscribe_success(mqtt_test_manager, mock_mqtt_client):
    """Test successful topic subscription"""
    test_topic = "test/topic"
    test_qos = 0

    result = await mqtt_test_manager.subscribe(test_topic, test_qos)

    assert result["status"] == "success"
    assert test_topic in result["message"]
    mock_mqtt_client.subscribe.assert_called_once_with(test_topic, test_qos)
    assert test_topic in mqtt_test_manager.connection.subscriptions


@pytest.mark.asyncio
async def test_unsubscribe_success(mqtt_test_manager, mock_mqtt_client):
    """Test successful topic unsubscription"""
    test_topic = "test/topic"
    # Pre-add topic to subscriptions
    mqtt_test_manager.connection.subscriptions.add(test_topic)

    result = await mqtt_test_manager.unsubscribe(test_topic)

    assert result["status"] == "success"
    assert test_topic in result["message"]
    mock_mqtt_client.unsubscribe.assert_called_once_with(test_topic)
    assert test_topic not in mqtt_test_manager.connection.subscriptions


@pytest.mark.asyncio
async def test_publish_success(mqtt_test_manager, mock_mqtt_client):
    """Test successful message publishing"""
    test_topic = "test/topic"
    test_message = "Test message"
    test_qos = 0
    test_retain = False

    result = await mqtt_test_manager.publish(test_topic, test_message, test_qos, test_retain)

    assert result["status"] == "success"
    assert test_topic in result["message"]
    mock_mqtt_client.publish.assert_called_once_with(
        test_topic,
        test_message,
        test_qos,
        test_retain
    )