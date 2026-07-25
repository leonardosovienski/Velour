from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base


class GenderTarget(str, enum.Enum):
    M = "M"
    F = "F"
    all = "all"


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    gender_target = Column(SAEnum(GenderTarget), nullable=False, default=GenderTarget.all)
    icon = Column(String(50), nullable=True)

    services = relationship("Service", back_populates="category")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    points_reward = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    category = relationship("ServiceCategory", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")
    recipes = relationship("ServiceRecipe", back_populates="service")
