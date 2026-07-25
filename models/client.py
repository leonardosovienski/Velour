from datetime import datetime, date
import enum
import random
import string

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    other = "other"


class LoyaltyTier(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


class ChatPreference(str, enum.Enum):
    chatty = "chatty"
    quiet = "quiet"
    neutral = "neutral"


# Thresholds do tier baseados em total_spent
TIER_THRESHOLDS = {
    LoyaltyTier.bronze:   0,
    LoyaltyTier.silver:   500,
    LoyaltyTier.gold:     1500,
    LoyaltyTier.platinum: 3000,
}


def calculate_tier(total_spent: float) -> LoyaltyTier:
    if total_spent >= 3000:
        return LoyaltyTier.platinum
    if total_spent >= 1500:
        return LoyaltyTier.gold
    if total_spent >= 500:
        return LoyaltyTier.silver
    return LoyaltyTier.bronze


def generate_referral_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # VLR-00042
    name = Column(String(120), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(120), nullable=True)
    gender = Column(SAEnum(Gender), nullable=False)
    birthdate = Column(Date, nullable=True)
    first_visit = Column(Date, nullable=False, default=date.today)
    photo_url = Column(String(500), nullable=True)

    # Perfil sensorial
    preferred_drink = Column(String(100), nullable=True)
    music_preference = Column(String(100), nullable=True)
    temperature_preference = Column(String(100), nullable=True)
    chat_preference = Column(SAEnum(ChatPreference), nullable=False, default=ChatPreference.neutral)
    allergies = Column(String(500), nullable=True)
    notes = Column(String(1000), nullable=True)

    # Fidelidade
    loyalty_points = Column(Integer, default=0)
    loyalty_tier = Column(SAEnum(LoyaltyTier), nullable=False, default=LoyaltyTier.bronze)
    total_spent = Column(Float, default=0.0)
    total_visits = Column(Integer, default=0)

    # Indicação
    referral_code = Column(String(20), unique=True, nullable=False)
    referred_by_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    appointments = relationship(
        "Appointment", back_populates="client", foreign_keys="Appointment.client_id"
    )
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="client")
    referrals_made = relationship(
        "Referral", back_populates="referrer", foreign_keys="Referral.referrer_id"
    )
    referred_clients = relationship(
        "Referral", back_populates="referred", foreign_keys="Referral.referred_id"
    )
    referred_by = relationship("Client", remote_side=[id], foreign_keys=[referred_by_id])
