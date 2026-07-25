from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base
from models.client import LoyaltyTier


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    status = Column(SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.scheduled)
    occasion = Column(String(200), nullable=True)
    notes = Column(String(1000), nullable=True)
    photo_before_url = Column(String(500), nullable=True)
    photo_after_url = Column(String(500), nullable=True)
    formula_used = Column(String(500), nullable=True)
    points_awarded = Column(Integer, default=0)
    price_charged = Column(Float, nullable=True)
    discount_points_used = Column(Integer, default=0)
    # Registro do benefício de tier aplicado no fechamento (para relatórios)
    tier_at_service = Column(SAEnum(LoyaltyTier), nullable=True)
    tier_discount_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)

    client = relationship("Client", back_populates="appointments", foreign_keys=[client_id])
    professional = relationship("Professional", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="appointment")
    stock_movements = relationship("StockMovement", back_populates="appointment")
