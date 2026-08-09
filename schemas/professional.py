from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from models.professional import ProfGender


class ProfessionalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=50)
    email: Optional[str] = None
    gender: ProfGender
    photo_url: Optional[str] = None
    specialty: str = Field(min_length=2, max_length=300)
    bio: Optional[str] = None
    commission_rate: Decimal = Field(default=Decimal("0.40"), ge=0, le=1, decimal_places=4)
    monthly_goal: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)


class ProfessionalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, min_length=8, max_length=50)
    email: Optional[str] = None
    gender: Optional[ProfGender] = None
    photo_url: Optional[str] = None
    specialty: Optional[str] = Field(None, min_length=2, max_length=300)
    bio: Optional[str] = None
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4)
    monthly_goal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_active: Optional[bool] = None


class ProfessionalResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    gender: ProfGender
    photo_url: Optional[str]
    specialty: str
    bio: Optional[str]
    commission_rate: Decimal
    monthly_goal: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
