from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from models.service import GenderTarget


class ServiceCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    gender_target: GenderTarget = GenderTarget.all
    icon: Optional[str] = None


class ServiceCategoryResponse(BaseModel):
    id: int
    name: str
    gender_target: GenderTarget
    icon: Optional[str]

    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None
    duration_minutes: int = Field(gt=0)
    price: float = Field(ge=0)
    points_reward: int = Field(default=0, ge=0)


class ServiceUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, ge=0)
    points_reward: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    category_id: int
    category: Optional[ServiceCategoryResponse]
    name: str
    description: Optional[str]
    duration_minutes: int
    price: float
    points_reward: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
