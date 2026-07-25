from datetime import datetime, timedelta

import pytest

from routers.professionals import professional_dashboard
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


def _completed_appt(db, client_id, prof_id, service_id, days_ago):
    when = datetime.now() - timedelta(days=days_ago)
    return make_appointment(
        db, client_id, prof_id, service_id,
        scheduled_at=when, ends_at=when + timedelta(hours=1), status="completed",
    )


# ── Clientes inativos por cadência ───────────────────────────────────────────

def test_cliente_acima_da_cadencia_aparece_inativo(db):
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=100.0)
    cli = make_client(db, name="Atrasado", code="VLR-00001", referral_code="R1")
    # Atendimentos: 100, 70 e 40 dias atrás → gaps 30 e 30 → cadência 30
    # Última visita há 40 dias > 30 → inativo (atrasado 10)
    for d in (100, 70, 40):
        _completed_appt(db, cli.id, prof.id, svc.id, d)
    db.flush()

    res = professional_dashboard(prof.id, db=db, _=None)
    inativos = res["inactive_clients"]

    assert len(inativos) == 1
    assert inativos[0]["client_id"] == cli.id
    assert inativos[0]["avg_cadence_days"] == pytest.approx(30.0)
    assert inativos[0]["days_since_last"] == 40
    assert inativos[0]["overdue_by_days"] == pytest.approx(10.0)


def test_cliente_dentro_da_cadencia_nao_aparece(db):
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=100.0)
    cli = make_client(db, name="Em dia", code="VLR-00002", referral_code="R2")
    # 60, 30 e 5 dias atrás → cadência ~27.5; última há 5 dias < 27.5 → não inativo
    for d in (60, 30, 5):
        _completed_appt(db, cli.id, prof.id, svc.id, d)
    db.flush()

    res = professional_dashboard(prof.id, db=db, _=None)
    assert res["inactive_clients"] == []


def test_cliente_com_uma_visita_nao_entra(db):
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, price=100.0)
    cli = make_client(db, name="Visita única", code="VLR-00003", referral_code="R3")
    _completed_appt(db, cli.id, prof.id, svc.id, 200)  # só 1 atendimento, sem cadência
    db.flush()

    res = professional_dashboard(prof.id, db=db, _=None)
    assert res["inactive_clients"] == []


# ── Meta financeira do mês ───────────────────────────────────────────────────

def test_progresso_da_meta_mensal(db):
    prof = make_professional(db)
    prof.monthly_goal = 1000.0
    cat = make_category(db)
    svc = make_service(db, cat.id, price=300.0)
    cli = make_client(db, code="VLR-00004", referral_code="R4")

    appt = _completed_appt(db, cli.id, prof.id, svc.id, days_ago=0)
    appt.price_charged = 300.0
    db.flush()

    res = professional_dashboard(prof.id, db=db, _=None)
    meta = res["monthly_goal"]

    assert meta["target"] == pytest.approx(1000.0)
    assert meta["revenue"] == pytest.approx(300.0)
    assert meta["progress"] == pytest.approx(0.3)
    assert meta["remaining"] == pytest.approx(700.0)
    assert meta["commission"] == pytest.approx(120.0)  # 300 * 0.40


def test_sem_meta_progresso_nulo(db):
    prof = make_professional(db)  # monthly_goal = 0 por padrão
    res = professional_dashboard(prof.id, db=db, _=None)
    assert res["monthly_goal"]["progress"] is None
    assert res["monthly_goal"]["remaining"] is None
