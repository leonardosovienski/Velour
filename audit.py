from jwt import decode, PyJWTError
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database import SessionLocal
from models.audit_log import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Registra mutações HTTP sem armazenar corpo, token ou dados sensíveis."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return response

        user_id = None
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            try:
                payload = decode(
                    authorization.split(" ", 1)[1],
                    settings.secret_key,
                    algorithms=[settings.jwt_algorithm],
                )
                user_id = int(payload["sub"])
            except (PyJWTError, KeyError, TypeError, ValueError):
                pass

        db = SessionLocal()
        try:
            db.add(AuditLog(
                user_id=user_id,
                action=request.method,
                resource=request.url.path,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None,
            ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return response
