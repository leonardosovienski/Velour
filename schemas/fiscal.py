import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from schemas.numbers import JsonDecimal


def validate_tax_id(value: str) -> str:
    if re.search(r"[^0-9./\-\s]", value):
        raise ValueError("Informe CPF ou CNPJ numérico")
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14) or len(set(digits)) == 1:
        raise ValueError("CPF/CNPJ inválido")
    base = digits[:-2]
    weights = ([10, 9, 8, 7, 6, 5, 4, 3, 2] if len(digits) == 11
               else [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    for attempt in range(2):
        total = sum(int(n) * w for n, w in zip(base, weights))
        remainder = total % 11
        base += str(0 if remainder < 2 else 11 - remainder)
        weights = ([11, 10, 9, 8, 7, 6, 5, 4, 3, 2] if len(digits) == 11
                   else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if base != digits:
        raise ValueError("Dígitos verificadores do CPF/CNPJ inválidos")
    return digits


class FiscalParty(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    legal_name: str = Field(min_length=2, max_length=150)
    tax_id: str = Field(min_length=11, max_length=20)
    email: EmailStr | None = None
    street: str = Field(min_length=2, max_length=120)
    number: str = Field(min_length=1, max_length=20)
    district: str = Field(min_length=2, max_length=60)
    postal_code: str = Field(pattern=r"^\d{8}$")
    city: str = Field(min_length=2, max_length=60)
    municipality_code: str = Field(pattern=r"^\d{7}$")
    state: str = Field(pattern=r"^(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)$")

    _tax_id = field_validator("tax_id")(validate_tax_id)


class FiscalProfileData(FiscalParty):
    municipal_registration: str = Field(default="", max_length=30)
    tax_regime: Literal["mei", "simples", "normal"]
    service_code: str = Field(pattern=r"^\d{6}$")
    iss_rate: Decimal = Field(ge=0, le=5, max_digits=3, decimal_places=2)


class FiscalDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    competence: date
    description: str = Field(min_length=5, max_length=2000)
    service_code: str = Field(pattern=r"^\d{6}$")
    iss_rate: Decimal = Field(ge=0, le=5, max_digits=3, decimal_places=2)
    recipient: FiscalParty


class AppointmentFiscalDraft(FiscalDraft):
    appointment_id: int = Field(gt=0)


class SubscriptionFiscalDraft(FiscalDraft):
    tenant_id: int = Field(gt=0)
    subscription_reference: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class FiscalCancellation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=15, max_length=300)


class FiscalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    issuer_kind: Literal["salon", "platform"]
    source_key: str
    appointment_id: int | None
    status: Literal["draft", "simulated", "cancelled"]
    environment: Literal["demo"]
    number: str | None
    competence: date
    description: str
    service_code: str
    amount: JsonDecimal
    iss_rate: JsonDecimal
    iss_amount: JsonDecimal
    issuer: FiscalProfileData
    recipient: FiscalParty
    created_at: datetime
    issued_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
