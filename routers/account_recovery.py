"""One-time password recovery with hashed tokens and session revocation."""
import hashlib
import secrets
import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.orm import Session

from account_email import send_password_reset
from auth import hash_password
from config import settings
from database import get_db, system_scope
from email_service import is_configured
from models import PasswordResetToken, Tenant, User
from rate_limit import RateLimiter, request_key
from schemas.tenant import ForgotPassword, ResetPassword

router = APIRouter(prefix="/auth", tags=["auth"])
_recovery_lock = threading.RLock()
_recovery_limiter = RateLimiter(5, 900, "Muitas solicitações. Aguarde alguns minutos.")
_email_limiter = RateLimiter(3, 3600, "Muitas solicitações. Aguarde alguns minutos.")
_reset_limiter = RateLimiter(10, 900, "Muitas tentativas. Aguarde alguns minutos.")
RECOVERY_MESSAGE = "Se o e-mail estiver cadastrado, enviaremos um link para redefinir sua senha."


@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    _recovery_limiter.check_and_record(request_key(request))
    email_key = hashlib.sha256(str(data.email).lower().encode()).hexdigest()
    _email_limiter.check_and_record(email_key)
    if not is_configured():
        raise HTTPException(status_code=503, detail="Recuperação por e-mail temporariamente indisponível. Contate o suporte.")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with _recovery_lock, system_scope(db):
        user = db.query(User).join(Tenant, Tenant.id == User.tenant_id).filter(
            User.email == str(data.email).lower(), User.is_active.is_(True), Tenant.is_active.is_(True),
        ).with_for_update().first()
        if user:
            token = secrets.token_urlsafe(32)
            db.execute(update(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None),
            ).values(used_at=now))
            db.add(PasswordResetToken(
                tenant_id=user.tenant_id, user_id=user.id,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=now + timedelta(minutes=settings.password_reset_expire_minutes),
            ))
            email, name = user.email, user.name
            db.commit()
            background.add_task(send_password_reset, email, name, token)
    return {"message": RECOVERY_MESSAGE}


@router.post("/reset-password")
def reset_password(data: ResetPassword, request: Request, db: Session = Depends(get_db)):
    _reset_limiter.check_and_record(request_key(request))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    digest = hashlib.sha256(data.token.encode()).hexdigest()
    with _recovery_lock, system_scope(db):
        reset = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == digest,
            PasswordResetToken.used_at.is_(None), PasswordResetToken.expires_at > now,
        ).first()
        if not reset:
            raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite outro link.")
        # Always lock User before updating reset records, matching issuance's
        # lock order and avoiding reset/issuance deadlocks in PostgreSQL.
        user = db.query(User).join(Tenant, Tenant.id == User.tenant_id).filter(
            User.id == reset.user_id, User.tenant_id == reset.tenant_id,
            User.is_active.is_(True), Tenant.is_active.is_(True),
        ).with_for_update().first()
        if not user:
            raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite outro link.")
        # The conditional write also prevents concurrent reuse on SQLite, whose
        # SELECT FOR UPDATE is a no-op.
        consumed = db.execute(update(PasswordResetToken).where(
            PasswordResetToken.id == reset.id, PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        ).values(used_at=now))
        if consumed.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=400, detail="Link inválido ou expirado. Solicite outro link.")
        user.hashed_password = hash_password(data.new_password)
        user.token_version += 1
        db.execute(update(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None),
        ).values(used_at=now))
        db.commit()
    return {"message": "Senha alterada. Entre novamente com sua nova senha."}
