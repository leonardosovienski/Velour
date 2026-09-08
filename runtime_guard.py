"""Enforce the supported single API process deployment using PostgreSQL.

Business locks, rate limits and schedulers are process-local. A dedicated
database session holds this advisory lock for the entire application lifetime.
It prevents accidentally launching a second worker against the same database.
"""
from sqlalchemy import text
import threading

LOCK_KEY = 621742910135


class RuntimeGuard:
    def __init__(self):
        self.connection = None
        self._lock = threading.Lock()

    def acquire(self, engine):
        connection = engine.connect()
        try:
            acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY}
            ).scalar_one()
            connection.commit()
            if not acquired:
                raise RuntimeError("Outra API Velour está ativa neste banco. Use uma única réplica e um worker.")
            self.connection = connection
        except Exception:
            connection.close()
            raise

    def check(self):
        with self._lock:
            self._check()

    def _check(self):
        # A lost session loses the lock. Do not silently reconnect and serve
        # traffic with local locks while another instance may own the lock.
        if self.connection is None or self.connection.invalidated:
            raise RuntimeError("Lease da API indisponível")
        try:
            self.connection.execute(text("SELECT 1"))
            self.connection.commit()
        except Exception:
            self.connection.invalidate()
            raise

    def release(self):
        if self.connection is not None:
            try:
                if not self.connection.invalidated:
                    self.connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
                    self.connection.commit()
            finally:
                self.connection.close()
                self.connection = None


runtime_guard = RuntimeGuard()
