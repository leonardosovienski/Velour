from datetime import datetime
import enum

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class ReferralStatus(str, enum.Enum):
    pending = "pending"
    converted = "converted"


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    status = Column(SAEnum(ReferralStatus), nullable=False, default=ReferralStatus.pending)
    points_awarded_referrer = Column(Integer, default=0)
    points_awarded_referred = Column(Integer, default=0)
    converted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    referrer = relationship("Client", back_populates="referrals_made", foreign_keys=[referrer_id])
    referred = relationship("Client", back_populates="referred_clients", foreign_keys=[referred_id])
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="referral")
