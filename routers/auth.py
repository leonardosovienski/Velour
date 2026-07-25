import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import create_access_token, verify_password, get_current_user
from database import get_db
from models.user import User
from schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiting de login em memória, por (IP, e-mail): protege contra força
# bruta em processo único. Só conta tentativas com credenciais erradas —
# logins bem-sucedidos não consomem a cota.
_RATE_LIMIT_MAX_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutos
_rate_limit_lock = threading.Lock()
_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _enforce_login_rate_limit(key: str):
    now = time.monotonic()
    with _rate_limit_lock:
        attempts = _failed_attempts[key]
        attempts[:] = [t for t in attempts if now - t < _RATE_LIMIT_WINDOW_SECONDS]
        if len(attempts) >= _RATE_LIMIT_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
            )


def _record_failed_login(key: str):
    with _rate_limit_lock:
        _failed_attempts[key].append(time.monotonic())


@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    rate_limit_key = f"{request.client.host if request.client else 'unknown'}:{form.username}"
    _enforce_login_rate_limit(rate_limit_key)

    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.hashed_password):
        _record_failed_login(rate_limit_key)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token(user.id, user.email, user.role.value)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "name": user.name}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
