from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401 — registra os modelos no metadata
import reminder_scheduler
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield Session
    engine.dispose()


def _seed_appointment(Session, scheduled_at, status="scheduled", client_email="cliente@teste.com"):
    db = Session()
    client = make_client(db, name="Cliente Lembrete", referral_code="LEMB0001", code="VLR-LEM01")
    client.email = client_email
    prof = make_professional(db, name="Prof Lembrete")
    cat = make_category(db)
    svc = make_service(db, cat.id)
    appt = make_appointment(db, client.id, prof.id, svc.id, scheduled_at=scheduled_at, status=status)
    db.commit()
    appt_id = appt.id
    db.close()
    return appt_id


def test_envia_lembrete_para_agendamento_na_janela_de_24h(session_factory):
    scheduled_at = datetime.now() + timedelta(hours=24, minutes=15)
    appt_id = _seed_appointment(session_factory, scheduled_at)

    with patch("reminder_scheduler.SessionLocal", session_factory), \
         patch("reminder_scheduler.send_appointment_reminder", return_value=True) as mock_send:
        reminder_scheduler._run_reminder_job()

    mock_send.assert_called_once()
    db = session_factory()
    from models.appointment import Appointment
    appt = db.get(Appointment, appt_id)
    assert appt.reminder_sent is True
    db.close()


def test_nao_envia_para_agendamento_fora_da_janela(session_factory):
    scheduled_at = datetime.now() + timedelta(hours=3)  # muito próximo, fora da janela de 24h
    _seed_appointment(session_factory, scheduled_at)

    with patch("reminder_scheduler.SessionLocal", session_factory), \
         patch("reminder_scheduler.send_appointment_reminder", return_value=True) as mock_send:
        reminder_scheduler._run_reminder_job()

    mock_send.assert_not_called()


def test_nao_reenvia_para_agendamento_ja_notificado(session_factory):
    scheduled_at = datetime.now() + timedelta(hours=24, minutes=10)
    appt_id = _seed_appointment(session_factory, scheduled_at)

    db = session_factory()
    from models.appointment import Appointment
    appt = db.get(Appointment, appt_id)
    appt.reminder_sent = True
    db.commit()
    db.close()

    with patch("reminder_scheduler.SessionLocal", session_factory), \
         patch("reminder_scheduler.send_appointment_reminder", return_value=True) as mock_send:
        reminder_scheduler._run_reminder_job()

    mock_send.assert_not_called()


def test_nao_envia_para_agendamento_cancelado(session_factory):
    scheduled_at = datetime.now() + timedelta(hours=24, minutes=10)
    appt_id = _seed_appointment(session_factory, scheduled_at, status="cancelled")

    with patch("reminder_scheduler.SessionLocal", session_factory), \
         patch("reminder_scheduler.send_appointment_reminder", return_value=True) as mock_send:
        reminder_scheduler._run_reminder_job()

    mock_send.assert_not_called()
