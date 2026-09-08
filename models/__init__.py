from models.tenant import Tenant
from models.saas import PasswordResetToken, BillingWebhookEvent
from models.user import User, UserRole
from models.client import Client, Gender, LoyaltyTier, ChatPreference, calculate_tier, generate_referral_code
from models.professional import Professional, ProfGender
from models.service import ServiceCategory, Service, GenderTarget
from models.appointment import Appointment, AppointmentStatus
from models.loyalty import LoyaltyTransaction, TransactionType
from models.referral import Referral, ReferralStatus
from models.product import Product, ProductUnit
from models.service_recipe import ServiceRecipe
from models.stock_movement import StockMovement, StockMovementType
from models.audit_log import AuditLog

__all__ = [
    "User", "UserRole",
    "Client", "Gender", "LoyaltyTier", "ChatPreference", "calculate_tier", "generate_referral_code",
    "Professional", "ProfGender",
    "ServiceCategory", "Service", "GenderTarget",
    "Appointment", "AppointmentStatus",
    "LoyaltyTransaction", "TransactionType",
    "Referral", "ReferralStatus",
    "Product", "ProductUnit",
    "ServiceRecipe",
    "StockMovement", "StockMovementType",
]

# Composite foreign keys enforce ownership even for privileged/direct SQL writes.
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from database import Base, TenantScoped

for _mapper in list(Base.registry.mappers):
    if not issubclass(_mapper.class_, TenantScoped):
        continue
    _table = _mapper.local_table
    _table.append_constraint(UniqueConstraint("tenant_id", "id", name=f"uq_{_table.name}_tenant_id"))
    for _column in list(_table.columns):
        if _column.name == "tenant_id":
            continue
        for _fk in list(_column.foreign_keys):
            _target = _fk.column.table
            if "tenant_id" in _target.c:
                _table.append_constraint(ForeignKeyConstraint(
                    ["tenant_id", _column.name],
                    [f"{_target.name}.tenant_id", f"{_target.name}.{_fk.column.name}"],
                    name=f"fk_{_table.name}_{_column.name}_tenant",
                ))
Client.__table__.append_constraint(UniqueConstraint("tenant_id", "code", name="uq_clients_tenant_code"))
Client.__table__.append_constraint(UniqueConstraint("tenant_id", "referral_code", name="uq_clients_tenant_referral_code"))
