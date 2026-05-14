from collections import deque
from threading import Lock
from time import time
from typing import Dict, Any


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._start_time = time()
        self._total_requests = 0
        self._total_errors = 0
        self._total_response_time_ms = 0.0
        self._per_endpoint: Dict[str, Dict[str, float]] = {}
        self._recent_errors = deque(maxlen=25)

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float, error: str = None) -> None:
        key = f"{method} {path}"
        with self._lock:
            self._total_requests += 1
            self._total_response_time_ms += duration_ms

            if key not in self._per_endpoint:
                self._per_endpoint[key] = {"count": 0, "error_count": 0, "total_ms": 0.0}

            endpoint = self._per_endpoint[key]
            endpoint["count"] += 1
            endpoint["total_ms"] += duration_ms

            if status_code >= 400:
                self._total_errors += 1
                endpoint["error_count"] += 1
                if error:
                    self._recent_errors.appendleft({
                        "timestamp": time(),
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "error": error,
                    })

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            avg_ms = (
                self._total_response_time_ms / self._total_requests
                if self._total_requests
                else 0.0
            )
            endpoints = {}
            for key, data in self._per_endpoint.items():
                count = data["count"]
                endpoints[key] = {
                    "count": count,
                    "error_count": data["error_count"],
                    "avg_response_ms": (data["total_ms"] / count) if count else 0.0,
                }

            return {
                "uptime_seconds": round(time() - self._start_time, 2),
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "avg_response_ms": round(avg_ms, 2),
                "endpoints": endpoints,
                "recent_errors": list(self._recent_errors),
            }


metrics = Metrics()
