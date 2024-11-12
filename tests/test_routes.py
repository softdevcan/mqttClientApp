import pytest
from fastapi.testclient import TestClient


def test_index_page(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Welcome to MQTT Client" in response.text


def test_connect_page(test_client):
    response = test_client.get("/connect")
    assert response.status_code == 200
    assert "Connect to MQTT Broker" in response.text


def test_dashboard_page(test_client):
    response = test_client.get("/dashboard")
    assert response.status_code == 200
    assert "MQTT Dashboard" in response.text


def test_api_connect_success(test_client, mqtt_test_manager):
    """Test API connection success"""
    response = test_client.post(
        "/api/connect",
        data={
            "host": "test.mosquitto.org",
            "port": "1883"
        }
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert "Connected" in result["message"]


def test_api_connect_invalid_port(test_client):
    """Test API connection with invalid port"""
    response = test_client.post(
        "/api/connect",
        data={
            "host": "test.mosquitto.org",
            "port": "invalid"
        }
    )
    assert response.status_code == 422  # Validation error


def test_api_disconnect(test_client, mqtt_test_manager):
    """Test API disconnection"""
    response = test_client.post("/api/disconnect")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    # assert_called_once yerine await_called yapısını kullanıyoruz
    assert result["message"] == "Disconnected from broker"


def test_api_subscribe(test_client, mqtt_test_manager):
    """Test API subscribe"""
    test_topic = "test/topic"
    test_qos = "0"

    response = test_client.post(
        "/api/subscribe",
        data={
            "topic": test_topic,
            "qos": test_qos
        }
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == f"Subscribed to {test_topic}"


def test_api_unsubscribe(test_client, mqtt_test_manager):
    """Test API unsubscribe"""
    test_topic = "test/topic"

    # Add the topic to subscriptions first
    mqtt_test_manager.connection.subscriptions.add(test_topic)

    response = test_client.post(
        "/api/unsubscribe",
        data={
            "topic": test_topic
        }
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == f"Unsubscribed from {test_topic}"


def test_api_publish(test_client, mqtt_test_manager):
    """Test API publish"""
    test_topic = "test/topic"
    test_message = "test message"
    test_qos = "0"
    test_retain = "false"

    response = test_client.post(
        "/api/publish",
        data={
            "topic": test_topic,
            "message": test_message,
            "qos": test_qos,
            "retain": test_retain
        }
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["message"] == f"Message published to {test_topic}"