from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if settings.environment == "production":
            from runtime_guard import runtime_guard
            try:
                await run_in_threadpool(runtime_guard.check)
            except Exception:
                return JSONResponse({"detail": "Serviço temporariamente indisponível"}, status_code=503)
        # The reverse proxy also enforces this before buffering the body.
        length = request.headers.get("content-length")
        if length and (not length.isdecimal() or int(length) > 11 * 1024 * 1024):
            return JSONResponse({"detail": "Corpo da requisição excede o limite"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
