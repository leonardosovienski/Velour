"""Public onboarding and owner-authorized portable account export."""
import re
import secrets
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password
from config import settings
from database import get_db, system_scope
from models import (
    Appointment, AuditLog, Client, LoyaltyTransaction, Product, Professional,
    Referral, Service, ServiceCategory, ServiceRecipe, StockMovement, Tenant, User,
    UserRole,
)
from rate_limit import RateLimiter, request_key
from schemas.tenant import TenantSignup

router = APIRouter(prefix="/tenants", tags=["tenants"])
TRIAL_DAYS = 14
_signup_limiter = RateLimiter(5, 3600, "Muitos cadastros. Aguarde e tente novamente.")
_export_limiter = RateLimiter(3, 3600, "Muitas exportações. Aguarde e tente novamente.")


def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador do salão")
    return user


@router.get("/signup-config")
def signup_config():
    return {
        "signup_enabled": settings.signup_enabled,
        "trial_days": TRIAL_DAYS,
        "terms_url": settings.terms_url,
        "privacy_url": settings.privacy_url,
        "terms_version": settings.terms_version,
    }


@router.post("/signup", status_code=201)
def signup(data: TenantSignup, request: Request, db: Session = Depends(get_db)):
    if not settings.signup_enabled:
        raise HTTPException(status_code=503, detail="Novos cadastros temporariamente indisponíveis")
    _signup_limiter.check_and_record(request_key(request))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    email = str(data.admin_email).strip().lower()
    normalized = unicodedata.normalize("NFKD", data.tenant_name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:60] or "salao"
    # Signup is deliberately independent of Stripe availability. A customer is
    # created lazily when its owner first starts Checkout.
    with system_scope(db):
        if db.query(User.id).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="Não foi possível cadastrar este e-mail. Tente entrar ou recuperar a senha.")
        tenant = Tenant(
            name=data.tenant_name, slug=f"{slug}-{secrets.token_hex(6)}",
            is_active=True, subscription_status="trialing",
            trial_ends_at=now + timedelta(days=TRIAL_DAYS),
            accepted_terms_at=now, terms_version=settings.terms_version,
        )
        try:
            db.add(tenant)
            db.flush()
            user = User(
                tenant_id=tenant.id, name=data.admin_name, email=email,
                hashed_password=hash_password(data.admin_password),
                role=UserRole.admin, is_active=True, token_version=0,
            )
            db.add(user)
            db.flush()
            result = {
                "access_token": create_access_token(
                    user.id, user.email, user.role.value,
                    tenant_id=tenant.id, token_version=user.token_version,
                ),
                "token_type": "bearer", "role": user.role.value,
                "name": user.name, "professional_id": None, "tenant_id": tenant.id,
            }
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Não foi possível concluir o cadastro. Verifique os dados.") from exc
    return result


@router.get("/export")
def export_tenant(request: Request, user: User = Depends(require_owner), db: Session = Depends(get_db)):
    _export_limiter.check_and_record(request_key(request, user))
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).one()
    tables = (User, Client, Professional, ServiceCategory, Service, Product,
              ServiceRecipe, Appointment, StockMovement, LoyaltyTransaction, Referral, AuditLog)
    excluded = {"hashed_password", "token_version"}
    exported = {}
    for model in tables:
        columns = [c.key for c in inspect(model).columns if c.key not in excluded]
        rows = db.query(model).filter(model.tenant_id == tenant.id).order_by(model.id).all()
        exported[model.__tablename__] = [{column: getattr(row, column) for column in columns} for row in rows]
    return JSONResponse(
        content=jsonable_encoder({
            "format_version": 1, "exported_at": datetime.now(timezone.utc),
            "tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug},
            "data": exported,
            "attachments": "Campos de fotos contêm referências. Os arquivos autenticados podem ser baixados separadamente.",
        }),
        headers={"Content-Disposition": f'attachment; filename="velour-{tenant.slug}.json"', "Cache-Control": "no-store"},
    )
