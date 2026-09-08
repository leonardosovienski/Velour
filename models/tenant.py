from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    subscription_status = Column(String(32), nullable=False, default="trialing")
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    past_due_since = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)
    accepted_terms_at = Column(DateTime, nullable=True)
    terms_version = Column(String(40), nullable=True)
    checkout_session_id = Column(String(255), nullable=True)
    checkout_session_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
