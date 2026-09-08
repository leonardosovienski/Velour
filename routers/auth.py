from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import create_access_token, verify_password, get_current_user
from database import get_db, system_scope
from models.tenant import Tenant
from models.user import User
from rate_limit import RateLimiter
from schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiting de login por (IP, e-mail): protege contra força bruta.
# Todas as tentativas consomem a cota, inclusive logins bem-sucedidos.
_login_limiter = RateLimiter(
    max_attempts=5,
    window_seconds=300,  # 5 minutos
    message="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
)
_login_ip_limiter = RateLimiter(max_attempts=30, window_seconds=300,
    message="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.")


@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    email = form.username.strip().lower()
    _login_ip_limiter.check_and_record(ip)
    _login_limiter.check_and_record(f"{ip}:{email}")
    with system_scope(db):
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        if not user or not verify_password(form.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id, Tenant.is_active == True).first()
        if not tenant:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        token = create_access_token(user.id, user.email, user.role.value,
                                    tenant_id=user.tenant_id, token_version=user.token_version)
        return {
            "access_token": token, "token_type": "bearer", "role": user.role,
            "name": user.name, "professional_id": user.professional_id, "tenant_id": user.tenant_id,
        }


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
