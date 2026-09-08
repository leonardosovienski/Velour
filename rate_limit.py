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
        self._last_cleanup = 0.0
        self.max_keys = 100_000

    def _prune(self, key: str, now: float) -> list[float]:
        if now - self._last_cleanup >= self.window_seconds:
            self._hits = defaultdict(list, {
                k: [t for t in hits if now - t < self.window_seconds]
                for k, hits in self._hits.items()
                if hits and now - hits[-1] < self.window_seconds
            })
            self._last_cleanup = now
        if key not in self._hits and len(self._hits) >= self.max_keys:
            raise HTTPException(status_code=429, detail=self.message,
                                headers={"Retry-After": str(self.window_seconds)})
        hits = self._hits[key]
        hits[:] = [t for t in hits if now - t < self.window_seconds]
        return hits

    def _check_hits(self, hits: list[float], now: float) -> None:
        if len(hits) >= self.max_attempts:
            retry = max(1, int(self.window_seconds - (now - hits[0])) + 1)
            raise HTTPException(status_code=429, detail=self.message,
                                headers={"Retry-After": str(retry)})

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._check_hits(self._prune(key, now), now)

    def record(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            hits = self._prune(key, now)
            if len(hits) < self.max_attempts:
                hits.append(now)

    def check_and_record(self, key: str) -> None:
        """Para endpoints onde toda chamada conta (não só falhas)."""
        with self._lock:
            now = time.monotonic()
            hits = self._prune(key, now)
            self._check_hits(hits, now)
            hits.append(now)


def request_key(request, current_user=None) -> str:
    ip = request.client.host if request.client else "unknown"
    if current_user is not None:
        return f"{ip}:{current_user.id}"
    return ip
