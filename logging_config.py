"""Logging estruturado (JSON) para facilitar leitura em produção por
ferramentas de agregação de log (ex.: CloudWatch, Loki, Datadog) sem
depender de nenhum serviço externo específico.
"""
import json
import logging
import os
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Reduz verbosidade de acesso do uvicorn (já cobrimos requests no
    # RequestLoggingMiddleware, com mais contexto).
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def log_with_fields(logger: logging.Logger, level: int, message: str, **fields) -> None:
    logger.log(level, message, extra={"extra_fields": fields})


def now_ms() -> float:
    return time.perf_counter() * 1000
