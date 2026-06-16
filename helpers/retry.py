import time
import math
from core.logger.logger import logger

class Retry:
    @staticmethod
    def execute(fn, options: dict = None):
        if options is None:
            options = {}
            
        max_attempts = options.get("maxAttempts", 3)
        delay_ms = options.get("delayMs", 1000)
        label = options.get("label", "Operation")
        exponential_backoff = options.get("exponentialBackoff", True)

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"[Attempt {attempt}/{max_attempts}] {label}")
                return fn()
            except Exception as error:
                last_error = error
                logger.warn(f"[Attempt {attempt}/{max_attempts}] {label} failed: {str(error)}")

                if attempt < max_attempts:
                    delay = (delay_ms * math.pow(2, attempt - 1)) if exponential_backoff else delay_ms
                    logger.debug(f"Retrying in {delay}ms...")
                    time.sleep(delay / 1000.0)

        raise RuntimeError(f"{label} failed after {max_attempts} attempts: {str(last_error)}")


# ========== PERFORMANCE MONITORING ==========

class PerformanceMonitor:
    _measurements = {}

    @classmethod
    def start_timer(cls, label: str):
        start_time = time.time()
        
        def end_timer() -> float:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000.0
            cls.record_measurement(label, duration_ms)
            return duration_ms
            
        return end_timer

    @classmethod
    def record_measurement(cls, label: str, duration_ms: float) -> None:
        if label not in cls._measurements:
            cls._measurements[label] = []
        cls._measurements[label].append(duration_ms)
        logger.debug(f"⏱️ {label}: {duration_ms:.2f}ms")

    @classmethod
    def get_stats(cls, label: str) -> dict:
        measurements = cls._measurements.get(label)
        if not measurements:
            return None

        sorted_m = sorted(measurements)
        total = sum(measurements)
        count = len(measurements)
        return {
            "count": count,
            "min": sorted_m[0],
            "max": sorted_m[-1],
            "avg": total / count,
            "total": total,
        }

    @classmethod
    def get_all_stats(cls) -> dict:
        stats = {}
        for label in cls._measurements:
            stats[label] = cls.get_stats(label)
        return stats

    @classmethod
    def print_report(cls) -> None:
        logger.info("📊 Performance Report")
        stats = cls.get_all_stats()
        for label, data in stats.items():
            if data:
                logger.info(f"{label}:", {
                    "count": data["count"],
                    "min": f"{data['min']:.2f}ms",
                    "max": f"{data['max']:.2f}ms",
                    "avg": f"{data['avg']:.2f}ms",
                    "total": f"{data['total']:.2f}ms",
                })

    @classmethod
    def reset(cls) -> None:
        cls._measurements.clear()


# ========== SLA VALIDATOR ==========

class SLAValidator:
    def __init__(self, slas: dict = None):
        self.slas = slas if slas is not None else {}

    def add_sla(self, operation: str, max_time_ms: float) -> None:
        self.slas[operation] = max_time_ms

    def validate_sla(self, operation: str, fn):
        end_timer = PerformanceMonitor.start_timer(operation)
        result = fn()
        duration = end_timer()

        sla = self.slas.get(operation)
        violated = (duration > sla) if sla else False

        status_str = "❌ VIOLATED" if violated else "✅ OK"
        logger.info(f"⏱️ SLA Check: {operation}", {
            "duration": f"{duration:.2f}ms",
            "sla": f"{sla:.2f}ms" if sla else "Not set",
            "status": status_str,
        })

        if violated:
            raise AssertionError(f"SLA VIOLATION: {operation} took {duration:.2f}ms (max allowed: {sla:.2f}ms)")

        return {"result": result, "duration": duration, "violated": False}
