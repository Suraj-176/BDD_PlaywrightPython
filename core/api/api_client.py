import time
import requests
from core.logger.logger import logger
from helpers.retry import Retry

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def post(self, endpoint: str, body: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        logger.info("API POST Request initiated", {"url": url, "body": body})
        start_time = time.time()

        def _execute_post():
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=30
            )
            status = response.status_code
            try:
                data = response.json()
            except Exception:
                data = response.text

            return {"status": status, "data": data}

        response_data = Retry.execute(
            _execute_post,
            {"label": f"POST {endpoint}"}
        )

        duration_ms = (time.time() - start_time) * 1000.0
        logger.info("API POST Response received", {
            "duration": f"{duration_ms:.2f}ms",
            "status": response_data["status"],
        })

        return response_data

    def get(self, endpoint: str) -> dict:
        url = f"{f'{self.base_url}{endpoint}'}"
        logger.info("API GET Request initiated", {"url": url})
        start_time = time.time()

        def _execute_get():
            response = requests.get(
                url,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            status = response.status_code
            try:
                data = response.json()
            except Exception:
                data = response.text

            return {"status": status, "data": data}

        response_data = Retry.execute(
            _execute_get,
            {"label": f"GET {endpoint}"}
        )

        duration_ms = (time.time() - start_time) * 1000.0
        logger.info("API GET Response received", {
            "duration": f"{duration_ms:.2f}ms",
            "status": response_data["status"],
        })

        return response_data
