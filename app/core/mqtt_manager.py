import functools
import time
from unittest.mock import Mock
import pytest
from ..models.mqtt_models import MQTTConnection, MQTTConnectionConfig
import paho.mqtt.client as mqtt
import asyncio
import logging
import threading
from typing import Optional, Dict, Any
import json


class MQTTManager:
    def __init__(self):
        self.connection = MQTTConnection()
        self._main_loop = None
        self._thread_local = threading.local()
        self._setup_logging()
        self._message_cache = set()
        self._last_published = None

    def _setup_logging(self):
        self.logger = logging.getLogger("mqtt_manager")
        self.logger.setLevel(logging.INFO)

    def _clear_old_messages(self):
        """Clear message cache periodically"""
        self._message_cache.clear()


    def _get_event_loop(self):
        if not hasattr(self._thread_local, 'loop'):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            self._thread_local.loop = loop
        return self._thread_local.loop

    def _wrap_callback(self, coro):
        @functools.wraps(coro)
        def wrapper(*args, **kwargs):
            if self._main_loop is None or not self._main_loop.is_running():
                self.logger.warning("Main event loop not available")
                return

            try:
                future = asyncio.run_coroutine_threadsafe(coro(*args, **kwargs), self._main_loop)
                future.result(timeout=5.0)  # 5 saniye timeout
            except Exception as e:
                self.logger.error(f"Callback error: {str(e)}")

        return wrapper

    def _should_process_message(self, topic: str, payload: str) -> bool:
        """Check if we should process this message based on recent publish history"""
        current_time = time.time()

        if self._last_published:
            last_topic, last_payload, timestamp = self._last_published

            # Eğer son 0.5 saniye içinde aynı mesaj publish edildiyse, işleme
            if (current_time - timestamp) < 0.5 and last_topic == topic and last_payload == payload:
                return False

        return True

    async def connect(self, config: MQTTConnectionConfig) -> Dict[str, Any]:
        try:
            self._main_loop = asyncio.get_running_loop()
            self._message_cache.clear()  # Bağlantı kurulduğunda cache'i temizle

            if self.connection.client:
                self.connection.client.disconnect()
                self.connection.client.loop_stop()

            client = mqtt.Client()
            client.on_message = self._handle_message
            client.on_connect = self._handle_connect
            client.on_disconnect = self._handle_disconnect

            if config.username and config.password:
                client.username_pw_set(config.username, config.password)

            client.connect(config.host, config.port)
            client.loop_start()

            self.connection.client = client
            self.connection.subscriptions.clear()
            return {"status": "success", "message": "Connected to MQTT broker"}
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_message(self, client, userdata, message):
        """Synchronous message handler"""
        if not self.connection.websocket or not self._main_loop:
            return

        try:
            topic = message.topic
            payload = message.payload.decode()

            # Eğer bu bizim gönderdiğimiz mesajsa, işleme alma
            if self._last_published and self._last_published[0] == topic and self._last_published[1] == payload:
                return

            # Sadece subscribe edilen mesajları işle
            if topic in self.connection.subscriptions:
                future = asyncio.run_coroutine_threadsafe(
                    self.connection.websocket.send_json({
                        'type': 'message',
                        'topic': topic,
                        'payload': payload
                    }),
                    self._main_loop
                )
                future.result(timeout=5.0)

        except Exception as e:
            self.logger.error(f"Message handling error: {str(e)}")

    def _handle_connect(self, client, userdata, flags, rc):
        """Synchronous connect handler"""
        if self.connection.websocket and self._main_loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._async_send_ws_message({
                        'type': 'status',
                        'message': 'Connected to MQTT broker'
                    }),
                    self._main_loop
                )
                future.result(timeout=5.0)
            except Exception as e:
                self.logger.error(f"Connect handling error: {str(e)}")

    def _handle_disconnect(self, client, userdata, rc):
        """Synchronous disconnect handler"""
        if self.connection.websocket and self._main_loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._async_send_ws_message({
                        'type': 'status',
                        'message': 'Disconnected from MQTT broker'
                    }),
                    self._main_loop
                )
                future.result(timeout=5.0)
            except Exception as e:
                self.logger.error(f"Disconnect handling error: {str(e)}")

    async def _async_send_ws_message(self, message: Dict):
        """Asynchronous websocket message sending"""
        if self.connection.websocket:
            try:
                # Mesajı tek bir formatta gönder
                final_message = {
                    'type': 'message',
                    'topic': message['topic'],
                    'payload': message['payload'],
                    'published': message.get('published', False)  # Published flag'i ekle
                }

                await self.connection.websocket.send_json(final_message)
            except Exception as e:
                self.logger.error(f"WebSocket send error: {str(e)}")

    async def disconnect(self) -> Dict[str, Any]:
        if self.connection.client:
            try:
                self.connection.client.disconnect()
                self.connection.client.loop_stop()
                self.connection.client = None
                self.connection.subscriptions.clear()
                self._main_loop = None  # Clear the main loop reference
                return {"status": "success", "message": "Disconnected from MQTT broker"}
            except Exception as e:
                self.logger.error(f"Disconnect error: {str(e)}")
                return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Not connected"}

    async def subscribe(self, topic: str, qos: int = 0) -> Dict[str, Any]:
        if not self.connection.client:
            return {"status": "error", "message": "Not connected to broker"}

        try:
            self.connection.client.subscribe(topic, qos)
            self.connection.subscriptions.add(topic)
            return {"status": "success", "message": f"Subscribed to {topic}"}
        except Exception as e:
            self.logger.error(f"Subscribe error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def unsubscribe(self, topic: str) -> Dict[str, Any]:
        if not self.connection.client:
            return {"status": "error", "message": "Not connected to broker"}

        try:
            self.connection.client.unsubscribe(topic)
            if topic in self.connection.subscriptions:
                self.connection.subscriptions.remove(topic)
            return {"status": "success", "message": f"Unsubscribed from {topic}"}
        except Exception as e:
            self.logger.error(f"Unsubscribe error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def publish(self, topic: str, message: str, qos: int = 0, retain: bool = False) -> Dict[str, Any]:
        if not self.connection.client:
            return {"status": "error", "message": "Not connected to broker"}

        try:
            # Son yayınlanan mesajı kaydet
            self._last_published = (topic, message, time.time())

            # MQTT üzerinden yayınla
            self.connection.client.publish(topic, message, qos, retain)

            # Sadece published mesajını WebSocket'e gönder
            if self.connection.websocket:
                await self.connection.websocket.send_json({
                    'type': 'message',
                    'topic': topic,
                    'payload': message,
                    'published': True
                })

            return {"status": "success", "message": "Message published"}
        except Exception as e:
            self.logger.error(f"Publish error: {str(e)}")
            return {"status": "error", "message": str(e)}




mqtt_manager = MQTTManager()