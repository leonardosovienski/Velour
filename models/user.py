from datetime import datetime
import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum

from database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    professional = "professional"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.professional)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
