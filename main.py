from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text

from auth import get_current_user
from database import engine, Base, SessionLocal
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
from birthday_scheduler import start_scheduler as start_birthday_scheduler
from reminder_scheduler import start_scheduler as start_reminder_scheduler
from config import settings
from audit import AuditMiddleware
from logging_config import setup_logging
from request_logging import RequestLoggingMiddleware

setup_logging()

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

settings.upload_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Velour — Sistema de Gestão para Salão Premium",
    description="API para gestão de clientes, agendamentos, fidelidade e indicações.",
    version="2.0.0",
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

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(clients_router)
app.include_router(professionals_router)
app.include_router(services_router)
app.include_router(products_router)
app.include_router(appointments_router)
app.include_router(loyalty_router)
app.include_router(referrals_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)

UPLOAD_ROOT = settings.upload_dir


@app.get("/uploads/{filename}", tags=["uploads"])
def get_upload(filename: str, _=Depends(get_current_user)):
    # Sanitiza contra path traversal: aceita só o componente de nome puro
    # (rejeita "../", separadores de diretório etc.) e confere que o
    # caminho resolvido continua dentro de UPLOAD_ROOT.
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    filepath = (UPLOAD_ROOT / safe_name).resolve()
    if not filepath.is_relative_to(UPLOAD_ROOT) or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(filepath)


@app.on_event("startup")
async def startup():
    if settings.scheduler_enabled:
        start_birthday_scheduler()
        start_reminder_scheduler()


@app.get("/health", tags=["health"])
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível") from exc
    return {"status": "ok", "system": "Velour", "environment": settings.environment}
