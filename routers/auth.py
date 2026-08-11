from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import create_access_token, verify_password, get_current_user
from database import get_db
from models.user import User
from rate_limit import RateLimiter
from schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiting de login por (IP, e-mail): protege contra força bruta.
# Só conta tentativas com credenciais erradas — logins bem-sucedidos não
# consomem a cota.
_login_limiter = RateLimiter(
    max_attempts=5,
    window_seconds=300,  # 5 minutos
    message="Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
)


@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    rate_limit_key = f"{request.client.host if request.client else 'unknown'}:{form.username}"
    _login_limiter.check(rate_limit_key)

    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.hashed_password):
        _login_limiter.record(rate_limit_key)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token(user.id, user.email, user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "professional_id": user.professional_id,
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
