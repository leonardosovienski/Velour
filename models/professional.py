from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class ProfGender(str, enum.Enum):
    M = "M"
    F = "F"
    other = "other"


class Professional(Base):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(120), nullable=True)
    gender = Column(SAEnum(ProfGender), nullable=False)
    photo_url = Column(String(500), nullable=True)
    specialty = Column(String(300), nullable=False)
    bio = Column(String(1000), nullable=True)
    commission_rate = Column(Float, default=0.40)
    monthly_goal = Column(Float, default=0.0)  # meta de receita do mês (R$)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    appointments = relationship("Appointment", back_populates="professional")
