from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text

from auth import get_current_user, ensure_professional_scope
from database import engine, Base, SessionLocal, get_db, system_scope
from sqlalchemy.orm import Session
from models.appointment import Appointment
from models.user import User
import models  # noqa: F401 — registra todos os modelos no metadata

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.clients import router as clients_router
from routers.professionals import router as professionals_router
from routers.services import router as services_router
from routers.products import router as products_router
from routers.appointments import router as appointments_router
from routers.loyalty import router as loyalty_router
from routers.referrals import router as referrals_router
from routers.dashboard import router as dashboard_router
from routers.reports import router as reports_router
from routers.audit_logs import router as audit_logs_router
from routers.tenants import router as tenants_router
from routers.billing import router as billing_router, require_active_subscription
from routers.account_recovery import router as account_recovery_router
from birthday_scheduler import start_scheduler as start_birthday_scheduler
from reminder_scheduler import start_scheduler as start_reminder_scheduler
from config import settings
from audit import AuditMiddleware
from logging_config import setup_logging
from request_logging import RequestLoggingMiddleware
from security_headers import SecurityHeadersMiddleware
from runtime_guard import runtime_guard


@asynccontextmanager
async def lifespan(app):
    if settings.environment == "production":
        runtime_guard.acquire(engine)
    try:
        if settings.scheduler_enabled:
            start_birthday_scheduler()
            start_reminder_scheduler()
        yield
    finally:
        from birthday_scheduler import scheduler as birthday_scheduler
        from reminder_scheduler import scheduler as reminder_scheduler
        for scheduler in (birthday_scheduler, reminder_scheduler):
            if scheduler.running:
                scheduler.shutdown(wait=False)
        if settings.environment == "production":
            runtime_guard.release()

setup_logging()

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

settings.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Velour — Sistema de Gestão para Salão Premium",
    description="API para gestão de clientes, agendamentos, fidelidade e indicações.",
    version="3.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router)
app.include_router(tenants_router)
app.include_router(billing_router)
app.include_router(account_recovery_router)
for business_router in (
    users_router, clients_router, professionals_router, services_router,
    products_router, appointments_router, loyalty_router, referrals_router,
    dashboard_router, reports_router, audit_logs_router,
):
    app.include_router(business_router, dependencies=[Depends(require_active_subscription)])

UPLOAD_ROOT = settings.upload_dir


@app.get("/uploads/{filename}", tags=["uploads"])
def get_upload(filename: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Sanitiza contra path traversal: aceita só o componente de nome puro
    # (rejeita "../", separadores de diretório etc.) e confere que o
    # caminho resolvido continua dentro de UPLOAD_ROOT.
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    filepath = (UPLOAD_ROOT / safe_name).resolve()
    if not filepath.is_relative_to(UPLOAD_ROOT) or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    photo_url = f"/uploads/{safe_name}"
    appointment = db.query(Appointment).filter(
        (Appointment.photo_before_url == photo_url) | (Appointment.photo_after_url == photo_url)
    ).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    ensure_professional_scope(current_user, appointment.professional_id)
    return FileResponse(filepath, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@app.get("/health", tags=["health"])
def health():
    try:
        with SessionLocal() as db, system_scope(db):
            db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível") from exc
    return {"status": "ok", "system": "Velour", "environment": settings.environment}
