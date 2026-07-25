from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field

from models.client import Gender, LoyaltyTier, ChatPreference


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=50)
    email: Optional[str] = None
    gender: Gender
    birthdate: Optional[date] = None
    photo_url: Optional[str] = None
    preferred_drink: Optional[str] = None
    music_preference: Optional[str] = None
    temperature_preference: Optional[str] = None
    chat_preference: ChatPreference = ChatPreference.neutral
    allergies: Optional[str] = None
    notes: Optional[str] = None
    referral_code_used: Optional[str] = None  # código de indicação de quem indicou


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, min_length=8, max_length=50)
    email: Optional[str] = None
    gender: Optional[Gender] = None
    birthdate: Optional[date] = None
    photo_url: Optional[str] = None
    preferred_drink: Optional[str] = None
    music_preference: Optional[str] = None
    temperature_preference: Optional[str] = None
    chat_preference: Optional[ChatPreference] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    code: str
    name: str
    phone: str
    email: Optional[str]
    gender: Gender
    birthdate: Optional[date]
    first_visit: date
    photo_url: Optional[str]
    preferred_drink: Optional[str]
    music_preference: Optional[str]
    temperature_preference: Optional[str]
    chat_preference: ChatPreference
    allergies: Optional[str]
    notes: Optional[str]
    loyalty_points: int
    loyalty_tier: LoyaltyTier
    total_spent: float
    total_visits: int
    referral_code: str
    referred_by_id: Optional[int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LastAppointmentBrief(BaseModel):
    date: datetime
    professional_name: str
    service_name: str
    formula_used: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class ClientBriefing(BaseModel):
    """Dados completos para briefing pré-atendimento."""
    id: int
    code: str
    name: str
    loyalty_tier: LoyaltyTier
    loyalty_points: int
    total_spent: float
    total_visits: int
    first_visit: date
    preferred_drink: Optional[str]
    music_preference: Optional[str]
    temperature_preference: Optional[str]
    chat_preference: ChatPreference
    allergies: Optional[str]
    notes: Optional[str]
    last_appointment: Optional[LastAppointmentBrief]
    spent_to_next_tier: Optional[float]  # quanto falta para próximo tier

    model_config = {"from_attributes": True}
