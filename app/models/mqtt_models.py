from pydantic import BaseModel
from typing import Optional, List, Set
from dataclasses import dataclass
import paho.mqtt.client as mqtt
from fastapi import WebSocket


class MQTTConnectionConfig(BaseModel):
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class MQTTPublishMessage(BaseModel):
    topic: str
    message: str
    qos: int = 0
    retain: bool = False


class MQTTSubscription(BaseModel):
    topic: str
    qos: int = 0


@dataclass
class MQTTConnection:
    client: mqtt.Client
    subscriptions: Set[str]
    websocket: Optional[WebSocket] = None

    def __init__(self):
        self.subscriptions = set()
        self.client = None