from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import create_access_token, verify_password, get_current_user
from database import get_db
from models.user import User
from schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token(user.id, user.email, user.role.value)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "name": user.name}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
