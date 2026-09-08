from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, NaiveDatetime

from models.appointment import AppointmentStatus, PaymentMethod
from models.client import LoyaltyTier
from schemas.client import ClientResponse
from schemas.professional import ProfessionalResponse
from schemas.service import ServiceResponse
from schemas.numbers import JsonDecimal


class AppointmentCreate(BaseModel):
    client_id: int
    professional_id: int
    service_id: int
    scheduled_at: NaiveDatetime = Field(description="Horário local do salão, sem Z ou offset de fuso horário")
    occasion: Optional[str] = None
    notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class RecipeOverride(BaseModel):
    """Ajuste da quantidade real de insumo consumida no fechamento."""
    product_id: int
    actual_qty: float = Field(ge=0)


class AppointmentComplete(BaseModel):
    price_charged: Decimal = Field(ge=0, decimal_places=2)
    discount_points_used: int = Field(default=0, ge=0)
    photo_before_url: Optional[str] = None
    photo_after_url: Optional[str] = None
    formula_used: Optional[str] = None
    notes: Optional[str] = None
    recipe_overrides: Optional[List[RecipeOverride]] = None
    paid: bool = False
    amount_paid: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    payment_method: Optional[PaymentMethod] = None


class AppointmentResponse(BaseModel):
    id: int
    client_id: int
    professional_id: int
    service_id: int
    scheduled_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    occasion: Optional[str]
    notes: Optional[str]
    photo_before_url: Optional[str]
    photo_after_url: Optional[str]
    formula_used: Optional[str]
    points_awarded: int
    price_charged: Optional[JsonDecimal]
    discount_points_used: int
    tier_at_service: Optional[LoyaltyTier]
    tier_discount_amount: JsonDecimal
    paid: bool
    amount_paid: Optional[JsonDecimal]
    payment_method: Optional[PaymentMethod]
    created_at: datetime

    model_config = {"from_attributes": True}


class AppointmentDetail(AppointmentResponse):
    """Resposta expandida com dados de client, profissional e serviço."""
    client: Optional[ClientResponse]
    professional: Optional[ProfessionalResponse]
    service: Optional[ServiceResponse]

    model_config = {"from_attributes": True}
