"""Demonstration documents are deliberately separate from authorized NFS-e."""
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint

from database import Base, TenantScoped


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FiscalProfile(TenantScoped, Base):
    __tablename__ = "fiscal_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_fiscal_profile_tenant"),)
    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class FiscalDocument(TenantScoped, Base):
    __tablename__ = "fiscal_documents"
    __table_args__ = (UniqueConstraint("tenant_id", "issuer_kind", "source_key", name="uq_fiscal_document_source"),)
    id = Column(Integer, primary_key=True)
    issuer_kind = Column(String(16), nullable=False)  # salon / platform
    source_key = Column(String(160), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    status = Column(String(16), nullable=False, default="draft")
    environment = Column(String(16), nullable=False, default="demo")
    number = Column(String(40), nullable=True, unique=True)
    competence = Column(Date, nullable=False)
    description = Column(String(2000), nullable=False)
    service_code = Column(String(6), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    iss_rate = Column(Numeric(5, 2), nullable=False)
    iss_amount = Column(Numeric(12, 2), nullable=False)
    issuer = Column(JSON, nullable=False)
    recipient = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    issued_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(300), nullable=True)


class FiscalEvent(TenantScoped, Base):
    __tablename__ = "fiscal_events"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("fiscal_documents.id"), nullable=False)
    action = Column(String(32), nullable=False)
    actor_user_id = Column(Integer, nullable=False)  # platform actor may belong to another tenant
    created_at = Column(DateTime, nullable=False, default=utcnow)


class PlatformFiscalProfile(Base):
    __tablename__ = "platform_fiscal_profile"
    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
