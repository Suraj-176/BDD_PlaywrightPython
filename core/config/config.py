import os
import json
from dotenv import load_dotenv
from core.logger.logger import logger

load_dotenv()

class Config:
    _validated = False

    @classmethod
    def validate(cls) -> None:
        if cls._validated:
            return

        required_vars = []

        if os.getenv("ENABLE_AI_HEALING") == "true":
            required_vars.append("GROQ_API_KEY")

        if os.getenv("ENABLE_DB_VALIDATION") == "true":
            required_vars.extend(["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"])

        missing = [v for v in required_vars if not os.getenv(v)]

        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}\nCreate .env file from .env.example"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("✅ Environment validation successful")
        cls._validated = True

    # Application
    @property
    def environment(self) -> str:
        return os.getenv("TEST_ENV", "SIT")

    @property
    def base_url(self) -> str:
        # Load from config.json if not in env
        env_val = os.getenv("BASE_URL")
        if env_val:
            return env_val
        
        return self.get_base_url_from_config()

    def get_base_url_from_config(self) -> str:
        config_path = os.path.join("helpers", "testdata", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                env = self.environment
                if env in config_data and "url" in config_data[env]:
                    return config_data[env]["url"]
            except Exception as e:
                logger.warn(f"Failed to load URL from config.json: {e}")
        return "https://www.saucedemo.com/"

    @property
    def is_dev(self) -> bool:
        return self.environment == "DEV"

    @property
    def is_sit(self) -> bool:
        return self.environment == "SIT"

    @property
    def is_uat(self) -> bool:
        return self.environment == "UAT"

    @property
    def is_prod(self) -> bool:
        return self.environment == "PROD"

    # API
    @property
    def api_base_url(self) -> str:
        return os.getenv("API_BASE_URL", "http://localhost:3000/api")

    @property
    def api_timeout(self) -> int:
        return int(os.getenv("API_TIMEOUT", "30000"))

    @property
    def api_retries(self) -> int:
        return int(os.getenv("API_RETRIES", "3"))

    # Timeouts
    @property
    def timeouts(self) -> dict:
        return {
            "default": int(os.getenv("DEFAULT_TIMEOUT", "30000")),
            "navigation": int(os.getenv("NAVIGATION_TIMEOUT", "90000")),
            "action": int(os.getenv("ACTION_TIMEOUT", "10000")),
        }

    @property
    def max_retries(self) -> int:
        return int(os.getenv("MAX_RETRIES", "3"))

    # Logging
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def debug_mode(self) -> bool:
        return os.getenv("DEBUG_MODE") == "true"

    @property
    def log_file_path(self) -> str:
        return os.getenv("LOG_FILE_PATH", "logs/automation.log")

    # Database
    @property
    def database(self) -> dict:
        return {
            "host": os.getenv("DB_HOST", "localhost"),
        }
        
    @property
    def enable_ai_healing(self) -> bool:
        return os.getenv("ENABLE_AI_HEALING", "false").lower() == "true"

config = Config() # Instantiate the config once