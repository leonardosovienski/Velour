import logging

from jwt import decode, PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from logging_config import log_with_fields, now_ms

logger = logging.getLogger("velour.request")


def _user_id_from_request(request) -> int | None:
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None
    try:
        payload = decode(
            authorization.split(" ", 1)[1],
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (PyJWTError, KeyError, TypeError, ValueError):
        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Loga cada requisição (método, rota, status, duração) em JSON.
    Não loga corpo, query string ou headers — só metadados de tráfego."""

    async def dispatch(self, request, call_next):
        start = now_ms()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(now_ms() - start, 2)
            log_with_fields(
                logger, logging.ERROR, "unhandled_exception",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                user_id=_user_id_from_request(request),
            )
            raise

        duration_ms = round(now_ms() - start, 2)
        level = logging.ERROR if response.status_code >= 500 else (
            logging.WARNING if response.status_code >= 400 else logging.INFO
        )
        log_with_fields(
            logger, level, "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=_user_id_from_request(request),
        )
        return response
