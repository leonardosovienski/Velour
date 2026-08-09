from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin, hash_password
from database import get_db
from models.user import User, UserRole
from models.professional import Professional
from schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(User).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    if body.professional_id is not None:
        professional = db.query(Professional).filter(Professional.id == body.professional_id, Professional.is_active == True).first()
        if not professional:
            raise HTTPException(status_code=422, detail="Profissional inválido ou inativo")
        if db.query(User).filter(User.professional_id == body.professional_id).first():
            raise HTTPException(status_code=409, detail="Profissional já possui usuário")
    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        professional_id=body.professional_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    changes = body.model_dump(exclude_unset=True)
    next_role = changes.get("role", user.role)
    next_professional_id = changes.get("professional_id", user.professional_id)
    if next_role == UserRole.professional and next_professional_id is None:
        raise HTTPException(status_code=422, detail="professional_id é obrigatório para usuários profissionais")
    if next_role != UserRole.professional:
        changes["professional_id"] = None
    if next_professional_id is not None:
        professional = db.query(Professional).filter(
            Professional.id == next_professional_id,
            Professional.is_active == True,
        ).first()
        if not professional:
            raise HTTPException(status_code=422, detail="Profissional inválido ou inativo")
        duplicate = db.query(User).filter(User.professional_id == next_professional_id, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Profissional já possui usuário")
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
