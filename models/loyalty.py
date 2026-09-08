from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base, TenantScoped


class TransactionType(str, enum.Enum):
    earned_appointment = "earned_appointment"
    earned_referral = "earned_referral"
    earned_birthday = "earned_birthday"
    redeemed = "redeemed"


class LoyaltyTransaction(TenantScoped, Base):
    __tablename__ = "loyalty_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=True)
    type = Column(SAEnum(TransactionType), nullable=False)
    points = Column(Integer, nullable=False)  # positivo = ganhou, negativo = usou
    description = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    client = relationship("Client", back_populates="loyalty_transactions", foreign_keys=[client_id])
    appointment = relationship("Appointment", back_populates="loyalty_transactions", foreign_keys=[appointment_id])
    referral = relationship("Referral", back_populates="loyalty_transactions", foreign_keys=[referral_id])
