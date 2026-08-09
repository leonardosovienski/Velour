from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import Numeric

from auth import ensure_professional_scope
from models.appointment import Appointment
from models.client import Client
from models.product import Product
from models.service import Service
from models.user import User, UserRole
from schemas.user import UserCreate


def test_professional_user_requires_professional_link():
    with pytest.raises(ValidationError):
        UserCreate(name="Profissional", email="p@example.com", password="123456789012", role=UserRole.professional)


def test_manager_cannot_receive_professional_link():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Gerente",
            email="g@example.com",
            password="123456789012",
            role=UserRole.manager,
            professional_id=1,
        )


def test_professional_scope_rejects_other_professional():
    user = User(role=UserRole.professional, professional_id=10)
    with pytest.raises(HTTPException) as exc:
        ensure_professional_scope(user, 11)
    assert exc.value.status_code == 403


def test_manager_can_access_any_professional():
    user = User(role=UserRole.manager)
    ensure_professional_scope(user, 999)


@pytest.mark.parametrize(
    "column,scale",
    [
        (Service.price, 2),
        (Appointment.price_charged, 2),
        (Appointment.tier_discount_amount, 2),
        (Client.total_spent, 2),
        (Product.cost_per_unit, 4),
    ],
)
def test_money_columns_use_fixed_precision(column, scale):
    assert isinstance(column.type, Numeric)
    assert column.type.scale == scale


def test_decimal_keeps_cent_precision():
    assert Decimal("0.10") + Decimal("0.20") == Decimal("0.30")
