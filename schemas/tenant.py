from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class TenantSignup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: str = Field(min_length=2, max_length=120)
    admin_name: str = Field(min_length=2, max_length=120)
    admin_email: EmailStr = Field(max_length=120)
    admin_password: str = Field(min_length=12, max_length=128)
    accepted_terms: Literal[True]

    @field_validator("tenant_name", "admin_name")
    @classmethod
    def trim_names(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Informe ao menos dois caracteres")
        return value


class ForgotPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=120)


class ResetPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)
