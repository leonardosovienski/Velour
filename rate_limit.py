"""Rate limiting em memória, por processo (threading.Lock + dict).

Adequado para como o projeto roda hoje (uvicorn sem --workers). Em um
deploy multi-worker/multi-processo cada worker teria sua própria janela —
não coordenam entre si. Para isso seria necessário um backend compartilhado
(ex.: Redis).
"""
import threading
import time
from collections import defaultdict

from fastapi import HTTPException


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int, message: str):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.message = message
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            hits[:] = [t for t in hits if now - t < self.window_seconds]
            if len(hits) >= self.max_attempts:
                raise HTTPException(status_code=429, detail=self.message)

    def record(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(time.monotonic())

    def check_and_record(self, key: str) -> None:
        """Para endpoints onde toda chamada conta (não só falhas)."""
        self.check(key)
        self.record(key)


def request_key(request, current_user=None) -> str:
    ip = request.client.host if request.client else "unknown"
    if current_user is not None:
        return f"{ip}:{current_user.id}"
    return ip
