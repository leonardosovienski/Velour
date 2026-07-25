import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

from routers.appointments import _check_conflict
from tests.conftest import make_client, make_professional, make_category, make_service, make_appointment


def dt(hour, minute=0):
    return datetime(2026, 6, 1, hour, minute)


@pytest.fixture
def setup(db):
    client = make_client(db)
    prof = make_professional(db)
    cat = make_category(db)
    svc = make_service(db, cat.id, duration_minutes=60)
    db.commit()
    return db, client, prof, svc


def test_sobreposicao_parcial_antes(setup):
    """Novo começa antes e termina durante o existente."""
    db, client, prof, svc = setup
    make_appointment(db, client.id, prof.id, svc.id,
                     scheduled_at=dt(10), ends_at=dt(11))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        _check_conflict(db, prof.id, dt(9, 30), dt(10, 30))
    assert exc.value.status_code == 409


def test_sobreposicao_total(setup):
    """Novo engloba completamente o existente."""
    db, client, prof, svc = setup
    make_appointment(db, client.id, prof.id, svc.id,
                     scheduled_at=dt(10), ends_at=dt(11))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        _check_conflict(db, prof.id, dt(9), dt(12))
    assert exc.value.status_code == 409


def test_adjacente_nao_conflita(setup):
    """Novo começa exatamente quando o existente termina — deve ser permitido."""
    db, client, prof, svc = setup
    make_appointment(db, client.id, prof.id, svc.id,
                     scheduled_at=dt(10), ends_at=dt(11))
    db.commit()

    _check_conflict(db, prof.id, dt(11), dt(12))  # não deve lançar exceção


def test_profissional_diferente_nao_conflita(setup):
    """Mesmo horário, profissional diferente — não deve conflitar."""
    db, client, prof, svc = setup
    make_appointment(db, client.id, prof.id, svc.id,
                     scheduled_at=dt(10), ends_at=dt(11))
    db.commit()

    outro_prof = make_professional(db, name="Outro Profissional")
    db.commit()

    _check_conflict(db, outro_prof.id, dt(10), dt(11))  # não deve lançar exceção


def test_ignore_id_exclui_proprio_agendamento(setup):
    """ignore_id deve excluir o próprio agendamento da checagem (usado em reagendamentos)."""
    db, client, prof, svc = setup
    appt = make_appointment(db, client.id, prof.id, svc.id,
                            scheduled_at=dt(10), ends_at=dt(11))
    db.commit()

    # Sem ignore_id conflitaria consigo mesmo, com ignore_id não deve conflitar
    _check_conflict(db, prof.id, dt(10), dt(11), ignore_id=appt.id)


def test_cancelado_nao_conflita(setup):
    """Agendamento cancelado não bloqueia o horário."""
    db, client, prof, svc = setup
    make_appointment(db, client.id, prof.id, svc.id,
                     scheduled_at=dt(10), ends_at=dt(11), status="cancelled")
    db.commit()

    _check_conflict(db, prof.id, dt(10), dt(11))  # não deve lançar exceção
