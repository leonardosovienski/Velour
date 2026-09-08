import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session

from database import get_db, tenant_scope
from models.tenant import Tenant
from models.user import User
from config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.jwt_algorithm
TOKEN_EXPIRE_MINUTES = settings.token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Hashing ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, key_hex = hashed.split(":", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


# ── JWT ────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, email: str, role: str, tenant_id: int | None = None, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire,
               "iat": datetime.now(timezone.utc), "tenant_id": tenant_id, "token_version": token_version}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        tenant_id = payload["tenant_id"]
        if user_id <= 0 or type(tenant_id) is not int or tenant_id <= 0:
            raise ValueError("Invalid token identity")
    except (PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    tenant_scope(db, tenant_id)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active == True).first()
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id, User.is_active == True).first()
    if not tenant or not user or payload.get("token_version") != user.token_version:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    request.state.user_id = user.id
    request.state.tenant_id = tenant.id
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """Dados financeiros e administrativos: apenas admin e gerente."""
    return require_admin(current_user)


def ensure_professional_scope(current_user: User, professional_id: int) -> None:
    if current_user.role == "professional":
        if current_user.professional_id is None:
            raise HTTPException(status_code=403, detail="Usuário profissional sem vínculo configurado")
        if current_user.professional_id != professional_id:
            raise HTTPException(status_code=403, detail="Acesso restrito ao próprio profissional")
