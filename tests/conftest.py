import sys
import os
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Garante que o root do projeto está no path para importar os módulos backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Base
import models  # noqa: F401 — registers all models with Base metadata


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_client(db, name="Cliente Teste", referral_code="TST00001", code="VLR-00001",
                gender="F", referred_by_id=None):
    from models.client import Client, Gender
    c = Client(
        code=code,
        name=name,
        phone="11999999999",
        gender=Gender.F,
        referral_code=referral_code,
        referred_by_id=referred_by_id,
        first_visit=date.today(),
    )
    db.add(c)
    db.flush()
    return c


def make_professional(db, name="Profissional Teste"):
    from models.professional import Professional, ProfGender
    p = Professional(name=name, specialty="Corte", phone="11888888888", gender=ProfGender.F)
    db.add(p)
    db.flush()
    return p


def make_category(db):
    from models.service import ServiceCategory, GenderTarget
    c = ServiceCategory(name="Categoria Teste", gender_target=GenderTarget.all)
    db.add(c)
    db.flush()
    return c


def make_service(db, category_id, duration_minutes=60, price=100.0, points_reward=50):
    from models.service import Service
    s = Service(
        category_id=category_id,
        name="Serviço Teste",
        duration_minutes=duration_minutes,
        price=price,
        points_reward=points_reward,
    )
    db.add(s)
    db.flush()
    return s


def make_appointment(db, client_id, professional_id, service_id,
                     scheduled_at=None, ends_at=None, status="scheduled"):
    from models.appointment import Appointment, AppointmentStatus
    from datetime import timedelta
    if scheduled_at is None:
        scheduled_at = datetime(2026, 6, 1, 10, 0)
    if ends_at is None:
        ends_at = scheduled_at + timedelta(hours=1)
    a = Appointment(
        client_id=client_id,
        professional_id=professional_id,
        service_id=service_id,
        scheduled_at=scheduled_at,
        ends_at=ends_at,
        status=AppointmentStatus(status),
    )
    db.add(a)
    db.flush()
    return a
