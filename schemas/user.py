from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole = UserRole.professional


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
