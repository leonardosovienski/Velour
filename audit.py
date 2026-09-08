import logging
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database import SessionLocal, tenant_scope
from models.audit_log import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Registra mutações HTTP sem armazenar corpo, token ou dados sensíveis."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return response

        # Record only identities actually authenticated by the request dependency.
        # Anonymous attempts remain visible in the structured request log.
        user_id = getattr(request.state, "user_id", None)
        tenant_id = getattr(request.state, "tenant_id", None)
        if user_id is None or tenant_id is None:
            return response

        db = SessionLocal()
        try:
            tenant_scope(db, tenant_id)
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
            logging.getLogger("velour.audit").exception("audit_write_failed")
        finally:
            db.close()
        return response
