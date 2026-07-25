import pytest
from datetime import datetime

from models.appointment import AppointmentStatus
from models.loyalty import LoyaltyTransaction, TransactionType
from models.referral import Referral, ReferralStatus
from routers.appointments import _apply_loyalty_completion, REFERRAL_POINTS_REFERRER, REFERRAL_POINTS_REFERRED
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


@pytest.fixture
def referral_setup(db):
    referrer = make_client(db, name="Indicador", referral_code="REF00001", code="VLR-00001")
    referred = make_client(db, name="Indicado", referral_code="REF00002", code="VLR-00002",
                           referred_by_id=referrer.id)
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=100.0, points_reward=0)

    referral = Referral(
        referrer_id=referrer.id,
        referred_id=referred.id,
        status=ReferralStatus.pending,
    )
    db.add(referral)
    db.commit()

    return db, referrer, referred, prof, svc, referral


def test_converte_no_primeiro_atendimento(referral_setup):
    db, referrer, referred, prof, svc, referral = referral_setup

    appt = make_appointment(db, referred.id, prof.id, svc.id)
    appt.status = AppointmentStatus.completed
    appt.price_charged = 100.0
    appt.discount_points_used = 0
    db.flush()

    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(referral)

    assert referral.status == ReferralStatus.converted
    assert referral.converted_at is not None


def test_nao_converte_no_segundo_atendimento(referral_setup):
    db, referrer, referred, prof, svc, referral = referral_setup

    # Primeiro atendimento: converte
    appt1 = make_appointment(db, referred.id, prof.id, svc.id,
                             scheduled_at=datetime(2026, 5, 1, 10, 0),
                             ends_at=datetime(2026, 5, 1, 11, 0),
                             status="completed")
    appt1.price_charged = 100.0
    appt1.discount_points_used = 0
    db.flush()
    _apply_loyalty_completion(db, appt1)
    db.commit()
    db.refresh(referral)
    assert referral.status == ReferralStatus.converted

    # Segundo atendimento: não deve criar nova conversão nem alterar status
    appt2 = make_appointment(db, referred.id, prof.id, svc.id,
                             scheduled_at=datetime(2026, 5, 2, 10, 0),
                             ends_at=datetime(2026, 5, 2, 11, 0))
    appt2.status = AppointmentStatus.completed
    appt2.price_charged = 100.0
    appt2.discount_points_used = 0
    db.flush()
    _apply_loyalty_completion(db, appt2)
    db.commit()

    # Deve haver apenas 1 referral (não duplicar conversão)
    referrals = db.query(Referral).filter(
        Referral.referred_id == referred.id,
        Referral.status == ReferralStatus.converted,
    ).all()
    assert len(referrals) == 1


def test_referrer_recebe_150_pts(referral_setup):
    db, referrer, referred, prof, svc, referral = referral_setup

    appt = make_appointment(db, referred.id, prof.id, svc.id)
    appt.status = AppointmentStatus.completed
    appt.price_charged = 100.0
    appt.discount_points_used = 0
    db.flush()

    pontos_antes = referrer.loyalty_points
    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(referrer)

    assert referrer.loyalty_points == pontos_antes + REFERRAL_POINTS_REFERRER
    assert REFERRAL_POINTS_REFERRER == 150


def test_referred_recebe_75_pts(referral_setup):
    db, referrer, referred, prof, svc, referral = referral_setup

    appt = make_appointment(db, referred.id, prof.id, svc.id)
    appt.status = AppointmentStatus.completed
    appt.price_charged = 100.0
    appt.discount_points_used = 0
    db.flush()

    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(referred)

    # Pontos de referral + pontos do atendimento (price * POINTS_PER_BRL)
    referral_pts = REFERRAL_POINTS_REFERRED
    assert referral_pts == 75

    earned_referral_txn = db.query(LoyaltyTransaction).filter(
        LoyaltyTransaction.client_id == referred.id,
        LoyaltyTransaction.type == TransactionType.earned_referral,
    ).first()
    assert earned_referral_txn is not None
    assert earned_referral_txn.points == 75


def test_status_muda_para_converted(referral_setup):
    db, referrer, referred, prof, svc, referral = referral_setup

    appt = make_appointment(db, referred.id, prof.id, svc.id)
    appt.status = AppointmentStatus.completed
    appt.price_charged = 100.0
    appt.discount_points_used = 0
    db.flush()

    _apply_loyalty_completion(db, appt)
    db.commit()
    db.refresh(referral)

    assert referral.status == ReferralStatus.converted
    assert referral.points_awarded_referrer == REFERRAL_POINTS_REFERRER
    assert referral.points_awarded_referred == REFERRAL_POINTS_REFERRED
