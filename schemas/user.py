from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = UserRole.professional
    professional_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_professional_link(self):
        if self.role == UserRole.professional and self.professional_id is None:
            raise ValueError("professional_id é obrigatório para usuários profissionais")
        if self.role != UserRole.professional and self.professional_id is not None:
            raise ValueError("professional_id só pode ser usado com o papel professional")
        return self


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    professional_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    email: str
    role: UserRole
    professional_id: Optional[int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
