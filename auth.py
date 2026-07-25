import hashlib
import os
import secrets
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

load_dotenv()

# Lidos de variáveis de ambiente; fallback para valores de desenvolvimento.
SECRET_KEY = os.getenv("SECRET_KEY", "velour-secret-key-salao-premium-2026")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))  # 8 horas

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

def create_access_token(user_id: int, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user
