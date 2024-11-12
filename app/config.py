from pydantic import BaseModel
from functools import lru_cache
import os


class Settings(BaseModel):
    APP_NAME: str = "MQTT Client"
    DEBUG_MODE: bool = True

    # MQTT default settings
    DEFAULT_HOST: str = "localhost"
    DEFAULT_PORT: int = 1883

    def load_env(self):
        """Load environment variables"""
        self.APP_NAME = os.getenv("APP_NAME", self.APP_NAME)

        # DEBUG_MODE için düzeltme
        debug_env = os.getenv("DEBUG_MODE")
        if debug_env is not None:
            self.DEBUG_MODE = debug_env.lower() == "true"

        self.DEFAULT_HOST = os.getenv("DEFAULT_MQTT_HOST", self.DEFAULT_HOST)
        self.DEFAULT_PORT = int(os.getenv("DEFAULT_MQTT_PORT", self.DEFAULT_PORT))
        return self


@lru_cache()
def get_settings():
    return Settings().load_env()


settings = get_settings()