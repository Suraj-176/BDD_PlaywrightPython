import time
from core.logger.logger import logger

class DatabaseClient:
    _is_connected = False

    @classmethod
    def connect(cls) -> None:
        if cls._is_connected:
            return
        logger.info("🔌 Connecting to enterprise Database Pool...")
        time.sleep(0.5) # mock network
        cls._is_connected = True
        logger.info("✅ Connected to database successfully (Mock Pool Active)")

    @classmethod
    def query(cls, sql: str, params: list = None) -> list:
        if params is None:
            params = []
        cls.connect()
        logger.debug("Executing DB query", {"sql": sql, "params": params})
        # Returns an empty list in mock mode
        return []

    @classmethod
    def disconnect(cls) -> None:
        if not cls._is_connected:
            return
        logger.info("🔌 Disconnecting from Database Pool...")
        cls._is_connected = False
        logger.info("✅ Disconnected from database successfully")
