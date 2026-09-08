from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from auth import get_current_user, require_admin, hash_password
from database import get_db
from domain_locks import serialized_mutation
from models.user import User, UserRole
from models.professional import Professional
from schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(User).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    if body.role == UserRole.admin and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Somente o proprietário pode criar administradores")
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
        email=str(body.email).strip().lower(),
        hashed_password=hash_password(body.password),
        role=body.role,
        professional_id=body.professional_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="E-mail ou profissional já cadastrado")
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
@serialized_mutation
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    changes = body.model_dump(exclude_unset=True)
    if any(changes.get(field) is None for field in ("name", "role", "is_active") if field in changes):
        raise HTTPException(status_code=422, detail="Nome, papel e situação não podem ser nulos")
    if (user.role == UserRole.admin or changes.get("role") == UserRole.admin) and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Somente o proprietário pode alterar administradores")
    removing_admin = user.role == UserRole.admin and (changes.get("role", user.role) != UserRole.admin or changes.get("is_active") is False)
    if removing_admin and db.query(User).filter(User.role == UserRole.admin, User.is_active == True, User.id != user.id).count() == 0:
        raise HTTPException(status_code=409, detail="Mantenha pelo menos um administrador ativo")
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
    if {"role", "is_active", "professional_id"}.intersection(changes):
        user.token_version += 1
    db.commit()
    db.refresh(user)
    return user
