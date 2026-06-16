import os
import re
import json
import logging
from datetime import datetime

class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        # Map string to python logging level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        self.level = level_map.get(log_level_str, logging.INFO)
        self.logs_dir = os.getenv("LOGS_DIR", "logs")

        # Create logs directory if it doesn't exist
        os.makedirs(self.logs_dir, exist_ok=True)

        self.current_log_date = ""
        self.logger = logging.getLogger("ICICI_Pru_Automation")
        self.logger.setLevel(self.level)
        self.logger.propagate = False # Avoid duplicate logging to root logger

        self.file_handler = None
        self.stream_handler = None
        self._ensure_current_log_file()
        self.info(f"\n========== TEST RUN STARTED: {datetime.utcnow().isoformat()}Z ==========\n")

    def _get_date_string(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _ensure_current_log_file(self):
        today_str = self._get_date_string()

        if self.current_log_date != today_str:
            # Remove old file handler if exists
            if self.file_handler:
                self.logger.removeHandler(self.file_handler)
                self.file_handler.close()

            self.current_log_date = today_str
            log_file_path = os.path.join(self.logs_dir, f"automation-{today_str}.log")

            # Create file handler
            self.file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            self.file_handler.setLevel(self.level)
            file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
            self.file_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.file_handler)

            # Create stream handler (console)
            if not self.stream_handler:
                self.stream_handler = logging.StreamHandler()
                self.stream_handler.setLevel(self.level)
                console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
                self.stream_handler.setFormatter(console_formatter)
                self.logger.addHandler(self.stream_handler)

            self._clean_old_logs()

    def _clean_old_logs(self):
        try:
            retention_days = int(os.getenv("LOG_RETENTION_DAYS", "7"))
            now = datetime.now()
            cutoff_timestamp = now.timestamp() - (retention_days * 24 * 60 * 60)

            if not os.path.exists(self.logs_dir):
                return

            for filename in os.listdir(self.logs_dir):
                match = re.match(r"^automation-(\d{4}-\d{2}-\d{2})\.log$", filename)
                if match:
                    file_date_str = match.group(1)
                    try:
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                        if file_date.timestamp() < cutoff_timestamp:
                            full_path = os.path.join(self.logs_dir, filename)
                            os.remove(full_path)
                            print(f"[Logger Auto-Cleanup] Deleted expired log file: {filename}")
                    except Exception as e:
                        print(f"[Logger Auto-Cleanup Date Parse Error] {e}")
        except Exception as error:
            print(f"[Logger Auto-Cleanup Error] {error}")

    def _mask_sensitive_data(self, value):
        if value is None:
            return value

        if isinstance(value, str):
            # Mask PAN and numeric sequences (like card numbers)
            masked = re.sub(r'([A-Z]{5}[0-9]{4}[A-Z])', '***MASKED_PAN***', value)
            masked = re.sub(r'\b\d{12,19}\b', '***MASKED_NUMBER***', masked)
            return masked

        if isinstance(value, list):
            return [self._mask_sensitive_data(item) for item in value]

        if isinstance(value, dict):
            masked = {}
            for key, entry in value.items():
                if re.search(r'password|token|secret|authorization|api[_-]?key|pan|account|card|pin', key, re.IGNORECASE):
                    masked[key] = '***MASKED***'
                else:
                    masked[key] = self._mask_sensitive_data(entry)
            return masked

        return value

    def _format_data(self, data) -> str:
        if data is None:
            return ""
        try:
            masked_data = self._mask_sensitive_data(data)
            return f" | {json.dumps(masked_data)}"
        except Exception:
            return f" | {str(data)}"

    def debug(self, message: str, data=None):
        self._ensure_current_log_file()
        suffix = self._format_data(data)
        self.logger.debug(f"{message}{suffix}")

    def info(self, message: str, data=None):
        self._ensure_current_log_file()
        suffix = self._format_data(data)
        self.logger.info(f"{message}{suffix}")

    def warn(self, message: str, data=None):
        self._ensure_current_log_file()
        suffix = self._format_data(data)
        self.logger.warning(f"{message}{suffix}")

    def warning(self, message: str, data=None):
        self.warn(message, data)

    def error(self, message: str, data=None):
        self._ensure_current_log_file()
        suffix = self._format_data(data)
        self.logger.error(f"{message}{suffix}")

# Singleton instance
logger = Logger()
